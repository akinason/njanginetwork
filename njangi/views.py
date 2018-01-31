from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from purse.models import WalletManager, WalletTransDescription
from njangi.models import LevelModel, LEVEL_CONTRIBUTIONS
from django.db.models import Sum, F, Value as V
from django.db.models.functions import Coalesce
from main.forms import SignupForm
from .forms import ContributionConfirmForm, LoadWithdrawForm
from main.utils import get_sponsor
from main.core import NSP
from mailer import services as mailer_services
from njangi.core import add_user_to_njangi_tree, create_user_levels, get_upline_to_pay_upgrade_contribution, \
    get_level_contribution_amount, get_processing_fee_rate
from django.urls import reverse_lazy, reverse
from njangi.models import NSP_CONTRIBUTION_PROCESSING_FEE_RATE, WALLET_CONTRIBUTION_PROCESSING_FEE_RATE, \
    NSP_WALLET_LOAD_PROCESSING_FEE_RATE, NSP_WALLET_WITHDRAWAL_PROCESSING_FEE_RATE, \
    NSP_CONTRIBUTION_PROCESSING_FEE_RATES, WALLET_CONTRIBUTION_PROCESSING_FEE_RATES
from purse.models import MTN_MOBILE_MONEY_PARTNER, ORANGE_MOBILE_MONEY_PARTNER
from django.utils.translation import ugettext_lazy as _
from njangi.tasks import process_contribution, process_payout, process_wallet_load
from django.http import HttpResponseRedirect
import decimal

wallet = WalletManager()
_nsp = NSP()
D = decimal.Decimal


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        # user_level_plus_one = self.request.user.level + 1
        user_levels = LevelModel.objects.filter(user=self.request.user)
        contribution_status = LevelModel.objects.filter(user=self.request.user).aggregate(
            total_contributed=Coalesce(Sum(F('total_sent')), V(0.00)),
            total_received=Coalesce(Sum(F('total_received')), V(0.00))
        )
        mtn_wallet_balance = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        orange_wallet_balance = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        wallet_balance = mtn_wallet_balance + orange_wallet_balance
        context['wallet_balance'] = wallet_balance
        context['total_contributed'] = contribution_status['total_contributed']
        context['total_received'] = contribution_status['total_received']
        context['user_levels'] = user_levels.order_by('level')
        context['LEVEL_CONTRIBUTIONS'] = LEVEL_CONTRIBUTIONS
        context['nsp'] = _nsp
        return context


class NetworkToolsView(generic.TemplateView):
    template_name = 'njangi/network_tools.html'


class DashboardSignupView(generic.CreateView):
    form_class = SignupForm
    template_name = 'njangi/new_registration.html'
    success_url = reverse_lazy("njangi:dashboard")

    def get_form_kwargs(self):
        """
       Returns the keyword arguments for instantiating the form.
       """
        kwargs = super(DashboardSignupView, self).get_form_kwargs()
        if self.request.method in ('GET', 'POST', 'PUT'):
            kwargs.update({'sponsor': get_sponsor(self.request).pk})
        return kwargs

    def form_valid(self, form):
        user = form.save()
        user.set_unique_random_sponsor_id()
        user.set_unique_random_tel1_code()
        user.set_unique_random_tel2_code()
        user.set_unique_random_tel3_code()
        user.save()
        sponsor = get_sponsor(self.request)
        add_user_to_njangi_tree(user=user, sponsor=sponsor)
        create_user_levels(user)
        mailer_services.send_signup_welcome_sms(user_id=user.id)
        mailer_services.send_signup_welcome_email(user_id=user.id)
        return super(DashboardSignupView, self).form_valid(form)


