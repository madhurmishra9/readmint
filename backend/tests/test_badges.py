from app.core import badges


def test_extract_ignores_non_shields_images():
    md = "![screenshot](https://example.com/shot.png)\n"
    assert badges.extract(md) == []


def test_extract_finds_shields_badge():
    md = "![license](https://img.shields.io/badge/license-MIT-blue)\n"
    out = badges.extract(md)
    assert len(out) == 1
    assert out[0]["url"].startswith("https://img.shields.io")


def test_static_license_badge_matches_expected():
    md = "![license](https://img.shields.io/badge/license-MIT-blue)\n"
    r = badges.validate(md, expected_license="MIT")
    assert r["checked"] == 1
    assert r["stale"] == []


def test_static_license_badge_stale():
    md = "![license](https://img.shields.io/badge/license-Apache--2.0-blue)\n"
    r = badges.validate(md, expected_license="MIT")
    assert r["checked"] == 1
    assert len(r["stale"]) == 1
    assert "MIT" in r["stale"][0]["reason"]


def test_static_version_badge_stale():
    md = "![version](https://img.shields.io/badge/version-v1.2.0-brightgreen)\n"
    r = badges.validate(md, expected_version="1.3.0")
    assert len(r["stale"]) == 1


def test_static_version_badge_matches_ignoring_leading_v():
    md = "![version](https://img.shields.io/badge/version-v1.3.0-brightgreen)\n"
    r = badges.validate(md, expected_version="1.3.0")
    assert r["stale"] == []


def test_dynamic_badge_never_flagged():
    md = "![license](https://img.shields.io/github/license/acme/widgets)\n"
    r = badges.validate(md, expected_license="Apache-2.0")
    assert r["checked"] == 1
    assert r["stale"] == []


def test_static_v1_query_form():
    md = "![custom](https://img.shields.io/static/v1?label=license&message=MIT&color=blue)\n"
    r = badges.validate(md, expected_license="Apache-2.0")
    assert len(r["stale"]) == 1


def test_no_badges():
    r = badges.validate("# just a title\n")
    assert r == {"checked": 0, "badges": [], "stale": []}
