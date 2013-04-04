import time
from oauth_provider.tests.auth import BaseOAuthTestCase

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

class OAuthTestsBug24PostWithApplicationJSON(BaseOAuthTestCase):
    def test_post_using_authorization_header(self):
        self._request_token()
        self._authorize()

        parameters = {
            'oauth_consumer_key': self.CONSUMER_KEY,
            'oauth_signature_method': "PLAINTEXT",
            'oauth_version': "1.0",
            'oauth_token': self.oauth_token,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(int(time.time()))+"nonce",
            'oauth_signature': "%s&%s" % (self.CONSUMER_SECRET, self.oauth_token_secret),
            }
        header = self._get_http_authorization_header(parameters)
        response = self.c.post("/oauth/photo/", HTTP_AUTHORIZATION=header)

        self.assertEqual(response.status_code, 200)

    def test_post_using_header_with_content_type_json(self):
        self._request_token()
        self._authorize()

        parameters = {
            'oauth_consumer_key': self.CONSUMER_KEY,
            'oauth_signature_method': "PLAINTEXT",
            'oauth_version': "1.0",
            'oauth_token': self.oauth_token,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(int(time.time()))+"nonce",
            'oauth_signature': "%s&%s" % (self.CONSUMER_SECRET, self.oauth_token_secret),
            }

        header = self._get_http_authorization_header(parameters)
        response = self.c.post("/oauth/photo/", HTTP_AUTHORIZATION=header, CONTENT_TYPE="application/json")

        self.assertEqual(response.status_code, 200)