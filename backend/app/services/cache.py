"""Input-hash cache — don't re-spend Cortex tokens on identical inputs.

Redis when ``RF_REDIS_URL`` is set, otherwise a bounded in-process dict so the
single-container deployment still benefits within a process lifetime.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Optional

from ..config import settings

try:  # optional dependency
    import redis as _redis_mod
except Exception:  # pragma: no cover - redis not installed
    _redis_mod = None

_r = None
if settings.redis_url and _redis_mod is not None:
    try:
        _r = _redis_mod.from_url(settings.redis_url)
    except Exception:  # pragma: no cover
        _r = None

_LOCAL_MAX = 512
_local: "OrderedDict[str, dict]" = OrderedDict()


def key(document: str, template: str) -> str:
    h = hashlib.sha256(((template or "") + "\x00" + (document or "")).encode("utf-8")).hexdigest()
    return f"readmint:{h}"


def get(document: str, template: str) -> Optional[dict]:
    k = key(document, template)
    if _r is not None:
        v = _r.get(k)
        return json.loads(v) if v else None
    val = _local.get(k)
    if val is not None:
        _local.move_to_end(k)
    return val


def put(document: str, template: str, result: dict, ttl: int = 86400) -> None:
    k = key(document, template)
    if _r is not None:
        _r.setex(k, ttl, json.dumps(result))
        return
    _local[k] = result
    _local.move_to_end(k)
    while len(_local) > _LOCAL_MAX:
        _local.popitem(last=False)
