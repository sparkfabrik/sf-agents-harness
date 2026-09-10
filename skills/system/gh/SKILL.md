---
name: gh
description: 'Invoke whenever the user is working with GitHub. Trigger on any of these signals: a URL containing "github.com" or a self-hosted GitHub Enterprise host, a git remote pointing to GitHub (git@github.com:... or https://github.com/...), the #N issue or PR notation (#15, #42), or words like "PR", "pull request", "gh", "GitHub issue", "GitHub Actions", "workflow run", "release", "gist", "review this PR", "merge this PR", "CI status", "checks", "fork", or "clone". Handles issues, pull requests, PR reviews and comments, GitHub Actions and CI runs, releases, gists, search, and reading files from GitHub repos. Always use gh, not WebFetch or curl, for any GitHub URL because gh handles authentication and returns structured data. This skill is the GitHub equivalent of glab for GitLab; if the project is on GitHub use this skill, and do not invoke it for GitLab tasks (use the glab skill instead).'
---

# gh CLI Skill

Use the `gh` CLI for ALL GitHub-related tasks including working with issues, pull requests, Actions workflows, releases, and repositories. If given a GitHub URL, use `gh` to get the information needed.

## Write short, plain text

Apply these rules whenever you draft or send a title, description, comment, review, changelog, or release note, including through the API. They apply even when `sf-writing-style` has not been loaded.

- **Content.** PR/MR descriptions lead with what changes, understandable without the task conversation. Add one sentence of context only when omitting it would make the change hard to understand or review. Issues state the problem and wanted result. Comments answer the point. Changelog entries state one change each.
- **Length.** Let the change determine the layout; a small fix can fit in one sentence. Default maximum: 80 words for a PR/MR description, 120 for an issue, 60 for a comment, and one sentence per changelog entry. These are team defaults, not targets or public standards. Preserve essential information even when it needs more words. Attribution and reference lines do not count.
- **Leave out.** No implementation details, even in a single sentence: file paths, function names, internal variables, source lines, test counts, diagnoses, or proposed fixes. Omit workarounds, investigation history, rejected approaches, and repeated summaries. Keep an identifier only when it names the changed interface or a required user action. Do not move omitted detail into unsolicited comments.
- **Select facts.** Investigation notes and the diff are input, not a checklist to summarize. For an issue, keep the symptom and wanted result. For a PR/MR, keep the changed behavior, essential context and required action. For a comment, answer only the question.
- **Evidence.** Use only supplied facts or results you observed. Omit unknowns. An error does not establish side effects, data loss, partial success, or affected environments. Do not invent causes, sample values, test cases, or reproduction results.
- **Plain English.** Use familiar words and concrete verbs. Keep necessary technical names exact. No invented jargon or padding. Use complete sentences in prose; parallel bullet items may be short phrases.
- **Layout.** Open with the main change. Bold a short key phrase, not a whole sentence. Put distinct features or changes in bullets instead of a comma-packed paragraph. Use headings only to separate useful sections, not generic labels like "MR description". One uncomplicated behavior change needs no list; a feature with several visible parts should list those parts. No empty sections, mandatory headings, bullet counts, or minimum length. State each fact once; do not restate the fix as its opposite in the old behavior unless the comparison is needed.
- **Supporting evidence.** Include supplied screenshots when they clarify a visible change; label before/after only when both are supplied. Include a short, verified validation result when it helps assess the change. Do not dump commands, logs, or test counts, or invent screenshots or results.
- **Exceptions.** Include essential breaking changes and required user actions. Expand only for these essentials, essential context, necessary validation, explicitly requested detail, or required template fields, using the fewest words needed. A direct question about how or why deserves a direct answer.

Before posting, read the actual outgoing text. Cut every sentence that does not state the change, problem, answer, essential context, required action, or useful verified evidence. Remove code locations and test inventories unless explicitly requested. Check each factual claim against the final diff and current evidence; remove stale claims when scope changes. Describe this diff; omit already-merged changes and workflow history unless explicitly requested. Can a reader outside the conversation identify what changes, any required action, and what was actually verified? Then check the length and remove repetition. Reading the diff is required; narrating it is not. Rewrite commit-generated descriptions before posting. Return the description itself, without code fences, block quotes, or commentary about omitted details unless requested.

