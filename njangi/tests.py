from django.test import TestCase, RequestFactory
from njangi.models import LevelModel, NjangiTree
from django.contrib.auth import get_user_model
from main.tests import create_test_users
from njangi.tasks import process_payout, process_contribution, process_wallet_load
from purse.models import WalletManager, WalletTransDescription, WalletTransStatus, WalletTransMessage
from main.core import NSP

nsp_list = NSP()
UserModel = get_user_model()
trans_description = WalletTransDescription()
trans_status = WalletTransStatus()
trans_message = WalletTransMessage()


class NjangiLevelModelTest(TestCase):

    def test_njangi_tree(self):

        users = create_test_users()
        i = 0
        parent_user = get_user_model()
        parent = NjangiTree()
        for user in users:
            if i == 0:
                tree = NjangiTree.objects.create(
                    user=user,
                )
            else:
                tree = NjangiTree.objects.create(
                    user=user,
                    parent_user=parent_user,
                    side=NjangiTree.tree_side.left(),
                    parent=parent
                )

            parent_user = user
            parent = tree
            i = + 1
        self.assertEqual(NjangiTree.objects.all().count(), 8)

        # Test for a tree node with user 'kinason' which is a root node.
        tree_node = NjangiTree.objects.filter(user__username='kinason').get()
        self.assertEqual(tree_node.is_leaf_node(), False)
        self.assertEqual(tree_node.has_left_downline(), True)
        self.assertEqual(tree_node.has_right_downline(), False)
        self.assertEqual(tree_node.is_left_downline(), False)
        self.assertEqual(tree_node.is_root_node(), True)
        self.assertEqual(tree_node.has_left_downline(), True)
        self.assertEqual(tree_node.has_right_downline(), False)
        left_downline = tree_node.get_left_downline()
        self.assertEqual(left_downline.user.username, 'fai')
        left_downlines = tree_node.get_left_downlines()
        self.assertEqual(left_downlines.count(), 7)
        self.assertEqual(tree_node.get_left_downline_count(), 7)

        # Test for a tree node with user 'simon' which is a 3rd descendant of 'kinason'
        tree_node = NjangiTree.objects.filter(user__username='simon').get()
        self.assertEqual(tree_node.is_leaf_node(), False)
        self.assertEqual(tree_node.has_left_downline(), True)
        self.assertEqual(tree_node.has_right_downline(), False)
        self.assertEqual(tree_node.is_left_downline(), True)
        self.assertEqual(tree_node.is_root_node(), False)
        left_downline = tree_node.get_left_downline()
        self.assertEqual(left_downline.user.username, 'helen')
        left_downlines = tree_node.get_left_downlines()
        self.assertEqual(left_downlines.count(), 4)
        self.assertEqual(tree_node.get_left_downline_count(), 4)
        # print(left_downlines)
        # print(tree_node.get_left_unmatched_downlines())
        # print(tree_node.get_right_unmatched_downlines())
        # print(tree_node.get_unmatched_downlines())
        queryset = tree_node.get_unmatched_downlines()
        node = queryset[:1].get()
        # print(node.is_leaf_node)
        if not tree_node.has_right_downline():
            # print('has no right downline.')
            pass


