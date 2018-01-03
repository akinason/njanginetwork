from main.core import FailedOperationTypes, TransactionStatus
from mailer import services as mailer_services
from purse.models import WalletTransStatus, WalletTransMessage, WalletTransDescription
from purse.models import WalletManager
from njangi.models import NSP
from njangi.tasks import process_payout_
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from njangi.models import FailedOperations

wallet = WalletManager()
trans_status = WalletTransStatus()
trans_message = WalletTransMessage()
trans_description = WalletTransDescription()
service_provider = NSP()
fot = FailedOperationTypes()
TRANSStatus = TransactionStatus()


@receiver(post_save, sender=FailedOperations)
def email_admin(sender, instance, **kwargs):
    """
    Send an email to admin each time a new record is added to the FailedOperations model.
    """
    mailer_services.send_failed_operation_admin_email(instance_id=instance.id)


@receiver(post_save, sender=FailedOperations)
def process_failed_withdrawals(sender, instance, **kwargs):
    """
    Processes withdrawals which failed as a result of the fact that the user does not have the NSP account or the NSP
    account is not verified. They have a status of 'provide_contact' and an operation_type of 'withdrawal' on the
    FailedOperations Model.
    """

    transaction = instance
    if transaction.status == TRANSStatus.provide_contact() and transaction.operation_type == fot.withdrawal():

        if transaction.attempts >= 10:
            return False
        else:
            response = process_payout_(
                recipient_id=transaction.user.id, amount=transaction.amount, nsp=transaction.nsp,
                processing_fee=transaction.processing_fee, is_failed_operation=True, failed_operation_id=transaction.id
            )
            if response['status'] == trans_status.success():
                transaction.resolved_on = timezone.now()
                transaction.status = trans_status.complete()
                transaction.attempts += 1
                transaction.save()
            else:
                transaction.attempts += 1
                transaction.save()
    else:
        return False


@receiver(post_save, sender=FailedOperations)
def process_failed_wallet_load_after_success_api_response(sender, instance, **kwargs):
    """
    Processes transaction who were already processed by the mobile money API but for one reason or the other, did not
    update the user's wallet. Their status is 'pending' and operation_type is 'account_load_api_processed'
    """

    transaction = instance
    if transaction.status == TRANSStatus.pending() and transaction.operation_type == fot.account_load_api_processed():

        # If the user does not have tel1 or a verified tel1 then just increase the attempts to solve the problem.
        if transaction.attempts >= 10:
            return False
        if transaction.nsp == service_provider.mtn() and not transaction.user.tel1 and not \
                transaction.user.tel1_is_verified:
            transaction.attempts += 1
            transaction.save()
        elif transaction.nsp == service_provider.orange() and not transaction.user.tel2 and not \
                transaction.user.tel2_is_verified:
            transaction.attempts += 1
            transaction.save()
        else:
            tel = ''
            if transaction.nsp == service_provider.mtn():
                tel = transaction.user.tel1.national_number
            elif transaction.nsp == service_provider.orange():
                tel = transaction.user.tel2.national_number
            information = _('wallet load through %s mobile money') % transaction.nsp.upper()
            load_response = wallet.load(
                user=transaction.user, amount=transaction.amount, nsp=transaction.nsp,
                description=trans_description.wallet_load(), charge=transaction.processing_fee,
                tel=tel, information=information, thirdparty_reference=transaction.transaction_id
            )
            if load_response['status'] == trans_status.success():
                # if the operation is loaded successfully, update the status of the operation and send email/sms.
                transaction.status == trans_status.complete()
                transaction.resolved_on = timezone.now()
                transaction.save()

                mailer_services.send_wallet_load_success_email(
                    user_id=transaction.user.id, amount=transaction.amount,
                    processing_fee=transaction.processing_fee
                )
                mailer_services.send_wallet_load_success_sms(
                    user_id=transaction.user.id, amount=transaction.amount,
                    processing_fee=transaction.processing_fee
                )
            else:
                transaction.attempts += 1
                transaction.save()
    else:
        return False

# @receiver(post_save, sender=FailedOperations)
# def process_failed_contributions_after_success_api_response(sender, instance, **kwargs):
#     """
#     Processes transactions who have already been processed by the API and for one reason or the other, have not been
#     successful in loading the user's wallet and contributing + processing the payout to the recipient.
#     Their status in the FailedOperations Model is 'pending' and operation_type is 'contribution'
#     """
#
