import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DefaultUserManager
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.utils import six, timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from njanginetwork import settings
from phonenumber_field.modelfields import PhoneNumberField


GENDER_TYPES = (
    ('male', 'Male'),
    ('female', 'Female'),
)

TEL_MAX_LENGTH = 13

TRUE_FALSE_CHOICES = (
    (True, _('Yes')),
    (False, _('No')),
)

RESERVED_USERNAMES = [
    'administrator', 'admin', 'administrateur', 'adminaccount', 'adminuser', 'administration',
 ]


class UserManager(DefaultUserManager):
    def create_admin(self, username, first_name, last_name, gender, tel1):
        user = self.model(
                username=username, first_name=first_name, last_name=last_name, gender=gender, tel1=tel1
            )
        user.is_admin = True
        user.sponsor = user.pk
        user.is_staff = True
        user.set_unique_random_sponsor_id()
        user.set_unique_random_tel1_code()
        user.set_unique_random_tel2_code()
        user.set_unique_random_tel3_code()
        user.save()
        return user


class User(AbstractUser):

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

    # Required Fields.  ************************

    username = models.CharField(
        _('username'),
        max_length=50,
        unique=True,
        help_text=_('*'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(
        _('first name'), max_length=30, blank=False, help_text='*', validators=[username_validator]
    )
    last_name = models.CharField(
        _('last name'), max_length=50, blank=False, help_text='*', validators=[username_validator]
    )
    gender = models.CharField(_('gender'), choices=GENDER_TYPES, max_length=6, help_text='*')
    sponsor = models.PositiveIntegerField(_('sponsor'), blank=True, null=True, db_index=True)

    # Non Required fields. **********************
    email = models.EmailField(_('email address'), blank=True, null=True, default=None)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    is_admin = models.BooleanField(default=False)
    country = CountryField(_('country'), max_length=3, default='CM')
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    tel1 = PhoneNumberField(_('MTN number'), help_text='', blank=True, null=True)
    tel2 = PhoneNumberField(_('Orange number'), help_text='', blank=True, null=True)
    tel3 = PhoneNumberField(_('Nexttel number'), help_text=_('optional'), blank=True, null=True)

    profile_picture = models.ImageField(
        _('profile picture'), upload_to=settings.PROFILE_PICTURE_PATH, blank=True, null=True
    )
    sponsor_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    level = models.PositiveIntegerField(_('level'), default=0)
    allow_automatic_contribution = models.BooleanField(
        _('allow automatic contributions'), default=False, choices=TRUE_FALSE_CHOICES
    )

    # Verification Fields.
    tel1_verification_uuid = models.IntegerField(blank=True, null=True, unique=True)
    tel2_verification_uuid = models.IntegerField(blank=True, null=True, unique=True)
    tel3_verification_uuid = models.IntegerField(blank=True, null=True, unique=True)
    email_verification_uuid = models.UUIDField('Unique Verification UUID', default=uuid.uuid4)

    tel1_is_verified = models.BooleanField(default=False)
    tel2_is_verified = models.BooleanField(default=False)
    tel3_is_verified = models.BooleanField(default=False)
    email_is_verified = models.BooleanField(default=False)

    object = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'gender', 'sponsor']
    EMAIL_FIELD = 'email'

    def set_unique_random_tel1_code(self):
        while True:
            code = password = User.objects.make_random_password(length=6, allowed_chars='23456789')
            if not User.objects.filter(tel1_verification_uuid=code).exists():
                self.tel1_verification_uuid = code
                break

    def set_unique_random_tel2_code(self):
        while True:
            code = password = User.objects.make_random_password(length=6, allowed_chars='23456789')
            if not User.objects.filter(tel2_verification_uuid=code).exists():
                self.tel2_verification_uuid = code
                break

    def set_unique_random_tel3_code(self):
        while True:
            code = password = User.objects.make_random_password(length=6, allowed_chars='23456789')
            if not User.objects.filter(tel3_verification_uuid=code).exists():
                self.tel3_verification_uuid = code
                break

    def set_unique_random_sponsor_id(self):
        while True:
            code = password = User.objects.make_random_password(length=6, allowed_chars='23456789')
            if not User.objects.filter(sponsor_id=code).exists():
                self.sponsor_id = code
                break

    def status(self):
        if self.is_active:
            return _('active')
        else:
            return _('inactive')


class LevelModel(models.Model):
    level = models.PositiveIntegerField(verbose_name=_('level'))
    downlines = models.PositiveIntegerField(_('downlines'))
    cumm_downlines = models.PositiveIntegerField(_('cumm. downlines'))
    contribution = models.DecimalField(_('contribution'), max_digits=10, decimal_places=2)
    receipts = models.DecimalField(_('receipts'), max_digits=10, decimal_places=2)
    cumm_receipts = models.DecimalField(_("cumm. receipts"), max_digits=10, decimal_places=2)
    cumm_contribution = models.DecimalField(_('cumm. contribution'), max_digits=10, decimal_places=2)
    monthly_profit = models.DecimalField(_('monthly profit'), max_digits=10, decimal_places=2)
    upgrade_after = models.PositiveIntegerField(_('upgrade after'), default=0)
