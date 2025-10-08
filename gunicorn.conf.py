# Gunicorn configuration for TidyMe

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, default 0
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "logs/access.log"
errorlog = "logs/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "tidyme"

# Server mechanics
daemon = False
pidfile = "data/tidyme.pid"
user = None
group = None
tmp_upload_dir = None

# Application
wsgi_module = "app:app"
pythonpath = "."

# SSL (if needed)
keyfile = None
certfile = None

# Development settings
reload = True
reload_engine = "auto"