from django.urls import path
from . import views

app_name = 'feedback'
urlpatterns = [
    path('', views.post_feedback_response, name='create')
]
