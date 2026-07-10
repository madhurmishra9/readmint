from app.core import version_sync


def test_extract_claims_basic():
    md = "Requires Python 3.10+ and Node.js 18.\n"
    claims = version_sync.extract_claims(md)
    tools = {c["tool"] for c in claims}
    assert tools == {"python", "node"}


def test_parse_pyproject():
    content = '[project]\nrequires-python = ">=3.11"\n'
    declared = version_sync.parse_manifest("pyproject.toml", content)
    assert declared == {"python": "3.11"}


def test_parse_package_json():
    content = '{"engines": {"node": ">=18.0.0"}}'
    declared = version_sync.parse_manifest("package.json", content)
    assert declared == {"node": "18.0.0"}


def test_parse_go_mod():
    content = "module example.com/x\n\ngo 1.21\n"
    declared = version_sync.parse_manifest("go.mod", content)
    assert declared == {"go": "1.21"}


def test_parse_cargo_toml():
    content = '[package]\nrust-version = "1.70"\n'
    declared = version_sync.parse_manifest("Cargo.toml", content)
    assert declared == {"rust": "1.70"}


def test_check_flags_mismatch():
    md = "Requires Python 3.9+.\n"
    manifests = {"pyproject.toml": 'requires-python = ">=3.11"\n'}
    r = version_sync.check(md, manifests)
    assert r["checked"] == 1
    assert len(r["mismatches"]) == 1
    assert r["mismatches"][0]["manifest_version"] == "3.11"


def test_check_matches_no_mismatch():
    md = "Requires Python 3.11+.\n"
    manifests = {"pyproject.toml": 'requires-python = ">=3.11"\n'}
    r = version_sync.check(md, manifests)
    assert r["mismatches"] == []


def test_check_patch_version_ignored():
    md = "Requires Node 18+.\n"
    manifests = {"package.json": '{"engines": {"node": ">=18.4.2"}}'}
    r = version_sync.check(md, manifests)
    assert r["mismatches"] == []


def test_check_no_manifest_no_mismatch():
    md = "Requires Python 3.9+.\n"
    r = version_sync.check(md, {})
    assert r["mismatches"] == []
    assert r["checked"] == 1


def test_malformed_manifest_ignored():
    declared = version_sync.parse_manifest("package.json", "not json")
    assert declared == {}
