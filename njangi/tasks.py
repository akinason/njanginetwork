import datetime
import decimal

from django.contrib.auth import get_user_model as UserModel
from django.db.models import F, ExpressionWrapper, DurationField
from django.db.models.functions import Extract
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


from mailer import services as mailer_services
from main.core import FailedOperationTypes, TransactionStatus
from njangi.core import get_level_contribution_amount, get_upline_to_pay_upgrade_contribution
from njangi.models import (
    LevelModel, FailedOperations, AccountPackage, UserAccountSubscriptionType, UserAccountManager, LEVEL_CONTRIBUTIONS,
    WALLET_CONTRIBUTION_PROCESSING_FEE_RATE, NSP, CONTRIBUTION_INTERVAL_IN_DAYS
)
from njanginetwork.celery import app
from purse import services as purse_services
from purse.models import WalletManager
from purse.models import (
    WalletTransStatus, WalletTransMessage, WalletTransDescription, MobileMoneyManager, MOMOPurpose,
    MMRequestType
)


wallet_manager = wallet = WalletManager()
user_account_manager = UserAccountManager()
trans_status = WalletTransStatus()
trans_message = WalletTransMessage()
trans_description = WalletTransDescription()
service_provider = NSP()
fot = FailedOperationTypes()
TRANSStatus = TransactionStatus()
D = decimal.Decimal
momo_purpose = MOMOPurpose()
momo_manager = MobileMoneyManager()
momo_request_type = MMRequestType()
user_account_subscription_type = UserAccountSubscriptionType()

