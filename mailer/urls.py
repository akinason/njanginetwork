from django.conf.urls import url
from .views import index

app_name = 'mailer'
urlpatterns = [
    url(r'^index/$', index, name='mailer_index'),
]
