from django.contrib import admin
from .models import WalletModel
# Register your models here.

admin.site.register(
    WalletModel,
    list_display=(
        'id', 'description', 'information', 'amount', 'charge', 'user', 'sender', 'reference', 'trans_code', 'tel', 'nsp',
        'status',
    )
)