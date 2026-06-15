import httpx
import respx

from app.config import Settings
from app.cortex_client import CortexClient
from app import prompts


def test_stub_mode_echoes_document():
    c = CortexClient(Settings(llm_stub=True))
    assert c.is_stub
    user = prompts.USER.format(document="# Hi\n\ncontent here")
    out = c.complete("sys", user)
    assert out == "# Hi\n\ncontent here"


def test_no_base_url_is_stub():
    c = CortexClient(Settings(llm_base_url=""))
    assert c.is_stub


def test_custom_stub_responder():
    c = CortexClient(Settings(llm_stub=True))
    c.set_stub_responder(lambda system, user: "REPLACED")
    assert c.complete("s", "u") == "REPLACED"


@respx.mock
def test_real_mode_oauth_then_completion():
    s = Settings(
        llm_base_url="https://cortex.example/v1",
        llm_token_url="https://auth.example/oauth2/token",
        llm_client_id="cid",
        llm_client_secret="csecret",
        llm_scope="cortex.completions",
        llm_stub=False,
    )
    c = CortexClient(s)
    assert not c.is_stub

    token_route = respx.post("https://auth.example/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok123", "expires_in": 3600})
    )
    comp_route = respx.post("https://cortex.example/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "# Refined"}}]})
    )

    out = c.complete("system prompt", "user prompt")
    assert out == "# Refined"
    assert token_route.called
    assert comp_route.called
    # Authorization header carried the fetched token
    sent = comp_route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer tok123"


@respx.mock
def test_token_is_cached_between_calls():
    s = Settings(
        llm_base_url="https://cortex.example/v1",
        llm_token_url="https://auth.example/oauth2/token",
        llm_client_id="cid",
        llm_client_secret="csecret",
        llm_stub=False,
    )
    c = CortexClient(s)
    token_route = respx.post("https://auth.example/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    respx.post("https://cortex.example/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})
    )
    c.complete("s", "u")
    c.complete("s", "u")
    assert token_route.call_count == 1  # cached
