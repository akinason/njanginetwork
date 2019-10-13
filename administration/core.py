from .models import SiteInformation


try:
    site_information = SiteInformation.objects.filter(is_default=True).get()
except SiteInformation.DoesNotExist:
    site_information = SiteInformation.objects.none()
