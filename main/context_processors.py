from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model as UserModel
from datetime import datetime, timedelta, time
from django.utils import timezone
from njangi.context_processors import get_user_node
from django.views import generic


class SiteInformation:
    _accronym = _('NNetwork')
    _name = _('Njangi Network')
    _website = 'www.njangi.network'
    _total_users = UserModel().objects.filter(is_admin=False).count()
    _total_admin_users = UserModel().objects.filter(is_admin=True).count()

    today = timezone.now().date()

    _today_users = UserModel().objects.filter(date_joined__date=today).count()
    _current_date = datetime.now()

    def accronym(self):
        return self._accronym

    def name(self):
        return self._name

    def website(self):
        return self._website

    def total_users(self):
        return self._total_users

    def total_admin_users(self):
        return self._total_admin_users

    def today_users(self):
        return self._today_users

    def current_date(self):
        return self._current_date


def main_context_processors(request):
    context = {
        'site_info': SiteInformation(),
    }
    return context