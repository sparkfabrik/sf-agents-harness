---
name: githuman
description: >-
  How to use GitHuman to review AI-generated code changes before committing. 
  GitHuman provides a GitHub-like diff review interface for your staging area 
  — visual diffs, inline comments, todos, and review workflows — all 
  running locally via Docker. Use this skill whenever the user mentions 
  "githuman", "code review before commit", "review staged changes", "review 
  AI changes", wants to review diffs in a browser, asks about reviewing code 
  before committing, or after completing a coding task where staged changes 
  should be reviewed. Also trigger when you see references to sjust/ajust 
  githuman commands.
metadata:
  tags: code-review, git, ai-workflow, commit, staging
---


## When to use

Use this skill whenever you are working with GitHuman to review AI-generated code changes before committing them. GitHuman provides a web interface for visual code review with inline comments, suggestions, and todo management.

## How to use

Read individual rule files for detailed explanations and examples:

- [rules/installation.md](rules/installation.md) - Installing and running GitHuman
- [rules/review-workflow.md](rules/review-workflow.md) - Complete workflow for reviewing AI-generated changes
- [rules/staging.md](rules/staging.md) - Staging files for review directly in GitHuman
- [rules/cli-commands.md](rules/cli-commands.md) - All CLI commands with examples
- [rules/todos.md](rules/todos.md) - Managing todos and follow-up tasks
- [rules/comments.md](rules/comments.md) - Adding inline comments and suggestions to code
- [rules/export.md](rules/export.md) - Exporting reviews for documentation
- [rules/tips.md](rules/tips.md) - Best practices and productivity tips
---

## Command invocation — this section overrides upstream examples

This environment runs GitHuman through Docker containers managed by Just recipes. The rules files above contain `npx githuman` commands in their examples — **ignore those invocations** and always apply the translation table below instead.

The command runner is platform-specific:

- **macOS** (default): `sjust`
- **Linux**: `ajust`

Detect the platform first. When in doubt, default to `sjust`:

```bash
if [[ "$(uname)" == "Linux" ]]; then
    JUST_CMD="ajust"
else
    JUST_CMD="sjust"
fi
```

**Every** `npx githuman` or bare `githuman` command has a Just recipe equivalent. Never use `npx githuman` or `githuman` directly, even when the upstream rules files show `npx` in their examples:

| Upstream (do NOT use) | Local (use this instead) |
|------------------------|--------------------------|
| `npx githuman serve` | `$JUST_CMD githuman-start [directory]` |
| `npx githuman serve` (open browser) | `$JUST_CMD githuman-open [directory]` |
| `npx githuman list` | `$JUST_CMD githuman-list` |
| `npx githuman resolve <id\|last>` | `$JUST_CMD githuman-exec resolve <id\|last>` |
| `npx githuman export <id\|last> [-o file]` | `$JUST_CMD githuman-exec export <id\|last> [-o file]` |
| `npx githuman todo <add\|list\|done> [args]` | `$JUST_CMD githuman-exec todo <add\|list\|done> [args]` |
| (get container ID) | `$JUST_CMD githuman-id [directory]` |
| (view container logs) | `$JUST_CMD githuman-logs [container-name]` |
| (stop instance) | `$JUST_CMD githuman-stop [container-name]` |
| (stop all + remove volumes) | `$JUST_CMD githuman-purge` |

No `npx githuman` or `githuman` invocation is valid in this environment — always use `$JUST_CMD` recipes.

## Infrastructure

GitHuman instances run as Docker containers with these SparkFabrik-specific conventions:

- **FQDN**: `<project>.githuman.sparkfabrik.loc` (numeric suffix for name collisions)
- **Auth**: random token per session, passed as `?token=<token>` query parameter
- **TLS**: provisioned via `spark-http-proxy` when available
- **Readiness**: `githuman-start` waits up to 60s for the container to respond

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container not starting | Check Docker is running: `docker info` |
| Review not ready after 60s | Check logs: `$JUST_CMD githuman-logs` |
| Certificate warning in browser | Install `spark-http-proxy` or accept the self-signed cert |
| Port conflict | GitHuman uses port 3847 inside the container; the reverse proxy handles external routing |
| Stale instance | Stop and restart: `$JUST_CMD githuman-stop` then `$JUST_CMD githuman-start` |

