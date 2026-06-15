from app.core import terminology

GLOSSARY = {"Readmint": ["readmint", "ReadMint", "read-mint"], "Kubernetes": ["k8s"]}


def test_canonicalises_prose():
    out = terminology.normalize("We deployed readmint on k8s.", GLOSSARY)
    assert out == "We deployed Readmint on Kubernetes."


def test_does_not_touch_code_blocks():
    md = "Run readmint.\n\n```\nreadmint --serve\n```"
    out = terminology.normalize(md, GLOSSARY)
    assert "Run Readmint." in out
    assert "readmint --serve" in out  # code untouched


def test_does_not_touch_inline_code_or_urls():
    md = "Use `readmint` at https://example.com/readmint/docs"
    out = terminology.normalize(md, GLOSSARY)
    assert "`readmint`" in out
    assert "https://example.com/readmint/docs" in out


def test_none_glossary_noop():
    assert terminology.normalize("readmint", None) == "readmint"
