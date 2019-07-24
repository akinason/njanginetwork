from django.contrib.auth import get_user_model as UserModel
from django.utils.translation import ugettext_lazy as _

from .models import InvoiceStatus, Invoice, InvoiceItem, Commission
from main import notification
from mailer import services as mailer_services
from njangi.models import NSP
from njanginetwork.celery import app
from purse.models import MOMOPurpose, TransactionStatus, WalletTransDescription, WalletManager


momo_purpose = MOMOPurpose()
trans_status = TransactionStatus()
trans_description = WalletTransDescription()
wallet_manager = WalletManager()
_nsp = NSP()
invoice_status = InvoiceStatus()
notification_type = notification.NotificationTypes()
notification_manager = notification.NotificationManager()


@app.task 
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
            product_name=product.name, invoice=invoice, product=product
        )

        # process level 2 commission
        amount = level_2_commission * invoice_total
        if upline.is_admin:
            if amount > 0:
                commission_log = Commission(invoice=invoice, product=product, user=admin, level=2,
                                            percentage=level_2_commission, amount=amount)
                commission_log.save()
            return True
        else:
            upline = pay_commission(
                purchaser=user, downline=upline, level=2, percentage=level_2_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice, product=product
            )

        # process level 3 commission
        amount = level_3_commission * invoice_total
        if upline.is_admin:
            if amount > 0:
                commission_log = Commission(invoice=invoice, product=product, user=admin, level=3,
                                            percentage=level_3_commission, amount=amount)
                commission_log.save()
            return True
        else:
            upline = pay_commission(
                purchaser=user, downline=upline, level=3, percentage=level_3_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice, product=product
            )

        # process level 4 commission
        amount = level_4_commission * invoice_total
        if upline.is_admin:
            if amount > 0:
                commission_log = Commission(invoice=invoice, product=product, user=admin, level=4,
                                            percentage=level_4_commission, amount=amount)
                commission_log.save()
            return True
        else:
            upline = pay_commission(
                purchaser=user, downline=upline, level=4, percentage=level_4_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice, product=product
            )

        # process level 5 commission
        amount = level_5_commission * invoice_total
        if upline.is_admin:
            if amount > 0:
                commission_log = Commission(invoice=invoice, product=product, user=admin, level=5,
                                            percentage=level_5_commission, amount=amount)
                commission_log.save()
            return True
        else:
            upline = pay_commission(
                purchaser=user, downline=upline, level=5, percentage=level_5_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice, product=product
            )

        # process level 6 commission
        amount = level_6_commission * invoice_total
        if upline.is_admin:
            if amount > 0:
                commission_log = Commission(invoice=invoice, product=product, user=admin, level=6,
                                            percentage=level_6_commission, amount=amount)
                commission_log.save()
            return True
        else:
            upline = pay_commission(
                purchaser=user, downline=upline, level=6, percentage=level_6_commission, amount=amount, admin=admin,
                product_name=product.name, invoice=invoice, product=product
            )

    invoice.is_commission_paid = True
    invoice.save()


def pay_commission(purchaser, downline, level, percentage, amount, product_name, admin, invoice, product):
    """
        This function gets a downline, and searches for the upline(the person who invited the downline)
        and gives the commission to that person and returns that upline for the next computation/sharing.
        purchaser: The person who bought the package.
        downline: The downline depending on the level. Level 1 downline is the purchaser. Used to get the upline.
        level: The level the commission is directed to.
        percentage: The percentage given to the upline.
        amount: The amount given to the upline
        product_name: the name of the product purchased.
        admin: the admin user from whose account the amount has to be transferred
    """
    information = _('market commission from %(username)s on product %(product_name)s.') % {
        'username': purchaser.username, 'product_name': product_name
    }
    upline = ''
    recipient = ''
    try:
        upline = UserModel().objects.get(pk=downline.sponsor)
    except:
        upline = admin
    
    if upline.is_admin: 
        recipient = upline
    else:
        if user_has_already_purchased_pack(user=upline, product=product):
            # Verify if the user has already purchased the pack.
            recipient = upline
        else:
            recipient = admin

            # Inform the upline, he/she has missed a commission because he/she has not yet purchased the pack.
            if amount > 0:
                notification_manager.templates.missed_commission(
                    user_id=upline.id, level=level, amount=amount, buyer_name=purchaser.username, product_name=product.name
                )
                # send an SMS
                mailer_services.send_missed_commission_sms(
                    user_id=upline.id, amount=amount, product_name=product.name
                )

    if amount > 0:
        wallet_manager.transfer(
            sender=admin, recipient=recipient, amount=amount, information=information, nsp=_nsp.mtn(),
            sender_description=trans_description.commission(), recipient_description=trans_description.commission(),
        )
        wallet_manager.reduce_balance(user=admin, available_balance=amount, force=True)
        wallet_manager.increase_balance(user=recipient, available_balance=amount)

        # Create a notification on the user's dashboard.
        text = information + ' Amount: ' + str(round(amount)) + ' XAF.'
        notification_manager.create(
            user_id=upline.id, notification_type=notification_type.commission_received(), text=text
        )

        # Send an SMS to the user.

        # Keep track of it in the commission table.
        commission_log = Commission(invoice=invoice, product=product, user=recipient, level=level, percentage=percentage, amount=amount)
        commission_log.save()
    return upline


def user_has_already_purchased_pack(user, product):
    """
        This function verifies if the user has already purchased the specified pack. It returns true or false.
    """
    count = InvoiceItem.objects.filter(product=product, invoice__user=user, invoice__status=invoice_status.paid).count()

    return True if count > 0 else False