@app.task
def process_contribution(level, nsp, processing_fee=0.00, user_id=None, recipient_id=None, tracker_id=None):
    """
    Processes the contribution and return the status of the transaction.
    0. Request cash deposit from mobile money API (API request is not needed here.) **Deprecated**

    1. Fund the users wallet if nsp=orange or mtn. (ignored if nsp=mtn_wallet or nsp=orange_wallet)
    2. Transfer funds from user's wallet to recipient's wallet.
    3. Request a withdrawal from the user's wallet.
    4. Upgrade the user if user's level is less than this level.
    5. Update user's LevelModel for last_payment, total_sent and update recipient's LevelModel with total_received.
    """
    user = None
    recipient = None
    thirdparty_reference = None
    mm_transaction = None

    contribution_amount = get_level_contribution_amount(level)
    amount = contribution_amount

    recipient_charge = 0.00
    recipient_amount = contribution_amount

    recipient_tel = None
    sender_tel = None

    if tracker_id and (nsp == service_provider.mtn() or nsp == service_provider.orange()):
        if not momo_manager.is_valid(tracker_id=tracker_id):
            response = {
                'status': trans_status.failed(), 'message': trans_message.failed_message(), 'tracker_id': tracker_id
            }
            return response

        mm_transaction = momo_manager.get_mm_transaction(tracker_id=tracker_id)
        api_callback_status_code = mm_transaction.callback_status_code
        processing_fee = mm_transaction.charge

        if mm_transaction.is_complete or not mm_transaction.purpose == momo_purpose.contribution() or \
                not mm_transaction.request_type == momo_request_type.deposit():
            response = {
                'status': trans_status.failed(), 'message': trans_message.already_treated_transaction(),
                'tracker_id': tracker_id
            }
            return response
        if api_callback_status_code and (not int(api_callback_status_code) == 200):
            response = {
                'status': trans_status.failed(), 'message': trans_message.failed_message(), 'tracker_id': tracker_id
            }
            mailer_services.send_nsp_contribution_failed_email.delay(user_id=mm_transaction.user.id, nsp=nsp,
                                                                     level=level, amount=recipient_amount)
            mailer_services.send_nsp_contribution_failed_sms.delay(user_id=mm_transaction.user.id, nsp=nsp,
                                                                   level=level, amount=recipient_amount)
            return response

        thirdparty_reference = tracker_id
        user = mm_transaction.user
        recipient = mm_transaction.recipient
    elif (nsp == service_provider.orange_wallet() or nsp == service_provider.mtn_wallet()) and user_id and recipient_id:
        user = UserModel().objects.get(pk=user_id)
        recipient = UserModel().objects.get(pk=recipient_id)
    else:
        response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
        return response

    params = {'level': level, 'sender': user.username, 'recipient': recipient.username}
    information = _('level %(level)s contribution from %(sender)s to %(recipient)s.') % params
    loading_amount = D(amount) + D(processing_fee)
    loading_charge = 0.00
    contribution_charge = processing_fee

    if nsp == service_provider.mtn() or nsp == service_provider.orange():
        if nsp == service_provider.mtn() and user.tel1 and user.tel1_is_verified:
            sender_tel = user.tel1.national_number
        elif nsp == service_provider.orange() and user.tel2 and user.tel2_is_verified:
            sender_tel = user.tel2.national_number
        else:
            mailer_services.send_nsp_contribution_failed_email.delay(user_id=user.id, nsp=nsp, level=level,
                                                                     amount=amount)
            mailer_services.send_nsp_contribution_failed_sms.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
            return {'status': trans_status.failed(), 'message': trans_message.failed_message()}

        response = wallet.load_and_contribute(
            user=user, recipient=recipient, loading_amount=loading_amount, contribution_amount=contribution_amount,
            recipient_amount=recipient_amount, loading_charge=loading_charge, recipient_charge=recipient_charge,
            contribution_charge=contribution_charge, information=information, sender_tel=sender_tel,
            recipient_tel=recipient_tel, thirdparty_reference=thirdparty_reference, nsp=nsp
        )

        # if the transaction is successful, update the user level, the njangi model and process the payout.
        if response['status'] == trans_status.success():

            process_contribution_response(response=response, user=user, recipient=recipient,
                                          level=level, recipient_amount=recipient_amount, nsp=nsp,
                                          processing_fee=recipient_charge, mm_transaction=mm_transaction
                                          )
            return {'status': trans_status.success(), 'message': trans_message.success_message()}
        else:
            FailedOperations.objects.create(
                user=user, recipient=recipient, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
                processing_fee=processing_fee, transaction_id=thirdparty_reference,
                status=trans_status.pending(), operation_type=fot.contribution(),
                message=response['message'], response_status=response['status']
            )
            mailer_services.send_nsp_contribution_pending_email.delay(user_id=user.id, nsp=nsp, level=level,
                                                                      amount=amount)
            mailer_services.send_nsp_contribution_pending_sms.delay(user_id=user.id, nsp=nsp, level=level,
                                                                    amount=amount)
            return {'status': trans_status.pending(), 'message': trans_message.failed_message()}

    elif nsp == service_provider.mtn_wallet():
        # then processing will be done in the mtn wallet
        nsp = service_provider.mtn()

        response = wallet.contribute(
            sender=user, recipient=recipient, sender_amount=contribution_amount, recipient_amount=recipient_amount,
            information=information, nsp=nsp, sender_tel=sender_tel, recipient_tel=recipient_tel,
            sender_charge=processing_fee, recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference
        )

        # if the transaction is successful, update the user level, the njangi model and process the payout.
        if response['status'] == trans_status.success():
            process_contribution_response(response=response, user=user, recipient=recipient,
                                          level=level, recipient_amount=recipient_amount, nsp=nsp,
                                          processing_fee=recipient_charge
                                          )
            return {'status': trans_status.success()}
        else:
            FailedOperations.objects.create(
                user=user, recipient=recipient, level=level, amount=amount, nsp=service_provider.mtn_wallet(),
                sender_tel=sender_tel, processing_fee=processing_fee, transaction_id=thirdparty_reference,
                status=trans_status.pending(), operation_type=fot.contribution(), message=response['message'],
                response_status=response['status']
            )
            mailer_services.send_wallet_contribution_failed_email.delay(
                user_id=user.id, nsp=service_provider.mtn_wallet(), level=level, amount=amount
            )
            mailer_services.send_wallet_contribution_failed_sms.delay(
                user_id=user.id, nsp=service_provider.mtn_wallet(), level=level, amount=amount
            )
            return {'status': trans_status.pending(), 'message': trans_message.failed_message()}

    elif nsp == service_provider.orange_wallet():
        # then processing will be done in the orange wallet
        nsp = service_provider.orange()

        response = wallet.contribute(
            sender=user, recipient=recipient, sender_amount=contribution_amount, recipient_amount=recipient_amount,
            information=information, nsp=nsp, sender_tel=sender_tel, recipient_tel=recipient_tel,
            sender_charge=processing_fee, recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference
        )

        # if the transaction is successful, update the user level, the njangi model and process the payout.
        if response['status'] == trans_status.success():
            process_contribution_response(response=response, user=user, recipient=recipient,
                                          level=level, recipient_amount=recipient_amount, nsp=nsp,
                                          processing_fee=recipient_charge
                                          )
            return {'status': trans_status.success()}
        else:
            FailedOperations.objects.create(
                user=user, recipient=recipient, level=level, amount=amount, nsp=service_provider.orange_wallet(),
                sender_tel=sender_tel,
                processing_fee=processing_fee, transaction_id=thirdparty_reference, status=trans_status.pending(),
                operation_type=fot.contribution(), message=response['message'], response_status=response['status']
            )
            mailer_services.send_wallet_contribution_failed_email.delay(
                user_id=user.id, nsp=service_provider.orange_wallet(), level=level, amount=amount
            )
            mailer_services.send_wallet_contribution_failed_sms.delay(
                user_id=user.id, nsp=service_provider.orange_wallet(), level=level, amount=amount
            )

            return {'status': trans_status.pending(), 'message': trans_message.failed_message()}
    else:
        return {'status': trans_status.failed(), 'message': trans_message.failed_message()}


