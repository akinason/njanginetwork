from django.conf.urls import url
from .views import SignupView, IndexView, change_password
from django.contrib.auth import views as auth_views

app_name = 'main'
urlpatterns =[
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'login/$', auth_views.login,
        {'template_name': 'main/login.html', 'redirect_authenticated_user': True}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'signup/$', SignupView.as_view(), name='signup'),
    url(r'^password/$', change_password, name='change_password'),
]