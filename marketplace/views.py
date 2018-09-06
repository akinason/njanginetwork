import decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from .models import Product, Invoice, InvoiceItem, InvoiceStatus, PaymentMethod, ProductType, ProductImage
from marketplace import service as market_services
from main.utils import add_promoter_id_to_session, add_sponsor_id_to_session
from njangi.models import NSP
from njanginetwork import production_settings
from purse import services as purse_services
from purse.models import MOMOPurpose, TransactionStatus, WalletTransDescription, WalletManager
from purse.lib import monetbil



invoice_status = InvoiceStatus()
payment_method = PaymentMethod()
_nsp = NSP()
momo_purpose = MOMOPurpose()
trans_status = TransactionStatus()
trans_description = WalletTransDescription()
wallet_manager = WalletManager()


class IndexView(generic.TemplateView):
    template_name = 'marketplace/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['product_types'] = ProductType.objects.all()[:3]
        try:
            context['trending_product'] = Product.objects.filter(is_trending=True, is_active=True)[:1].get()
        except Product.DoesNotExist:
            context['trending_product'] = Product.objects.all()[:1].get()

        try:
            context['index_image'] = ProductImage.objects.filter(is_index_image=True)[:1].get()
        except ProductImage.DoesNotExist:
            pass
        
        context['popular_products'] = Product.objects.filter(is_active=True)

        return context

    def get(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        add_promoter_id_to_session(request)
        return super(IndexView, self).get(request, *args, **kwargs)


class ProductListView(generic.ListView):
    model = Product
    paginate_by = 10
    context_object_name = 'product_list'
    template_name = 'marketplace/shop.html'

    def get_queryset(self):
        return self.model.objects.filter(is_active=True)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProductListView, self).get_context_data(object_list=object_list, kwargs=kwargs)
        context['product_types'] = ProductType.objects.all()
        context['product_count'] = self.get_queryset().filter(is_active=True).count()
        return context


class ProductDetailView(generic.DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'marketplace/product_detail.html'

    def get_object(self, queryset=None):
        obj = super(ProductDetailView, self).get_object(queryset)
        if obj.is_active:
            return obj
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        obj = self.get_object()
        context['l1comm'] = ("%f" % (obj.level_1_commission * 100)).rstrip('0').rstrip('.') + '%'
        context['l2comm'] = ("%f" % (obj.level_2_commission * 100)).rstrip('0').rstrip('.') + '%' 
        context['l3comm'] = ("%f" % (obj.level_3_commission * 100)).rstrip('0').rstrip('.') + '%' 
        context['l4comm'] = ("%f" % (obj.level_4_commission * 100)).rstrip('0').rstrip('.') + '%'
        context['l5comm'] = ("%f" % (obj.level_5_commission * 100)).rstrip('0').rstrip('.') + '%' 
        context['l6comm'] = ("%f" % (obj.level_6_commission * 100)).rstrip('0').rstrip('.') + '%'
        return context


class CreateInvoiceView(LoginRequiredMixin, generic.View):
    """ View to show the invoice details to the user. """
    model = Invoice

    def post(self, request, *args, **kwargs):
        """ Create an invoice with one item. and returns that invoice"""
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity') if request.POST.get('quantity') else 1
        discount = request.POST.get('discount') if request.POST.get('discount') else 0

        product = ""

        try:
            product = Product.objects.filter(id=product_id).get()
        except:
            """ catch any other error and end processing"""
            return render(request, 'marketplace/not_found.html')

        # Create the invoice and the invoice item.
        invoice = self.model(user=request.user)
        invoice.save()

        invoice_item = InvoiceItem(
            invoice=invoice, product=product, quantity=quantity, price=product.price, amount=product.price * quantity,
            discount=discount
        )
        invoice_item.save()

        # Update the total on the invoice.
        invoice.total = product.price * quantity
        invoice.save()

        return HttpResponseRedirect(reverse('marketplace:invoice_detail', kwargs={'pk': invoice.pk}))

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('marketplace:product_list'))


class InvoiceDetailView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'marketplace/invoice.html'

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        invoice_id = kwargs.get('pk')
        context['payment_method'] = payment_method

        try:
            invoice = Invoice.objects.get(id=invoice_id, user=self.request.user)
            invoice_items = InvoiceItem.objects.filter(invoice=invoice)
            context['invoice'] = invoice
            context['invoice_items'] = invoice_items
            return context
        except Exception as e:
            # Return not found invoice
            return context

    def get(self, request, *args, **kwargs):
        invoice_id = kwargs.get('pk')

        try:
            Invoice.objects.get(id=invoice_id, user=request.user)
            return super(InvoiceDetailView, self).get(request, *args, **kwargs)
        except:
            # Return not found invoice
            return render(request, 'marketplace/not_found.html')


class PaymentView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        invoice_id = request.POST.get('invoice_id')
        method = request.POST.get('paymentoption')

        invoice = Invoice.objects.get(pk=invoice_id)

        if method == payment_method.wallet():
            # do wallet processing
            information = _('Purchase invoice #') + invoice_id
            response = wallet_manager.purchase_payment(
                user=request.user, amount=invoice.total, description=trans_description.purchase(),
                information=information
            )
            if response['status'] == trans_status.success():
                market_services.payment_complete_process(invoice_id=invoice_id)
            else:
                return HttpResponseRedirect(reverse(viewname='marketplace:invoice_detail', kwargs={'pk': invoice_id}))

        elif method == payment_method.mobilemoney():
            # Do payment processing through mobile money

            # 1. Create a mobile money monetbil payment request.
            tel = request.user.tel1.national_number if request.user.tel1 else request.user.tel2.national_number
            response = purse_services.request_momo_deposit(
                phone_number=tel, amount=invoice.total, user_id=self.request.user.id,
                nsp=_nsp.mtn(), level=0, purpose=momo_purpose.market_purchase(), recipient_id=self.request.user.id,
                charge=0.00, invoice_number=invoice_id
            )

            tracker_id = response['tracker_id']

            # Change Invoice status to Pending Payment
            invoice.status = invoice_status.pending_payment()
            invoice.save()

            protocol = production_settings.PROTOCOL
            domain = str(get_current_site(request))
            path = '/marketplace/invoice/' + invoice_id
            return_url = protocol + domain + path

            payment_url = monetbil.send_payment_widget_request(
                amount=invoice.total, phone=tel, payment_ref=tracker_id, return_url=return_url
            )

            # 3. if payment request is successful, redirect the user to the payment widget.
            if payment_url:
                return HttpResponseRedirect(payment_url)

        else:
            # There's no valid payment method. Error..
            pass

        return HttpResponseRedirect(reverse(viewname='marketplace:invoice_detail', kwargs={'pk': invoice_id}))



