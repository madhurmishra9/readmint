import pytest
from fastapi import HTTPException

from app.auth import rbac
from app.config import settings


def test_auth_disabled_grants_admin():
    u = rbac.current_user(None, None)
    assert u.is_admin


def test_auth_enabled_requires_identity(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    with pytest.raises(HTTPException) as ei:
        rbac.current_user(None, None)
    assert ei.value.status_code == 401


def test_auth_enabled_parses_groups(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    u = rbac.current_user("a@b.com", "readmint-admins, other")
    assert u.email == "a@b.com"
    assert u.is_admin


def test_require_admin_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    user = rbac.current_user("a@b.com", "viewers")
    with pytest.raises(HTTPException) as ei:
        rbac.require_admin(user)
    assert ei.value.status_code == 403
