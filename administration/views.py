from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import Http404
from django.views import generic
from django.contrib.auth import get_user_model as UserModel

from main.mixins import AdminPermissionRequiredMixin
from marketplace.models import MarketManager
from purse.models import WalletManager
from administration.models import Remuneration, Beneficiary
from administration.forms import RemunerationForm
from njanginetwork.celery import app

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
        context = super(UserAccountBalancesView,
                        self).get_context_data(**kwargs)
        context['total_user_balance'] = wallet_manager.get_total_balance()
        return context

    def get_queryset(self):
        if self.user:
            self.wallet_balances = wallet_manager.get_account_balances(
                user=self.user)
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
        context = super(UserTransactionListView,
                        self).get_context_data(**kwargs)
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

# @app.task
# def create_beneficiary_list(users, remuneration_id, *args, **kwargs):
#     for user in users:
#         try:
#             renumeration = Remuneration.objects.
#         renumeration = Remuneration.
#         new_beneficiary = Beneficiary()


class RemunerationList(AdminPermissionRequiredMixin, generic.TemplateView):
    model = Remuneration
    queryset = Remuneration.objects.all()
    template_name = "remuneration/index.html"
    # create_beneficiary_list.delay()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remunerations'] = self.queryset
        return context


remuneration_list = RemunerationList.as_view()


class RemunerationCreate(AdminPermissionRequiredMixin, generic.CreateView):
    model = Remuneration
    form_class = RemunerationForm
    template_name = "remuneration/renumeration_create.html"

    def get_success_url(self):
        return reverse('administration:remuneration_list')

    def form_valid(self, form):
        request = self.request
        print(form.cleaned_data)
        # form.save(commit=True)
        return super(RemunerationCreate, self).form_valid(form)


remuneration_create = RemunerationCreate.as_view()


class RemunerationUpdate(AdminPermissionRequiredMixin, generic.UpdateView):
    template_name = "remuneration/remuneration_update.html"
    form_class = RemunerationForm
    context_object_name = "remuneration"

    def get_object(self, *args, **kwargs):
        remuneration_id = self.kwargs.get('remuneration_id')

        try:
            remuneration = Remuneration.objects.get(id=remuneration_id)
        except Remuneration.DoesNotExist:
            raise Http404("Remuneration not found")

        return remuneration

    def get_success_url(self):
        return reverse('administration:remuneration_list')


remuneration_update = RemunerationUpdate.as_view()


class BeneficiaryList(AdminPermissionRequiredMixin, generic.ListView):
    template_name = "remuneration/beneficiary_list.html"
    context_object_name = 'beneficiaries'
    model = Beneficiary()

    def get_queryset(self, *args, **kwargs):
        remuneration_id = self.kwargs.get('remuneration_id')
        beneficiaries = Beneficiary.objects.filter(
            remuneration__id=remuneration_id)
        print(beneficiaries)
        return beneficiaries

    def get_context_data(self, *args, **kwargs):
        context = super(BeneficiaryList, self).get_context_data(
            *args, **kwargs)
        print(context)
        return context


beneficiary_list = BeneficiaryList.as_view()