def process_contribution_response(
    response, user, recipient, level, recipient_amount, nsp, processing_fee, mm_transaction=None
):
    """
    If the response status received is 'success' it does the following:
        1) Upgrade the user level if need be.
        2) Update the status of the user on the LevelModel: last_payment, next_payment, is_active, total_sent,
           total_received etc
        3) Update the recipient's LevelModel for total_received
        4) Send emails and sms to the recipient and the sender
        5) Process payout to the recipient
        6) Return a response.
    If the response status received is 'failed' then it returns a failed response as well.

    :param response:
    :param user:
    :param recipient:
    :param level:
    :param recipient_amount:
    :param nsp:
    :param processing_fee:
    :return: returns a dictionary response
    :param mm_transaction: An instance of the mobile money transaction.
    {'status': <success or failed>, 'message': <trans_message.success_message() or trans_message.failed_message()>}
    """

    if response['status'] == trans_status.success():
        # proceed to upgrade the user level and the Level model.
        if user.level < int(level):
            user.level = level
            user.save()

        njangi_level, created = LevelModel.objects.get_or_create(user=user, level=level)
        njangi_level.is_active = True
        njangi_level.recipient = recipient
        njangi_level.amount = recipient_amount
        njangi_level.total_sent += recipient_amount
        njangi_level.last_payment = timezone.now()

        if njangi_level.next_payment:
            next_payment = njangi_level.next_payment
            if next_payment > timezone.now():
                # If the user is paying in advance, increase the next due date starting from the previous due date.
                next_payment_date = next_payment + datetime.timedelta(days=CONTRIBUTION_INTERVAL_IN_DAYS)
                njangi_level.next_payment = next_payment_date
            else:
                # But if the user is paying after the due date, just add the interval of contribution starting
                # from today's date.
                next_payment_date = timezone.now() + datetime.timedelta(days=CONTRIBUTION_INTERVAL_IN_DAYS)
                njangi_level.next_payment = next_payment_date
        else:
            njangi_level.next_payment = timezone.now() + datetime.timedelta(days=CONTRIBUTION_INTERVAL_IN_DAYS)
        njangi_level.save()

        # Update the recipient's LevelModel's total_received.
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received += recipient_amount
        njangi_level.save()

        # Mark the MOMO transaction as complete.
        if mm_transaction:
            mm_transaction.is_complete = True
            mm_transaction.save()

        # Send a confirmation sms and/or email to sender.
        mailer_services.send_wallet_contribution_paid_email.delay(sender_id=user.id, recipient_id=recipient.id,
                                                                  amount=recipient_amount,
                                                                  processing_fee=processing_fee, nsp=nsp, level=level,
                                                                  )
        mailer_services.send_wallet_contribution_paid_sms.delay(sender_id=user.id, recipient_id=recipient.id,
                                                                amount=recipient_amount, processing_fee=processing_fee,
                                                                nsp=nsp, level=level,
                                                                )

        # send sms or email to recipient notifying him/her of amount received in the wallet.
        mailer_services.send_wallet_contribution_received_email.delay(sender_id=user.id, recipient_id=recipient.id,
                                                                      nsp=nsp,
                                                                      amount=recipient_amount, processing_fee=0.00,
                                                                      level=level
                                                                      )
        mailer_services.send_wallet_contribution_received_sms.delay(sender_id=user.id, recipient_id=recipient.id,
                                                                    nsp=nsp,
                                                                    amount=recipient_amount, processing_fee=0.00,
                                                                    level=level
                                                                    )

        # process payout to the recipient. Delay it and let Celery take over.
        _nsp = None
        tel = None
        if nsp == service_provider.mtn() or nsp == service_provider.mtn_wallet():
            _nsp = service_provider.mtn()
            if recipient.tel1 and recipient.tel1_is_verified:
                tel = recipient.tel1.national_number
        elif nsp == service_provider.orange() or nsp == service_provider.orange_wallet():
            _nsp = service_provider.orange()
            if recipient.tel2 and recipient.tel2_is_verified:
                tel = recipient.tel2.national_number
        if tel:
            purse_services.request_momo_payout(
                phone_number=tel, amount=recipient_amount, user_id=recipient.id,
                purpose=momo_purpose.contribution_wallet_withdraw(), nsp=_nsp, recipient_id=recipient.id, level=level,
                processing_fee=processing_fee,
            )

        process_response = {
            'status': trans_status.success(),
            'message': trans_message.success_message()
        }

        return process_response
    else:
        process_response = {
            'status': trans_status.failed(),
            'message': trans_message.failed_message()
        }
        return process_response


