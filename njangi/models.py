import datetime

from django.contrib.auth import get_user_model as UserModel
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Q, Count, F, ExpressionWrapper, DurationField
from django.db.models.functions import Extract
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from main.core import NSP
from main.models import TEL_MAX_LENGTH


NSP_CONTRIBUTION_PROCESSING_FEE_RATE = 0.025
NSP_WALLET_LOAD_PROCESSING_FEE_RATE = 0.0
NSP_WALLET_WITHDRAWAL_PROCESSING_FEE_RATE = 0
WALLET_CONTRIBUTION_PROCESSING_FEE_RATE = 0.025
DEFAULT_USER_ACCOUNT_LIMIT = 2

NSP_CONTRIBUTION_PROCESSING_FEE_RATES = {
    1: 0.025,
    2: 0.025,
    3: 0.025,
    4: 0.025,
    5: 0.025,
    6: 0.025,
}

WALLET_CONTRIBUTION_PROCESSING_FEE_RATES = {
    1: 0.025,
    2: 0.025,
    3: 0.025,
    4: 0.025,
    5: 0.025,
    6: 0.025,
}

NJANGI_LEVELS = [1, 2, 3, 4, 5, 6]
NJANGI_LEVEL_LIST = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))
LEVEL_CONTRIBUTIONS = {
    1: 2000,
    2: 3000,
    3: 5000,
    4: 10000,
    5: 25000,
    6: 50000,
}
CONTRIBUTION_INTERVAL_IN_DAYS = 30
# Network Service Provider List
nsp = NSP()
NSP_LIST = (
    (nsp.mtn(), _('MTN')),
    (nsp.orange(), _('Orange')),
    (nsp.mtn_wallet(), _('MTN Wallet')),
    (nsp.orange_wallet(), _('Orange Wallet')),
)


class NjangiTreeSide:
    _left = 'L'
    _right = 'R'

    def left(self):
        return self._left

    def right(self):
        return self._right


class UserAccountSubscriptionType:
    _monthly = 'monthly'
    _annually = 'annually'

    def monthly(self):
        return self._monthly

    def annually(self):
        return self._annually


