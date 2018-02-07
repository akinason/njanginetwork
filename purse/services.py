import requests
from njanginetwork import settings
from purse.models import TransactionStatus, WalletTransMessage
from mailer.services import send_admin_email


trans_status = TransactionStatus()
trans_message = WalletTransMessage()


def request_momo_payout(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.MOMO_PAYMENT_URL
        email = settings.MOMO_AUTH_EMAIL
        password = settings.MOMO_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
    except Exception as e:
        message = "MoMo Payout Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_momo_payout:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
    return response


def request_momo_deposit(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.MOMO_CHECKOUT_URL
        email = settings.MOMO_AUTH_EMAIL
        password = settings.MOMO_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
    except Exception as e:
        message = "MoMo Deposit Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_momo_deposit:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
    return response


def request_orange_money_payout(phone_number, amount):
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


def request_orange_money_deposit(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.ORANGE_MONEY_CHECKOUT_URL
        email = settings.ORANGE_MONEY_AUTH_EMAIL
        password = settings.ORANGE_MONEY_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params, timeout=(3.05, 120))
        response = r.json()
    except Exception as e:
        message = "Orange Money deposit Request of %(amount)s by %(phone_number)s <br><br> ErrorMsg: %(error)s" % {
            'amount': amount, 'phone_number': phone_number, 'error': e
        }
        send_admin_email.delay(message=message, subject="request_orange_money_deposit:")
        response = {'status': trans_status.failure(), 'message': '%s' % e}
    return response
