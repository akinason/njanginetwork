from .models import NjangiTree, LevelModel, NjangiTreeSide, NJANGI_LEVELS, LEVEL_CONTRIBUTIONS, \
    NSP_CONTRIBUTION_PROCESSING_FEE_RATES, WALLET_CONTRIBUTION_PROCESSING_FEE_RATE, NSP, \
    NSP_CONTRIBUTION_PROCESSING_FEE_RATE, WALLET_CONTRIBUTION_PROCESSING_FEE_RATES
from django.contrib.auth import get_user_model as UserModel
from django.db.models import Q
from main.utils import get_admin_users
from django.utils import timezone
import random
from mailer import services as mailer_services

tree_side = NjangiTreeSide()
_nsp = NSP()

def _create_njangi_tree_node(user, sponsor, sponsor_node, side):
    tree_node = NjangiTree.objects.create(
        user=user,
        side=side,
        parent_user=sponsor,
        parent=sponsor_node,
    )
    return tree_node


def add_user_to_njangi_tree(user, side=None, sponsor=None, sponsor_pk=None):
    # Adds the user to the Njangi Tree. It uses sponsor_pk to get a specific sponsor or user.sponsor otherwise.
    if sponsor_pk and not sponsor:
        try:
            sponsor = UserModel().objects.get(pk=sponsor_pk)
        except (KeyError, UserModel().DoesNotExist):
            sponsor = UserModel().objects.get(pk=user.sponsor)

    if user.is_admin:
        # add as a root node.
        tree_node = NjangiTree.objects.create(user=user)
        return tree_node
    else:
        # The Njangi Tree Node for the sponsor.
        sponsor_node = NjangiTree.objects.filter(user=sponsor).get()

        if sponsor_node.has_left_downline() and not sponsor_node.has_right_downline():
            # Add the new user to the right leg regardless of the value of 'side'
            return _create_njangi_tree_node(
                user=user, sponsor=sponsor, sponsor_node=sponsor_node, side=tree_side.right()
            )
        elif not sponsor_node.has_left_downline() and sponsor_node.has_right_downline():
            # Add the new user to the left regardless of the value of 'side'
            return _create_njangi_tree_node(
                user=user, sponsor=sponsor, sponsor_node=sponsor_node, side=tree_side.left()
            )
        elif sponsor_node.is_leaf_node():
            # Verify if a side was provided and matches the standards then position the user to
            # corresponding side else position to the left.
            if side and side in [tree_side.left(), tree_side.right()]:
                return _create_njangi_tree_node(
                    user=user, sponsor=sponsor, sponsor_node=sponsor_node, side=side
                )
            else:
                return _create_njangi_tree_node(
                    user=user, sponsor=sponsor, sponsor_node=sponsor_node, side=tree_side.left()
                )
        elif sponsor_node.has_right_downline() and sponsor_node.has_left_downline():
            # Then get a queryset of the downlines with unmatched downlines and position the new user
            queryset = sponsor_node.get_unmatched_downlines()
            id_list = []
            for node in queryset:
                id_list.append(node.pk)
            random.shuffle(id_list)
            pk = id_list[0]
            node = queryset.filter(pk=pk).get()

            if node.has_left_downline() and not node.has_right_downline():
                # Add the new user to the right leg regardless of the value of 'side'
                return _create_njangi_tree_node(
                    user=user, sponsor=node.user, sponsor_node=node, side=tree_side.right()
                )
            elif not node.has_left_downline() and node.has_right_downline():
                # Add the new user to the left leg regardless of the value of 'side'
                return _create_njangi_tree_node(
                    user=user, sponsor=node.user, sponsor_node=node, side=tree_side.left()
                )
            elif node.is_leaf_node():
                # Verify if a side was provided and matches the standards then position the user to
                # corresponding side else position to the left.
                if side and side in [tree_side.left(), tree_side.right()]:
                    return _create_njangi_tree_node(
                        user=user, sponsor=node.user, sponsor_node=node, side=side
                    )
                else:
                    return _create_njangi_tree_node(
                        user=user, sponsor=node.user, sponsor_node=node, side=tree_side.left()
                    )


def create_user_levels(user):
    for level in NJANGI_LEVELS:
        obj = LevelModel.objects.create(user=user, level=level, is_active=False)
        if user.is_admin:
            obj.is_active = True
            obj.save()
    return True


