import decimal
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import Sum, F, Value as V, Q
from django.db.models.functions import Coalesce
from django.db.utils import DataError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from main.core import TransactionStatus, NSP_LIST, NSP
from main.models import TEL_MAX_LENGTH

from njanginetwork import settings

D = decimal.Decimal
MTN_MOBILE_MONEY_PARTNER = 'AURBANPAY'
ORANGE_MOBILE_MONEY_PARTNER = 'Extended Limits Inc'
DEFAULT_TRANSACTION_LIST_LIMIT = 30
_nsp = NSP()


class MOMOAPIProvider:
    _afkanerd = 'afkanerd'
    _gloxon = 'gloxon'
    _webshinobis = 'webshinobis'
    _monetbil = 'monetbil'

    def afkanerd(self):
        return self._afkanerd

    def gloxon(self):
        return self._gloxon

    def webshinobis(self):
        return self._webshinobis

    def monetbil(self):
        return self._monetbil

class MOMOPurpose:

    def __init__(self):
        self._contribution = 'contribution'
        self._wallet_load = 'wallet_load'
        self._wallet_withdraw = 'wallet_withdraw'
        self._contribution_wallet_withdraw = 'contribution_wallet_withdraw'
        self._signup_contribution = 'signup_contribution'
        self._market_purchase = 'market_purchase'

    def contribution(self):
        return self._contribution

    def wallet_load(self):
        return self._wallet_load

    def wallet_withdraw(self):
        return self._wallet_withdraw

    def contribution_wallet_withdraw(self):
        return self._contribution_wallet_withdraw

    def signup_contribution(self):
        return self._signup_contribution

    def market_purchase(self):
        return self._market_purchase


class MMRequestType:

    def __init__(self):
        self._deposit = 'deposit'
        self._payout = 'payout'
        self._afkanerd_payout = 'cashin'
        self._afkanerd_deposit = 'cashout'
        self._unknown = 'unknown'

    def payout(self):
        return self._payout

    def deposit(self):
        return self._deposit

    def afkanerd_payout(self):
        return self._afkanerd_payout

    def afkanerd_deposit(self):
        return self._afkanerd_deposit

    def unknown(self):
        return self._unknown


