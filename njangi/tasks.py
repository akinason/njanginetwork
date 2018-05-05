import datetime
import decimal

from django.contrib.auth import get_user_model as UserModel
from django.db.models import F, ExpressionWrapper, DurationField
from django.db.models.functions import Extract
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


from mailer import services as mailer_services
from main.core import FailedOperationTypes, TransactionStatus
from njangi.core import get_upline_to_pay_upgrade_contribution, get_contribution_beneficiaries
from njangi.models import (
    LevelModel, FailedOperations, AccountPackage, UserAccountSubscriptionType, UserAccountManager, LEVEL_CONTRIBUTIONS,
    WALLET_CONTRIBUTION_PROCESSING_FEE_RATE, NSP, CONTRIBUTION_INTERVAL_IN_DAYS, RemunerationPlan
)
from main.notification import notification
from njanginetwork.celery import app
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
def process_nsp_contribution(tracker_id):
    """
    Process contributions not deducting the money from user's wallet but rather from a mobile money transaction.
    :param tracker_id: the tracker_id of the transaction from MobileMoney Model
    :return: a dict response {status, message}: success or failed
     Processes a contribution deducting the money from the user's wallet but ensuring the deposit was successful.
        1) Check if the deposit was successful
        2) Update the user's wallet balance
        3) Process wallet contribution
    """
    if not momo_manager.is_valid(tracker_id=tracker_id):
        return {'status': trans_status.failed(), 'message': trans_message.invalid_transaction()}

    # 1 - Check if the deposit was successful
    mm_transaction = momo_manager.get_mm_transaction(tracker_id=tracker_id)
    api_callback_status_code = mm_transaction.callback_status_code

    if mm_transaction.is_complete or not (mm_transaction.purpose == momo_purpose.contribution() or
                                          mm_transaction.purpose == momo_purpose.signup_contribution()) or not \
            mm_transaction.request_type == momo_request_type.deposit():

        response = {
            'status': trans_status.failed(), 'message': trans_message.already_treated_transaction(),
            'tracker_id': tracker_id
        }
        notification().templates.transaction_failed(
            user_id=mm_transaction.user.id, purpose=mm_transaction.purpose, amount=mm_transaction.amount,
            nsp=mm_transaction.nsp
        )
        return response
    if api_callback_status_code and (not int(api_callback_status_code) == 200):
        response = {
            'status': trans_status.failed(), 'message': trans_message.failed_message(), 'tracker_id': tracker_id
        }
        mailer_services.send_nsp_contribution_failed_email.delay(user_id=mm_transaction.user.id, nsp=mm_transaction.nsp,
                                                                 level=mm_transaction.level, amount=mm_transaction.amount)
        mailer_services.send_nsp_contribution_failed_sms.delay(user_id=mm_transaction.user.id, nsp=mm_transaction.nsp,
                                                               level=mm_transaction.level, amount=mm_transaction.amount)
        notification().templates.transaction_failed(
            user_id=mm_transaction.user.id, purpose=mm_transaction.purpose, amount=mm_transaction.amount,
            nsp=mm_transaction.nsp
        )
        return response

    # 2 - Update the user's wallet balance
    response = wallet_manager.load(
        user=mm_transaction.user, amount=mm_transaction.amount, nsp=mm_transaction.nsp,
        description=trans_description.wallet_load(),
        information=_('cash deposit through %s mobile money.') % mm_transaction.nsp.upper(), tel=mm_transaction.tel,
    )
    if response['status'] == trans_status.success():
        # mark the transaction as complete.
        mm_transaction.is_complete = True
        mm_transaction.save()

    # 3 - process wallet contribution
        res = process_wallet_contribution(
            level=mm_transaction.level, nsp=mm_transaction.nsp, user_id=mm_transaction.user.id,
            processing_fee=mm_transaction.charge
        )
        return res
    else:
        # But if the operation is not successful, then something is really wrong. This is not suppose to happen.
        # however, keep track of it.
        FailedOperations.objects.create(
            user=mm_transaction.user, recipient=mm_transaction.recipient, level=mm_transaction.level,
            amount=mm_transaction.amount, nsp=mm_transaction.nsp, sender_tel=mm_transaction.amount,
            processing_fee=mm_transaction.charge, transaction_id=mm_transaction.tracker_id,
            status=trans_status.pending(), operation_type=fot.contribution(),
            message=response['message'], response_status=response['status']
        )
        notification().templates.contribution_in_process(
            user_id=mm_transaction.user.id, purpose=mm_transaction.purpose, amount=mm_transaction.amount,
            nsp=mm_transaction.nsp
        )
        return response


