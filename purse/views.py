import json
import requests

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from main.core import TransactionStatus
from njangi.tasks import process_contribution, process_wallet_load, process_wallet_withdraw
from purse.models import (
    MobileMoneyManager, MOMOPurpose, MMRequestType, WalletManager
)

# Responsible for processing mobile money callback_url from gsmtools.afkanerd.com/api/


momo_purpose = MOMOPurpose()
momo_request_type = MMRequestType()
momo_manager = MobileMoneyManager()
trans_status = TransactionStatus()
wallet_manager = WalletManager()


@method_decorator(csrf_exempt, name='dispatch')
def afknerdgsmtoolsview(request, *args, **kwargs):
    if request.method == "POST":
        request_body = request.body
        # print(request_body)
        if isinstance(request_body, bytes):
            request_body = request_body.decode()
        post_data = json.loads(request_body)
        uuid = kwargs.get('uuid4')
        server_response = post_data.get('serverResponse')
        status_code = post_data.get('statusCode')
        tracker_id = post_data.get('trackerId')
        unique_id = post_data.get('uniqueId')
        # print(uuid, server_response, status_code, tracker_id, unique_id)
        process_transaction_update(tracker_id=tracker_id, uuid=uuid, status_code=status_code)
    return JsonResponse(data={'status': 'success', 'message': 'Thanks'})


def process_transaction_update(tracker_id, uuid, status_code):

    # Check to ensure the transaction actually originated from our servers
    if momo_manager.is_valid(tracker_id=tracker_id, uuid=uuid):
        transaction_id = momo_manager.get_mm_transaction_id(tracker_id=tracker_id, uuid=uuid)
        response_status = trans_status.success()
        if not int(status_code) == 200:
            response_status = trans_status.failed()
        mm_transaction = momo_manager.get_response(
            mm_request_id=transaction_id, callback_status_code=status_code, response_status=response_status,
            callback_response_date=timezone.now()
        )
        if int(status_code) == 200 and not mm_transaction.is_complete:
            # Proceed to process the transaction.
            if mm_transaction.purpose == momo_purpose.contribution() and mm_transaction.level and \
             mm_transaction.request_type == momo_request_type.deposit():
                r = process_contribution(
                    level=mm_transaction.level, nsp=mm_transaction.nsp, user_id=mm_transaction.user.id,
                    recipient_id=mm_transaction.recipient.id, tracker_id=mm_transaction.tracker_id
                )
            elif mm_transaction.purpose == momo_purpose.wallet_load():
                r = process_wallet_load(
                    user_id=mm_transaction.user.id, amount=mm_transaction.amount, nsp=mm_transaction.nsp,
                    tracker_id=mm_transaction.tracker_id, charge=mm_transaction.charge
                )
            elif mm_transaction.purpose == momo_purpose.wallet_withdraw() or \
                    mm_transaction.purpose == momo_purpose.contribution_wallet_withdraw():
               r = process_wallet_withdraw(
                   user_id=mm_transaction.recipient.id, amount=mm_transaction.amount, nsp=mm_transaction.nsp,
                   tracker_id=mm_transaction.tracker_id, charge=mm_transaction.charge
               )
        else:
            if not mm_transaction.is_complete and mm_transaction.purpose == momo_purpose.wallet_withdraw():
                r = wallet_manager.update_status(
                    status=trans_status.failed(), tracker_id=mm_transaction.tracker_id
                )

                mm_transaction.is_complete = True
                mm_transaction.save()
            print('This transaction is already completed or its a failed operation.')
    else:
        print('API request received but does not pass test. Certainly not sent by me.')
        pass

from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate

class TestView(generic.TemplateView):
    template_name = 'purse/test.html'
    success_url = reverse_lazy('main:login')

    def post(self, request, *args, **kwargs):
        # url = 'http://localhost:8012/purse/gsmtools/afkanerd/api/momo/2b28b40b-a462-404f-a2f9-114c86d442d0/'
        # data = {'trackerId': 'L188', 'status': 'success', 'statusCode': 200, 'serverResponse': 'success'}
        # headers = {'Content-Type': 'application/json', }
        # response = requests.post(url, data=json.dumps(data), headers=headers)
        # # print(response)
        return HttpResponseRedirect(reverse('main:login',), )
