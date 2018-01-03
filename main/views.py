from django.shortcuts import render, redirect
from .forms import SignupForm, ProfileChangeForm
from django.views import generic
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .utils import add_sponsor_id_to_session, get_sponsor
from django.contrib.auth.views import LoginView as DefaultLoginView, PasswordResetView as DefaultPasswordResetView, \
    PasswordResetConfirmView as DefaultPasswordConfirmView, \
    PasswordResetCompleteView as DefaultPasswordResetCompleteView, PasswordChangeView as DefaultPasswordChangeView, \
    PasswordChangeDoneView as DefaultPasswordChangeDoneView, LogoutView as DefaultLogoutView
from njangi.core import add_user_to_njangi_tree, create_user_levels
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(generic.TemplateView):
    template_name = 'main/index.html'

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        return super(IndexView, self).get(request, *args, **kwargs)


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
            kwargs.update({'sponsor': get_sponsor(self.request).pk })
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
        return super(SignupView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        return super(SignupView, self).get(request, *args, **kwargs)


class ProfileChangeView(LoginRequiredMixin, generic.UpdateView):
    form_class = ProfileChangeForm
    template_name = 'registration/profile_change.html'
    model = get_user_model()
    success_url = reverse_lazy('main:profile_change')

    def get_object(self, queryset=None):
        return self.request.user


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
    template_name = 'registration/password_reset_complete'


class PasswordChangeView(DefaultPasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('main:password_change_done')


class PasswordChangeDoneView(DefaultPasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'
