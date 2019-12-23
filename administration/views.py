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


class UserListView(AdminPermissionRequiredMixin, generic.ListView):
    model = UserModel()
    context_object_name = 'user_list'
    template_name = 'administration/user_list.html'
    paginate_by = 20

    def get_queryset(self):
        username = self.request.GET.get('username')
        if self.model.objects.filter(username=username).exists():
            return self.model.objects.filter(username=username)
        else:
            return super(UserListView, self).get_queryset()


class UserDetailView(AdminPermissionRequiredMixin, generic.DetailView):
    model = UserModel()
    context_object_name = 'member'
    template_name = 'administration/user_details.html'


class UserTransactionListView(AdminPermissionRequiredMixin, generic.ListView):

    context_object_name = 'transactions'
    template_name = 'administration/transactions.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(UserTransactionListView, self).get_context_data(**kwargs)
        context['transaction_user'] = self.get_user()
        return context

    def get_user(self):
        """
        Get the user we want to get the list of transactions
        """
        id = self.kwargs.get('user_id')
        if UserModel().objects.filter(pk=id).exists():
            return UserModel().objects.filter(pk=id).get()
        else:
            return UserModel().objects.none()

    def get_queryset(self):
        if self.get_user():
            return wallet_manager.transaction_list(user=self.get_user(), last_x_transactions=10000)
        else:
            return None


# Remuneration views

class RemunerationList(AdminPermissionRequiredMixin, generic.TemplateView):
    template_name = "remuneration/index.html"


remuneration_list = RemunerationList.as_view()
