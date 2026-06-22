#!/usr/bin/env bash
#
# Generic upstream skill sync script.
#
# Downloads skill directories from upstream GitHub or GitLab repos (via tarball)
# and installs them into skills/system/<name>/. Reads the skill list and config
# from config/upstream-skills.json. The optional per-skill "host" field selects
# the tarball URL scheme (github.com by default, or a GitLab host).
#
# For each skill the script:
#   1. Downloads the repo tarball (one per unique repo, cached in tmpdir)
#   2. Extracts the skill directory from the tarball
#   3. Patches SKILL.md frontmatter with any overrides from the manifest
#   4. Appends custom-sections.md (if present) to SKILL.md
#   5. Preserves local-only files (custom-sections.md, evals/)
#
# Usage:
#   ./scripts/sync-skill.sh <name>           # sync a single skill
#   ./scripts/sync-skill.sh <name> --check   # dry-run: exit 1 if stale
#   ./scripts/sync-skill.sh --all            # sync all skills
#   ./scripts/sync-skill.sh --all --check    # dry-run for all skills
#
# Requires: bash 4+, jq, curl, tar

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
MANIFEST="${REPO_ROOT}/config/upstream-skills.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required but not installed."
}

require_cmd jq
require_cmd curl

# ---------------------------------------------------------------------------
# Manifest validation (structural checks via jq)
# ---------------------------------------------------------------------------

validate_manifest() {
  [[ -f "$MANIFEST" ]] || die "Manifest not found: ${MANIFEST}"

  jq -e '.skills | type == "array" and length > 0' "$MANIFEST" >/dev/null 2>&1 \
    || die "Manifest must contain a non-empty 'skills' array."

  local errors
  errors=$(jq -r '
    .skills | to_entries[] |
    .key as $i | .value |
    (if .name  | type != "string" or length == 0 then "skills[\($i)]: missing or empty \"name\""  else empty end),
    (if .repo  | type != "string" or length == 0 then "skills[\($i)]: missing or empty \"repo\""  else empty end),
    (if .path  | type != "string" or length == 0 then "skills[\($i)]: missing or empty \"path\""  else empty end),
    (if .repo  | type == "string" and (test("^[^/]+(/[^/]+)+$") | not) then "skills[\($i)]: \"repo\" must be owner/repo (GitHub) or a slash-separated path (GitLab)" else empty end)
  ' "$MANIFEST" 2>&1)

  if [[ -n "$errors" ]]; then
    die "Manifest validation failed:\n${errors}"
  fi
}

validate_manifest

# ---------------------------------------------------------------------------
# Tarball cache — one download per unique repo+ref
# ---------------------------------------------------------------------------

declare -A TARBALL_CACHE  # key: "repo@ref" -> path to extracted dir

download_tarball() {
  local repo="$1" ref="$2" host="$3"
  local cache_key="${host}/${repo}@${ref}"

  if [[ -n "${TARBALL_CACHE[$cache_key]:-}" ]]; then
    return
  fi

  # Sanitize ref for filesystem use (e.g. "release/1.2" -> "release_1.2")
  local safe_ref="${ref//\//_}"
  local tarball="${TMPDIR_ROOT}/${host//\//_}_${repo//\//_}_${safe_ref}.tar.gz"
  local extract_dir="${TMPDIR_ROOT}/${host//\//_}_${repo//\//_}_${safe_ref}"

  # Build the tarball URL by host. Both schemes accept branches and tags.
  # The extracted top-level dir name varies (GitLab appends a short SHA), but
  # --strip-components=1 drops it regardless of name.
  local url
  case "$host" in
    github.com)
      url="https://github.com/${repo}/archive/${ref}.tar.gz"
      ;;
    *)
      url="https://${host}/${repo}/-/archive/${ref}/${repo##*/}-${ref}.tar.gz"
      ;;
  esac

  printf 'Downloading %s/%s@%s...\n' "$host" "$repo" "$ref"
  if ! curl -sSfL "$url" -o "$tarball"; then
    die "Failed to download tarball from ${url}"
  fi

  mkdir -p "$extract_dir"
  tar -xzf "$tarball" -C "$extract_dir" --strip-components=1

  TARBALL_CACHE[$cache_key]="$extract_dir"
}