def process_wallet_withdraw(user_id, amount, nsp, tracker_id, charge=0.00):
    """
    Called after a callback is received from the Mobile Money provider.
    The objective of this function is to update the status of the transaction
    in the user's wallet from "pending" to "complete" or "failed"
    :param user_id:
    :param amount:
    :param nsp:
    :param tracker_id:
    :param charge:
    :return:
    """

    mm_transaction = momo_manager.get_mm_transaction(tracker_id=tracker_id)
    if mm_transaction and (
            mm_transaction.purpose == momo_purpose.wallet_withdraw() or
            mm_transaction.purpose == momo_purpose.contribution_wallet_withdraw()
    ):
        # Continue the processing of the transaction.
        if mm_transaction.is_complete:
            response = {
                'status': trans_status.failed(), 'message': trans_message.already_treated_transaction(),
                'tracker_id': tracker_id
            }
            return response
        elif mm_transaction.callback_status_code and not int(mm_transaction.callback_status_code) == 200:
            response = {
                'status': trans_status.failed(), 'message': trans_message.failed_message(),
                'tracker_id': tracker_id
            }
            # Change the status of the transaction from "pending" to "failed" in the user's wallet.
            r = wallet_manager.update_status(
                status=trans_status.complete(), tracker_id=mm_transaction.tracker_id
            )

            mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=user_id,
                                                                      message=trans_message.failed_message(),
                                                                      status=trans_status.failed())
            mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=user_id,
                                                                    message=trans_message.failed_message(),
                                                                    status=trans_status.failed())
            # Mark the transaction as complete
            mm_transaction.is_complete = True
            mm_transaction.save()
            return response
        else:
            r = wallet_manager.update_status(
                status=trans_status.complete(), tracker_id=mm_transaction.tracker_id
            )
            mailer_services.send_wallet_withdrawal_email.delay(
                user_id=user_id, amount=amount, processing_fee=charge, nsp=nsp
            )
            mailer_services.send_wallet_withdrawal_sms.delay(
                user_id=user_id, amount=amount, processing_fee=charge, nsp=nsp
            )
            # Mark the transaction as complete
            mm_transaction.is_complete = True
            mm_transaction.save()
    else:

        response = {
            'status': trans_status.failed(), 'message': trans_message.invalid_transaction(),
            'tracker_id': tracker_id
        }

        return response


