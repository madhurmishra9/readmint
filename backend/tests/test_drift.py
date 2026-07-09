from app.core import drift


def test_extract_inline_code_reference():
    md = "Run `cli/readmint_cli.py refine README.md`.\n"
    refs = drift.extract_references(md)
    assert "cli/readmint_cli.py" in refs


def test_extract_fenced_code_reference():
    md = "```bash\npython backend/app/main.py\n```\n"
    refs = drift.extract_references(md)
    assert "backend/app/main.py" in refs


def test_extract_relative_markdown_link():
    md = "See [the docs](docs/templates/README.md) for details.\n"
    refs = drift.extract_references(md)
    assert "docs/templates/README.md" in refs


def test_extract_ignores_urls_and_owner_repo():
    md = "See https://example.com/a/b and clone acme/widgets.\n"
    refs = drift.extract_references(md)
    assert not any(r.startswith("http") for r in refs)


def test_check_flags_missing_file():
    md = "Run `scripts/build.sh` to build.\n"
    r = drift.check(md, existing_paths=["README.md", "src/main.py"])
    assert r["checked"] == 1
    assert "scripts/build.sh" in r["missing"]


def test_check_passes_when_file_exists():
    md = "Run `cli/readmint_cli.py` to refine.\n"
    r = drift.check(md, existing_paths=["cli/readmint_cli.py", "README.md"])
    assert r["missing"] == []


def test_check_directory_reference_ok_if_nonempty():
    md = "See the [templates](docs/templates) folder.\n"
    r = drift.check(md, existing_paths=["docs/templates/README.md"])
    assert r["missing"] == []


def test_check_empty_doc():
    r = drift.check("", existing_paths=["README.md"])
    assert r == {"checked": 0, "missing": []}
