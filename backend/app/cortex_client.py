"""LLM client — picks a provider, calls an OpenAI-compatible chat API.

Three providers, resolved in this order on every call:

1. **stub** — ``RF_LLM_STUB=true``. No network; a responder function is used
   (the default echoes the document verbatim, exercising the no-loss pipeline in
   tests and CI). Tests inject adversarial behaviour via ``set_stub_responder``.
2. **cortex** — ``RF_LLM_BASE_URL`` set. The hosted LLM, OAuth2 client-creds.
3. **local** — neither of the above, but a local OpenAI-compatible server
   (Ollama / LM Studio / vLLM) is reachable at ``RF_LOCAL_LLM_BASE_URL``. This is
   the default when Cortex is unavailable; if nothing is reachable we fall back
   to the stub so the app still runs out of the box.

Honours ``https_proxy`` and ``ca_bundle_path`` for every outbound call. Reasoning
("thinking") models wrap their scratchpad in ``<think>…</think>``; that is
stripped from every completion so it never pollutes the README or the no-loss
verifier.
"""
from __future__ import annotations

import re
import time
from typing import Callable, List, Optional

import httpx

from . import prompts
from .config import Settings, settings as _settings

StubResponder = Callable[[str, str], str]

# Reasoning models emit a hidden scratchpad in <think>…</think> (or <thinking>…).
# Strip it from output — "disable thoughts" — so only the answer reaches the pipeline.
_THINK_RE = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)

# How long a local-server probe result is trusted before we re-check.
_LOCAL_PROBE_TTL = 15.0


def strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).lstrip("\n")


def _default_stub(system: str, user: str) -> str:
    # Identity transform on the document → preserves every atom (no loss).
    return prompts.extract_document(user)


class CortexClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._token: Optional[str] = None
        self._token_exp: float = 0.0
        self._stub_responder: StubResponder = _default_stub
        # cached local-server discovery
        self._local_models: List[str] = []
        self._local_checked: float = 0.0

    # -- stub hooks -------------------------------------------------------
    @property
    def is_stub(self) -> bool:
        return self.provider() == "stub"

    def set_stub_responder(self, fn: StubResponder) -> None:
        self._stub_responder = fn

    # -- provider resolution ---------------------------------------------
    def provider(self) -> str:
        if self.settings.llm_stub:
            return "stub"
        if self.settings.llm_base_url:
            return "cortex"
        if self.list_local_models():
            return "local"
        return "stub"

    def provider_info(self) -> dict:
        """For the UI: active provider, selectable models, and the default pick."""
        prov = self.provider()
        if prov == "local":
            models = self.list_local_models()
            selected = self.settings.local_llm_model or (models[0] if models else "")
        elif prov == "cortex":
            models, selected = [self.settings.llm_model], self.settings.llm_model
        else:
            models, selected = [], ""
        return {"provider": prov, "models": models, "selected": selected}

    def list_local_models(self, *, force: bool = False) -> List[str]:
        """Model ids reported by the local server, or [] if none is reachable.

        A non-empty list also doubles as the 'local server is up' signal. The
        result is cached briefly so provider() can be called freely."""
        now = time.time()
        if not force and (now - self._local_checked) < _LOCAL_PROBE_TTL:
            return self._local_models
        self._local_checked = now
        base = (self.settings.local_llm_base_url or "").rstrip("/")
        if not base:
            self._local_models = []
            return self._local_models
        try:
            with self._httpx(timeout=3.0) as c:
                r = c.get(base + "/models")
                r.raise_for_status()
                data = r.json().get("data", [])
                self._local_models = [m["id"] for m in data if m.get("id")]
        except Exception:  # noqa: BLE001 — unreachable/garbage ⇒ no local provider
            self._local_models = []
        return self._local_models

    # -- transport --------------------------------------------------------
    def _httpx(self, *, timeout: Optional[float] = None) -> httpx.Client:
        return httpx.Client(
            proxy=self.settings.https_proxy or None,
            verify=self.settings.ca_bundle_path or True,
            timeout=self.settings.llm_timeout if timeout is None else timeout,
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

    def _chat(self, base_url: str, model: str, system: str, user: str,
              *, token: Optional[str], temperature: float, timeout: float) -> str:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        url = base_url.rstrip("/") + "/chat/completions"
        with self._httpx(timeout=timeout) as c:
            r = c.post(url, headers=headers, json=payload)
            r.raise_for_status()
            body = r.json()
        return strip_thinking(body["choices"][0]["message"]["content"])

    # -- completion -------------------------------------------------------
    def complete(self, system: str, user: str, *, temperature: Optional[float] = None,
                 model: Optional[str] = None) -> str:
        from .observability import LLM_CALLS

        prov = self.provider()
        temp = self.settings.llm_temperature if temperature is None else temperature

        if prov == "stub":
            LLM_CALLS.labels(mode="stub").inc()
            return self._stub_responder(system, user)

        if prov == "local":
            LLM_CALLS.labels(mode="local").inc()
            chosen = model or self.settings.local_llm_model or (self.list_local_models() or [""])[0]
            return self._chat(
                self.settings.local_llm_base_url, chosen, system, user,
                token=None, temperature=temp, timeout=self.settings.local_llm_timeout,
            )

        LLM_CALLS.labels(mode="live").inc()
        return self._chat(
            self.settings.llm_base_url, model or self.settings.llm_model, system, user,
            token=self._get_token(), temperature=temp, timeout=self.settings.llm_timeout,
        )


# module-level singleton (mirrors `from .cortex_client import cortex`)
cortex = CortexClient(_settings)
