from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.html import format_html, format_html_join

from APIs.validators import validators

# from APIs.tasks import sendAlert


class Tag(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField('Tag name', max_length=50, unique=True)

    def clean(self):
        self.name = self.name.upper()

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __unicode__(self):
        return self.name


class WhiteListedHash(models.Model):
    """(WhiteListedHashes description)"""
    sha256sum = models.CharField(max_length=256)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.sha256sum


class WatcherConfig(models.Model):
    technique_choices = (
        ('walker', 'walker'),
        ('watchdog', 'watchdog')
    )
    created = models.DateTimeField(auto_now_add=True)
    technique = models.CharField(choices=technique_choices, max_length=20)
    server_name = models.CharField(
        'Server name', max_length=50, unique=True,
        help_text="This is an identifier for the mount you"
        " want to monitor.<br />Example: <b>OWA-Server1</b>.")

    share_path = models.CharField(
        'Share path', max_length=250, unique=True,
        help_text='An absolute path for the directory you'
        ' want to monitor.<br />Exampe: <b>/mnt/OWAServer1</b>.',
        validators=[validators.validate_share_path],)

    patterns = models.CharField(
        'Patterns', max_length=200,
        help_text='List of the patterns that need to be monitored'
        ' within the share path.<br />Exampe: <b>*.aspx,*.dll,*.dll</b>.')

    ignored_patterns = models.CharField(
        'Ignored patterns', max_length=200, blank=True, null=True,
        help_text='List of the patterns you may ignore incase the'
        ' patterns field is set to match all files \'*.*\'.')

    comment = models.TextField(blank=True)

    tags = models.ManyToManyField('Tag', blank=True)

    WhiteListedHashes = models.ManyToManyField('WhiteListedHash', blank=True)

    allow_alerting = models.BooleanField(
        'Send email alerts',
        default=True, help_text="Send an email alert when an event triggers.")

    is_up = models.BooleanField(
        default=False,
        help_text='The watcher status (up/down).'
    )
    exception = models.TextField(
        blank=True, null=True,
        help_text='The exception that mad the watcher to stop.')
    needs_restart = models.BooleanField(
        default=False, help_text='Restart the watcher incase of an exception.')

    def clean(self):
        self.server_name = self.server_name.replace(' ', '_')

    class Meta:
        verbose_name = "Watcher"
        verbose_name_plural = "Watchers"

    def save(self, *args, **kwargs):
        if self.technique == 'walker':
            self.patterns = self.patterns.replace('*', '')
        super(WatcherConfig, self).save(*args, **kwargs)

    def __str__(self):
        return self.server_name


class Hit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    src_path = models.CharField("Path", max_length=250)
    event_type = models.CharField(
        "Evenet type", max_length=200, null=True, blank=True)
    md5sum = models.CharField('MD5', blank=True, null=True, max_length=50)
    sha256sum = models.CharField(
        'SHA256', blank=True, null=True, max_length=256)
    filesize = models.CharField(
        "File size", blank=True, null=True, max_length=50)
    fileType = models.CharField(
        'File type', max_length=100, blank=True, null=True)
    fileExtension = models.CharField(
        'File extension', null=True, blank=True, max_length=50)
    fileContent = models.TextField('File content', null=True, blank=True)
    wasSeenBefore = models.BooleanField('Was seen before', default=False)
    emailWasSent = models.BooleanField('An alert was sent?', default=False)
    is_malicious = models.BooleanField('Is malicious', default=False)
    yara_tags = models.CharField('Yara tags',
                                 max_length=50, null=True, blank=True)
    yara_patterns = models.TextField(null=True, blank=True)

    watcher = models.ForeignKey('WatcherConfig', on_delete=models.CASCADE)

    def vTotal(self):
        if self.sha256sum:
            r = format_html(
                '<a target="_blank" href="https://www.virustotal.com/en/'
                'file/{0}/analysis/">{1}</a>',
                self.sha256sum, truncatechars(self.md5sum, 20))
        else:
            r = None
        return r

    def matched_files(self):
        if self.wasSeenBefore:
            hits = Hit.objects.filter(
                sha256sum=self.sha256sum).exclude(pk=self.pk)
            return format_html_join(
                ' ', '<a href="{}">({}:{})</a>',
                (
                    (
                        reverse(
                            'admin:%s_%s_change' % (
                                self._meta.app_label, self._meta.model_name),
                            args=[h.id]),
                        h.watcher.server_name,
                        h.src_path
                    ) for h in hits
                )
            )
        else:
            return

    def save(self, *args, **kwargs):
        if Hit.objects.filter(sha256sum=self.sha256sum).exists():
            self.wasSeenBefore = True
        super(Hit, self).save(*args, **kwargs)

    @property
    def short_fileType(self):
        return truncatechars(self.fileType, 30)

    class Meta:
        verbose_name = "Hit"
        verbose_name_plural = "Hits"
        ordering = ("created",)

    def __unicode__(self):
        return self.src_path
