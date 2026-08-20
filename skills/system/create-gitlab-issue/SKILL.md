---
name: create-gitlab-issue
argument-hint: "[-y|--yes] [-n|--dry-run] [gitlab-url|group/project] <task description>"
description: >-
  Create a well-grounded GitLab issue on any GitLab instance (gitlab.com or
  self-hosted) from a short task description. Before writing the issue, audit the
  project's current state -- git branch and recent commits, existing open issues
  and MRs, in-flight specs or change proposals, and the relevant source files --
  so the issue is accurate, scoped, de-duplicated, and carries the labels the
  board actually uses. Use this skill whenever the user wants to "open an issue",
  "create an issue", "create a GitLab issue", "file an issue on GitLab", "create
  a task", "add a ticket", "put this on the board", "file a bug", "log some tech
  debt", or otherwise turn a piece of context into a tracked work item. Host,
  project, labels and attribution are resolved at runtime -- nothing is
  hardcoded -- with optional per-project overrides in `.claude/gitlab-issue.json`.
  Defers to the glab skill for the actual GitLab API calls and shows a draft for
  approval before creating, unless the invocation passes `-y`/`--yes` to
  auto-confirm or `-n`/`--dry-run` to stop at the draft. Do not use for GitHub
  issues -- use the gh skill instead.
---

# Create GitLab issue

Turn a short task description into a properly grounded GitLab issue. The value of
this skill is the audit step: a task description in isolation is usually vague,
possibly a duplicate, and rarely names the real files or acceptance criteria. By
inspecting the live project state first, the issue you write is accurate, scoped,
linked to related work, and lands in the correct board column via labels.

All GitLab calls go through the **glab skill** -- load it for the create call and
any list/view queries. It owns authentication, host targeting, and TLS handling;
do not re-derive those rules here.

If the project's remote is GitHub, **stop** and use the `gh` skill instead.

## Arguments

Invocation shape:

```
/create-gitlab-issue [-y|--yes] [-n|--dry-run] [gitlab-url|group/project] <task description>
```

| Flag | Effect |
|------|--------|
| `-y`, `--yes`, `yes` | **Auto-confirm.** Run the full audit, then create without waiting for an OK. Print the draft you used and the resulting URL. |
| `-n`, `--dry-run` | **Draft only.** Stop after step 5, never call `glab issue create`. |
| a GitLab URL or `group/project` | Target override -- see step 1. |

**Options are recognized only in the leading run of arguments.** Consume them
from the front while each token matches; the first token that doesn't begins the
task description, and from there everything is prose -- a flag-looking token
inside it is part of the task, not an option. So `-n` in
"Document the `-n` flag in the README" is text, not a dry-run request.

`-y` and `-n` are mutually exclusive; if both appear, `-n` wins (the safer one).

Auto-confirm skips the *approval* gate, never the *audit*. Two checks still stop
you cold even under `-y`: a near-duplicate issue, and an unresolvable target.
Report and stop in both cases rather than creating.

## Workflow

The flow is always: **resolve target → gather context → audit → draft → confirm →
create**. Never skip the audit, and do not create without either an explicit OK
or `-y` in the invocation; the issue is an outward-facing artifact and that gate
is what makes it trustworthy.

## 1. Resolve the target

Work out *where* the issue goes before anything else. First hit wins:

1. **Explicit user input** -- a GitLab URL (issue, board, project, file) or an
   `group/project` path in the prompt. Extract the hostname and project path and
   target them per the glab skill's "Targeting a project" section.
2. **Project config** -- `.claude/gitlab-issue.json` at the repo root, if present
   (schema below).
3. **Auto-detect** -- parse the origin remote:
   ```bash
   git remote -v
   ```
   Both forms appear: `git@<host>:<group>/<sub>/<repo>.git` and
   `https://<host>/<group>/<repo>.git`. Take the host and the full path with the
   `.git` suffix stripped.

If the host is not a GitLab instance, or no remote resolves and the user gave no
URL, ask -- do not guess a project.

Then resolve the rest at runtime. **Config always overrides detection.**

- **Labels** -- never assume label names. List what the board really has:
  ```bash
  glab label list
  ```
  Infer the groups from the `::` prefixes actually present (a project may use
  `type::`, `phase::`, `priority::`, `area::`, or none at all), and note that
  some boards mix in **unscoped** labels for a group -- e.g. a bare `Bug` label
  where you would expect `type::bug`. Use what the board has, not what you
  expect. Config `labels` may name the groups and give per-label meanings, which
  is what lets you pick correctly rather than plausibly.
- **Attribution** -- the AI-disclaimer handle:
  ```bash
  glab api user
  ```
  Take `.username`. Config `attribution` overrides it. If neither resolves,
  **omit the disclaimer line** rather than inventing a handle.
- **Spec directory** -- probe in order and use the first that exists:
  `openspec/changes/`, `specs/`, `docs/adr/`, `.openspec/`. Config `specDir`
  pins one. If none exists, skip that audit step silently.
- **Test gates** -- the commands an implementer can run to prove the work done.
  Read the real ones from `Makefile` targets, `package.json` scripts, or
  `composer.json` scripts. Config `testGates` pins the preferred ones. Never
  cite a command you have not seen defined.

