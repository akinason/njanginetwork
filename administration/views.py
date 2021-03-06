from django.contrib.auth import get_user_model as UserModel
from django.http import Http404
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views import generic
from django.contrib.auth import authenticate
from django.contrib import messages

from administration.models import Remuneration, Beneficiary, remuneration_status
from administration.forms import RemunerationForm
from administration import task
from main.mixins import AdminPermissionRequiredMixin
from marketplace.models import MarketManager
from purse.models import WalletManager
from administration.service import pay_remunerations


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
class RemunerationList(AdminPermissionRequiredMixin, generic.ListView):
    model = Remuneration
    queryset = Remuneration.objects.all()
    template_name = "remuneration/index.html"
    context_object_name = 'remunerations'

remuneration_list = RemunerationList.as_view()


class RemunerationCreate(AdminPermissionRequiredMixin, generic.CreateView):
    model = Remuneration
    form_class = RemunerationForm
    template_name = "remuneration/renumeration_create.html"

    def get_success_url(self):
        return reverse('administration:remuneration_list')

    def form_valid(self, form):
        # assigning background task for creating beneficiaries...
        remuneration = form.save(commit=True)
        task.create_beneficiaries.delay(remuneration.id)

        return super(RemunerationCreate, self).form_valid(form)


remuneration_create = RemunerationCreate.as_view()


class RemunerationUpdate(AdminPermissionRequiredMixin, generic.UpdateView):
    template_name = "remuneration/remuneration_update.html"
    form_class = RemunerationForm
    context_object_name = "remuneration"

    def get_object(self, *args, **kwargs):
        remuneration_id = self.kwargs.get('remuneration_id')
        remuneration = get_object_or_404(Remuneration, pk=remuneration_id)
        return remuneration

    def get_success_url(self):
        return reverse('administration:remuneration_list')

    def form_valid(self, form):
        # deleting all the old beneficiaries related to this remuneration
        remuneration_id = self.kwargs.get('remuneration_id')
        remuneration = get_object_or_404(Remuneration, pk=remuneration_id)

        if remuneration != remuneration_status.paid() or remuneration != remuneration_status.partially_paid():
            old_beneficiaries = Beneficiary.objects.filter(
                remuneration=remuneration)
            old_beneficiaries.delete()

            # assigning background task for creating beneficiaries...
            remuneration = form.save(commit=True)
            task.create_beneficiaries.delay(remuneration.id)

        return super(RemunerationUpdate, self).form_valid(form)


remuneration_update = RemunerationUpdate.as_view()


class BeneficiaryList(AdminPermissionRequiredMixin, generic.ListView):
    template_name = "remuneration/beneficiary_list.html"
    context_object_name = 'beneficiaries'
    model = Beneficiary()

    def get_queryset(self, *args, **kwargs):
        remuneration_id = self.kwargs.get('remuneration_id')
        beneficiaries = Beneficiary.objects.filter(
            remuneration__id=remuneration_id)
        return beneficiaries

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        remuneration = get_object_or_404(
            Remuneration, pk=self.kwargs.get('remuneration_id'))
        context['remuneration'] = remuneration
        context['remuneration_status'] = remuneration_status
        return context
    

beneficiary_list = BeneficiaryList.as_view()


class TransferFundsConfirmView(AdminPermissionRequiredMixin, generic.View):
    template_name = 'remuneration/authentification.html'
    
    def get(self, request, *args, **kwargs):
        request = self.request
        context = self.get_context_object(*args, **kwargs)
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        remuneration_id = request.POST['remuneration_id']
        user = authenticate(username=request.user.username, password=request.POST['password'])
        
        if not user or user != request.user:
            messages.add_message(request=request, level=messages.INFO, message="Sorry, you are not allowed to perform this operation")
            return redirect('administration:remuneration_funds_transfer_confirmation', remuneration_id=remuneration_id)
        
        else:
            pay_remunerations(remuneration_id)
            messages.add_message(request=request, level=messages.INFO, message="Remuneration is being processsed")
            return redirect('administration:remuneration_list')
    
    def get_context_object(self, *args, **kwargs):
        context = {}
        remuneration = get_object_or_404(
            Remuneration, pk=self.kwargs.get('remuneration_id'))
        context['remuneration'] = remuneration
        context['remuneration_status'] = remuneration_status
        return context


transfer_funds_confirm = TransferFundsConfirmView.as_view()