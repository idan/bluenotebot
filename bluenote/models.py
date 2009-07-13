from django.db import models
from django.conf import settings
from bluenote.managers import SearchManager

class DocEntry(models.Model):
    """(DocEntry description)"""
    parent = models.ForeignKey('DocEntry', blank=True, null=True)
    rank = models.IntegerField(blank=True, null=True, default=0)
    text = models.CharField(blank=True, max_length=255)
    link = models.CharField(blank=True, max_length=255)
    objects = SearchManager()
    
    class Meta:
        ordering = ['rank',]
        verbose_name, verbose_name_plural = 'Documentation Entry', 'Documentation Entries'
    
    def __unicode__(self):
        return self.text
    
    def get_absolute_link(self):
        return settings.DJANGO_DOCS_URL + self.link
    
