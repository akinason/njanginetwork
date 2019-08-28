import random
import decimal

from django.contrib.auth import get_user_model as UserModel
from django.db.models import Q
from django.db.utils import IntegrityError
from main.utils import get_admin_users
from django.utils import timezone

from mailer import services as mailer_services
from .models import (
    NjangiTree, LevelModel, NjangiTreeSide, RemunerationPlan, NJANGI_LEVELS, LEVEL_CONTRIBUTIONS,
    NSP_CONTRIBUTION_PROCESSING_FEE_RATES, NSP, NSP_CONTRIBUTION_PROCESSING_FEE_RATE,
    WALLET_CONTRIBUTION_PROCESSING_FEE_RATES
)

tree_side = NjangiTreeSide()
_nsp = NSP()
D = decimal.Decimal


def _create_njangi_tree_node(user, sponsor, sponsor_node, side):

    obj, created = NjangiTree.objects.get_or_create(
        user=user,
        side=side,
        parent_user=sponsor,
        parent=sponsor_node,
    )
    user.is_in_network = True
    user.save()
    return obj


def get_sponsor_node_to_place_new_user(user):
    """
    This function exist because some users signup but do not contribute. In such cases, they are not added
    to the Tree. So when a referral of theirs wants to contribute, it causes an error.

    This function then gets an upline under whose network the new user will be placed.
    :param user: The new user.
    :return: The node under whom the new user should be placed.
    """
    from main.utils import get_sponsor_using_sponsor_id

    sponsors_id = user.sponsor
    while True:
        sponsor = get_sponsor_using_sponsor_id(sponsor_id=sponsors_id)
        if sponsor.is_admin:
            return NjangiTree.objects.get(user=sponsor)
        elif sponsor.is_in_network:
            return NjangiTree.objects.get(user=sponsor)
        sponsors_id = sponsor.sponsor


def add_user_to_njangi_tree(user, side=None, sponsor=None, sponsor_pk=None):
    # Adds the user to the Njangi Tree. It uses sponsor_pk to get a specific sponsor or user.sponsor otherwise.
    if sponsor_pk and not sponsor:
        try:
            sponsor = UserModel().objects.get(pk=sponsor_pk)
        except (KeyError, UserModel().DoesNotExist):
            sponsor = UserModel().objects.get(pk=user.sponsor)

    if user.is_admin:
        # add as a root node.
        tree_node, created = NjangiTree.objects.get_or_create(user=user)
        return tree_node
    else:
        # The Njangi Tree Node for the sponsor.
        sponsor_node = ''
        if sponsor.is_in_network:
            sponsor_node = NjangiTree.objects.filter(user=sponsor).get()
        else:
            sponsor_node = get_sponsor_node_to_place_new_user(user=user)

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
            queryset = ""
            left_downline_count = sponsor_node.get_left_downline_count()
            right_downline_count = sponsor_node.get_right_downline_count()

            if left_downline_count > right_downline_count:
                queryset = sponsor_node.get_right_unmatched_downlines(limit=3, limit_output=True)
            else:
                queryset = sponsor_node.get_left_unmatched_downlines(limit=3, limit_output=True)

            id_list = []
            for node in queryset:
                id_list.append(node.pk)
            random.shuffle(id_list)
            pk = id_list[0]
            node = NjangiTree.objects.get(pk=pk)

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
        obj, created = LevelModel.objects.get_or_create(user=user, level=level)
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
                    )[:30]
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
    try:
        return LEVEL_CONTRIBUTIONS[int(level)]
    except Exception as e:
        print(e)
        return 2000


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
                    """ We do not deactivate people again due to next payment date"""
                    # elif level_model.next_payment < timezone.now():
                    #     # if the user has allow_automatic_contribution set on, check if he/she has sufficient balance.
                    #     if recipient.allow_automatic_contribution:
                    #         from purse.models import WalletManager
                    #         from main.core import NSP
                    #         nsp = NSP()
                    #         wallet = WalletManager()
                    #         mtn_balance = wallet.balance(user=recipient, nsp=nsp.mtn())
                    #         orange_balance = wallet.balance(user=recipient, nsp=nsp.orange())
                    #         if mtn_balance > amount or orange_balance > amount:
                    #             return True
                    #         else:
                    #             level_model.is_active = False
                    #             level_model.save()
                    #             mailer_services.send_level_deactivation_email.delay(
                    #                 user_id=recipient.id, level=_level, amount=amount
                    #             )
                    #             mailer_services.send_level_deactivation_sms.delay(
                    #                 user_id=recipient.id, level=_level, amount=amount
                    #             )
                    #             return False
                    #     else:
                    #         if this happens, deactivate the user at that level and return False
                    #
                    #         Update: 20-11-2018: We disallow deactivating people whose contribution is due. This time
                    #         contribution does not expire., so simply return True
                    #
                    #         level_model.is_active = False
                    #         level_model.save()
                    #         mailer_services.send_level_deactivation_email.delay(
                    #             user_id=recipient.id, level=_level, amount=amount
                    #         )
                    #         mailer_services.send_level_deactivation_sms.delay(
                    #             user_id=recipient.id, level=_level, amount=amount
                    #         )
                    #         return True
                else:
                    return True
            except LevelModel.DoesNotExist:
                return False


