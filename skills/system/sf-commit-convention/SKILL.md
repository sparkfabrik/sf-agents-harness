---
name: sf-commit-convention
description: 'Enforce SparkFabrik commit message and branch naming conventions including conventional commits, legacy format detection, issue references, branch prefixes, and the mandatory Assisted-by trailer. MUST be loaded before EVERY git commit, commit message preparation, MR/PR title creation, branch creation, or any commit-related operation. Use whenever the agent is about to run git commit, git checkout -b, git branch, write a commit message, create a branch, or prepare a merge request or pull request title. Also use when the user mentions "commit", "git commit", "conventional commit", "commit message", "refs #", "assisted-by", "commit convention", "branch name", "new branch", or "feature branch". Never create a commit or branch without consulting this skill first.'
---

# SparkFabrik Commit Convention

This skill enforces SparkFabrik commit message and branch naming conventions. Follow these rules for every commit and branch you create.

## Branch Naming

Create branches following this pattern:

```
<prefix>/<issue-number>-<description>
```

- **All lowercase**, hyphens as word separators
- **Issue number required** (except `release/` branches)
- **Description**: 2-4 words, concise

### Prefixes

| Prefix      | When to use                                               |
| ----------- | --------------------------------------------------------- |
| `feat/`     | New features                                              |
| `fix/`      | Bug fixes                                                 |
| `docs/`     | Documentation only                                        |
| `chore/`    | Maintenance, dependencies, config                         |
| `refactor/` | Code restructuring, no behavior change                    |
| `ci/`       | CI/CD pipeline changes                                    |
| `test/`     | Test additions or fixes                                   |
| `release/`  | Release branches — use `release/vX.Y.Z` (no issue number) |

### Examples

```
feat/42-add-pdf-ingestion
fix/18-oauth-token-refresh
docs/33-update-api-reference
chore/71-bump-dependencies
release/v1.2.0
```

### When to create a branch

When work should happen on a separate branch (new feature, bug fix, or any issue-tracked work), create a branch following this convention before committing. If the user asks to start work on an issue and no branch exists, propose a branch name and confirm with the user before creating it.

## Format Detection

Projects may enforce different commit message conventions via git hooks. Before the first commit in a session, detect the project's convention:

### Step 1: Inspect recent history

Run `git log --oneline -5` and look for a dominant pattern:

| Pattern                     | Format                   | Example                            |
| --------------------------- | ------------------------ | ---------------------------------- |
| `type(scope): description`  | Conventional commits     | `feat(auth): add JWT refresh`      |
| `refs #N: description`      | SparkFabrik legacy       | `refs #42: fix token expiry`       |
| `[PROJECT-123] description` | Jira-style               | `[ACME-456] fix login redirect`    |
| `PROJECT-123: description`  | Jira-style (no brackets) | `ACME-456: fix login redirect`     |
| Other recognizable pattern  | Custom                   | Adapt to whatever the project uses |

If the last 5 commits consistently follow one format, use that format. If mixed, use the most recent commit's format — the project is likely transitioning, and the latest commit reflects the current convention. If there are no commits or no recognizable pattern in the history (e.g., freeform messages like `"updated stuff"`, `"wip"`), ask the user what commit format the project expects.

### Step 2: Check for commit-msg hooks

Check if the project has a `commit-msg` hook (`.git/hooks/commit-msg`, husky, lefthook, or similar). The presence of a hook means the project enforces a specific format — the git log inspection from Step 1 becomes even more important because the hook will reject non-compliant messages.

### Step 3: Handle hook rejection

If a commit is rejected by a `commit-msg` hook:

1. **Read the hook's error output** — it usually tells you the expected format.
2. **Retry with the format indicated by the error**, not a hardcoded fallback.
3. **If the error is unclear**, check `git log --oneline -3` for examples and match that pattern.
4. **If still unclear**, ask the user what commit format the project expects.

### Step 4: Cache

Once detected, cache the format for the rest of the session. Do not re-detect on subsequent commits.

### Adapting to custom formats

When a project uses a non-standard format (e.g., Jira-style), adapt the commit message to that format while still applying the `Assisted-by` trailer. The trailer is a git mechanism independent of the commit message format — it works with any convention.

For custom formats, the issue reference rules from this skill (fully qualified path in footers) may not apply — follow whatever convention the project uses. The `Assisted-by` trailer is the only rule that always applies regardless of project convention.

## Conventional Commits (preferred)

```
<type>(<scope>): <description>
```

- **Types**: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`, `style`, `perf`, `ci`, `build`, `revert`
- **Scope**: optional but recommended — use the component or area being changed
- **Description**: lowercase, imperative mood, no trailing period

## Legacy Format (transitional)

```
refs #<issue-number>: <description>
```

- Strictly lowercase `refs`
- Always `#` before the issue number
- Colon + space before description
- Lowercase description, imperative mood
- This format is validated by git hooks in projects still using it
- Cross-project issue references are not supported in legacy format

## Issue References

**Always reference an issue.** If none is apparent from context (branch name, conversation, MR/PR description), ask the user:

> "Is there a related issue to reference? Provide the number (e.g. `#35`) or the full cross-project path (e.g. `owner/project#35`). Type 'none' if there is no related issue."

