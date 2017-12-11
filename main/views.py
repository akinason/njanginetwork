from django.shortcuts import render, redirect
from .forms import SignupForm
from django.views import generic
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .utils import add_sponsor_id_to_session, get_sponsor
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView as DefaultLoginView


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
    success_url = reverse_lazy("main:signup")

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
        return super(SignupView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        return super(SignupView, self).get(request, *args, **kwargs)


class LoginView(DefaultLoginView):
    redirect_authenticated_user = True


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'main/change_password.html', {
        'form': form
    })