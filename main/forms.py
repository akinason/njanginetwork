from django.contrib.auth import get_user_model
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import HiddenInput
from django.contrib.auth.forms import AuthenticationForm

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3

from main.models import TEL_MAX_LENGTH, RESERVED_USERNAMES
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field import widgets as phonenumber_widgets
from main import validators as main_validators


class SignupForm(forms.ModelForm):
    error_messages = (
        ('length', _('Password must be greater than 8 characters')),
        ('no_match', _('Password does not match.')),
        ('invalid', _('Current Password is invalid.')),
    )

    tel1 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('Phone Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237675366885')}), help_text='*'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Password'), 'class': 'form-control'}), label=_('Password'),
        help_text=_('* min 8'), min_length=8, validators=[main_validators.validate_password]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Confirm Password')}), label=_('Confirm Password'),
        error_messages={'no_match': _('Password does not match')},
        help_text=_('* min 8'), min_length=8
    )

    captcha = ReCaptchaField(widget=ReCaptchaV3)

    def __init__(self, *args, **kwargs):
        self.sponsor = kwargs.pop("sponsor")
        self.promoter = kwargs.pop('promoter')
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields["sponsor"].initial = self.promoter
        self.fields['sponsor'].widget = HiddenInput()
        self.fields["network_parent"].initial = self.sponsor
        self.fields['network_parent'].widget = HiddenInput()
        self.fields['tel1'].required = True
        # self.fields['tel2'].required = False

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'tel1', 'sponsor', 'email', 'network_parent']

    def clean_confirm_password(self):
        super(SignupForm, self).clean()
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and password != confirm_password:
            raise forms.ValidationError(self.fields['confirm_password'].error_messages['no_match'])
        return confirm_password

    def clean(self):
        username = self.cleaned_data.get('username')
        if username in RESERVED_USERNAMES:
            msg = forms.ValidationError(_('username already exist.'))
            self.add_error('username', msg)
        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if email:
            if get_user_model().objects.filter(email=email).exists():
                msg = _('Email already exist.')
                self.add_error('email', msg)
            else:
                return email

    def send_email(self):
        pass

    def save(self, commit=True):
        instance = super(SignupForm, self).save(commit=False)
        if not instance.id:
            instance.set_password(self.cleaned_data.get('password'))
        if commit:

            if instance.tel3:
                instance.tel3_is_verified = True
            if instance.email:
                instance.email_is_verified = True

            instance.tel1_is_verified = True
            instance.tel2_is_verified = True
            instance.tel2 = instance.tel1
            instance.first_name = "NA"
            instance.last_name = "NA"
            instance.gender = "other"
            instance.save()
        return instance


class LoginForm(AuthenticationForm):
    pass


class ProfileChangeForm(forms.ModelForm):
    error_messages = (
        ('length', _('Password must be greater than 8 characters')),
        ('no_match', _('Password does not match.')),
        ('invalid', _('Current Password is invalid.')),
    )
    
    tel1 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('MTN Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237675366885')}), help_text='',
    )

    tel2 = PhoneNumberField(
        max_length=TEL_MAX_LENGTH, min_length=TEL_MAX_LENGTH,
        label=_('Orange Number'), widget=phonenumber_widgets.PhoneNumberInternationalFallbackWidget(
            attrs={'placeholder': _('e.g. +237695366885')}), help_text='',
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(ProfileChangeForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['tel1'].required = False
        self.fields['tel2'].required = False

    class Meta:
        model = get_user_model()
        fields = ['username', 'tel1', 'tel2', 'tel3', 'first_name', 'last_name', 'gender', 'email',
                  'allow_automatic_contribution']

    def clean(self):
        tel1 = self.cleaned_data.get('tel1')
        tel2 = self.cleaned_data.get('tel2')

        if not tel1 and not tel2:
            msg = forms.ValidationError(_('Provide at least an MTN or Orange number.'))
            self.add_error('tel1', msg)
        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if email:
            if get_user_model().objects.exclude(pk=self.user.id).filter(email=email).exists():
                msg = _('Email already exist.')
                self.add_error('email', msg)
            else:
                return email

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
    captcha = ReCaptchaField(widget=ReCaptchaV3)


class PhonePasswordResetForm(forms.Form):
    username = forms.CharField(label=_('username'), required=True, max_length=50)
    phone_number = forms.IntegerField(label=_('phone number'), required=True)


class PhonePasswordResetCodeForm(forms.Form):
    code = forms.IntegerField(label=_('enter code'), required=True)
