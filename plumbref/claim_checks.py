from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from plumbref.models import detect_broad_language


class ClaimCheckError(ValueError):
    pass


def render_claim_check(
    *,
    claims_path: Path,
    repo_root: Path,
    diff_target: str | None = None,
    diff_path: Path | None = None,
) -> str:
    claims = parse_claims_file(claims_path)
    changed_files = changed_files_for_inputs(repo_root=repo_root, diff_target=diff_target, diff_path=diff_path)
    results = [check_claim_against_diff(claim, changed_files) for claim in claims]
    return render_claim_check_markdown(
        claims_path=claims_path,
        diff_label=str(diff_path or diff_target or "worktree"),
        changed_files=changed_files,
        results=results,
    )


def parse_claims_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ClaimCheckError(f"could not read claims file {path}: {exc}") from exc
    claims: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        if line:
            claims.append(line)
    if not claims:
        raise ClaimCheckError(f"{path} does not contain any claims")
    return claims


def changed_files_for_inputs(
    *,
    repo_root: Path,
    diff_target: str | None,
    diff_path: Path | None,
) -> list[str]:
    if diff_path:
        return changed_files_from_diff(diff_path)
    target = diff_target or "HEAD"
    completed = subprocess.run(
        ["git", "diff", "--name-only", target],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ClaimCheckError(completed.stderr.strip() or f"git diff failed for {target}")
    return dedupe([line.strip() for line in completed.stdout.splitlines() if line.strip()])


def changed_files_from_diff(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ClaimCheckError(f"could not read diff {path}: {exc}") from exc
    files: list[str] = []
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line.removeprefix("+++ b/"))
        elif line.startswith("--- a/"):
            files.append(line.removeprefix("--- a/"))
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3].removeprefix("b/"))
    return dedupe([file for file in files if file and file != "/dev/null"])


def check_claim_against_diff(claim: str, changed_files: list[str]) -> dict[str, Any]:
    normalized = claim.lower()
    risky_terms = detect_broad_language(claim)
    non_docs = [file for file in changed_files if not is_docs_or_copy_file(file)]
    docs = [file for file in changed_files if is_docs_or_copy_file(file)]
    result = {
        "claim": claim,
        "status": "not_ready",
        "risky_terms": risky_terms,
        "evidence": [],
        "unchecked": [
            "Run Plumbref verification against source evidence before relying on this claim.",
        ],
        "safer_wording": "",
    }
    if claims_only_docs_or_copy(normalized) and non_docs:
        result["status"] = "contradicted"
        result["evidence"] = [f"Changed non-doc/copy file: {file}" for file in non_docs[:6]]
        result["safer_wording"] = (
            "The diff includes documentation/copy changes and code or config changes; "
            "do not describe it as docs/copy only."
        )
        result["unchecked"] = [
            "Downstream behavior still needs a source-backed Plumbref check.",
        ]
    elif risky_terms:
        result["status"] = "needs_verification"
        result["unchecked"] = [
            f"Broad language detected: {', '.join(risky_terms)}.",
            "Record required searches, contradiction searches, and evidence snippets before relying on this.",
        ]
    elif docs and not non_docs:
        result["status"] = "plausible_but_unverified"
        result["evidence"] = [f"Changed doc/copy file: {file}" for file in docs[:6]]
        result["unchecked"] = [
            "This is based on changed-file paths only, not source evidence.",
        ]
    return result


def claims_only_docs_or_copy(normalized: str) -> bool:
    return bool(
        re.search(r"\bonly\b", normalized)
        and any(term in normalized for term in ("doc", "docs", "documentation", "copy", "text", "readme"))
    )


def is_docs_or_copy_file(path: str) -> bool:
    lowered = path.lower()
    suffixes = (".md", ".mdx", ".txt", ".rst")
    if lowered.endswith(suffixes):
        return True
    return lowered.startswith(("docs/", "documentation/"))


def render_claim_check_markdown(
    *,
    claims_path: Path,
    diff_label: str,
    changed_files: list[str],
    results: list[dict[str, Any]],
) -> str:
    contradicted = [item for item in results if item["status"] == "contradicted"]
    needs_verification = [item for item in results if item["status"] == "needs_verification"]
    not_ready = [item for item in results if item["status"] == "not_ready"]
    plausible = [item for item in results if item["status"] == "plausible_but_unverified"]
    lines = [
        "# Plumbref Advisory Claim Check",
        "",
        f"Claims file: `{claims_path}`",
        f"Diff: `{diff_label}`",
        f"Changed files: {len(changed_files)}",
        "",
        "This is advisory. It checks risky wording against the diff and identifies claims "
        "that need Plumbref verification.",
    ]
    lines.extend(render_result_section("Do Not Rely On", contradicted))
    lines.extend(render_result_section("Needs Verification", needs_verification))
    lines.extend(render_result_section("Plausible But Unverified", plausible))
    lines.extend(render_result_section("Not Ready", not_ready))
    if not results:
        lines.extend(["", "No claims checked."])
    return "\n".join(lines).strip() + "\n"


def render_result_section(title: str, items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return []
    lines = ["", f"## {title}"]
    for item in items:
        lines.append(f"- {item['claim']}")
        if item.get("risky_terms"):
            lines.append(f"  - Risky language: {', '.join(item['risky_terms'])}")
        for evidence in item.get("evidence", [])[:6]:
            lines.append(f"  - Evidence: {evidence}")
        if item.get("safer_wording"):
            lines.append(f"  - Safer wording: {item['safer_wording']}")
        for unchecked in item.get("unchecked", [])[:3]:
            lines.append(f"  - Unchecked: {unchecked}")
    return lines


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
