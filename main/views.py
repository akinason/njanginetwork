
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DefaultLoginView, PasswordResetView as DefaultPasswordResetView,
    PasswordResetConfirmView as DefaultPasswordConfirmView,
    PasswordResetCompleteView as DefaultPasswordResetCompleteView, PasswordChangeView as DefaultPasswordChangeView,
    PasswordChangeDoneView as DefaultPasswordChangeDoneView, LogoutView as DefaultLogoutView
)
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from mailer import services as mailer_services
from main import website
from main.forms import SignupForm, ProfileChangeForm, ContactForm
from main.models import LevelModel
from main.notification import notification
from main.utils import add_sponsor_id_to_session, get_sponsor, get_promoter, add_promoter_id_to_session
from njangi.core import add_user_to_njangi_tree, create_user_levels
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
        return context


class SignupView(generic.CreateView):
    template_name = 'main/signup.html'
    context_object_name = 'user'
    form_class = SignupForm
    model = get_user_model()
    success_url = reverse_lazy("main:login")

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
        add_user_to_njangi_tree(user=user, sponsor=sponsor)
        create_user_levels(user=user)
        mailer_services.send_signup_welcome_sms(user_id=user.id)
        mailer_services.send_signup_welcome_email(user_id=user.id)

        # Authenticate and login the user
        user_logged = authenticate(username=user.username, password=form.cleaned_data['password'])
        login(self.request, user_logged)
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
        notification_id = kwargs.get('notification_id')
        notification().update(notification_id=notification_id)
        return HttpResponseRedirect(reverse_lazy('njangi:dashboard'))
