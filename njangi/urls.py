from django.conf.urls import url
from .views import *

app_name = 'njangi'
urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^contribute/(?P<level>[1-6]+)/$', ContributionCheckoutView.as_view(), name='contribution_checkout'),
    url(r'^contribute/(?P<level>[1-6]+)/(?P<nsp>[a-z_]+)/confirm/$', NSPCheckoutConfirmView.as_view(),
        name='nsp_contribution_confirmation'),
    url(r'^contribute/done/$', NSPContributionDoneView.as_view(), name='contribution_done'),
    url(r'^network_tools/$', NetworkToolsView.as_view(), name='network_tools'),
    url(r'^new_registration/$', DashboardSignupView.as_view(), name='new_registration'),
    url(r'^wallet/(?P<nsp>[a-z]+)/statement/$', WalletTransactionListView.as_view(), name='statement'),
    url(r'^wallet/(?P<action>[a-z]+)/choice/$', WalletLoadAndWithdrawChoiceView.as_view(),
        name='load_or_withdraw_choice'),
    url(r'^wallet/(?P<nsp>[a-z_]+)/(?P<action>[a-z]+)/$', WalletLoadAndWithdrawView.as_view(),
        name='load_or_withdraw'),
    url(r'^wallet/(?P<nsp>[a-z_]+)/(?P<action>[a-z]+)/(?P<amount>[0-9]+)/confirm/$',
        WalletLoadAndWithdrawConfirmView.as_view(), name='load_or_withdraw_confirm'),
    url(r'^wallet/(?P<nsp>[a-z_]+)/(?P<action>[a-z]+)/done/$', WalletLoadAndWithdrawDoneView.as_view(),
        name='load_or_withdraw_done'),

    # Signup Contribution URLs
    url(r'^signup/contribution/required/$', NSPSignupContributionView.as_view(), name='signup_contribution_required'),
    url(r'^signup/contribution/(?P<nsp>[a-z]+)/checkout/$', NSPSignupContributionCheckoutView.as_view(),
        name='signup_contribution_checkout'),
    url(r'^signup/contribution/done/$', NSPSignupContributionDoneView.as_view(), name='signup_contribution_done'),

    # Premium Service URLs
    url(r'^premium/switch_user/(?P<user_id>[0-9]+)/$', SwitchUserView.as_view(), name='switch_user'),
    url(r'^premium/account/list/$', UserAccountListView.as_view(), name='user_account_list'),
    url(r'^premium/account/create/$', CreateUserAccountView.as_view(), name='add_user_account'),
    url(r'^premium/account/(?P<user_id>[0-9]+)/remove/$', RemoveUserAccountView.as_view(), name='remove_user_account'),
    url(r'^premium/account/packages/list/$', UserAccountPackages.as_view(), name='user_account_packages'),
    url(r'^premium/account/package/subscription/(?P<subscription_type>[a-z]+)/(?P<package_id>[0-9]+)/$',
        UserAccountPackageSubscriptionView.as_view(), name='package_subscription'),

]
