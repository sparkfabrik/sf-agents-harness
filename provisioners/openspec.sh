#!/usr/bin/env bash
set -euo pipefail

# OpenSpec provisioner — installs OpenSpec skills and commands globally for
# Claude Code, keeping them in sync with the installed CLI.
#
# OpenSpec skills/commands are NOT vendored as static files: their bodies are
# compiled into the `openspec` binary and change between versions. Vendoring a
# snapshot drifts from the CLI and the skills (thin orchestration over CLI
# verbs) start telling the agent to run commands that no longer exist. Instead
# this provisioner GENERATES them from the locally installed CLI and refreshes
# on every sync, so the skills always match the binary — zero drift.
#
# Strategy: generate into a staging workspace under the cache dir (so the
# OpenSpec workspace, which `init`/`update` require, never pollutes $HOME and
# the generated AGENTS.md/CLAUDE.md instruction files never overwrite the
# user's global ones), then symlink the generated skills and commands into
# Claude Code's global directories. Symlinks mean a later `openspec update` of
# the staging area is picked up with no redeploy.
#
# Contract (shared by all harness provisioners):
#   sync       generate + (re)link into global tool dirs. Idempotent.
#   status     report CLI version and what is currently linked.
#   uninstall  remove only the symlinks this provisioner created.
#
# The CLI itself is NOT installed here. `sf-harness-sync` is "fast, no sudo";
# `brew install openspec` belongs in `sf-harness-upgrade` (ansible). If the CLI
# is absent, `sync` logs a hint and exits 0 so the rest of the harness sync is
# never blocked.
#
# Usage: openspec.sh [sync|status|uninstall]

SCRIPT_NAME="openspec"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Configuration (env-overridable, mainly for tests) ---

# Staging workspace: holds the OpenSpec workspace + generated .claude tree.
# Lives in cache, never in $HOME.
OPENSPEC_STAGING="${OPENSPEC_STAGING:-${HOME}/.cache/sparkdock/openspec}"

# Tool to generate integration for (OpenSpec --tools name).
OPENSPEC_TOOLS="${OPENSPEC_TOOLS:-claude}"

# Global target directories for Claude Code.
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}"
CLAUDE_COMMANDS_DIR="${CLAUDE_COMMANDS_DIR:-${HOME}/.claude/commands}"
CLAUDE_HOOKS_DIR="${CLAUDE_HOOKS_DIR:-${HOME}/.claude/hooks}"
CLAUDE_SETTINGS="${CLAUDE_SETTINGS:-${HOME}/.claude/settings.json}"

# Source of the guard hook, shipped alongside this provisioner in the repo.
OPENSPEC_GUARD_SRC="${OPENSPEC_GUARD_SRC:-${SCRIPT_DIR}/../hooks/openspec-guard.sh}"
GUARD_NAME="openspec-guard.sh"

# Naming markers used to recognize resources owned by OpenSpec.
SKILL_PREFIX="openspec-"   # generated skill folder prefix
CLAUDE_CMD_DIR_NAME="opsx"  # Claude commands live in a nested opsx/ dir

# --- Logging ---

log_info() { printf '  [%s] %s\n' "${SCRIPT_NAME}" "$*"; }
log_warn() { printf '  [%s] WARN: %s\n' "${SCRIPT_NAME}" "$*" >&2; }
log_error() { printf '  [%s] ERROR: %s\n' "${SCRIPT_NAME}" "$*" >&2; }

# --- Helpers ---

has_cli() { command -v openspec >/dev/null 2>&1; }

has_jq() { command -v jq >/dev/null 2>&1; }

cli_version() { openspec --version 2>/dev/null | head -1; }

# Generate or refresh the staging workspace from the installed CLI.
generate_staging() {
    mkdir -p "${OPENSPEC_STAGING}"
    if [[ -d "${OPENSPEC_STAGING}/openspec" ]]; then
        log_info "refreshing staging workspace (openspec update)"
        openspec update "${OPENSPEC_STAGING}" --force >/dev/null
    else
        log_info "initializing staging workspace (openspec init --tools ${OPENSPEC_TOOLS})"
        openspec init "${OPENSPEC_STAGING}" --tools "${OPENSPEC_TOOLS}" --force >/dev/null
    fi
}