class ContributionCheckoutView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/contribution_checkout.html'

    def get_context_data(self, **kwargs):
        level = kwargs['level']
        amount = get_level_contribution_amount(level)
        recipient = get_upline_to_pay_upgrade_contribution(user_id=self.request.user.id, level=level)
        context = super(ContributionCheckoutView, self).get_context_data(**kwargs)
        context['level'] = level
        context['amount'] = amount
        context['recipient'] = recipient
        context['mtn_wallet_balance'] = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        context['orange_wallet_balance'] = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        context['nsp'] = _nsp
        return context

# class WalletCheckoutConfirmView(LoginRequiredMixin, generic.TemplateView):


class NSPContributionDoneView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/contribution_done.html'


class NSPCheckoutConfirmView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/nsp_checkout_confirm.html'
    form_class = ContributionConfirmForm

    def get_context_data(self, **kwargs):
        context = super(NSPCheckoutConfirmView, self).get_context_data(**kwargs)
        level = kwargs['level']
        amount = get_level_contribution_amount(level)
        recipient = get_upline_to_pay_upgrade_contribution(user_id=self.request.user.id, level=level)
        nsp = kwargs['nsp']
        processing_fee = amount * get_processing_fee_rate(level=level, nsp=nsp)

        total = amount + processing_fee
        message = ''
        tel = ''
        _message = _(
            'We will send you a request of %(total)s to your %(nsp)s mobile number %(tel)s through our partner '
            '%(partner)s. Please confirm the operation on your mobile phone so we can process your contribution.'
        )
        _message2 = _(
            "We will withdraw the sum of %(total)s from your %(nsp)s to contribute. Confirm the operation so we can "
            "process your contribution."
        )

        if nsp == _nsp.mtn():
            partner = MTN_MOBILE_MONEY_PARTNER
            tel = ''
            if self.request.user.tel1:
                tel = self.request.user.tel1.as_national

            message = _message % {'total': total, 'nsp': nsp, 'partner': partner, 'tel': tel}

        elif nsp == _nsp.orange():
            partner = ORANGE_MOBILE_MONEY_PARTNER
            if self.request.user.tel2:
                tel = self.request.user.tel2.national_number
            message = _message % {'total': total, 'nsp': nsp, 'partner': partner, 'tel': tel}

        elif nsp == _nsp.mtn_wallet() or nsp == _nsp.orange_wallet():
            message = _message2 % {'total': total, 'nsp': nsp.replace('_', ' ')}
        context['level'] = level
        context['message'] = message
        context['amount'] = amount
        context['processing_fee'] = processing_fee
        context['tel'] = tel
        context['nsp'] = nsp
        context['total'] = total
        context['recipient'] = recipient
        return context

    def post(self, request, *args, **kwargs):
        level = self.get_context_data(**kwargs).pop('level')
        amount = self.get_context_data(**kwargs).pop('amount')
        processing_fee = self.get_context_data(**kwargs).pop('processing_fee')
        total = self.get_context_data(**kwargs).pop('total')
        recipient = self.get_context_data(**kwargs).pop('recipient')
        nsp = self.get_context_data(**kwargs).pop('nsp')
        sender_tel = ''

        if nsp == _nsp.mtn():
            if request.user.tel1 and request.user.tel1_is_verified:
                sender_tel = request.user.tel1.national_number
            else:
                return render(request, 'njangi/error.html', context={
                    'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp}, 'status': 'warning'
                })
        elif nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })

            # if request.user.tel2 and request.user.tel2_is_verified:
            #     sender_tel = request.user.tel2.national_number
            # else:
            #     return render(request, 'njangi/error.html', context={
            #         'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp}, 'status': 'warning'
            #     })
        elif nsp == _nsp.mtn_wallet():
            if wallet.balance(user=self.request.user, nsp=_nsp.mtn()) < total:
                return render(request, 'njangi/error.html', context={
                    'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
                    'status': 'warning'
                })
        elif nsp == _nsp.orange_wallet():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
        #     if wallet.balance(user=self.request.user, nsp=_nsp.orange()) < total:
        #         return render(request, 'njangi/error.html', context={
        #             'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
        #             'status': 'warning'
        #         })
        # else:
        #     return render(request, 'njangi/error.html', context={
        #         'message': _('Invalid request.'), 'status': 'warning'
        #     })

        response = process_contribution(user_id=request.user.id, recipient_id=recipient.id, level=level,
                                        amount=amount, nsp=nsp, sender_tel=sender_tel, processing_fee=processing_fee)

        return HttpResponseRedirect(reverse('njangi:contribution_done'))

    def get(self, request, *args, **kwargs):
        nsp = self.get_context_data(**kwargs).pop('nsp')
        total = self.get_context_data(**kwargs).pop('total')
        sender_tel = ''
        if nsp == _nsp.mtn():
            if request.user.tel1 and request.user.tel1_is_verified:
                sender_tel = request.user.tel1.national_number
            else:
                return render(request, 'njangi/error.html', context={
                    'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp}, 'status': 'warning'
                })
        elif nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
            # if request.user.tel2 and request.user.tel2_is_verified:
            #     sender_tel = request.user.tel2.national_number
            # else:
            #     return render(request, 'njangi/error.html', context={
            #         'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp}, 'status': 'warning'
            #     })
        elif nsp == _nsp.mtn_wallet():
            if wallet.balance(user=self.request.user, nsp=_nsp.mtn()) < total:
                return render(request, 'njangi/error.html', context={
                    'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
                    'status': 'warning'
                })
        elif nsp == _nsp.orange_wallet():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
            # if wallet.balance(user=self.request.user, nsp=_nsp.orange()) < total:
            #     return render(request, 'njangi/error.html', context={
            #         'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
            #         'status': 'warning'
            #     })
        else:
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid request.'), 'status': 'warning'
            })

        return super(NSPCheckoutConfirmView, self).get(request, *args, **kwargs)


