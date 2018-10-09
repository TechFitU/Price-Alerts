# -*- coding: utf-8 -*-
#Docs for deploying on Heroku: https://devcenter.heroku.com/articles/python-gunicorn

from multiprocessing import cpu_count

##### Gunicorn configs#####
# Server Socket
# bind = "0.0.0.0:5000"

# Este tipo de sockets es más rápido que
# utilizando la interfaz local. Por lo que si el Nginx y el Gunicorn están en
# el mismo servidor es el que les recomiendo.
# bind = "unix:/var/run/gunicorn-price-alerts.sock"
backlog = 2048

# Worker Processes
workers = cpu_count() * 2 + 1  # Valor recomendado por la doc oficial: http://docs.gunicorn.org/en/stable/design.html#how-many-workers
worker_class = 'gthread'  # gevent para un mejor rendimiento, pero no funciona con preload_app=True.
threads = 2 * cpu_count()
# The maximum number of simultaneous clients.
#This setting only affects the Eventlet and Gevent worker types.
worker_connections = 1000
# The maximum number of requests a worker will process before restarting, 0 means unlimited.
max_requests = 1200
keepalive = 5
timeout = 10  # Workers silent for more than this many seconds are killed and restarted.
graceful_timeout = 40  # Timeout for graceful workers restart.


# Security
limit_request_line = 4096
limit_request_fields = 100
# limit_request_fields = 8190

# Server Mechanics
# pidfile = '/var/run/gunicorn/gunicorn-price-alerts.pid'
# user = 'user1'
# group = 'user1'

# Logging
loglevel = 'error'
#accesslog = '/var/log/gunicorn/gunicorn-price-alerts.access.log'
#errorlog = '/var/log/gunicorn/gunicorn-price-alerts.error.log'

# Process Naming
proc_name = 'price_alert_service'

###### End Gunicorn settings#####