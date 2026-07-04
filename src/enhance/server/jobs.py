"""Serialized single-worker job queue — replaces `QThreadPool(1)` + `AsyncWorker`.

Runs one job at a time on a dedicated worker thread and records status/latency/
device for the task-queue view (`WorkerHistory` equivalent). Not yet wired to the
first-commit endpoints, but provided so the transport layer is complete.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class JobStatus:
    label: str
    device: Optional[str] = None
    status: str = "scheduled"  # scheduled | running | finished | interrupted | error
    scheduleTime: float = field(default_factory=time.time)
    latency: Optional[float] = None


class JobQueue:
    def __init__(self) -> None:
        self._queue: "queue.Queue[tuple[Callable[[], None], JobStatus]]" = queue.Queue()
        self.history: List[JobStatus] = []
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self._worker.start()

    def submit(self, work: Callable[[], None], label: str, device: Optional[str] = None) -> JobStatus:
        status = JobStatus(label=label, device=device)
        self.history.append(status)
        self._queue.put((work, status))
        return status

    def _run(self) -> None:
        while True:
            work, status = self._queue.get()
            status.status = "running"
            start = time.time()
            try:
                work()
                status.status = "finished"
            except Exception as e:  # pragma: no cover - defensive
                logger.exception("Job failed: %s", e)
                status.status = "error"
            finally:
                status.latency = time.time() - start
                self._queue.task_done()


job_queue = JobQueue()
