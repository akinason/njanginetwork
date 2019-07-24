import datetime

from django.db.models import Q

from django.contrib.auth import get_user_model
from njangi.core import create_user_levels, add_user_to_njangi_tree
from mailer import services as mailer_services
from njangi.models import LevelModel
from njangi import tasks
from purse.models import Balance, WalletModel, Coalesce, Q, Sum, WalletTransStatus, D, V, F


def create_admin_user(username, password):
    failed_reason = ''
    if get_user_model().objects.filter(username=username).exists():
        failed_reason = 'Username already exist.'
        return failed_reason
    else:
        user = get_user_model().objects.create(
            username=username, first_name='Awa', last_name='kinason', is_active=True,
            gender='male', is_admin=True, tel1='+23765397307', tel2='+237655916762'
        )
        user.set_password(password)
        user.sponsor_id = user.id
        user.level = 6
        user.set_unique_random_sponsor_id()
        user.set_unique_random_tel1_code()
        user.set_unique_random_tel2_code()
        user.set_unique_random_tel3_code()
        user.tel1_is_verified = True
        user.tel2_is_verified = True
        user.tel3_is_verified = True
        user.email_is_verified = True
        user.save()
        add_user_to_njangi_tree(user=user)
        create_user_levels(user=user)
        return user


def send_mtn_mass_sms(body):
    number_list = []
    users = get_user_model().objects.filter(tel1__isnull=False, is_admin=False)
    for user in users:
        try:
            if user.tel1:
                tel = user.tel1.as_international
                _tel = tel.replace("+", "").replace(" ", "")
                number_list.append(_tel)
        except Exception:
            pass
    response = mailer_services.send_1s2u_mass_sms(to_numbers=number_list, body=body)
    return response


def send_orange_mass_sms(body):
    number_list = []
    users = get_user_model().objects.filter(tel2__isnull=False, is_admin=False)
    for user in users:
        try:
            if user.tel1:
                tel = user.tel2.as_international
                _tel = tel.replace("+", "").replace(" ", "")
                number_list.append(_tel)
        except Exception:
            pass
    response = mailer_services.send_1s2u_mass_sms(to_numbers=number_list, body=body)
    return response


def send_mass_sms(body):
    number_list = []
    tel = ''
    users = get_user_model().objects.filter(Q(tel1__isnull=False) | Q(tel2__isnull=False), is_admin=False)
    for user in users:
        try:
            if user.tel1 and not user.tel2:
                tel = user.tel1.as_international
            elif not user.tel1 and user.tel2:
                tel = user.tel2.as_international
            elif user.tel1 and user.tel2:
                tel = user.tel1.as_international
            else:
                pass
            _tel = tel.replace("+", "").replace(" ", "")
            number_list.append(_tel)
        except Exception:
            pass
    response = mailer_services.send_1s2u_mass_sms(to_numbers=number_list, body=body)
    return response


def mass_increase_next_payment_duration(days):
    levels = LevelModel.objects.filter(next_payment__isnull=False)
    for level in levels:
        level.is_active = True
        level.next_payment += datetime.timedelta(days=days)
        level.save()
    return levels.count()


def mass_update_user_balances():
    users = get_user_model().objects.all()
    results = []
    for user in users:
        balance, created = Balance.objects.get_or_create(user=user)
        if created:
            trans_status = WalletTransStatus()
            wallet = WalletModel.objects.filter(user=user).filter(
                Q(status=trans_status.complete()) | Q(status=trans_status.success()) | Q(status=trans_status.pending())
            )

            wallet = wallet.aggregate(
                balance=Coalesce(Sum(F('amount')+F('charge')), V(0.00))
            )
            account_balance = D(wallet['balance'])
            balance.available_balance = account_balance
            balance.save()
            results.append({"user": user.username, "balance": account_balance})
    return results


def mass_upgrade_users():
    results = []
    users = get_user_model().objects.filter(is_admin=False, is_in_network=True, level__gt=0).all()
    for user in users:
        res = tasks.create_upgrade_contribution_reserves(
            recipient=user, level=user.level, amount_received=0, upgrade_balance=user.balance.available_balance
        )
        results.append(res)
    return results
