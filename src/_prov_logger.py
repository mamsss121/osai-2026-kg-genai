"""
_prov_logger.py — Captura runtime real de cada paso del pipeline para PROV-O.

Cada script del pipeline llama a:

    from _prov_logger import start_activity, end_activity

    start_activity("topic_modeling", params={...}, inputs=[Path(...), ...])
    # ... trabajo ...
    end_activity("topic_modeling", outputs=[Path(...), ...])

Esto vuelca a data/run_log.json:
    - timestamps reales de inicio/fin (UTC ISO 8601)
    - parametros (modelos, umbrales, etc.)
    - checksums SHA-256 de cada input y output
    - hash del commit Git actual del codigo
    - hostname y usuario que ejecuto

08_prov.py lee este JSON y emite un grafo PROV-O completo.

Sketch initially generated with AI assistance, subsequently reviewed by the group.
"""
from __future__ import annotations

import datetime as dt
import getpass
import hashlib
import json
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_LOG = PROJECT_ROOT / "data" / "run_log.json"


def _now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return ""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return ""


def _file_info(path: Path) -> dict[str, Any]:
    p = Path(path)
    rel = str(p.relative_to(PROJECT_ROOT)) if p.is_absolute() and PROJECT_ROOT in p.parents else str(p)
    info = {
        "path": rel.replace("\\", "/"),
        "exists": p.exists(),
    }
    if p.is_dir():
        files = sorted(p.glob("*"))
        info["type"] = "directory"
        info["file_count"] = len(files)
        # Para directorios grandes, hashear solo la lista de nombres+tamano
        digest = hashlib.sha256()
        for f in files:
            if f.is_file():
                digest.update(f"{f.name}:{f.stat().st_size}\n".encode("utf-8"))
        info["sha256_listing"] = digest.hexdigest()
    elif p.is_file():
        info["type"] = "file"
        info["size_bytes"] = p.stat().st_size
        info["sha256"] = _sha256(p)
    return info


def _load_log() -> dict[str, Any]:
    if RUN_LOG.exists():
        try:
            return json.loads(RUN_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_log(log: dict[str, Any]) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def start_activity(
    name: str,
    params: dict[str, Any] | None = None,
    inputs: list[Path | str] | None = None,
) -> None:
    log = _load_log()
    log.setdefault("activities", {})
    log["activities"][name] = {
        "started_at": _now(),
        "params": params or {},
        "inputs": [_file_info(Path(p)) for p in (inputs or [])],
        "git_commit": _git_commit(),
        "host": socket.gethostname(),
        "user": getpass.getuser(),
        "platform": platform.platform(),
    }
    _save_log(log)


def end_activity(
    name: str,
    outputs: list[Path | str] | None = None,
) -> None:
    log = _load_log()
    log.setdefault("activities", {})
    rec = log["activities"].setdefault(name, {"started_at": _now()})
    rec["ended_at"] = _now()
    rec["outputs"] = [_file_info(Path(p)) for p in (outputs or [])]
    _save_log(log)


def get_log() -> dict[str, Any]:
    return _load_log()
