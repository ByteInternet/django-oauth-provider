import time
import re

import oauth2 as oauth
import json

from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory

from oauth_provider.compat import User
from oauth_provider.models import Resource, Consumer
from oauth_provider.models import Token
from oauth_provider import utils
from oauth_provider.store import store as oauth_provider_store
from oauth_provider.store import InvalidTokenError

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

class OauthTestIssue24(BaseOAuthTestCase):
    """
    See https://bitbucket.org/david/django-oauth-plus/issue/24/utilspy-initialize_server_request-should
    """
    def setUp(self):
        super(OauthTestIssue24, self).setUp()

        #setting the access key/secret to made-up strings
        access_token = Token(
            key="key",
            secret="secret",
            consumer=self.consumer,
            user=self.jane,
            token_type=2,
            resource=self.resource
        )
        access_token.save()


    def __make_querystring(self, http_method, path, data, content_type):
        """
        Utility method for creating a request which is signed using query params
        """
        consumer = oauth.Consumer(key=self.CONSUMER_KEY, secret=self.CONSUMER_SECRET)
        token = oauth.Token(key="key", secret="secret")

        url = "http://testserver:80" + path

        #if data is json, we want it in the body, else as parameters (i.e. queryparams on get)
        parameters=None
        body = ''
        if content_type == "application/json":
            body = data
        else:
            parameters = data

        request = oauth.Request.from_consumer_and_token(
            consumer=consumer,
            token=token,
            http_method=http_method,
            http_url=url,
            parameters=parameters,
            body=body
        )

        # Sign the request.
        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        request.sign_request(signature_method, consumer, token)
        return request.to_url()

    def test_that_initialize_server_request_does_not_include_post_data_in_params(self):

        data = json.dumps({"data": {"foo": "bar"}})
        content_type = "application/json"
        querystring = self.__make_querystring("POST", "/path/to/post", data, content_type)

        #we're just using the request, don't bother faking sending it
        rf = RequestFactory()
        request = rf.post(querystring, data, content_type)

        #this is basically a "remake" of the relevant parts of OAuthAuthentication in django-rest-framework
        oauth_request = utils.get_oauth_request(request)

        consumer_key = oauth_request.get_parameter('oauth_consumer_key')
        consumer = oauth_provider_store.get_consumer(request, oauth_request, consumer_key)

        token_param = oauth_request.get_parameter('oauth_token')
        token = oauth_provider_store.get_access_token(request, oauth_request, consumer, token_param)

        oauth_server, oauth_request = utils.initialize_server_request(request)

        #check that this does not throw an oauth.Error
        oauth_server.verify_request(oauth_request, consumer, token)