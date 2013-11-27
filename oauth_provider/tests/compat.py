# -*- coding: utf-8 -*-
from unittest import TestCase


class Issue45ErrorLoadingOauthStoreModule(TestCase):
    def test_store_import(self):
        from oauth_provider.store import store
        self.assertIsNotNone(store)

    def test_import_user_from_compat(self):
        from oauth_provider.compat import User
        from oauth_provider.compat import AUTH_USER_MODEL

        self.assertIsNotNone(User)
        self.assertIsNotNone(AUTH_USER_MODEL)