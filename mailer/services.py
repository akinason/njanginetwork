from njanginetwork.celery import app
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template import loader
from main.context_processors import SiteInformation
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from purse.models import WalletManager
from njangi.models import FailedOperations
from twilio.rest import Client
from njanginetwork import settings
from main.core import NSP
import os
from django.utils.http import urlencode
import requests

_nsp = NSP()
wallet = WalletManager()


@app.task
def send_sms(to_number, body):
    response = send_1s2u_sms(to_number, body)
    return response

@app.task 
def send_twilio_sms(to_number, body):
    _to_number = str(to_number).replace(" ", "").replace("+", "")
    if len(_to_number) <= 9:
        _to_number = '237%s' % _to_number

    to_number_ = int(_to_number)
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            to=_to_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            body=body
        )
        return True
    except Exception as e:
        return False

@app.task
def send_1s2u_sms(to_number, body):
    _to_number = str(to_number).replace(" ", "").replace("+", "")
    if len(_to_number) <= 9:
        _to_number = '237%s' % _to_number

    to_number_ = int(_to_number)
    url = settings.ONE_S_2_U_SEND_URL
    username = settings.ONE_S_2_U_USERNAME
    password = settings.ONE_S_2_U_PASSWORD
    mno = to_number_
    msg = body
    sid = "NjangiNetwk"
    fl = 0
    mt = 0
    ipcl = "127.0.0.1"
    params = {
        'username': username, 'password': password, 'msg': msg,
        'Sid': sid, 'fl': fl, 'mt': mt, 'ipcl': ipcl, 'mno': mno
    }
    encoded_params = urlencode(params)
    response = requests.get(url=url, params=encoded_params)
    content = ''
    try:
        content = response.content.decode('ascii')
    except AttributeError:
        content = response.content

    r = {'status_code': str(response.status_code), 'content': content}
    return r


@app.task
def send_email(subject, message, user=None, introduction=None, to_email=None, reply_to=None, request=None):
    headers = {}

    context = {
        'subject': subject,
        'message': message,
        'introduction': introduction,
        'site_info': SiteInformation(request),
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

    try:
        msg = EmailMultiAlternatives(subject=subject, body=html_mail, to=[recipient_email, ], headers=headers)
        msg.attach_alternative(html_mail, "text/html")
        msg.send()
        return True
    except Exception:
        return False


@app.task
def send_admin_email(message, subject=None):
    """
    Sends a mail to the admin when an error occurs in the system.
    :param message:
    :param subject:
    :return:
    """
    send_mail(
        subject=subject if subject else "Attention Needed",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=True
    )


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=sender, subject=subject, message=message)


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
    return send_email(user=recipient, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=recipient, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=_message)


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
    return send_email(user=user, subject=subject, message=_message)


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message)


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

    return send_email(user=user, subject=subject, message=message)


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

    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message)


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
    return send_email(user=user, subject=subject, message=message, to_email=settings.ADMIN_EMAIL)


@app.task
def send_signup_welcome_email(user_id):
    subject = _('Welcome to the Network!')
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    message = _(
                "Welcome to the network. Please be fast to do your first contribution so you don't "
                "miss to receive from your network."
                "Thanks for Collaborating!"
                ) 
    try:
        if user.email:
            return send_email(user=user, subject=subject, message=message)
        else:
            return False
    except Exception as e:
        return False


# SMS notifications.
@app.task
def send_wallet_load_success_sms(user_id, amount, processing_fee, nsp, transaction_id):

    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance, 'username': user.username if user.username else _('Member'),
        'transaction_id': transaction_id
    }
    message = _('Hello %(username)s! \nYou have successfully reloaded your %(nsp)s wallet '
                'with the sum of %(amount)s XOF. '
                'Processing fees: %(processing_fee)s XOF. New balance %(balance)s XOF. Ref:'
                '%(transaction_id)s') % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            to_number = user.tel2.as_international
        elif nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            to_number = user.tel1.as_international
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_load_failed_sms(user_id, amount, processing_fee, nsp):
    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance, 'username': user.username if user.username else _('Member')
    }
    message = _('Hello %(username)s! \nYour request to reload your %(nsp)s wallet with the sum of %(amount)s '
                'XOF failed.'
                'Processing fees: %(processing_fee)s XOF. Wallet balance %(balance)s XOF.') % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            to_number = user.tel2.as_international
        elif nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            to_number = user.tel1.as_international
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_contribution_paid_sms(sender_id, recipient_id, amount, processing_fee, nsp, level):
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        return False

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(), 'level': level,
        'recipient': recipient.username if recipient else None,
        'sender': sender.username if sender else _('Member')
    }
    message = _('Hello %(sender)s! \nYour level %(level)s contribution to %(recipient)s of %(amount)s XOF through '
                '%(nsp)s was successful.'
                'Processing fees: %(processing_fee)s XOF. ') % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            to_number = sender.tel2.as_international
        elif nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            to_number = sender.tel1.as_international
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_contribution_received_sms(sender_id, recipient_id, amount, processing_fee, nsp, level):
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        return False

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(), 'level': level,
        'recipient': recipient.username if recipient else None,
        'sender': sender.username if sender else _('Member')
    }
    message = _('Hello %(recipient)s! \nYou have received %(amount)s as level %(level)s contribution from %(sender)s '
                'through %(nsp)s.') % params

    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            to_number = sender.tel2.as_international
        elif nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            to_number = sender.tel1.as_international
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_withdrawal_sms(user_id, amount, processing_fee, nsp):
    balance = 0
    try:
        user = UserModel().objects.get(pk=user_id)
        balance = wallet.balance(user=user, nsp=nsp)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'balance': balance, 'username': user.username if user.username else _('Member')
    }
    message = _('Hello %(username)s! \nYou have successfully withdrawn the sum of %(amount)s XOF from '
                'your %(nsp)s wallet Processing fees: %(processing_fee)s XOF. New balance %(balance)s XOF.') % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet() and user.tel2:
            to_number = user.tel2.as_international
        elif (nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet()) and user.tel1:
            to_number = user.tel1.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_contribution_auto_withdrawal_sms(sender_id, recipient_id, amount, processing_fee, nsp):
    balance = 0
    try:
        sender = UserModel().objects.get(pk=sender_id)
    except UserModel().DoesNotExist:
        return False

    try:
        recipient = UserModel().objects.get(pk=recipient_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'amount': amount, 'processing_fee': processing_fee, 'nsp': nsp.replace('_', ' ').upper(),
        'username': sender.username if sender.username else _('Member'), 'recipient': recipient.username
    }
    message = _(
        'Hello %(username)s!\n'
        'Auto Wallet Contribution successful\n'
        'Amt: %(amount)s XOF\n'
        'Fees: %(processing_fee)s XOF\n'
        'Wallet: %(nsp)s\n'
        'Recipient: %(recipient)s\n'
        'Thanks for Collaborating!'
    ) % params
    to_number = ''
    try:
        if (nsp == _nsp.orange() or nsp == _nsp.orange_wallet()) and sender.tel2:
            to_number = sender.tel2.as_international
        elif (nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet()) and sender.tel1:
            to_number = sender.tel1.as_international
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_wallet_withdrawal_failed_sms(user_id, message, status):

    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'message': message, 'status': status
    }
    _message = _('Hi %(username)s!\n'
                 'Withdrawal Failed\n'
                 'status: %(status)s\n'
                 '%(message)s\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_unverified_phone_number_sms(user_id, nsp):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'nsp': nsp
    }
    message = _('Hi %(username)s!\n'
                'Please verify your %(nsp)s phone number.\n'
                'You will not be able to receive contributions directly in your %(nsp)s account if this is not done.\n'
                'Thanks for collaborating!'
                ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=message)


