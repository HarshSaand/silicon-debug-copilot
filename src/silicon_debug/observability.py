from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

logger = logging.getLogger("silicon_debug")


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    events: list[dict] = field(default_factory=list)

    def record(self, state: str, **fields: object) -> None:
        event = {"state": state, **fields}
        self.events.append(event)
        logger.info(json.dumps({"trace_id": self.trace_id, **event}, default=str))

    @contextmanager
    def span(self, state: str):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.record(state, latency_ms=round((time.perf_counter() - started) * 1000, 3))