class WalletTransactionListView(LoginRequiredMixin, generic.ListView):
    template_name = 'njangi/statement.html'
    paginate_by = 10
    context_object_name = 'transaction_list'

    def get_queryset(self):
        nsp = self.kwargs['nsp']
        return wallet.transaction_list(user=self.request.user, nsp=nsp)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(WalletTransactionListView, self).get_context_data(object_list=None, **kwargs)
        nsp = self.kwargs['nsp']
        context['nsp'] = nsp
        balance = 0.00
        if nsp == _nsp.mtn():
            balance = wallet.balance(user=self.request.user, nsp=nsp)
        elif nsp == _nsp.orange():
            balance = wallet.balance(user=self.request.user, nsp=nsp)
        else:
            balance = 0
        context['balance'] = balance

        return context


class WalletLoadAndWithdrawChoiceView(LoginRequiredMixin, generic.TemplateView):
    """
    View that displays the wallets and their balances for the user to chose which to
    perform an action on.
    """
    template_name = 'njangi/checkout/load_or_withdraw_wallet_choice.html'

    def get_context_data(self, **kwargs):
        context = super(WalletLoadAndWithdrawChoiceView, self).get_context_data(**kwargs)
        context['mtn_wallet_balance'] = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        context['orange_wallet_balance'] = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        context['action'] = self.kwargs['action']
        return context


