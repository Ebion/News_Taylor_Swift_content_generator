"""File-based persistence layer for RunState.

Implements:
- One JSON file per run under `db/`
- Concurrency safety via `filelock`
- Atomic writes (write temp then replace)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, TypeVar

from filelock import FileLock

from app.domain.models import RunState


DB_DIR = Path("db")


def get_run_path(project_id: str, run_id: str) -> Path:
    return DB_DIR / f"proj_{project_id}_run_{run_id}.json"


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def load_run(project_id: str, run_id: str) -> RunState:
    path = get_run_path(project_id, run_id)
    if not path.exists():
        raise FileNotFoundError(f"Run not found: {path}")

    lock = FileLock(str(_lock_path(path)))
    with lock:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        state = RunState.model_validate(data)
        state.assert_invariants()
        return state


def save_run(state: RunState) -> Path:
    """Persist run state atomically."""
    DB_DIR.mkdir(exist_ok=True)
    state.assert_invariants()

    path = get_run_path(state.project_id, state.run_id)
    lock = FileLock(str(_lock_path(path)))

    with lock:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # Atomic replace on Windows and POSIX
        os.replace(tmp_path, path)

    return path


T = TypeVar("T")


def update_run(project_id: str, run_id: str, mutator: Callable[[RunState], T]) -> T:
    """Read-modify-write under the same lock.

    Returns the mutator's result.
    """
    path = get_run_path(project_id, run_id)
    if not path.exists():
        raise FileNotFoundError(f"Run not found: {path}")

    lock = FileLock(str(_lock_path(path)))
    with lock:
        data = json.loads(path.read_text(encoding="utf-8"))
        state = RunState.model_validate(data)
        state.assert_invariants()

        result = mutator(state)
        state.assert_invariants()

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp_path, path)
        return result
