#!/usr/bin/python

from django.utils.encoding import force_unicode

class IRCRequest(object):
    def __init__(self, connection, user, channel, msg, method='privmsg',
                 **kwargs):
        self.my_nick = connection.nickname
        self.chanmodes = connection.chanmodes
        self.user = user
        if '!' in user:
            self.nick, self.mask = user.split('!', 1)
        else:
            self.nick, self.mask = user, None
        self.channel = channel
        self.message = force_unicode(msg)
        self.method = method.upper()
        self.context = kwargs
        self.addressee = ''
        if self.channel == self.my_nick:
            self.addressed = True
            self.reply_recipient = self.nick
        elif self.my_nick.lower() in self.message.lower():
            self.addressed = True
            self.reply_recipient = self.channel
            self.addressee = self.nick
        else:
            self.addressed = False
            self.reply_recipient = self.channel
    def __unicode__(self):
        return u'%s: <%s> %s' % (self.channel, self.user, self.message)


class IRCResponse(object):
    def __init__(self, recipient, data, method='PRIVMSG',
                 **kwargs):
        self.recipient = recipient
        self.data = force_unicode(data)
        self.method = method
        self.context = kwargs
    def __unicode__(self):
        return u'%s: <%s> %s' % (self.method, self.recipient, self.data)
