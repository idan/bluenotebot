from django.conf.urls.defaults import *
from bluenote.ircviews import *

urlpatterns = patterns('',
    (r'\?\?(?P<terms>[\w,]+)', documentation),
)

handler404 = 'yardbird.shortcuts.render_silence'
handler500 = 'yardbird.shortcuts.render_silence'