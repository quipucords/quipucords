"""Gunicorn configuration."""

import os

bind = '0.0.0.0:443'
backlog = 2048
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = os.getenv('QPC_SERVER_TIMEOUT', 120)
keepalive = 2
spew = False
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s"' \
    ' %(s)s %(b)s "%(f)s" "%(a)s"'


# Raw environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=quipucords.settings'
]

# SSL configuration
keyfile = '/etc/ssl/qpc/server.key'
certfile = '/etc/ssl/qpc/server.crt'

proc_name = None


def post_fork(server, worker):
    """After fork logging."""
    server.log.info('Worker spawned (pid: %s)', worker.pid)


def pre_fork(server, worker):
    """Before fork logging."""
    pass


def pre_exec(server):
    """Before exectution logging."""
    server.log.info('Forked child, re-executing.')


def when_ready(server):
    """Notify when server is ready."""
    server.log.info('Server is ready. Spawning workers')


def worker_int(worker):
    """Signal handling for worker."""
    worker.log.info('worker received INT or QUIT signal')

    # get traceback info
    import threading
    import sys
    import traceback
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append('\n# Thread: %s(%d)' % (id2name.get(threadId, ''),
                                            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                                                        lineno, name))
            if line:
                code.append('  %s' % (line.strip()))
    worker.log.debug('\n'.join(code))


def worker_abort(worker):
    """Abort logging for worker."""
    worker.log.info('worker received SIGABRT signal')
