import time
import re

from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User
from oauth_provider.models import Resource, Consumer
from oauth_provider.models import Token

class BaseOAuthTestCase(TestCase):
    def setUp(self):
        username = self.username = 'jane'
        password = self.password = 'toto'
        email = self.email = 'jane@example.com'
        jane = self.jane = User.objects.create_user(username, email, password)
        resource = self.resource = Resource(name='photos', url='/oauth/photo/')
        resource.save()
        CONSUMER_KEY = self.CONSUMER_KEY = 'dpf43f3p2l4k3l03'
        CONSUMER_SECRET = self.CONSUMER_SECRET = 'kd94hf93k423kf44'
        consumer = self.consumer = Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET,
            name='printer.example.com', user=jane)
        consumer.save()

        self.callback_token = self.callback = 'http://printer.example.com/request_token_ready'
        self.callback_confirmed = True
        self.request_token_parameters = {
            'oauth_consumer_key': self.CONSUMER_KEY,
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_signature': '%s&' % self.CONSUMER_SECRET,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': 'requestnonce',
            'oauth_version': '1.0',
            'oauth_callback': self.callback,
            'scope': 'photos',  # custom argument to specify Protected Resource
        }

        self.c = Client()

    def _request_token(self):
        # The Consumer sends the following HTTP POST request to the
        # Service Provider:
        response = self.c.get("/oauth/request_token/", self.request_token_parameters)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assert_(
            re.match(r'oauth_token_secret=[^&]+&oauth_token=[^&]+&oauth_callback_confirmed=true',
                response.content
            ))
        token = self.request_token = list(Token.objects.all())[-1]
        self.assert_(token.key in response.content)
        self.assert_(token.secret in response.content)
        self.assert_(not self.request_token.is_approved)
        return response


class OAuthTestsBug10(BaseOAuthTestCase):
    """
    See https://code.welldev.org/django-oauth-plus/issue/10/malformed-callback-url-when-user-denies
    """
    def test_Request_token_request_succeeds_with_valid_request_token_parameters(self):
        response = self._request_token()
        token = self.request_token

        self.assertEqual(token.callback,
                         self.callback_token)
        self.assertEqual(
            token.callback_confirmed,
            self.callback_confirmed)

    def test_Requesting_user_authorization_fails_when_user_denies_authorization(self):
        self._request_token()
        self.c.login(username=self.username, password=self.password)
        parameters = authorization_parameters = {'oauth_token': self.request_token.key}
        response = self.c.get("/oauth/authorize/", parameters)
        self.assertEqual(
            response.status_code,
            200)

        # fake access not granted by the user (set session parameter again)
        authorization_parameters['authorize_access'] = False
        response = self.c.post("/oauth/authorize/", authorization_parameters)
        self.assertEqual(
            response.status_code,
            302)
        self.assertEqual('http://printer.example.com/request_token_ready?error=Access+not+granted+by+user.', response['Location'])
        self.c.logout()

class OAuthOutOfBoundTests(BaseOAuthTestCase):
    def test_Requesting_user_authorization_succeeds_when_oob(self):
        self.request_token_parameters['oauth_callback'] = 'oob'
        self._request_token()

        self.c.login(username=self.username, password=self.password)
        parameters = self.authorization_parameters = {'oauth_token': self.request_token.key}
        response = self.c.get("/oauth/authorize/", parameters)

        self.assertEqual(
            response.status_code,
            200)