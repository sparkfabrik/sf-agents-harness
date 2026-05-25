## Context

The `sf-create-agentsmd` skill (`skills/system/sf-create-agentsmd/SKILL.md`) is the canonical place where this team scaffolds and reviews `AGENTS.md`. Several tools in the toolchain — most importantly Claude Code (`CLAUDE.md`) — still expect a project-root file under their own name. The team standard is to maintain a single source of truth at `AGENTS.md` and alias other names to it.

Today the skill produces only `AGENTS.md`. Users either manually `ln -s AGENTS.md CLAUDE.md` after the fact (often forgotten) or end up with two divergent files. Folding the alias step into the skill removes a foot-gun.

The skill is prose-driven (executed by the LLM through shell commands), so this change is primarily SKILL.md text plus matching eval scenarios — no application code.

## Goals / Non-Goals

**Goals:**

- After the skill handles the project root `AGENTS.md` (Scaffold or Pkg-managed mode), it auto-creates a `CLAUDE.md` symlink to it whenever no `CLAUDE.md` exists at the root.
- Pre-existing `CLAUDE.md` files (regular file or mismatched symlink) are preserved and the user is warned, never overwritten.
- For non-root or non-default AGENTS-style files, the skill explicitly asks the user (default **No**) before creating any alias.
- Behavior is documented in the skill blueprint AND covered by evals so the behavior is testable.

**Non-Goals:**

- Auto-aliasing other tool-specific filenames (e.g. `.cursorrules`, `.github/copilot-instructions.md`). Out of scope; AGENTS.md ↔ CLAUDE.md only.
- A Windows-specific symlink fallback (e.g. junction or hard-link). Documented as a caveat below.
- Backfilling CLAUDE.md in repos where the skill is not run.
- Touching pkg-managed `AGENTS.md` content — the existing rule "never overwrite the pkg-managed root AGENTS.md" still holds; the symlink step does not modify the target.

## Decisions

### D1. Symlink target is relative (`AGENTS.md`), not absolute

**Rationale:** A relative symlink survives `git clone`, repository moves, container mounts, and worktrees. An absolute target breaks the moment the repo is opened on another machine. The two files always live in the same directory, so a one-segment relative target is sufficient.

**Alternatives considered:** Absolute path (rejected — fragile across machines), creating a copy instead of a symlink (rejected — defeats the single-source-of-truth goal, reintroduces drift).

### D2. Auto-create only when no CLAUDE.md exists; never overwrite

**Rationale:** Overwriting a CLAUDE.md the user wrote by hand would silently destroy their work. The cheapest safe default is "create only when absent". Conflict cases (regular file present; symlink to a different target) are surfaced with a warning so the human can decide.

**Alternatives considered:** Force-replace with a confirmation prompt (rejected — extra friction in the common case and still risky); back up to `CLAUDE.md.bak` (rejected — pollutes the tree and the user almost certainly wants AGENTS.md content, not the orphaned backup).

### D3. Pkg-managed projects get the alias too

**Rationale:** Pkg-managed projects already have a curated root AGENTS.md they don't own. The CLAUDE.md alias is purely additive — it never modifies the pkg-managed file — and gives Claude Code the same view of project instructions as agents.md-aware tools. Skipping it would leave pkg-managed projects without the very feature this change is for.

### D4. Default No for non-root AGENTS-style files

**Rationale:** Monorepo subprojects and `.agents/AGENTS.project.md` have different ergonomics. Some users keep CLAUDE.md only at the root and rely on tool walk-up; others want per-package CLAUDE.md. We don't know which, so we ask. Default **No** matches the safer choice (don't add files the user didn't request).

### D5. Surface the action in the post-action summary

**Rationale:** Symlink creation is silent on the filesystem. Without explicit reporting the user wouldn't notice, then later be surprised when CLAUDE.md shows up in a `git status`. Reporting "Created CLAUDE.md → AGENTS.md symlink" closes the loop.

## Risks / Trade-offs

- **Windows symlink permissions** → On Windows without Developer Mode or admin rights, `ln -s` / `mklink` requires elevation. Mitigation: the skill documents the caveat; if `ln` fails, it surfaces the error and skips. No automatic fallback to hard-link or copy (would diverge from the spec).
- **Filesystems without symlink support** (e.g. some FAT volumes) → Same handling as Windows: detect failure, warn, skip.
- **`git` config that ignores symlinks** (`core.symlinks=false`) → The symlink will be committed as a plain text file. Out of scope; surfacing this would require probing git config. Mitigation: documented in design only.
- **User regenerates AGENTS.md while CLAUDE.md is a symlink** → No risk; the symlink resolves to the new content automatically. This is exactly the desired property.
- **Concurrent run leaves CLAUDE.md half-created** → The operation is a single `ln -s`. Not atomic on every filesystem but failure leaves either nothing or a complete link; both states are safe.

## Migration Plan

- No data or runtime migration. The change is documentation + skill behavior.
- Existing projects with both AGENTS.md and a hand-maintained CLAUDE.md are unaffected: the skill detects CLAUDE.md and skips with a warning.
- Rollout is per-invocation: once the updated skill ships, the next time it runs in a repo without CLAUDE.md, the alias appears.

## Open Questions

- Should the skill offer a `--force` style override for users who explicitly want the existing CLAUDE.md replaced? Deferred — not requested, and the workaround (`rm CLAUDE.md && rerun`) is trivial. Revisit if it comes up.
