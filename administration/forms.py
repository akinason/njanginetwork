from django import forms
from . import models


class RemunerationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RemunerationForm, self).__init__(*args, **kwargs)
        # Making name required
        # self.fields['level_1'] = forms.CharField(max_length=10)

    class Meta:
        model = models.Remuneration
        exclude = ['is_paid', 'status']
        widgets = {
            'purpose': forms.Textarea(),
        }
