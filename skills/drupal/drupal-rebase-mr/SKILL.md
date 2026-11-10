---
name: drupal-rebase-mr
description: 'Rebase a Drupal.org issue merge request onto its target branch (or a newer version branch). Use this skill whenever the user mentions rebasing a Drupal merge request, rebasing a drupal.org issue, fixing merge conflicts on a Drupal MR, updating a Drupal contribution branch, or wants to bring a Drupal.org issue fork up to date. Also trigger when the user pastes a drupal.org issue URL, a git.drupalcode.org MR or work item URL, or a project#IID reference and mentions rebase, update, conflicts, or "bring up to date". Even if the user just says "rebase this drupal issue" or "update this MR" with a drupalcode.org link, this skill is what they need. Handles both same-branch rebases and cross-version rebases (e.g., 10.x to 11.x).'
---

# Drupal Merge Request Rebase Skill

Guide the user through rebasing a Drupal.org issue's merge request onto its
target branch or a newer version branch,
handling issue fork setup, MR/patch detection, conflict resolution, and safe
pushing with explicit user confirmation at
every dangerous step.

This skill covers the rebase. For the wider contribution loop (fixing the code,
pushing, following the pipeline), the `drupalorg` CLI ships its own
`drupalorg-work-on-issue` skill.

## Safety Rules

**NEVER** perform these actions without explicit user confirmation:

- `git clone` — always ask the user where their repo is first
- `git commit`
- `git push` (including `--force-with-lease`)
- Creating new branches on remotes
- Applying patch files
- Resolving merge conflicts — each conflict must be shown to the user and
  resolved interactively, one file at a time
- Posting on drupal.org or GitLab, including CLI commands that post, such as
  `issue:fork`, `issue:get-access` or `issue:comment`

**STOP means STOP**: Whenever this document says "STOP", you must pause
execution, present the information to the user,
and **wait for their explicit response** before continuing. Do not assume,
guess, or proceed autonomously.

## The drupalorg CLI

Check once whether the [`drupalorg` CLI](https://github.com/mglaman/drupalorg-cli) is
available: `command -v drupalorg`, or its MCP tools loaded in the session. When it
is, load its own skill (`drupalorg skill:get drupalorg-cli`) and pass
`--format=llm` to its read commands. Every step below gives the CLI command and a
fallback that works without it.

Some projects moved their issues from drupal.org to GitLab work items on
`git.drupalcode.org`. Their issues are referenced as `<project>#<IID>`, and the CLI
accepts that form wherever it takes a node ID.

## Workflow

### Step 1: Parse the Input

Accept any of:

- A **Drupal.org issue URL** (e.g.,
  `https://www.drupal.org/project/drupal/issues/1234567`)
- A **GitLab work item** URL or reference (e.g.,
  `https://git.drupalcode.org/project/ai_context/-/work_items/3586692` or
  `ai_context#3586692`)
- A **GitLab MR URL** (e.g.,
  `https://git.drupalcode.org/project/drupal/-/merge_requests/123`)

Extract:

- The project name (e.g., `drupal`, `webform`, `paragraphs`)
- The issue number (the drupal.org node ID, or the work item IID)
- The MR number (if provided directly)

If a GitLab MR URL is given, you already know the MR. Skip to Step 3.

### Step 2: Discover MRs and Patches on the Issue

Read the issue with its comments, then list its MRs, its fork branches and its
attached patches:

| Lookup             | With the CLI                                 | Without the CLI                                                                                                                                                                                                       |
| ------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Issue and comments | `drupalorg issue:show <ref> --with-comments` | drupal.org: `https://www.drupal.org/api-d7/node.json?nid=<nid>` and `https://www.drupal.org/api-d7/comment.json?node=<nid>`. Work item: `https://git.drupalcode.org/api/v4/projects/project%2F<project>/issues/<IID>` |
| MRs | `drupalorg mr:list <ref> --state=all` | For either issue type, get the fork's `id` from `https://git.drupalcode.org/api/v4/projects/issue%2F<project>-<number>`, then paginate `https://git.drupalcode.org/api/v4/projects/project%2F<project>/merge_requests?state=all` and retain MRs whose `source_project_id` matches that fork ID. |
| Fork and branches  | `drupalorg issue:get-fork <ref>`             | `git ls-remote https://git.drupalcode.org/issue/<project>-<number>.git` (fails when no fork exists)                                                                                                                   |

The CLI does not list attached patches. For a drupal.org issue, read the
`field_issue_files` list of the api-d7 node above and resolve each file with
`https://www.drupal.org/api-d7/file/<fid>.json`, which gives its name and download
URL. Hidden files have `display` set to `0`; skip them. The GitLab API returns the
work item description without a token, but its comments need one.

Decision tree:

- **Multiple active MRs**: Ask the user which MR to work with. List them with
  their branch names and status.
- **Single active MR**: Confirm with the user: "I found MR !N targeting branch
  X. Use this one?"
- **MR(s) exist AND patches exist**: Inform the user that patches are also
  attached. Ask whether to consider them or
  proceed with the MR only.
- **No MR, but patches exist**: List available patches (newest first). Ask which
  patch to use (default: latest). Then
  ask if the user wants to create a new MR from it.
- **No MR, no patches**: Inform the user there's nothing to rebase yet. Offer to
  help create an issue fork and branch.

### Step 3: Ensure a Local Clone Exists

**STOP** — You must ask the user before cloning or assuming a directory. Never
clone silently.

First, check if the current working directory is a git repository whose remote
points to
`git.drupalcode.org/project/<project-name>`.

- **If yes**: Tell the user: "Your current directory appears to be a clone of
  `<project-name>`. I'll use this." Then run `git fetch origin` to update.
- **If no**: **STOP and ask the user** (present these choices explicitly):
  1. "Do you already have a local clone of `<project-name>`? If so, provide
     the path."
  2. "Should I clone it to a temp directory? (default:
     `/tmp/<project-name>-<ISSUE_NUMBER>`)"
  3. "Should I clone it somewhere else? Provide the path."

