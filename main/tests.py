from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model as UserModel
from django.urls import reverse
from main.views import IndexView, SignupView, LoginView, LogoutView
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from main.utils import add_admin_sponsor_id_to_session, add_sponsor_id_to_session



test_users = [
    {'username': 'kinason', 'first_name': 'awa', 'last_name': 'mokom', 'gender': 'male', 'is_admin': True, 'sponsor': 1},
    {'username': 'fai', 'first_name': 'fai', 'last_name': 'marcel', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'khan', 'first_name': 'khan', 'last_name': 'quini', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'simon', 'first_name': 'simon', 'last_name': 'peter', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'helen', 'first_name': 'helen', 'last_name': 'amba', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'mark', 'first_name': 'mark', 'last_name': 'vivian', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'peter', 'first_name': 'peter', 'last_name': 'nduku', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
    {'username': 'musa', 'first_name': 'musa', 'last_name': 'abdou', 'gender': 'male', 'is_admin': False, 'sponsor': 1},
]


def create_test_users():
    sponsor_id = 1
    users = []
    for test_user in test_users:
        user, created = UserModel().objects.get_or_create(
            username=test_user['username'],
            first_name=test_user['first_name'],
            last_name=test_user['last_name'],
            gender=test_user['gender'],
            is_admin=test_user['is_admin'],
            sponsor=sponsor_id
        )
        user.set_password('123456s')
        users.append(user)
        sponsor_id = user.id
    return users


class UserModelTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

    def test_insert_tests_user_data(self):
        """
        Insert test user records to be used in running the test. Here we insert just an admin user.
        """

        kinason = UserModel().objects.create(username='kinason', first_name='awa', last_name='mokom',
                            gender='male', tel1='675397307', sponsor=1)
        kinason.is_admin = True
        kinason.set_password('scoolings')
        kinason.set_unique_random_tel1_code()
        kinason.set_unique_random_tel2_code()
        kinason.set_unique_random_tel3_code()
        kinason.set_unique_random_sponsor_id()
        kinason.save()
        user = UserModel().objects.get(username='kinason')
        self.assertEqual(user.first_name, 'awa')


class IndexViewTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        user = UserModel().objects.create_user(username='kinason', first_name='awa', last_name='mokom',
                                               gender='male', tel1='675397307', sponsor=1)
        user.is_admin = True
        user.set_password('123456s')
        user.set_unique_random_sponsor_id()
        user.save()
        self.user = user

    def test_index_view(self):
        # Create an instance of a GET request.
        request = self.factory.get(reverse('main:index'))

        # Recall that middleware are not supported. Session and authentication attributes must be supplied by the
        # test itself if required for the view to function properly.
        # https: // docs.djangoproject.com / en / 2.0 / topics / testing / advanced /

        session = self.client.session
        session.save()
        request.session = session
        request.user = self.user

        response = IndexView.as_view()(request)
        # Ensure the sponsor_id was added on GET Request of the IndexView
        self.assertTrue(request.user)
        self.assertIs(request.user.username, 'kinason')
        self.assertTrue(request.session['sponsor_id'])
        self.assertEqual(response.status_code, 200)


class SignupViewTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        user = UserModel().objects.create_user(username='kinason', first_name='awa', last_name='mokom',
                                               gender='male', tel1='675397307', sponsor=1)
        user.is_admin = True
        user.set_password('123456s')
        user.set_unique_random_sponsor_id()
        user.save()
        self.user = user

    def test_signup(self):

        # Create an instance of a POST request.
        request = self.factory.post(
            reverse('main:signup'),
            {
                'username': 'fai', 'first_name': 'Dufola', 'last_name': 'Marcel', 'password': '123456sss',
                'confirm_password': '123456sss', 'gender': 'male', 'tel1': '67552251', 'sponsor': self.user.id
            }
        )

        # Recall that middleware are not supported. Session and authentication attributes must be supplied by the
        # test itself if required for the view to function properly.
        # https: // docs.djangoproject.com / en / 2.0 / topics / testing / advanced /

        request.user = self.user

        session = self.client.session
        session.save()
        request.session = session

        response = SignupView.as_view()(request)
        self.assertTrue(request.user)
        self.assertEqual(response.status_code, 200)


class LoginAndOutViewTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        user = UserModel().objects.create_user(username='kinason', first_name='awa', last_name='mokom',
                                             gender='male', tel1='675397307', sponsor=1)
        user.is_admin = True
        user.set_password('123456s')
        user.set_unique_random_sponsor_id()
        user.save()
        self.user = user

    def test_login(self):

        request = self.factory.post(reverse('main:login'), {'username': 'kinason', 'password': '123456s'})
        request.user = self.user
        session = self.client.session
        session.save()
        request.session = session
        response = LoginView.as_view()(request)

        self.assertTrue(response.status_code, 302)


class UtilsTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        user = UserModel().objects.create_user(username='kinason', first_name='awa', last_name='mokom',
                                             gender='male', tel1='675397307', sponsor=1)
        user.is_admin = True
        user.set_password('123456s')
        user.set_unique_random_sponsor_id()
        user.save()
        self.user = user

    def test_add_sponsor_id_to_session(self):
        request = HttpRequest()
        request.user = self.user
        session = self.client.session
        session.save()
        request.session = session
        response = add_sponsor_id_to_session(request)
        self.assertEqual(response, self.user.sponsor_id)

    def test_add_admin_sponsor_id_to_session(self):
        request = HttpRequest()
        request.user = self.user
        session = self.client.session
        session.save()
        request.session = session
        response = add_admin_sponsor_id_to_session(request)
        self.assertEqual(int(response), int(self.user.sponsor_id))

    def test_create_tests_users(self):
        users = create_test_users()
        print(users)
        self.assertTrue(users)
