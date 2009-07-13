from django.conf.urls.defaults import *
from bluenote.views import search, home

urlpatterns = patterns('',
    url(r'search/(?P<terms>[\w,]+)', search, name='search'),
    url(r'^$', home, name='home')
)