from BeautifulSoup import BeautifulSoup
from django.utils.html import strip_tags
from bluenote.models import DocEntry

def parse_docs():
    with open('contents.html', 'r') as fp:
        soup = BeautifulSoup(fp)
    
    links = soup.findAll('a', {'class': 'reference external'})
    for link in links:
        href = link.attrMap['href']
        href = href.replace('.html', '')
        contents = strip_tags(link.contents[0])
        # split and look for parent
        parts = href.split('#', 2)
        if len(parts) == 2:
            parent = DocEntry.objects.get(link__exact=parts[0])
            rank = parent.rank + 1
        else:
            parent = None
            rank = 0
        
        d , created = DocEntry.objects.get_or_create(parent=parent, text=contents, link=href, rank=rank)
        print("%s, %s: %s" % (parent, contents, href))
        d.save()