"""WebSocket hub — replaces the Qt `Signals` push model.

Server -> renderer messages (progress, file updates, gpuStats, etc.) are
broadcast as JSON to every connected renderer. A background task pushes GPU
stats on a fixed cadence, replacing the Qt `QTimer`.
"""

import asyncio
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)

GPU_PUSH_INTERVAL_SECONDS = 2.0


class EventHub:
    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the server event loop so background threads can broadcast."""
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_threadsafe(self, message: Dict[str, Any]) -> None:
        """Broadcast from a non-async context (e.g. a job worker thread)."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)


hub = EventHub()


async def gpu_stats_loop(get_stats) -> None:
    """Periodically push GPU stats to all clients (replaces the Qt QTimer)."""
    while True:
        try:
            await hub.broadcast({"type": "gpuStats", "payload": get_stats()})
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("gpu_stats_loop error: %s", e)
        await asyncio.sleep(GPU_PUSH_INTERVAL_SECONDS)
