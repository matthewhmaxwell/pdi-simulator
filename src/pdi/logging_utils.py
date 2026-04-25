"""Thin logging layer. Uses rich when available, falls back to stdlib."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    from rich.logging import RichHandler
    _HANDLER: logging.Handler = RichHandler(rich_tracebacks=True, show_time=False, show_path=False)
except ImportError:  # pragma: no cover
    _HANDLER = logging.StreamHandler()


def get_logger(name: str = "pdi", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        logger.addHandler(_HANDLER)
        logger.propagate = False
    return logger


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, default=str) + "\n")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
