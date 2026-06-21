import httpx
import respx

from app.core import links


@respx.mock
def test_validate_checks_image_urls_and_skips_code_fence_urls():
    # A badge (image), a real prose link, and a localhost URL inside a code fence.
    md = (
        "# T\n\n"
        "![badge](https://img.shields.io/badge/x-y-green)\n"
        "See https://real.example/docs\n\n"
        "```bash\ncurl http://localhost:8080/skip\n```\n"
    )
    respx.head("https://img.shields.io/badge/x-y-green").mock(return_value=httpx.Response(200))
    respx.head("https://real.example/docs").mock(return_value=httpx.Response(200))

    rep = links.validate(md)

    # Exactly the badge + the prose link are probed; the code-fence localhost URL
    # is not in the target set (if it were, it would be an unmocked 3rd request).
    assert rep["checked"] == 2
    assert rep["broken"] == []


@respx.mock
def test_validate_reports_broken_link():
    md = "# T\n\nbroken https://dead.example/x and ok https://ok.example/y\n"
    respx.head("https://dead.example/x").mock(return_value=httpx.Response(404))
    respx.get("https://dead.example/x").mock(return_value=httpx.Response(404))
    respx.head("https://ok.example/y").mock(return_value=httpx.Response(200))

    rep = links.validate(md)

    assert rep["checked"] == 2
    assert [b["url"] for b in rep["broken"]] == ["https://dead.example/x"]
