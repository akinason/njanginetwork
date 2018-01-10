from njanginetwork.celery import app
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from main.context_processors import SiteInformation
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from purse.models import WalletManager
from njangi.models import FailedOperations
from njanginetwork import settings


wallet = WalletManager()


@app.task
def send_email(subject, message, user=None, introduction=None, to_email=None, reply_to=None):
    headers = {}
    context = {
        'subject': subject,
        'message': message,
        'introduction': introduction,
        'site_info': SiteInformation(),
    }

    if user:
        context.update({
            'user': user
        })

    if not introduction:
        introduction = ''

    template_name = 'mailer/email.html'
    html_mail = loader.render_to_string(
        template_name=template_name,
        context=context
    )

    recipient_email = ''
    if to_email:
        recipient_email = to_email
    else:
        if user:
            if user.email:
                recipient_email = user.email
            else:
                return False
        else:
            return False

    if reply_to:
        headers.update({
            'reply_to': reply_to,
        })

        msg = EmailMultiAlternatives(subject=subject, body=html_mail, to=[recipient_email, ], headers=headers)
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
        'recipient': recipient.username if recipient else None
    }
    message = _('Your level %(level)s contribution to %(recipient)s of %(amount)s XOF through %(nsp)s was successful.'
                'Processing fees: %(processing_fee)s XOF. ') % params
    send_email(user=sender, subject=subject, message=message)


@app.task
def send_wallet_contribution_received_email(sender_id, recipient_id, amount, processing_fee, nsp, level):
    subject = _('Level %s Contribution Received') % str(level)
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        sender = UserModel().objects.none()

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
    except UserModel().DoesNotExist:
        recipient = UserModel().objects.none()

    params = {
        'amount': amount, 'nsp': nsp.replace('_', ' ').upper(), 'level': level,
        'sender': sender.username if sender else None
    }
    message = _('You have received %(amount)s as level %(level)s contribution from %(sender)s through'
                '%(nsp)s.') % params
    send_email(user=recipient, subject=subject, message=message)


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
    subject = _('Contribution Auto Withdrawal Successful')
    balance = 0
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        sender = UserModel().objects.none()

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
        balance = wallet.balance(user=recipient, nsp=nsp)
    except UserModel().DoesNotExist:
        recipient = UserModel().objects.none()

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance, 'sender': sender.username if sender else None
    }
    message = _('You have successfully withdrawn the sum of %(amount)s XOF from your %(nsp)s wallet '
                'Processing fees: %(processing_fee)s XOF. New balance %(balance)s XOF. Contribution from '
                ' %(sender)s') % params
    send_email(user=recipient, subject=subject, message=message)


@app.task
def send_wallet_withdrawal_failed_email(user_id, message, status):
    subject = _('Withdrawal Failed')
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        "status": status,
        "reason": message,
    }
    _message = _('Your withdrawal request failed. Status: %(status)s, Reason: %(reason)s') % params
    send_email(user=user, subject=subject, message=_message)


@app.task
def send_unverified_phone_number_mail(user_id, nsp):
    subject = _('Phone Number Verification Needed')
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'nsp': nsp.replace('_', ' ').upper()
    }
    _message = _('Your %(nsp)s phone number is not verified. Please verify it else you will not be able to '
                 'receive any contributions.') % params
    send_email(user=user, subject=subject, message=_message)


@app.task
def send_nsp_contribution_failed_email(user_id, nsp, level, amount):
    subject = _('Level %(level)s contribution failed') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'nsp': nsp.replace('_', ' ').upper(), 'amount': amount, 'level': level
    }
    message = _('Your level %(level)s contribution of %(amount)s XOF through %(nsp)s failed. We will automatically '
                'do a retry for a while for you.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_wallet_contribution_failed_email(user_id, nsp, level, amount):
    subject = _('Level %(level)s wallet contribution failed') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'nsp': nsp.replace('_', ' ').upper(), 'amount': amount, 'level': level
    }
    message = _('Your level %(level)s contribution of %(amount)s XOF through %(nsp)s failed. We will automatically '
                'do a retry for a while for you.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_contribution_due_reminder_email(user_id, level, amount, duration, is_over_due=False):
    subject = _('Level %(level)s contribution due reminder') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'duration': duration, 'amount': amount, 'level': level
    }

    message = _('Your level %(level)s contribution of %(amount)s XOF is due in %(duration)s. You will be deactivated'
                ' from this level is this time elapses without you contributing..') % params

    if is_over_due:
        message = _(
            'Your level %(level)s contribution of %(amount)s XOF is has been due for %(duration)s. You are'
            ' loosing contributions you ought to receive for this level.') % params

    send_email(user=user, subject=subject, message=message)


@app.task
def send_level_deactivation_email(user_id, level, amount):
    subject = _('Level %(level)s deactivation notice') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
        'amount': amount, 'level': level
    }

    message = _('You have been deactivated in level %(level)s. You cannot receive contributions for this level '
                ' until you pay your past due level contribution of %(amount)s XOF.') % params

    send_email(user=user, subject=subject, message=message)


@app.task
def send_auto_wallet_contribution_failed_email(user_id, level, amount):
    subject = _('Level %(level)s auto wallet contribution failed') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
         'amount': amount, 'level': level
    }
    message = _('We could not process your level %(level)s contribution of %(amount)s XOF. Please ensure you have '
                'sufficient balance.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_nsp_contribution_pending_email(user_id, nsp, level, amount):
    subject = _('Level %(level)s contribution pending') % {'level': str(level)}
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    params = {
         'amount': amount, 'level': level, 'nsp': nsp.replace('_', ' ').upper()
    }
    message = _('Your level %(level)s contribution of %(amount)s through %(nsp)s is pending processing. '
                'We will notify you as soon as we complete the process.') % params
    send_email(user=user, subject=subject, message=message)


@app.task
def send_failed_operation_admin_email(instance_id):
    subject = _('New Failed Operation')
    try:
        user = UserModel().objects.filter(is_admin=True)[:1]
    except UserModel().DoesNotExist:
        user = UserModel().objects.none()

    try:
        instance = FailedOperations.objects.get(pk=instance_id)
    except FailedOperations.DoesNotExist:
        instance = FailedOperations.objects.none()
    message = instance
    send_email(user=user, subject=subject, message=message, to_email=settings.ADMIN_EMAIL)


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
def send_wallet_contribution_received_sms(sender_id, recipient_id, amount, processing_fee, nsp, level):
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
