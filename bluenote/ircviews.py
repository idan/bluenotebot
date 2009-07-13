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
        responses.append("{0}: {1}".format(
            mark_safe(result.text), settings.DJANGO_DOCS_URL + result.link))
    
    limit = 7 if request.addressed else 3    
    if len(responses) > limit:
        current_site = Site.objects.get_current()
        url = "http://{0}{1}".format(
            current_site.domain,
            reverse('search', kwargs={'terms':terms}))
        responses = responses[:limit]
        responses.append("There are {0} results for '{1}', see {2} for the full list.".format(
            len(results), terms, url))
    
    if request.addressed:
        target = request.reply_recipient
    else:
        target = request.channel
        
    return IRCResponse(
        target, 
        '\n'.join(responses),
        'PRIVMSG')