# Gunicorn Configuration for Production
# Usage: gunicorn -c gunicorn.conf.py app:app

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv('WORKER_TIMEOUT', 120))
keepalive = 5
max_requests = 10000
max_requests_jitter = 1000

# Preload application for memory efficiency
preload_app = True

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "proteinhub-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"

# SSL (handled by nginx)
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Application preloading
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called when receiving SIGHUP."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    pass

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass
