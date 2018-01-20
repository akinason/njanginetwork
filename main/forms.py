from django.contrib.auth import get_user_model
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import HiddenInput
from main.models import TEL_MAX_LENGTH
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field import widgets as phonenumber_widgets
from mailer import services


class SignupForm(forms.ModelForm):
    error_messages = (
        ('length', _('Password must be greater than 5 characters')),
        ('no_match', _('Password does not match.')),
        ('invalid', _('Current Password is invalid.')),
    )

    tel1 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('MTN Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237675366885')}), help_text='*'
    )

    tel2 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('Orange Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237695366885')}), help_text='*'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Password'), 'class': 'form-control'}), label=_('Password'),
        help_text=_('* min 5'), min_length=5
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Confirm Password')}), label=_('Confirm Password'),
        error_messages={'no_match': _('Password does not match')},
        help_text=_('* min 5'), min_length=5
    )

    def __init__(self, *args, **kwargs):
        self.sponsor = kwargs.pop("sponsor")
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields["sponsor"].initial = self.sponsor
        self.fields['sponsor'].widget = HiddenInput()

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'tel1', 'tel2', 'first_name', 'last_name', 'gender', 'sponsor', 'email']

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
            if instance.tel1:
                instance.tel1_is_verified = True
            if instance.tel2:
                instance.tel2_is_verified = True
            if instance.tel3:
                instance.tel3_is_verified = True
            if instance.email:
                instance.email_is_verified = True
            instance.save()
            services.send_signup_welcome_email(user_id=instance.id)
            services.send_signup_welcome_sms(user_id=instance.id)
        return instance


class ProfileChangeForm(forms.ModelForm):
    error_messages = (
        ('length', _('Password must be greater than 5 characters')),
        ('no_match', _('Password does not match.')),
        ('invalid', _('Current Password is invalid.')),
    )

    tel1 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('MTN Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237675366885')}), help_text='*',
    )

    tel2 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('Orange Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237695366885')}), help_text='*',
    )

    def __init__(self, *args, **kwargs):
        super(ProfileChangeForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True

    class Meta:
        model = get_user_model()
        fields = ['username', 'tel1', 'tel2', 'tel3', 'first_name', 'last_name', 'gender', 'email',
                  'allow_automatic_contribution']

    def send_email(self):
        pass

    def save(self, commit=True):
        instance = super(ProfileChangeForm, self).save(commit=False)
        if commit:
            if instance.tel1:
                instance.tel1_is_verified = True
            if instance.tel2:
                instance.tel2_is_verified = True
            if instance.tel3:
                instance.tel3_is_verified = True
            if instance.email:
                instance.email_is_verified = True
            instance.save()
        return instance


class ContactForm(forms.Form):
    contact_name = forms.CharField(label=_('full name'), required=True, max_length=50)
    contact_email = forms.EmailField(label=_('email'), required=True)
    message = forms.CharField(
        label=_('message'),
        required=True,
        widget=forms.Textarea
    )
