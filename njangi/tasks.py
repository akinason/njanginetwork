import datetime
from purse.models import WalletManager
from njangi.models import LevelModel, FailedOperations
from njangi.core import get_level_contribution_amount
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db.models import Q, F, ExpressionWrapper, DateTimeField, DurationField
from django.db.models.functions import Extract
from purse.models import WalletTransStatus, WalletTransMessage, WalletTransDescription
from njangi.models import NSP, CONTRIBUTION_INTERVAL_IN_DAYS
from purse import services as api_services
from njanginetwork.celery import app
from main.core import FailedOperationTypes, TransactionStatus
from mailer import services as mailer_services
from django.contrib.auth import get_user_model as UserModel
from njangi.models import LEVEL_CONTRIBUTIONS, WALLET_CONTRIBUTION_PROCESSING_FEE_RATE
from njangi.core import get_upline_to_pay_upgrade_contribution

wallet = WalletManager()
trans_status = WalletTransStatus()
trans_message = WalletTransMessage()
trans_description = WalletTransDescription()
service_provider = NSP()
fot = FailedOperationTypes()
TRANSStatus = TransactionStatus()


def process_payout_(
    recipient_id, amount, nsp, processing_fee=0.00, is_failed_operation=False, failed_operation_id=None,
    is_contribution=False
):
    """
    processes withdrawal from the recipient's wallet to his/her Mobile money account.
    :param recipient_id:
    :param amount: Amount requested for withdrawal.
    :param nsp: Network Service Provider.
    :param processing_fee: The withdrawal processing fee.
    :param is_failed_operation
    :param failed_operation_id
    :param is_contribution: Determines whether its a contribution or not. Used to decide whether to send success sms
            and email or not. In case is_contribution=True, success email and sms are not sent because
            process_contribution_response would have sent them.
    :return:
    """
    try:
        recipient = UserModel().objects.get(pk=recipient_id)

        if wallet.balance(user=recipient, nsp=nsp) >= (amount + processing_fee):
            # Check if the user has a valid nsp telephone number
            if nsp.upper() == service_provider.mtn().upper():
                if recipient.tel1 and recipient.tel1_is_verified:
                    # Process the transaction
                    response = api_services.request_momo_payout(
                        phone_number=recipient.tel1.national_number, amount=amount
                    )
                    if response['status'].upper() == trans_status.success().upper():
                        information = _('withdrawal through %(nsp)s mobile money.') % {'nsp': nsp}
                        wallet_response = wallet.withdraw(user=recipient, amount=amount, nsp=nsp, charge=0.00,
                                                          tel=recipient.tel1.national_number, information=information,
                                                          thirdparty_reference=response['transactionId'],
                                                          )
                        if wallet_response['status'] == trans_status.failed():
                            # do a force withdraw
                            wallet_response = wallet.withdraw(user=recipient, amount=amount, nsp=nsp, charge=0.00,
                                                              tel=recipient.tel1.national_number,
                                                              thirdparty_reference=response['transactionId'],
                                                              information=information, force_withdraw=True
                                                              )
                            if not is_contribution:  # Only send sms and email if its not a contribution.
                                mailer_services.send_wallet_withdrawal_email.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                                mailer_services.send_wallet_withdrawal_sms.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                            return wallet_response  # Inner wallet response
                        else:
                            if not is_contribution:
                                mailer_services.send_wallet_withdrawal_email.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                                mailer_services.send_wallet_withdrawal_sms.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                            return wallet_response  # Outer wallet response

                    else:   # if the api response is not successful.
                            # Send a notification mail to the recipient
                            status = trans_status.failed()
                            message = trans_message.failed_message()
                            mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient.id, message=message,
                                                                                status=status)
                            mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient.id, message=message,
                                                                              status=status)
                            response = {
                               'status': status,
                               'message': message
                            }
                            return response

                else:
                    # Send a notification mail to the recipient and set the transaction status to provide_contact or
                    # simply increase the number of attempts if it's a previously failed operation.
                    if is_failed_operation:
                        try:
                            failed_operation = FailedOperations.objects.filter(pk=failed_operation_id).get()
                            failed_operation.attempts += 1
                            failed_operation.save()
                        except FailedOperations.DoesNotExist:
                            FailedOperations.objects.create(
                                user=recipient, amount=amount, nsp=nsp, processing_fee=processing_fee,
                                status=TRANSStatus.provide_contact(), operation_type=fot.withdrawal()
                            )
                    else:
                        FailedOperations.objects.create(
                            user=recipient, amount=amount, nsp=nsp, processing_fee=processing_fee,
                            status=TRANSStatus.provide_contact(), operation_type=fot.withdrawal()
                        )
                    message = trans_message.provide_contact_and_receive_payments() % {'nsp': nsp.upper()}
                    status = trans_status.pending()
                    if not is_failed_operation:
                        mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient.id, message=message,
                                                                                  status=status)
                        mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient.id, message=message,
                                                                                status=status)
                    response = {
                        'status': status,
                        'message': message,
                    }
                    return response
            elif nsp.upper() == service_provider.orange().upper():
                if recipient.tel2 and recipient.tel2_is_verified:
                    # Process the transaction
                    response = api_services.request_orange_money_payout(phone_number=recipient.tel2.national_number, amount=amount)
                    if response['status'].upper() == trans_status.success().upper():
                        information = _('withdrawal through %(nsp)s mobile money.') % {'nsp': nsp}
                        wallet_response = wallet.withdraw(user=recipient, amount=amount, nsp=nsp, charge=0.00,
                                                          tel=recipient.tel2.national_number,
                                                          thirdparty_reference=response['transactionId'],
                                                          information=information
                                                          )
                        if wallet_response['status'] == trans_status.failed():
                            # do a force withdraw
                            wallet_response = wallet.withdraw(user=recipient, amount=amount, nsp=nsp, charge=0.00,
                                                              tel=recipient.tel1.national_number,
                                                              thirdparty_reference=response['transactionId'],
                                                              information=information, force_withdraw=True
                                                              )
                            if not is_contribution:  # Only send email and sms if its not a contribution.
                                mailer_services.send_wallet_withdrawal_email.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                                mailer_services.send_wallet_withdrawal_sms.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                            return wallet_response  # Inner wallet response
                        else:
                            if not is_contribution:
                                mailer_services.send_wallet_withdrawal_email.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                                mailer_services.send_wallet_withdrawal_sms.delay(
                                    user_id=recipient.id, amount=amount, processing_fee=0.00, nsp=nsp
                                )
                            return wallet_response  # Outer wallet response

                    else:  # if the api response to orange is not successful.
                            # Send a notification mail to the recipient
                            status = trans_status.failed()
                            message = trans_message.failed_message()
                            if not is_failed_operation:
                                mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient.id,
                                                                                          message=message,
                                                                                          status=status)
                                mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient.id,
                                                                                        message=message,
                                                                                        status=status)
                            response = {
                               'status': status,
                               'message': message
                            }
                            return response

                else:
                    # Send a notification mail to the recipient and set the transaction status to provide_contact or just
                    # increase the number of attempts if it's a previously failed transaction.
                    if is_failed_operation:
                        try:
                            failed_operation = FailedOperations.objects.get(pk=failed_operation_id)
                            failed_operation.attempts += 1
                            failed_operation.save()
                        except FailedOperations.DoesNotExist:
                            FailedOperations.objects.create(
                                user=recipient, amount=amount, nsp=nsp, processing_fee=processing_fee,
                                status=TRANSStatus.provide_contact(), operation_type=fot.withdrawal()
                            )
                    else:
                        FailedOperations.objects.create(
                            user=recipient, amount=amount, nsp=nsp, processing_fee=processing_fee,
                            status=TRANSStatus.provide_contact(), operation_type=fot.withdrawal()
                        )
                    message = trans_message.provide_contact_and_receive_payments() % {'nsp': nsp}
                    status = trans_status.pending()
                    if not is_failed_operation:
                        mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient_id, message=message,
                                                                                  status=status)
                        mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient_id, message=message,
                                                                                status=status)
                    response = {
                        'status': status,
                        'message': message
                    }
                    return response

            else:
                status = trans_status.failed()
                message = trans_message.insufficient_balance_message()
                if not is_failed_operation:
                    mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient.id, message=message,
                                                                              status=status)
                    mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient.id, message=message,
                                                                        status=status)
                response = {
                    'status': status,
                    'message': message
                }
                return response

        else:  # if the balance is insufficient
            status = trans_status.failed()
            message = trans_message.insufficient_balance_message()
            if not is_failed_operation:
                mailer_services.send_wallet_withdrawal_failed_email.delay(user_id=recipient.id, message=message,
                                                                          status=status)
                mailer_services.send_wallet_withdrawal_failed_sms.delay(user_id=recipient_id, message=message,
                                                                        status=status)
            response = {
                'status': status,
                'message': message
            }
            return response
    except UserModel().DoesNotExist:
        response = {
            'status': trans_status.failed(),
            'message': trans_message.failed_message()
        }
        return response


