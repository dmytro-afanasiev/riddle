import platform

bind = "127.0.0.1:18080"
workers = 2
worker_class = "sync"
wsgi_app = "riddle.app:make_app()"

worker_tmp_dir = "/dev/shm" if platform.system() == "Linux" else None
timeout = 30
graceful_timeout = 10

max_requests = 200
max_requests_jitter = 20
