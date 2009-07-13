#!/usr/bin/python
import logging
from os import uname

from twisted.words.protocols.irc import IRCClient
from twisted.internet import defer, threads, task
from twisted import version as twisted_version
from django import get_version as django_version
from django.core import urlresolvers
from django.conf import settings

from irc import IRCRequest, IRCResponse
from signals import request_started, request_finished
from version import VERSION

log = logging.getLogger('yardbird')
log.setLevel(logging.DEBUG)

def terrible_error(failure, bot, request, *args, **kwargs):
    """FIXME: This errback function is likely more terrible than the
    errors it handles. It sends a NOTICE with any traceback message, and
    tries to be cute about erroring out on a complete lack of
    urlresolver matches. This is handy for debugging, but likely
    irritating for production bots."""
    #def reply(bot, request, message, *args, **kwargs):
    #    recipient = request.reply_recipient
    #    res = IRCResponse(recipient, message % kwargs, method='NOTICE')
    #    return bot.methods[res.method](res.recipient, res.data.encode('utf-8'))
    log.warn(failure)
    #e = str(failure.getErrorMessage())
    #if 'path' in e and 'tried' in e:
    #    return reply(bot, request, 'Dude?')
    #return reply(bot, request, u'Dude! %s' % e)

class DjangoBot(IRCClient):
    """DjangoBot subclasses the Twisted Python IRCClient class in order
    to connect Twisted to Django with the smallest surface area
    possible.  Incoming events are largely dispatched to a Django
    urlresolver, which contains mappings from regular expressions to
    dispatch functions.  The IRCRequest and IRCResponse objects are used
    to communicate the incoming message and the desired response action
    between this class and the Django view functions."""
    def __init__(self):
        self.methods = {'PRIVMSG':  self.msg,
                        'ACTION':   self.me,
                        'NOTICE':   self.notice,
                        'TOPIC':    self.topic,
                        'RESET':    self.reimport,
                       }
        self.chanmodes = {}
        self.whoreplies = {}
        self.hostmask = '' # until we see ourselves speak, we do not know
        self.servername = ''
        self.lineRate = 1

        self.versionName = 'Yardbird'
        self.versionNum = VERSION
        udata = uname()
        self.versionEnv = 'Twisted %s and Django %s on %s-%s' % \
                (twisted_version.short(), django_version(), udata[0],
                 udata[4])
        self.sourceURL = 'http://zork.net/~nick/yardbird/ '
        self.realname = 'Charlie Parker Jr.'
        self.fingerReply = str(settings.INSTALLED_APPS)


    ############### Connection management methods ###############
    def myInfo(self, servername, version, umodes, cmodes):
        """This function is run once the connection is complete and we
        have information about what server we're talking to.  We fire
        off a periodic PING request to regularly test the connection."""
        self.servername = servername
        log.info("Connected to %s" % self.servername)
        self.l = task.LoopingCall(self.PING)
        self.l.start(60.0) # call every minute
    def connectionMade(self):
        """This function assumes that the factory was added to this
        object by the calling script.  It may be more desirable to
        implement this as an argument to the __init__"""
        self.nickname = self.factory.nickname
        IRCClient.connectionMade(self)
    def connectionLost(self, reason):
        IRCClient.connectionLost(self, reason)
        self.l.stop() # All done now.
        log.warn("Disconnected from %s" % self.servername)
    def signedOn(self):
        """Since we can't know what our hostmask will be in advance, the
        DjangoBot sends itself a trivial PRIVMSG after sign-on.  The
        privmsg() method watches for a message from the bot itself
        (based on nickname) and stores the mask internally."""
        self.msg(self.nickname, 'Watching for my own hostmask')
        for channel in self.factory.channels:
            self.join(channel)
    def joined(self, channel):
        log.info("[I have joined %s]" % channel)
        self.who(channel)
    def PING(self):
        log.debug('PING %s' % self.servername)
        self.sendLine('PING %s' % self.servername)

    ############### Event dispatch methods ###############
    @defer.inlineCallbacks
    def dispatch(self, req):
        """This method invokes a django url resolver to detect
        interesting messages and dispatch them to callback functions
        based on regular expression matches."""
        def asynchronous_work(request, args, kwargs):
            """This function runs in a separate thread, as the signal
            handlers and callback functions may take forever and a day
            to execute."""
            request_started.send(sender=self, request=request)
            response = callback(req, *args, **kwargs)
            request_finished.send(sender=self, request=request,
                                  response=response)
            return response

        resolver = urlresolvers.get_resolver('.'.join(
            (settings.ROOT_MSGCONF, req.method.lower())))
        try:
            callback, args, kwargs = yield resolver.resolve('/' + req.message)
        except urlresolvers.Resolver404:
            response = IRCResponse('', '', 'QUIET')
        else:
            response = yield threads.deferToThread(asynchronous_work, req,
                                               args, kwargs)
        if response.method == 'QUIET':
            log.debug(response)
            defer.returnValue(True)
        elif response.method == 'PRIVMSG':
            opts = {'length':
                    510 - len(':! PRIVMSG  :' + self.nickname +
                              response.recipient + self.hostmask)}
        else:
            opts = {}
        log.info(unicode(response))
        defer.returnValue(
            self.methods[response.method](response.recipient,
                                          response.data.encode('UTF-8'),
                                          **opts))
    def dispatchable_event(self, user, channel, msg, method):
        """All events that can be handled by Django code construct an
        IRCRequest representation and pass that on to the dispatch()
        method."""
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self, user, channel, msg, method)
            log.info(unicode(req))
            self.dispatch(req).addErrback(terrible_error, self, req)
        else:
            self.hostmask = user.split('!', 1)[1]
    def noticed(self, *args, **kwargs):
        """Bots are required to ignore NOTICE events to avoid endless
        loops.  This is largely irrelevant since bots use PRIVMSG these
        days anyway, but you can't say we didn't try."""
        pass # We're automatic for the people
    def privmsg(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'privmsg')
    def action(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'action')
    def topicUpdated(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'topic')
    def irc_NICK(self, user, params):
        """When a user changes nickname, there is one dispatchable event
        for each channel."""
        old_nick, mask = user.split('!', 1)
        new_nick = params[0]
        if self.nickname not in (old_nick, new_nick):
            for channel in self.chanmodes:
                if mask in self.chanmodes[channel]:
                    return self.dispatchable_event(user, channel,
                                                   new_nick, 'nick')

    ############### Special methods ###############
    def reimport(self, recipient, data, **kwargs):
        """Since our interface with the django application code is
        strictly limited to the urlresolver, we can be confident
        that it will be refreshed if we:
            * reimport all django apps listed in settings.py
            * reset the urlresolver cache"""
        import sys
        for modname, module in sys.modules.iteritems():
            # We reload yardbird library code as well as all known
            # django apps.
            for app in ['yardbird.'] + settings.INSTALLED_APPS:
                if module and modname.startswith(app):
                    reload(module)
                    break # On to next module
        urlresolvers.clear_url_caches() # Drop stale references to apps 
        self.notice(recipient, data)

    ############### Channel user-mode tracking methods ###############
    def who(self, channel):
        """Send a WHO request.  Results will come back to the irc_*WHO*
        handlers, which will update the information about user flags in
        the specified channel. Note that we explicitly lower-case the
        channel name, as some events come in with capitalization set the
        way remote users used it (e.g: "/join #YaRdBiRd")."""
        self.whoreplies[channel.lower()] = {}
        self.sendLine('WHO %s' % channel.lower())
    def irc_RPL_WHOREPLY(self, prefix, args):
        """Parse each line of the WHO listing and plug it into a
        temporary data structure."""
        me, chan, uname, host, server, nick, modes, name = args
        mask = '%s@%s' % (uname, host)
        self.whoreplies[chan.lower()][mask] = modes
    def irc_RPL_ENDOFWHO(self, prefix, args):
        """All WHO data are received, and the newly-populated data
        structure replaces a portion of the existing per-channel user
        flags data."""
        channel = args[1].lower()
        self.chanmodes[channel] = self.whoreplies[channel]
    def invalidate_chanmodes(self, user, channel, *args, **kwargs):
        """Some events do not provide us with enough information about
        the user affected, or do so in a different format (consider
        modeChanged which uses letters instead of punctuation to
        represent the varying operator status levels.  To simplify the
        code, we just get a new listing for the relevant channel rather
        than query the individual user and translate. At some point this
        should be broken out so that the individual functions can
        dispatch these events to user code."""
        self.who(channel)
    modeChanged = invalidate_chanmodes
    userJoined = invalidate_chanmodes
    userLeft = invalidate_chanmodes
    userKicked = invalidate_chanmodes
    def irc_QUIT(self, user, message):
        """Users who quit must be removed from all channel mode
        records."""
        mask = user.split('!', 1)[1]
        for channel in self.chanmodes:
            if mask in self.chanmodes[channel]:
                del(self.chanmodes[channel][mask])

