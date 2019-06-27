
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DefaultLoginView, PasswordResetView as DefaultPasswordResetView,
    PasswordResetConfirmView as DefaultPasswordConfirmView,
    PasswordResetCompleteView as DefaultPasswordResetCompleteView, PasswordChangeView as DefaultPasswordChangeView,
    PasswordChangeDoneView as DefaultPasswordChangeDoneView, LogoutView as DefaultLogoutView, PasswordContextMixin
)
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from mailer import services as mailer_services
from main import website
from main.forms import (
    SignupForm, ProfileChangeForm, ContactForm, PhonePasswordResetCodeForm, PhonePasswordResetForm
)
from main.mixins import ContributionRequiredMixin
from main.models import LevelModel
from main.notification import notification
from main.utils import add_sponsor_id_to_session, get_sponsor, get_promoter, add_promoter_id_to_session
from njangi.core import add_user_to_njangi_tree, create_user_levels
from njangi.models import LEVEL_CONTRIBUTIONS
from njanginetwork import settings


class IndexView(generic.FormView):
    template_name = 'main/index.html'
    form_class = SignupForm

    def get_form_kwargs(self):
        """
       Returns the keyword arguments for instantiating the form.
       """
        kwargs = super(IndexView, self).get_form_kwargs()
        if self.request.method in ('GET', 'POST', 'PUT'):
            kwargs.update({'sponsor': get_sponsor(self.request).pk, 'promoter': get_promoter(self.request)})
        return kwargs

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        add_promoter_id_to_session(request)
        return super(IndexView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['the_problem'] = website.the_problem()
        context['njangi_network'] = website.njangi_network()
        context['the_model'] = website.the_model()
        context['njangi_levels'] = LevelModel.objects.all().order_by('level')
        context['level_1_contribution'] = ("%f" % LEVEL_CONTRIBUTIONS[1]).rstrip('0').rstrip('.')

        return context


class SignupView(generic.CreateView):
    template_name = 'main/signup.html'
    context_object_name = 'user'
    form_class = SignupForm
    model = get_user_model()
    success_url = reverse_lazy("njangi:dashboard")

    def get_form_kwargs(self):
        """
       Returns the keyword arguments for instantiating the form.
       """
        kwargs = super(SignupView, self).get_form_kwargs()
        if self.request.method in ('GET', 'POST', 'PUT'):
            kwargs.update({'sponsor': get_sponsor(self.request).pk, 'promoter': get_promoter(self.request).pk})
        return kwargs

    def form_valid(self, form):
        user = form.save()
        user.set_unique_random_sponsor_id()
        user.set_unique_random_tel1_code()
        user.set_unique_random_tel2_code()
        user.set_unique_random_tel3_code()
        user.save()
        self.object = user
        sponsor = get_sponsor(self.request)
        # add_user_to_njangi_tree(user=user, sponsor=sponsor)
        # create_user_levels(user=user)
        mailer_services.send_signup_welcome_sms(user_id=user.id)
        mailer_services.send_signup_welcome_email(user_id=user.id)

        # Authenticate and login the user
        user_logged = authenticate(username=user.username, password=form.cleaned_data['password'])
        login(self.request, user_logged)
        if 'marketplace' in self.request.session:
            return HttpResponseRedirect(reverse('marketplace:index'))
        return super(SignupView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        add_promoter_id_to_session(request)
        return super(SignupView, self).get(request, *args, **kwargs)


class ProfileChangeView(LoginRequiredMixin, generic.UpdateView):
    form_class = ProfileChangeForm
    template_name = 'registration/profile_change.html'
    model = get_user_model()
    success_url = reverse_lazy('main:profile_change')

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(ProfileChangeView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class LoginView(DefaultLoginView):
    template_name = 'main/login.html'
    redirect_authenticated_user = True


class LogoutView(DefaultLogoutView):
    next_page = '/'


class PasswordResetView(DefaultPasswordResetView):
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('main:password_reset_done')


class PasswordResetConfirmView(DefaultPasswordConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('main:password_reset_complete')


class PasswordResetCompleteView(DefaultPasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


class PasswordChangeView(DefaultPasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('main:password_change_done')


class PasswordChangeDoneView(DefaultPasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'


class PhonePasswordResetView(PasswordContextMixin, generic.FormView):
    template_name = 'registration/phone_password_reset_form.html'
    success_url = reverse_lazy('main:phone_password_reset_code')
    form_class = PhonePasswordResetForm
    title = _('Mobile Password Reset')

    def get(self, request, *args, **kwargs):

        if 'reset_code' in request.session:
            return HttpResponseRedirect(reverse('main:phone_password_reset_code'))

        return super(PhonePasswordResetView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        phone_number = str(form.cleaned_data.get('phone_number'))
        phone_number_is_valid = False
        user = ''
        tel1 = ''
        tel2 = ''

        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            form.add_error('username', _('There is no account with this username.'))
            return render(request=self.request, template_name=self.template_name, context={
                'form': form, 'username': username, 'phone_number': phone_number, 'message': _('Invalid username')
            })

        # Geerate the code.
        user.set_unique_random_tel1_code()
        user.save()
        code = user.tel1_verification_uuid

        # Ensure that the phone number provided is linked to the account.
        if user.tel1:
            tel1 = user.tel1.as_national.replace(' ', '')
            phone_number_is_valid = True if tel1 == phone_number else False

        if user.tel2 and not phone_number_is_valid:
            tel2 = user.tel2.as_national.replace(' ', '')
            phone_number_is_valid = True if tel2 == phone_number else False

        if phone_number_is_valid:
            # Send sms
            if 'reset_code' not in self.request.session:
                mailer_services.send_sms(
                    to_number='237' + phone_number,
                    body=_(
                        'Njangi Network \n\nPlease enter the code below to reset your Njangi '
                        'Network Account password  %s') % code
                )
                self.request.session['reset_code'] = code
                self.request.session['phone_number'] = phone_number
                self.request.session['user_id'] = user.pk

            return HttpResponseRedirect(reverse('main:phone_password_reset_code'))
        else:
            form.add_error('phone_number', _('This phone number is not associated to this account.'))
            return render(request=self.request, template_name=self.template_name, context={
                'form': form, 'username': username, 'phone_number': phone_number, 'message': _('Invalid phone number')
            })


class PhonePasswordResetCodeView(generic.FormView):
    template_name = 'registration/phone_password_reset_code.html'
    form_class = PhonePasswordResetCodeForm
    success_url = reverse_lazy('main:phone_password_reset_confirm')

    def get(self, request, *args, **kwargs):
        if 'reset_code' not in request.session:
            return HttpResponseRedirect(reverse('main:phone_password_reset'))

        return super(PhonePasswordResetCodeView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        code = form.cleaned_data.get('code')

        if str(code) == str(self.request.session['reset_code']):
            self.request.session['validcode'] = True

        else:
            form.add_error('code', _('Wrong Code.'))
            return render(request=self.request, template_name=self.template_name, context={'form': form})

        return super(PhonePasswordResetCodeView, self).form_valid(form)


class PhonePasswordResetConfirmView(generic.FormView):
    template_name = 'registration/phone_password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('main:login')
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user(pk=request.session['user_id'])

        if 'validcode' not in request.session or self.user is None:
            return HttpResponseRedirect(reverse('main:phone_password_reset'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session['reset_code']
        del self.request.session['user_id']
        del self.request.session['phone_number']
        del self.request.session['validcode']
        login(self.request, user)

        return super().form_valid(form)

    def get_user(self, pk):
        try:
            user = get_user_model().objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None
        return user

    def get_context_data(self, **kwargs):
        context = super(PhonePasswordResetConfirmView, self).get_context_data(**kwargs)
        context['validlink'] = True
        return context


class ContactView(generic.FormView):
    template_name = 'main/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('main:contact')

    def form_valid(self, form):
        name = self.request.POST.get('contact_name')
        email = self.request.POST.get('contact_email')
        content = self.request.POST.get('message')

        mailer_services.send_email.delay(
            subject='Contact From:' + str(name),
            message=content + "<p><br>" + email + "</p>",
            reply_to=email,
            to_email=settings.CONTACT_EMAIL,
        )

        messages.add_message(
            request=self.request, level=messages.SUCCESS, message=_(
                "Thanks for contacting, we will get back to you as soon as possible."
            )
        )
        return super(ContactView, self).form_valid(form)


class UpdateAllNotificationsView(LoginRequiredMixin, generic.View):

    def get(self, request, *args, **kwargs):
        notification().mark_notifications_as_read(user_id=request.user.id)
        return HttpResponseRedirect(reverse_lazy('njangi:dashboard'))


class UpdateNotificationView(LoginRequiredMixin, generic.View):

    def get(self, request, *args, **kwargs):
        notification_id = kwargs.get('pk')
        if not notification_id:
            notification_id = args[0]['pk']
        notification().update(notification_id=notification_id)
        return HttpResponseRedirect(reverse_lazy('njangi:dashboard'))