## 2. Gather the task context

Take what the user gave you. If the intent is genuinely unclear (e.g. you can't
tell if it's a bug, a feature, or tech debt, or you don't know which part of the
app it touches), ask **one** focused question -- otherwise proceed and let the
audit fill the gaps.

## 3. Audit the project state

Run these in parallel where possible. The point is to ground every claim in the
issue -- don't write "the X component does Y" unless you've confirmed it.

- **Git state** -- current branch, recent commits, uncommitted changes:
  ```bash
  git status --short && git log --oneline -10 && git branch --show-current
  ```
  Use this to mention work-in-progress and to avoid filing a task for something
  already half-done on the current branch.

- **Open issues & MRs** -- find duplicates and related work (via glab skill):
  ```bash
  glab issue list --per-page 30
  glab mr list --per-page 20
  ```
  If a near-duplicate exists, **stop and tell the user** rather than creating a
  second issue. If related issues exist, link them in the body (`Related: #NN`).

- **In-flight specs** -- read the resolved spec directory, if there is one:
  ```bash
  ls <specDir> 2>/dev/null
  ```
  Read any entry whose name matches the task area. If the task belongs inside an
  active spec or change proposal, say so -- it may not need a separate issue at
  all.

- **Relevant source files** -- grep/read the files the task touches so the
  **Scope** section names real paths, not guesses. Naming exact files is what
  makes the issue actionable.

## 4. Draft the issue

Pick the template by task type. Match the house style of the issues you listed in
step 3 -- if they share a section layout, follow it; config `bodySections`
overrides. Lead `Scope` with concrete file paths.

**Feature / tech-debt / spec template:**
```markdown
> :robot: _This was written by an AI agent on behalf of @<attribution>._

## Context
<why this matters now; link related issues #NN, MRs !NN, spec changes, external refs>

## Goal
<the desired end state in one or two sentences>

## Scope -- N files
- `path/to/file` -- <what changes>
- ...

## Acceptance criteria
- <verifiable outcome>
- <build/test gate from the resolved test gates, e.g. `<command>` green>
```

**Bug template:**
```markdown
> :robot: _This was written by an AI agent on behalf of @<attribution>._

<one-line description of the broken behavior>

## Expected
<what should happen instead>

## Scope
- <files/components to inspect, from the audit>
```

Keep the AI disclaimer line when an attribution handle resolved -- it is the
convention for agent-authored issues. Drop the line entirely if none did.

## 5. Choose labels

Pick from the live label set gathered in step 1. Typical boards want a **type**
and some **stage/phase** marker, plus **priority** when you can infer it. Scoped
labels are what place the issue in the right board column, so getting them right
is the difference between a tracked task and an orphan.

- Match each group to what the work *is*, using the meanings in config
  `labels` where provided.
- Omit a group rather than guessing -- an unlabeled priority is better than a
  wrong one.
- If the board has no labels at all, skip this step and say so in the draft.

## 6. Confirm, then create

Show the user the full draft -- **title, rendered body, and chosen labels** -- and
wait for an explicit OK. Incorporate edits. Only then create.

With `-y` (see Arguments), create straight away and show the draft alongside the
resulting URL instead of before it.

Write the body to a scratchpad file to keep multiline markdown intact, then
create via the glab skill:
```bash
glab issue create \
  --title "<concise, specific title -- no trailing period>" \
  --description "$(cat /path/to/scratchpad/issue-body.md)" \
  --label "<comma-separated labels>"
```

Add the glab skill's host/project targeting flags when the target came from a URL
rather than the current repo's remote.

Report the resulting issue URL back to the user.

## Optional project config

`.claude/gitlab-issue.json` at the project root tunes the skill per project.
**Every key is optional** -- with no file at all, everything in step 1 is
auto-detected.

```json
{
  "host": "<gitlab host, if not the origin remote's>",
  "projectPath": "<group/.../repo, if not the origin remote's>",
  "attribution": "<@handle for the AI disclaimer>",
  "specDir": "openspec/changes",
  "testGates": ["make test", "make lint"],
  "labels": {
    "type": ["type::feature", "type::spec", "type::tech-debt", "Bug"],
    "phase": {
      "phase::1": "<what phase 1 covers>",
      "phase::2": "<what phase 2 covers>"
    },
    "priority": ["priority::high", "priority::medium", "priority::low"]
  },
  "bodySections": {
    "work": ["Context", "Goal", "Scope", "Acceptance criteria"],
    "bug": ["Expected", "Scope"]
  }
}
```

A label group may be a **list** (names only) or an **object** (name → meaning).
Prefer the object form for groups whose names don't explain themselves -- that
mapping is what makes the label choice informed rather than a guess.

## Notes

- **Title style**: specific and descriptive, present tense, no trailing period --
  e.g. "Persist the session token so login survives reloads", not "Fix login".
- **Don't invent acceptance criteria** you can't tie to the audit. A criterion
  like "X passes" is only useful if X is a real command or behavior in this repo.
- **Dry-run**: if the user passes `-n`, or only wants the draft (to paste
  elsewhere or review), stop after step 4--5 and output the body + labels without
  calling glab.
- If `glab` reports an auth/host error, that's a glab-skill concern -- hand off
  there rather than working around it.
