import pytest

from app.config import settings
from app.cortex_client import cortex, _default_stub


@pytest.fixture(autouse=True)
def reset_stub():
    """Each test starts in stub mode with the identity (no-loss) responder, so the
    suite is deterministic even on a machine running a local LLM. Tests that
    exercise the cortex/local providers opt out by monkeypatching ``llm_stub``."""
    prev = settings.llm_stub
    settings.llm_stub = True
    cortex.set_stub_responder(_default_stub)
    yield
    settings.llm_stub = prev
    cortex.set_stub_responder(_default_stub)
