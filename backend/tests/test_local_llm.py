"""Local-LLM provider resolution, model discovery, and thinking-token stripping."""
import httpx
import pytest
import respx

from app.config import settings
from app.cortex_client import CortexClient, strip_thinking


@pytest.fixture
def fresh_client():
    """A client that is neither stub nor cortex — i.e. eligible for local."""
    return CortexClient(settings)


def test_strip_thinking_removes_scratchpad():
    out = strip_thinking("<think>let me reason\nabout this</think>\n# Title\n\nbody")
    assert out == "# Title\n\nbody"
    assert "reason" not in out


def test_strip_thinking_is_noop_without_tags():
    assert strip_thinking("# Title\n\nplain") == "# Title\n\nplain"


def test_strip_thinking_handles_thinking_variant_and_case():
    assert strip_thinking("<Thinking>hmm</Thinking>X") == "X"


@respx.mock
def test_provider_is_local_when_server_reachable(monkeypatch, fresh_client):
    monkeypatch.setattr(settings, "llm_stub", False)
    monkeypatch.setattr(settings, "llm_base_url", "")
    monkeypatch.setattr(settings, "local_llm_base_url", "http://localhost:11434/v1")
    respx.get("http://localhost:11434/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "llama3.2"}, {"id": "qwen3"}]})
    )
    assert fresh_client.provider() == "local"
    assert fresh_client.list_local_models(force=True) == ["llama3.2", "qwen3"]
    info = fresh_client.provider_info()
    assert info["provider"] == "local"
    assert info["selected"] == "llama3.2"  # first model when none pinned


@respx.mock
def test_falls_back_to_stub_when_local_unreachable(monkeypatch, fresh_client):
    monkeypatch.setattr(settings, "llm_stub", False)
    monkeypatch.setattr(settings, "llm_base_url", "")
    respx.get("http://localhost:11434/v1/models").mock(side_effect=httpx.ConnectError("nope"))
    assert fresh_client.list_local_models(force=True) == []
    assert fresh_client.provider() == "stub"


@respx.mock
def test_complete_uses_local_and_strips_thinking(monkeypatch, fresh_client):
    monkeypatch.setattr(settings, "llm_stub", False)
    monkeypatch.setattr(settings, "llm_base_url", "")
    respx.get("http://localhost:11434/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3"}]})
    )
    chat = respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "<think>plan</think>\n# Clean\n\nbody"}}]
        })
    )
    out = fresh_client.complete("sys", "user", model="qwen3")
    assert out == "# Clean\n\nbody"
    # request went to the local server with the chosen model, no auth header
    sent = chat.calls.last.request
    assert '"model":"qwen3"' in sent.content.decode().replace(" ", "")
    assert "authorization" not in {k.lower() for k in sent.headers}


def test_cortex_takes_precedence_over_local(monkeypatch, fresh_client):
    monkeypatch.setattr(settings, "llm_stub", False)
    monkeypatch.setattr(settings, "llm_base_url", "https://cortex.example/v1")
    # provider() must not even probe local when Cortex is configured
    assert fresh_client.provider() == "cortex"
