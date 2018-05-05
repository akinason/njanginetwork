import decimal

from django.contrib.auth import get_user_model as UserModel, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Value as V
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views import generic


from mailer import services as mailer_services
from main.core import NSP
from main.forms import SignupForm
from main.mixins import ContributionRequiredMixin
from main.utils import get_sponsor, get_promoter
from njangi.core import (
    add_user_to_njangi_tree, create_user_levels, get_upline_to_pay_upgrade_contribution, get_level_contribution_amount,
    get_processing_fee_rate
)
from njangi.forms import ContributionConfirmForm
from njangi.models import (
    UserAccountSubscriptionType, NSP_WALLET_LOAD_PROCESSING_FEE_RATE, NSP_WALLET_WITHDRAWAL_PROCESSING_FEE_RATE,
    LevelModel, LEVEL_CONTRIBUTIONS, NjangiTree, UserAccountManager
)
from njangi.tasks import process_wallet_contribution
from purse import services as purse_services
from purse.models import WalletManager, MTN_MOBILE_MONEY_PARTNER, ORANGE_MOBILE_MONEY_PARTNER,  MOMOPurpose

wallet = WalletManager()
account_manager = UserAccountManager()
_nsp = NSP()
D = decimal.Decimal
momo_purpose = MOMOPurpose()
subscription_types = UserAccountSubscriptionType()


class DashboardView(ContributionRequiredMixin, generic.TemplateView):
    template_name = 'njangi/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        user_node = None
        try:
            user_node = NjangiTree.objects.filter(user=self.request.user).get()
        except Exception:
            pass
        user_levels = LevelModel.objects.filter(user=self.request.user)
        contribution_status = LevelModel.objects.filter(user=self.request.user).aggregate(
            total_contributed=Coalesce(Sum(F('total_sent')), V(0.00)),
            total_received=Coalesce(Sum(F('total_received')), V(0.00))
        )
        mtn_wallet_balance = wallet.balance(user=self.request.user, nsp=_nsp.mtn())
        orange_wallet_balance = wallet.balance(user=self.request.user, nsp=_nsp.orange())
        today = timezone.now().date()
        wallet_balance = mtn_wallet_balance + orange_wallet_balance
        context['wallet_balance'] = wallet_balance
        context['total_contributed'] = contribution_status['total_contributed']
        context['total_received'] = contribution_status['total_received']
        context['user_levels'] = user_levels.order_by('level')
        context['total_users'] = UserModel().objects.filter(is_admin=False).count()
        context['LEVEL_CONTRIBUTIONS'] = LEVEL_CONTRIBUTIONS
        context['nsp'] = _nsp
        context['today_users'] = UserModel().objects.filter(date_joined__date=today, is_admin=False).count()

        if user_node:
            context['my_network_users'] = user_node.get_descendant_count()
        else:
            context['my_network_users'] = 0
        return context


class NetworkToolsView(generic.TemplateView):
    template_name = 'njangi/network_tools.html'

    def get(self, request, *args, **kwargs):
        return super(NetworkToolsView, self).get(request, *args, **kwargs)


class DashboardSignupView(ContributionRequiredMixin, generic.CreateView):
    form_class = SignupForm
    template_name = 'njangi/new_registration.html'
    success_url = reverse_lazy("njangi:dashboard")

    def get_form_kwargs(self):
        """
       Returns the keyword arguments for instantiating the form.
       """
        kwargs = super(DashboardSignupView, self).get_form_kwargs()
        if self.request.method in ('GET', 'POST', 'PUT'):
            kwargs.update({'sponsor': get_sponsor(self.request).pk, 'promoter': get_promoter(self.request)})
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


class ContributionCheckoutView(ContributionRequiredMixin, generic.TemplateView):
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


