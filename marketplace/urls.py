from django.conf.urls import url
from .views import *

app_name = 'marketplace'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^product/list', ProductListView.as_view(), name='product_list'),
    url(r'^product/(?P<pk>[0-9]+)/details', ProductDetailView.as_view(), name='product_details'),
    url(r'^invoice/create', CreateInvoiceView.as_view(), name='new_invoice'),
    url(r'^invoice/(?P<pk>[0-9]+)', InvoiceDetailView.as_view(), name='invoice_detail'),
    url(r'^invoice/payment', PaymentView.as_view(), name='payment'),
]
