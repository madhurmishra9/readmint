import pytest

from app.cortex_client import cortex, _default_stub


@pytest.fixture(autouse=True)
def reset_stub():
    """Each test starts with the identity (no-loss) stub responder."""
    cortex.set_stub_responder(_default_stub)
    yield
    cortex.set_stub_responder(_default_stub)