def get_upline_to_pay_upgrade_contribution(user_id, level):
    """
    :param user_id: The user_id of the user who wants to upgrade.
    :param level: The level to which the contribution has to go.
    :return: The user who has to receive the contribution or False if other wise.

    NB: Users who are not active in the level and those not active at all are ignored.
    """
    try:
        user = UserModel().objects.get(pk=user_id)
        _level = int(level)
        if user.is_admin:
            return user
        else:
            tree_node = NjangiTree.objects.filter(user=user).get()
            ancestors = tree_node.get_ancestors(ascending=True)[:_level]  # Limit the queryset to the level.
            ancestor_count = ancestors.count()
            ancestor_dic = ancestors.values('id', 'user')  # Get a dictionary of the ancestors (id and user_id only).
            # step 1: Get the ancestor node to whom the contribution has to go to
            #         even if the user is inactive.
            node = {}
            if ancestor_count <= _level:
                node = ancestor_dic[ancestor_count-1]
            elif ancestor_count > _level:
                node = ancestor_dic[_level-1]

            user_id = node['user']  # Extract the user_id from the dictionary. This is the user to whom the donation
                                    # is suppose to go to
            # Step 2: Check if the user(recipient) is active.
            try:
                recipient = UserModel().objects.get(pk=user_id)
                # Check if the recipient is active in the current level and whether he is active at all + user level >=
                # current level.
                if recipient_can_receive_level_contribution(
                        recipient=recipient, level=level, amount=get_level_contribution_amount(level)
                ):
                    return recipient
                else:
                    # If the recipient is not active, then the contribution should go to anyone on his upline who is
                    # active as a user and active in the level.
                    recipient_node = NjangiTree.objects.filter(user=recipient).get()
                    recipient_node_ancestors = recipient_node.get_ancestors(ascending=True).filter(
                        Q(user__is_active=True, user__level__gte=_level) | Q(user__is_admin=True)
                    )
                    # Loop through the list of recipient's ancestors and return the ancestor who is active in the level.
                    # NB: This will end up returning the admin if it gets to that level. The admin user is always active
                    for ancestor_node in recipient_node_ancestors:
                        ancestor_user = ancestor_node.user
                        if recipient_can_receive_level_contribution(
                                recipient=ancestor_user, level=level, amount=get_level_contribution_amount(level)
                        ):
                            return ancestor_user
                        else:
                            pass
            except UserModel().DoesNotExist:
                return get_admin_users()[0]
            except LevelModel.DoesNotExist:
                return get_admin_users()[0]
            except NjangiTree.DoesNotExist:
                return get_admin_users()[0]
    except UserModel().DoesNotExist:
        return get_admin_users()[0]
    except NjangiTree.DoesNotExist:
        return get_admin_users()[0]
    except IndexError:
        return get_admin_users()[0]


def get_level_contribution_amount(level):
    # Returns the amount to contribute for a particular level
    if int(level) in NJANGI_LEVELS:
        return LEVEL_CONTRIBUTIONS[int(level)]
    else:
        return 5000


def recipient_can_receive_level_contribution(recipient, level, amount):
    """
    Returns True if the recipient(user) can receive contribution or False otherwise.
    Also deactivates the user if he/she is not able to receive contribution.
    It by-passes users who have automatic contribution set to True and who have
    sufficient balance in either of their wallet.
    """
    _level = int(level)
    if recipient.is_admin:
        return True
    else:
        if not recipient.is_active:
            return False
        elif recipient.level < _level:
            return False
        else:
            try:
                level_model = LevelModel.objects.filter(user=recipient, level=_level).get()
                if not level_model.is_active:
                    return False
                elif not level_model.next_payment:
                    return False
                elif level_model.next_payment < timezone.now():
                    # if the user has allow_automatic_contribution set on, check if he/she has sufficient balance.
                    if recipient.allow_automatic_contribution:
                        from purse.models import WalletManager
                        from main.core import NSP
                        nsp = NSP()
                        wallet = WalletManager()
                        mtn_balance = wallet.balance(user=recipient, nsp=nsp.mtn())
                        orange_balance = wallet.balance(user=recipient, nsp=nsp.orange())
                        if mtn_balance > amount or orange_balance > amount:
                            return True
                        else:
                            level_model.is_active = False
                            level_model.save()
                            mailer_services.send_level_deactivation_email.delay(
                                user_id=recipient.id, level=_level, amount=amount
                            )
                            mailer_services.send_level_deactivation_sms.delay(
                                user_id=recipient.id, level=_level, amount=amount
                            )
                            return False
                    else:
                        # if this happens, deactivate the user at that level and return False
                        level_model.is_active = False
                        level_model.save()
                        mailer_services.send_level_deactivation_email.delay(
                            user_id=recipient.id, level=_level, amount=amount
                        )
                        mailer_services.send_level_deactivation_sms.delay(
                            user_id=recipient.id, level=_level, amount=amount
                        )
                        return False
                else:
                    return True
            except LevelModel.DoesNotExist:
                return False


def get_processing_fee_rate(level, nsp):
    rate = NSP_CONTRIBUTION_PROCESSING_FEE_RATE
    try:
        if nsp == _nsp.orange() or nsp == _nsp.mtn():
            rate = NSP_CONTRIBUTION_PROCESSING_FEE_RATES[int(level)]
        else:
            rate = WALLET_CONTRIBUTION_PROCESSING_FEE_RATES[int(level)]
        return rate
    except KeyError:
        return rate
