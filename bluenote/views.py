from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from bluenote.models import DocEntry
from bluenote.forms import SearchForm
import re

patt_split = re.compile(r'[\s,]')

def search(request, terms):
    """Show a list of search results for a list of terms."""
    results = DocEntry.objects.search(terms.split(','))
    
    current_rank = 0
    ordered = {}
    for r in results:
        if r.rank == 0:
            ordered[r] = []
        else:
            if r.parent in ordered.keys():
                ordered[r.parent].append(r)
            else:
                if None not in ordered.keys():
                    ordered[None] = []
                ordered[None].append(r)
    
    
    context = {
        'terms': terms.split(','),
        'results': ordered,
        'count': results.count(),
    }
    
    return render_to_response(
        'bluenote/results.html',
        context,
        context_instance=RequestContext(request))

def home(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            terms = [t for t in patt_split.split(form.cleaned_data['terms']) if t != '']
            redirect_to = reverse('search', kwargs={'terms':','.join(terms)})
            return HttpResponseRedirect(redirect_to)
    else:
        form = SearchForm()
    
    return render_to_response(
        'bluenote/home.html',
        {'form':form},
        context_instance=RequestContext(request))