class WalletLoadAndWithdrawView(LoginRequiredMixin, generic.TemplateView):
    """
    A view that receives the user's wallet choice and action and displays a form
    for the user to provide an amount. Then on post, processes the operation and
    redirects to the confirmation page.
    """
    template_name = 'njangi/checkout/load_withdraw_checkout.html'

    def get_context_data(self, **kwargs):
        context = super(WalletLoadAndWithdrawView, self).get_context_data(**kwargs)
        context['action'] = self.kwargs['action']
        nsp = self.kwargs['nsp']
        context['nsp'] = nsp
        balance = 0.00
        if nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            balance = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        elif nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            balance = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        else:
            balance = 0.00
        context['balance'] = balance
        return context

    def post(self, request, *args, **kwargs):
        nsp = self.kwargs['nsp']
        action = self.kwargs['action']
        amount = D(request.POST.get('amount'))
        balance = D(self.get_context_data(**kwargs).get('balance'))

        if nsp not in [_nsp.orange_wallet(), _nsp.mtn_wallet()]:
            return render(request, 'njangi/error.html', context={
                'message': _('Unknown Network service provider %(nsp)s.') % {'nsp': nsp},
                'status': 'warning'
            })

        # This code should be eliminated onces the orange money API is itegrated.
        # **********Code start***********
        elif nsp == _nsp.orange_wallet() or nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
        #************End of code*********

        elif amount < 0:
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid Amount %(amount)s. Amounts must be greater than zero.') % {'amount': amount},
                'status': 'warning'
            })
        elif action not in ['load', 'withdraw']:
                return render(request, 'njangi/error.html', context={
                    'message': _('Invalid action %(action)s.') % {'action': action},
                    'status': 'warning'
                })
        elif amount > balance and action == 'withdraw':
            return render(request, 'njangi/error.html', context={
                'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
                'status': 'warning'
            })

        return HttpResponseRedirect(
                reverse('njangi:load_or_withdraw_confirm', kwargs={'nsp': nsp, 'action': action, 'amount': amount})
                )

    def get(self, request, *args, **kwargs):
        nsp = self.kwargs['nsp']
        action = self.kwargs['action']

        if nsp not in [_nsp.orange_wallet(), _nsp.mtn_wallet()]:
            return render(request, 'njangi/error.html', context={
                'message': _('Unknown Network service provider %(nsp)s.') % {'nsp': nsp},
                'status': 'warning'
            })

        # This code should be eliminated onces the orange money API is itegrated.
        # **********Code start***********
        elif nsp == _nsp.orange_wallet() or nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
        #************End of code*********

        elif action not in ['load', 'withdraw']:
                return render(request, 'njangi/error.html', context={
                    'message': _('Invalid action %(action)s.') % {'action': action},
                    'status': 'warning'
                })
        elif nsp == _nsp.mtn_wallet() and (not request.user.tel1 or not request.user.tel1_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.mtn()},
                'status': 'warning'
            })
        elif nsp == _nsp.orange_wallet() and (not request.user.tel2 or not request.user.tel2_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.orange()},
                'status': 'warning'
            })

        return super(WalletLoadAndWithdrawView, self).get(request, *args, **kwargs)


