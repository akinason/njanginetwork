from django.contrib import admin
from .models import Product, ProductType, Invoice, InvoiceItem, Commission, ProductImage


# Register your models here.

admin.site.register(Product)
admin.site.register(ProductType)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Commission)
admin.site.register(ProductImage)
