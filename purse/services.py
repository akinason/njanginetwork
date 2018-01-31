import requests
from njanginetwork import settings
from django.utils import timezone
from json.decoder import JSONDecodeError
from purse.models import TransactionStatus, WalletTransMessage


trans_status = TransactionStatus()
trans_message = WalletTransMessage()

def request_momo_payout(phone_number, amount):
    # url = settings.MOMO_PAYMENT_URL
    # email = settings.MOMO_AUTH_EMAIL
    # password = settings.MOMO_AUTH_PASSWORD
    # params = {'email': email, 'password': password, 'amount': amount, 'phone': phone_number}
    # r = requests.post(url=url, data=params)
    # response = r.json()
    response = {'status': 'success', 'message': 'operation successful', 'transactionId': 256582,
                'transactionDate': timezone.now(), 'phoneNumber': 675588556, 'amount': 5000
                }
    return response


def request_momo_deposit(phone_number, amount):
    # try:
    #     url = settings.MOMO_CHECKOUT_URL
    #     email = settings.MOMO_AUTH_EMAIL
    #     password = settings.MOMO_AUTH_PASSWORD
    #     params = {'email': email, 'password': password, 'amount': amount, 'phone': phone_number}
    #     r = requests.post(url=url, data=params)
    #     response = r.json()
    # except JSONDecodeError as json_error:
    #     response = {'status': trans_status.failure(), 'message': 'JSONDecodeError: %s' % json_error}
    # except ConnectionError as conn_error:
    #     response = {'status': trans_status.failure(), 'message': 'ConnectionError: %s' % conn_error}
    response = {'status': 'success', 'message': 'operation successful', 'transactionId': 256582,
                'transactionDate': timezone.now(), 'phoneNumber': 675588556, 'amount': 5000
                }
    return response


def request_orange_money_payout(phone_number, amount):
    # url = settings.MOMO_PAYMENT_URL
    # email = settings.MOMO_AUTH_EMAIL
    # password = settings.MOMO_AUTH_PASSWORD
    # params = {'email': email, 'password': password, 'amount': amount, 'phone': phone_number}
    # r = requests.post(url=url, data=params)
    # response = r.json()
    response = {'status': 'success', 'message': 'operation successful', 'transactionId': 256582,
                'transactionDate': timezone.now(), 'phoneNumber': 675588556, 'amount': 5000
                }
    return response


def request_orange_money_deposit(phone_number, amount):
    url = settings.MOMO_CHECKOUT_URL
    email = settings.MOMO_AUTH_EMAIL
    password = settings.MOMO_AUTH_PASSWORD
    params = {'email': email, 'password': password, 'amount': amount, 'phone': phone_number}
    response = {}
    try:
        r = requests.post(url=url, data=params)
        response = r.json()
        # response = {'status': 'success', 'message': 'operation successful', 'transactionId': 256582,
        #             'transactionDate': timezone.now(), 'phoneNumber': 675588556, 'amount': 5000
        #             }
    except Exception as e:
        response = {'status': trans_status.failed(), 'message': trans_message.failed_message()}
    return response

