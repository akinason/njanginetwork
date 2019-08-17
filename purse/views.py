import json

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response

from main.core import TransactionStatus
from main.notification import notification
from marketplace import service as market_services
from main.utils import get_sponsor_using_sponsor_id
from njangi.core import add_user_to_njangi_tree, create_user_levels
from njangi.tasks import process_nsp_contribution, process_wallet_load, process_wallet_withdraw
from purse.models import (
    MobileMoneyManager, MOMOPurpose, MMRequestType, WalletManager
)


momo_purpose = MOMOPurpose()
momo_request_type = MMRequestType()
momo_manager = MobileMoneyManager()
trans_status = TransactionStatus()
wallet_manager = WalletManager()


@method_decorator(csrf_exempt, name='dispatch')
def afknerdgsmtoolsview(request, *args, **kwargs):
    # Responsible for processing mobile money callback_url from gsmtools.afkanerd.com/api/

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
        process_transaction_update(
            tracker_id=tracker_id, uuid=uuid, status_code=status_code, server_response=server_response
        )
    return JsonResponse(data={'status': 'success', 'message': 'Thanks'})


@method_decorator(csrf_exempt, name='dispatch')
def monetbilpayoutnotificationview(request, *args, **kwargs):
    # Responsible for processing successful mobile money callback_url from monetbil.com
    if request.method == "POST" or request.method == "GET":
        uuid = None
        server_response = request.POST.get('message')
        success = request.POST.get('success')
        tracker_id = request.POST.get('processing_number')
        transaction_id = request.POST.get('operator_transaction_id')

        if str(success) == '1':
            status_code = 200
        else:
            status_code = 400

        process_transaction_update(
            tracker_id=tracker_id, uuid=uuid, status_code=status_code, server_response=server_response,
            transaction_id=None
        )
    return JsonResponse(data={'status': 'success', 'message': 'Thanks'})


