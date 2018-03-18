from django.conf.urls import url
from .views import *

app_name = 'purse'
urlpatterns = [
    url(r'^gsmtools/afkanerd/api/momo/(?P<uuid4>[0-9A-Za-z_\-]+)', afknerdgsmtoolsview,
        name='afkanerd_momo_api'),
    url(r'^tests/', TestView.as_view(), name='test_view')
]
