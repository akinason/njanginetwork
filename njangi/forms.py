from django import forms
from django.utils.translation import ugettext_lazy as _


class ContributionConfirmForm(forms.Form):
    level = forms.CharField(max_length=1, label=_('level'))
    recipient = forms.CharField(max_length=50, label=_('recipient'))
    amount = forms.DecimalField(max_digits=15, decimal_places=2, label=_('amount'))
    processing_fee = forms.DecimalField(max_digits=15, decimal_places=2, label=_('processing fee'))
    total = forms.DecimalField(max_digits=15, decimal_places=2, label=_('total'))

    def __init__(self, *args, **kwargs):
        # self._level = kwargs.pop('level')
        # self._recipient = kwargs.pop('recipient')
        # self._amount = kwargs.pop('amount')
        # self._processing_fee = kwargs.pop('processing_fee')
        # self._total = kwargs.pop('total')
        super(ContributionConfirmForm, self).__init__(*args, **kwargs)
        self.fields['level'].widget.attrs['readonly'] = True
        self.fields['recipient'].widget.attrs['readonly'] = True
        self.fields['amount'].widget.attrs['readonly'] = True
        self.fields['processing_fee'].widget.attrs['readonly'] = True
        self.fields['total'].widget.attrs['readonly'] = True
        # self.fields['level'].initial = self._level
        # self.fields['recipient'].initial = self._recipient.get_username()
        # self.fields['amount'].initial = self._amount
        # self.fields['processing_fee'].initial = self._processing_fee
        # self.fields['total'].initial = self._total


class LoadWithdrawForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label=_('amount'))
