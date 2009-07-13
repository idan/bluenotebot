from yardbird.irc import IRCRequest, IRCResponse
from yardbird.shortcuts import render_to_response, render_silence
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from bluenote.models import DocEntry

def documentation(request, terms):
    results = DocEntry.objects.search(terms.split(','))
    if not results:
        return render_silence()
        
    
    responses = []
    for result in results:
        responses.append("%s: %s" % (
            mark_safe(result.text), settings.DJANGO_DOCS_URL + result.link))
    
    limit = 7 if request.addressed else 3    
    if len(responses) > limit:
        current_site = Site.objects.get_current()
        url = "http://%s%s" % (
            current_site.domain,
            reverse('search', kwargs={'terms':terms}))
        responses = responses[:limit]
        responses.append("There are %s results for '%s', see %s for the full list." % (
            len(results), terms, url))
    
    if request.addressed:
        target = request.reply_recipient
    else:
        target = request.channel
        
    return IRCResponse(
        target, 
        mark_safe('\n'.join(responses)),
        'PRIVMSG')

def help(request):
    if request.addressed:
        target = request.reply_recipient
    else:
        target = request.channel
    
    return IRCResponse(
    target,
    "I'm a bot which finds entries in the django docs. Try writing '??serve'. For multiple terms, try '??admin,customizing'",
    'PRIVMSG')

def private_help(request):
    if not request.addressed:
        return render_silence()
    
    return IRCResponse(
    request.reply_recipient,
    "I'm a bot which finds entries in the django docs. Try writing '??serve'. For multiple terms, try '??admin,customizing'",
    'PRIVMSG')
