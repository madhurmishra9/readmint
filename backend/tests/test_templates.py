from app.core import scoring, templates
from app import prompts


def test_list_templates_finds_yaml():
    names = templates.list_templates()
    assert "service" in names
    assert "library" in names
    assert "terraform-module" in names


def test_load_terraform_module_template():
    t = templates.load("terraform-module")
    assert t["name"] == "Terraform Module"
    headings = {s["heading"]: s["required"] for s in t["sections"]}
    # terraform-docs/CFT core sections
    assert headings["Inputs"] is True
    assert headings["Outputs"] is True
    assert headings["Requirements"] is True
    assert headings["Usage"] is True
    # Requirements sub-sections present but optional
    assert headings["Service Account"] is False
    assert headings["APIs"] is False


def test_terraform_module_governance_scoring():
    t = templates.load("terraform-module")
    md = (
        "# Cloud Storage Module\n\n"
        "## Usage\n```hcl\nmodule \"x\" { source = \"...\" }\n```\n\n"
        "## Inputs\n| Name | Description |\n|---|---|\n\n"
        "## Outputs\n| Name | Description |\n|---|---|\n"
    )
    s = scoring.score(md, t)
    assert s["mode"] == "template"
    assert s["breakdown"]["Usage"]["passed"]
    assert s["breakdown"]["Inputs"]["passed"]
    assert s["breakdown"]["Outputs"]["passed"]
    assert not s["breakdown"]["Requirements"]["passed"]


def test_load_service_template():
    t = templates.load("service")
    assert t["name"] == "Internal Service"
    headings = [s["heading"] for s in t["sections"]]
    assert "Runbook" in headings
    assert all("required" in s for s in t["sections"])


def test_readme_templates_default_doc_type():
    t = templates.load("service")
    assert t["doc_type"] == "readme"


def test_companion_templates_have_doc_type():
    assert templates.load("contributing")["doc_type"] == "contributing"
    assert templates.load("security")["doc_type"] == "security"
    assert templates.load("code-of-conduct")["doc_type"] == "code_of_conduct"


def test_list_templates_filters_by_doc_type():
    contributing = templates.list_templates(doc_type="contributing")
    assert contributing == ["contributing"]
    readme = templates.list_templates(doc_type="readme")
    assert "service" in readme
    assert "contributing" not in readme


def test_list_doc_types_includes_companions():
    doc_types = templates.list_doc_types()
    assert {"readme", "contributing", "security", "code_of_conduct"} <= set(doc_types)


def test_security_template_governance_scoring():
    t = templates.load("security")
    md = "# Security\n\n## Supported Versions\nv2.x\n\n## Reporting a Vulnerability\nEmail us.\n"
    s = scoring.score(md, t)
    assert s["mode"] == "template"
    assert s["breakdown"]["Supported Versions"]["passed"]
    assert not s["breakdown"]["Contact"]["passed"]


def test_load_missing_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        templates.load("does-not-exist")


def test_template_governance_scoring():
    t = templates.load("service")
    md = "# Svc\n\n## Overview\nx\n## Runbook\ny\n"
    s = scoring.score(md, t)
    assert s["mode"] == "template"
    assert s["breakdown"]["Overview"]["passed"]
    assert not s["breakdown"]["Deployment"]["passed"]


def test_system_prompt_includes_template_sections():
    t = templates.load("service")
    sysprompt = prompts.system_for(t)
    assert "Internal Service" in sysprompt
    assert "Runbook (required)" in sysprompt
    # base rules still present
    assert "NEVER remove or alter factual content" in sysprompt
