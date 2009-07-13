from django.contrib import admin
from bluenote.models import DocEntry

class DocEntryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'text', 'link',)
    search_fields = ('text',)
    
admin.site.register(DocEntry, DocEntryAdmin)