@app.task
def process_wallet_load(user_id, amount, nsp, tracker_id, charge=0.00):
    # This function is called after a successful callback response is received from the MOMO API provider.
    loading_amount = D(amount) + D(charge)
    user = UserModel().objects.get(pk=user_id)
    information = _('wallet load through %s mobile money') % nsp.upper()

    mm_transaction = momo_manager.get_mm_transaction(tracker_id=tracker_id)
    if mm_transaction:
        if not momo_manager.is_valid(tracker_id=tracker_id):
            response = {'status': trans_status.failed(), 'message': trans_message.invalid_transaction(),
                        'tracker_id': tracker_id}
            return response
        elif not mm_transaction.callback_status_code or not int(mm_transaction.callback_status_code) == 200:
            response = {
                'status': trans_status.failed(), 'tracker_id': tracker_id,
                'message': trans_message.unauthenticated_transaction()
            }
            return response
        elif not mm_transaction.purpose == momo_purpose.wallet_load():
            response = {
                'status': trans_status.failed(),  'tracker_id': tracker_id,
                'message': trans_message.not_a_x_transaction() % momo_purpose.wallet_load()
            }
            return response
        elif mm_transaction.is_complete:
            response = {'status': trans_status.failed(), 'message': trans_message.already_treated_transaction(),
                        'tracker_id': tracker_id}
            return response
    else:
        response = {'status': trans_status.failed(), 'message': trans_message.invalid_transaction(),
                    'tracker_id': tracker_id}
        return response

    if nsp == service_provider.mtn():
        """Process loading operation"""
        # Proceed to update the user's wallet.
        load_response = wallet.load(
            user=user, amount=loading_amount, nsp=nsp, description=trans_description.wallet_load(),
            charge=charge, tel=user.tel1.national_number, thirdparty_reference=tracker_id,
            information=information,
        )
        if load_response['status'] == trans_status.failed():
            # add the transaction to FailedOperations and let celery take over.
            FailedOperations.objects.create(
                user=user, amount=loading_amount, nsp=nsp, processing_fee=charge,
                status=TRANSStatus.pending(), operation_type=fot.account_load_api_processed(),
                transaction_id=tracker_id
            )
            response = {'status': trans_status.pending(), 'message': trans_message.pending_message()}
            return response
        elif load_response['status'] == trans_status.success():
            # inform the user by sms/mail of the successful operation.
            mailer_services.send_wallet_load_success_email.delay(user_id=user.id, amount=amount,
                                                                 processing_fee=charge, nsp=nsp)
            mailer_services.send_wallet_load_success_sms.delay(user_id=user.id, amount=amount,
                                                               processing_fee=charge, nsp=nsp,
                                                               transaction_id=load_response['transactionId']
                                                               )
            # Mark the transaction as completed
            mm_transaction.is_complete = True
            mm_transaction.save()
            return load_response
    elif nsp == service_provider.orange():
        # Proceed to update the user's wallet.
        load_response = wallet.load(
            user=user, amount=loading_amount, nsp=nsp, description=trans_description.wallet_load(),
            charge=charge, tel=user.tel2.national_number, thirdparty_reference=tracker_id,
            information=information,
        )
        if load_response['status'] == trans_status.failed():
            # add the transaction to FailedOperations and let celery take over.
            FailedOperations.objects.create(
                user=user, amount=amount, nsp=nsp, processing_fee=charge,
                status=TRANSStatus.pending(), operation_type=fot.account_load_api_processed()
            )
            response = {'status': trans_status.pending(), 'message': trans_message.pending_message()}
            return response
        elif load_response['status'] == trans_status.success():
            # inform the user by sms/mail of the successful operation.
            mailer_services.send_wallet_load_success_email.delay(user_id=user.id, amount=amount,
                                                                 processing_fee=charge, nsp=nsp)
            mailer_services.send_wallet_load_success_sms.delay(user_id=user.id, amount=amount,
                                                               processing_fee=charge, nsp=nsp,
                                                               transaction_id=load_response['transactionId']
                                                               )
            # Mark the transaction as completed
            mm_transaction.is_complete = True
            mm_transaction.save()
            return load_response
    else:
        """inform of invalid nsp"""
        mailer_services.send_wallet_load_failed_email.delay(user_id=user.id, amount=amount,
                                                            processing_fee=charge, nsp=nsp)
        mailer_services.send_wallet_load_failed_sms.delay(user_id=user.id, amount=amount, processing_fee=charge,
                                                          nsp=nsp)
        response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
        return response