class NSPContributionDoneView(ContributionRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/contribution_done.html'


class NSPCheckoutConfirmView(ContributionRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/nsp_checkout_confirm.html'
    form_class = ContributionConfirmForm

    def get_context_data(self, **kwargs):
        context = super(NSPCheckoutConfirmView, self).get_context_data(**kwargs)
        level = kwargs['level']
        amount = get_level_contribution_amount(level)
        recipient = get_upline_to_pay_upgrade_contribution(user_id=self.request.user.id, level=level)
        nsp = kwargs['nsp']
        processing_fee = round(amount * get_processing_fee_rate(level=level, nsp=nsp), 0)

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
                purse_services.request_momo_deposit.delay(
                    phone_number=sender_tel, amount=total, user_id=self.request.user.id, nsp=nsp, level=level,
                    purpose=momo_purpose.contribution(), recipient_id=recipient.id, charge=processing_fee
                )
            else:
                return render(request, 'njangi/error.html', context={
                    'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp}, 'status': 'warning'
                })
        elif nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences,'
                                 ' it will be restored soon.'), 'status': 'info'
                })

            # if request.user.tel2 and request.user.tel2_is_verified:
            #     sender_tel = request.user.tel2.national_number
            #     purse_services.request_momo_deposit.delay(
            #         phone_number=sender_tel, amount=total, user_id=self.request.user.id, nsp=nsp, level=level,
            #         purpose=momo_purpose.contribution(), recipient_id=recipient.id, charge=processing_fee
            #     )
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
            else:
                process_wallet_contribution.delay(
                    level=level, nsp=nsp, user_id=request.user.id, processing_fee=processing_fee
                )
        elif nsp == _nsp.orange_wallet():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, '
                                 'it will be restored soon.'), 'status': 'info'
                })
            # if wallet.balance(user=self.request.user, nsp=_nsp.orange()) < total:
            #     return render(request, 'njangi/error.html', context={
            #         'message': _('Insufficient funds in your %(nsp)s.') % {'nsp': nsp.replace('_', ' ')},
            #         'status': 'warning'
            #     })
            # else:
            #     process_wallet_contribution.delay(
            #         level=level, nsp=nsp, user_id=request.user.id, processing_fee=processing_fee
            #     )
        # else:
        #     return render(request, 'njangi/error.html', context={
        #         'message': _('Invalid request.'), 'status': 'warning'
        #     })

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
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, '
                                 'it will be restored soon.'), 'status': 'info'
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
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences,'
                                 ' it will be restored soon.'), 'status': 'info'
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


class NSPSignupContributionView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/signup_contribution_notification.html'

    def get(self, request, *args, **kwargs):
        if request.user.has_contributed:
            return HttpResponseRedirect(reverse('njangi:dashboard'))
        else:
            return super(NSPSignupContributionView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NSPSignupContributionView, self).get_context_data(**kwargs)
        context['contribution_amount'] = round(LEVEL_CONTRIBUTIONS[1])
        return context


