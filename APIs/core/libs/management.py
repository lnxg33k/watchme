from APIs.models import WatcherConfig

from celery.task.control import inspect
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from kombu import Connection, exceptions

import subprocess
import time
import psutil
import os
import re


def start_beat(log_pid_dir):
    cmd_beat = "celery beat -A watchMe -l info -S django"
    cmd_beat += " --detach"
    cmd_beat += " --pidfile=%s/celerybeat.pid" % log_pid_dir

    subprocess.Popen(
        cmd_beat.split(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    pidfile = '%s/celerybeat.pid' % log_pid_dir
    while True:
        time.sleep(1)
        with open(pidfile) as f:
            parent_pid = int(f.read().strip())
            parent = psutil.Process(parent_pid)
            if parent.is_running():
                break

    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10, period=IntervalSchedule.SECONDS,)

    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name='Monitor the watcher.',
        task='APIs.tasks.test',)


def start_worker(servername, q, log_pid_dir, c=2, command='start'):
    i = inspect()

    cmd = "celery multi %s -Q %s" % (command, q)
    cmd += " -A watchMe worker -c %d" % c
    cmd += " --pidfile='%s/%s.pid'" % (log_pid_dir, servername)
    cmd += " --logfile='%s/celery.log'" % log_pid_dir
    cmd += " --hostname=%s" % servername
    cmd += " --purge"
    cmd += " --loglevel=info"

    subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        time.sleep(1)
        if i.ping():
            if i.active_queues().get('worker@%s' % servername):
                break

    return {'status': 'ok', 'msg': 'Worker is up'}


def status_worker(servername=None):
    to_ping = []
    if servername:
        to_ping.append('worker@%s' % servername)

        msg_up = 'Worker [%s] is up.' % servername
        msg_down = 'Worker [%s] is down.' % servername
        if servername != 'main':
            share_path = WatcherConfig.objects.get(
                server_name=servername).share_path
            msg_up = 'Worker [%s => %s] is up.' % (servername, share_path)
            msg_down = 'Worker [%s => %s] is down.' % (servername, share_path)

    i = inspect(to_ping).ping()

    if i:
        if servername:
            return {
                'status': 'up',
                'msg': msg_up}
        else:
            return {
                'status': 'up',
                'active_workers': map(
                    lambda x: str(x.replace('worker@', '')), i.keys()),
                'msg': 'Workers %s are up.' % map(
                    lambda x: str(x.replace('worker@', '')), i.keys())}
    else:
        if servername:
            return {
                'status': 'down', 'msg': msg_down}
        else:
            return {'status': 'down', 'msg': 'All workers are *already* down.'}


def kill_worker(servername, log_pid_dir):
    try:
        pidfile = '%s/%s.pid' % (log_pid_dir, servername)

        with open(pidfile) as f:
            parent_pid = int(f.read().strip())
            parent = psutil.Process(parent_pid)

        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
        os.remove(pidfile)
        return {'status': 'ok', 'msg': 'Worker [%s] is killed.' % servername}
    except psutil.NoSuchProcess:
        os.remove(pidfile)
        return {
            'status': 'ok',
            'msg': 'PID exists but worker [%s] is not running.' % servername}
    except IOError:
        return {
            'status': 'ok', 'msg': 'Worker [%s] is not running.' % servername}
    except Exception as exc:
        return {'status': 'error', 'msg': str(exc)}


def rabbitMQstatus(broker_url):
    try:
        conn = Connection(broker_url)
        conn.ensure_connection(max_retries=1)
        return {
            'status': 'ok', 'msg': 'The broker is up.'}
    except exceptions.OperationalError:
        cburl = re.sub(
            '(?<=watcher:)(?P<pass>.*?)\W', '***', broker_url)
        return {
            'status': 'error',
            'msg': 'Failed to connect to RabbitMQ instance at %s' % cburl}


def get_available_watchers(prop='server_name'):
    try:
        watchers = WatcherConfig.objects.values_list(
            prop, flat=True)
        watchers = map(str, list(watchers))
        watchers.insert(0, 'main')
        return {
            'status': 'ok',
            'watchers': watchers,
            'msg': 'Available watchers are %s.' % watchers}
    except Exception as exc:
        return {'status': 'error', 'msg': str(exc)}
