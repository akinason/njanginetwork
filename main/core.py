

class NSP:
    """
    a class that returns the list of Network Service Providers to avoid typographical errors in other parts
    of the application.
    """
    _orange = 'orange'
    _mtn = 'mtn'
    _mtn_wallet = 'mtn_wallet'
    _orange_wallet = 'orange_wallet'

    def orange(self):
        return self._orange

    def mtn(self):
        return self._mtn

    def mtn_wallet(self):
        return self._mtn_wallet

    def orange_wallet(self):
        return self._orange_wallet

nsp = NSP()
NSP_LIST = [nsp.mtn(), nsp.orange()]


class TransactionStatus:
    """
    A class that holds payment status to avoid typographical errors in other parts of the application
    """
    _complete = 'complete'
    _active = 'active'
    _processing = 'processing'
    _cancelled = 'cancelled'
    _provide_contact = 'provide_contact'
    _suspended = 'suspended'
    _pending = 'pending'
    _pending_confirmation = 'pending_confirmation'
    _failed = 'failed'
    _confirmed = 'confirmed'
    _success = 'success'
    _failure = 'failure'

    def complete(self):
        return self._complete

    def active(self):
        return self._active

    def processing(self):
        return self._processing

    def cancelled(self):
        return self._cancelled

    def provide_contact(self):
        return self._provide_contact

    def suspended(self):
        return self._suspended

    def pending_confirmation(self):
        return self._pending_confirmation

    def pending(self):
        return self._pending

    def failed(self):
        return self._failed

    def confirmed(self):
        return self._confirmed

    def success(self):
        return self._success

    def failure(self):
        return self._failure


class FailedOperationTypes:
    _contribution = 'contribution'
    _account_load_api_processed = 'account_load_api_processed'
    _withdrawal = 'withdrawal'

    def contribution(self):
        # Used when a contribution operation fails.
        return self._contribution

    def account_load_api_processed(self):
        # Used if the transaction has already been processed by thirdparty API pending
        # Loading to the user's wallet.
        return self._account_load_api_processed

    def withdrawal(self):
        # Used when a withdrawal request fails.
        return self._withdrawal
