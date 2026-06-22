#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
review_root="$repo_root/reviews"
prompt_dir="$review_root/prompts"
packet_dir="$review_root/packet"
out_dir="$review_root/out"

codex_bin="${CODEX_BIN:-codex}"
sandbox="${CODEX_SANDBOX:-read-only}"
model_args=()
if [[ -n "${CODEX_MODEL:-}" ]]; then
  model_args=(-m "$CODEX_MODEL")
fi

independent_reviewers=(
  "00-blind-readme"
  "01-technical-trust"
  "02-user-value"
  "03-positioning"
  "04-alternatives"
  "05-first-run-friction"
)
synthesis_reviewer="06-synthesis"

usage() {
  cat <<'USAGE'
Usage:
  reviews/run.sh [reviewer ...]

Examples:
  reviews/run.sh
  reviews/run.sh 00-blind-readme 01-technical-trust

Environment:
  CODEX_BIN       Codex executable path. Defaults to codex.
  CODEX_MODEL     Optional model override passed to codex exec -m.
  CODEX_SANDBOX   Sandbox mode. Defaults to read-only.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

selected=("$@")
if [[ ${#selected[@]} -eq 0 ]]; then
  selected=("${independent_reviewers[@]}" "$synthesis_reviewer")
fi

contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

is_independent() {
  contains "$1" "${independent_reviewers[@]}"
}

include_packet() {
  [[ "$1" != "00-blind-readme" && "$1" != "$synthesis_reviewer" ]]
}

validate_reviewers() {
  local reviewer
  for reviewer in "${selected[@]}"; do
    if ! is_independent "$reviewer" && [[ "$reviewer" != "$synthesis_reviewer" ]]; then
      echo "Unknown reviewer: $reviewer" >&2
      exit 2
    fi
    if [[ ! -f "$prompt_dir/$reviewer.md" ]]; then
      echo "Missing prompt: $prompt_dir/$reviewer.md" >&2
      exit 2
    fi
  done
}

render_packet() {
  local file
  printf "\n\n# Review Packet\n"
  printf "Use these notes as supplied context. Verify against the repository when possible.\n"
  for file in "$packet_dir"/*.md; do
    printf "\n\n## %s\n\n" "$(basename "$file")"
    sed -n '1,220p' "$file"
  done
}

render_synthesis_input() {
  local reviewer
  cat "$prompt_dir/$synthesis_reviewer.md"
  printf "\n\n# Independent Review Outputs\n"
  for reviewer in "${independent_reviewers[@]}"; do
    if [[ -f "$tmp_dir/$reviewer.md" ]]; then
      printf "\n\n## %s\n\n" "$reviewer"
      sed -n '1,260p' "$tmp_dir/$reviewer.md"
    elif [[ -n "${previous_out_dir:-}" && -f "$previous_out_dir/$reviewer.md" ]]; then
      printf "\n\n## %s\n\n" "$reviewer"
      sed -n '1,260p' "$previous_out_dir/$reviewer.md"
    elif [[ -f "$out_dir/$reviewer.md" ]]; then
      printf "\n\n## %s\n\n" "$reviewer"
      sed -n '1,260p' "$out_dir/$reviewer.md"
    else
      printf "\n\n## %s\n\nNot available in this run.\n" "$reviewer"
    fi
  done
}

run_reviewer() {
  local reviewer="$1"
  local output="$2"

  echo "==> $reviewer"
  if include_packet "$reviewer"; then
    {
      cat "$prompt_dir/$reviewer.md"
      render_packet
    } | "$codex_bin" exec -C "$repo_root" --sandbox "$sandbox" "${model_args[@]}" \
      -o "$output" -
  else
    "$codex_bin" exec -C "$repo_root" --sandbox "$sandbox" "${model_args[@]}" \
      -o "$output" - < "$prompt_dir/$reviewer.md"
  fi
}

validate_reviewers
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/plumbref-review.XXXXXX")"
previous_out_dir=""
echo "Temporary review directory: $tmp_dir"

selected_has_independent=false
for reviewer in "${selected[@]}"; do
  if is_independent "$reviewer"; then
    selected_has_independent=true
    break
  fi
done

if [[ "$selected_has_independent" == "true" && -d "$out_dir" ]]; then
  previous_out_dir="$tmp_dir/previous-out"
  mv "$out_dir" "$previous_out_dir"
fi

restore_previous_outputs_on_error() {
  local status=$?
  if [[ $status -ne 0 && -n "$previous_out_dir" && -d "$previous_out_dir" ]]; then
    rm -rf "$out_dir"
    mv "$previous_out_dir" "$out_dir"
  fi
  exit "$status"
}

trap restore_previous_outputs_on_error EXIT

for reviewer in "${selected[@]}"; do
  if is_independent "$reviewer"; then
    run_reviewer "$reviewer" "$tmp_dir/$reviewer.md"
  fi
done

if contains "$synthesis_reviewer" "${selected[@]}"; then
  echo "==> $synthesis_reviewer"
  render_synthesis_input | "$codex_bin" exec -C "$repo_root" --sandbox "$sandbox" "${model_args[@]}" \
    -o "$tmp_dir/$synthesis_reviewer.md" -
fi

for reviewer in "${selected[@]}"; do
  if [[ -f "$tmp_dir/$reviewer.md" ]]; then
    mkdir -p "$out_dir"
    cp "$tmp_dir/$reviewer.md" "$out_dir/$reviewer.md"
  fi
done

if [[ -n "$previous_out_dir" && -d "$previous_out_dir" ]]; then
  mkdir -p "$out_dir"
  cp -R "$previous_out_dir"/. "$out_dir"/
  for reviewer in "${selected[@]}"; do
    if [[ -f "$tmp_dir/$reviewer.md" ]]; then
      cp "$tmp_dir/$reviewer.md" "$out_dir/$reviewer.md"
    fi
  done
fi

trap - EXIT

echo
echo "Review outputs written to: $out_dir"
