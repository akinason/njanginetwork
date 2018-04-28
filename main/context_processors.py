
from datetime import datetime

from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext_lazy as _

from main.utils import get_sponsor, get_promoter
from main.notification import notification


class SiteInformation:

    def __init__(self, request):
        self.request = request
        self._accronym = _('NNetwork')
        self._name = _('Njangi Network')
        self._website = 'www.njanginetwork.com'
        self._current_date = datetime.now()
        self._contact_numbers = '+237 675397307'

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
        'sponsor': get_sponsor(request),
        'promoter': get_promoter(request),
        'notification_list': notification().get_user_notifications(request.user.id),
        'unread_notification_count': notification().get_unread_notification_count(request.user.id),
    }
    return context
