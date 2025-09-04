import json
import os
import queue
import threading
import time
from typing import Any, Dict
import fcntl


class FileLock:
    """A simple file lock using ``fcntl`` for atomic access."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._fh: any = None

    def __enter__(self) -> "FileLock":
        self._fh = open(self.path, "w")
        fcntl.flock(self._fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()
        self._fh = None


class ReliableWriter:
    """Thread based writer with retry and file locking.

    Events are queued and periodically flushed to disk. A file lock is used to
    guard concurrent access. If a write fails, the data is returned to the
    queue for later retries.
    """

    def __init__(self, file_path: str, poll_interval: float = 1.0, max_retry: int = 3) -> None:
        self.file_path = file_path
        self.poll_interval = poll_interval
        self.max_retry = max_retry
        self.lock = FileLock(f"{file_path}.lock")
        self.queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._stop = threading.Event()
        self._index = self._load_last_index()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _load_last_index(self) -> int:
        """Return the index of the last successfully written line."""
        if not os.path.exists(self.file_path):
            return 0
        index = 0
        with open(self.file_path, "r", encoding="utf-8") as f:
            for index, _ in enumerate(f, 1):
                pass
        return index

    def write(self, data: Dict[str, Any]) -> None:
        """Queue data for writing.

        Each record is assigned an incremental ``idx`` field so that on restart
        new records continue after the last written line.
        """
        self._index += 1
        payload = {"idx": self._index, **data}
        self.queue.put(payload)

    def _worker(self) -> None:
        pending: list[Dict[str, Any]] = []
        while not self._stop.is_set():
            try:
                while True:
                    pending.append(self.queue.get_nowait())
            except queue.Empty:
                pass

            if not pending:
                time.sleep(self.poll_interval)
                continue

            attempts = 0
            while attempts < self.max_retry and pending:
                try:
                    with self.lock:
                        with open(self.file_path, "a", encoding="utf-8") as f:
                            for item in pending:
                                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    pending.clear()
                except Exception:
                    attempts += 1
                    time.sleep(self.poll_interval)

            if pending:
                # Writing failed after retries, put items back to queue
                for item in pending:
                    self.queue.put(item)
                pending.clear()
                time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Stop the background worker and flush remaining records."""
        self._stop.set()
        self.thread.join()

