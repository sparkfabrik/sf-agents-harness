#!/usr/bin/env bash
#
# openspec-guard.sh
# -----------------
# Guard hook that blocks any OpenSpec invocation when the current working
# directory does not contain an `openspec/` folder. This prevents OpenSpec
# slash commands, the `openspec` CLI, and OpenSpec skills from running in
# projects that have not been initialized with OpenSpec.
#
# Triggered on two hook events:
#   - UserPromptSubmit: catches user-typed slash commands such as
#     `/opsx:explore` or `/openspec-*` anywhere in the submitted prompt.
#   - PreToolUse: catches programmatic invocations, either a Bash command
#     running `openspec ...` or a model-invoked Skill named `opsx:*` /
#     `openspec-*`.
#
# Behavior:
#   - If the invocation is not OpenSpec-related, the hook exits 0 (allow).
#   - If it is OpenSpec-related and `openspec/` exists in cwd, exit 0 (allow).
#   - Otherwise the hook emits a block/deny decision as JSON, shaped to the
#     triggering event, instructing the user to run from an OpenSpec project
#     or to run `openspec init`.
#
set -euo pipefail

payload="$(cat)"

event="$(printf '%s' "$payload" | jq -r '.hook_event_name // ""')"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // ""')"
[ -n "$cwd" ] || cwd="$PWD"

is_openspec=""

case "$event" in
  UserPromptSubmit)
    prompt="$(printf '%s' "$payload" | jq -r '.prompt // ""')"
    # Match a typed slash command anywhere in the prompt.
    if printf '%s' "$prompt" | grep -Eq '(^|[[:space:]])/(opsx:|openspec-)'; then
      is_openspec="1"
    fi
    ;;
  PreToolUse)
    tool="$(printf '%s' "$payload" | jq -r '.tool_name // ""')"
    case "$tool" in
      Bash)
        command="$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')"
        if printf '%s' "$command" | grep -Eq '(^|[;&|]|&&|\|\|)[[:space:]]*openspec([[:space:]]|$)'; then
          is_openspec="1"
        fi
        ;;
      Skill)
        skill="$(printf '%s' "$payload" | jq -r '.tool_input.skill // ""')"
        if printf '%s' "$skill" | grep -Eq '^(opsx:|openspec-)'; then
          is_openspec="1"
        fi
        ;;
    esac
    ;;
esac

[ -n "$is_openspec" ] || exit 0

[ -d "$cwd/openspec" ] && exit 0

reason="
OpenSpec blocked: no 'openspec/' directory in '$cwd'.

Run from a directory that contains an openspec/ folder,
or run 'openspec init --tools none'."

if [ "$event" = "UserPromptSubmit" ]; then
  jq -n --arg r "$reason" '{decision: "block", reason: $r}'
else
  jq -n --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
fi
exit 0
