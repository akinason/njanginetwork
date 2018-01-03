import decimal
from django.db import models, IntegrityError, transaction
from django.db.models import Sum, F, Value as V
from django.db.models.functions import Coalesce
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from main.core import TransactionStatus, NSP_LIST
from main.models import TEL_MAX_LENGTH
from django.db.utils import DataError

# Create your models here.
D = decimal.Decimal
MTN_MOBILE_MONEY_PARTNER = 'WEBSHINOBIS Inc'
ORANGE_MOBILE_MONEY_PARTNER = 'Extended Limits Inc'
DEFAULT_TRANSACTION_LIST_LIMIT = 30


class WalletTransDescription:
    _wallet_load = _('wallet_load')
    _contribution_received = _('contribution_received')
    _contribution_paid = _('contribution_paid')
    _funds_transfer = _('funds_transfer')
    _transfer_received = _('transfer_received')
    _charge = _('charge')
    _funds_withdrawal = _('funds_withdrawal')
    _purchase = _('purchase')

    def wallet_load(self):
        return self._wallet_load

    def contribution_received(self):
        return self._contribution_received

    def contribution_paid(self):
        return self._contribution_paid

    def funds_transfer(self):
        return self._funds_transfer

    def transfer_received(self):
        return self._transfer_received

    def charge(self):
        return self._charge

    def funds_withdrawal(self):
        return self._funds_withdrawal

    def purchase(self):
        return self._purchase


class WalletTransMessage:
    _failed_message = _('operation failed.')
    _wallet_load_success_message = _("%(user)s's wallet load by %(nsp)s, amount: %(amount)s , fees: %(charge)s, "
                                     "ref: %(reference)s ")
    _success_message = _('operation successful')
    _insufficient_balance = _('insufficient balance')
    _provide_contact_message = _('provide %(nsp)s phone number and/or verify your %(nsp)s phone number')
    _provide_contact_and_receive_payments = _('you have %(nsp)s payments pending reception. please ') + \
                                            str(_provide_contact_message)
    _pending_processing = _('transaction pending processing')

    def failed_message(self):
        return self._failed_message

    def wallet_load_success_message(self):
        return self._wallet_load_success_message

    def success_message(self):
        return self._success_message

    def insufficient_balance_message(self):
        return self._insufficient_balance

    def provide_contact_message(self):
        return self._provide_contact_message

    def provide_contact_and_receive_payments(self):
        return self._provide_contact_and_receive_payments

    def pending_message(self):
        return self._pending_processing


class WalletTransStatus:
    TRANXStatus = TransactionStatus()
    _complete = TRANXStatus.complete()
    _failed = TRANXStatus.failed()
    _pending = TRANXStatus.pending()
    _success = TRANXStatus.success()
    _failure = TRANXStatus.failure()

    def complete(self):
        return self._complete

    def failed(self):
        return self._failed

    def pending(self):
        return self._pending

    def success(self):
        return self._success

    def failure(self):
        return self._failure()