@app.task
def send_nsp_contribution_failed_sms(user_id, nsp, level, amount):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level, 'nsp': nsp
    }
    _message = _('Hi %(username)s!\n'
                 'Level %(level)s contribution through %(nsp)s Failed\n'
                 'Amount: %(amount)s XOF\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet() and user.tel2:
            to_number = user.tel2.as_international
        elif (nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet()) and user.tel1:
            to_number = user.tel1.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_wallet_contribution_failed_sms(user_id, nsp, level, amount):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level, 'nsp': nsp
    }
    _message = _('Hi %(username)s!\n'
                 'Level %(level)s contribution through %(nsp)s Failed\n'
                 'Amount: %(amount)s XOF\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if nsp == _nsp.orange() or nsp == _nsp.orange_wallet() and user.tel2:
            to_number = user.tel2.as_international
        elif (nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet()) and user.tel1:
            to_number = user.tel1.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_nsp_contribution_pending_sms(user_id, nsp, level, amount):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level, 'nsp': nsp
    }
    _message = _('Hi %(username)s!\n'
                 'Level %(level)s contribution through %(nsp)s Pending\n'
                 'We will retry and notify you when its done.'
                 'Amount: %(amount)s XOF\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if (nsp == _nsp.orange() or nsp == _nsp.orange_wallet()) and user.tel2:
            to_number = user.tel2.as_international
        elif (nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet()) and user.tel1:
            to_number = user.tel1.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_contribution_due_reminder_sms(user_id, level, amount, duration, is_over_due=False):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level,
        'duration': duration
    }
    _message = ''
    if is_over_due:
        _message = _('Hi %(username)s!\n'
                     'Your level %(level)s contribution is due in %(duration)s. \n'
                     'Amount: %(amount)s XOF\n'
                     'Thanks for Collaborating!'
                     ) % params
    else:
        _message = _('Hi %(username)s!\n'
                     'Your level %(level)s contribution has been due since %(duration)s. \n'
                     'Amount: %(amount)s XOF\n'
                     'Thanks for Collaborating!'
                     ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_level_deactivation_sms(user_id, level, amount):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level,

    }

    _message = _('Hello %(username)s!\n'
                 'You have been deactivated from level %(level)s as a result of your due contribution.\n'
                 'Amount: %(amount)s XOF\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_auto_wallet_contribution_failed_sms(user_id, level, amount):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member'), 'amount': amount, 'level': level
    }
    _message = _('Hi %(username)s!\n'
                 'We tried processing your level %(level)s contribution but it failed.\n'
                 'Please check your account balance\n'
                 'Amount: %(amount)s XOF\n'
                 'Thanks for Collaborating!'
                 ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)


@app.task
def send_signup_welcome_sms(user_id):
    try:
        user = UserModel().objects.get(pk=user_id)
    except UserModel().DoesNotExist:
        return False

    params = {
        'username': user.username if user.username else _('Member')
    }
    _message = _('Hi %(username)s!\n'
                 "Welcome to the network. Please be fast to do your first contribution so you don't "
                 "miss to receive from your network.\n"
                 "Thanks for Collaborating!"
                 ) % params
    to_number = ''
    try:
        if user.tel1:
            to_number = user.tel1.as_international
        elif user.tel2:
            to_number = user.tel2.as_international
        else:
            return False
    except Exception as e:
        return False
    return send_sms(to_number=to_number, body=_message)
