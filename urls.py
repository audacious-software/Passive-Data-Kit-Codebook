# pylint: disable=wrong-import-position

import sys

if sys.version_info[0] > 2:
    from django.urls import re_path as url # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url

from .views import pdk_codebook_page, pdk_codebook_sitemap, pdk_codebook_page_start

urlpatterns = [
    url(r'^(?P<generator>.+)/$', pdk_codebook_page, name='pdk_codebook_page'),
    url(r'^sitemap.json$', pdk_codebook_sitemap, name='pdk_codebook_sitemap'),
    url(r'^$', pdk_codebook_page_start, name='pdk_codebook_page_start'),
]
