"""Central configuration.

Every value is overridable via an ``RF_``-prefixed environment variable (see
``deploy/secret.example.yaml``). Optional add-ons (Redis, Postgres,
oauth2-proxy, GitHub App) are *off by default*: leave their env vars unset and
the app stays a stateless single container.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Readmint"
    environment: str = "dev"
    log_level: str = "INFO"

    # --- Cortex LLM (OAuth2 client-credentials) ---
    llm_base_url: str = ""
    llm_model: str = "cortex-default"
    llm_token_url: str = ""
    llm_client_id: str = ""
    llm_client_secret: str = ""
    llm_scope: str = ""
    llm_temperature: float = 0.2
    llm_timeout: float = 180.0
    # When true the client runs in stub mode and never makes a network call —
    # used by tests and CI. When false and no Cortex URL is set, the client
    # auto-detects a local LLM (see below) and only falls back to the stub if
    # none is reachable.
    llm_stub: bool = False

    # --- Local LLM (Ollama / LM Studio / vLLM — OpenAI-compatible) ---
    # Used automatically when Cortex is not configured (llm_base_url empty) and a
    # server is reachable here. Ollama's default is http://localhost:11434/v1.
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = ""  # empty ⇒ first model the server reports
    local_llm_timeout: float = 600.0  # local models can be slow on first load

    # --- Pipeline ---
    max_retries: int = 2
    batch_concurrency: int = 4

    # --- Secret policy ---
    # "block" (default) refuses high-severity findings; "redact" rewrites them.
    secret_policy: str = "block"

    # --- Outbound HTTP (proxy / TLS) — honoured by every egress call ---
    https_proxy: Optional[str] = None
    ca_bundle_path: Optional[str] = None

    # --- GitHub App (optional) ---
    gh_app_id: str = ""
    gh_installation_id: str = ""
    gh_private_key: str = ""
    gh_api_base: str = "https://api.github.com"

    # --- Cache (optional) ---
    redis_url: Optional[str] = None
    cache_ttl: int = 86400

    # --- Persistence / audit (optional) ---
    database_url: Optional[str] = None

    # --- Confluence export (optional) ---
    confluence_base_url: str = ""
    confluence_token: str = ""
    confluence_space: str = ""

    # --- Auth / RBAC ---
    # When false, rbac trusts everyone (single-tenant / dev). oauth2-proxy sets
    # the X-Auth-Request-* headers in production.
    auth_enabled: bool = False
    admin_groups: str = "readmint-admins"

    # --- Templates ---
    templates_dir: str = "templates"

    # ---- derived helpers ----
    @property
    def cache_enabled(self) -> bool:
        return bool(self.redis_url)

    @property
    def history_enabled(self) -> bool:
        return bool(self.database_url)

    @property
    def github_enabled(self) -> bool:
        return bool(self.gh_app_id and self.gh_installation_id and self.gh_private_key)

    @property
    def confluence_enabled(self) -> bool:
        return bool(self.confluence_base_url and self.confluence_token)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_base_url) and not self.llm_stub

    @property
    def cortex_enabled(self) -> bool:
        """Cortex (the hosted LLM) is the provider when its URL is configured."""
        return bool(self.llm_base_url) and not self.llm_stub

    def admin_group_set(self) -> set[str]:
        return {g.strip() for g in self.admin_groups.split(",") if g.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenient module-level singleton (mirrors the plan's `from .config import settings`).
settings = get_settings()
