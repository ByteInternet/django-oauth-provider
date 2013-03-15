import os
ROOT_PATH = os.path.dirname(__file__)

TEMPLATE_DEBUG = DEBUG = True
MANAGERS = ADMINS = ()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'testdb.sqlite',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = os.path.join(ROOT_PATH, 'testdb.sqlite')
DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'oauthprovider'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = '2+@4vnr#v8e273^+a)g$8%dre^dwcn#d&n#8+l6jk7r#$p&3zk'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)
ROOT_URLCONF = 'urls'
TEMPLATE_DIRS = (os.path.join(ROOT_PATH, 'templates'),)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'oauth_provider',
    'oauth_provider.tests'
)

import django
if django.VERSION >= (1, 5):
    # custom user model for tests issue #22
    INSTALLED_APPS += ('test_app',)
    AUTH_USER_MODEL = 'test_app.TestUser'