**Wait for the user's answer.** Do not proceed until you have it.

Only after the user confirms, clone if needed:

```bash
git clone git@git.drupal.org:project/<project-name>.git /tmp/<project-name>-<ISSUE_NUMBER>
cd /tmp/<project-name>-<ISSUE_NUMBER>
```

### Step 3b: Pre-Flight Check — Clean Working Tree

Before performing any git operations (checkout, rebase, etc.), verify the
working tree is clean:

```bash
git status --short
```

- **If clean** (no output): Proceed to Step 4.
- **If dirty** (uncommitted changes): **STOP** and tell the user:

  > "The working tree has uncommitted changes. We need a clean state before
  > rebasing."

  Present options:
  1. `git stash` — stash changes and continue (will remind to `git stash pop`
     at the end)
  2. `git checkout .` — discard changes
  3. Abort — let the user handle it manually

  **Wait for the user's choice before proceeding.**

### Step 4: Set Up the Issue Fork Remote

The issue fork remote is named `<project-name>-<ISSUE_NUMBER>`, the name the
CLI creates. Run these commands from the clone.

With the CLI:

```bash
drupalorg issue:setup-remote <ref>
```

Without it:

```bash
git remote add <project-name>-<ISSUE_NUMBER> git@git.drupal.org:issue/<project-name>-<ISSUE_NUMBER>.git
git fetch <project-name>-<ISSUE_NUMBER>
```

If the remote already exists, just fetch:

```bash
git fetch <project-name>-<ISSUE_NUMBER>
```

### Step 5: Check Out the MR Branch

Identify the branch name from the MR. Check it out.

With the CLI:

```bash
drupalorg issue:checkout <ref> <BRANCH_NAME>
```

Without it:

```bash
git checkout -b <BRANCH_NAME> <project-name>-<ISSUE_NUMBER>/<BRANCH_NAME>
```

If the branch already exists locally, switch to it and reset:

```bash
git checkout <BRANCH_NAME>
git reset --hard <project-name>-<ISSUE_NUMBER>/<BRANCH_NAME>
```

### Step 6: Ask Rebase Type

Ask the user:

> "Rebase on the **same target branch** (default), or onto a **newer version
> branch**?"

- **Same branch** (default): The target branch is whatever the MR is targeting (
  e.g., `11.x`, `2.0.x`).
- **New version**: Ask which branch to rebase onto (e.g., from `10.x` to
  `11.x`).

### Step 7: Ensure Target Branch is Up to Date

```bash
git checkout <TARGET_BRANCH>
git pull origin <TARGET_BRANCH>
git checkout <BRANCH_NAME>
```

### Step 8: Perform the Rebase

**Same-branch rebase:**

```bash
git rebase <TARGET_BRANCH>
```

**Cross-version rebase (onto a new base branch):**

Determine the OLD base branch (from MR target or by inspecting git log). Then:

```bash
git rebase --onto <NEW_TARGET_BRANCH> <OLD_BASE_BRANCH>
```

If the old base branch doesn't have a local tracking branch, use the remote ref:

```bash
git rebase --onto <NEW_TARGET_BRANCH> <project-name>-<ISSUE_NUMBER>/<OLD_BASE_BRANCH>
```

For complex cross-version rebases spanning multiple versions, suggest doing it
incrementally (e.g., 10.2.x → 10.3.x →
11.x).

### Step 9: Handle Conflicts — INTERACTIVE, ONE BY ONE

**CRITICAL: You MUST NOT resolve conflicts autonomously.** Each conflict
requires the user's decision.

If the rebase encounters conflicts:

1. **STOP.** Tell the user: "The rebase hit conflicts. Let's resolve them
   together, one file at a time."

2. Show which files have conflicts:

   ```bash
   git status
   ```