def get_processing_fee_rate(level, nsp):
    rate = D(NSP_CONTRIBUTION_PROCESSING_FEE_RATE)
    try:
        if nsp == _nsp.orange() or nsp == _nsp.mtn():
            rate = D(NSP_CONTRIBUTION_PROCESSING_FEE_RATES[int(level)])
        else:
            rate = D(WALLET_CONTRIBUTION_PROCESSING_FEE_RATES[int(level)])
        return rate
    except KeyError:
        return rate


def get_contribution_beneficiaries(contributor, level):
    """
    :param contributor: the user who wants to contribute
    :param level: the contribution level
    :return: a dictionary response or False

    dictionary kwargs:  level -> int
                        contributor -> user instance
                        contribution_amount -> decimal
                        recipient -> dict {user, amount}
                        company_commission -> dict {user, amount}
                        velocity_reserve -> dict {user, amount}
                        direct_commission -> dict {user, amount}
                        network_commission -> list [{user, amount}, {user, amount}]
    """
    contributor_node = NjangiTree.objects.filter(user=contributor).get()
    _level = int(level)
    beneficiaries = {'level': level, 'contributor': contributor}
    admin_user = get_admin_users()[0]
    remuneration = ""
    try:
        remuneration = RemunerationPlan.objects.get(level=level)
    except RemunerationPlan.DoesNotExist:
        return False

    recipient = {
        'user': get_upline_to_pay_upgrade_contribution(user_id=contributor.id, level=_level),
        'amount': remuneration.recipient_amount
    }
    total_commission = D(remuneration.contribution_amount) - D(remuneration.recipient_amount)
    company_commission = {'user': admin_user, 'amount': round(total_commission * D(remuneration.company_commission))}
    velocity_reserve = {'user': admin_user, 'amount': round(total_commission * D(remuneration.velocity_reserve))}

    left_user = ''
    if contributor_node.has_left_downline():
        left_user = contributor_node.get_left_downline().user
        if not left_user.is_active or not left_user.level > 0:
            left_user = admin_user
    else:
        left_user = admin_user
    right_user = ""
    if contributor_node.has_right_downline():
        right_user = contributor_node.get_right_downline().user
        if not right_user.is_active or not right_user.level > 0:
            right_user = admin_user
    else:
        right_user = admin_user
    network_commission = [
        {'user': left_user, 'amount': round(total_commission * D(remuneration.network_commission) * D(0.5))},
        {'user': right_user, 'amount': round(total_commission * D(remuneration.network_commission) * D(0.5))}
    ]
    direct_commission = {
        'user': get_promoter(contributor), 'amount': round(total_commission * D(remuneration.direct_commission))
    }

    beneficiaries['contribution_amount'] = remuneration.contribution_amount
    beneficiaries['recipient'] = recipient
    beneficiaries['company_commission'] = company_commission
    beneficiaries['velocity_reserve'] = velocity_reserve
    beneficiaries['network_commission'] = network_commission
    beneficiaries['direct_commission'] = direct_commission

    return beneficiaries


def get_promoter(user):
    try:
        return UserModel().objects.get(id=user.sponsor, is_in_network=True)
    except UserModel().DoesNotExist:
        return get_admin_users()[0]
