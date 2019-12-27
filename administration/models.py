from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from django.utils import timezone
from django.urls import reverse


class SiteInformation(models.Model):
    allow_withdrawal = models.BooleanField(default=True)
    allow_deposit = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)


REMUNERATION_STATUS = (
    ('DRAFT', _('DRAFT')),
    ('GENERATED', _('GENERATED')),
    ('PAID', _('PAID')),
    ('PARTIALLY_PAID', _('PARTIALLY_PAID'))
)


class RemunerationStatus:

    def __init__(self):
        self._draft = 'DRAFT'
        self._generated = 'GENERATED'
        self._paid = 'PAID'
        self._partially_paid = 'PARTIALLY_PAID'

    def draft(self):
        return self._draft

    def generated(self):
        return self._generated

    def paid(self):
        return self._paid

    def partially_paid(self):
        return self._partially_paid


remuneration_status = RemunerationStatus()

# Remuneration Models


class Remuneration(models.Model):
    allocated_amount = models.DecimalField(
        _("allocated_amount"), decimal_places=2, max_digits=10)
    level_1 = models.DecimalField(_("level_1"), decimal_places=2, max_digits=3)
    level_2 = models.DecimalField(_("level_2"), decimal_places=2, max_digits=3)
    level_3 = models.DecimalField(_("level_3"), decimal_places=2, max_digits=3)
    level_4 = models.DecimalField(_("level_4"), decimal_places=2, max_digits=3)
    level_5 = models.DecimalField(_("level_5"), decimal_places=2, max_digits=3)
    level_6 = models.DecimalField(_("level_6"), decimal_places=2, max_digits=3)
    title = models.CharField(_('title'), max_length=25)
    source_account = models.ForeignKey(UserModel(), on_delete=models.CASCADE)
    purpose = models.CharField(_("purpose"), max_length=200)
    is_paid = models.BooleanField(_("is_paid"), default=False)
    status = models.CharField(_("status"), max_length=20,
                              choices=REMUNERATION_STATUS, default=REMUNERATION_STATUS[0][0])

    created_on = models.DateTimeField(_('creation date'), auto_now_add=True)

    def __str__(self):
        return f"Remuneration({self.allocated_amount}-{self.is_paid}-{self.status})"


class Beneficiary(models.Model):
    remuneration = models.ForeignKey(Remuneration, on_delete=models.CASCADE)
    user = models.ForeignKey(UserModel(), on_delete=models.CASCADE)
    amount = models.DecimalField(_("amount"), decimal_places=2, max_digits=10)
    user_level = models.IntegerField(_("user_level"))
    is_paid = models.BooleanField(_("is_paid"), default=False)
    payment_date = models.DateTimeField(
        _("payment_date"), blank=True, null=True)

    created_on = models.DateTimeField(_('creation date'), auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Beneficiaries'

    def __str__(self):
        return f"Beneficiary({self.user.username}-{self.amount}-{self.is_paid})"
