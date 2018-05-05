from django.conf.urls import url
from .views import (
    SignupView, IndexView, PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView, LoginView, LogoutView, ProfileChangeView, ContactView,
    UpdateAllNotificationsView, UpdateNotificationView
)
from django.contrib.auth import views as auth_views

app_name = 'main'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^signup/$', SignupView.as_view(), name='signup'),
    url(r'^contact/$', ContactView.as_view(), name='contact'),
    url(r'^dashboard/password/$', PasswordChangeView.as_view(), name='password_change'),
    url(r'^dashboard/password/done/$', PasswordChangeDoneView.as_view(), name='password_change_done'),
    url(r'^password_reset/$', PasswordResetView.as_view(), name='password_reset'),
    url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^reset/done/$', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'^dashboard/profile_change/$', ProfileChangeView.as_view(), name='profile_change'),
    url(r'^dashboard/notification/(?P<pk>[0-9]+)/update/$', UpdateNotificationView.as_view(),
        name='update_notification'),
    url(r'^dashboard/notification/update/all/$', UpdateAllNotificationsView.as_view(),
        name='update_all_notifications'),


]
