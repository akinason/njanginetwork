from django.db import models
from django.db.models import Q, Count
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth import get_user_model as UserModel
from django.utils.translation import ugettext_lazy as _
from main.core import NSP
from main.models import TEL_MAX_LENGTH
from django.utils import timezone

NSP_CONTRIBUTION_PROCESSING_FEE_RATE = 0.01
NSP_WALLET_LOAD_PROCESSING_FEE_RATE = 0.0
NSP_WALLET_WITHDRAWAL_PROCESSING_FEE_RATE = 0
WALLET_CONTRIBUTION_PROCESSING_FEE_RATE = 0.01

NSP_CONTRIBUTION_PROCESSING_FEE_RATES = {
    1: 0.02,
    2: 0.015,
    3: 0.02,
    4: 0.02,
    5: 0.02,
    6: 0.02,
}

WALLET_CONTRIBUTION_PROCESSING_FEE_RATES = {
    1: 0.02,
    2: 0.015,
    3: 0.02,
    4: 0.02,
    5: 0.02,
    6: 0.02,
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

    def get_downlines(self):
        """
        Creates a QuerySet containing descendants of the user instance, in tree order.
        If include_self is True, the QuerySet will also include the model instance itself.
        Raises a ValueError if the instance isn’t saved already.
        """
        return super(NjangiTree, self).get_descendants(include_self=False)

    def get_left_downlines(self):
        """
        Creates a QuerySet containing descendants of the user's left side or left leg, in tree order.
        Raises a ValueError if the instance isn’t saved already.
        """
        if self.has_left_downline():
            downline = self.get_left_downline()
            return downline.get_descendants(include_self=True)
        else:
            return NjangiTree.objects.none()

    def get_right_downlines(self):
        """
        Creates a QuerySet containing descendants of the user's left side or left leg, in tree order.
        Raises a ValueError if the instance isn’t saved already.
        """
        if self.has_right_downline():
            downline = self.get_right_downline()
            return downline.get_descendants(include_self=True)
        else:
            return NjangiTree.objects.none()

    def get_left_downline_count(self):
        """
        Returns the number of people on the left leg of the user.
        """
        if self.has_left_downline():
            return self.get_left_downlines().count()
        else:
            return 0

    def get_right_downline_count(self):
        """
        Returns the number of people on the right leg of the user or zero if the user does not have a right downline.
        """
        if self.has_right_downline():
            return self.get_right_downline().count()
        else:
            return 0

    def get_left_unmatched_downlines(self):
        """
        Returns a queryset containing the list of users having 1 or no downline on the left leg in tree order.
        If the user does not have a left downline, it returns the user.
        """
        if self.has_left_downline():
            queryset = self.get_left_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)

    def get_right_unmatched_downlines(self):
        """
        Returns a queryset containing the list of users having 1 or no downline on the right leg in tree order.
        If the user does not have a left downline, it returns the user.
        """
        if self.has_right_downline():
            queryset = self.get_right_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)

    def get_unmatched_downlines(self):
        """
        Returns a queryset containing the list of users having 1 or no downline on the left and right leg in
        tree order. If the user does not have a left or right downline, it returns the user.
        """
        if self.has_right_downline() or self.has_left_downline():
            queryset = self.get_downlines()
            queryset = queryset.annotate(children_count=Count('children')).filter(
                Q(children_count=0) | Q(children_count=1)
            )
            return queryset
        else:
            return NjangiTree.objects.filter(pk=self.pk)
