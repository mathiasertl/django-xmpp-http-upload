from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Upload


class UploadedListFilter(admin.SimpleListFilter):
    title = _('Uploaded')
    parameter_name = 'uploaded'

    def lookups(self, request, model_admin):
        return (
            ('2', _('Expired')),
            ('1', _('Yes')),
            ('0', _('No'))
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == '2':
            return queryset.expired()
        elif value == '1':
            return queryset.uploaded()
        elif value == '0':
            return queryset.for_upload()
        return queryset


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    ordering = ('-created', 'jid', )
    list_filter = (UploadedListFilter, )
    search_fields = ('jid', 'name', )
    list_display = ('jid', 'name', 'created', )
    list_display_links = ('jid', 'name', )
