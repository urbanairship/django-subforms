DATABASES = {'default':{
    'NAME':':memory:',
    'ENGINE':'django.db.backends.sqlite3'
}}

# install the bare minimum for
# testing django-subforms
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'subforms',
)


# point to ourselves as the root urlconf, define no patterns (see below)
ROOT_URLCONF = 'test_settings'

# set this to turn off an annoying "you're doing it wrong" message
SECRET_KEY = 'HAHAHA subforms!'

# turn this file into a pseudo-urls.py.
from django.conf.urls.defaults import *

urlpatterns = patterns('',)
