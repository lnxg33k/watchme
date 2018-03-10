from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.core.exceptions import ValidationError
from django.db.models import Q

from APIs.validators import validators
from APIs.models import WatcherConfig, Tag


class Command(BaseCommand):
    help = 'Create a config for a watcher and a share path.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--server-name', dest='server-name',
            help="his is an identifier for the mount you want to monitor.")

        parser.add_argument(
            '-t', '--technique', required=True,
            choices=['walker', 'watchdog'],
            help="Either run using watchdog or walker.")

        parser.add_argument(
            '-sharepath', dest='share_path',
            help="An absolute path for the directory you want to monitor.")

        parser.add_argument(
            '-patterns', dest='patterns',
            help="List of the patterns that need to" +
            "be monitored within the share path.")

        parser.add_argument(
            '--ignored-patterns', dest="ignored_patterns",
            help="List of the patterns you may" +
            "ignore incase the patterns field is set to match all files.")

        parser.add_argument(
            '--allow-alerting', action='store_true',
            default=True, dest='allow_alerting',
            help='Send email alerts based in a YARA signature.')

        parser.add_argument(
            '--tags', dest='tags',
            help='Tags to identify the watcher seprated by a comma \',\'')

        parser.add_argument(
            '--comment', dest='comment',
            help='Add a comment to the watcher config.')

        parser.add_argument(
            '--force', action='store_true', dest='force',
            help='Force monitoring empty directories.')

        parser.add_argument(
            '--watch', action='store_true', dest='watch',
            help='Start watching the share after creating the config.')

    def handle(self, *args, **options):
        server_name = options['server-name']
        technique = options['technique']
        share_path = options['share_path']
        patterns = options['patterns']
        ignored_patterns = options['ignored_patterns'] or None
        allow_alerting = options['allow_alerting']
        tags = options['tags'] or None
        comment = options['comment'] or None
        force = options['force']
        watch = options['watch']

        if not (server_name and share_path and patterns):
            raise CommandError('Missing arguemtns: -h|--help')

        if WatcherConfig.objects.filter(
                Q(server_name=server_name) |
                Q(share_path=share_path)).exists():

            w = WatcherConfig.objects.get(
                Q(server_name=server_name) |
                Q(share_path=share_path))

            # incase the config exists, start to watch
            if not (watch and force):
                raise CommandError(
                    'The shared path is being watched on the following:\n'
                    '------------------------------------------------\n'
                    '[+] Server-name: {0}\n'
                    '[+] Share-path: {1}\n'
                    '[+] Pattern: {2}\n'
                    '------------------------------------------------\n'
                    '[!] If you want to start watch use:'
                    ' --force --watch'.format(
                        w.server_name, w.share_path, w.patterns))
            else:
                management.call_command(
                    'watcher', '-s', server_name, '-c', 'start', '--force')
                return

        else:
            try:
                w = WatcherConfig(
                    server_name=server_name, share_path=share_path,
                    patterns=patterns, ignored_patterns=ignored_patterns,
                    comment=comment, allow_alerting=allow_alerting,
                    technique=technique
                )
                w.full_clean()

                if not force:
                    if validators.is_empty_share_path(share_path):
                        raise CommandError(
                            'The share path "{0}" doesn\'t contain files'
                            ', if you want to ignore that use,'
                            ' --force flag.'.format(share_path)
                        )

                w.save()
                if tags:
                    tags = map(str.strip, tags.split(','))
                    tags = map(str.upper, tags)
                    w.tags.add(
                        *Tag.objects.filter(name__in=tags))
            except ValidationError as e:
                raise CommandError(e)

        self.stdout.write(self.style.SUCCESS(
            '[+] Successfully created a config for "%s".' % server_name))

        if watch:
            management.call_command(
                'watcher', '-s', server_name, '-c', 'start', '--force')
