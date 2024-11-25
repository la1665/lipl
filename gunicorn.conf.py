# gunicorn.conf.py

# Server Socket
bind = "0.0.0.0:8000"
workers = 1  # Number of workers (adjust based on your server's CPU cores)
worker_class = "uvicorn.workers.UvicornWorker"
threads = 2  # Number of threads per worker (for IO-heavy applications)

# Logging
loglevel = "debug"
errorlog = "-"  # Log errors to stderr
accesslog = "-"  # Log access to stdout

# Timeout
timeout = 120  # Adjust based on your application's needs

# Preload App (Optional)
# If your app has a long startup time, preload app loads it before workers are forked.
preload_app = True
