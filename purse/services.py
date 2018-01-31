import requests
from njanginetwork import settings
from django.utils import timezone
from json.decoder import JSONDecodeError
from purse.models import TransactionStatus, WalletTransMessage


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
        r = requests.post(url=url, data=params)
        response = r.json()
    except Exception as e:
        response = {'status':trans_status.failure(), 'message': '%s' % e }
    return response


def request_momo_deposit(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.settings.MOMO_CHECKOUT_URL
        email = settings.MOMO_AUTH_EMAIL
        password = settings.MOMO_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params)
        response = r.json()
    except Exception as e:
        response = {'status':trans_status.failure(), 'message': '%s' % e }
    return response



def request_orange_money_payout(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.settings.ORANGE_MONEY_PAYMENT_URL
        email = settings.ORANGE_MONEY_AUTH_EMAIL
        password = settings.ORANGE_MONEY_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params)
        response = r.json()
    except Exception as e:
        response = {'status':trans_status.failure(), 'message': '%s' % e }
    return response


def request_orange_money_deposit(phone_number, amount):
    try:
        _phone_number = str(phone_number).replace(" ", "").replace("+", "")
        _phone_number = int(_phone_number)
        url = settings.settings.ORANGE_MONEY_CHECKOUT_URL
        email = settings.ORANGE_MONEY_AUTH_EMAIL
        password = settings.ORANGE_MONEY_AUTH_PASSWORD
        params = {'email': email, 'password': password, 'amount': amount, 'phone': _phone_number}
        r = requests.post(url=url, data=params)
        response = r.json()
    except Exception as e:
        response = {'status':trans_status.failure(), 'message': '%s' % e }
    return response
