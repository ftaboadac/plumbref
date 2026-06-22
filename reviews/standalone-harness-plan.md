# Standalone Review Harness Plan

Status: parked for later.

## Why Extract It

The review process in this repo is useful beyond Plumbref. It should become a
standalone, reusable feedback harness that can run isolated Codex review passes
against any project repository.

The goal is not to create a multi-agent framework. The goal is a boring,
repeatable pipeline:

1. Run independent review passes with no access to each other's outputs.
2. Give each reviewer a narrow skeptical role.
3. Run synthesis only after the independent passes finish.
4. Produce ranked adoption blockers, unsupported claims, and proof artifacts.

## Proposed Shape

```text
repo-review-harness/
  prompts/
    00-blind-readme.md
    01-technical-trust.md
    02-user-value.md
    03-positioning.md
    04-alternatives.md
    05-first-run-friction.md
    06-synthesis.md
  packet-template/
    claim.md
    demo-transcript.md
    example-failure.md
    example-report.md
    alternatives.md
  repo_review/
    cli.py
  README.md
```

Each target project should keep only project-specific context and outputs:

```text
target-project/
  reviews/
    packet/
      claim.md
      demo-transcript.md
      alternatives.md
    out/
```

## Expected CLI

```shell
repo-review run --project /path/to/plumbref
repo-review run --project /path/to/project --packet ./reviews/packet
repo-review run --project . --reviewer 03-positioning
repo-review run --project . --model gpt-5.5
```

Useful options:

- `--project`: repository root to review
- `--packet`: project-specific review packet
- `--out`: output directory
- `--reviewer`: run one or more named reviewers
- `--model`: pass a model override to `codex exec`
- `--sandbox`: default to `read-only`
- `--fresh`: ignore previous outputs
- `--keep-logs`: retain nested Codex logs

## Design Notes

- Keep reviewer prompts generic.
- Keep the packet project-specific.
- Preserve isolation: independent passes must not see previous or sibling
  outputs.
- Let synthesis read all available independent outputs.
- Prefer a Python CLI for the standalone version; shell is fine for the current
  repo spike, but Python will handle config, paths, logs, and errors better.
- Avoid adding CrewAI, LangGraph, or a heavier agent framework until the simple
  deterministic harness is already useful across several projects.

## Migration Steps

1. Copy the current `reviews/prompts/` into a new standalone repo.
2. Turn `reviews/run.sh` into a Python CLI while preserving the same execution
   model.
3. Add a packet template generator.
4. Add tests for reviewer selection, output isolation, synthesis input, and
   error recovery.
5. Use Plumbref as the first integration target.
6. Run the harness against at least two other projects before generalizing more.

## Open Questions

- Should outputs live inside each target repo, outside in a central review
  workspace, or both?
- Should the standalone tool support non-OpenAI models directly, or just expose
  hooks/env vars for alternate commands?
- Should reviewer prompts be versioned so old review outputs are comparable?
- Should the synthesis output include a machine-readable JSON summary?

## Resume Point

When returning to this, start by extracting the current Plumbref `reviews/`
harness into a new repo named something like `repo-review-harness`, keeping the
current shell runner behavior as the reference implementation.
