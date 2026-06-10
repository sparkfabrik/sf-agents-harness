#!/usr/bin/env bash
set -euo pipefail

# OpenSpec provisioner — installs OpenSpec skills and commands globally for
# Claude Code and OpenCode, keeping them in sync with the installed CLI.
#
# OpenSpec skills/commands are NOT vendored as static files: their bodies are
# compiled into the `openspec` binary and change between versions. Vendoring a
# snapshot drifts from the CLI and the skills (thin orchestration over CLI
# verbs) start telling the agent to run commands that no longer exist. Instead
# this provisioner GENERATES them from the locally installed CLI and refreshes
# on every sync, so the skills always match the binary — zero drift.
#
# Strategy: generate into a staging workspace under the cache dir (so the
# OpenSpec workspace, which `init`/`update` require, never pollutes $HOME),
# then symlink the generated skills and commands into each tool's global
# directory. Symlinks mean a later `openspec update` of the staging area is
# picked up with no redeploy.
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

# --- Configuration (env-overridable, mainly for tests) ---

# Staging workspace: holds the OpenSpec workspace + generated .claude/.opencode
# trees. Lives in cache, never in $HOME.
OPENSPEC_STAGING="${OPENSPEC_STAGING:-${HOME}/.cache/sparkdock/openspec}"

# Tools to generate integration for (OpenSpec --tools names).
OPENSPEC_TOOLS="${OPENSPEC_TOOLS:-claude,opencode}"

# Global target directories per tool.
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}"
CLAUDE_COMMANDS_DIR="${CLAUDE_COMMANDS_DIR:-${HOME}/.claude/commands}"
OPENCODE_SKILLS_DIR="${OPENCODE_SKILLS_DIR:-${HOME}/.config/opencode/skills}"
OPENCODE_COMMANDS_DIR="${OPENCODE_COMMANDS_DIR:-${HOME}/.config/opencode/commands}"

# Naming markers used to recognize resources owned by OpenSpec.
SKILL_PREFIX="openspec-"   # generated skill folder prefix (both tools)
CLAUDE_CMD_DIR_NAME="opsx"  # Claude commands live in a nested opsx/ dir
OPENCODE_CMD_PREFIX="opsx-" # OpenCode commands are flat opsx-*.md files

# --- Logging ---

log_info() { printf '  [%s] %s\n' "${SCRIPT_NAME}" "$*"; }
log_warn() { printf '  [%s] WARN: %s\n' "${SCRIPT_NAME}" "$*" >&2; }
log_error() { printf '  [%s] ERROR: %s\n' "${SCRIPT_NAME}" "$*" >&2; }

# --- Helpers ---

has_cli() { command -v openspec >/dev/null 2>&1; }

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

# --- Tool deployers ---

deploy_claude() {
    local stage="${OPENSPEC_STAGING}/.claude"
    [[ -d "${stage}" ]] || { log_warn "no generated .claude tree, skipping Claude"; return 0; }
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

deploy_opencode() {
    local stage="${OPENSPEC_STAGING}/.opencode"
    [[ -d "${stage}" ]] || { log_warn "no generated .opencode tree, skipping OpenCode"; return 0; }
    link_skills "${stage}/skills" "${OPENCODE_SKILLS_DIR}"
    # Commands: flat opsx-*.md files.
    if [[ -d "${stage}/commands" ]]; then
        mkdir -p "${OPENCODE_COMMANDS_DIR}"
        local f name count=0
        for f in "${stage}/commands/${OPENCODE_CMD_PREFIX}"*.md; do
            [[ -f "${f}" ]] || continue
            name="$(basename "${f}")"
            link_one "${f}" "${OPENCODE_COMMANDS_DIR}/${name}"
            count=$((count + 1))
        done
        log_info "linked ${count} commands -> ${OPENCODE_COMMANDS_DIR}"
    fi
}

undeploy_opencode() {
    unlink_skills "${OPENCODE_SKILLS_DIR}"
    local l
    [[ -d "${OPENCODE_COMMANDS_DIR}" ]] || return 0
    for l in "${OPENCODE_COMMANDS_DIR}/${OPENCODE_CMD_PREFIX}"*.md; do
        [[ -L "${l}" ]] || continue
        case "$(readlink "${l}")" in
            "${OPENSPEC_STAGING}"/*) rm -f "${l}" ;;
        esac
    done
}

# Run a deployer function for each configured tool.
for_each_tool() {
    local action="$1" tool
    IFS=',' read -ra tools <<< "${OPENSPEC_TOOLS}"
    for tool in "${tools[@]}"; do
        case "${tool}" in
            claude) "${action}_claude" ;;
            opencode) "${action}_opencode" ;;
            *) log_warn "unsupported tool '${tool}', skipping" ;;
        esac
    done
}

# --- Verbs ---

cmd_sync() {
    if ! has_cli; then
        log_warn "openspec CLI not found — skipping. Run 'sjust sf-harness-upgrade' to install it."
        return 0
    fi
    log_info "openspec $(cli_version)"
    generate_staging
    for_each_tool deploy
    log_info "sync complete"
}

cmd_status() {
    if ! has_cli; then
        log_warn "openspec CLI not installed (run 'sjust sf-harness-upgrade')"
        return 0
    fi
    log_info "CLI version: $(cli_version)"
    log_info "staging: ${OPENSPEC_STAGING}"
    local claude_skills=0 opencode_skills=0
    [[ -d "${CLAUDE_SKILLS_DIR}" ]] && claude_skills=$(find "${CLAUDE_SKILLS_DIR}" -maxdepth 1 -type l -name "${SKILL_PREFIX}*" 2>/dev/null | wc -l | tr -d ' ')
    [[ -d "${OPENCODE_SKILLS_DIR}" ]] && opencode_skills=$(find "${OPENCODE_SKILLS_DIR}" -maxdepth 1 -type l -name "${SKILL_PREFIX}*" 2>/dev/null | wc -l | tr -d ' ')
    log_info "Claude: ${claude_skills} skills linked"
    log_info "OpenCode: ${opencode_skills} skills linked"
}

cmd_uninstall() {
    log_info "removing OpenSpec symlinks from global tool dirs"
    undeploy_claude
    undeploy_opencode
    log_info "uninstall complete (staging workspace at ${OPENSPEC_STAGING} left intact)"
}

usage() {
    cat <<EOF
Usage: openspec.sh [sync|status|uninstall]

  sync       Generate OpenSpec skills/commands from the installed CLI and link
             them into the global Claude Code and OpenCode directories. Default.
  status     Show CLI version and how many skills are currently linked.
  uninstall  Remove the symlinks created by this provisioner.

Environment overrides: OPENSPEC_STAGING, OPENSPEC_TOOLS, CLAUDE_SKILLS_DIR,
CLAUDE_COMMANDS_DIR, OPENCODE_SKILLS_DIR, OPENCODE_COMMANDS_DIR.
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
