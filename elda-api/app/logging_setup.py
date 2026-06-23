"""Structured logging with trace/task IDs."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
task_id_var: ContextVar[str] = ContextVar("task_id", default="-")


class TraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        record.task_id = task_id_var.get()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    fmt = "%(asctime)s [%(levelname)s] trace=%(trace_id)s task=%(task_id)s %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(TraceFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def bind_context(trace_id: str = "-", task_id: str = "-") -> None:
    trace_id_var.set(trace_id)
    task_id_var.set(task_id)
