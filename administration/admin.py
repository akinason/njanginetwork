from django.contrib import admin
from .models import SiteInformation, Remuneration, Beneficiary

# Register your models here.

admin.site.register(SiteInformation)
admin.site.register(Remuneration)
admin.site.register(Beneficiary)
