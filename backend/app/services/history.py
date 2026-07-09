"""Runs / versions / audit log (optional Postgres).

The governance record a bank wants: ``(user, action, target, score_before,
score_after, verified, timestamp)``. Never stores README bodies or secret
matches. When ``RF_DATABASE_URL`` is unset the app stays stateless and keeps a
small in-memory ring for the current process so ``/api/history`` still works in
dev.
"""
from __future__ import annotations

import datetime as _dt
from collections import deque
from typing import Dict, List, Optional

import structlog

from ..config import settings

log = structlog.get_logger(__name__)

_RING: "deque[dict]" = deque(maxlen=200)
_engine = None
_table = None


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _init_db():
    global _engine, _table
    if _engine is not None or not settings.history_enabled:
        return
    from sqlalchemy import (Boolean, Column, DateTime, Integer, MetaData, String, Table, create_engine, func)

    _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    meta = MetaData()
    _table = Table(
        "readmint_runs", meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("ts", DateTime(timezone=True), server_default=func.now()),
        Column("user_email", String(320)),
        Column("action", String(32)),
        Column("target", String(512)),
        Column("status", String(16)),
        Column("score_before", Integer),
        Column("score_after", Integer),
        Column("verified", Boolean),
    )
    meta.create_all(_engine)


def _score(result: dict, side: str) -> Optional[int]:
    try:
        return int(result["score"][side]["score"])
    except Exception:
        return None


def record(user_email: str, action: str, target: str, result: dict) -> None:
    entry = {
        "ts": _now(),
        "user_email": user_email,
        "action": action,
        "target": target,
        "status": result.get("status"),
        "score_before": _score(result, "before"),
        "score_after": _score(result, "after"),
        "verified": result.get("verified"),
    }
    _RING.appendleft(entry)
    if not settings.history_enabled:
        return
    try:
        _init_db()
        with _engine.begin() as conn:
            conn.execute(_table.insert().values(**{k: v for k, v in entry.items() if k != "ts"}))
    except Exception as e:  # pragma: no cover - audit must never break the request
        log.warning("history.record_failed", error=str(e))


def list_runs(limit: int = 50) -> List[dict]:
    if settings.history_enabled:
        try:
            _init_db()
            from sqlalchemy import select
            with _engine.connect() as conn:
                rows = conn.execute(
                    select(_table).order_by(_table.c.ts.desc()).limit(limit)
                ).mappings().all()
                return [dict(r) | {"ts": str(r["ts"])} for r in rows]
        except Exception as e:  # pragma: no cover
            log.warning("history.list_failed", error=str(e))
    return list(_RING)[:limit]


def dashboard(limit: int = 500) -> List[dict]:
    """One row per target (repo/file), worst-scoring first.

    Built entirely from ``list_runs`` — no new storage, no new schema. A
    target with no ``score_after`` yet (e.g. blocked on secrets) sorts last,
    not first, so it doesn't masquerade as the worst-scoring repo."""
    runs = list_runs(limit)  # newest-first
    by_target: "Dict[str, List[dict]]" = {}
    for r in runs:
        by_target.setdefault(r["target"], []).append(r)

    rows = []
    for target, entries in by_target.items():
        trend = [e["score_after"] for e in reversed(entries) if e["score_after"] is not None]
        latest = entries[0]
        rows.append({
            "target": target,
            "runs": len(entries),
            "latest_score": latest["score_after"],
            "latest_ts": latest["ts"],
            "verified": latest["verified"],
            "trend": trend,
        })
    rows.sort(key=lambda r: r["latest_score"] if r["latest_score"] is not None else 101)
    return rows
