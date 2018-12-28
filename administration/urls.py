from django.conf.urls import url
from .views import *

app_name = 'administration'
urlpatterns = [
    url(r'^$', SummaryView.as_view(), name='summary'),
    url(r'^account/balances/$', UserAccountBalancesView.as_view(), name='user_account_balances'),
    url(r'account/(?P<pk>[0-9]+)/details/$', UserDetailView.as_view(), name='user_details'),
    url(r'account/list/$', UserListView.as_view(), name='user_list'),
    url(r'account/(?P<user_id>[0-9]+)/transactions/$', UserTransactionListView.as_view(), name='transactions'),
]