@app.task
def process_payout(recipient_id, amount, nsp, processing_fee=0.00, is_contribution=False):
    return process_payout_(
        recipient_id=recipient_id, amount=amount, nsp=nsp, processing_fee=processing_fee,
        is_contribution=is_contribution
    )


@app.task
def process_contribution(user_id, recipient_id, level, amount, nsp, sender_tel, processing_fee=0.00,
                         thirdparty_reference=None):
    """
    Processes the contribution and return the status of the transaction.
    0. Request cash deposit from mobile money API
    1. Fund the users wallet if nsp=orange or mtn. (ignored if nsp=mtn_wallet or nsp=orange_wallet)
    2. Transfer funds from user's wallet to recipient's wallet.
    3. Request a withdrawal from the user's wallet.
    4. Upgrade the user if user's level is less than this level.
    5. Update user's LevelModel for last_payment, total_sent and update recipient's LevelModel with total_received.
    """
    user = UserModel().objects.get(pk=user_id)
    recipient = UserModel().objects.get(pk=recipient_id)
    loading_amount = amount + processing_fee
    loading_charge = processing_fee
    contribution_amount = get_level_contribution_amount(level)

    recipient_charge = 0.00
    contribution_charge = 0.00
    recipient_amount = get_level_contribution_amount(level)

    params = {'level': level, 'sender': user.username, 'recipient': recipient.username}
    information = _('level %(level)s contribution from %(sender)s to %(recipient)s.') % params

    sender_tel = sender_tel
    recipient_tel = None
    thirdparty_reference = thirdparty_reference
    nsp = nsp

    if nsp == service_provider.mtn() or nsp == service_provider.orange():
        api_response = {}
        if nsp == service_provider.mtn() and user.tel1 and user.tel1_is_verified:
            sender_tel = user.tel1.national_number
            api_response = api_services.request_momo_deposit(sender_tel, amount=loading_amount)
        elif nsp == service_provider.orange() and user.tel2 and user.tel2_is_verified:
            sender_tel = user.tel2.national_number
            api_response = api_services.request_orange_money_deposit(sender_tel, amount=loading_amount)
        else:
            mailer_services.send_nsp_contribution_failed_email.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
            mailer_services.send_nsp_contribution_failed_sms.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
            return {'status': trans_status.failed(), 'message': trans_message.failed_message()}
        if api_response and api_response['status'] == trans_status.success():
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
                                              processing_fee=processing_fee
                                              )
                return {'status': trans_status.success(), 'message': trans_message.success_message()}
            else:

                FailedOperations.objects.create(
                    user=user, recipient=recipient, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
                    processing_fee=processing_fee, transaction_id=api_response['transactionId'],
                    status=trans_status.pending(), operation_type=fot.contribution(),
                    message=response['message'], response_status=response['status']
                )
                mailer_services.send_nsp_contribution_pending_email.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
                mailer_services.send_nsp_contribution_pending_sms.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
                return {'status': trans_status.pending(), 'message': trans_message.failed_message()}
        else:
            mailer_services.send_nsp_contribution_failed_email.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
            mailer_services.send_nsp_contribution_failed_sms.delay(user_id=user.id, nsp=nsp, level=level, amount=amount)
            return {'status': trans_status.failed(), 'message': trans_message.failed_message()}
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
                                          processing_fee=processing_fee
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
                                          processing_fee=processing_fee
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