3. **For each conflicting file** (one at a time):
   a. Show the conflict markers and surrounding context (use `git diff` or show
   the file section).
   b. Explain what each side represents:
   - "OURS (HEAD / target branch)" = upstream changes
   - "THEIRS (the MR branch)" = the patch/MR author's changes
     c. **Propose** a resolution and explain your reasoning.
     d. **STOP and ask**: "Does this resolution look correct? Should I apply
     it, or would you prefer something different?"
     e. **Wait for the user's approval** before writing the resolved file.

4. Only after the user approves the resolution for a file:

   ```bash
   git add <resolved-file>
   ```

5. After all conflicts in the current rebase step are resolved:

   ```bash
   git rebase --continue
   ```

6. If new conflicts appear in subsequent commits, repeat from step 3.

7. At any point, if the user wants to abort:
   ```bash
   git rebase --abort
   ```

**Never** silently resolve a conflict and move on. The user must see and approve
every resolution.

### Step 10: Review & Synthesis — Before Proposing Push

**Before asking to push, present a full summary of what was accomplished.** This
helps the user verify everything is correct.

Show:

1. **What was done** (one-liner summary):

   > "Rebased branch `<BRANCH_NAME>` onto `<TARGET_BRANCH>` (same-branch /
   > cross-version from `<OLD>`)."

2. **Commit log** after rebase:

   ```bash
   git log --oneline <TARGET_BRANCH>..<BRANCH_NAME>
   ```

3. **Files changed** (diff stats):

   ```bash
   git diff --stat <TARGET_BRANCH>..<BRANCH_NAME>
   ```

4. **Conflicts that were resolved** (if any): list each file and briefly what
   was decided.

5. **Any warnings**: e.g., "The test-only patch was not included" or "The MR
   target branch may need updating on GitLab."

Then **STOP and ASK FOR CONFIRMATION** before pushing:

> "Here's the full summary above. Ready to push with `--force-with-lease` to the
> issue fork? (This will overwrite the remote branch.)"

Only after explicit confirmation:

```bash
git push --force-with-lease <project-name>-<ISSUE_NUMBER> <BRANCH_NAME>
```

If the user performed a cross-version rebase onto a new branch name, also
mention that they may need to update the MR
target branch on GitLab, or create a new MR targeting the new branch.

After the push, check the MR pipeline and report its result:

- With the CLI: `drupalorg mr:status <ref> <MR_IID>`, and `drupalorg mr:logs <ref> <MR_IID>`
  for the failed jobs.
- Without it: the `head_pipeline` of
  `https://git.drupalcode.org/api/v4/projects/project%2F<project-name>/merge_requests/<MR_IID>`.

### Step 11: Patch-to-MR Flow (if applicable)

If the user started from a patch file (no existing MR):

1. Download the patch and check that it starts with diff headers (`diff --git`,
   `---`/`+++` or `From <sha>`), not HTML.
2. **ASK CONFIRMATION** to apply the patch:
   ```bash
   git apply <patch-file>
   ```
   or if it's a git-formatted patch:
   ```bash
   git am <patch-file>
   ```
3. If it doesn't apply cleanly, help resolve issues (try `git apply --3way`).
4. **ASK CONFIRMATION** to commit.
5. **ASK CONFIRMATION** to push to the issue fork.
6. Remind the user to create a merge request on GitLab (provide the URL to do
   so).

### Step 12: Wrap Up

After a successful push:

1. **If the project was cloned to a temp directory** (Step 3), ask the user
   whether they want to keep it or delete it.

2. Remind the user:

> "Done! Don't forget to add a comment on the Drupal.org issue explaining the
> rebase (e.g., 'Rebased onto 11.x, resolved
> conflicts in X and Y')."

Offer a draft for the user to edit into their own words. Drupal.org's
[policy on the use of AI when contributing](https://www.drupal.org/docs/develop/issues/issue-procedures-and-etiquette/policy-on-the-use-of-ai-when-contributing-to-drupal)
applies: when AI resolved conflicts or wrote code, the comment discloses it.

3. If the rebase was to a new version, also remind them to:

- Update the MR target branch (or create a new MR)
- Consider whether a backport to the old branch is needed

## Edge Cases

- **User doesn't have push access**: On a drupal.org issue, the user clicks "Get
  push access" on the issue page. On a GitLab work item, the CLI can request it
  with `drupalorg issue:get-access <ref>` after the user's OK.
- **Issue fork doesn't exist yet**: On a drupal.org issue, the user creates it
  with "Create issue fork" on the issue page. On a GitLab work item, the CLI can
  create it with `drupalorg issue:fork <ref>` after the user's OK; the bot works
  asynchronously, so check again with `drupalorg issue:get-fork <ref> --no-cache`.
- **Detached HEAD or dirty working tree**: Warn the user and offer to stash or
  clean before proceeding.
- **The MR is already up to date**: Inform the user no rebase is needed.

## Git Remote Naming Convention

Always use `<project-name>-<ISSUE_NUMBER>` as the remote name for issue forks.
The `drupalorg` CLI creates the same name, so a fork set up with or without it
works the same way, and the name avoids conflicts with the main `origin` remote.
