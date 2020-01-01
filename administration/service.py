from njanginetwork import celery_app as app

from administration.models import Beneficiary, Remuneration, remuneration_status
from mailer.services import send_sms, send_email
from main.notification import NotificationManager
from main.core import TransactionStatus, NSP
from main.utils import get_admin_users
from purse.models import WalletManager


trans_status = TransactionStatus()
wallet_manager = WalletManager()
nsp = NSP()
notification_manager = NotificationManager()


@app.task
def pay_remunerations(remuneration_id):
    """
    1. Generate the list of beneficiaries already computed (taken from administration.models.Beneficiary).
    2. Arrange and call the wallet_manager.pay on the admin account and wallet_manager.load on recipient accounts.
    3. Send sms, email and dashboard notifications
    4. Return response.
    """

    try:
        remuneration = Remuneration.objects.get(pk=remuneration_id)
    except Remuneration.ObjectDoesNotExist:
        return {'status': trans_status.failed(), 'message': 'Remuneration with id  does not exist.'.format(remuneration_id)}

    if remuneration.is_paid:
        return {
            'status': trans_status.failed(), 'message': 'Remuneration with id %s has already been paid.'.format(remuneration_id)
        }

    allowed_status = ['GENERATED', 'PARTIALLY_PAID']
    if remuneration.status not in allowed_status:
        return {
            'status': trans_status.failed(), 'message': 'Remuneration status must be one of %s'.format(allowed_status)
        }

    """If the function reaches here, it means we are good to proceed."""

    beneficiaries = Beneficiary.objects.filter(remuneration=remuneration, is_paid=False)
    if not beneficiaries:
        return {
            'status': trans_status.failed(), 'message': 'There are no beneficiaries for this remuneration.'
        }

    source_account = remuneration.source_account
    allocated_amount = remuneration.allocated_amount
    title = remuneration.title
    if not source_account.balance.available_balance >= allocated_amount:
        return {
            'status': trans_status.failed(),
            'message': 'There is not sufficient funds in %s account to transfer %s'.format(
                source_account.username, remuneration.allocated_amount
            )
        }

    """Payout the money from the source_account """
    description = f"{title}  sent to {beneficiaries.count()} users."
    res = wallet_manager.pay(
        user=source_account, amount=allocated_amount, nsp=nsp.mtn_wallet(),
        description=description
    )

    if not res['status'] == trans_status.success():
        return {'status': trans_status.failed(), 'message': res['message']}

    """Multi Threading will be used here."""
    # change remuneration status to PARTIALLY_PAID
    remuneration.status = remuneration_status.partially_paid()
    remuneration.save()
    
    beneficiary_list = []
    for beneficiary in beneficiaries:
        if not beneficiary.is_paid and beneficiary.amount > 0:
            _beneficiary = _pay_remuneration(beneficiary, title)
            beneficiary_list.append(_beneficiary)
    
    # change remuneration status to PAID
    remuneration.status = remuneration_status.paid()
    remuneration.save()
    
    return {'status': trans_status.success(), 'message': 'Operation Successful', 'beneficiaries': beneficiary_list}


def _pay_remuneration(beneficiary, title):
    #  1. Load the user's account.
    res = wallet_manager.load(
        user=beneficiary.user, amount=beneficiary.amount, nsp=nsp.mtn_wallet(), description=title
    )
    if res['status'] != trans_status.success():
        return {'user': beneficiary.user, 'allocated': beneficiary.amount, 'paid': 0}

    # Send notifications
    message = "You received a {title} of {amount} from Njangi Network. Enjoy it, thanks for " \
              "collaboration. Keep Networking...".format(
                title=title, amount=beneficiary.amount
            )

    if beneficiary.user.email:
        send_email(subject=title, message=message, user=beneficiary.user, to_email=beneficiary.user.email)

    if beneficiary.user.tel1:
        body = "Hello {username}\nYou received a {title} of {amount} from Njangi Network".format(
            username=beneficiary.user.username, title=title, amount=beneficiary.amount
        )

        r = send_sms(to_number=beneficiary.user.tel1, body=body)

    notification_manager.create(
        notification_type='remuneration_received', text=message, user_id=beneficiary.user.id
    )

    return {'user': beneficiary.user, 'allocated': beneficiary.amount, 'paid': beneficiary.amount}