Skipping the reference is the exception, not the norm. Never silently omit it.

### Resolving the full project path

**Always use the fully qualified project path in footers — never a bare `#N`.** A bare `#N` is ambiguous: on platforms like GitLab it only links within the current project context, which breaks when commits are cherry-picked, mirrored, or viewed outside the original project. The fully qualified path (`owner/repo#N`) is unambiguous everywhere.

Run `git remote get-url origin` and parse the namespace/project path (e.g., `sparkfabrik/sf-awesome-copilot` on GitHub, `sparkfabrik-innovation-team/r-d/ai/project` on GitLab). When the user provides a bare `#N`, resolve it to `<project-path>#N`:

| User provides      | Footer                                                                  |
| ------------------ | ----------------------------------------------------------------------- |
| `#35`              | `Refs: owner/repo#35` or `Closes: owner/repo#35` (resolved from remote) |
| `owner/project#35` | `Refs: owner/project#35` or `Closes: owner/project#35` (used as-is)     |

**Wrong:** `Refs: #35`, `Closes: #42` (bare references — never do this)
**Correct:** `Refs: sparkfabrik/sf-awesome-copilot#35`, `Closes: sparkfabrik/sf-awesome-copilot#42`

Use `Closes:` when the commit fully resolves the issue. Use `Refs:` otherwise.

### Legacy format

The issue reference is part of the subject line (`refs #N: ...`). No separate footer is needed.

## Assisted-by Trailer

**Mandatory on every commit**, regardless of format (legacy or conventional).

- Format: `Assisted-by: <agentname>/<full-model-id>` (agent name MUST be all lowercase)
- Applied via `--trailer` flag on `git commit`
- Substitute your own runtime identity (agent name and model ID)

Example for opencode with claude-opus-4.6:

```
Assisted-by: opencode/github-copilot/claude-opus-4.6
```

## MR/PR Titles

Follow the same conventional commit format as the subject line. Issue reference goes in the MR/PR description body, never in the title.

## Non-interactive Operations

Agents run without a TTY. Any git command that opens `$EDITOR` or expects interactive keyboard input will hang indefinitely. Always pass messages and options via command-line flags.

### Commands to avoid

| Don't use                          | Why                             | Use instead                                  |
| ---------------------------------- | ------------------------------- | -------------------------------------------- |
| `git rebase -i`                    | Opens editor for pick/squash    | `git rebase <branch>` (non-interactive)      |
| `git add -i` / `git add -p`        | Interactive staging prompts     | `git add <file>` or `git add .`              |
| `git commit` (without `-m`)        | Opens editor for commit message | `git commit -m "..."` with `--trailer` flags |
| `git merge` (conflict with editor) | Opens editor for merge message  | `git merge --no-edit <branch>`               |
| `git tag -a` (without `-m`)        | Opens editor for tag annotation | `git tag -a v1.0 -m "..."`                   |
| `git commit-tree`                  | Bypasses commit machinery, skips GPG signing and hooks | `git commit --amend -S` or `git rebase --exec "git commit --amend --no-edit -S"` |

**General rule:** if a git command has a `-i` or `--interactive` flag, never use it. If a command normally opens an editor, find the flag that passes the value inline.

### Rebase

- `git rebase <branch>` (non-interactive) is safe for straightforward rebases.
- For squashing commits, prefer the platform's squash merge option (GitHub / GitLab) over `git rebase -i`.
- Prefer `git pull --rebase` over manual fetch + rebase when updating a branch.
- If rebase conflicts occur, resolve the files then run `git rebase --continue`. Do not add `--edit` — the original commit messages are reused automatically.

## GPG Signing & Commit Rewriting

When `commit.gpgsign = true` is set, **never use git plumbing commands to rewrite commits**. `git commit-tree` and similar low-level commands bypass the commit machinery entirely, skipping GPG signing even when it is globally configured — resulting in "Unverified" commits on GitHub/GitLab.

Always rewrite through `git commit`:

```bash
# Amend a single commit (re-signs automatically)
git commit --amend --no-edit -S

# Re-sign N commits after any history rewrite
git rebase HEAD~N --exec "git commit --amend --no-edit -S"

# Squash N commits (git commit handles signing automatically)
git reset --soft HEAD~N && git commit -m "msg" --trailer "..."
```

Check if signing is active: `git config commit.gpgsign`

## Git Command Examples

### Conventional, same-project issue

```bash
git commit -m "feat(rag): add document ingestion pipeline" \
  --trailer "Refs: owner/repo#35" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```

### Conventional, cross-project issue

```bash
git commit -m "feat(rag): add document ingestion pipeline" \
  --trailer "Refs: sparkfabrik-innovation-team/r-d/ai/poc-drupal-rag-intelligence#35" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```

### Conventional, auto-closing same-project issue

```bash
git commit -m "fix(discovery): handle symlink loops in file scanning" \
  --trailer "Closes: owner/repo#42" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```

### Conventional, no issue (user confirmed none)

```bash
git commit -m "chore(deps): bump lockfile" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```

### Legacy format

```bash
git commit -m "refs #35: add document ingestion pipeline" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```
