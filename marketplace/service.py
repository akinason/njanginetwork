from django.contrib.auth import get_user_model as UserModel
from django.utils.translation import ugettext_lazy as _

from .models import InvoiceStatus, Invoice, InvoiceItem, Commission
from main import notification
from njangi.models import NSP
from purse.models import MOMOPurpose, TransactionStatus, WalletTransDescription, WalletManager

momo_purpose = MOMOPurpose()
trans_status = TransactionStatus()
trans_description = WalletTransDescription()
wallet_manager = WalletManager()
_nsp = NSP()
invoice_status = InvoiceStatus()
notification_type = notification.NotificationTypes()
notification_manager = notification.NotificationManager()


def payment_complete_process(invoice_id, payment_reference=None, payment_method=None):
    """ Function called when payment is completed. """
    invoice = ""

    try:
        invoice = Invoice.objects.get(pk=invoice_id)
    except Exception as err:
        return False

    if not invoice:
        return False

    # change the status of the invoice.
    invoice.status = invoice_status.paid()
    invoice.is_paid = True
    if payment_method:
        invoice.payment_method = payment_method
    if payment_reference:
        invoice.payment_reference = payment_reference
    invoice.save()
    share_commission(invoice_id)

    return True


def share_commission(invoice_id):

    # 1. Get Product List
    invoice = Invoice.objects.get(pk=invoice_id)
    invoice_lines = InvoiceItem.objects.filter(invoice=invoice)

    if not invoice_lines:
        return False

    # 2. Share commission
    user = invoice.user  # The user who did the purchase.
    admin = UserModel().objects.filter(is_admin=True).order_by('username')[:1].get()
    invoice_total = invoice.total
    for invoice_line in invoice_lines:
        product = invoice_line.product
        level_1_commission = product.level_1_commission
        level_2_commission = product.level_2_commission
        level_3_commission = product.level_3_commission
        level_4_commission = product.level_4_commission
        level_5_commission = product.level_5_commission
        level_6_commission = product.level_6_commission

        # process level 1 commission
        amount = level_1_commission * invoice_total
        upline = pay_commission(
            purchaser=user, downline=user, level=1, percentage=level_1_commission, amount=amount, admin=admin,
            product_name=product.name, invoice=invoice
        )

        # process level 2 commission
        if upline.is_admin:
            return True
        else:
            amount = level_2_commission * invoice_total
            upline = pay_commission(
                purchaser=user, downline=upline, level=2, percentage=level_2_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice
            )

        # process level 3 commission
        if upline.is_admin:
            return True
        else:
            amount = level_3_commission * invoice_total
            upline = pay_commission(
                purchaser=user, downline=upline, level=3, percentage=level_3_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice
            )

        # process level 4 commission
        if upline.is_admin:
            return True
        else:
            amount = level_4_commission * invoice_total
            upline = pay_commission(
                purchaser=user, downline=upline, level=4, percentage=level_4_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice
            )

        # process level 5 commission
        if upline.is_admin:
            return True
        else:
            amount = level_5_commission * invoice_total
            upline = pay_commission(
                purchaser=user, downline=upline, level=5, percentage=level_5_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice
            )

        # process level 6 commission
        if upline.is_admin:
            return True
        else:
            amount = level_6_commission * invoice_total
            upline = pay_commission(
                purchaser=user, downline=upline, level=6, percentage=level_6_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice
            )

    invoice.is_commission_paid = True
    invoice.save()


def pay_commission(purchaser, downline, level, percentage, amount, product_name, admin, invoice):
    """
        This function gets a downline, and searches for the upline(the person who invited the downline)
        and gives the commission to that person and returns that upline for the next computation/sharing.
        purchaser: The person who bought the package.
        downline: The downline depending on the level. Level 1 downline is the purchaser. Used to get the upline.
        level: The level the commission is directed to.
        percentage: The percentage given the the upline.
        amount: The amount given to the upline
        product_name: the name of the product purchased.
        admin: the admin user from whose account the amount has to be transferred
    """
    information = _('market commission from %(username)s on product %(product_name)s.') % {
        'username': purchaser.username, 'product_name': product_name
    }
    upline = ''
    try:
        upline = UserModel().objects.get(pk=downline.sponsor)
    except:
        upline = UserModel().objects.filter(is_admin=True).order_by('username')[:1].get()
    if amount > 0:
        wallet_manager.transfer(
            sender=admin, recipient=upline, amount=amount, information=information, nsp=_nsp.mtn(),
            sender_description=trans_description.commission(), recipient_description=trans_description.commission(),
        )

        text = information + ' Amount: ' + str(round(amount)) + ' XAF.'
        notification_manager.create(
            user_id=upline.id, notification_type=notification_type.commission_received(), text=text
        )

    # Keep track of it in the commission table.
    commission_log = Commission(invoice=invoice, user=upline, level=level, percentage=percentage, amount=amount)
    commission_log.save()
    return upline