class WalletModel(models.Model):
    trans_status = WalletTransStatus()

    description = models.CharField(max_length=50, verbose_name=_('description'), blank=True)
    information = models.CharField(max_length=100, verbose_name=_('transaction information'), blank=True)
    reference = models.CharField(_('reference'), max_length=20, unique=True, db_index=True, null=True)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    charge = models.DecimalField(_('fees'), max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(_('transaction status'), max_length=20, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name=_('user'))
    trans_code = models.CharField(max_length=20, verbose_name=_('transaction code'), blank=True)
    sender = models.ForeignKey(get_user_model(), verbose_name=_('fund sender'),
                               related_name='fund_sender', on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateTimeField(default=timezone.now)
    thirdparty_reference = models.CharField(max_length=30, verbose_name=_('third party reference'), db_index=True)
    nsp = models.CharField(_('network service provider'), max_length=30, blank=True, null=True)
    tel = models.CharField(_('phone number'), max_length=TEL_MAX_LENGTH, blank=True)


class WalletManager:
    model = WalletModel
    trans_status = WalletTransStatus()
    trans_message = WalletTransMessage()
    trans_description = WalletTransDescription()

    def _generate_trans_code(self):
        # Returns a transaction code to be used for a single or group of transactions.
        while True:
            code = get_user_model().objects.make_random_password(length=7, allowed_chars='23456789')
            trans_code = str(timezone.now().year) + str(code)  # Convert to string to combine and not add.
            trans_code = int(trans_code)  # Convert the string back to integer.
            if not self.model.objects.filter(trans_code=trans_code).exists():
                return trans_code

    def _generate_reference(self):
        # Returns a reference to be used for each transaction in the model.
        while True:
            code = get_user_model().objects.make_random_password(length=7, allowed_chars='23456789')
            reference = str(timezone.now().year) + str(code)  # Convert to string to combine and not add.
            reference = int(reference)  # Convert the string back to integer.
            if not self.model.objects.filter(reference=reference).exists():
                return reference

    def _load(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
              information=None, trans_code=None, sender=None):
        # Funds the wallet of the specified user. Returns a dictionary response

        modified_charge = abs(charge) * -1

        wallet = self.model.objects.create( user=user, amount=amount, charge=modified_charge, nsp=nsp )
        if tel:
            wallet.tel = tel
        if thirdparty_reference:
            wallet.thirdparty_reference = thirdparty_reference
        reference = self._generate_reference()
        if not trans_code:
            trans_code = self._generate_trans_code()
        wallet.reference = reference
        wallet.trans_code = trans_code
        if information:
            wallet.information = information
        else:
            information = self.trans_description.wallet_load() + _(' through %(nsp)s') % {'nsp': nsp}
            wallet.information = information
        wallet.description = description
        wallet.status = self.trans_status.complete()
        if sender:
            wallet.sender = sender
        wallet.save()
        response = {
            'status':  self.trans_status.success(),
            'message': self.trans_message.success_message(),
            'phoneNumber': tel,
            'transactionId': reference,
            'transactionDate': wallet.created_on,
            'description': self.trans_description.wallet_load().replace('_', ' '),
            'charge': abs(charge),
            'amount': amount,
            'instance': wallet,
        }
        return response

    def _pay(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
             information=None, trans_code=None, sender=None):
        # Pays money from the wallet of the specified user. Returns a dictionary response,
        # Checks to ensure the user has sufficient balance in his/her account.
        amount = D(amount)
        charge = D(charge)
        total = D(abs(amount)) + D(abs(charge))

        if self.balance(user, nsp) < total:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.insufficient_balance_message(),
            }
            return response
        else:
            neg_amount = abs(amount) * -1
            neg_charge = abs(charge) * -1
            wallet = self.model.objects.create(user=user, amount=neg_amount, charge=neg_charge, nsp=nsp)

            if tel:
                wallet.tel = tel
            if thirdparty_reference:
                wallet.thirdparty_reference = thirdparty_reference
            reference = self._generate_reference()
            if not trans_code:
                trans_code = self._generate_trans_code()

            wallet.reference = reference
            wallet.trans_code = trans_code

            if information:
                wallet.information = information
            else:
                information = self.trans_description.funds_withdrawal() + _(' through %(nsp)s') % {'nsp': nsp}
                wallet.information = information
            wallet.description = description
            wallet.status = self.trans_status.complete()
            if sender:
                wallet.sender = sender
            wallet.save()
            response = {
                'status': self.trans_status.success(),
                'message': self.trans_message.success_message(),
                'phoneNumber': tel,
                'transactionId': reference,
                'transactionDate': wallet.created_on,
                'description': description.replace('_', ' '),
                'charge': abs(charge),
                'amount': abs(amount),
                'instance': wallet,
            }
            return response

    def _force_pay(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
                   information=None, trans_code=None, sender=None):
        # Pays money from the wallet of the specified user. Returns a dictionary response,
        # Does not Check to ensure the user has sufficient balance in his/her account.
        amount = D(amount)
        charge = D(charge)
        neg_amount = abs(amount) * -1
        neg_charge = abs(charge) * -1
        wallet = self.model.objects.create(user=user, amount=neg_amount, charge=neg_charge, nsp=nsp)

        if tel:
            wallet.tel = (str(tel)[:TEL_MAX_LENGTH]) if len(str(tel)) > TEL_MAX_LENGTH else str(tel)
        if thirdparty_reference:
            wallet.thirdparty_reference = thirdparty_reference
        reference = self._generate_reference()
        if not trans_code:
            trans_code = self._generate_trans_code()

        wallet.reference = reference
        wallet.trans_code = trans_code

        if information:
            wallet.information = information
        else:
            information = self.trans_description.funds_withdrawal() + _(' through %(nsp)s') % {'nsp': nsp}
            wallet.information = information
        wallet.description = description
        wallet.status = self.trans_status.complete()
        if sender:
            wallet.sender = sender
        wallet.save()
        response = {
            'status': self.trans_status.success(),
            'message': self.trans_message.success_message(),
            'phoneNumber': tel,
            'transactionId': reference,
            'transactionDate': wallet.created_on,
            'description': description.replace('_', ' '),
            'charge': abs(charge),
            'amount': abs(amount),
            'instance': wallet,
        }
        return response

    def balance(self, user, nsp):
        # returns the wallet balance of the specified user.
        wallet = self.model.objects.filter(user=user, nsp=nsp).aggregate(
            balance=Coalesce(Sum(F('amount')+F('charge')), V(0.00))
        )
        balance = D(wallet['balance'])
        return balance

    def load(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
             information=None, trans_code=None, sender=None):
        # Funds the wallet of the specified user. Returns a dictionary response
        try:
            with transaction.atomic():
                response = self._load(
                    user=user, nsp=nsp, amount=amount, description=description, charge=charge, tel=tel,
                    thirdparty_reference=thirdparty_reference, information=information, trans_code=trans_code,
                    sender=sender
                )
                if response['status'] == self.trans_status.success():
                    del response['instance']  # Delete the WalletModel instance before returning the response.
                return response
        except IntegrityError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response
        except DataError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response

    def pay(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
            information=None, trans_code=None, force_pay=False):
        # Pays money from the wallet of the specified user. Returns a dictionary response
        if force_pay:
            response = self._force_pay(
                user=user, nsp=nsp, amount=amount, description=description, charge=charge, tel=tel,
                thirdparty_reference=thirdparty_reference, information=information, trans_code=trans_code
            )
            return response
        else:
            try:
                with transaction.atomic():
                    response = self._pay(
                        user=user, nsp=nsp, amount=amount, description=description, charge=charge, tel=tel,
                        thirdparty_reference=thirdparty_reference, information=information, trans_code=trans_code
                    )
                    # del response['instance']
                    if response['status'] == self.trans_status.success():
                        del response['instance']  # Delete the WalletModel instance before returning the response.
                    return response
            except IntegrityError:
                response = {
                    'status': self.trans_status.failed(),
                    'message': self.trans_message.failed_message()
                }
                return response
            except DataError:
                response = {
                    'status': self.trans_status.failed(),
                    'message': self.trans_message.failed_message()
                }
                return response

    def contribute(self, sender, recipient, sender_amount, recipient_amount, information, nsp, sender_tel=None,
                   recipient_tel=None, sender_charge=0.00, recipient_charge=0.00, thirdparty_reference=None,
                   trans_code=None
                   ):

        try:
            with transaction.atomic():
                if not trans_code:
                    trans_code = self._generate_trans_code()
                pay_response = self._pay(user=sender, amount=sender_amount, nsp=nsp,
                                         description=self.trans_description.contribution_paid(),
                                         charge=sender_charge, tel=sender_tel,
                                         thirdparty_reference=thirdparty_reference,
                                         information=information, trans_code=trans_code
                                         )
                if pay_response['status'] == self.trans_status.success():
                    load_response = self.load(user=recipient, amount=recipient_amount, nsp=nsp,
                                              description=self.trans_description.contribution_received(),
                                              charge=recipient_charge, tel=recipient_tel, information=information,
                                              trans_code=trans_code, thirdparty_reference=thirdparty_reference,
                                              sender=sender
                                              )
                    if load_response['status'] == self.trans_status.success():  # Construct the response.
                        response = {
                            'status': self.trans_status.success(),
                            'message': self.trans_message.success_message(),
                            'transactionCode': trans_code,
                            'senderPhoneNumber': pay_response['phoneNumber'],
                            'recipientPhoneNumber': load_response['phoneNumber'],
                            'senderTransactionId': pay_response['transactionId'],
                            'recipientTransactionId': load_response['transactionId'],
                            'senderTransactionDate': pay_response['transactionDate'],
                            'senderDescription': pay_response['description'],
                            'recipientDescription': load_response['description'],
                            'senderCharge': pay_response['charge'],
                            'recipientCharge': load_response['charge'],
                            'senderAmount': pay_response['amount'],
                            'recipientAmount': load_response['amount']
                        }
                        return response
                    else:
                        # There was an error during execution, rollback the first operation "pay_response"
                        # and return the load_response which contains the failed status.
                        instance = pay_response['instance']
                        instance.delete()
                        return load_response
                else:
                    return pay_response
        except IntegrityError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response
        except DataError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response
        except KeyError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response

    def withdraw(self, user, amount, nsp, charge=0.00, tel=None, thirdparty_reference=None,
                 information=None, force_withdraw=False):

            response = self.pay(
                user=user, amount=amount, description=self.trans_description.funds_withdrawal(),
                nsp=nsp, charge=charge, tel=tel, thirdparty_reference=thirdparty_reference,
                information=information, force_pay=force_withdraw
            )
            return response

    def load_and_contribute(self, user, recipient, loading_amount, contribution_amount, recipient_amount, information,
                            nsp, loading_charge=0.00, recipient_charge=0.00, contribution_charge=0.00, sender_tel=None,
                            recipient_tel=None, thirdparty_reference=None
                            ):
            # Funds the user's wallet and does a contribution to another person. Transaction will fail if the user
            # has insufficient balance.
            try:
                trans_code = self._generate_trans_code()
                load_response = self._load(
                    user=user, amount=loading_amount, nsp=nsp, description=self.trans_description.wallet_load(),
                    charge=loading_charge, tel=sender_tel, thirdparty_reference=thirdparty_reference,
                    information=information, trans_code=trans_code
                )

                if load_response['status'] == self.trans_status.success():  # Proceed with the contribution.
                    contribute_response = self.contribute(
                        sender=user, recipient=recipient, sender_amount=contribution_amount,
                        recipient_amount=recipient_amount, information=information, nsp=nsp, sender_tel=sender_tel,
                        recipient_tel=recipient_tel, sender_charge=contribution_charge,
                        recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference,
                        trans_code=trans_code
                    )

                    if contribute_response['status'] == self.trans_status.success():

                        # construct a response and return.
                        contribute_response.update(
                            {
                                'loadAmount': load_response['amount'],
                                'loadCharge': load_response['charge'],
                                'loadPhoneNumber': load_response['phoneNumber'],
                                'loadTransactionId': load_response['transactionId'],
                                'loadDescription': load_response['description'],
                                'loadTransactionDate': load_response['transactionDate'],
                                'loadStatus': load_response['status'],
                            }
                        )
                        return contribute_response
                    else:
                        # Rollback the load transaction and return the contribution_response which contains a
                        # failed transaction status.
                        instance = load_response['instance']
                        instance.delete()
                        return contribute_response
                else:
                    return load_response
            except IntegrityError:
                response = {
                    'status': self.trans_status.failed(),
                    'message': self.trans_message.failed_message(),
                    'reason': 'IntegrityError'
                }
                return response
            except DataError:
                response = {
                    'status': self.trans_status.failed(),
                    'message': self.trans_message.failed_message(),
                    'reason': 'DataError',
                }
                return response

    def transfer(self, sender, recipient, amount, information, nsp, sender_tel=None, recipient_tel=None,
                 sender_charge=0.00, recipient_charge=0.00, thirdparty_reference=None
                 ):

        try:
            with transaction.atomic():
                trans_code = self._generate_trans_code()
                pay_response = self._pay(user=sender, amount=amount, nsp=nsp,
                                         description=self.trans_description.funds_transfer(),
                                         charge=sender_charge, tel=sender_tel, thirdparty_reference=thirdparty_reference,
                                         information=information, trans_code=trans_code
                                         )
                if pay_response['status'] == self.trans_status.success():
                    load_response = self.load(user=recipient, amount=amount, nsp=nsp,
                                              description=self.trans_description.transfer_received(),
                                              charge=recipient_charge, tel=recipient_tel, information=information,
                                              trans_code=trans_code, thirdparty_reference=thirdparty_reference,
                                              sender=sender
                                              )
                    if load_response['status'] == self.trans_status.success():  # Construct the response.
                        response = {
                            'status': self.trans_status.success(),
                            'message': self.trans_message.success_message(),
                            'transactionCode': trans_code,
                            'senderPhoneNumber': pay_response['phoneNumber'],
                            'recipientPhoneNumber': load_response['phoneNumber'],
                            'senderTransactionId': pay_response['transactionId'],
                            'recipientTransactionId': load_response['transactionId'],
                            'senderTransactionDate': pay_response['transactionDate'],
                            'senderDescription': pay_response['description'],
                            'recipientDescription': load_response['description'],
                            'senderCharge': pay_response['charge'],
                            'recipientCharge': load_response['charge'],
                            'senderAmount': pay_response['amount'],
                            'recipientAmount': load_response['amount']
                        }
                        return response
                    else:
                        # There was an error during execution, rollback the first operation "pay_response"
                        # and return the load_response which contains the failed status.
                        instance = pay_response['instance']
                        instance.delete()
                        return load_response
                else:
                    return pay_response
        except IntegrityError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response
        except DataError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response
        except KeyError:
            response = {
                'status': self.trans_status.failed(),
                'message': self.trans_message.failed_message()
            }
            return response

    def transaction_list(self, user, nsp, last_x_transactions=0):
        """
        :param user: The user whose transaction list is to be returned.
        :param nsp: The Network service provider.
        :param last_x_transactions: The number of transactions to return. defaults to DEFAULT_TRANSACTION_LIST_LIMIT
        :return: The list of transactions
        """
        if nsp in NSP_LIST:
            if last_x_transactions:
                transaction_limit = int(last_x_transactions)
            else:
                transaction_limit = DEFAULT_TRANSACTION_LIST_LIMIT

            return self.model.objects.filter(user=user, nsp=nsp).order_by(
                '-created_on'
            )[:transaction_limit]

        else:
            return self.model.objects.none()
