import requests
from njanginetwork import settings
from purse.models import TransactionStatus, WalletTransMessage, MobileMoneyManager, MMRequestType
from mailer.services import send_admin_email
from main.core import NSP
from njanginetwork.celery import app

trans_status = TransactionStatus()
trans_message = WalletTransMessage()
mm_manager = MobileMoneyManager()
mm_request_type = MMRequestType()
_nsp = NSP()


def request_momo_payout(phone_number, amount, user=None):
    _phone_number = str(phone_number).replace(" ", "").replace("+", "")
    _phone_number = int(_phone_number)
    log = log_transaction(
            request_type=mm_request_type.payout, amount=amount, tel=_phone_number, nsp=_nsp.mtn(), user=user
        )
    try:
        url = settings.MOMO_PAYMENT_URL
        email = settings.MOMO_AUTH_EMAIL
        password = settings.MOMO_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
        try:
            log_transaction(mm_request_id=log.id, api_response=response)
        except Exception:
            pass
    except Exception as e:
        message = "MoMo Payout Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_momo_payout:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
        try:
            log_transaction(mm_request_id=log.id, api_response=response)
        except Exception:
            pass
    return response


def request_momo_deposit(phone_number, amount, user=None):
    _phone_number = str(phone_number).replace(" ", "").replace("+", "")
    _phone_number = int(_phone_number)
    log = log_transaction(
            request_type=mm_request_type.deposit, amount=amount, tel=_phone_number, nsp=_nsp.mtn(), user=user
        )
    try:
        url = settings.MOMO_CHECKOUT_URL
        email = settings.MOMO_AUTH_EMAIL
        password = settings.MOMO_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        # r = requests.post(url=url, data=params, timeout=(3.05, 120))
        # response = r.json()
        response = {'status': 'failure', 'message': "HTTPConnectionPool(host='api.webshinobis.com', port=80): Max retries exceeded with url: /api/v1/momo/checkout (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f50882bbb70>: Failed to establish a new connection: [Errno -2] Name or service not known',))"}
        try:
            log_transaction(mm_request_id=log.id, api_response=response)
        except Exception as e:
            print(e)
    except Exception as e:
        message = "MoMo Deposit Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_momo_deposit:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
        try:
            log_transaction(mm_request_id=log.id, api_response=response)
        except Exception:
            pass
    return response


def request_orange_money_payout(phone_number, amount, user=None):
    try:

        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.ORANGE_MONEY_PAYMENT_URL
        email = settings.ORANGE_MONEY_AUTH_EMAIL
        password = settings.ORANGE_MONEY_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
    except Exception as e:
        message = "Orange Money Payout Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_orange_money_payout:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
    return response


def request_orange_money_deposit(phone_number, amount, user=None):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.ORANGE_MONEY_CHECKOUT_URL
        email = settings.ORANGE_MONEY_AUTH_EMAIL
        password = settings.ORANGE_MONEY_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
        return response
    except Exception as e:
        message = "Orange Money deposit Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_orange_money_deposit:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
    return response


@app.task
def log_transaction(request_type=None, nsp=None, tel=None, amount=None, user=None, api_response=None, mm_request_id=None):
    # if there is a mm_request_id, consider as a get_response else a send_request

    if mm_request_id:
        response_transaction_date = None
        transaction_id = None
        response_code = None
        message = api_response['message']
        response_status = api_response['status']
        if response_status == trans_status.success():
            # response_transaction_date = api_response['transactionDate']['date']
            # tz = api_response['transactionDate']['timezone']
            transaction_id = api_response['transactionId']
        try:
            r = mm_manager.get_response(
                mm_request_id=mm_request_id, response_status=response_status, message=message,
                transaction_id=transaction_id, response_transaction_date=response_transaction_date,
                response_code=response_code
            )
            return r
        except Exception as e:
            print(e)
    else:
        try:
            r = mm_manager.send_request(
                request_type=request_type, nsp=nsp, tel=tel, amount=amount, user=user
            )
            return r
        except Exception:
            pass
