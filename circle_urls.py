# pylint: disable=wrong-import-position

import sys

import django

from django.contrib import admin

if sys.version_info[0] > 2:
    from django.urls import re_path as url, include # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url, include

urlpatterns = [
    url(r'^admin/', django.contrib.admin.site.urls),
    url(r'^data/codebook', include('passive_data_kit_codebook.urls')),
    url(r'^data/', include('passive_data_kit.urls')),
]
