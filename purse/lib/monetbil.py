import requests
from njanginetwork import production_settings as settings

WIDGET_REQUEST_BASE_URL = "https://api.monetbil.com/widget/%(version)s/%(service_key)s" % {
                            'version': "v2.1", 'service_key': settings.MONETBIL_NJANGI_NETWORK_SERVICE_KEY,
                            }
PAYOUT_BASE_URL = "https://api.monetbil.com/%(version)s/payouts/withdrawal" % {'version': 'v1'}
LOGO_URL = 'https://njanginetwork.com/static/website/images/logo/logo-gold.png'
PAYMENT_NOTIFY_URL = 'https://njanginetwork.com/purse/monetbil/notifications/aljfalsthosljlk5j'
PAYMENT_RETURN_URL = 'https://njanginetwork.com/dashboard/payment/done'


def send_payment_widget_request(
        amount, payment_ref, phone=None, locale=None, operator=None, country=None, currency=None, item_ref=None,
        user=None, first_name=None, last_name=None, email=None, return_url=None, notify_url=None
):
    params = {'amount': amount, 'payment_ref': payment_ref, 'logo': LOGO_URL, 'notify_url': PAYMENT_NOTIFY_URL,
              'return_url': PAYMENT_RETURN_URL}

    if phone:
        params['phone'] = phone
    if locale:
        params['locale'] = locale
    if operator:
        params['operator'] = operator
    if country:
        params['country'] = country
    if item_ref:
        params['item_ref'] = item_ref
    if user:
        params['user'] = user
    if first_name:
        params['first_name'] = first_name
    if last_name:
        params['last_name'] = last_name
    if email:
        params['email'] = email
    if return_url:
        params['return_url'] = return_url
    if notify_url:
        params['notify_url'] = notify_url

    r = requests.post(WIDGET_REQUEST_BASE_URL, params)
    response = r.json()
    success = response['success']
    payment_url = response['payment_url']

    if success:
        return payment_url
    else:
        return None


def send_payout_request(amount, phone, tracker_id):

    notification_url = 'https://njanginetwork.com/purse/monetbil/payout/notifications/jlasjdlkjwiurewopusl'

    params = {
        'amount': amount, 'phonenumber': phone, 'processing_number': tracker_id,
        'service_key': settings.MONETBIL_NJANGI_NETWORK_SERVICE_KEY,
        'service_secret': settings.MONETBIL_NJANGI_NETWORK_SERVICE_SECRET,
        'payout_notification_url': notification_url
    }
    r = requests.post(PAYOUT_BASE_URL, params)
    return r