@app.task
def send_contribution_due_reminder():
    """
    Sends reminders to users, from 3 days to the date of their next level due contribution.
    """
    queryset = LevelModel.objects.filter(
        is_active=True
    ).annotate(
        duration=ExpressionWrapper(F('next_payment') - timezone.now(), DurationField())
    ).annotate(
        day=Extract('duration', 'day'), hour=Extract('duration', 'hour'), minute=Extract('duration', 'minute')
    ).filter(
        day__lte=3, day__gt=-1
    )

    if queryset:
        for obj in queryset:
            duration = _("%(day)s day(s) %(hour)s hour(s)") % {'day': obj.day, 'hour': obj.hour}

            mailer_services.send_contribution_due_reminder_email.delay(
                user_id=obj.user.id, level=obj.level, amount=LEVEL_CONTRIBUTIONS[obj.level], duration=duration
            )
            mailer_services.send_contribution_due_reminder_sms.delay(
                user_id=obj.user.id, level=obj.level, amount=LEVEL_CONTRIBUTIONS[obj.level], duration=duration
            )


@app.task
def deactivate_users_with_past_due_contribution():
    """
    deactivates users at a particular level whose contribution for the level is due.
    """
    queryset = LevelModel.objects.filter(is_active=True, next_payment__lt=timezone.now(), user__is_admin=False)
       
    if queryset:
        for obj in queryset:
            obj.is_active = False
            obj.save()
            mailer_services.send_level_deactivation_email.delay(
                user_id=obj.user.id, level=obj.level, amount=LEVEL_CONTRIBUTIONS[obj.level]
            )
            mailer_services.send_level_deactivation_sms.delay(
                user_id=obj.user.id, level=obj.level, amount=LEVEL_CONTRIBUTIONS[obj.level]
            )


@app.task
def process_automatic_contributions():
    """
    processes contributions for those whose contribution is due in 1 day or less and who have set
    UserModel().allow_automatic_contribution to True and who have enough balance in either their Orange Wallet or MTN
    wallet.
    In the event of failure or success, they are informed by email and/or sms.
    """

    # Get the list of users whose contribution is due in less than or equal to 1 day
    queryset = LevelModel.objects.filter(
        next_payment__isnull=False, user__allow_automatic_contribution=True
    ).annotate(
        duration=ExpressionWrapper(F('next_payment') - timezone.now(), DurationField())
    ).annotate(
        day=Extract('duration', 'day'), hour=Extract('duration', 'hour'), minute=Extract('duration', 'minute')
    ).filter(
        day__lte=1
    )

    if queryset:
        _nsp = NSP()
        for obj in queryset:
            level = obj.level
            amount = LEVEL_CONTRIBUTIONS[level]
            processing_fee = amount * WALLET_CONTRIBUTION_PROCESSING_FEE_RATE
            nsp = ''
            total = D(amount) + D(processing_fee)
            recipient = get_upline_to_pay_upgrade_contribution(user_id=obj.user.id, level=level)
            sender_tel = ''
            # Check if there is sufficient funds in the wallet.
            if wallet.balance(user=obj.user, nsp=_nsp.orange()) >= total:
                nsp = _nsp.orange_wallet()
                sender_tel = obj.user.tel2.national_number
            elif wallet.balance(user=obj.user, nsp=_nsp.mtn()) >= total:
                nsp = _nsp.mtn_wallet()
                sender_tel = obj.user.tel1.national_number
            else:  # Insufficient funds, send them failed mails/sms
                mailer_services.send_auto_wallet_contribution_failed_email.delay(
                    user_id=obj.user.id, level=level, amount=amount
                )
                mailer_services.send_auto_wallet_contribution_failed_email.delay(
                    user_id=obj.user.id, level=level, amount=amount
                )

            if nsp == _nsp.orange_wallet() or nsp == _nsp.mtn_wallet():
                if (nsp == _nsp.orange_wallet() and obj.user.tel2 and obj.user.tel2_is_verified) or \
                        (nsp == _nsp.mtn_wallet() and obj.user.tel1 and obj.user.tel1_is_verified):
                    # Process the contribution from either orange_wallet or mtn_wallet.
                    response = process_contribution(
                        user_id=obj.user.id, recipient_id=recipient.id, level=level, nsp=nsp,
                        processing_fee=processing_fee
                    )

                    if response['status'] == trans_status.success():
                        pass
                    else:
                        mailer_services.send_auto_wallet_contribution_failed_email.delay(
                            user_id=obj.user.id, level=level, amount=amount
                        )
                        mailer_services.send_auto_wallet_contribution_failed_sms.delay(
                            user_id=obj.user.id, level=level, amount=amount
                        )
                else:
                    mailer_services.send_auto_wallet_contribution_failed_email.delay(
                        user_id=obj.user.id, level=level, amount=amount
                    )
                    mailer_services.send_auto_wallet_contribution_failed_email.delay(
                        user_id=obj.user.id, level=level, amount=amount
                    )
            else:
                # Simply pass because the email/sms have already been sent to the user.
                pass


