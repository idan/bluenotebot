from django.shortcuts import render_to_response
from django.template.context import RequestContext
from bluenote.models import DocEntry

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
    pass