get_tarball_dir() {
  local repo="$1" ref="$2" host="$3"
  printf '%s' "${TARBALL_CACHE[${host}/${repo}@${ref}]}"
}

# ---------------------------------------------------------------------------
# Frontmatter patching
# ---------------------------------------------------------------------------

# Reads upstream SKILL.md, applies frontmatter_overrides, returns the patched
# frontmatter (including --- delimiters) followed by the body.
patch_skill_md() {
  local upstream_skill_md="$1"
  local overrides_json="$2"  # JSON object or "null"

  # Use awk to split into frontmatter and body at the second --- delimiter.
  # Frontmatter lines go to fd 3, body goes to stdout.
  local fm_file="${TMPDIR_ROOT}/fm_$$"
  local body_file="${TMPDIR_ROOT}/body_$$"
  awk '
    BEGIN { delim = 0 }
    /^---[[:space:]]*$/ {
      delim++
      if (delim <= 2) next
    }
    { if (delim < 2) print > "'"$fm_file"'"; else print > "'"$body_file"'" }
  ' "$upstream_skill_md"

  # Read frontmatter lines into array
  local frontmatter_lines=()
  if [[ -f "$fm_file" ]]; then
    while IFS= read -r line; do
      frontmatter_lines+=("$line")
    done < "$fm_file"
    rm -f "$fm_file"
  fi

  # If no overrides, emit the original frontmatter as-is
  if [[ "$overrides_json" == "null" ]] || [[ -z "$overrides_json" ]]; then
    printf '%s\n' "---"
    for fm_line in "${frontmatter_lines[@]}"; do
      printf '%s\n' "$fm_line"
    done
    printf '%s\n\n' "---"
    [[ -f "$body_file" ]] && cat "$body_file"
    rm -f "$body_file"
    return
  fi

  # Build a list of override keys
  local override_keys=()
  while IFS= read -r k; do
    override_keys+=("$k")
  done < <(printf '%s' "$overrides_json" | jq -r 'keys[]')

  # Parse existing frontmatter into an ordered list of key-value pairs.
  # We handle simple "key: value" and multi-line block scalars (>-, |, etc.)
  local patched_fm=()
  local current_key=""
  local skip_continuation=false

  for fm_line in "${frontmatter_lines[@]}"; do
    # Check if this is a new key (not indented, contains colon)
    if [[ "$fm_line" =~ ^([a-zA-Z_-]+):[[:space:]]*(.*) ]]; then
      current_key="${BASH_REMATCH[1]}"

      # Check if this key has an override
      local override_value
      override_value=$(printf '%s' "$overrides_json" | jq -r --arg k "$current_key" '.[$k] // empty')

      if [[ -n "$override_value" ]]; then
        # Check if the value needs multi-line YAML (contains quotes or is long)
        if [[ ${#override_value} -gt 80 ]] || [[ "$override_value" == *'"'* ]]; then
          patched_fm+=("${current_key}: >-")
          # Word-wrap the value at ~78 chars with 2-space indent
          while IFS= read -r wrap_line || [[ -n "$wrap_line" ]]; do
            patched_fm+=("  ${wrap_line}")
          done < <(printf '%s' "$override_value" | fold -s -w 76)
        else
          patched_fm+=("${current_key}: ${override_value}")
        fi
        skip_continuation=true
      else
        patched_fm+=("$fm_line")
        skip_continuation=false
      fi
    elif [[ "$fm_line" =~ ^[[:space:]] ]]; then
      # Continuation line (indented) — belongs to current_key
      if ! $skip_continuation; then
        patched_fm+=("$fm_line")
      fi
    else
      patched_fm+=("$fm_line")
      skip_continuation=false
    fi
  done

  # Add any override keys that weren't in the original frontmatter
  for key in "${override_keys[@]}"; do
    local found=false
    for fm_line in "${frontmatter_lines[@]}"; do
      if [[ "$fm_line" == "${key}:"* ]]; then
        found=true
        break
      fi
    done
    if ! $found; then
      local override_value
      override_value=$(printf '%s' "$overrides_json" | jq -r --arg k "$key" '.[$k]')
      if [[ ${#override_value} -gt 80 ]] || [[ "$override_value" == *'"'* ]]; then
        patched_fm+=("${key}: >-")
        while IFS= read -r wrap_line || [[ -n "$wrap_line" ]]; do
          patched_fm+=("  ${wrap_line}")
        done < <(printf '%s' "$override_value" | fold -s -w 76)
      else
        patched_fm+=("${key}: ${override_value}")
      fi
    fi
  done

  # Emit patched SKILL.md
  printf '%s\n' "---"
  for fm_line in "${patched_fm[@]}"; do
    printf '%s\n' "$fm_line"
  done
  printf '%s\n\n' "---"
  [[ -f "$body_file" ]] && cat "$body_file"
  rm -f "$body_file"
}

# ---------------------------------------------------------------------------
# Sync a single skill
# ---------------------------------------------------------------------------

sync_skill() {
  local skill_name="$1"
  local check_mode="${2:-false}"

  # Read skill config from manifest
  local skill_json
  skill_json=$(jq -r --arg name "$skill_name" '.skills[] | select(.name == $name)' "$MANIFEST")

  if [[ -z "$skill_json" ]]; then
    die "Skill '${skill_name}' not found in manifest."
  fi

  local repo ref path host overrides_json
  repo=$(echo "$skill_json" | jq -r '.repo')
  ref=$(echo "$skill_json" | jq -r '.ref // "main"')
  path=$(echo "$skill_json" | jq -r '.path')
  host=$(echo "$skill_json" | jq -r '.host // "github.com"')
  overrides_json=$(echo "$skill_json" | jq '.frontmatter_overrides // null')

  local target_dir="${REPO_ROOT}/skills/system/${skill_name}"
  local custom_sections="${target_dir}/custom-sections.md"
  local build_dir="${TMPDIR_ROOT}/build_${skill_name}"

  # Download tarball if not cached
  download_tarball "$repo" "$ref" "$host"
  local tarball_dir
  tarball_dir=$(get_tarball_dir "$repo" "$ref" "$host")

  local upstream_dir="${tarball_dir}/${path}"
  if [[ ! -d "$upstream_dir" ]]; then
    die "Path '${path}' not found in ${host}/${repo}@${ref} tarball."
  fi

  printf 'Syncing %s from %s/%s@%s:%s...\n' "$skill_name" "$host" "$repo" "$ref" "$path"

  # Build into temp directory
  mkdir -p "$build_dir"

  # Copy all upstream files
  cp -a "$upstream_dir"/. "$build_dir"/

  # Patch SKILL.md frontmatter + append custom sections
  if [[ -f "$build_dir/SKILL.md" ]]; then
    local patched
    patched=$(patch_skill_md "$build_dir/SKILL.md" "$overrides_json")

    # Append custom sections if they exist locally
    if [[ -f "$custom_sections" ]] && [[ -s "$custom_sections" ]]; then
      patched+=$'\n'
      patched+=$(cat "$custom_sections")
      patched+=$'\n'
    fi

    printf '%s\n' "$patched" > "$build_dir/SKILL.md"
  fi

  # --check mode: compare build vs local
  if [[ "$check_mode" == "true" ]]; then
    local changed=false

    if [[ ! -d "$target_dir" ]]; then
      printf '  %s: target directory does not exist.\n' "$skill_name"
      changed=true
    else
      # Compare all files from build against target (new/modified)
      while IFS= read -r -d '' file; do
        local rel="${file#$build_dir/}"
        local local_file="${target_dir}/${rel}"

        if [[ ! -f "$local_file" ]]; then
          printf '  %s: %s does not exist locally.\n' "$skill_name" "$rel"
          changed=true
        elif ! diff -q "$file" "$local_file" > /dev/null 2>&1; then
          printf '  %s: %s differs.\n' "$skill_name" "$rel"
          changed=true
        fi
      done < <(find "$build_dir" -type f -print0)

      # Detect stale files in target that no longer exist upstream
      # (excluding preserved local-only paths)
      while IFS= read -r -d '' file; do
        local rel="${file#$target_dir/}"
        case "$rel" in
          custom-sections.md | evals | evals/*) continue ;;
        esac
        if [[ ! -f "${build_dir}/${rel}" ]]; then
          printf '  %s: %s is stale (removed upstream).\n' "$skill_name" "$rel"
          changed=true
        fi
      done < <(find "$target_dir" -type f -print0)
    fi

    if $changed; then
      printf '  %s: OUT OF DATE\n' "$skill_name"
      return 1
    else
      printf '  %s: up to date\n' "$skill_name"
      return 0
    fi
  fi

  # Sync mode: preserve local-only files, then copy build over
  mkdir -p "$target_dir"

  # Save local-only files to temp
  local preserve_dir="${TMPDIR_ROOT}/preserve_${skill_name}"
  mkdir -p "$preserve_dir"

  for preserve in custom-sections.md evals; do
    if [[ -e "${target_dir}/${preserve}" ]]; then
      cp -a "${target_dir}/${preserve}" "${preserve_dir}/${preserve}"
    fi
  done

  # Wipe target directory (except preserved paths) so files removed upstream
  # don't accumulate as stale artifacts.
  while IFS= read -r -d '' path; do
    local rel="${path#$target_dir/}"
    case "$rel" in
      custom-sections.md | evals | evals/*) continue ;;
    esac
    rm -rf -- "$path"
  done < <(find "$target_dir" -mindepth 1 -maxdepth 1 -print0)

  # Copy built files
  cp -a "$build_dir"/. "$target_dir"/

  # Restore preserved files
  # Remove the destination first: if it already exists (e.g. evals/ was never
  # wiped because it's in the skip list), cp -a would nest the source inside
  # the existing directory instead of replacing it, creating evals/evals/.
  for preserve in custom-sections.md evals; do
    if [[ -e "${preserve_dir}/${preserve}" ]]; then
      rm -rf "${target_dir:?}/${preserve}"
      cp -a "${preserve_dir}/${preserve}" "${target_dir}/${preserve}"
    fi
  done

  printf '  %s: synced to %s\n' "$skill_name" "$target_dir"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

check_mode=false
sync_all=false
skill_name=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) check_mode=true; shift ;;
    --all)   sync_all=true; shift ;;
    -*)      die "Unknown option: $1" ;;
    *)       skill_name="$1"; shift ;;
  esac
done

if $sync_all && [[ -n "$skill_name" ]]; then
  die "Cannot specify both --all and a skill name."
fi

if ! $sync_all && [[ -z "$skill_name" ]]; then
  die "Usage: $0 <name> [--check] | --all [--check]"
fi

any_stale=false

if $sync_all; then
  while IFS= read -r name; do
    if ! sync_skill "$name" "$check_mode"; then
      any_stale=true
    fi
  done < <(jq -r '.skills[].name' "$MANIFEST")
else
  if ! sync_skill "$skill_name" "$check_mode"; then
    any_stale=true
  fi
fi

if $check_mode && $any_stale; then
  printf '\nOne or more skills are out of date.\n'
  exit 1
elif $check_mode; then
  printf '\nAll skills up to date.\n'
fi

printf '\nDone.\n'