Example of a small fix: "Rejects empty passwords with a validation message instead of returning a 500 error."

Example of a feature with several visible parts (copy the layout, not these facts):

> Adds **export controls**:
>
> - Date-range selection.
> - CSV download.

The lead sentence names the feature; the bullets name its parts. The description remains short without becoming a bare paragraph.

## Before you start

1. **Detect GitHub URLs**: if the user provided a URL containing "github.com", this is a GitHub resource. Extract the owner and repo from the URL and proceed with `gh` commands using `-R owner/repo`.
2. **Confirm it's a GitHub project**: check `git remote -v` for "github" in the URL. If so, use `gh` (not `glab`).
3. **Verify authentication**: run `gh auth status`. If not authenticated, **stop and ask the user** -- do not proceed.

## CLI-first principle

**Always prefer gh subcommands** (`gh issue list`, `gh pr list`, `gh run list`, etc.) over raw `gh api` calls. The CLI subcommands provide better output formatting, pagination, and are less error-prone. Use `gh api` **only** when no subcommand covers the operation (see the `gh api` section below).

## Targeting a repository

Before running any `gh` command, determine the repository context:

1. **User provided a GitHub URL** (e.g., `https://github.com/owner/repo/issues/42` or `https://github.com/owner/repo/pull/15`):
   Extract the **owner/repo** from the URL, then use `-R`:

   ```bash
   # URL: https://github.com/acme/webapp/pull/15
   # Extracted: acme/webapp
   gh pr view 15 -R acme/webapp
   gh issue list -R acme/webapp --label "bug"
   ```

2. **Inside a git repo with a GitHub remote**: no `-R` needed, `gh` detects the repository from the remote automatically.

3. **No URL provided and not inside a git repo**: **ask the user** for the full GitHub repository URL before proceeding. Do not guess or assume a repository.

## Handling auth errors

If any `gh` command fails with "authentication", "401", "403", or "could not determine", **stop immediately**. Do NOT work around auth failures with WebFetch, curl, or `glab`.

Present the user with these options:

### Option 1: Browser login (preferred -- more secure, tokens auto-refresh)

```bash
gh auth login --web
# Browser opens -> authorize -> done
```

### Option 2: Personal Access Token

Tell the user to generate a token at: `https://github.com/settings/tokens?type=beta` -- recommend fine-grained tokens with minimal scopes and a short expiry (30-90 days).

```bash
gh auth login --with-token < token.txt
```

### Option 3: Skip the operation

## Core terminology

| GitLab                             | GitHub           | CLI                     |
| ---------------------------------- | ---------------- | ----------------------- |
| Merge Request                      | **Pull Request** | `gh pr`                 |
| Snippet                            | **Gist**         | `gh gist`               |
| CI/CD                              | **Actions**      | `gh run`, `gh workflow` |
| `GROUP/PROJECT` (supports nesting) | `OWNER/REPO`     | --                      |
| MR `!15`                           | PR `#15`         | --                      |

Issues and PRs both use `#` prefix.

---

## Writing on behalf of the user

Every piece of content you create on GitHub carries this attribution header: PR and issue descriptions, comments, reviews, and `gh api` body fields.

```
> :robot: _This was written by an AI agent on behalf of @<username> (<agentname>/<full-model-id>)._
```

Fetch the username, never hardcode it. For `<agentname>/<full-model-id>` substitute your own runtime identity: the harness you run in as the agent name, lowercase, and the model ID exactly as your runtime reports it, never a friendly name. Same string as the `Assisted-by` trailer in `sf-commit-convention`, so keep the two identical.

Leave the header out only when the user asks you to, for instance on a project whose policy rejects AI-assisted content. Never suggest it, never decide it yourself, never swap in a softer marker.

Fetch and post in one command: a separate command runs in its own shell, so the variable is empty by the time you post and the header renders `on behalf of @ (...)` with no username.

