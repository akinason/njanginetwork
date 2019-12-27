from django.conf.urls import url
from .views import *

app_name = 'administration'
urlpatterns = [
    url(r'^$', SummaryView.as_view(), name='summary'),
    url(r'^account/balances/$', UserAccountBalancesView.as_view(),
        name='user_account_balances'),
    url(r'account/(?P<pk>[0-9]+)/details/$',
        UserDetailView.as_view(), name='user_details'),
    url(r'account/list/$', UserListView.as_view(), name='user_list'),
    url(r'account/(?P<user_id>[0-9]+)/transactions/$',
        UserTransactionListView.as_view(), name='transactions'),

    # remuneration routes
    url(r"^remuneration/$", remuneration_list, name="remuneration_list"),
    url(r"^remuneration/create/$", remuneration_create, name="remuneration_create"),
    url(r"^remuneration/(?P<remuneration_id>[0-9]+)/update/$",
        remuneration_update, name="remuneration_update"),
    url(r"^remuneration/(?P<remuneration_id>[0-9]+)/beneficiary_list/$",
        beneficiary_list, name="beneficiary_list"),
    url(r"^remuneration/(?P<remuneration_id>[0-9]+)/transfer_funds/$",
        name="remuneration_funds_transfer"),
]
