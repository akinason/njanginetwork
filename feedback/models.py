from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from tinymce.models import HTMLField


RESPONSE_TYPE = (
    (1, _('Yes or No')),
    (2, _('Textfield')),
    (3, _('Single Checkbox Select')),
    (4, _('Multiple Checkbox Select'))
)


class Feedback(models.Model):
    title = models.CharField(max_length=100, verbose_name=_(
        'Title'))
    note = models.TextField(_('note'), blank=True, null=True)
    start_date = models.DateTimeField(verbose_name=_('Start Date'))
    end_date = models.DateTimeField(verbose_name=_('End Date'))
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_('Created By'))
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        # return f"Feedback({self.title}-{self.is_active}-{self.start_date}-{self.end_date})"
        return self.title


class Question(models.Model):
    feedback_id = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, verbose_name=_('Feedback ID'))
    title = models.CharField(max_length=200, verbose_name=_('Question'))
    order = models.IntegerField(verbose_name=_('order'))
    response_type = models.IntegerField(choices=RESPONSE_TYPE)

    def __str__(self):
        # return f"Question({self.title}-{self.response_type})"
        return self.title


class Response(models.Model):
    question_id = models.ForeignKey(
        Question, on_delete=models.CASCADE, verbose_name=_("Question ID"))
    response = models.CharField(max_length=300, verbose_name=_('Response'))
    user_id = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_("User ID"))
    response_date = models.DateTimeField(verbose_name=_('Response Date'))

    def __str__(self):
        # return f"Response({self.response}-user({self.user_id})-{self.response_date})"
        return self.response
