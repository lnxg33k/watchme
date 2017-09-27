from django.utils.encoding import smart_str
from django.core.mail import EmailMessage
from django.core import management
from django.template.loader import get_template

from celery import shared_task
from celery.utils.log import get_task_logger

from watchMe.celery import app
from watchMe.settings import rules, ALERT_EMAIL_FROM, ALERT_EMAIL_TO

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import PatternMatchingEventHandler

from APIs.models import WatcherConfig, Hit

import time
import os
import sys
import magic
import hashlib
import threading
import subprocess

logger = get_task_logger(__name__)


def installThreadExcepthook(watcher_name=None, task_id=None):
    """
    Workaround for sys.excepthook thread bug
    From
    http://spyced.blogspot.com/2007/06/workaround-for-sysexcepthook-bug.html
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psyco.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    init_old = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run

        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                # os._exit(0)
                log.delay(
                    task_id=task_id, watcher_name=watcher_name,
                    error=str(sys.exc_info()[1]), kill=True)
                w = WatcherConfig.objects.get(server_name=watcher_name)
                w.is_up = False
                w.needs_restart = True
                w.exception = str(sys.exc_info()[1])
                w.save()
                # sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init


class MyHandler(PatternMatchingEventHandler):
    def __init__(self, patterns=None, watcher_id=None, task_id=None):
        self.watcher_id = watcher_id
        self.task_id = task_id
        super(MyHandler, self).__init__(patterns)

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def process(self, event):
        if event.is_directory:
            return

        if event.src_path and event.event_type not in ('deleted', 'moved'):
            try:
                # We did this in case the file got quickly deleted
                h = Hit(
                    watcher_id=self.watcher_id,
                    src_path=event.src_path.split('/')[-1],
                    event_type=event.event_type,
                )
                h.save()

                filesize = self.sizeof_fmt(os.path.getsize(event.src_path))
                fileExtension = event.src_path.split('.')[-1]
                fileType = magic.from_file(event.src_path)

                with open(event.src_path, 'rb') as f:
                    f = f.read()
                    matches = rules.match(data=f)
                    if matches:
                        tags = ", ".join(i.rule for i in matches)
                        patterns = "\n\n".join(map(
                            lambda x: "\n".join(map(str, x.strings)), matches))

                    md5sum = hashlib.md5(f).hexdigest()
                    sha256sum = hashlib.sha256(f).hexdigest()

                    if Hit.objects.filter(sha256sum=sha256sum).exists():
                        Hit.objects.filter(pk=h.pk).update(wasSeenBefore=True)

                Hit.objects.filter(pk=h.pk).update(
                    filesize=filesize,
                    fileExtension=fileExtension,
                    fileContent=smart_str(
                        f, encoding='ascii', errors='ignore'),
                    fileType=fileType,
                    md5sum=md5sum,
                    sha256sum=sha256sum,
                )
                if matches:
                    watcher = WatcherConfig.objects.get(
                        pk=self.watcher_id)

                    Hit.objects.filter(pk=h.pk).update(
                        is_malicious=True,
                        yara_tags=tags,
                        yara_patterns=patterns
                    )

                    if watcher.allow_alerting:
                        sendAlert.delay(
                            file_path=event.src_path,
                            event_type=event.event_type,
                            watcher_name=watcher.server_name,
                            hit_pk=h.pk
                        )
            except Exception, e:
                watcher_name = WatcherConfig.objects.get(
                    pk=self.watcher_id).server_name
                log.delay(
                    task_id=self.task_id, watcher_name=watcher_name,
                    error=e.message, kill=False)
        else:
            Hit.objects.create(
                src_path=event.src_path.split('/')[-1],
                event_type=event.event_type,
                watcher_id=self.watcher_id
            )

    def on_any_event(self, event):
        self.process(event)


# # @app.on_after_finalize.connect
# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # with open('/tmp/testx.txt', 'a') as f:
#     #     f.write(time.ctime())
#     # Calls test('hello') every 10 seconds.
#     sender.add_periodic_task(5.0, test.s(), name='add every 1')

#     # # Calls test('world') every 30 seconds
#     # sender.add_periodic_task(30.0, test.s('world'), expires=10)

#     # Executes every Monday morning at 7:30 a.m.
#     # sender.add_periodic_task(
#     #     crontab(hour=7, minute=30, day_of_week=1),
#     #     test.s('Happy Mondays!'),
#     # )


@shared_task(bind=True)
def sendAlert(self, *args, **kwargs):
    file_path = kwargs.get('file_path')
    event_type = kwargs.get('event_type')
    watcher_name = kwargs.get('watcher_name')
    hit_pk = kwargs.get('hit_pk')

    subject = "WatchMe Alert! - Malicious file was just {0}".format(event_type)

    msg = EmailMessage(
        subject=subject,
        body=get_template('sendAlert.html').render({
            'file_path': file_path,
            'event_type': event_type,
            'watcher_name': watcher_name,
            'hit': Hit.objects.get(pk=hit_pk)
        }),
        from_email=ALERT_EMAIL_FROM,
        to=ALERT_EMAIL_TO,
        headers={'X-Priority': '1'}
    )
    msg.content_subtype = "html"
    msg.send()


@shared_task(bind=True)
def log(self, *args, **kwargs):
    watcher_name = kwargs.get('watcher_name')
    task_id = kwargs.get('task_id')
    error = kwargs.get('error')
    kill = kwargs.get('kill')
    logger.error('Q: %s -> Traceback: %s' % (watcher_name, error))
    if kill:
        app.control.revoke(task_id, terminate=1)
        subprocess.call(["pkill", "-9", "-f", watcher_name])


@shared_task(bind=True)
def watch(self, watcher_id):
    watcher = WatcherConfig.objects.get(pk=watcher_id)
    patterns = watcher.patterns.split(',')

    event_handler = MyHandler(
        patterns=patterns, watcher_id=watcher_id, task_id=self.request.id)
    observer = Observer()

    installThreadExcepthook(
        watcher_name=watcher.server_name, task_id=self.request.id)

    observer.schedule(
        event_handler,
        path=watcher.share_path,
        recursive=True,
    )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@shared_task(bind=True)
def keep_an_eye(self, *args, **kwargs):
    for w in WatcherConfig.objects.filter(needs_restart=True, is_up=False):
        management.call_command(
            'watcher', '-c', 'start', '-s', w.server_name)
