from django.test import TestCase
from .service import payment_complete_process as pcp
from django.contrib.auth import get_user_model as UserModel
# Create your tests here.


def cs(user_id, sponsor_id):
    user = UserModel().objects.get(pk=user_id)
    user.sponsor = sponsor_id
    user.save()
    return user.sponsor


def ts(invoice_id):
    print(pcp(invoice_id))
