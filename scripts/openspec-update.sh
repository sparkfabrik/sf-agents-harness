#!/usr/bin/env bash
#
# Regenerate the OpenSpec commands and skills checked into this repository.
#
# The generated trees depend on the global OpenSpec CLI profile, which is pinned
# in config/openspec-profile.json. This script applies that profile to the global
# config (merging, never replacing) and runs the latest published CLI, so the
# output does not depend on personal settings or on a locally installed version.
#
# Usage:
#   ./scripts/openspec-update.sh           # regenerate in place
#   ./scripts/openspec-update.sh --check   # dry-run: exit 1 if the tree is stale
#   ./scripts/openspec-update.sh --paths   # print the generated trees and exit

set -euo pipefail

readonly PROFILE="config/openspec-profile.json"
readonly PACKAGE="@fission-ai/openspec@latest"

# Trees written by `openspec update`. Keep in sync with the tools configured in
# the repository (Claude Code, GitHub Copilot, OpenCode).
readonly GENERATED_PATHS=(
  ".claude/commands/opsx"
  ".claude/skills"
  ".github/prompts"
  ".github/skills"
  ".opencode/commands"
  ".opencode/skills"
)

check_only=false
for argument in "$@"; do
  case "$argument" in
    --check) check_only=true ;;
    --paths)
      printf '%s\n' "${GENERATED_PATHS[@]}"
      exit 0
      ;;
    *)
      echo "error: unknown argument: $argument" >&2
      exit 2
      ;;
  esac
done

for tool in jq npx git; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: $tool is required" >&2
    exit 2
  fi
done

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

config_home="${XDG_CONFIG_HOME:-$HOME/.config}/openspec"
config_file="$config_home/config.json"
mkdir -p "$config_home"

# Merge the pinned keys into the existing config so personal settings this
# repository does not pin (feature flags, unrelated keys) are preserved.
existing_config="{}"
if [[ -f "$config_file" ]]; then
  existing_config=$(cat "$config_file")
fi
jq -s '.[0] * .[1]' <(printf '%s' "$existing_config") "$PROFILE" >"$config_file.tmp"
mv "$config_file.tmp" "$config_file"

echo "Regenerating OpenSpec files with $PACKAGE"
npx --yes "$PACKAGE" update --force

if [[ "$check_only" != true ]]; then
  exit 0
fi

stale=$(
  {
    git diff --name-only -- "${GENERATED_PATHS[@]}"
    git ls-files --others --exclude-standard -- "${GENERATED_PATHS[@]}"
  } | sort -u
)

if [[ -n "$stale" ]]; then
  echo "error: OpenSpec generated files are stale. Run ./scripts/openspec-update.sh" >&2
  printf '%s\n' "$stale" >&2
  exit 1
fi

echo "OpenSpec generated files are up to date"