class WalletLoadAndWithdrawConfirmView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/load_or_withdraw_confirm.html'

    def get_context_data(self, **kwargs):
        context = super(WalletLoadAndWithdrawConfirmView, self).get_context_data(**kwargs)
        context['action'] = self.kwargs['action']
        nsp = self.kwargs['nsp']
        action = self.kwargs['action']
        amount = D(self.kwargs['amount'])
        context['nsp'] = nsp
        context['action'] = action
        context['amount'] = amount
        balance = 0.00
        if nsp == _nsp.mtn() or nsp == _nsp.mtn_wallet():
            balance = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        elif nsp == _nsp.orange() or nsp == _nsp.orange_wallet():
            balance = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        else:
            balance = 0.00
        context['balance'] = balance
        processing_fee = 0.00
        if action == 'load':
            processing_fee = amount * D(NSP_WALLET_LOAD_PROCESSING_FEE_RATE)
        elif action == 'withdraw':
            processing_fee = amount * D(NSP_WALLET_WITHDRAWAL_PROCESSING_FEE_RATE)
        _processing_fee = int(processing_fee)
        context['processing_fee'] = _processing_fee
        context['total'] = amount + _processing_fee
        return context

    def get(self, request, *args, **kwargs):
        nsp = self.get_context_data(**kwargs).get('nsp')
        action = self.get_context_data(**kwargs).get('action')

        if nsp not in [_nsp.orange_wallet(), _nsp.mtn_wallet()]:
            return render(request, 'njangi/error.html', context={
                'message': _('Unknown Network service provider %(nsp)s.') % {'nsp': nsp},
                'status': 'warning'
            })

        # This code should be eliminated onces the orange money API is itegrated.
        # **********Code start***********
        elif nsp == _nsp.orange_wallet() or nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
        #************End of code*********

        elif action not in ['load', 'withdraw']:
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid action %(action)s.') % {'action': action},
                'status': 'warning'
            })
        elif nsp == _nsp.mtn_wallet() and (not request.user.tel1 or not request.user.tel1_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.mtn()},
                'status': 'warning'
            })
        elif nsp == _nsp.orange_wallet() and (not request.user.tel2 or not request.user.tel2_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.orange()},
                'status': 'warning'
            })

        return super(WalletLoadAndWithdrawConfirmView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        nsp = self.get_context_data(**kwargs).get('nsp')
        action = self.get_context_data(**kwargs).get('action')
        amount = self.get_context_data(**kwargs).get('amount')
        balance = self.get_context_data(**kwargs).get('balance')
        total = self.get_context_data(**kwargs).get('total')
        processing_fee = self.get_context_data(**kwargs).get('processing_fee')

        if nsp not in [_nsp.orange_wallet(), _nsp.mtn_wallet()]:
            return render(request, 'njangi/error.html', context={
                'message': _('Unknown Network service provider %(nsp)s.') % {'nsp': nsp},
                'status': 'warning'
            })

        # This code should be eliminated onces the orange money API is itegrated.
        # **********Code start***********
        elif nsp == _nsp.orange_wallet() or nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be restored soon.'), 'status': 'info'
                })
        #************End of code*********

        elif action not in ['load', 'withdraw']:
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid action %(action)s.') % {'action': action},
                'status': 'warning'
            })
        elif total > balance and action == 'withdraw':
            return render(request, 'njangi/error.html', context={
                'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
                'status': 'warning'
            })
        elif nsp == _nsp.mtn_wallet() and (not request.user.tel1 or not request.user.tel1_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.mtn()},
                'status': 'warning'
            })
        elif nsp == _nsp.orange_wallet() and (not request.user.tel2 or not request.user.tel2_is_verified):
            return render(request, 'njangi/error.html', context={
                'message': _('Invalid or unverified %(nsp)s phone number.') % {'nsp': _nsp.orange()},
                'status': 'warning'
            })
        else:
            response = {}

            if nsp == _nsp.orange_wallet() and action == 'withdraw':
               response = process_payout(
                   request.user.id, amount=amount, nsp=_nsp.orange(), processing_fee=processing_fee
               )
            elif nsp == _nsp.orange_wallet() and action == 'load':
                response = process_wallet_load(
                    user_id=request.user.id, amount=amount, nsp=_nsp.orange(), charge=processing_fee
                )
            elif nsp == _nsp.mtn_wallet() and action == 'withdraw':
                response = process_payout(
                    request.user.id, amount=amount, nsp=_nsp.mtn(), processing_fee=processing_fee
                )
            elif nsp == _nsp.mtn_wallet() and action == 'load':
                response = process_wallet_load(
                    user_id=request.user.id, amount=amount, nsp=_nsp.mtn(), charge=processing_fee
                )
        return HttpResponseRedirect(
            reverse('njangi:load_or_withdraw_done', kwargs={'nsp': nsp, 'action': action})
        )


class WalletLoadAndWithdrawDoneView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/load_or_withdraw_done.html'

    def get_context_data(self, **kwargs):
        context = super(WalletLoadAndWithdrawDoneView, self).get_context_data(**kwargs)
        action = self.kwargs['action']
        nsp = self.kwargs['nsp']
        context['message'] = _('Your %(nsp)s %(action)s is been processed.') % \
                        {'nsp': nsp.replace('_', ' '), 'action': action}
        return context
