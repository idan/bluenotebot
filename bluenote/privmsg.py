from django.conf.urls.defaults import *
from django.conf import settings
from bluenote.ircviews import *

self_nick = settings.IRC_NICK

urlpatterns = patterns('',
    (r'\?\?(?P<terms>[\w,]+)', documentation),
    (r'^%s' % settings.IRC_NICK, help),
    (r'^.*', private_help),
)

handler404 = 'yardbird.shortcuts.render_silence'
handler500 = 'yardbird.shortcuts.render_silence'