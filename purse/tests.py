import random
import os
from django.test import TestCase
from main.tests import create_test_users
from purse.models import WalletTransStatus, WalletTransDescription, WalletManager
from django.contrib.auth import get_user_model
from njanginetwork import settings
from main.core import NSP
from django.utils import timezone

UserModel = get_user_model()


class WalletManagerTest(TestCase):

    def setUp(self):
        self.users = create_test_users()
        self.charge_list = [0, 100, 200, 50, 10]
        self.amount_list = [2000, 3000, 1500, 25000, 4500]
        nsp = NSP()
        self.nsp_list = [nsp.orange(), nsp.mtn()]
        self.wallet = WalletManager()
        self.trans_status = WalletTransStatus()
        self.trans_description = WalletTransDescription()
        # Create test entries for the WalletModel

    def test_wallet_balance(self):
        user = self.users[0]
        self.assertEqual(self.wallet.balance(user, nsp=self.nsp_list[0]), 0)
        self.assertEqual(self.wallet.balance(user, nsp=self.nsp_list[1]), 0)

    def test_wallet_load(self):
        for user in self.users:
            random.shuffle(self.amount_list)
            amount = self.amount_list[0]
            random.shuffle(self.charge_list)
            charge = self.charge_list[0]
            random.shuffle(self.nsp_list)
            nsp = self.nsp_list[0]
            response = self.wallet.load(
                user=user, amount=amount, nsp=nsp, charge=charge, tel=675397307, thirdparty_reference=201250001,
                description=self.trans_description.wallet_load()
            )
            status = response['status']
            self.assertEqual(status, self.trans_status.success())

    def test_wallet_load_a_thousand_transactions(self):
            file = open(os.path.join(settings.BASE_DIR, 'tests.txt'), 'w')
            file.write('test_wallet_load_a_thousand_transactions. \n')
            for n in range(1, 10):  # 8 users in the list times 100 = 800 Loops
                for user in self.users:
                    random.shuffle(self.amount_list)
                    amount = self.amount_list[0]
                    random.shuffle(self.charge_list)
                    charge = self.charge_list[0]
                    random.shuffle(self.nsp_list)
                    nsp = self.nsp_list[0]
                    response = self.wallet.load(
                        user=user, amount=amount, nsp=nsp, charge=charge, tel=675397307, thirdparty_reference=201250001,
                        description=self.trans_description.wallet_load()
                    )
                    status = response['status']

                    if status == self.trans_status.success():
                        reference = response['transactionId']
                        file.write(str(reference))
                        file.write('\n')
                    else:
                        # print(str(n) + ' | ' + response['status'] + ' | ' + response['message'])
                        pass

                    self.assertEqual(status, self.trans_status.success())
            file.close()

    def test_wallet_pay_a_thousand_transactions(self):
            file = open(os.path.join(settings.BASE_DIR, 'tests.txt'), 'w')
            file.write('test_wallet_pay_a_thousand_transactions. \n')
            for n in range(1, 2):  # 8 users in the list times 100 = 800 Loops
                for user in self.users:
                    random.shuffle(self.amount_list)
                    amount = self.amount_list[0]
                    random.shuffle(self.charge_list)
                    charge = self.charge_list[0]
                    random.shuffle(self.nsp_list)
                    nsp = self.nsp_list[0]

                    # Use random figures to fund the accounts.
                    response = self.wallet.load(
                        user=user, amount=amount, nsp=nsp, charge=charge, tel=675397307, thirdparty_reference=201250001,
                        description=self.trans_description.wallet_load()
                    )

                    # Use random figures to withdraw from the accounts.
                    random.shuffle(self.amount_list)
                    amount = self.amount_list[0]
                    random.shuffle(self.charge_list)
                    charge = self.charge_list[0]
                    random.shuffle(self.nsp_list)
                    response = self.wallet.pay(
                        user=user, amount=amount, nsp=nsp, charge=charge, tel=675397307, thirdparty_reference=201250001,
                        description=self.trans_description.wallet_load()
                    )
                    status = response['status']

                    if status == self.trans_status.success():
                        reference = response['transactionId']
                        # file.write(str(reference) + '\n')
                    else:
                        res = str(n) + ' | ' + str(response['status']) + ' | ' + str(response['message'])
                        file.write(res + '\n')
                    # self.assertEqual(status, self.trans_status.success())
            file.close()

    def test_wallet_contribute(self):
        sender = self.users[0]
        recipient = self.users[1]
        sender_amount = 4000.00
        recipient_amount = 3900.00
        sender_charge = 150.00
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 675397307
        recipient_tel = 67558866
        information = 'Level 2 contribution.'
        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        # Fund the user's wallet.
        load_response = self.wallet.load(
            user=sender, amount=5000, nsp=self.nsp_list[0], charge=0, tel=sender_tel, thirdparty_reference=201250001,
            description=self.trans_description.wallet_load()
        )

        self.assertEqual(load_response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(load_response) + '\n')

        response = self.wallet.contribute(
            sender=sender, recipient=recipient, sender_amount=sender_amount, recipient_amount=recipient_amount,
            nsp=self.nsp_list[0], sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=sender_charge,
            recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference, information=information,
        )

        self.assertEqual(response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_contribution_with_wrong_tel_length(self):
        sender = self.users[0]
        recipient = self.users[1]
        sender_amount = 4000.00
        recipient_amount = 3900.00
        sender_charge = 150.00
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 67397307  # Wrong Tel length
        recipient_tel = 67558866025
        information = 'Level 2 contribution.'
        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        # Fund the user's wallet.
        load_response = self.wallet.load(
            user=sender, amount=5000, nsp=self.nsp_list[0], charge=0, tel=sender_tel, thirdparty_reference=201250001,
            description=self.trans_description.wallet_load()
        )
        self.assertEqual(load_response['status'], self.trans_status.success())

        file.write(str(timezone.now()) + '\n')
        file.write(str(load_response) + '\n')

        response = self.wallet.contribute(
            sender=sender, recipient=recipient, sender_amount=sender_amount, recipient_amount=recipient_amount,
            nsp=self.nsp_list[0], sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=sender_charge,
            recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference, information=information,
        )
        self.assertEqual(response['status'], self.trans_status.failed())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_load_and_contribute(self):

        sender = self.users[0]
        recipient = self.users[1]
        loading_amount = 6000.00
        contribution_amount = 4500
        recipient_amount = 3900.00
        loading_charge = 150.00
        contribution_charge = 100
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 675397307  # Wrong Tel length
        recipient_tel = 675588667
        information = 'Level 2 contribution.'

        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        response = self.wallet.load_and_contribute(
            user=sender, recipient=recipient, loading_amount=loading_amount, contribution_amount=contribution_amount,
            recipient_amount=recipient_amount, information=information, nsp=self.nsp_list[0],
            loading_charge=loading_charge, recipient_charge=recipient_charge, contribution_charge=contribution_charge,
            sender_tel=sender_tel, recipient_tel=recipient_tel, thirdparty_reference=thirdparty_reference
        )
        self.assertEqual(response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_load_and_contribute_with_insufficient_balance(self):

        sender = self.users[0]
        recipient = self.users[1]
        loading_amount = 4000.00
        contribution_amount = 4500
        recipient_amount = 3900.00
        loading_charge = 150.00
        contribution_charge = 100
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 675397307  # Wrong Tel length
        recipient_tel = 675588667
        information = 'Level 2 contribution.'

        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        response = self.wallet.load_and_contribute(
            user=sender, recipient=recipient, loading_amount=loading_amount, contribution_amount=contribution_amount,
            recipient_amount=recipient_amount, information=information, nsp=self.nsp_list[0],
            loading_charge=loading_charge, recipient_charge=recipient_charge, contribution_charge=contribution_charge,
            sender_tel=sender_tel, recipient_tel=recipient_tel, thirdparty_reference=thirdparty_reference
        )

        self.assertEqual(response['status'], self.trans_status.failed())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_transfer(self):
        sender = self.users[0]
        recipient = self.users[1]
        sender_amount = 4000.00
        sender_charge = 150.00
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 675397307
        recipient_tel = 67558866
        information = 'Funds transfer'
        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        # Fund the user's wallet.
        load_response = self.wallet.load(
            user=sender, amount=5000, nsp=self.nsp_list[0], charge=0, tel=sender_tel,
            thirdparty_reference=201250001,
            description=self.trans_description.wallet_load()
        )

        self.assertEqual(load_response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(load_response) + '\n')

        response = self.wallet.transfer(
            sender=sender, recipient=recipient, amount=sender_amount,
            nsp=self.nsp_list[0], sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=sender_charge,
            recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference, information=information,
        )

        self.assertEqual(response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_transfer_with_insufficient_balance(self):
        sender = self.users[0]
        recipient = self.users[1]
        sender_amount = 7000.00
        sender_charge = 150.00
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 675397307
        recipient_tel = 67558866
        information = 'Funds transfer'
        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        # Fund the user's wallet.
        load_response = self.wallet.load(
            user=sender, amount=5000, nsp=self.nsp_list[0], charge=0, tel=sender_tel,
            thirdparty_reference=201250001,
            description=self.trans_description.wallet_load()
        )

        self.assertEqual(load_response['status'], self.trans_status.success())
        file.write(str(timezone.now()) + '\n')
        file.write(str(load_response) + '\n')

        response = self.wallet.transfer(
            sender=sender, recipient=recipient, amount=sender_amount,
            nsp=self.nsp_list[0], sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=sender_charge,
            recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference, information=information,
        )

        self.assertEqual(response['status'], self.trans_status.failed())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

    def test_wallet_transfer_with_invalid_phone_numbers(self):
        sender = self.users[0]
        recipient = self.users[1]
        sender_amount = 7000.00
        sender_charge = 150.00
        recipient_charge = 100.00
        thirdparty_reference = 20153684
        sender_tel = 6753973070125225562
        recipient_tel = 6755886601225556
        information = 'Funds transfer'
        file = open(os.path.join(settings.BASE_DIR, 'purse', 'tests.txt'), 'w')

        # Fund the user's wallet.
        load_response = self.wallet.load(
            user=sender, amount=5000, nsp=self.nsp_list[0], charge=0, tel=sender_tel,
            thirdparty_reference=201250001,
            description=self.trans_description.wallet_load()
        )

        self.assertEqual(load_response['status'], self.trans_status.failed())
        file.write(str(timezone.now()) + '\n')
        file.write(str(load_response) + '\n')

        response = self.wallet.transfer(
            sender=sender, recipient=recipient, amount=sender_amount,
            nsp=self.nsp_list[0], sender_tel=sender_tel, recipient_tel=recipient_tel, sender_charge=sender_charge,
            recipient_charge=recipient_charge, thirdparty_reference=thirdparty_reference, information=information,
        )

        self.assertEqual(response['status'], self.trans_status.failed())
        file.write(str(timezone.now()) + '\n')
        file.write(str(response) + '\n')
        file.close()