```bash
GH_USERNAME=$(gh api user --jq '.login')
gh issue comment 42 --body "> :robot: _This was written by an AI agent on behalf of @${GH_USERNAME} (claude-code/claude-opus-5)._

Root cause identified: ..."
```

Never single-quote a heredoc delimiter (`<<'EOF'`): it blocks expansion and emits the literal `$GH_USERNAME`.

```bash
GH_USERNAME=$(gh api user --jq '.login')
gh pr create --title "feat: add dark mode" --body "$(cat <<EOF
> :robot: _This was written by an AI agent on behalf of @${GH_USERNAME} (claude-code/claude-opus-5)._

Adds a dark mode toggle to the settings page.
EOF
)"
```

> **Issue auto-linking:** GitHub renders bare `#N` as a clickable link to issue N. Use backticks (`` `#18` ``) when referring to issue numbers as text (examples, tables, logs). Leave `#N` bare only when it should link to an actual issue (e.g., `Closes #42`).

### Authoring rules for descriptions and commit messages

These rules apply to every issue title and description, pull request title and description, comment, review, and commit message you write.

Apply [Write short, plain text](#write-short-plain-text) before every write. Conversational styles such as caveman do not apply to published text.

**Use the full path for cross-project references.** When you reference an issue or pull request that lives in a _different_ repository than the one you are writing in, use the full `owner/repo#123` form rather than a bare `#123`. A bare `#123` (or a short form) only resolves within the same repository and will not render as a link from another repository. Apply this in prose and in footers alike (`Closes:`, `Refs:`). For example, to reference the platform-team board from a code repository, write `sparkfabrik-innovation-team/board#4379`, never a bare `board#4379` or `#4379`. Within the same repository, a bare `#123` is correct and renders as a link.

Load `sf-writing-style` for additional writing guidance. The rules above apply independently and take priority for these short artifacts. Never use em or en dashes outside quotations or code.

---

## Issues

### Issue title format

Issue titles must be **human-readable, short, and concise** — a few words that express the goal or scope of the work. Issue titles are NOT commit messages and must NOT use the Conventional Commits format (no `feat:`, `fix(scope):`, `chore:` prefixes, no imperative commit-style phrasing).

The title is read by humans scanning boards, backlogs, and notifications — it should describe **what the issue is about**, not how the eventual fix will be committed. Conventional Commits belongs on PR titles and commit messages, where it drives changelogs and tooling. Issues sit upstream of that, often before the solution is even known, so a commit-shaped title is both premature and harder to scan.

Style guidelines:

- Sentence case, no trailing period.
- Aim for under ~60 characters.
- Prefer noun phrases ("Slow dashboard load on Safari") or short problem statements ("Users locked out after password reset") over imperative verbs.
- Do not prefix with `Bug:`, `Feature:`, `Task:`, etc. — use **labels** for categorization instead.

**Examples:**

| Bad (commit-shaped)                            | Good (human-readable)             |
| ---------------------------------------------- | --------------------------------- |
| `feat(auth): add JWT token refresh`            | `JWT token refresh`               |
| `fix: prevent crash on empty password`         | `Login crash with empty password` |
| `docs(api): update rate limiting section`      | `Rate limiting docs out of date`  |
| `refactor(parser): simplify config validation` | `Simplify config parser`          |
| `chore: bump dependencies`                     | `Update dependencies`             |
| `Bug: login broken on Safari`                  | `Login broken on Safari`          |

### Issue commands

```bash
gh issue create --title "Login broken on Safari" --body "..." --label bug --label "high-priority" --assignee "@me"
gh issue list --assignee @me                      # list my issues
gh issue list --label "bug" --search "login"      # filter and search
gh issue view 42 --comments                       # view with comments
gh issue comment 42 --body "Root cause found."    # add a comment
gh issue edit 42 --add-label "confirmed"          # update metadata
gh issue close 42                                 # close (ask confirmation first)
gh issue reopen 42
```

### Issue template selection

Many GitHub projects define issue templates (stored in `.github/ISSUE_TEMPLATE/`) that encode the team's expected structure -- sections to fill, checklists, labels. Skipping these creates issues that don't match the project's conventions and forces manual cleanup.

Use `--template` to select a template by name:

```bash
# List templates by checking the repository
ls .github/ISSUE_TEMPLATE/
# Or via API
gh api repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE --jq '.[].name'

# Create with a template
gh issue create --template "Bug Report" --title "Login crash on empty password"
```

If no `--template` is specified and templates exist, `gh issue create` will prompt interactively. When running non-interactively, check for templates first and ask the user which one to use.

### Label selection process

If the user specified exact labels, use them. Otherwise:

1. **Discover available labels**: `gh label list` (or `gh label list --json name,description` for more detail)
2. **Propose labels that fit** the issue context.
3. **Ask the user to confirm or adjust** before creating the issue.

Do NOT invent label names. Only propose labels that actually exist in the repository.

### Create a branch from an issue

```bash
gh issue develop 42 --checkout              # create branch linked to issue and check it out
gh issue develop 42 --name fix/issue-42     # custom branch name
gh issue develop 42 --base develop          # branch from a specific base
```

---

## Pull Requests

### Creating PRs

```bash
gh pr create --title "Fix login crash" --body "Closes #42" \
  --base develop --reviewer "marco" --assignee "@me"
gh pr create --fill                   # title/description from commits
gh pr create --fill-verbose           # commits msg+body for description
gh pr create --draft --fill           # draft PR
```

Include `Closes #42` or `Fixes #42` in the body to auto-close issues on merge.

### PR title format

PR titles must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format:

```
<type>[(optional scope)]: <description>
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Use a scope when the change is clearly scoped to a module, component, or area of the codebase. Keep the description lowercase, concise, and in imperative mood.

**Examples:**

```
feat(auth): add JWT token refresh
fix: prevent crash on empty password submission
docs(api): update rate limiting section
refactor(parser): simplify config validation logic
ci: add deploy stage for staging environment
chore: bump dependencies
```

Breaking changes append `!` before the colon: `feat(api)!: change response format for /users endpoint`.

**PR creation checklist** (follow this carefully):

1. **Inspect branch state**: `git status`, `git log <base>...HEAD --oneline`, `git diff <base>...HEAD`
2. **Draft from the actual diff**: state what changes, using the writing rules above. Include identifiers only for the changed interface or a required user action.
3. **Push**: `git push -u origin HEAD` if not yet pushed.
4. **Check and create**: apply the final writing check to the PR description, then run `gh pr create` with all relevant flags.
5. **Return the PR URL** to the user.

### Reviewing and managing PRs

```bash
gh pr view 15 --comments              # view PR with comments
gh pr diff 15                         # see the diff
gh pr diff 15 --name-only             # list changed files
gh pr list --author @me               # my PRs
gh pr checkout 15                     # checkout locally
gh pr comment 15 --body "LGTM"       # leave a top-level comment
gh pr review 15 --approve --body "Looks good"  # formal approval
gh pr review 15 --request-changes --body "Please fix..." # request changes
gh pr merge 15 --squash --delete-branch
gh pr update-branch 15                # update with latest base branch
gh pr edit 15 --add-label "reviewed"
gh pr ready 15                        # mark draft as ready for review
gh pr ready 15 --undo                 # convert back to draft
gh pr close 15                        # close without merging
```

**Code review workflow**: view PR -> read diff -> check CI (`gh pr checks`) -> read comments -> leave feedback -> approve or request changes.

Approval and comments are separate actions -- `gh pr review --approve` handles GitHub's formal review system, `gh pr comment` posts a timeline comment.

### PR checks (CI status per PR)

```bash
gh pr checks 15                       # one-shot status
gh pr checks 15 --watch               # stream until all checks finish
gh pr checks 15 --watch --interval 5  # custom refresh interval
gh pr checks 15 --required            # only show required checks
gh pr checks 15 --fail-fast           # exit on first failure in watch mode
```

---

## PR Comments and Reviews

GitHub PRs have **three distinct comment types**. Using the wrong one is a common mistake -- a top-level comment when the user wanted a threaded reply to an inline review creates noise and loses context.

### Comment types

| Type                        | What it is                                                      | How to post                              |
| --------------------------- | --------------------------------------------------------------- | ---------------------------------------- |
| **Top-level comment**       | Timeline comment on the PR (like an issue comment)              | `gh pr comment 15 --body "..."`          |
| **Review**                  | Formal review: approve, request changes, or comment with a body | `gh pr review 15 --approve --body "..."` |
| **Inline review comment**   | Comment on a specific line of code, starting a thread           | `gh api` (no CLI subcommand)             |
| **Reply to inline comment** | Threaded reply to an existing inline code comment               | `gh api` (no CLI subcommand)             |

### Replying to review comments

There is no `gh pr` subcommand for replying to inline code review comments. You must use `gh api`.

**Step 1: List review comments to find the comment ID**

```bash
# List all review comments on PR #15
gh api repos/{owner}/{repo}/pulls/15/comments \
  --jq '.[] | {id, user: .user.login, path, line, body: (.body | .[0:80])}'
```

Each comment has an `id` field. Top-level review comments have no `in_reply_to_id`; replies do.

**Step 2: Reply to a specific comment**

Use the dedicated replies endpoint:

```bash
GH_USERNAME=$(gh api user --jq '.login')
gh api -X POST repos/{owner}/{repo}/pulls/15/comments/<comment_id>/replies \
  -f body="> :robot: _This was written by an AI agent on behalf of @${GH_USERNAME} (claude-code/claude-opus-5)._

The null check is needed because..."
```

Constraint: **replies to replies are not supported** by the API -- you can only reply to top-level review comments (those without `in_reply_to_id`). If the comment you want to reply to is itself a reply, reply to the parent comment instead.

**Step 3 (alternative): Reply using `in_reply_to`**

You can also reply via the create comment endpoint with the `in_reply_to` parameter. When `in_reply_to` is set, all other parameters except `body` are ignored:

```bash
gh api -X POST repos/{owner}/{repo}/pulls/15/comments \
  -f body="Agreed, good catch." \
  -F in_reply_to=<comment_id>
```

### Creating a new inline review comment

To start a new thread on a specific line of code:

```bash
# Get the latest commit SHA on the PR
COMMIT_SHA=$(gh pr view 15 --json headRefOid --jq '.headRefOid')

gh api -X POST repos/{owner}/{repo}/pulls/15/comments \
  -f body="This null check should handle empty strings too." \
  -f commit_id="$COMMIT_SHA" \
  -f path="src/auth.ts" \
  -F line=42 \
  -f side="RIGHT"
```

Parameters:

- `commit_id` (required): use the PR's HEAD commit SHA. Using an older commit may render the comment outdated.
- `path` (required): relative file path in the repo.
- `line` (required for line comments): line number in the diff.
- `side`: `RIGHT` for additions (green), `LEFT` for deletions (red).
- `start_line` + `start_side`: for multi-line comments, the first line of the range.

### Responding to all open review comments

When the user asks to respond to review comments on a PR, follow this workflow:

1. **List all review comments**: `gh api repos/{owner}/{repo}/pulls/15/comments --jq '.[] | {id, in_reply_to_id, user: .user.login, path, line, body}'`
2. **Filter to top-level comments** (those without `in_reply_to_id`) that haven't been addressed yet.
3. **Present a summary** to the user: who commented, on which file/line, what they said.
4. **Draft replies** and get user confirmation before posting.
5. **Post replies** using the replies endpoint for each comment.

Never post replies without showing them to the user first.

### Editing and deleting comments

`gh pr comment` and `gh issue comment` only support editing/deleting your **last** comment:

```bash
gh pr comment 15 --edit-last --body "Updated comment"   # edit your last comment
gh pr comment 15 --delete-last                           # delete your last comment
```

To edit or delete an arbitrary comment by ID, use the API:

```bash
# Edit a PR timeline comment (issue comment)
gh api -X PATCH repos/{owner}/{repo}/issues/comments/<comment_id> -f body="Updated"

# Edit a review comment
gh api -X PATCH repos/{owner}/{repo}/pulls/comments/<comment_id> -f body="Updated"

# Delete a review comment
gh api -X DELETE repos/{owner}/{repo}/pulls/comments/<comment_id>
```

---

## GitHub Actions / CI

```bash
gh run list                             # recent runs for current branch
gh run list --branch main               # runs on a specific branch
gh run list --workflow "ci.yml"          # filter by workflow
gh run list --status failure             # filter by status
gh run view <run-id>                    # run summary
gh run view <run-id> --verbose          # show job steps
gh run view <run-id> --log              # full logs
gh run view <run-id> --log-failed       # logs only for failed steps
gh run view <run-id> --job <job-id>     # specific job
gh run watch <run-id>                   # stream status in real-time until done
gh run watch <run-id> --exit-status     # exit non-zero if run fails
gh run rerun <run-id>                   # rerun entire run
gh run rerun <run-id> --job <job-id>    # rerun specific job
gh run cancel <run-id>                  # cancel running workflow
gh run download <run-id>                # download artifacts
gh run download <run-id> --name build   # download specific artifact
```

### Workflows

```bash
gh workflow list                        # list all workflows
gh workflow view ci.yml                 # view workflow details
gh workflow view ci.yml --yaml          # view workflow YAML
gh workflow run ci.yml                  # trigger workflow_dispatch
gh workflow run ci.yml --ref develop    # trigger on specific ref
gh workflow run ci.yml -f version="1.0" -f env="prod"  # with inputs
gh workflow enable ci.yml               # enable disabled workflow
gh workflow disable ci.yml              # disable workflow
```

### Monitoring a run

**To watch a specific run**, first find its ID, then watch it:

```bash
# Find the run ID
gh run list --branch main --limit 1 --json databaseId --jq '.[0].databaseId'

# Watch it
gh run watch <run-id>

# Or watch with compact output (only relevant/failed steps)
gh run watch <run-id> --compact
```

`gh run watch` takes a **run ID**, not a branch name. To monitor a run on a specific branch, always look up the run ID first via `gh run list --branch <branch>`.

**For PR-specific checks**, use `gh pr checks` instead -- it shows all status checks on a PR and supports `--watch`:

```bash
gh pr checks 15 --watch
```

### Viewing failed logs

When a run fails, `--log-failed` is the most efficient way to see what went wrong:

```bash
gh run view <run-id> --log-failed
```

This shows only the output from failed steps, avoiding hundreds of lines of passing step output.

### Actions caches

```bash
gh cache list                           # list all caches
gh cache list --limit 50                # show more
gh cache delete <cache-id>              # delete specific cache
```

---

## Releases

```bash
gh release list                         # list releases
gh release view v1.0.0                  # view specific release
gh release create v1.0.0 --notes "Release notes" --title "Version 1.0.0"
gh release create v1.0.0 --generate-notes     # auto-generate notes
gh release create v1.0.0 --notes-file notes.md
gh release create v1.0.0 --draft               # draft release
gh release create v1.0.0 --prerelease          # pre-release
gh release create v1.0.0 ./dist/*.tar.gz       # with assets
gh release upload v1.0.0 ./file.tar.gz         # upload asset to existing release
gh release download v1.0.0                      # download all assets
gh release download v1.0.0 --pattern "*.tar.gz" # download matching assets
gh release edit v1.0.0 --notes "Updated notes"
gh release delete v1.0.0                        # delete (NEVER do this -- see Safety Protocol)
```

---

## Search

`gh search` lets you search across all of GitHub, not just the current repository:

```bash
gh search issues "label:bug state:open" --repo owner/repo
gh search prs "is:open review:required" --repo owner/repo
gh search code "TODO" --repo owner/repo
gh search commits "fix auth" --repo owner/repo
gh search repos "stars:>1000 language:python"
```

All search commands support `--json`, `--jq`, and `--limit` for structured output.

---

## Safety Protocol

**Your default role is read-only.** Do NOT proactively suggest, offer, or execute state-changing operations. Only perform write or mutating operations when the user explicitly asks for them.

### Tier 1 -- FORBIDDEN (never execute these)

These commands are **never** executed, regardless of what the user asks. If the user needs one of these, explain the consequences and tell them how to run it manually.

| Action                       | Command                                       |
| ---------------------------- | --------------------------------------------- |
| Delete repo                  | `gh repo delete`                              |
| Delete release               | `gh release delete`                           |
| Delete workflow runs         | `gh run delete`                               |
| Destructive API calls        | `gh api -X DELETE` on critical resources      |
| Force push to default branch | `git push --force` to `main`/`master`/default |
| Hard reset                   | `git reset --hard`                            |

### Tier 2 -- EXPLICIT REQUEST ONLY (never suggest, never offer)

These commands are executed **only** when the user explicitly requests them with clear intent (e.g., "merge the PR", "close issue #42"). Never propose them, never include them in automated workflows, never ask "should I merge/close this?".

Before executing, **always** explain what will happen and ask for confirmation.

| Action                          | Command                                                             |
| ------------------------------- | ------------------------------------------------------------------- |
| Merge PR                        | `gh pr merge`                                                       |
| Merge bypassing checks          | `gh pr merge --admin` (bypasses branch protection -- extra caution) |
| Close issue or PR               | `gh issue close`, `gh pr close`                                     |
| Delete issue                    | `gh issue delete`                                                   |
| Cancel workflow run             | `gh run cancel`                                                     |
| Disable workflow                | `gh workflow disable`                                               |
| Modify secrets                  | `gh secret set`, `gh secret delete`                                 |
| Modify variables                | `gh variable set`, `gh variable delete`                             |
| Delete release assets           | `gh release delete-asset`                                           |
| Delete all caches               | `gh cache delete --all`                                             |
| Force push (non-default branch) | `git push --force`                                                  |
| Skip hooks                      | `--no-verify`                                                       |

### Tier 3 -- SAFE WITH CONFIRMATION

These operations can be proposed when relevant, but require a brief confirmation before execution.

| Action                                    | Command                             |
| ----------------------------------------- | ----------------------------------- |
| Update PR branch                          | `gh pr update-branch`               |
| Update metadata (labels, assignees, etc.) | `gh pr edit`, `gh issue edit`       |
| Change draft status                       | `gh pr ready`, `gh pr ready --undo` |
| Rerun workflow                            | `gh run rerun`                      |
| Trigger workflow                          | `gh workflow run`                   |

### Git safety

- **Prefer `gh pr update-branch`** over manual rebase + force push
- When in doubt about target branch, check the repo default: `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`

---

## `gh api` -- last resort for advanced operations

> **Do NOT use `gh api` when a CLI subcommand can do the job.** For issues, PRs, runs, labels -- always use the dedicated subcommands first. Use `gh api` only for operations not covered by any subcommand (e.g., review comment replies, team membership, GraphQL queries).

```bash
gh api repos/{owner}/{repo}/collaborators                              # GET
gh api -X POST repos/{owner}/{repo}/issues -f title="New" -f body="..." # POST
gh api -X PATCH repos/{owner}/{repo}/pulls/15 -f title="Updated"      # PATCH
gh api repos/{owner}/{repo}/issues --paginate                          # paginate
```

### Placeholder variables

Inside a git repo, `{owner}`, `{repo}`, and `{branch}` are auto-resolved:

```bash
gh api repos/{owner}/{repo}/pulls    # resolves to the current repo
```

### Native `--jq` filtering

Unlike `glab` (which requires piping to external `jq`), `gh api` has **built-in `--jq` support**:

```bash
gh api repos/{owner}/{repo}/pulls --jq '.[].title'
gh api user --jq '.login'
gh api repos/{owner}/{repo}/contributors --jq '.[] | {login: .login, contributions: .contributions}'
```

Use `--jq` instead of piping to `jq` whenever possible -- it's faster and avoids a dependency.

### GraphQL

```bash
gh api graphql -f query='
  query {
    repository(owner: "owner", name: "repo") {
      pullRequests(states: OPEN, first: 10) {
        nodes {
          number
          title
          author { login }
          reviewDecision
        }
      }
    }
  }
'
```

For comprehensive API patterns (GraphQL, pagination, advanced queries), read `references/api-patterns.md`.
