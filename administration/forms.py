from django import forms
from . import models


class RemunerationForm(forms.ModelForm):
    class Meta:
        model = models.Remuneration
        exclude = ['is_paid', 'status']
        widgets = {
            'purpose': forms.Textarea(),
        }

    def clean_level_1(self):
        level_1 = self.cleaned_data['level_1']

        if level_1 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_1 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_1

    def clean_level_2(self):
        level_2 = self.cleaned_data['level_2']

        if level_2 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_2 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_2

    def clean_level_3(self):
        level_3 = self.cleaned_data['level_3']

        if level_3 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_3 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_3

    def clean_level_4(self):
        level_4 = self.cleaned_data['level_4']

        if level_4 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_4 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_4

    def clean_level_5(self):
        level_5 = self.cleaned_data['level_5']

        if level_5 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_5 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_5

    def clean_level_6(self):
        level_6 = self.cleaned_data['level_6']

        if level_6 > 1:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")
        elif level_6 < 0:
            raise forms.ValidationError(
                "remuneration ratio lies in range(0,1)")

        return level_6

    def clean(self):
        level_1 = self.cleaned_data['level_1']
        level_2 = self.cleaned_data['level_2']
        level_3 = self.cleaned_data['level_3']
        level_4 = self.cleaned_data['level_4']
        level_5 = self.cleaned_data['level_5']
        level_6 = self.cleaned_data['level_6']

        total_ratio = level_1 + level_2 + level_3 + level_4 + level_5 + level_6

        if total_ratio != 1:
            raise forms.ValidationError(
                "remuneration ratio must all sum up to '1'")

        return super(RemunerationForm, self).clean()
