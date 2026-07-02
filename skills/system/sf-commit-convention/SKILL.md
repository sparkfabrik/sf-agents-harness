---
name: sf-commit-convention
description: 'Enforce SparkFabrik commit message and branch naming conventions including conventional commits, legacy format detection, issue references, branch prefixes, and the mandatory Assisted-by trailer. MUST be loaded before EVERY git commit, commit message preparation, MR/PR title creation, branch creation, or any commit-related operation. Use whenever the agent is about to run git commit, git checkout -b, git branch, write a commit message, create a branch, or prepare a merge request or pull request title. Also use when the user mentions "commit", "git commit", "conventional commit", "commit message", "refs #", "assisted-by", "commit convention", "branch name", "new branch", or "feature branch". Never create a commit or branch without consulting this skill first.'
---

# SparkFabrik Commit Convention

Core rules for every commit and branch. For worked git examples, format-detection
edge cases, non-interactive git, and GPG signing, see [reference.md](reference.md).

## Branch Naming

Pattern: `<prefix>/<issue-number>-<description>`

- All lowercase, hyphens as separators
- Issue number required (except `release/`)
- Description: 2-4 words

| Prefix      | When to use                            |
| ----------- | -------------------------------------- |
| `feat/`     | New features                           |
| `fix/`      | Bug fixes                              |
| `docs/`     | Documentation only                     |
| `chore/`    | Maintenance, dependencies, config      |
| `refactor/` | Code restructuring, no behavior change |
| `ci/`       | CI/CD pipeline changes                 |
| `test/`     | Test additions or fixes                |
| `release/`  | `release/vX.Y.Z` (no issue number)     |

Examples: `feat/42-add-pdf-ingestion`, `fix/18-oauth-token-refresh`, `release/v1.2.0`

When work belongs on a separate branch (new feature, bug fix, issue-tracked work),
create the branch before committing. If no branch exists, propose a name and confirm
with the user before creating it.

## Format Detection

Before the first commit in a session, detect the project's convention by running
`git log --oneline -5` and matching the dominant pattern:

| Pattern                     | Format               | Example                         |
| --------------------------- | -------------------- | ------------------------------- |
| `type(scope): description`  | Conventional commits | `feat(auth): add JWT refresh`   |
| `refs #N: description`      | SparkFabrik legacy   | `refs #42: fix token expiry`    |
| `[PROJECT-123] description` | Jira-style           | `[ACME-456] fix login redirect` |
| `PROJECT-123: description`  | Jira-style           | `ACME-456: fix login redirect`  |

Use the dominant format; if mixed, use the most recent commit's format. If there is no
recognizable pattern, ask the user. Cache the detected format for the rest of the
session. A `commit-msg` hook (`.git/hooks/commit-msg`, husky, lefthook) means the format
is enforced, so match it. For hook rejection, custom formats, and caching details, see
[reference.md](reference.md).

## Conventional Commits (preferred)

```
<type>(<scope>): <description>
```

- Types: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`, `style`, `perf`, `ci`, `build`, `revert`
- Scope: optional but recommended; the component or area changed
- Description: lowercase, imperative mood, no trailing period
- Subject length: keep the whole subject line under 72 characters, and aim for 50. Longer subjects are truncated with `…` in GitHub and GitLab commit lists. Move detail into the commit body, never the subject.
- No AI-slop writing tells: in the subject or body, do not use the em dash (—) or en dash (–) as a sentence connector; rewrite with a period, comma, colon, or parentheses. Write like a human engineer, not a generated summary.

## Legacy Format (transitional)

```
refs #<issue-number>: <description>
```

- Strictly lowercase `refs`, always `#` before the number, colon + space before the description
- Lowercase description, imperative mood
- Validated by git hooks in projects still using it; cross-project references not supported
- The issue reference is part of the subject; no separate footer needed

## Issue References

**Always reference an issue.** If none is apparent from context (branch name,
conversation, MR/PR description), ask the user:

> "Is there a related issue to reference? Provide the number (e.g. `#35`) or the full
> cross-project path (e.g. `owner/project#35`). Type 'none' if there is no related issue."

Skipping the reference is the exception, not the norm. Never silently omit it.

**Always use the fully qualified project path in footers, never a bare `#N`.** A bare
`#N` is ambiguous and breaks when commits are cherry-picked, mirrored, or viewed outside
the original project. Run `git remote get-url origin`, parse the `owner/repo` path, and
resolve a bare `#35` to `<project-path>#35`:

- **Wrong:** `Refs: #35`, `Closes: #42`
- **Correct:** `Refs: sparkfabrik/sf-awesome-copilot#35`, `Closes: sparkfabrik/sf-awesome-copilot#42`

Use `Closes:` when the commit fully resolves the issue, `Refs:` otherwise. (Legacy format
keeps the reference in the subject line instead.)

## Assisted-by Trailer

**Mandatory on every commit**, regardless of format.

- Format: `Assisted-by: <agentname>/<full-model-id>` (agent name MUST be all lowercase)
- Applied via the `--trailer` flag on `git commit`
- Substitute your own runtime identity (agent name and model ID)

Example: `Assisted-by: opencode/github-copilot/claude-opus-4.6`

## MR/PR Titles

MR/PR titles are **human-readable**, like issue titles, not the Conventional Commits
format. Write a short sentence-case phrase describing the change (for example `Add OAuth2
authentication flow`), with no `feat:`/`fix(scope):` prefix and no lowercase imperative
commit phrasing. The issue reference goes in the MR/PR description body, never in the
title. See the `gh` and `glab` skills for the full title rule and examples.

The commit history stays conventional. The commits on the branch, and the single commit
that lands on the default branch, still follow the Conventional Commits format above.
Because these repositories squash-merge and default the squash commit subject to the
human-readable MR/PR title, set the squash commit subject to the conventional format when
you squash-merge, so the default-branch history stays conventional.

## Write in plain prose, not caveman

Commit messages (subject and body), MR/PR titles, and MR/PR descriptions are
durable, outward-facing artifacts: write them in normal, complete English. An
active terse output style overrides nothing here. A session-level reminder such
as `CAVEMAN MODE ACTIVE` (drop articles, fragments OK, short synonyms) applies to
your conversational replies, not to these artifacts. Write the commit, title, and
description in full prose regardless of the active style; do not run any command
to toggle the style off.

Avoid AI-slop writing tells in these artifacts too: do not use the em dash (—) or
en dash (–) as a sentence connector; rewrite with a period, comma, colon, or
parentheses. This matches the same rule in the `gh` and `glab` skills for PR/MR
bodies, so subjects, titles, and descriptions all read the same way.

## Quick Example

```bash
git commit -m "feat(rag): add document ingestion pipeline" \
  --trailer "Refs: owner/repo#35" \
  --trailer "Assisted-by: opencode/github-copilot/claude-opus-4.6"
```

For cross-project issues, auto-closing, legacy format, GPG signing, and non-interactive
git command guidance, see [reference.md](reference.md).
