from django.contrib.auth import get_user_model
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import HiddenInput


class SignupForm(forms.ModelForm):
    error_messages = (
        ('length', _('Password must be greater than 5 characters')),
        ('no_match', _('Password does not match.')),
        ('invalid', _('Current Password is invalid.')),
    )

    password = forms.CharField(
        widget=forms.PasswordInput, label=_('Password')
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label=_('Confirm Password'),
        error_messages={'no_match': _('Password does not match')}
    )

    def __init__(self, *args, **kwargs):
        self.sponsor = kwargs.pop("sponsor")
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields["sponsor"].initial = self.sponsor
        # self.fields['sponsor'].widget = HiddenInput()

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'tel1', 'first_name', 'last_name', 'gender', 'sponsor']

    def clean_confirm_password(self):
        super(SignupForm, self).clean()
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and password != confirm_password:
            raise forms.ValidationError(self.fields['confirm_password'].error_messages['no_match'])
        return confirm_password

    def send_email(self):
        pass

    def save(self, commit=True):
        instance = super(SignupForm, self).save(commit=False)
        if not instance.id:
            instance.set_password(self.cleaned_data.get('password'))
        if commit:
            instance.save()
        return instance
