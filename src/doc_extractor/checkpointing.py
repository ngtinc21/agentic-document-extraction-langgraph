"""Small SQLite checkpoint helpers for portfolio demos."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .schemas import ExtractionJob
from .state import WorkflowState


def resolve_checkpoint_path(state: WorkflowState) -> Path | None:
    """Resolve the configured checkpoint path for a workflow state."""

    if "job" not in state:
        return None

    job = ExtractionJob.model_validate(state["job"])
    if not job.run_options.enable_checkpoints:
        return None

    base_dir = Path(state["job_base_dir"])
    configured_path = job.run_options.checkpoint_path
    if configured_path:
        path = Path(configured_path)
        return path if path.is_absolute() else base_dir / path
    return base_dir / "outputs" / "checkpoints" / f"{job.job_id}.sqlite"


def save_checkpoint(node_name: str, state: WorkflowState) -> None:
    """Persist one JSON workflow state snapshot after a node completes."""

    checkpoint_path = resolve_checkpoint_path(state)
    if checkpoint_path is None:
        return

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    job = ExtractionJob.model_validate(state["job"])
    payload = {**state, "last_completed_node": node_name}

    with sqlite3.connect(checkpoint_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              job_id TEXT NOT NULL,
              node_name TEXT NOT NULL,
              created_at TEXT NOT NULL,
              state_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO checkpoints (job_id, node_name, created_at, state_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                job.job_id,
                node_name,
                datetime.now(UTC).isoformat(),
                json.dumps(payload, ensure_ascii=False),
            ),
        )


def load_latest_checkpoint(checkpoint_path: str | Path) -> WorkflowState | None:
    """Load the latest checkpoint state from a SQLite checkpoint database."""

    path = Path(checkpoint_path)
    if not path.exists():
        return None

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT state_json
            FROM checkpoints
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None
    return json.loads(row[0])
