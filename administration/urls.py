from django.conf.urls import url
from .views import *

app_name = 'administration'
urlpatterns = [
    url(r'^$', SummaryView.as_view(), name='summary'),
    url(r'^account/balances', UserAccountBalancesView.as_view(), name='user_account_balances'),
    
]