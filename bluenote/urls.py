from django.conf.urls.defaults import *
from bluenote.views import search

urlpatterns = patterns('',
    url(r'search/(?P<terms>[\w,]+)', search, name='search'),
)