@app.task
def process_subscription_update(user_id, package_id, subscription_type, nsp, user_account_id=None):
    # Function responsible for processing user account subscriptions
    # Returns True on success and False on failure
    user = UserModel().objects.none()
    admin_user = UserModel().objects.none()
    package = AccountPackage.objects.none()
    user_account = None

    try:
        user = UserModel().objects.get(pk=user_id)
        admin_user = UserModel().objects.filter(is_admin=True).order_by('username')[:1].get()
    except UserModel().DoesNotExist:
        return False

    try:
        package = AccountPackage.objects.get(pk=package_id)
    except AccountPackage.DoesNotExist:
        return False

    if subscription_type not in [
        user_account_subscription_type.annually(), user_account_subscription_type.monthly()
    ]:
        return False

    if nsp not in [service_provider.mtn_wallet(), service_provider.orange()]:
        return False

    if user_account_id:
        user_account = user_account_manager.get_user_account(user_account_id)
    elif user.user_account_id:
        user_account = user_account_manager.get_user_account_user_list(user.user_account_id)
    else:
        user_account = user_account_manager.add_user_to_user_account(user=user)

    if not user_account:
        return False

    else:
        _nsp = None
        amount = 0.00
        processing_fee = 0.00
        sender_tel = None
        recipient_tel = None

        if nsp == service_provider.orange_wallet():
            _nsp = service_provider.orange()
            sender_tel = user.tel2.national_number
            recipient_tel = admin_user.tel2.national_number
        elif nsp == service_provider.mtn_wallet():
            _nsp = service_provider.mtn()
            sender_tel = user.tel1.national_number
            recipient_tel = admin_user.tel1.national_number
        balance = wallet_manager.balance(user=user, nsp=_nsp)

        if subscription_type == user_account_subscription_type.monthly():
            amount = package.monthly_subscription
        elif subscription_type == user_account_subscription_type.annually():
            amount = package.annual_subscription

        if D(balance) < D(amount):
            return False
        else:
            information = _("%(package_name)s package subscription through %(nsp)s by %(username)s.") % {
                'package_name': package.name.upper(), 'nsp': _nsp.upper(), 'username': user.username
            }
            response = wallet_manager.transfer(
                sender=user, recipient=admin_user, amount=amount, information=information, nsp=_nsp,
                sender_description=trans_description.purchase(),
                recipient_description=trans_description.user_account_subscription(),
                sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=processing_fee
            )
            if response['status'] == trans_status.success():
                r = user_account_manager.update_subscription(
                    user_account_id=user_account.id, package_id=package_id, subscription=subscription_type,
                )
                return True if r else False
            else:
                return False


@app.task
def deactivate_users_with_due_package_subscription():
    user_accounts = user_account_manager.deactivate_over_due_subscriptions()
    for user_account in user_accounts:
        user_list = user_account_manager.get_user_account_user_list(user_account.id)
        for user in user_list:
            if user.email:
                mailer_services.send_user_account_subscription_deactivation_email.delay(
                    username=user.username, package_name=user_account.package.name, email=user.email
                )

    return user_accounts.count()


@app.task
def send_package_subscription_reminder():
    user_accounts = user_account_manager.get_user_accounts_to_send_subscription_reminder()
    for user_account in user_accounts:
        user_list = user_account_manager.get_user_account_user_list(user_account.id)
        duration = _("%(day)s day(s) %(hour)s hour(s)") % {'day': user_account.day, 'hour': user_account.hour}
        for user in user_list:
            if user.email:
                mailer_services.send_user_account_subscription_reminder_email.delay(
                    username=user.username, package_name=user_account.package.name, email=user.email, duration=duration
                )
    return user_accounts.count()


