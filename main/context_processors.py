from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from datetime import datetime
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from main.utils import get_sponsor


class SiteInformation:

    def __init__(self, request):
        self.request = request
        self._accronym = _('NNetwork')
        self._name = _('Njangi Network')
        self._website = 'www.njanginetwork.com'
        self._current_date = datetime.now()
        self._contact_numbers = '+237 675397307 | +237 655916762'

    def accronym(self):
        return self._accronym

    def name(self):
        return self._name

    def website(self):
        return 'https://%s' % get_current_site(self.request)

    def current_date(self):
        return self._current_date

    def contact_numbers(self):
        return self._contact_numbers


def main_context_processors(request):
    context = {
        'site_info': SiteInformation(request),
        'sponsor': get_sponsor(request)
    }
    return context
