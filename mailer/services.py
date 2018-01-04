from njanginetwork.celery import app
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from main.context_processors import SiteInformation
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from purse.models import WalletManager

wallet = WalletManager()


def send_email(user, subject, message, introduction=None, to_email=None):
    if not introduction:
        introduction = ''

    template_name = 'mailer/email.html'
    html_mail = loader.render_to_string(
        template_name=template_name,
        context={
            'subject': subject,
            'message': message,
            'introduction': introduction,
            'site_info': SiteInformation(),
            'user': user,
        }
    )

    if to_email or user.email:
        recipient_email = ''
        if to_email:
            recipient_email = to_email
        else:
            recipient_email = user.email

        msg = EmailMultiAlternatives(subject=subject, body=html_mail, to=[recipient_email, ])
        msg.attach_alternative(html_mail, "text/html")
        msg.send()
        return True
    else:
        return False


@app.task
def send_wallet_load_success_email(user_id, amount, processing_fee, nsp):
    subject = _('Wallet Load Successful')
    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance
    }
    message = _('You have successfully reloaded your %(nsp)s wallet with the sum of %(amount)s XOF. '
                'Processing fees: %(processing_fee)s XOF. New balance %(balance)s XOF.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_wallet_load_failed_email(user_id, amount, processing_fee, nsp):
    subject = _('Wallet Load Failed')
    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance
    }
    message = _('Your request to reload your %(nsp)s wallet with the sum of %(amount)s XOF failed. '
                'Processing fees: %(processing_fee)s XOF. Wallet balance %(balance)s XOF.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_wallet_contribution_paid_email(sender_id, recipient_id, amount, processing_fee, nsp, level):
    subject = _('Contribution Payment Successful')
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        sender = UserModel().objects.none()

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
    except UserModel().DoesNotExist:
        recipient = UserModel().objects.none()

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(), 'level': level,
        'recipient': recipient.get_username()
    }
    message = _('Your level %(level)s contribution to %(recipient)s of %(amount)s XOF through %(nsp)s was successful.'
                'Processing fees: %(processing_fee)s XOF. ') % params
    send_email(user=sender, subject=subject, message=message)


@app.task
def send_wallet_contribution_received_email(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_withdrawal_email(user_id, amount, processing_fee, nsp):
    subject = _('Withdrawal Successful')
    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance
    }
    message = _('You have successfully withdrawn the sum of %(amount)s XOF from your %(nsp)s wallet '
                'Processing fees: %(processing_fee)s XOF. New balance %(balance)s XOF.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_wallet_contribution_auto_withdrawal_email(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_withdrawal_failed_email(user_id, message, status):
    pass


@app.task
def send_unverified_phone_number_mail(user_id, nsp):
    pass


@app.task
def send_nsp_contribution_failed_email(user_id, nsp, level, amount):
    pass


@app.task
def send_wallet_contribution_failed_email(user_id, nsp, level, amount):
    pass


@app.task
def send_contribution_due_reminder_email(user_id, level, amount, duration, is_over_due=False):
    pass


@app.task
def send_level_deactivation_email(user_id, level, amount):
    pass


@app.task
def send_auto_wallet_contribution_failed_email(user_id, level, amount):
    pass


@app.task
def send_nsp_contribution_pending_email(user_id, nsp, level, amount):
    print('An error has occured in the failed operations model')
    pass

@app.task
def send_failed_operation_admin_email(instance_id):
    pass


# SMS notifications.
@app.task
def send_wallet_load_success_sms(user_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_load_failed_sms(user_id, amount, processing_fee, nsp):
    pass

@app.task
def send_wallet_contribution_paid_sms(sender_id, recipient_id, amount, processing_fee, nsp, level):
    pass


@app.task
def send_wallet_contribution_received_sms(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_withdrawal_sms(user_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_contribution_auto_withdrawal_sms(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_withdrawal_failed_sms(user_id, message, status):
    pass


@app.task
def send_unverified_phone_number_sms(user_id, nsp):
    pass


@app.task
def send_nsp_contribution_failed_sms(user_id, nsp, level, amount):
    pass


@app.task
def send_wallet_contribution_failed_sms(user_id, nsp, level, amount):
    pass

@app.task
def send_nsp_contribution_pending_sms(user_id, nsp, level, amount):
    pass

@app.task
def send_contribution_due_reminder_sms(user_id, level, amount, duration, is_over_due=False):
    pass


@app.task
def send_level_deactivation_sms(user_id, level, amount):
    pass


@app.task
def send_auto_wallet_contribution_failed_sms(user_id, level, amount):
    pass
