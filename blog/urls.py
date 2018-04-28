from django.conf.urls import url

from blog.views import (
   BlogIndexView, PostDetailView, PostListView, CategoryList
)

app_name = 'blog'
urlpatterns = [
    url(r'^$', BlogIndexView.as_view(), name='index'),
    url(r'^/category/(?P<pk>[0-9]+)/list/', CategoryList.as_view(), name='category_list'),
    url(r'^category/(?P<pk>[0-9]+)/post/list/$', PostListView.as_view(), name='post_list'),
    url(r'^category/post/(?P<pk>[0-9]+)/detail/$', PostDetailView.as_view(), name='post_detail'),
]