class FailedOperations(models.Model):
    user = models.ForeignKey(UserModel(), related_name='sender', on_delete=models.CASCADE)
    recipient = models.ForeignKey(UserModel(), related_name='recipient', on_delete=models.CASCADE, blank=True, null=True)
    level = models.PositiveIntegerField(blank=True,  null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    nsp = models.CharField(max_length=20)
    sender_tel = models.CharField(max_length=TEL_MAX_LENGTH, blank=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50)
    operation_type = models.CharField(max_length=100)
    message = models.CharField(max_length=150, blank=True)
    response_status = models.CharField(max_length=50, blank=True)
    created_on = models.DateTimeField(default=timezone.now)
    resolved_on = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    tracker_id = models.CharField(_('tracker id'), max_length=15, blank=True)


class LevelModel(models.Model):
    """
    The model that tracks user levels and their level status (is_active). Users will not receive level contribution
     if they are not active for that level. But a user will not receive any contribution if he/she is not active in the
     USER model.
    """
    user = models.ForeignKey(UserModel(), null=False, blank=False,
                             verbose_name=_('user'), related_name='level_user', on_delete=models.CASCADE)
    level = models.PositiveIntegerField(_('njangi level'), choices=NJANGI_LEVEL_LIST)
    is_active = models.BooleanField(default=False)
    last_payment = models.DateTimeField(_('last payment date'), blank=True, null=True)
    next_payment = models.DateTimeField(_('next payment date'), blank=True, null=True)
    recipient = models.ForeignKey(UserModel(), verbose_name=_('recipient'), related_name='last_recipient',
                                  on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_sent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_received = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        unique_together = (('user', 'level'),)


class NjangiTree(MPTTModel):
    """
    A MPTT Model that manages Hierarchical representation of njangi network users.
    """
    tree_side = NjangiTreeSide()

    user = models.OneToOneField(UserModel(), null=False, blank=False, related_name='child_user',
                                verbose_name=_('child user'), on_delete=models.CASCADE, db_index=True, )
    parent_user = models.ForeignKey(UserModel(), blank=True, null=True, related_name='parent_user',
                                    verbose_name=_('parent user'), on_delete=models.CASCADE, db_index=True)
    side = models.CharField(_('position side'), max_length=1, blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            db_index=True, on_delete=models.CASCADE)

    class MPTTMeta:
        unique_together = (('user', 'parent_user'), ('user', 'side'))

    def __str__(self):
        return str(self.user.username) + '(' + str(self.pk) + ')' + ' ' + str(self.side)

    def is_left_downline(self):
        """
        Returns True if it's a left downline or false if it's not.
        """
        if self.side == self.tree_side.left():
            return True
        else:
            return False

    def is_right_downline(self):
        """
        Returns True if it's a right downline or False otherwise.
        """
        if self.side == self.tree_side.right():
            return True
        else:
            return False

    def has_left_downline(self):
        """
        Returns True if the user has a left downline or False otherwise.
        """

        if self.is_leaf_node():
            return False

        children = self.get_children()
        for child in children:
            if child.side == self.tree_side.left():
                return True
        return False

    def has_right_downline(self):
        """
          Returns True if the user has a right downline or False otherwise.
        """
        if self.is_leaf_node():
            return False

        children = self.get_children()
        for child in children:
            if child.side == self.tree_side.right():
                return True
        return False

    def get_left_downline(self):
        """
        Returns an instance of the left sibling if it exist or None. Its advised to check for self.has_left_downline
        before calling this method.
        """
        if self.has_left_downline():
            try:
                return NjangiTree.objects.filter(parent_user=self.user, side=self.tree_side.left()).get()
            except (KeyError, NjangiTree.DoesNotExist):
                return NjangiTree.objects.none()
        else:
            return NjangiTree.objects.none()

    def get_right_downline(self):
        """
        Returns an instance of the left sibling if it exist or None. Its advised to check for self.has_left_downline
        before calling this method.
        """
        if self.has_right_downline():
            try:
                return NjangiTree.objects.filter(parent_user=self.user, side=self.tree_side.right()).get()
            except (KeyError, NjangiTree.DoesNotExist):
                return NjangiTree.objects.none().get()
        else:
            return NjangiTree.objects.none().get()

    def get_downlines(self, limit=3, limit_output=False):
        """
        Creates a QuerySet containing descendants of the user instance, in tree order.
        If include_self is True, the QuerySet will also include the model instance itself.
        Raises a ValueError if the instance isn’t saved already.
        """
        queryset = super(NjangiTree, self).get_descendants(include_self=False)
        if limit_output:
            queryset = queryset[:limit]
        return queryset

    def get_left_downlines(self, limit=3, limit_output=False):
        """
        Creates a QuerySet containing descendants of the user's left side or left leg, in tree order.
        Raises a ValueError if the instance isn’t saved already.
        """
        if self.has_left_downline():
            downline = self.get_left_downline()
            queryset = downline.get_descendants(include_self=True)
            if limit_output:
                queryset = queryset[:limit]
            return queryset
        else:
            return NjangiTree.objects.none()

    def get_right_downlines(self, limit=3, limit_output=False):
        """
        Creates a QuerySet containing descendants of the user's left side or left leg, in tree order.
        Raises a ValueError if the instance isn’t saved already.
        """
        if self.has_right_downline():
            downline = self.get_right_downline()
            queryset = downline.get_descendants(include_self=True)

            if limit_output:
                queryset = queryset[:limit]
            return queryset
        else:
            return NjangiTree.objects.none()

    def get_left_downline_count(self):
        """
        Returns the number of people on the left leg of the user.
        """
        if self.has_left_downline():
            return self.get_left_downline().get_descendant_count() + 1
        else:
            return 0

    def get_right_downline_count(self):
        """
        Returns the number of people on the right leg of the user or zero if the user does not have a right downline.
        """
        if self.has_right_downline():
            return self.get_right_downline().get_descendant_count() + 1
        else:
            return 0

    def get_left_unmatched_downlines(self, limit=3, limit_output=False):
        """
        Returns a queryset containing the list of users having 1 or no downline on the left leg in tree order.
        If the user does not have a left downline, it returns the user.
        """
        if self.has_left_downline():
            queryset = self.get_left_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )
            if limit_output:
                queryset = queryset[:limit]
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)

    def get_right_unmatched_downlines(self, limit=3, limit_output=False):
        """
        Returns a queryset containing the list of users having 1 or no downline on the right leg in tree order.
        If the user does not have a left downline, it returns the user.
        """
        if self.has_right_downline():
            queryset = self.get_right_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )
            if limit_output:
                queryset = queryset[:limit]
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)

    def get_unmatched_downlines(self, limit=3, limit_output=False):
        """
        Returns a queryset containing the list of users having 1 or no downline on the left and right leg in
        tree order. If the user does not have a left or right downline, it returns the user.
        """
        if self.has_right_downline() or self.has_left_downline():
            queryset = self.get_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )[:limit]
            if limit_output:
                queryset = queryset[:limit]
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)


