import decimal

from django.contrib.auth import get_user_model as UserModel
from django.db import models
from django.db.models import Sum, F, Value as V, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from tinymce.models import HTMLField

D = decimal.Decimal
INVOICE_STATUS = (('DRAFT', 'DRAFT'), ('PENDING_PAYMENT', 'PENDING_PAYMENT'), ('PAID', 'PAID'), ('CANCELLED', 'CANCELLED'))
PRODUCT_TYPE_IMAGE_URL = 'marketplace/product_type/'
PRODUCT_IMAGE_URL = 'marketplace/product/'


class PaymentMethod:
    _wallet = "wallet"
    _mobilemoney = "mobilemoney"

    def wallet(self):
        return self._wallet

    def mobilemoney(self):
        return self._mobilemoney


class InvoiceStatus:
    _draft = 'DRAFT'
    _pending_payment = 'PENDING_PAYMENT'
    _paid = "PAID"
    _cancelled = "CANCELLED"

    def pending_payment(self):
        return self._pending_payment

    def paid(self):
        return self._paid

    def cancelled(self):
        return self._cancelled

    def draft(self):
        return self._draft


class ProductType(models.Model):
    name = models.CharField(_('name'), max_length=255)
    image = models.ImageField(_('product type image'), upload_to=PRODUCT_TYPE_IMAGE_URL, blank=True, null=True)

    def child_records(self):
        return Product.objects.filter(product_type__id=self.pk)


class Product(models.Model):
    name = models.CharField(_('product name'), max_length=255)
    code = models.CharField(_('product code'), blank=True, max_length=255)
    description = HTMLField(_('description'))
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=10)
    company_commission = models.DecimalField(_('company commission'), max_digits=3, decimal_places=3)
    rating = models.IntegerField(_('rating'), blank=True, null=True)
    level_1_commission = models.DecimalField(_('level 1 commission'), max_digits=3, decimal_places=3, default=30)
    level_2_commission = models.DecimalField(_('level 2 commission'), max_digits=3, decimal_places=3, default=15)
    level_3_commission = models.DecimalField(_('level 3 commission'), max_digits=3, decimal_places=3, default=5)
    level_4_commission = models.DecimalField(_('level 4 commission'), max_digits=3, decimal_places=3, default=0.00)
    level_5_commission = models.DecimalField(_('level 5 commission'), max_digits=3, decimal_places=3, default=0.00)
    level_6_commission = models.DecimalField(_('level 6 commission'), max_digits=3, decimal_places=3, default=0.00)
    is_active = models.BooleanField(default=False)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name='product_type',
                                     verbose_name=_('product type'))
    background_image = models.ImageField(upload_to=PRODUCT_IMAGE_URL, blank=True, null=True)
    is_trending = models.BooleanField(default=False)
    auto_add_to_invoice = models.BooleanField(default=False)
    discount = models.DecimalField(_('discount rate'), default=0.00, decimal_places=3, max_digits=3)
    allow_discount = models.BooleanField(_('allow discount'), default=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def product_images(self):
        return ProductImage.objects.filter(product__pk=self.pk)

    def image(self):
        try:
            i = ProductImage.objects.filter(product__pk=self.pk)[:1].get()
            return i.image
        except Exception as err:
            return ProductImage.objects.none()

    def price_rstrip(self):
        return ("%f" % self.price).rstrip('0').rstrip('.')


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(_('image'), upload_to=PRODUCT_IMAGE_URL)
    is_index_image = models.BooleanField(default=False)

    def __str__(self):
        return self.image.url


class Invoice(models.Model):
    invoice_status = InvoiceStatus()

    total = models.DecimalField(_('invoice total'), max_digits=10, decimal_places=3, default=0.00)
    net_payable = models.DecimalField(_('net payable'), max_digits=10, decimal_places=3, default=0.00)
    user = models.ForeignKey(UserModel(), on_delete=models.CASCADE, related_name='invoice_owner', verbose_name=_('owner'))
    status = models.CharField(_('status'), choices=INVOICE_STATUS, default=invoice_status.draft(), max_length=255)
    is_paid = models.BooleanField(default=False)
    is_commission_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(_('payment reference'), blank=True, max_length=255)
    payment_method = models.CharField(_('payment method'), max_length=255, blank=True)
    paid_by = models.ForeignKey(UserModel(), on_delete=models.CASCADE, blank=True, null=True)
    paid_on = models.DateTimeField(_('paid on'), blank=True, null=True)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return str(self.pk)

    def total_rstrip(self):
        return ("%f" % self.total ).rstrip('0').rstrip('.')

    def status_rstrip(self):
        return self.status.replace('_', ' ').capitalize()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name='invoice_product_item', verbose_name=_('product'), on_delete=models.CASCADE
    )
    quantity = models.DecimalField(_('quantity'), default=1, max_digits=10, decimal_places=3)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=3)
    discount = models.DecimalField(_('discount'), max_digits=10, decimal_places=3, default=0.00)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=3)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.product.name

    def price_rstrip(self):
        return ("%f" % self.price).rstrip('0').rstrip('.')

    def amount_rstrip(self):
        return ("%f" % self.amount).rstrip('0').rstrip('.')


class Commission(models.Model):
    """ A model to store all commission sharing history."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(UserModel(), on_delete=models.CASCADE)
    level = models.IntegerField()
    percentage = models.DecimalField(max_digits=3, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

    def amount_rstrip(self):
        return ("%f" % self.amount).rstrip('0').rstrip('.')


class MarketManager:
    invoice_status = InvoiceStatus()

    def get_total_invoice_count(self):
        # Returns the total number of paid invoices.
        return Invoice.objects.filter(status=self.invoice_status.paid()).count()

    def get_total_invoice_value(self):
        # Returns the total value of all paid invoices.
        invoice = Invoice.objects.filter(status=self.invoice_status.paid()).aggregate(
            value=Coalesce(Sum(F('total')), V(0.00))
        )
        return D(invoice['value'])

    def get_total_commission_paid(self):
        # Returns the total commission paid out to users.
        commission = Commission.objects.filter(user__is_admin=False).aggregate(
            total_commission=Coalesce(Sum(F('amount')), V(0.00))
        )
        return D(commission['total_commission'])

    def get_total_marketplace_income(self):
        # Returns the total income made in the marketplace. InvoiceTotal - TotalCommissionPaid
        return self.get_total_invoice_value() - self.get_total_commission_paid()
