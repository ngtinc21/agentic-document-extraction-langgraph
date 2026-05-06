"""I/O helpers for jobs, dictionaries, source documents, and outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import ExtractionJob, SourceDocument


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_job_file(job_path: str | Path) -> tuple[ExtractionJob, Path]:
    """Load a job and resolve an optional external dictionary path."""

    path = Path(job_path).resolve()
    payload = read_json(path)
    if payload.get("dictionary_path") and not payload.get("dictionary"):
        dictionary_path = (path.parent / payload["dictionary_path"]).resolve()
        payload["dictionary"] = read_json(dictionary_path)["dictionary"]
    return ExtractionJob.model_validate(payload), path.parent


def load_source_documents(job: ExtractionJob, base_dir: Path) -> list[SourceDocument]:
    """Load markdown/plain-text source document content relative to the job file."""

    documents: list[SourceDocument] = []
    for source in job.source_documents:
        source_path = (base_dir / source.path).resolve()
        content = source_path.read_text(encoding="utf-8")
        documents.append(source.model_copy(update={"content": content}))
    return documents