class AccountPackage(models.Model):
    name = models.CharField(_('package name'), max_length=20)
    limit = models.IntegerField(_('account limits'))
    monthly_subscription = models.DecimalField(_('monthly subscription'), decimal_places=2, max_digits=10)
    annual_subscription = models.DecimalField(_('annual subscription'), decimal_places=2, max_digits=10)
    monthly_subscription_duration = models.IntegerField(_('monthly subscription duration'))
    annual_subscription_duration = models.IntegerField(_('annual subscription duration'))
    photo = models.FileField(upload_to='account_package/', blank=True, null=True)
    rank = models.IntegerField(_('rank'), default=0)
    is_default = models.BooleanField(_('is default'), default=False)

    def __str__(self):
        return '%(name)s Limit: %(limit)s' % {'name': self.name.upper(), 'limit': self.limit}


class UserAccount(models.Model):
    limit = models.IntegerField(_('account limits'), default=DEFAULT_USER_ACCOUNT_LIMIT)
    related_users = JSONField(_('related users'), blank=True, null=True)
    account_manager = models.ForeignKey(
        UserModel(), blank=True, null=True, verbose_name=_('account manager'), on_delete=models.SET_NULL
    )
    last_payment = models.DateTimeField(_('last payment'), blank=True, null=True)
    next_payment = models.DateTimeField(_('next payment'), blank=True, null=True)
    package = models.ForeignKey(AccountPackage, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(_('status'), blank=True, max_length=20)
    is_active = models.BooleanField(_('is active'), default=False)
    auto_renewal = models.BooleanField(_('auto renewal'), default=False)
    created_on = models.DateTimeField(_('created on'), default=timezone.now)

    def __str__(self):
        return '%s Limit: %s' % (self.related_users, self.limit)


class UserAccountManager:

    def __init__(self):
        self.model = UserAccount
        self.user = UserModel().objects.none()

    def add_user_to_user_account(self, user, user_account_id=None):
        self.user = user
        if self.user.user_account_id:  # Return False if the user has already been added to another user account.
            response = {
                'status': 'failure', 'message': _('This user account has already been added to a list.'),
                'instance': self.model.objects.none()
            }
            return response

        elif not user_account_id:
            # Create a new user account if the user has not been added to any account and the user_account_id is not
            # provided.
            package = None
            if user.is_admin:
                package = AccountPackage.objects.order_by('-limit')[:1].get()
            else:
                package = AccountPackage.objects.filter(is_default=True)[:1].get()
            related_users = [user.id]
            user_account = self.model.objects.create(
                is_active=True, status='active', related_users=related_users, account_manager=self.user,
                package=package,
            )

            self.user.user_account_id = user_account.id
            self.user.save()
            response = {
                'status': 'success', 'message': _('User Account added successfully.'),
                'instance': user_account
            }
            return response

        elif user_account_id:
            # But if the user has not been added to any user account and the user_account_id is provided, update the
            # list of related users. But first ensure the limits have not been reached.,
            user_account = None
            try:
                user_account = self.model.objects.get(pk=user_account_id)
            except self.model.DoesNotExist:
                response = {
                    'status': 'failure', 'message': _('Invalid user account Id supplied.'),
                    'instance': self.model.objects.none()
                }
                return response

            if user_account and len(user_account.related_users) < user_account.limit:
                related_users = user_account.related_users
                related_users.append(user.id)
                user_account.related_users = related_users
                user_account.save()
                self.user.user_account_id = user_account.id
                self.user.save()
                response = {
                    'status': 'success', 'message': _('Account added successfully.'),
                    'instance': user_account,
                }
                return response
            else:
                response = {
                    'status': 'failure', 'message': _('User not added. Account Limits reached.'),
                    'instance': self.model.objects.none()
                }
                return response

    def remove_user_from_user_account(self, user, user_account_id):
        self.user = user
        try:
            user_account = self.model.objects.get(pk=user_account_id)
        except self.model.DoesNotExist:
            return False

        if user_account:
            related_users = user_account.related_users
            try:
                related_users.remove(self.user.id)
                # if len(related_users) == 0:  # Delete the user account if it has no more related accounts.
                #     user_account.delete()
                # else:
                user_account.related_users = related_users
                user_account.save()
                self.user.user_account_id = None
                self.user.save()
            except ValueError:
                pass
            return user_account
        else:
            return False

    def get_user_account(self, user_account_id):
        # Returns an instance of a user account or empty queryset
        try:
            return self.model.objects.get(pk=user_account_id)
        except self.model.DoesNotExist:
            return self.model.objects.none()

    def get_user_account_user_list(self, user_account_id):
        # Returns a list of related_users instances e.g. [34, 30, 5, 70]

        user_account = self.get_user_account(user_account_id)
        user_list = []
        if user_account:
            related_users = user_account.related_users
            for user_id in related_users:
                try:
                    user = UserModel().objects.get(pk=user_id)
                    user_list.append(user)
                except UserModel().DoesNotExist:
                    pass
        return user_list

    def user_is_in_list(self, user_id, user_account_id):
        # Checks to ensure the given user_id is in the list of a particular user_account's related users
        user_account = self.get_user_account(user_account_id=user_account_id)
        if user_account:
            related_users = user_account.related_users
            if int(user_id) in related_users:
                return True
            else:
                return False
        else:
            return False

    def is_account_manager(self, user, user_account_id):
        """
        :param user: The user we wish to verify if he/she is an account manager.
        :param user_account_id: The user_account_id of the account we wish to check in.
        :return: True is the user is the account manager and False otherwise
        """
        user_account = self.get_user_account(user_account_id)
        if user_account:
            return user == user_account.account_manager
        else:
            return False

    def update_account_manager(self, user, user_account_id):

        user_account = self.get_user_account(user_account_id)
        if user_account:
            user_account.account_manager = user
            user_account.save()
            return user_account
        else:
            return False

    def update_subscription(self, user_account_id, package_id, subscription):
        """
        Updates the user's subscription to a package.
        :param user_account_id: The user account id of the account to be updated.
        :param package_id: The package_id of the package chosen
        :param subscription: the subscription type (monthly or annually)
        :return: An instance of the  user_account or False
        """
        package = None
        user_account = None
        subscription_type = UserAccountSubscriptionType()
        subscription_duration = 0
        subscription_amount = 0.00
        try:
            package = AccountPackage.objects.get(pk=package_id)
        except AccountPackage.DoesNotExist:
            return AccountPackage.objects.none()

        user_account = self.get_user_account(user_account_id)
        if user_account:
            if subscription == subscription_type.monthly():
                subscription_duration = package.monthly_subscription_duration
                subscription_amount = package.monthly_subscription
            elif subscription == subscription_type.annually():
                subscription_duration = package.annual_subscription_duration
                subscription_amount = package.annual_subscription

            user_account.last_payment = timezone.now()
            user_account.next_payment = (
                user_account.next_payment + datetime.timedelta(days=subscription_duration) if user_account.next_payment
                else timezone.now() + datetime.timedelta(days=subscription_duration)
            )
            user_account.package = package
            user_account.amount = subscription_amount
            user_account.limit = package.limit
            user_account.is_active = True
            user_account.save()
            self.resize_user_account_related_users(user_account=user_account, size_limit=package.limit)
            return user_account
        else:
            return False

    def resize_user_account_related_users(self, user_account, size_limit):
        """
        Resizes a user_account related user's len. Ensures the account manager is not removed from the list.

        :param user_account:
        :param size_limit: The maximum size of the related_user list.
        :return: And instance of user_account
        """
        related_user_list = user_account.related_users
        if len(related_user_list) < int(size_limit):
            return user_account
        else:
            account_manager = user_account.account_manager
            account_manager_id = 0 if not account_manager else account_manager.id
            new_related_user_list = related_user_list[:size_limit]
            if account_manager_id not in new_related_user_list:
                del new_related_user_list[len(new_related_user_list)-1]
                new_related_user_list.append(account_manager_id)
            user_account.related_users = new_related_user_list
            user_account.save()
            return user_account

    def deactivate_subscription(self, user_account_id):
        user_account = self.get_user_account(user_account_id)
        if user_account:
            user_account.is_active = False
            user_account.save()
            return user_account
        else:
            return False

    def deactivate_over_due_subscriptions(self):
        # Deactivates all accounts with past due subscriptions
        user_accounts = self.model.objects.filter(next_payment__lte=timezone.now(), package__isnull=False)
        if user_accounts:
            for user_account in user_accounts:
                if user_account.account_manager and user_account.account_manager.is_admin:
                    pass
                else:
                    self.deactivate_subscription(user_account_id=user_account.id)
        return user_accounts

    def get_user_accounts_to_send_subscription_reminder(self):
        # Returns the list of user accounts to which the subscription is due in 3 days or less
        queryset = self.model.objects.filter(
            next_payment__isnull=False, package__isnull=False
        ).annotate(
            duration=ExpressionWrapper(F('next_payment') - timezone.now(), DurationField())
        ).annotate(
            day=Extract('duration', 'day'), hour=Extract('duration', 'hour'), minute=Extract('duration', 'minute')
        ).filter(
            day__gt=-1, day__lte=3
        )
        return queryset

    def get_user_account_packages(self):
        return AccountPackage.objects.filter(is_default=False).order_by('rank')

    def get_package(self, package_id):
        try:
            return AccountPackage.objects.get(pk=package_id)
        except AccountPackage.DoesNotExist:
            return AccountPackage.objects.none()
