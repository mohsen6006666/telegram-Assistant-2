"""Gunicorn configuration file"""

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Server mechanics
daemon = False
reload = True
spew = False

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "gunicorn_telegram_bot"

# Important: Use app.py instead of main.py
wsgi_app = "app:app"

# Server hooks
def on_starting(server):
    """Log when server is starting"""
    server.log.info("Starting Gunicorn for Telegram Bot Server")

def when_ready(server):
    """Log when server is ready"""
    server.log.info("Gunicorn server is ready. Listening at: {}".format(bind))

def worker_exit(server, worker):
    """Log when a worker exits"""
    server.log.info("Worker exited (pid: %d)", worker.pid)