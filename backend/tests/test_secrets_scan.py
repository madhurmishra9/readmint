from app.core import secrets_scan as ss


def test_high_severity_blocks():
    md = "Here is a key AKIAIOSFODNN7EXAMPLE in the config."
    f = ss.scan(md)
    assert f.blocking
    assert any(i["type"] == "aws_access_key" and i["severity"] == "high" for i in f.items)


def test_github_token_high():
    md = "token: ghp_" + "a" * 36
    f = ss.scan(md)
    assert f.blocking


def test_private_key_high():
    f = ss.scan("-----BEGIN RSA PRIVATE KEY-----\nMII...\n")
    assert f.blocking


def test_generic_secret_medium_not_blocking():
    f = ss.scan('API_KEY = "swordfish12345"')
    assert not f.blocking
    assert any(i["type"] == "generic_secret" for i in f.items)


def test_clean_doc_no_findings():
    f = ss.scan("# Title\n\nJust prose and a `pip install foo` command.")
    assert f.items == []
    assert not f.blocking


def test_match_is_masked():
    f = ss.scan("AKIAIOSFODNN7EXAMPLE")
    item = f.items[0]
    assert "IOSFODNN7" not in item["match"]
    assert item["match"].startswith("AKIA")


def test_line_numbers_reported():
    md = "line1\nline2\nAKIAIOSFODNN7EXAMPLE\n"
    f = ss.scan(md)
    assert f.items[0]["line"] == 3


def test_high_entropy_string_flagged():
    secret = "ZmFrZS1zZWNyZXQtdmFsdWUtMTIzNDU2Nzg5MA=="  # base64-ish, 40 chars
    f = ss.scan(f'config = "{secret}"')
    assert any(i["type"] == "high_entropy_string" for i in f.items)


def test_redact_preserves_generic_secret_label():
    out = ss.redact('API_KEY = "swordfish12345"')
    assert "API_KEY" in out
    assert "swordfish12345" not in out
    assert ss.REDACTION in out


def test_redact_removes_aws_key():
    out = ss.redact("key AKIAIOSFODNN7EXAMPLE here")
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert ss.REDACTION in out


def test_email_medium_severity():
    f = ss.scan("Contact dev@example.com")
    assert any(i["type"] == "email" and i["severity"] == "medium" for i in f.items)
    assert not f.blocking
