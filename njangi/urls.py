from django.conf.urls import url
from .views import DashboardView

app_name = 'njangi'
urlpatterns =[
    url(r'^$', DashboardView.as_view(), name='dashboard'),
]