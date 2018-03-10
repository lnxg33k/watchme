from celery.task.control import inspect
from django.core import management
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from APIs.core.libs.management import (get_available_watchers, kill_worker,
                                       rabbitMQstatus, start_beat,
                                       start_worker, status_worker)
from APIs.models import WatcherConfig
from APIs.tasks import watch
from APIs.validators import validators
from watchMe.settings import CELERY_BROKER_URL, CELERY_PID_LOGS

rmq = rabbitMQstatus(CELERY_BROKER_URL)

if rmq.get('status') is 'error':
    exit(rmq.get('msg'))

if status_worker('main').get('status') is 'down':
    print '[*] Please note, %s' % status_worker('main').get('msg')


class Command(BaseCommand):
    help = 'Start the watcher on a specific directory.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--command', default='status',
            choices=['start', 'stop', 'status', 'restart'],
            help="The command you want to execute.")

        parser.add_argument(
            '-a', '--auto-start', dest='auto', action='store_true',
            help="Auto start the worker incase -c status reported it is down.")

        parser.add_argument(
            '-s', '--server-name', dest='server-name',
            help="The servername you already set when adding the watcher.")

        parser.add_argument(
            '-t', '--technique', required=True,
            choices=['walker', 'watchdog'],
            help="Either run using watchdog or walker.")

        parser.add_argument(
            '-f', '--force', action='store_true', dest='force',
            help='Force executing the command.')

    def handle(self, *args, **options):
        servername = options['server-name']
        force = options['force']
        command = options['command']
        auto_start = options['auto']
        technique = options['technique']
        # verbosity = options['verbosity']
        if auto_start:
            if command != 'status':
                raise CommandError(
                    'The --auto-start argument is only '
                    'applicable with the status command.'
                )

        try:

            if command == 'start':
                if not servername:
                    if not force:
                        raise CommandError(
                            'That will start all the workers, '
                            'use "--force".'
                        )

                    watchers = WatcherConfig.objects.all()
                    if watchers:
                        try:
                            management.call_command(
                                'watcher', '-c', 'start',
                                '-t', technique, '-s', 'main')
                        except Exception as exc:
                            self.stdout.write(self.style.ERROR(
                                exc))
                        for watcher in watchers:
                            try:
                                management.call_command(
                                    'watcher', '-c', 'start', '-t', technique,
                                    '-s', watcher.server_name, '--force')
                            except Exception as exc:
                                self.stdout.write(self.style.ERROR(
                                    exc))
                                pass
                    return

                # check if the path exists or no
                if servername != 'main':
                    watcher = WatcherConfig.objects.get(server_name=servername)
                    try:
                        validators.validate_share_path(watcher.share_path)
                    except ValidationError:
                        raise CommandError(
                            "[*] W: {0} => Tha path \"{1}\" doesn't exists, "
                            "create it first.".format(
                                watcher, watcher.share_path
                            )
                        )

                self.stdout.write(self.style.WARNING(
                    '[!] Starting the worker "{}", '
                    'Please wait...'.format(servername)))

                i = inspect()

                if i.ping():    # Any worker is up ?
                    i = i.stats()

                    if i.get('worker@main'):    # celery main queue is UP
                        wisup = i.get('worker@%s' % servername)

                        if wisup:
                            pid = i.get('worker@%s' % servername).get('pid')
                            ps = i.get(
                                'worker@%s' % servername)['pool']['processes']

                            raise CommandError(
                                '[-] The worker "{}" is already running under'
                                ' the following PIDs "{} {}"'.format(
                                    servername, pid, ps)
                            )

                        else:
                            if not force:
                                if validators.is_empty_share_path(
                                        watcher.share_path):
                                    raise CommandError(
                                        'The share path "{0}" doesn\'t'
                                        ' contain files'
                                        ', if you want to ignore that use,'
                                        ' --force flag.'.format(
                                            watcher.share_path)
                                    )

                            start_worker(
                                servername=servername,
                                q=servername, log_pid_dir=CELERY_PID_LOGS
                            )

                    else:
                        start_worker(
                            servername='main', q='celery',
                            log_pid_dir=CELERY_PID_LOGS)

                        start_beat(log_pid_dir=CELERY_PID_LOGS)

                        r = status_worker(servername)
                        if r.get('status') is 'down':
                            start_worker(
                                servername=servername, q=servername,
                                command='start', log_pid_dir=CELERY_PID_LOGS)

                else:
                    if not force and servername != 'main':
                        if validators.is_empty_share_path(
                                watcher.share_path):
                            raise CommandError(
                                'The share path "{0}" doesn\'t'
                                ' contain files'
                                ', if you want to ignore that use,'
                                ' --force flag.'.format(
                                    watcher.share_path)
                            )

                    start_worker(
                        servername='main', q='celery',
                        log_pid_dir=CELERY_PID_LOGS)

                    start_beat(log_pid_dir=CELERY_PID_LOGS)

                    if servername != 'main':
                        start_worker(
                            servername=servername,
                            q=servername, log_pid_dir=CELERY_PID_LOGS)

                if servername != 'main':
                    watch.apply_async(
                        (watcher.pk, technique), queue=servername)
                    watcher.is_up = True
                    watcher.needs_restart = False
                    watcher.exception = None
                    watcher.save()

                self.stdout.write(self.style.SUCCESS(
                    '[+] Successfully started watching "%s".' % servername))

            elif command == 'stop':
                if not servername:
                    if not force:
                        raise CommandError(
                            'That will stop all the running workers, '
                            'use "--force".'
                        )
                    r = status_worker(servername)
                    if r.get('status') is 'up':
                        for watcher in r.get('active_workers'):
                            management.call_command(
                                'watcher', '-s', watcher,
                                '-c', 'stop', '-t', technique
                            )
                        kill_worker('celerybeat', log_pid_dir=CELERY_PID_LOGS)
                        return
                    else:
                        self.stdout.write(self.style.WARNING(
                            '[!] %s' % r.get('msg')))
                        return

                s = kill_worker(
                    servername=servername, log_pid_dir=CELERY_PID_LOGS)
                if s.get('status') is 'ok':
                    if servername and servername not in ('main', 'celerybeat'):
                        watcher = WatcherConfig.objects.get(
                            server_name=servername)
                        watcher.is_up = False
                        watcher.save()
                    self.stdout.write(self.style.WARNING(
                        '[!] %s' % s.get('msg')))
                else:
                    raise CommandError(s.get('msg'))

                if servername == 'main':
                    kill_worker('celerybeat', CELERY_PID_LOGS)

            elif command == 'restart':
                try:
                    if not servername:
                        if not force:
                            raise CommandError(
                                'That will restart all the running workers, '
                                'use "--force".'
                            )
                        r = status_worker(servername)

                        if r.get('status') is 'down':
                            raise CommandError(
                                'All the workers are down.'
                            )

                        if servername:
                            # Stop the main worker
                            management.call_command(
                                'watcher', '-s', 'main',
                                '-c', 'stop', '-t', technique
                            )
                            # Start the main worker
                            management.call_command(
                                'watcher', '-s', 'main',
                                '-c', 'start', '-t', technique
                            )

                        # Restart main worker first
                        management.call_command(
                            'watcher', '-s', 'main',
                            '-c', 'stop', '-t', technique
                        )
                        management.call_command(
                            'watcher', '-s', 'main',
                            '-c', 'start', '-t', technique
                        )
                        active_workers = r.get('active_workers')
                        active_workers.remove('main')
                        for watcher in active_workers:
                            management.call_command(
                                'watcher', '-s', watcher,
                                '-c', 'stop', '-t', technique
                            )
                            management.call_command(
                                'watcher', '-s', watcher, '-c',
                                'start', '-t', technique
                            )
                        return

                    # This inner exception, the worker my be already down
                    try:
                        # if servername != 'main':
                        #     # Stop the main worker
                        #     management.call_command(
                        #         'watcher', '-s', 'main', '-c', 'stop'
                        #     )

                        management.call_command(
                            'watcher', '-s', servername,
                            '-c', 'stop', '-t', technique
                        )

                    except Exception:
                        pass

                    cmd_args = [
                        '-s', servername, '-c', 'start', '-t', technique]

                    if force:
                        cmd_args.append('--force')

                    if status_worker('main').get('status') is 'down':
                        management.call_command(
                            'watcher', '-s', 'main',
                            '-c', 'start', '-t', technique
                        )
                    management.call_command('watcher', *cmd_args)

                    self.stdout.write(self.style.WARNING(
                        '[+] Successfully restarted %s' % servername))

                except Exception, e:
                    raise CommandError(e)

            elif command == 'status':
                # if auto_start:
                #     f = open(os.devnull, 'w')
                #     sys.stdout = f

                if servername:
                    r = status_worker(servername)

                    if r.get('status') is 'up':
                        self.stdout.write(self.style.SUCCESS(
                            '[+] %s' % r.get('msg')))
                    else:
                        self.stdout.write(self.style.WARNING(
                            '[+] %s' % r.get('msg')))
                        if auto_start:
                            management.call_command(
                                'watcher', '-s', servername,
                                '-c', 'start', '-t', technique, force=force
                            )
                else:
                    watchers = get_available_watchers()
                    if watchers.get('status') is 'ok':
                        self.stdout.write(self.style.SUCCESS(
                            '[!] ' + watchers.get('msg'))
                        )
                        # if verbosity >= 2:
                        for watcher in watchers.get('watchers'):
                            management.call_command(
                                'watcher', '-s', watcher,
                                '-c', 'status', '-t', technique,
                                auto=auto_start, force=force
                            )
                            # sw = status_worker(watcher)
                            # if sw.get('status') is 'up':
                            #     self.stdout.write(self.style.SUCCESS(
                            #         '[+] ' + sw.get('msg')
                            #     ))
                            # else:
                            #     print sw
                            #     self.stdout.write(self.style.WARNING(
                            #         '[+] ' + sw.get('msg')
                            #     ))
                    else:
                        raise CommandError(watchers.get('msg'))
                return
        except WatcherConfig.DoesNotExist:
            ws = WatcherConfig.objects.values_list('server_name', flat=True)
            raise CommandError(
                'Watcher "{0}" does not exist.\n'
                'Available watchers: {1}'.format(servername, list(ws)))