def process_contribution_response(response, user, recipient, level, recipient_amount, nsp, processing_fee):
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
            njangi_level.last_payment = timezone.now()
            njangi_level.next_payment = timezone.now() + datetime.timedelta(days=CONTRIBUTION_INTERVAL_IN_DAYS)
        njangi_level.save()

        # Update the recipient's LevelModel's total_received.
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received += recipient_amount
        njangi_level.save()

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
        process_payout.delay(recipient_id=recipient.id, amount=recipient_amount, nsp=nsp, is_contribution=True)

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


@app.task
def process_wallet_load(user_id, amount, nsp, charge=0.00):
    loading_amount = amount + charge
    user = UserModel().objects.get(pk=user_id)
    information = _('wallet load through %s mobile money') % nsp.upper()
    if nsp == service_provider.mtn():
        if user.tel1 and user.tel1_is_verified:
            """Process loading operation"""
            response = api_services.request_momo_deposit(phone_number=user.tel1.national_number, amount=loading_amount)
            if response['status'] == trans_status.success():
                # Proceed to update the user's wallet.
                load_response = wallet.load(
                    user=user, amount=loading_amount, nsp=nsp, description=trans_description.wallet_load(),
                    charge=charge, tel=user.tel1.national_number, thirdparty_reference=response['transactionId'],
                    information=information,
                )
                if load_response['status'] == trans_status.failed():
                    # add the transaction to FailedOperations and let celery take over.
                    FailedOperations.objects.create(
                        user=user, amount=loading_amount, nsp=nsp, processing_fee=charge,
                        status=TRANSStatus.pending(), operation_type=fot.account_load_api_processed(),
                        transaction_id=response['transactionId']
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
                    return load_response
            else:
                # Inform the user of a failed operation.
                mailer_services.send_wallet_load_failed_email.delay(user_id=user.id, amount=amount,
                                                                    processing_fee=charge, nsp=nsp)
                mailer_services.send_wallet_load_failed_sms.delay(user_id=user.id, amount=amount, processing_fee=charge,
                                                                  nsp=nsp)
                response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
                return response
        else:
            """Inform of unverified MTN Number"""
            mailer_services.send_unverified_phone_number_mail(user_id=user_id, nsp=nsp)
            mailer_services.send_unverified_phone_number_sms.delay(user_id=user_id, nsp=nsp)
            response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
            return response

    elif nsp == service_provider.orange():
        if user.tel2 and user.tel2_is_verified:
            """Process loading operation"""
            response = api_services.request_orange_money_deposit(phone_number=user.tel2.national_number,
                                                                 amount=loading_amount)
            if response['status'] == trans_status.success():
                # Proceed to update the user's wallet.
                load_response = wallet.load(
                    user=user, amount=loading_amount, nsp=nsp, description=trans_description.wallet_load(),
                    charge=charge, tel=user.tel2.national_number, thirdparty_reference=response['transactionId'],
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
                    return load_response
            else:
                # Inform the user of a failed operation.
                mailer_services.send_wallet_load_failed_email.delay(user_id=user.id, amount=amount,
                                                                    processing_fee=charge, nsp=nsp)
                mailer_services.send_wallet_load_failed_sms.delay(user_id=user.id, amount=amount, processing_fee=charge,
                                                                  nsp=nsp)
                response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
                return response
        else:
            """Inform of unverified MTN Number"""
            mailer_services.send_unverified_phone_number_mail(user_id=user_id, nsp=nsp)
            mailer_services.send_unverified_phone_number_sms.delay(user_id=user_id, nsp=nsp)
            response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
            return response
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
            duration = str(obj.day) + _('day(s)') + ' ' + str(obj.hour) + _('hour(s)')

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
    processes contributions for those whose contribution is due in 1 minute and who have set
    UserModel().allow_automatic_contribution to True and who have enough balance in either their Orange Wallet or MTN
    wallet.
    In the event of failure or success, they are informed by email and/or sms.
    """

    # Get the list of users whose contribution is due in 1 minute
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
            total = amount + processing_fee
            recipient = get_upline_to_pay_upgrade_contribution(user_id=obj.user.id, level=level)
            sender_tel = ''
            # Check if there is sufficient funds in the wallet.
            if wallet.balance(user=obj.user, nsp=_nsp.orange()) >= total:
                nsp = _nsp.orange_wallet()
                sender_tel = obj.user.tel2
            elif wallet.balance(user=obj.user, nsp=_nsp.mtn()) >= total:
                nsp = _nsp.mtn_wallet()
                sender_tel = obj.user.tel1
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
                        user_id=obj.user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp,
                        sender_tel=sender_tel.national_number, processing_fee=processing_fee
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
