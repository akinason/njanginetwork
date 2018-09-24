from django.contrib import admin
from .models import Product, ProductType, Invoice, InvoiceItem, Commission, ProductImage


# Register your models here.

class InvoiceAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'total', 'payment_reference', 'status')
    list_display = (
        'id', 'user', 'total', 'status', 'is_paid', 'is_commission_paid', 'created_on'
    )
    list_filter = ('status',)


class CommissionAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'product__name')
    list_display = (
        'id', 'user', 'product', 'level', 'amount', 'percentage', 'invoice', 'created_on'
    )
    list_display_links = ('id', 'invoice')

admin.site.register(Product)
admin.site.register(ProductType)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(ProductImage)