class NSPSignupContributionCheckoutView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/signup_contribution_checkout.html'

    def get_context_data(self, **kwargs):
        nsp = kwargs.get('nsp')
        amount = get_level_contribution_amount(1)
        processing_fee = round(amount * get_processing_fee_rate(1, nsp))
        context = super(NSPSignupContributionCheckoutView, self).get_context_data(**kwargs)
        context['service_provider'] = nsp
        context['contribution_amount'] = amount
        context['processing_fee'] = processing_fee
        context['total'] = round(amount + processing_fee)
        return context

    def get(self, request, *args, **kwargs):
        nsp = kwargs.get('nsp')
        if request.user.has_contributed:
            return HttpResponseRedirect(reverse('njangi:dashboard'))

        if nsp not in [_nsp.mtn(), _nsp.orange()]:
            content = "<h2>%s</h2>" % _('Sorry the URL you requested was not found on this server')
            return HttpResponseNotFound(content)
        else:
            if nsp == _nsp.orange():
                subject = "No offence"
                message = _("We are sorry that Orange Money services are temporally not available. We will inform you "
                            "ones we set it up.")
                return render(request, 'njangi/checkout/notification.html', {'subject': subject, 'message': message})
            return super(NSPSignupContributionCheckoutView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        nsp = request.POST.get('nsp')
        amount = request.POST.get('contribution_amount')
        processing_fee = request.POST.get('processing_fee')
        total = request.POST.get('total')
        level = 1

        if nsp == _nsp.orange():
            subject = "No offence"
            message = _("We are sorry that Orange Money services are temporally not available. We will inform you "
                        "ones we set it up.")
            return render(request, 'njangi/checkout/notification.html', {'subject': subject, 'message': message})
        elif nsp == _nsp.mtn():
            if request.user.tel1 and request.user.tel1_is_verified:
                sender_tel = request.user.tel1.national_number
                purse_services.request_momo_deposit.delay(
                    phone_number=sender_tel, amount=total, user_id=request.user.id, nsp=nsp, level=level,
                    purpose=momo_purpose.signup_contribution(), charge=processing_fee
                )
            else:
                return render(request, 'njangi/checkout/notification.html', context={
                    'message': _('Please provide or verify your %(nsp)s number.') % {'nsp': nsp.upper()},
                    'subject': _('Phone number required')
                })
        return HttpResponseRedirect(reverse('njangi:signup_contribution_done'))


class NSPSignupContributionDoneView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/signup_contribution_done.html'

    def post(self, request, *args, **kwargs):
        if request.user.has_contributed:
            return HttpResponseRedirect(reverse('njangi:dashboard'))
        else:
            message = _("We are still processing your request. If it has been more that 5 minutes, "
                        "please start all over.")
            return render(request, self.template_name, {"message": message})


class WalletTransactionListView(ContributionRequiredMixin, generic.ListView):
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


class WalletLoadAndWithdrawChoiceView(ContributionRequiredMixin, generic.TemplateView):
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


class WalletLoadAndWithdrawView(ContributionRequiredMixin, generic.TemplateView):
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
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, '
                                 'it will be restored soon.'), 'status': 'info'
                })
        # ************End of code*********

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
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, '
                                 'it will be restored soon.'), 'status': 'info'
                })
        # ************End of code*********

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


class WalletLoadAndWithdrawConfirmView(ContributionRequiredMixin, generic.TemplateView):
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
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, '
                                 'it will be restored soon.'), 'status': 'info'
                })
        # ************End of code*********

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

        # This code should be eliminated once the orange money API is integrated.
        # **********Code start***********
        elif nsp == _nsp.orange_wallet() or nsp == _nsp.orange():
            return render(request, 'njangi/error.html', context={
                    'message': _('Orange money is temporally unavailable, sorry for inconveniences, it will be '
                                 'restored soon.'), 'status': 'info'
                })
        # ************End of code*********

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
               # response = process_payout.delay(
               #     user_id=self.request.user.id, amount=amount, nsp=_nsp.orange(), processing_fee=processing_fee
               # )
                pass
            elif nsp == _nsp.orange_wallet() and action == 'load':
                purse_services.request_momo_deposit.delay(
                    phone_number=self.request.user.tel2.national_number, amount=total, user_id=self.request.user.id,
                    nsp=_nsp.orange(), level=0, purpose=momo_purpose.wallet_load(), recipient_id=self.request.user.id,
                    charge=processing_fee
                )
            elif nsp == _nsp.mtn_wallet() and action == 'withdraw':
                purse_services.request_momo_payout(
                    user_id=self.request.user.id, phone_number=self.request.user.tel1.national_number, amount=amount,
                    recipient_id=self.request.user.id, nsp=_nsp.mtn(), processing_fee=processing_fee,
                    purpose=momo_purpose.wallet_withdraw(),
                )

            elif nsp == _nsp.mtn_wallet() and action == 'load':
                r = purse_services.request_momo_deposit(
                    phone_number=self.request.user.tel1.national_number, amount=total, user_id=self.request.user.id,
                    nsp=_nsp.mtn(), level=0, purpose=momo_purpose.wallet_load(), recipient_id=self.request.user.id,
                    charge=processing_fee
                )
                # print(r)
        return HttpResponseRedirect(
            reverse('njangi:load_or_withdraw_done', kwargs={'nsp': nsp, 'action': action})
        )