class MonetbilNotificationView(APIView):

    def post(self, request, *args, **kwargs):
        uuid = None
        server_response = request.data.get('message')
        status = request.data.get('status')
        tracker_id = request.data.get('payment_ref')
        # transaction_id = request.data.get('transaction_id')

        if status == "success":
            status_code = 200
        else:
            status_code = 400

        process_transaction_update(
            tracker_id=tracker_id, uuid=uuid, status_code=status_code, server_response=server_response,
            transaction_id=None, full_response=request.data
        )

        return Response({"message": "success"}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
def monetbilnotificationview(request, *args, **kwargs):
    """Discontinued in favour of class based view. See above."""
    # Responsible for processing successful mobile money callback_url from monetbil.com
    print(request.POST)
    if request.method == "POST" or request.method == "GET":
        uuid = None
        server_response = request.POST.get('message')
        status = request.POST.get('status')
        tracker_id = request.POST.get('payment_ref')
        # transaction_id = request.POST.get('transaction_id')

        if status == "success":
            status_code = 200
        else:
            status_code = 400

        process_transaction_update(
            tracker_id=tracker_id, uuid=uuid, status_code=status_code, server_response=server_response,
            transaction_id=None, full_response=request.data
        )

    return JsonResponse(data={'status': 'success', 'message': 'Thanks'})


def process_transaction_update(
    tracker_id, status_code, server_response=None, uuid=None, transaction_id=None, full_response=None
):

    # Check to ensure the transaction actually originated from our servers
    if momo_manager.is_valid(tracker_id=tracker_id, uuid=uuid):
        transaction_id = momo_manager.get_mm_transaction_id(tracker_id=tracker_id, uuid=uuid)
        response_status = trans_status.success()
        if not int(status_code) == 200:
            response_status = trans_status.failed()
        mm_transaction = momo_manager.get_response(
            mm_request_id=transaction_id, callback_status_code=status_code, response_status=response_status,
            callback_response_date=timezone.now(), callback_server_response=server_response, full_response=full_response
        )

        if int(status_code) == 200 and not mm_transaction.is_complete:
            # Proceed to process the transaction.
            if mm_transaction.purpose == momo_purpose.contribution() and mm_transaction.level and \
             mm_transaction.request_type == momo_request_type.deposit():
                user = mm_transaction.user
                if not user.is_in_network:
                    sponsor = get_sponsor_using_sponsor_id(sponsor_id=user.sponsor)
                    add_user_to_njangi_tree(user=user, sponsor=sponsor)
                    create_user_levels(user=user)
                    user.has_contributed = True
                    user.save()

                process_nsp_contribution.delay(mm_transaction.tracker_id)
            elif mm_transaction.purpose == momo_purpose.wallet_load():
                process_wallet_load(
                    user_id=mm_transaction.user.id, amount=mm_transaction.amount, nsp=mm_transaction.nsp,
                    tracker_id=mm_transaction.tracker_id, charge=mm_transaction.charge
                )
            elif mm_transaction.purpose == momo_purpose.wallet_withdraw() or \
                    mm_transaction.purpose == momo_purpose.contribution_wallet_withdraw():
                process_wallet_withdraw(
                   user_id=mm_transaction.recipient.id, amount=mm_transaction.amount, nsp=mm_transaction.nsp,
                   tracker_id=mm_transaction.tracker_id, charge=mm_transaction.charge
                )
            elif mm_transaction.purpose == momo_purpose.signup_contribution():
                # Add the user to network tree.
                # create Njangi levels for the user.
                # Process nsp contribution.
                user = mm_transaction.user
                if not user.is_in_network:
                    sponsor = get_sponsor_using_sponsor_id(sponsor_id=user.sponsor)
                    add_user_to_njangi_tree(user=user, sponsor=sponsor)
                    create_user_levels(user=user)
                user.has_contributed = True
                user.save()
                process_nsp_contribution(mm_transaction.tracker_id)
            elif mm_transaction.purpose == momo_purpose.market_purchase():
                mm_transaction.is_complete = True
                mm_transaction.save()
                market_services.payment_complete_process(invoice_id=mm_transaction.invoice_number)

        else:
            if not mm_transaction.is_complete:
                # First mark the failed transaction as complete.
                mm_transaction.is_complete = True
                mm_transaction.save()

                # Insert a failure notification.
                notification().templates.transaction_failed(
                    user_id=mm_transaction.user.id, purpose=mm_transaction.purpose, amount=mm_transaction.amount,
                    nsp=mm_transaction.nsp
                )
                if mm_transaction.purpose == momo_purpose.wallet_withdraw():
                    wallet_manager.update_status(
                        status=trans_status.failed(), tracker_id=mm_transaction.tracker_id
                    )
            else:
                # the transaction is already marked as complete. Just pass.
                pass

    else:
        # Looks like this transaction is not from our server, however, keep track of it.
        mm_transaction = momo_manager.send_request(
            request_type=momo_request_type.unknown(), nsp="unknown", tel="unknown", amount=0,
            provider="unknown", purpose="unknown", user=None
        )
        mm_transaction.tracker_id = tracker_id if tracker_id else 0
        mm_transaction.message = uuid if uuid else "Null"
        mm_transaction.callback_status_code = status_code
        mm_transaction.is_complete = True
        mm_transaction.save()


# from django.urls import reverse_lazy, reverse
# import requests
# from django.http import HttpResponse, HttpResponseRedirect
# from django.contrib.auth import login, authenticate
# from main.models import User
# from django.views import generic


# class TestView(generic.TemplateView):
#     template_name = 'purse/test.html'
#     success_url = reverse_lazy('main:login')
#
#     def get(self, request, *args, **kwargs):
#         return HttpResponseRedirect('https://google.com')

#         url = 'http://localhost:8012/purse/gsmtools/afkanerd/api/momo/8b0db72e-78ef-4eb2-adf1-9cbfd63346c8/'
#         data = {'trackerId': 'L216', 'status': 'success', 'statusCode': 200, 'serverResponse': 'success'}
#         headers = {'Content-Type': 'application/json', }
#         response = requests.post(url, data=json.dumps(data), headers=headers)
#         print(response)
#         # user = User.objects.get(username='kinason')
#         # login(request, user)
#         return HttpResponseRedirect(reverse('purse:test_view',), )
#         # return render(request, self.template_name)