class NjangiTasksTest(TestCase):
    # This test must be disable in production environment else it will trigger real time cash transactions.

    def setUp(self):
        self.wallet = WalletManager()
        self.users = create_test_users()
        admin_kinason = self.users[0]
        fai = self.users[1]
        admin_kinason.tel1 = '+237675397307'
        admin_kinason.tel2 = '+237695316762'
        admin_kinason.save()
        fai.tel1 = '+23767855632'
        fai.tel2 = '+23769855632'

        fai.save()
        self.admin_kinason = admin_kinason
        self.fai = fai

    def test_payout_processing_with_invalid_network_service_provider(self):
        information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
        load_response = self.wallet.load(
            user=self.admin_kinason, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
            charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
            information=information,
        )
        self.assertEqual(load_response['status'], trans_status.success())

        payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=350000, nsp='camtel')
        self.assertEqual(payment_response['message'], trans_message.insufficient_balance_message())

    def test_payout_processing_with_insufficient_balance(self):
        information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
        load_response = self.wallet.load(
            user=self.admin_kinason, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
            charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
            information=information,
        )
        self.assertEqual(load_response['status'], trans_status.success())

        payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=350000, nsp=nsp_list.mtn())
        self.assertEqual(payment_response['message'], trans_message.insufficient_balance_message())

    def test_payout_processing_with_mtn_unverified_tel_number(self):

        information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
        load_response = self.wallet.load(
            user=self.admin_kinason, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
            charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
            information=information,
        )
        self.assertEqual(load_response['status'], trans_status.success())

        payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.mtn())
        self.assertEqual(payment_response['status'], trans_status.pending())

    # def test_payout_processing_with_mtn_verified_tel_number_and_failed_api_response(self):
    #     information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
    #     self.admin_kinason.tel1_is_verified = True
    #     self.admin_kinason.save()
    #     load_response = self.wallet.load(
    #         user=self.admin_kinason, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
    #         charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
    #         information=information,
    #     )
    #     self.assertEqual(load_response['status'], trans_status.success())
    #     payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.mtn())
    #     self.assertEqual(payment_response['status'], trans_status.failed())

    # def test_payout_processing_with_mtn_verified_tel_number_and_success_api_response(self):
    #     information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
    #     self.admin_kinason.tel1_is_verified = True
    #     self.admin_kinason.save()
    #     load_response = self.wallet.load(
    #         user=self.admin_kinason, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
    #         charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
    #         information=information,
    #     )
    #     self.assertEqual(load_response['status'], trans_status.success())
    #     payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.mtn())
    #     self.assertEqual(payment_response['status'], trans_status.success())

    # **********************************************************************************
    # Testing with ORANGE MONEY
    # **********************************************************************************

    def test_payout_processing_with_orange_unverified_tel_number(self):

        information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
        load_response = self.wallet.load(
            user=self.admin_kinason, amount=50000, nsp=nsp_list.orange(), description=trans_description.wallet_load(),
            charge=100, tel=self.admin_kinason.tel2.national_number, thirdparty_reference=2500251,
            information=information,
        )
        self.assertEqual(load_response['status'], trans_status.success())

        payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.orange())
        self.assertEqual(payment_response['status'], trans_status.pending())

    # def test_payout_processing_with_orange_verified_tel_number_and_failed_api_response(self):
    #
    #     information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
    #     self.admin_kinason.tel2_is_verified = True
    #     self.admin_kinason.save()
    #     load_response = self.wallet.load(
    #         user=self.admin_kinason, amount=50000, nsp=nsp_list.orange(), description=trans_description.wallet_load(),
    #         charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
    #         information=information,
    #     )
    #     self.assertEqual(load_response['status'], trans_status.success())
    #     payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.orange())
    #     self.assertEqual(payment_response['status'], trans_status.failed())

    def test_payout_processing_with_orange_verified_tel_number_and_success_api_response(self):

        information = str(trans_description.wallet_load()) + ' through ' + str(nsp_list.mtn().upper())
        self.admin_kinason.tel2_is_verified = True
        self.admin_kinason.save()
        load_response = self.wallet.load(
            user=self.admin_kinason, amount=50000, nsp=nsp_list.orange(), description=trans_description.wallet_load(),
            charge=100, tel=self.admin_kinason.tel1.national_number, thirdparty_reference=2500251,
            information=information,
        )
        self.assertEqual(load_response['status'], trans_status.success())
        payment_response = process_payout(recipient_id=self.admin_kinason.id, amount=35000, nsp=nsp_list.orange())
        self.assertEqual(payment_response['status'], trans_status.success())

    def test_process_contribution_with_invalid_nsp(self):
        user = self.fai
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = 'camtel'
        sender_tel = user.tel1.national_number
        processing_fee = 0.00

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.failed())

    def test_process_contribution_with_with_mtn_as_nsp(self):
        user = self.fai
        user.tel2_is_verified = True
        user.tel1_is_verified = True
        user.save()
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.mtn()
        sender_tel = user.tel1.national_number
        processing_fee = 0.00

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.success())

    def test_process_contribution_with_with_orange_as_nsp(self):
        user = self.fai
        user.tel2_is_verified = True
        user.tel1_is_verified = True
        user.save()
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.orange()
        sender_tel = user.tel2.national_number
        processing_fee = 0.00

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.success())

    def test_process_contribution_with_with_orange_wallet_as_nsp_and_insufficient_funds(self):
        user = self.fai
        user.tel2_is_verified = True
        user.tel1_is_verified = True
        user.save()
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.orange_wallet()
        sender_tel = user.tel1.national_number
        processing_fee = 0.00

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.pending())

    def test_process_contribution_with_with_mtn_wallet_as_nsp_and_insufficient_balance(self):
        user = self.fai
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.mtn_wallet()
        sender_tel = user.tel1
        processing_fee = 0.00

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.pending())

    def test_process_contribution_with_with_mtn_wallet_as_nsp(self):
        user = self.fai
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.mtn_wallet()
        sender_tel = user.tel1.national_number
        processing_fee = 0.00
        information = str(trans_description.wallet_load()) + ' through ' + str(nsp.upper())

        load_response = self.wallet.load(
            user=user, amount=50000, nsp=nsp_list.mtn(), description=trans_description.wallet_load(),
            charge=100, tel=user.tel1.national_number, thirdparty_reference=2500251, information=information,
            )

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.success())

    def test_process_contribution_with_orange_wallet_as_nsp(self):
        user = self.fai
        recipient = self.admin_kinason
        level = 1
        amount = 2000
        nsp = nsp_list.orange_wallet()
        sender_tel = user.tel1.national_number
        processing_fee = 0.00
        information = str(trans_description.wallet_load()) + ' through ' + str(nsp.upper())

        load_response = self.wallet.load(
            user=user, amount=50000, nsp=nsp_list.orange(), description=trans_description.wallet_load(),
            charge=100, tel=user.tel1.national_number, thirdparty_reference=2500251, information=information,
        )

        response = process_contribution(
            user_id=user.id, recipient_id=recipient.id, level=level, amount=amount, nsp=nsp, sender_tel=sender_tel,
            processing_fee=processing_fee, thirdparty_reference=25200
        )
        self.assertEqual(response['status'], trans_status.success())

    def test_wallet_load_to_mtn_with_verified_tel_number(self):
        """This test will fail if the API request is inactive or returns a Failure Status.
            In order to test its success, edit the return status at: "purse.services.request_momo_deposit "
            to return a status of "Success"
        """
        user = self.fai
        user.tel1_is_verified = True
        user.save()
        amount = 25600
        charge = 0.00
        response = process_wallet_load(user_id=user.id, amount=amount, nsp=nsp_list.mtn(), charge=charge)
        self.assertEqual(response['status'], trans_status.success())

    def test_wallet_load_to_orange_with_verified_tel_number(self):
        """This test will fail if the API request is inactive or returns a Failure Status.
            In order to test its success, edit the return status at: "purse.services.request_orange_money_deposit "
            to return a status of "Success"
        """
        user = self.fai
        user.tel2 = '+237699553687'
        user.tel2_is_verified = True
        user.save()
        amount = 25600
        charge = 0.00
        response = process_wallet_load(user_id=user.id, amount=amount, nsp=nsp_list.orange(), charge=charge)
        self.assertEqual(response['status'], trans_status.success())

    def test_wallet_load_with_invalid_nsp(self):
        user = self.fai
        amount = 25600
        charge = 0.00
        response = process_wallet_load(user_id=user.id, amount=amount, nsp=nsp_list.mtn_wallet(), charge=charge)
        self.assertEqual(response['status'], trans_status.failed())

    def test_wallet_load_with_valid_nsp_and_unverified_tel1(self):
        user = self.fai
        amount = 25600
        charge = 0.00
        response = process_wallet_load(user_id=user.id, amount=amount, nsp=nsp_list.mtn(), charge=charge)
        self.assertEqual(response['status'], trans_status.failed())
