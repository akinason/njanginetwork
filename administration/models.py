from django.db import models

# Create your models here.


class SiteInformation(models.Model):
    allow_withdrawal = models.BooleanField(default=True)
    allow_deposit = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
