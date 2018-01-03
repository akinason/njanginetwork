from njanginetwork.celery import app
from django.core.mail import EmailMultiAlternatives



@app.task
def send_wallet_load_success_email(user_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_load_failed_email(user_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_contribution_paid_email(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_contribution_received_email(sender_id, recipient_id, amount, processing_fee, nsp):
    pass


@app.task
def send_wallet_withdrawal_email(user_id, amount, processing_fee, nsp):
    pass


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
def send_wallet_contribution_paid_sms(sender_id, recipient_id, amount, processing_fee, nsp):
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
