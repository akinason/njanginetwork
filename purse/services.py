import decimal
import requests

from django.contrib.auth import get_user_model as UserModel
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

# from administration.core import site_information
from main.core import NSP
from main.notification import notification
from njanginetwork import settings
from njanginetwork.celery import app
from purse.models import (
    TransactionStatus, WalletTransMessage, MobileMoneyManager, MMRequestType, MOMOAPIProvider, WalletManager,
    WalletTransDescription
)
from purse.lib import monetbil


trans_status = TransactionStatus()
trans_description = WalletTransDescription()
trans_message = WalletTransMessage()
wallet_manager = WalletManager()
mm_manager = MobileMoneyManager()
mm_request_type = MMRequestType()
momoapi_provider = MOMOAPIProvider()
_nsp = NSP()
D = decimal.Decimal


@app.task
def request_momo_deposit(phone_number, amount, user_id, purpose, nsp, level, recipient_id=None, charge=None,
                         invoice_number=None):
    user = UserModel().objects.get(pk=user_id)
    recipient = None

    if recipient_id:
        recipient = UserModel().objects.get(pk=recipient_id)

    payment_log = mm_manager.send_request(
        request_type=mm_request_type.deposit(), amount=amount, provider=momoapi_provider.monetbil(),
        tel=phone_number, nsp=nsp, user=user, recipient=recipient, purpose=purpose, level=level, charge=charge,
        invoice_number=invoice_number
    )

    response = {
        'status': trans_status.success(),
        'message': trans_message.success_message(),
        'tracker_id': payment_log.tracker_id, 'transactionId': payment_log.id}
    return response


@app.task
def request_momo_payout(phone_number, amount, user_id, purpose, nsp, recipient_id=None, processing_fee=0.00, level=None,
                        invoice_number=None):

    # if not site_information.allow_withdrawal:
    #     response = {
    #         'status': trans_status.failed(),
    #         'message': trans_message.failed_message(),
    #         }
    #     return response

    user = UserModel().objects.get(pk=user_id)
    recipient = None

    if recipient_id:
        recipient = UserModel().objects.get(pk=recipient_id)

    payment_log = mm_manager.send_request(
        request_type=mm_request_type.payout(), amount=amount, provider=momoapi_provider.monetbil(),
        tel=phone_number, nsp=nsp, user=user, recipient=recipient, purpose=purpose, level=level, charge=processing_fee,
        invoice_number=invoice_number
    )

    # freeze the amount in the user's account.
    information = _('Funds withdrawal though %s mobile money') % nsp.upper()
    wallet_manager.withdraw(
        user=recipient, amount=amount, nsp=nsp, charge=processing_fee, tel=phone_number,
        tracker_id=payment_log.tracker_id, information=information, force_withdraw=True,
        status=trans_status.pending(),
    )

    # Send a payout request to Monetbil
    phone = str(237) + str(phone_number)
    monetbil.send_payout_request(amount=amount, phone=phone, tracker_id=payment_log.tracker_id)

    response = {
        'status': trans_status.success(),
        'message': trans_message.success_message(),
        'tracker_id': payment_log.tracker_id, 'transactionId': payment_log.id}
    return response


def process_through_afkanerd(log, phone_number, amount, operation_type):
    callback_url = get_afkanerd_callback_url(log.uuid)
    url = settings.AFKANERD_MOMO_URL
    sid = settings.AFKANERD_AUTH_SID
    params = {
        'client': phone_number,
        'amount': amount,
        'sid': sid,
        'email': settings.AFKANERD_AUTH_EMAIL,
        'type': mm_request_type.afkanerd_payout() if operation_type == mm_request_type.payout() else mm_request_type.afkanerd_deposit(),
        'trackerId': log.tracker_id,
        'callbackUrl': callback_url
    }

    returnable_response = ""

    try:
        r = requests.post(url=url, data=params, timeout=(60, 60))
        response = r.json()
        # import random
        # response = {'statusCode': 200, 'userAuth': 'valid', 'trackerId': log.tracker_id,
        #             'serverResponse': 'Everything moving on', 'uniqueId': random.randint(1000, 9999)}
        # Treatment of the response
        status_code = 0
        user_auth = ''
        server_response = ''
        error_message = ''
        transaction_state = ''
        tracker_id = ''
        unique_id = ''

        try:
            status_code = response['statusCode']
        except Exception:
            pass
        try:
            user_auth = response['userAuth']
        except Exception:
            pass
        try:
            server_response = response['serverResponse']
        except Exception:
            pass
        try:
            error_message = response['errorMessage']
        except Exception:
            pass
        try:
            transaction_state = response['transactionState']
        except Exception:
            pass
        try:
            tracker_id = response['trackerId']
        except Exception:
            pass
        try:
            unique_id = response['uniqueId']
        except Exception:
            pass

        if int(status_code) == 402:  # This means we do not have enough balance in the AFKANERD wallet.
            # There will be no callback so consider the transaction as failed and complete.
            wallet_manager.update_status(
                status=trans_status.failed(), tracker_id=log.tracker_id
            )
            mm_transaction = mm_manager.get_response(
                mm_request_id=log.id, response_status=trans_status.failed(), response_code=status_code,
                message=error_message, response_transaction_date=timezone.now(), user_auth=user_auth,
                server_response=server_response, unique_id=unique_id, is_complete=True,
                callback_server_response=server_response, callback_status_code=status_code
            )
            notification().templates.transaction_failed(
                user_id=mm_transaction.user.id, purpose=mm_transaction.purpose,
                amount=mm_transaction.amount,
                nsp=mm_transaction.nsp
            )
        else:
            mm_manager.get_response(
                mm_request_id=log.id, response_status=transaction_state, response_code=status_code,
                message=error_message,
                response_transaction_date=timezone.now(), user_auth=user_auth, server_response=server_response,
                unique_id=unique_id
            )
        returnable_response = {
            'status': trans_status.success() if (
            int(status_code) and int(status_code) == 102) else trans_status.failure(),
            'message': trans_message.success_message() if (
            int(status_code) and int(status_code) == 102) else trans_message.failed_message(),
            'tracker_id': log.tracker_id, 'status_code': status_code, 'transactionId': log.id,
            'unique_id': unique_id,
        }
    except Exception as e:
        returnable_response = {
            'status': trans_status.failure(), 'message': trans_message.failed_message(),
            'status_code': 404, 'error': e
        }
    return returnable_response


def get_afkanerd_callback_url(uuid):
    url = '%(base_url)s%(uuid)s/' % {'base_url': settings.AFKANERD_BASE_CALLBACK_URL, 'uuid': uuid}
    return url

