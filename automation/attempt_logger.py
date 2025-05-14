import os
import time
import threading
from datetime import datetime

class AttemptLogger:
    """Helper for detailed per-attempt logging with ms precision and blob upload."""
    def __init__(self, reservation_folder, attempt, blob_service):
        self.reservation_folder = reservation_folder
        self.attempt = attempt
        self.blob_service = blob_service
        self.log_dir = os.path.join(os.path.dirname(__file__), 'logs', 'temp')
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_name = f"attempt_{self.attempt}"
        self.log_path = os.path.join(self.log_dir, f"{self.log_name}.log")
        self._lock = threading.Lock()
        self._start_time = time.time()
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"Log for reservation: {self.reservation_folder}, attempt: {self.attempt}\n")
            f.write(f"Start time: {datetime.now().isoformat()}\n")

    def log(self, message):
        now = datetime.now()
        ms = int((now - now.replace(microsecond=0)).microseconds / 1000)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S') + f'.{ms:03d}'
        with self._lock:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")

    def log_duration(self, label, start, end, extra=None):
        duration_ms = int((end - start) * 1000)
        msg = f"{label} took {duration_ms} ms"
        if extra:
            msg += f" | {extra}"
        self.log(msg)

    def context(self, label):
        class Ctx:
            def __init__(self, logger):
                self.logger = logger
                self.label = label
            def __enter__(self):
                self._start = time.time()
                self.logger.log(f"START: {self.label}")
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                end = time.time()
                self.logger.log_duration(self.label, self._start, end)
                self.logger.log(f"END: {self.label}")
        return Ctx(self)

    def close_and_upload(self):
        self.log(f"Log finished at {datetime.now().isoformat()}")
        try:
            self.blob_service.upload_log_file(self.log_path, self.log_name)
            os.remove(self.log_path)
        except Exception as e:
            self.log(f"Failed to upload log file: {e}")