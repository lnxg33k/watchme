# -*- coding: utf-8 -*-

from dal import autocomplete
from django import forms
from django.contrib import admin

from APIs.models import Hit, Tag, WatcherConfig, WhiteListedHash
from APIs.widgets import HtmlEditor

# admin.site.register(WatcherConfig)
# admin.site.register(Hit)


class HitInline(admin.TabularInline):
    model = Hit
    fields = ('src_path', 'event_type', 'wasSeenBefore', 'is_malicious')
    classes = ['collapse']


class WatcherConfigAdminForm(forms.ModelForm):
    model = WatcherConfig

    class Meta:
        widgets = {
            'tags': autocomplete.ModelSelect2Multiple(url='tag-autocomplete')
        }


class WatcherConfigAdmin(admin.ModelAdmin):

    form = WatcherConfigAdminForm

    list_display = (
        'server_name', 'technique', 'share_path', 'patterns',
        'ignored_patterns', 'allow_alerting', 'is_up',
        'needs_restart', 'get_tags', 'created')
    list_filter = ('patterns', 'tags', 'is_up', 'needs_restart')
    search_fields = ('share_path', 'server_name')
    readonly_fields = ('is_up', 'needs_restart', 'exception')
    inlines = [
        HitInline
    ]
    filter_horizontal = ('WhiteListedHashes', )

    def get_tags(self, obj):
        return ", ".join([p.name for p in obj.tags.all()])

    get_tags.short_description = "Tags"


class HitAdminForm(forms.ModelForm):
    model = Hit

    class Meta:
        widgets = {'fileContent': HtmlEditor()}


class HitAdmin(admin.ModelAdmin):
    '''
        Admin View for Hit
    '''

    form = HitAdminForm
    list_display = ('src_path', 'event_type',
                    'yara_tags', 'vTotal',
                    'filesize', 'short_fileType', 'watcher',
                    'wasSeenBefore', 'is_malicious', 'created')
    list_filter = ('is_malicious', 'watcher__server_name',
                   'event_type', 'fileExtension', 'wasSeenBefore', 'created')

    # raw_id_fields = ('',)
    readonly_fields = (
        'matched_files', 'is_malicious',
        'wasSeenBefore', 'emailWasSent')
    search_fields = ('src_path', 'md5sum', 'sha256sum',
                     'fileType', 'fileContent')
    ordering = ['-created']


class TagAdmin(admin.ModelAdmin):
    '''
        Admin View for Tag
    '''
    list_display = ('name',)
    list_filter = ('name',)
    # inlines = [
    #     Inline,
    # ]
    # raw_id_fields = ('',)
    # readonly_fields = ('',)
    # search_fields = ('',)


class WhiteListedHashAdmin(admin.ModelAdmin):
    '''
        Admin View for WhiteListedHashes
    '''
    list_display = ('sha256sum', )


admin.site.register(Tag, TagAdmin)
admin.site.register(WhiteListedHash, WhiteListedHashAdmin)
admin.site.register(Hit, HitAdmin)
admin.site.register(WatcherConfig, WatcherConfigAdmin)

admin.site.site_title = 'WatchME!'
admin.site.site_header = 'WatchME!'
# admin.site.empty_value_display = '(None)'