class WalletLoadAndWithdrawDoneView(ContributionRequiredMixin, generic.TemplateView):
    template_name = 'njangi/checkout/load_or_withdraw_done.html'

    def get_context_data(self, **kwargs):
        context = super(WalletLoadAndWithdrawDoneView, self).get_context_data(**kwargs)
        action = self.kwargs['action']
        nsp = self.kwargs['nsp']
        context['message'] = _('Your %(nsp)s %(action)s is been processed.') % \
                        {'nsp': nsp.replace('_', ' '), 'action': action}
        return context


class SwitchUserView(ContributionRequiredMixin, generic.View):

    # View responsible for switching a user from the dashboard.
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        user_account_id = self.request.user.user_account_id
        if user_account_id and user_id:
            if account_manager.user_is_in_list(user_id=user_id, user_account_id=user_account_id):
                user_account = account_manager.get_user_account(user_account_id=user_account_id)
                if user_account.is_active or user_account.last_payment > timezone.now():
                    try:
                        user = UserModel().objects.get(pk=user_id)
                        login(self.request, user)
                    except UserModel().DoesNotExist:
                        pass
            else:
                pass
        else:
            pass

        return HttpResponseRedirect(reverse('njangi:dashboard',))


class UserAccountListView(ContributionRequiredMixin, generic.ListView):
    template_name = 'njangi/premium/user_account_list.html'
    paginate_by = 5
    context_object_name = 'user_account_list'

    def get_queryset(self):
        if self.request.user.user_account_id:
            return account_manager.get_user_account_user_list(user_account_id=self.request.user.user_account_id)
        else:
            return []


class CreateUserAccountView(ContributionRequiredMixin, generic.View):
    template_name = 'njangi/premium/add_user_account.html'
    form = AuthenticationForm

    def get(self, request, *args, **kwargs):
        return render(
            request=request, template_name=self.template_name, context={
                'form': self.form, 'error_message': None
            }
        )

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        error_message = None
        response1 = {}
        response2 = {}
        response = {}
        user = authenticate(username=username, password=password)
        if not user:
            error_message = _('Username and password incorrect.')
        else:
            if user.user_account_id:
                error_message = _('This user has already been added to a list.')
            else:
                if request.user.user_account_id:
                    response = account_manager.add_user_to_user_account(
                        user=user, user_account_id=request.user.user_account_id
                    )
                else:
                    response1 = account_manager.add_user_to_user_account(
                        user=request.user
                    )
                    if response1['status'] == 'success' and not user == request.user:
                        # Only add the user to user account if "user" is different from "request.user"
                        response2 = account_manager.add_user_to_user_account(
                            user=user, user_account_id=response1['instance'].id
                        )

                    elif response1['status'] == 'success' and user == request.user:
                        # if the user is the same as the request.user, just add a "success" status to response2

                        success_message = _('Account added successfully.')
                        response2['status'] = 'success'
                    else:
                        error_message = _('Account not added. Check your subscription package.')

            if (response and response['status'] == 'success') or (response2 and response2['status'] == 'success'):
                success_message = _('Account added successfully.')
                return render(
                    request=request, template_name=self.template_name, context={
                        'form': self.form, 'success_message': success_message
                    }
                )
            else:
                if response:
                    error_message = response['message']
                elif response2:
                    error_message = response['messate']
        return render(
            request=request, template_name=self.template_name, context={
                'form': self.form, 'error_message': error_message
            }
        )


