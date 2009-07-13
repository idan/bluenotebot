from django.db.models import Manager

class SearchManager(Manager):
    def search(self, terms):
        qs = self.get_query_set()
        for term in terms:
            qs = qs.filter(text__icontains=term)
        qs = qs.order_by('rank')
        return qs