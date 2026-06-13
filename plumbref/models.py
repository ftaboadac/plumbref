from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"
    TOO_BROAD = "too_broad"
    NOT_FOUND = "not_found"
    NOT_VERIFIABLE = "not_verifiable"


class ClaimType(StrEnum):
    DEFINITION = "definition"
    BEHAVIOR = "behavior"
    API = "api"
    UI = "ui"
    BUSINESS_RULE = "business_rule"
    IMPACT = "impact"
    RECOMMENDATION = "recommendation"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BudgetMode(StrEnum):
    FAST = "fast"
    NORMAL = "normal"
    DEEP = "deep"


class OutputMode(StrEnum):
    ENGINEER = "engineer"
    SUPPORT = "support"
    JSON = "json"


class ReportPolicy(StrEnum):
    MANUAL = "manual"
    ON_DEMAND = "on_demand"
    ALWAYS = "always"


class VerificationMode(StrEnum):
    EXPLANATION = "explanation"
    SCENARIO = "scenario"
    CHANGE_IMPACT = "change_impact"


class ChangeSource(StrEnum):
    WORKTREE = "worktree"
    DIFF = "diff"
    BRANCH = "branch"
    FILES = "files"


class SearchBudget(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_claims: int = Field(gt=0)
    searches_per_claim: int = Field(gt=0)
    files_per_claim: int = Field(gt=0)
    snippets_per_claim: int = Field(gt=0)
    reference_depth: int = Field(ge=0)


class VerificationTemplate(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    modes: list[VerificationMode] = Field(default_factory=list)
    required_claim_types: list[ClaimType] = Field(default_factory=list)
    required_searches: list[str] = Field(default_factory=list)
    contradiction_searches: list[str] = Field(default_factory=list)
    evidence_categories: list[str] = Field(default_factory=list)
    report_sections: list[str] = Field(default_factory=list)
    unchecked_area_prompts: list[str] = Field(default_factory=list)
    budgets: dict[BudgetMode, SearchBudget] = Field(default_factory=dict)
    source: str = "builtin"

    @field_validator(
        "required_searches",
        "contradiction_searches",
        "evidence_categories",
        "report_sections",
        "unchecked_area_prompts",
    )
    @classmethod
    def reject_blank_template_items(cls, values: list[str]) -> list[str]:
        for value in values:
            if not value.strip():
                raise ValueError("template list items cannot be blank")
        return values


class BudgetUsage(BaseModel):
    searches: int = 0
    files: int = 0
    snippets: int = 0
    reference_depth: int = 0


class CacheStats(BaseModel):
    search_hits: int = 0
    search_misses: int = 0
    evidence_hits: int = 0
    evidence_misses: int = 0
    evidence_reuses: int = 0
    source_text_chars_returned: int = 0


class ChangedSymbol(BaseModel):
    name: str = Field(min_length=1)
    kind: str = "unknown"
    file: str = Field(min_length=1)
    start_line: int | None = Field(default=None, gt=0)
    end_line: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_line_order(self) -> ChangedSymbol:
        if self.start_line is not None and self.end_line is not None and self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ChangeContext(BaseModel):
    source: ChangeSource
    base_ref: str | None = None
    compare_ref: str | None = None
    diff_target: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    changed_symbols: list[ChangedSymbol] = Field(default_factory=list)
    diff_summary: str = ""


class VerificationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    repo_root: Path
    question: str
    answer: str
    mode: VerificationMode = VerificationMode.EXPLANATION
    scenario: str | None = None
    template: VerificationTemplate | None = None
    template_values: dict[str, str] = Field(default_factory=dict)
    change_context: ChangeContext | None = None
    budget_mode: BudgetMode = BudgetMode.NORMAL
    output_modes: list[OutputMode] = Field(default_factory=lambda: [OutputMode.ENGINEER])
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("repo_root")
    @classmethod
    def normalize_repo_root(cls, value: Path) -> Path:
        return value.expanduser().resolve()


class ClaimWorkItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(min_length=1)
    expected_outcome: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    claim_type: ClaimType = ClaimType.UNKNOWN
    entities: list[str] = Field(default_factory=list)
    risk: RiskLevel = RiskLevel.MEDIUM
    absolute_language: list[str] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNCERTAIN
    usage: BudgetUsage = Field(default_factory=BudgetUsage)

    @model_validator(mode="after")
    def detect_absolute_language(self) -> ClaimWorkItem:
        detected = detect_broad_language(self.text)
        existing = [term.lower() for term in self.absolute_language]
        self.absolute_language = list(dict.fromkeys([*existing, *detected]))
        return self


BROAD_LANGUAGE_TERMS = (
    "all",
    "always",
    "every",
    "guarantee",
    "guaranteed",
    "guarantees",
    "never",
    "none",
    "only",
)


def detect_broad_language(text: str) -> list[str]:
    normalized = text.lower()
    return [
        term
        for term in BROAD_LANGUAGE_TERMS
        if re.search(rf"\b{re.escape(term)}\b", normalized)
    ]


class SearchMatch(BaseModel):
    file: str
    line: int = Field(gt=0)
    preview: str


class SearchTrace(BaseModel):
    claim_id: str
    query: str
    command: list[str]
    matched_files: list[str] = Field(default_factory=list)
    matches: list[SearchMatch] = Field(default_factory=list)
    elapsed_ms: int
    truncated: bool = False
    budget_exhausted: bool = False
    cache_hit: bool = False
    cache_key: str | None = None


class EvidenceSnippet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    claim_id: str
    claim_ids: list[str] = Field(default_factory=list)
    file: str
    start_line: int = Field(gt=0)
    end_line: int = Field(gt=0)
    excerpt: str
    excerpt_returned: bool = True
    summary: str = ""
    evidence_category: str | None = None
    sha256: str
    cache_hit: bool = False
    cache_key: str | None = None

    @model_validator(mode="after")
    def validate_line_order(self) -> EvidenceSnippet:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        if not self.claim_ids:
            self.claim_ids = [self.claim_id]
        elif self.claim_id not in self.claim_ids:
            self.claim_ids.insert(0, self.claim_id)
        return self


class Judgment(BaseModel):
    claim_id: str
    status: ClaimStatus
    evidence_ids: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    limits: str = ""
    contradiction_searched: bool = False
    contradiction_notes: str = ""

    @model_validator(mode="after")
    def validate_supported_judgment(self) -> Judgment:
        if self.status == ClaimStatus.SUPPORTED and not self.evidence_ids:
            raise ValueError("supported judgments require at least one evidence id")
        if self.status == ClaimStatus.SUPPORTED and not self.contradiction_searched:
            raise ValueError("supported judgments require a contradiction pass")
        return self


class RenderedReport(BaseModel):
    session_id: str
    verdict: str
    markdown: str
    json_report: dict[str, Any]
    report_written: bool = False
    report_write_reason: str | None = None
    markdown_path: Path | None = None
    json_path: Path | None = None


class SessionState(BaseModel):
    session: VerificationSession
    budget: SearchBudget
    claims: dict[str, ClaimWorkItem] = Field(default_factory=dict)
    traces: list[SearchTrace] = Field(default_factory=list)
    evidence: dict[str, EvidenceSnippet] = Field(default_factory=dict)
    judgments: dict[str, Judgment] = Field(default_factory=dict)
    cache_stats: CacheStats = Field(default_factory=CacheStats)
    repo_state_fingerprint: str | None = None