@app.task
def process_wallet_contribution(level, nsp, user_id, processing_fee=0.00):
    """
    :param level: The level for which the contribution is intended for
    :param nsp: The Network Service Provider (mtn_wallet or orange_wallet)
    :param user_id: The user_id of the user doing the contribution
    :param processing_fee: contribution processing fees
    :return: a dict response. {status, message}
        Processes a contribution deducting the money from the user's wallet.
        1) Ensure the user has sufficient funds
        2) Generate the beneficiary's list
        3) Process the contribution
        4) Update statuses and Send notifications, emails, sms
    """
    _nsp = ""
    if nsp == service_provider.orange() or nsp == service_provider.orange_wallet():
        _nsp = service_provider.orange()
    elif nsp == service_provider.mtn() or nsp == service_provider.mtn_wallet():
        _nsp = service_provider.mtn()
    remuneration = RemunerationPlan.objects.get(level=level)
    user = UserModel().objects.get(id=user_id)
    balance = wallet.balance(user=user, nsp=_nsp)

    # 1 - Check balance
    if balance < (D(remuneration.contribution_amount) + D(processing_fee)):
        return {'status': trans_status.failed(), 'message': trans_message.insufficient_balance_message()}

    # 2 - Get the beneficiaries of this contribution
    beneficiaries = get_contribution_beneficiaries(contributor=user, level=level)

    if not beneficiaries:
        return {'status': trans_status.failed(), 'message': trans_message.insufficient_balance_message()}

    # 3 - contribute
    contribution_response = wallet_manager.contribute(
        beneficiaries=beneficiaries, nsp=_nsp, processing_fee=processing_fee
    )
    if not contribution_response['status'] == trans_status.success():
        return {'status': trans_status.failed(), 'message': contribution_response['message']}

    # 4 - Update status and send notifications
    update_status_and_send_notifications(beneficiaries=beneficiaries)

    return {'status': trans_status.success(), 'message': trans_message.success_message()}


def update_status_and_send_notifications(beneficiaries):

    # Get done with the contributor.
    user = beneficiaries['contributor']
    level = beneficiaries['level']
    recipient = beneficiaries['recipient']['user']
    contribution_amount = beneficiaries['contribution_amount']
    njangi_level, created = LevelModel.objects.get_or_create(user=user, level=level)
    njangi_level.is_active = True
    njangi_level.recipient = recipient
    njangi_level.amount = contribution_amount
    njangi_level.total_sent = F('total_sent') + D(contribution_amount)
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

    if int(user.level) < int(level):
        user.level = level
        user.save()
    notification().templates.transaction_successful(
        user_id=user.id, purpose="level %s contribution" % level, amount=contribution_amount
    )

    # Now let's proceed to the recipient
    recipient = beneficiaries['recipient']['user']
    recipient_amount = beneficiaries['recipient']['amount']
    if recipient_amount > 0:
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received = F('total_received') + D(recipient_amount)
        njangi_level.save()
        notification().templates.contribution_received(
            user_id=recipient.id, username=user.username, level=level, amount=recipient_amount
        )

    # Now to direct commission
    recipient = beneficiaries['direct_commission']['user']
    recipient_amount = beneficiaries['direct_commission']['amount']
    if recipient_amount > 0:
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received = F('total_received') + D(recipient_amount)
        njangi_level.save()
        notification().templates.commission_received(
            user_id=recipient.id,
            username=user.username, level=level, commission_type="direct commission", amount=recipient_amount
        )

    # Now to velocity reserve
    recipient = beneficiaries['velocity_reserve']['user']
    recipient_amount = beneficiaries['velocity_reserve']['amount']
    if recipient_amount > 0:
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received = F('total_received') + D(recipient_amount)
        njangi_level.save()
        notification().templates.commission_received(
            user_id=recipient.id,
            username=user.username, level=level, commission_type="velocity reserve", amount=recipient_amount
        )

    # Now to company commission
    recipient = beneficiaries['company_commission']['user']
    recipient_amount = beneficiaries['company_commission']['amount']
    if recipient_amount > 0:
        njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
        njangi_level.total_received = F('total_received') + D(recipient_amount)
        njangi_level.save()
        notification().templates.commission_received(
            user_id=recipient.id,
            username=user.username, level=level, commission_type="company commission", amount=recipient_amount
        )

    # Now to network commission
    object_list = beneficiaries['network_commission']
    for obj in object_list:
        recipient = obj['user']
        recipient_amount = obj['amount']
        if recipient_amount > 0:
            njangi_level, created = LevelModel.objects.get_or_create(user=recipient, level=level)
            njangi_level.total_received = F('total_received') + D(recipient_amount)
            njangi_level.save()
            notification().templates.commission_received(
                user_id=recipient.id,
                username=user.username, level=level, commission_type="network commission", amount=recipient_amount
            )


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
                    response = process_wallet_contribution(
                        level=level, nsp=nsp, user_id=obj.user.id, processing_fee=processing_fee
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


