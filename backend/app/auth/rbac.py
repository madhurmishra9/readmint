"""Role checks from oauth2-proxy headers.

oauth2-proxy (Azure AD) injects ``X-Auth-Request-Email`` and
``X-Auth-Request-Groups`` after authenticating. When ``RF_AUTH_ENABLED`` is
false (dev / single-tenant) we synthesise an anonymous admin so the app is
usable without the sidecar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from fastapi import Depends, Header, HTTPException, status

from ..config import settings


@dataclass
class User:
    email: str
    groups: List[str]

    @property
    def is_admin(self) -> bool:
        return bool(set(self.groups) & settings.admin_group_set())


def current_user(
    x_auth_request_email: str | None = Header(default=None),
    x_auth_request_groups: str | None = Header(default=None),
) -> User:
    if not settings.auth_enabled:
        return User(email="anonymous@localhost", groups=list(settings.admin_group_set()))
    if not x_auth_request_email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing authenticated identity")
    groups = [g.strip() for g in (x_auth_request_groups or "").split(",") if g.strip()]
    return User(email=x_auth_request_email, groups=groups)


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin role required")
    return user
