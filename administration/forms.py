from django import forms
from administration import models


class RemunerationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for level in range(6):
            self.fields[f'level_{level + 1}'] = forms.DecimalField(initial=0.00,
                                                                   widget=forms.NumberInput(attrs={'max': 1, 'min': 0, 'step': 0.01}))

    class Meta:
        model = models.Remuneration
        exclude = ['is_paid', 'status']
        widgets = {
            'purpose': forms.Textarea(),
        }

    def clean(self):
        levels = [self.cleaned_data['level_1'], self.cleaned_data['level_2'], self.cleaned_data['level_3'],
                  self.cleaned_data['level_4'], self.cleaned_data['level_5'], self.cleaned_data['level_6']]
        total_ratio = 0

        for level in levels:
            if level > 1:
                raise forms.ValidationError(
                    "remuneration ratio lies in range(0,1)")
            elif level < 0:
                raise forms.ValidationError(
                    "remuneration ratio lies in range(0,1)")
            else:
                total_ratio += level

        if total_ratio != 1:
            raise forms.ValidationError(
                "remuneration ratio must all sum up to '1'")

        return super(RemunerationForm, self).clean()