# Symlink ${src} -> ${dest}, replacing only a symlink we own. Refuses to
# clobber a real file/dir the user may have placed there.
link_one() {
    local src="$1" dest="$2"
    if [[ -L "${dest}" ]]; then
        rm -f "${dest}"
    elif [[ -e "${dest}" ]]; then
        log_warn "skipping ${dest}: exists and is not a symlink (left untouched)"
        return 0
    fi
    ln -s "${src}" "${dest}"
}

# Link all ${SKILL_PREFIX}* skill folders from ${src_dir} into ${dest_dir}.
link_skills() {
    local src_dir="$1" dest_dir="$2" count=0
    [[ -d "${src_dir}" ]] || return 0
    mkdir -p "${dest_dir}"
    local d name
    for d in "${src_dir}/${SKILL_PREFIX}"*/; do
        [[ -d "${d}" ]] || continue
        name="$(basename "${d}")"
        link_one "${d%/}" "${dest_dir}/${name}"
        count=$((count + 1))
    done
    log_info "linked ${count} skills -> ${dest_dir}"
}

# Remove ${SKILL_PREFIX}* symlinks under ${dest_dir} that point into staging.
unlink_skills() {
    local dest_dir="$1"
    [[ -d "${dest_dir}" ]] || return 0
    local l
    for l in "${dest_dir}/${SKILL_PREFIX}"*; do
        [[ -L "${l}" ]] || continue
        case "$(readlink "${l}")" in
            "${OPENSPEC_STAGING}"/*) rm -f "${l}" ;;
        esac
    done
}

# --- Claude Code deploy ---

deploy_claude() {
    local stage="${OPENSPEC_STAGING}/.claude"
    [[ -d "${stage}" ]] || { log_warn "no generated .claude tree, skipping"; return 0; }
    link_skills "${stage}/skills" "${CLAUDE_SKILLS_DIR}"
    # Commands: a single nested opsx/ directory.
    if [[ -d "${stage}/commands/${CLAUDE_CMD_DIR_NAME}" ]]; then
        mkdir -p "${CLAUDE_COMMANDS_DIR}"
        link_one "${stage}/commands/${CLAUDE_CMD_DIR_NAME}" "${CLAUDE_COMMANDS_DIR}/${CLAUDE_CMD_DIR_NAME}"
        log_info "linked commands -> ${CLAUDE_COMMANDS_DIR}/${CLAUDE_CMD_DIR_NAME}"
    fi
}

undeploy_claude() {
    unlink_skills "${CLAUDE_SKILLS_DIR}"
    local cmd="${CLAUDE_COMMANDS_DIR}/${CLAUDE_CMD_DIR_NAME}"
    [[ -L "${cmd}" ]] && rm -f "${cmd}" || true
}

# --- Guard hook (Claude Code settings.json) ---
#
# Copies openspec-guard.sh into ~/.claude/hooks and registers it on the
# UserPromptSubmit and PreToolUse events. The guard blocks OpenSpec slash
# commands / CLI / skills when the cwd has no openspec/ directory. Registration
# is idempotent: any prior openspec-guard entry is stripped before re-adding.

# Edit settings.json in place with a jq program. Creates the file as {} if
# missing; writes atomically.
settings_edit() {
    local prog="$1"; shift
    local current tmp
    if [[ -f "${CLAUDE_SETTINGS}" ]]; then
        current="$(cat "${CLAUDE_SETTINGS}")"
    else
        current="{}"
        mkdir -p "$(dirname "${CLAUDE_SETTINGS}")"
    fi
    tmp="$(mktemp)"
    if printf '%s' "${current}" | jq "$@" "${prog}" >"${tmp}" 2>/dev/null; then
        mv "${tmp}" "${CLAUDE_SETTINGS}"
    else
        rm -f "${tmp}"
        log_warn "could not update ${CLAUDE_SETTINGS} (invalid JSON?) — skipping hook registration"
        return 1
    fi
}

deploy_hook() {
    if ! has_jq; then
        log_warn "jq not found — skipping guard hook registration"
        return 0
    fi
    if [[ ! -f "${OPENSPEC_GUARD_SRC}" ]]; then
        log_warn "guard source ${OPENSPEC_GUARD_SRC} not found — skipping hook"
        return 0
    fi
    mkdir -p "${CLAUDE_HOOKS_DIR}"
    cp -f "${OPENSPEC_GUARD_SRC}" "${CLAUDE_HOOKS_DIR}/${GUARD_NAME}"
    chmod +x "${CLAUDE_HOOKS_DIR}/${GUARD_NAME}"

    # Quoted command so a space in $HOME is handled by the hook shell.
    local cmd="\"${CLAUDE_HOOKS_DIR}/${GUARD_NAME}\""
    settings_edit '
      def strip(ev): (ev // []) | map(select((.hooks // []) | any((.command // "") | test("openspec-guard\\.sh")) | not));
      .UserPromptSubmit = (strip(.UserPromptSubmit) + [
        { hooks: [ { type: "command", command: $cmd, timeout: 5, statusMessage: "Checking openspec..." } ] }
      ])
      | .PreToolUse = (strip(.PreToolUse) + [
        { matcher: "Bash|Skill", hooks: [ { type: "command", command: $cmd, timeout: 5, statusMessage: "Checking openspec..." } ] }
      ])
    ' --arg cmd "${cmd}" \
      && log_info "guard hook installed -> ${CLAUDE_HOOKS_DIR}/${GUARD_NAME} (UserPromptSubmit, PreToolUse)"
}

undeploy_hook() {
    if has_jq && [[ -f "${CLAUDE_SETTINGS}" ]]; then
        settings_edit '
          def strip(ev): (ev // []) | map(select((.hooks // []) | any((.command // "") | test("openspec-guard\\.sh")) | not));
          .UserPromptSubmit = strip(.UserPromptSubmit)
          | .PreToolUse = strip(.PreToolUse)
          | if (.UserPromptSubmit | length) == 0 then del(.UserPromptSubmit) else . end
          | if (.PreToolUse | length) == 0 then del(.PreToolUse) else . end
        ' && log_info "guard hook unregistered from ${CLAUDE_SETTINGS}"
    fi
    rm -f "${CLAUDE_HOOKS_DIR}/${GUARD_NAME}"
}

# --- Verbs ---

cmd_sync() {
    if ! has_cli; then
        log_warn "openspec CLI not found — skipping. Run 'sjust sf-harness-upgrade' to install it."
        return 0
    fi
    log_info "openspec $(cli_version)"
    generate_staging
    deploy_claude
    deploy_hook
    log_info "sync complete"
}

cmd_status() {
    if ! has_cli; then
        log_warn "openspec CLI not installed (run 'sjust sf-harness-upgrade')"
        return 0
    fi
    log_info "CLI version: $(cli_version)"
    log_info "staging: ${OPENSPEC_STAGING}"
    local claude_skills=0
    [[ -d "${CLAUDE_SKILLS_DIR}" ]] && claude_skills=$(find "${CLAUDE_SKILLS_DIR}" -maxdepth 1 -type l -name "${SKILL_PREFIX}*" 2>/dev/null | wc -l | tr -d ' ')
    log_info "Claude: ${claude_skills} skills linked"
    if [[ -f "${CLAUDE_HOOKS_DIR}/${GUARD_NAME}" ]]; then
        log_info "guard hook: installed"
    else
        log_info "guard hook: not installed"
    fi
}

cmd_uninstall() {
    log_info "removing OpenSpec symlinks from Claude Code dirs"
    undeploy_claude
    undeploy_hook
    log_info "uninstall complete (staging workspace at ${OPENSPEC_STAGING} left intact)"
}

usage() {
    cat <<EOF
Usage: openspec.sh [sync|status|uninstall]

  sync       Generate OpenSpec skills/commands from the installed CLI, link them
             into the global Claude Code directories, and install the guard
             hook. Default.
  status     Show CLI version, how many skills are linked, and hook state.
  uninstall  Remove the symlinks and guard hook created by this provisioner.

Environment overrides: OPENSPEC_STAGING, OPENSPEC_TOOLS, CLAUDE_SKILLS_DIR,
CLAUDE_COMMANDS_DIR, CLAUDE_HOOKS_DIR, CLAUDE_SETTINGS, OPENSPEC_GUARD_SRC.
EOF
}

main() {
    local verb="${1:-sync}"
    case "${verb}" in
        sync) cmd_sync ;;
        status) cmd_status ;;
        uninstall) cmd_uninstall ;;
        -h | --help | help) usage ;;
        *) log_error "unknown command '${verb}'"; usage; exit 2 ;;
    esac
}

main "$@"