class RemoveUserAccountView(ContributionRequiredMixin, generic.DeleteView):
    success_url = reverse_lazy('njangi:user_account_list')

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id:
            try:
                user = UserModel().objects.get(pk=user_id)
                if self.request.user.user_account_id:
                    account_manager.remove_user_from_user_account(
                        user=user, user_account_id=self.request.user.user_account_id
                    )
            except UserModel().DoesNotExist:
                pass
        return HttpResponseRedirect(self.success_url)


class UserAccountPackages(ContributionRequiredMixin, generic.ListView):
    template_name = 'njangi/premium/user_account_packages.html'
    context_object_name = 'package_list'

    def get_queryset(self):
        return account_manager.get_user_account_packages()

    def get_context_data(self, **kwargs):
        context = super(UserAccountPackages, self).get_context_data(**kwargs)
        context['subscription_types'] = subscription_types
        return context


class UserAccountPackageSubscriptionView(ContributionRequiredMixin, generic.TemplateView):
    template_name = 'njangi/premium/package_subscription.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        package_id = context['package_id']
        package = account_manager.get_package(package_id)
        if not package:
            content = "<h2>%s</h2>" % _('Package Not Found')
            return HttpResponseNotFound(content)
        return super(UserAccountPackageSubscriptionView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserAccountPackageSubscriptionView, self).get_context_data(**kwargs)
        package_id = kwargs.get('package_id')
        subscription_type = kwargs.get('subscription_type')
        context['package'] = account_manager.get_package(package_id)
        context['subscription_type'] = subscription_type
        context['subscription_types'] = subscription_types
        return context

    def post(self, request, *args, **kwargs):
        package_id = kwargs.get('package_id')
        subscription_type = kwargs.get('subscription_type')
        amount = 0.00
        package = account_manager.get_package(package_id)
        user_account_id = None
        if package:
            if subscription_type == subscription_types.annually():
                amount = package.annual_subscription
            elif subscription_type == subscription_types.monthly():
                amount = package.monthly_subscription
            else:
                context = self.get_context_data(**kwargs)
                context['message'] = _('Invalid subscription. Please choose a subscription from the list')
                context['status'] = 'error'

                return render(request, self.template_name, context={
                    'status': 'error', 'message': _('Invalid subscription. Please choose a subscription from the list'),
                    'package': package, 'subscription_type': subscription_type,
                    'subscription_types': subscription_types
                })

            if D(amount) <= 0.00:
                return render(request, self.template_name, context={
                    'status': 'error', 'message': _('Invalid subscription. Please choose a subscription from the list'),
                    'package': package, 'subscription_type': subscription_type,
                    'subscription_types': subscription_types
                })

            if request.user.user_account_id:
                user_account_id = request.user.user_account_id
            else:
                r = account_manager.add_user_to_user_account(user=request.user)
                if r['status'] == 'success':
                    user_account_id = r['instance'].id

            if user_account_id:
                pay_response = wallet.pay_subscription(user=request.user, amount=amount)
                if pay_response['status'] == 'success':
                    account_manager.update_subscription(
                        user_account_id=user_account_id, package_id=package_id, subscription=subscription_type
                    )
                    return render(request, self.template_name, context={
                        'status': 'success', 'message': _('Subscription completed Successfully.'),
                        'package': package, 'subscription_type': subscription_type,
                        'subscription_types': subscription_types
                    })
                else:
                    return render(request, self.template_name, context={
                        'status': 'error', 'message': pay_response['message'],
                        'package': package, 'subscription_type': subscription_type,
                        'subscription_types': subscription_types
                    })
            else:
                return render(request, self.template_name, context={
                    'status': 'error', 'message': _('Please add the current user to your list of user accounts.'),
                    'package': package, 'subscription_type': subscription_type,
                    'subscription_types': subscription_types
                })
        else:
            content = "<h2>%s</h2>" % _('Package does not exist.')
            return HttpResponseNotFound(content=content, *args, **kwargs)


