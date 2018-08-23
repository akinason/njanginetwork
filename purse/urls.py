from django.conf.urls import url
from .views import *

app_name = 'purse'
urlpatterns = [
    url(r'^gsmtools/afkanerd/api/momo/(?P<uuid4>[0-9A-Za-z_\-]+)', afknerdgsmtoolsview,
        name='afkanerd_momo_api'),
    url(r'^monetbil/notifications/aljfalsthosljlk5j', monetbilnotificationview, name='monetbil_notifications'),
    url(r'^monetbil/payout/notifications/jlasjdlkjwiurewopusl', monetbilpayoutnotificationview,
        name='monetbil_payout_notifications'),
]
