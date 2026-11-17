# CI/CD

## TTY-only commands -- do NOT use

`glab ci view` is a **full-screen terminal UI** (TUI) that requires an interactive TTY with keyboard input. It will **always fail** in non-interactive contexts (agent bash tools, scripts, piped commands). Never use it.

| Command        | Why it fails             | Use instead                                                        |
| -------------- | ------------------------ | ------------------------------------------------------------------ |
| `glab ci view` | Requires interactive TTY | `glab ci get` (structured data) or `glab ci status` (text summary) |

## Pipeline commands

```bash
glab ci status                       # pipeline status for current branch
glab ci status --branch main         # pipeline status for a specific branch
glab ci status --branch main --live  # stream status in real-time until pipeline completes
glab ci get                          # pipeline details as JSON (current branch)
glab ci get -b main                  # pipeline details for a specific branch
glab ci get -p <pipeline-id>         # pipeline details for a specific pipeline ID
glab ci get -p <pipeline-id> -d      # include extended job details
glab ci get -p <pipeline-id> -F json # explicit JSON output format
glab ci list                         # recent pipelines for current branch/project
glab ci list --per-page 10           # show more pipelines
glab ci trace                        # stream logs of the active job on current branch
glab ci trace --branch main          # stream logs for a specific branch
glab ci trace --branch main -p <id>  # stream logs for a specific pipeline ID
glab ci trace <job-name>             # stream logs for a specific job by name
glab ci run                          # trigger new pipeline
glab ci retry <pipeline-id>          # retry failed pipeline
glab ci cancel <pipeline-id>         # cancel running pipeline
glab ci artifact <refName> <jobName> # download artifacts (deprecated: use `glab job artifact`)
glab ci lint                         # validate .gitlab-ci.yml syntax
```

**Important:** `glab ci get` accepts **zero positional arguments**. The pipeline ID must be passed via the `-p` / `--pipeline-id` flag, not as a positional argument. Passing it as `glab ci get <id>` will fail with "Accepts 0 arg(s)".

Run `glab ci lint` before committing CI config changes to catch syntax errors early.

## Branch targeting

`glab ci status` and `glab ci trace` default to the **current git branch**. When monitoring pipelines on other branches (e.g., `main` after a push), use `--branch`:

```bash
glab ci status --branch main              # one-shot status check
glab ci status --branch main --live       # stream until pipeline finishes
glab ci trace --branch main               # stream active job logs on main
```

Without `--branch`, these commands look for a pipeline on the current branch, and may fail if none exists.

## Monitoring a specific pipeline

**Preferred: `--live` flag** — streams pipeline status in real-time until the pipeline completes (success, failed, or canceled). No polling loop needed:

```bash
glab ci status --branch main --live
```

**For pipeline details** (non-interactive, structured data):

```bash
# Get pipeline details by ID (JSON output)
glab ci get -p <pipeline-id>

# With extended job details
glab ci get -p <pipeline-id> -d
```

**For job-level detail** within a specific pipeline:

```bash
# 1. Find the pipeline ID
glab ci list --per-page 5

# 2. Stream logs of a specific pipeline
glab ci trace --branch main --pipeline-id <pipeline-id>

# 3. Check individual job statuses via API (when you need structured data beyond what `glab ci get -d` provides)
glab api "projects/:id/pipelines/<pipeline-id>/jobs" | jq '.[] | {name: .name, status: .status, stage: .stage}'
```

---
