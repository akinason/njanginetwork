from django.shortcuts import render
from django.views import generic
from django.contrib.auth import get_user_model as UserModel

from main.mixins import AdminPermissionRequiredMixin
from marketplace.models import MarketManager
from purse.models import WalletManager

wallet_manager = WalletManager()
market_manager = MarketManager()


class SummaryView(AdminPermissionRequiredMixin, generic.TemplateView):
    template_name = 'administration/summary.html'

    def get_context_data(self, **kwargs):
        context = super(SummaryView, self).get_context_data(**kwargs)
        context['total_user_balance'] = wallet_manager.get_total_balance()
        context['total_admin_balance'] = wallet_manager.get_total_admin_balance()
        context['total_charge'] = wallet_manager.get_total_charge()
        context['total_invoice_count'] = market_manager.get_total_invoice_count()
        context['total_commission_paid'] = market_manager.get_total_commission_paid()
        context['marketplace_income'] = market_manager.get_total_marketplace_income()
        return context


class UserAccountBalancesView(AdminPermissionRequiredMixin, generic.ListView):
    template_name = 'administration/user_account_balances.html'
    context_object_name = 'balances'
    paginate_by = 25
    user = ''
    wallet_balances = ''

    def get_context_data(self, **kwargs):
        context = super(UserAccountBalancesView, self).get_context_data(**kwargs)
        context['total_user_balance'] = wallet_manager.get_total_balance()
        return context

    def get_queryset(self):
        if self.user:
            self.wallet_balances = wallet_manager.get_account_balances(user=self.user)
        else:
            self.wallet_balances = wallet_manager.get_account_balances()

        return self.wallet_balances
        
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')

        try:
            self.user = UserModel().objects.get(username=username)
        except UserModel().DoesNotExist:
            pass

        return super(UserAccountBalancesView, self).get(request, *args, **kwargs)
