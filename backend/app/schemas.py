"""Pydantic request/response models for the API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RefineOptions(BaseModel):
    template: Optional[str] = None
    check_links: bool = False
    check_style: bool = False
    check_badges: bool = False
    # Needs the repo's real file tree, so it only takes effect on
    # /api/github/refine, which supplies that context.
    check_drift: bool = False
    # Needs manifest content, so it only takes effect on /api/github/refine,
    # which fetches pyproject.toml/package.json/go.mod/Cargo.toml.
    check_version_sync: bool = False
    summary: bool = False
    allow_secrets: bool = False
    redact: bool = False
    model: Optional[str] = None  # override the LLM model (e.g. a local model id)

    def to_opts(self) -> dict:
        return {
            "check_links": self.check_links,
            "check_style": self.check_style,
            "check_badges": self.check_badges,
            "check_drift": self.check_drift,
            "check_version_sync": self.check_version_sync,
            "summary": self.summary,
            "allow_secrets": self.allow_secrets,
            "redact": self.redact,
            "model": self.model,
        }


class ScoreRequest(BaseModel):
    text: str
    template: Optional[str] = None


class BatchItem(BaseModel):
    name: str
    text: str


class BatchListRequest(BaseModel):
    documents: List[BatchItem]
    options: RefineOptions = Field(default_factory=RefineOptions)


class GithubRefineRequest(BaseModel):
    owner: str
    repo: str
    ref: str = "HEAD"
    base: Optional[str] = None  # None ⇒ use the repo's default branch
    open_pr: bool = False
    # Per-request Personal Access Token. When set, the user's own PAT is used to
    # fetch + open the PR (no server-side GitHub App required). Never persisted.
    pat: Optional[str] = Field(default=None, exclude=True, repr=False)
    options: RefineOptions = Field(default_factory=RefineOptions)


class ExportRequest(BaseModel):
    markdown: str
    format: str = "html"  # html | pdf | confluence
    title: str = "README"
    # confluence-only
    space: Optional[str] = None
    parent_id: Optional[str] = None


class RefineResult(BaseModel):
    status: str
    markdown: Optional[str] = None
    verified: Optional[bool] = None
    loss: Optional[Dict[str, List[str]]] = None
    secrets: Optional[Dict[str, Any]] = None
    redacted: Optional[bool] = None
    score: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None
    badges: Optional[Dict[str, Any]] = None
    drift: Optional[Dict[str, Any]] = None
    version_sync: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    retries: Optional[int] = None
    cached: Optional[bool] = None
