"""Cortex LLM client — OAuth2 client-credentials, OpenAI-compatible chat API.

Honours ``https_proxy`` and ``ca_bundle_path`` for every outbound call. Caches
the bearer token until shortly before expiry.

Stub mode (``RF_LLM_STUB=true`` or no ``RF_LLM_BASE_URL``): no network call is
made; a responder function is used instead. The default responder echoes the
wrapped document verbatim — perfect for exercising the no-loss pipeline in tests
and local dev. Tests can inject adversarial behaviour via ``set_stub_responder``.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

import httpx

from . import prompts
from .config import Settings, settings as _settings

StubResponder = Callable[[str, str], str]


def _default_stub(system: str, user: str) -> str:
    # Identity transform on the document → preserves every atom (no loss).
    return prompts.extract_document(user)


class CortexClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._token: Optional[str] = None
        self._token_exp: float = 0.0
        self._stub_responder: StubResponder = _default_stub

    # -- stub hooks -------------------------------------------------------
    @property
    def is_stub(self) -> bool:
        return self.settings.llm_stub or not self.settings.llm_base_url

    def set_stub_responder(self, fn: StubResponder) -> None:
        self._stub_responder = fn

    # -- transport --------------------------------------------------------
    def _httpx(self) -> httpx.Client:
        return httpx.Client(
            proxy=self.settings.https_proxy or None,
            verify=self.settings.ca_bundle_path or True,
            timeout=self.settings.llm_timeout,
        )

    def _get_token(self) -> Optional[str]:
        if not (self.settings.llm_token_url and self.settings.llm_client_id):
            return None
        now = time.time()
        if self._token and now < self._token_exp - 30:
            return self._token
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.llm_client_id,
            "client_secret": self.settings.llm_client_secret,
        }
        if self.settings.llm_scope:
            data["scope"] = self.settings.llm_scope
        with self._httpx() as c:
            r = c.post(self.settings.llm_token_url, data=data)
            r.raise_for_status()
            body = r.json()
        self._token = body["access_token"]
        self._token_exp = now + float(body.get("expires_in", 3600))
        return self._token

    # -- completion -------------------------------------------------------
    def complete(self, system: str, user: str, *, temperature: Optional[float] = None) -> str:
        from .observability import LLM_CALLS

        if self.is_stub:
            LLM_CALLS.labels(mode="stub").inc()
            return self._stub_responder(system, user)
        LLM_CALLS.labels(mode="live").inc()

        token = self._get_token()
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.llm_temperature if temperature is None else temperature,
        }
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        with self._httpx() as c:
            r = c.post(url, headers=headers, json=payload)
            r.raise_for_status()
            body = r.json()
        return body["choices"][0]["message"]["content"]


# module-level singleton (mirrors `from .cortex_client import cortex`)
cortex = CortexClient(_settings)