class WalletTransDescription:
    _wallet_load = 'wallet_load'
    _contribution_received = 'contribution_received'
    _contribution_paid = 'contribution_paid'
    _funds_transfer = 'funds_transfer'
    _transfer_received = 'transfer_received'
    _charge = 'charge'
    _funds_withdrawal = 'funds_withdrawal'
    _purchase = 'purchase'
    _user_account_subscription = 'user_account_subscription'
    _commission = 'commission'
    _network_commission = 'network_commission'
    _velocity_reserve = 'velocity_reserve'
    _company_commission = 'company_commission'
    _direct_commission = 'direct_commission'

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

    def user_account_subscription(self):
        return self._user_account_subscription

    def commission(self):
        return self._commission

    def velocity_reserve(self):
        return self._velocity_reserve

    def company_commission(self):
        return self._company_commission

    def direct_commission(self):
        return self._direct_commission

    def network_commission(self):
        return self._network_commission


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

    _already_treated_transaction = _('transaction already treated and completed.')
    _invalid_transaction = _('invalid transaction')
    _not_a_x_transaction = _('not a %s transaction')
    _unauthenticated_transaction = _('unauthenticated transaction.')
    _commission_received = _("%(commission)s from %(username)s level %(level)s contribution.")
    _velocity_reserve = _("velocity reserve from %(username)s level %(level)s contribution.")

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

    def already_treated_transaction(self):
        return self._already_treated_transaction

    def invalid_transaction(self):
        return self._invalid_transaction

    def not_a_x_transaction(self):
        return self._not_a_x_transaction

    def unauthenticated_transaction(self):
        return self._unauthenticated_transaction

    def commission_received(self, commission, username, level):
        return self._commission_received % {
            'commission': commission.replace("_", " ").upper(), 'username': username, 'level': level
        }

    def velocity_reserve(self, username, level):
        return self._velocity_reserve % {'username': username, 'level': level}


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
    tracker_id = models.CharField(_('tracker id'), max_length=20, blank=True)


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
              information=None, trans_code=None, sender=None, status=None):
        # Funds the wallet of the specified user. Returns a dictionary response

        modified_charge = abs(charge) * -1

        wallet = self.model.objects.create(user=user, amount=amount, charge=modified_charge, nsp=nsp)
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
        wallet.status = status if status else self.trans_status.complete()
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
             information=None, trans_code=None, sender=None, status=None, tracker_id=None):
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

            if tracker_id:
                wallet.tracker_id = tracker_id

            if information:
                wallet.information = information
            else:
                information = self.trans_description.funds_withdrawal() + _(' through %(nsp)s') % {'nsp': nsp}
                wallet.information = information
            wallet.description = description
            wallet.status = status if status else self.trans_status.complete()
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
                   information=None, trans_code=None, sender=None, status=None, tracker_id=None):
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
        if tracker_id:
            wallet.tracker_id = tracker_id
        wallet.description = description
        wallet.status = status if status else self.trans_status.complete()
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

    def update_status(self, status, tracker_id):
        # Update's the status of a transaction based on the tracker_id
        try:
            wallet = self.model.objects.filter(tracker_id=tracker_id).get()
            wallet.status = status
            wallet.save()
            return {'status': self.trans_status.success(), 'message': self.trans_message.success_message()}
        except self.model.DoesNotExist:
            return {'status': self.trans_status.failed(), 'message': self.trans_message.invalid_transaction()}
        except self.model.MultipleValuesReturned:
            return {'status': self.trans_status.failed(), 'message': self.trans_message.invalid_transaction()}
        except Exception as e:
            return {'status': self.trans_status.failed(), 'message': e}

    def balance(self, user, nsp):
        trans_status = WalletTransStatus()
        # returns the wallet balance of the specified user.
        wallet = self.model.objects.filter(user=user, nsp=nsp).filter(
            Q(status=trans_status.complete()) | Q(status=trans_status.success()) | Q(status=trans_status.pending())
        ).aggregate(
            balance=Coalesce(Sum(F('amount')+F('charge')), V(0.00))
        )
        balance = D(wallet['balance'])
        return balance

    def load(self, user, amount, nsp, description, charge=0.00, tel=None, thirdparty_reference=None,
             information=None, trans_code=None, sender=None, status=None):
        # Funds the wallet of the specified user. Returns a dictionary response
        try:
            with transaction.atomic():
                response = self._load(
                    user=user, nsp=nsp, amount=amount, description=description, charge=charge, tel=tel,
                    thirdparty_reference=thirdparty_reference, information=information, trans_code=trans_code,
                    sender=sender, status=status,
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
            information=None, trans_code=None, force_pay=False, tracker_id=None, status=None):
        # Pays money from the wallet of the specified user. Returns a dictionary response
        if force_pay:
            response = self._force_pay(
                user=user, nsp=nsp, amount=amount, description=description, charge=charge, tel=tel,
                thirdparty_reference=thirdparty_reference, information=information, trans_code=trans_code,
                tracker_id=tracker_id, status=status
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

    def pay_subscription(self, user, amount, charge=0.00):

        bal1 = self.balance(user, _nsp.mtn())
        bal2 = self.balance(user, _nsp.orange())
        amount1 = 0.00
        amount2 = 0.00
        amt = D(abs(amount))
        total = amt + D(charge)

        if bal1 >= total:
            amount1 = total
        elif bal2 >= total:
            amount2 = total
        elif (D(bal1) + D(bal2)) >= total:
            amount1 = D(bal1)
            amount2 = total - amount1
        else:
            return {
                'status': self.trans_status.failed(), 'message': self.trans_message.insufficient_balance_message()
            }

        trans_code = self._generate_trans_code()
        recipient = get_user_model().objects.filter(is_admin=True).order_by('username')[:1].get()
        response = {}

        if amount1 > 0:
            information = _('Package Subscription through %s wallet.') % _nsp.mtn().upper()
            response = self.transfer(
                sender=user, recipient=recipient, amount=amount1, information=information, nsp=_nsp.mtn(),
                sender_description=self.trans_description.user_account_subscription(),
                recipient_description=self.trans_description.user_account_subscription(),
                trans_code=trans_code
            )
            if response['status'] == self.trans_status.failed():
                return {
                    'status': self.trans_status.failed(), 'message': self.trans_message.failed_message()
                }

        if amount2 > 0:
            information = _('Package Subscription through %s wallet by %s.') % (_nsp.orange().upper(), user.username)
            response = self.transfer(
                sender=user, recipient=recipient, amount=amount2, information=information, nsp=_nsp.orange(),
                sender_description=self.trans_description.user_account_subscription(),
                recipient_description=self.trans_description.user_account_subscription(),
                trans_code=trans_code
            )

        return response

    def purchase_payment(self, user, amount, description, information, charge=0.00):
        bal1 = self.balance(user, _nsp.mtn())
        bal2 = self.balance(user, _nsp.orange())
        amount1 = 0.00
        amount2 = 0.00
        amt = D(abs(amount))
        total = amt + D(charge)

        if bal1 >= total:
            amount1 = total
        elif bal2 >= total:
            amount2 = total
        elif (D(bal1) + D(bal2)) >= total:
            amount1 = D(bal1)
            amount2 = total - amount1
        else:
            return {
                'status': self.trans_status.failed(), 'message': self.trans_message.insufficient_balance_message()
            }

        trans_code = self._generate_trans_code()
        recipient = get_user_model().objects.filter(is_admin=True).order_by('username')[:1].get()
        response = {}

        if amount1 > 0:
            response = self.transfer(
                sender=user, recipient=recipient, amount=amount1, information=information, nsp=_nsp.mtn(),
                sender_description=description,
                recipient_description=description,
                trans_code=trans_code
            )
            if response['status'] == self.trans_status.failed():
                return {
                    'status': self.trans_status.failed(), 'message': self.trans_message.failed_message()
                }

        if amount2 > 0:
            response = self.transfer(
                sender=user, recipient=recipient, amount=amount2, information=information, nsp=_nsp.orange(),
                sender_description=description,
                recipient_description=description,
                trans_code=trans_code
            )
        print(user, recipient)
        return response

    def contribute(self, beneficiaries, nsp, processing_fee):
        user = beneficiaries['contributor']
        level = beneficiaries['level']
        contribution_amount = beneficiaries['contribution_amount']
        contribution_recipient = beneficiaries['recipient']['user']
        object_list = []

        # Now let's proceed to the recipient
        recipient = beneficiaries['recipient']['user']
        recipient_amount = beneficiaries['recipient']['amount']
        if recipient_amount > 0:
            obj = {
                'user': recipient, 'amount': recipient_amount,
                'description': self.trans_description.contribution_received(),
                'information': _('level %(level)s contribution received from %(username)s.') % {
                    'level': level, 'username': user.username
                }
            }
            object_list.append(obj)

        # Now to direct commission
        recipient = beneficiaries['direct_commission']['user']
        recipient_amount = beneficiaries['direct_commission']['amount']
        if recipient_amount > 0:
            obj = {
                'user': recipient, 'amount': recipient_amount,
                'description': self.trans_description.direct_commission(),
                'information': _('level %(level)s direct commission received from %(username)s.') % {
                    'level': level, 'username': user.username
                }
            }
            object_list.append(obj)

        # Now to velocity reserve
        recipient = beneficiaries['velocity_reserve']['user']
        recipient_amount = beneficiaries['velocity_reserve']['amount']
        if recipient_amount > 0:
            obj = {
                'user': recipient, 'amount': recipient_amount,
                'description': self.trans_description.velocity_reserve(),
                'information': _('level %(level)s velocity reserve received from %(username)s.') % {
                    'level': level, 'username': user.username
                }
            }
            object_list.append(obj)

        # Now to company commission
        recipient = beneficiaries['company_commission']['user']
        recipient_amount = beneficiaries['company_commission']['amount']
        if recipient_amount > 0:
            obj = {
                'user': recipient, 'amount': recipient_amount,
                'description': self.trans_description.company_commission(),
                'information': _('level %(level)s company commission received from %(username)s.') % {
                    'level': level, 'username': user.username
                }
            }
            object_list.append(obj)

        # Now to network commission
        beneficiary_list = beneficiaries['network_commission']
        for beneficiary in beneficiary_list:
            recipient = beneficiary['user']
            recipient_amount = beneficiary['amount']
            if recipient_amount > 0:
                obj = {
                    'user': recipient, 'amount': recipient_amount,
                    'description': self.trans_description.network_commission(),
                    'information': _('level %(level)s network commission received from %(username)s.') % {
                        'level': level, 'username': user.username
                    }
                }
                object_list.append(obj)

        # Remove the money from the contributor's account
        response = self.pay(
            user=user, amount=contribution_amount, description=self.trans_description.contribution_paid(),
            information=_('level %(level)s contribution paid to %(recipient)s.') % {
                'level': level, 'recipient': contribution_recipient.username
            },
            charge=processing_fee, nsp=nsp
        )

        if response['status'] == self.trans_status.success():
            for obj in object_list:
                self.load(
                    user=obj['user'], amount=obj['amount'], nsp=nsp, description=obj['description'],
                    information=obj['information'], sender=user
                )
        else:
            return {'status': self.trans_status.failed(), 'message': self.trans_message.failed_message()}
        return {'status': self.trans_status.success(), 'message': self.trans_message.success_message()}

    def withdraw(self, user, amount, nsp, charge=0.00, tel=None, thirdparty_reference=None,
                 information=None, force_withdraw=False, status=None, tracker_id=None):

            response = self.pay(
                user=user, amount=amount, description=self.trans_description.funds_withdrawal(),
                nsp=nsp, charge=charge, tel=tel, thirdparty_reference=thirdparty_reference,
                information=information, force_pay=force_withdraw, status=status, tracker_id=tracker_id
            )
            return response

    def transfer(self, sender, recipient, amount, information, nsp, sender_description=None, recipient_description=None,
                 sender_tel=None, recipient_tel=None, sender_charge=0.00, recipient_charge=0.00,
                 thirdparty_reference=None, trans_code=None
                 ):
        try:
            with transaction.atomic():
                trans_code = trans_code if trans_code else self._generate_trans_code()
                _sender_description = (
                    sender_description if sender_description else self.trans_description.funds_transfer()
                )
                _recipient_description = (
                    recipient_description if recipient_description else self.trans_description.transfer_received()
                )
                pay_response = self._pay(user=sender, amount=amount, nsp=nsp,
                                         description=_sender_description,
                                         charge=sender_charge, tel=sender_tel, information=information,
                                         trans_code=trans_code, thirdparty_reference=thirdparty_reference,
                                         )
                if pay_response['status'] == self.trans_status.success():
                    load_response = self.load(user=recipient, amount=amount, nsp=nsp,
                                              description=_recipient_description,
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


    def account_balances(self):
        """
        Returns the list of all accounts and their balances.
        """
        trans_status = WalletTransStatus()
        # returns the wallet balance of the specified user.
        balances = self.model.objects.filter(user__is_admin=False).filter(
            Q(status=trans_status.complete()) | Q(status=trans_status.success()) | Q(status=trans_status.pending())
        ).values('user').annotate(
            balance=Coalesce(Sum(F('amount')+F('charge')), V(0.00))
        ).order_by('balance')
        
        return balances

class MobileMoney(models.Model):
    request_status = models.CharField(_('request status'), max_length=20, blank=True)
    response_status = models.CharField(_('response status'), max_length=20, blank=True)
    response_code = models.CharField(_('response code'), max_length=15, blank=True)
    callback_status_code = models.CharField(_('callback status code'), max_length=15, blank=True)
    user_auth = models.CharField(_('user authentication'), max_length=255, blank=True)
    request_type = models.CharField(_('request type'), max_length=20)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, verbose_name=_('user'),
                             on_delete=models.CASCADE, related_name='momo_user')
    recipient = models.ForeignKey(get_user_model(), null=True, blank=True, verbose_name=_('recipient'),
                                  on_delete=models.CASCADE, related_name='momo_recipient')
    nsp = models.CharField(_('NSP'), max_length=15)
    tel = models.CharField(_('tel'), max_length=20)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    message = models.TextField(_('message'), blank=True)
    provider = models.CharField(_('Service Provider'), max_length=100, blank=True)
    purpose = models.CharField(_('purpose'), max_length=50, blank=True)
    server_response = models.CharField(_('server response'), max_length=255, blank=True)
    callback_server_response = models.CharField(_('callback server response'), max_length=255, blank=True)
    transaction_id = models.CharField(_('transaction id'), max_length=30, blank=True)
    request_date = models.DateTimeField(_('request date'), default=timezone.now)
    response_date = models.DateTimeField(_('response date'), blank=True, null=True)
    processing_status = models.CharField(_('processing status'), blank=True, max_length=50)
    callback_response_date = models.DateTimeField(_('callback response date'), blank=True, null=True)
    response_transaction_date = models.DateTimeField(_('response tranx date'), blank=True, null=True)
    uuid = models.UUIDField(_('unique verification UUID'), default=uuid.uuid4)
    tracker_id = models.CharField(_('tracker id'), max_length=50, blank=True)
    is_complete = models.BooleanField(_('is complete'), default=False)
    level = models.IntegerField(_('level'), blank=True, null=True)
    charge = models.DecimalField(_('charge'), decimal_places=2, max_digits=10, default=0, blank=True, null=True)
    unique_id = models.CharField(_('api unique id'), max_length=20, blank=True)
    invoice_number = models.CharField(_('invoice number'), max_length=100, blank=True, null=True)


class MobileMoneyManager:

    def __init__(self):
        self.model = MobileMoney
        self.trans_status = TransactionStatus()
        self.mm_request_id = None

    def is_valid(self, tracker_id, uuid=None):
        if uuid:
            try:
                return self.model.objects.filter(tracker_id=tracker_id, uuid=uuid).exists()
            except ValidationError:
                return False
        else:
            return self.model.objects.filter(tracker_id=tracker_id).exists()

    def send_request(self, request_type, nsp, tel, amount, user, provider, purpose, recipient=None, level=None,
                     charge=None, invoice_number=None):
        mm_transaction = self.model.objects.create(
            request_status=self.trans_status.processing(), request_type=request_type, nsp=nsp, tel=tel, amount=amount,
            user=user, purpose=purpose, provider=provider, level=level, charge=charge, invoice_number=invoice_number
        )

        self.mm_request_id = mm_transaction.id
        if recipient:
            mm_transaction.recipient = recipient
        mm_transaction.tracker_id = self.get_tracker_id()
        mm_transaction.save()
        return mm_transaction

    def get_response(self, mm_request_id, response_status=None, response_code=None, message=None,
                     transaction_id=None, response_transaction_date=None, callback_response_date=None,
                     callback_status_code=None, user_auth=None, server_response=None, processing_status=None,
                     unique_id=None, callback_server_response=None, is_complete=False
                     ):
        try:
            mm_transaction = self.model.objects.get(pk=mm_request_id)

            if mm_transaction.is_complete:
                return mm_transaction

            mm_transaction.response_date = timezone.now()

            if callback_status_code:
                mm_transaction.callback_status_code = callback_status_code
                mm_transaction.request_status = self.trans_status.complete()
                mm_transaction.callback_response_date = timezone.now()
            if response_status:
                mm_transaction.response_status = response_status
            if response_code:
                mm_transaction.response_code = response_code
            if message:
                mm_transaction.message = message
            if transaction_id:
                mm_transaction.transaction_id = transaction_id
            if response_transaction_date:
                mm_transaction.response_transaction_date = response_transaction_date
            if callback_response_date:
                mm_transaction.callback_response_date = callback_response_date
            if user_auth:
                mm_transaction.user_auth = user_auth
            if server_response:
                mm_transaction.server_response = server_response
            if processing_status:
                mm_transaction.processing_status = processing_status
            if unique_id:
                mm_transaction.unique_id = unique_id
            if callback_server_response:
                mm_transaction.callback_server_response = callback_server_response
            if is_complete:
                mm_transaction.is_complete = True
            mm_transaction.save()
            return mm_transaction
        except self.model.DoesNotExist:
            return self.model.objects.none()

    def check_transaction(self, mm_request_id):
        pass

    def change_processing_status(self, new_status):
        pass

    def get_tracker_id(self):
        if settings.DEBUG:
            tracker_id = 'L%s' % self.mm_request_id
        else:
            tracker_id = 'P%s' % self.mm_request_id
        return tracker_id

    def get_mm_transaction_id(self, tracker_id, uuid=None):
        try:
            mm_transaction = self.model.objects.filter(tracker_id=tracker_id).get()
            return mm_transaction.id
        except self.model.MultipleObjectsReturned or self.model.DoesNotExist:
            if uuid:
                try:
                    mm_transaction = self.model.objects.filter(uuid=uuid).get()
                    return mm_transaction.id
                except self.model.DoesNotExist:
                    return 0
            else:
                return 0

    def get_mm_transaction(self, tracker_id, uuid=None):
        try:
            mm_transaction = self.model.objects.filter(tracker_id=tracker_id).get()
            return mm_transaction
        except self.model.MultipleObjectsReturned or self.model.DoesNotExist:
            if uuid:
                try:
                    mm_transaction = self.model.objects.filter(uuid=uuid).get()
                    return mm_transaction
                except self.model.DoesNotExist:
                    return self.model.objects.none()
            else:
                return self.model.objects.none()
        except self.model.DoesNotExist:
            return self.model.objects.none()
