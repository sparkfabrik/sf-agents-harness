## Why

Many AI coding tools (notably Claude Code) still read `CLAUDE.md` at the project root, while our team standard is to maintain instructions in `AGENTS.md` (the open agents.md format). Keeping two files in sync drifts; a `CLAUDE.md` symlink to `AGENTS.md` gives both tool families a single source of truth. The `sf-create-agentsmd` skill is the natural place to ensure that alias is created — it already owns AGENTS.md scaffolding and review.

## What Changes

- The `sf-create-agentsmd` skill SHALL ensure a root-level `CLAUDE.md` symlink to `AGENTS.md` exists whenever it handles the project root `AGENTS.md` (both scaffold mode and pkg-managed mode where the root file already exists).
- The symlink is created automatically only when no `CLAUDE.md` exists at the target location. If `CLAUDE.md` exists as a regular file or as a symlink pointing to a different target, the skill SHALL skip creation and warn the user. If it already points at `AGENTS.md`, the skill SHALL do nothing (idempotent).
- For any AGENTS-style file outside the project root (e.g. monorepo subproject `AGENTS.md`, `.agents/AGENTS.project.md`, alternate filename), the skill MUST ask the user before creating a `CLAUDE.md` alias, defaulting to **No**.
- Symlink targets SHALL be relative (`AGENTS.md`, not an absolute path) so the link survives clones, moves, and worktrees.
- The skill SHALL surface the action taken (created / skipped / warned) in its post-action summary.

## Capabilities

### New Capabilities

- `agentsmd-claude-symlink`: Management of the `CLAUDE.md` alias for `AGENTS.md` — when to auto-create, when to ask, how to handle pre-existing files, and the symlink-target convention.

### Modified Capabilities

_(none — `sf-create-agentsmd` has no prior capability spec in `openspec/specs/`. This change introduces its first capability spec.)_

## Impact

- **Skill file**: `skills/system/sf-create-agentsmd/SKILL.md` gains a new "Ensure CLAUDE.md alias" step and small updates to Mode Detection and Monorepo Considerations.
- **Skill evals**: `skills/system/sf-create-agentsmd/evals/evals.json` gains two entries covering the new behavior.
- **No code changes** elsewhere — the skill is prose-driven, executed by the LLM via shell.
- **Cross-platform caveat**: symlinks behave differently on Windows without Developer Mode; the design notes this but does not implement a fallback.
- **No breaking changes**: pre-existing `CLAUDE.md` files are never overwritten.
