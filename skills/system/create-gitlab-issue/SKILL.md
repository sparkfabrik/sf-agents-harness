---
name: create-gitlab-issue
argument-hint: "[-y|--yes] [-n|--dry-run] [-R group/project] [gitlab-url] <task description>"
description: >-
  Create a well-grounded GitLab issue on any GitLab instance (gitlab.com or
  self-hosted) from a short task description. Audits the project first -- git
  state, open issues and MRs, in-flight specs, and the relevant source files --
  so the issue is accurate, scoped, de-duplicated, and carries the labels the
  board actually uses. Use whenever the user wants to "open an issue", "create an
  issue", "create a GitLab issue", "file an issue on GitLab", "create a task",
  "add a ticket", "put this on the board", "file a bug", "log some tech debt", or
  otherwise turn context into a tracked work item. Host, project, labels and
  attribution are resolved at runtime, with optional per-project overrides in
  `.claude/gitlab-issue.json`. Defers to the glab skill for the API calls and
  shows a draft for approval, unless `-y`/`--yes` auto-confirms or
  `-n`/`--dry-run` stops at the draft.
---

# Create GitLab issue

Turn a short task description into a grounded GitLab issue. The audit step is the
value: a bare description is vague, often a duplicate, and rarely names the real
files or acceptance criteria.

All GitLab calls go through the **glab skill** -- it owns authentication, host
targeting, and TLS handling. Do not re-derive those rules here.

## Arguments

```
/create-gitlab-issue [-y|--yes] [-n|--dry-run] [-R group/project] [gitlab-url] <task description>
```

| Flag | Effect |
|------|--------|
| `-y`, `--yes`, `yes` | **Auto-confirm.** Full audit, then create without waiting for an OK. Print the draft and the resulting URL. |
| `-n`, `--dry-run` | **Draft only.** Stop after step 5, never call `glab issue create`. |
| a GitLab URL | Target override -- see step 1. |
| `-R <group/project>` | Target override with no URL. Consumes the next token as its value. |

**Options are recognized only in the leading run of arguments.** Consume from the
front while each token matches; the first that doesn't begins the task
description, and from there everything is prose. So `-n` in "Document the `-n`
flag in the README" is text, not a dry-run request.

Never infer a project path from a slash -- descriptions open with one all the time
(`src/auth token is not persisted` is *about* `src/auth`). Only a URL or an
explicit `-R` targets.

`-y` and `-n` are mutually exclusive; `-n` wins.

Auto-confirm skips the *approval* gate, never the *audit*. Two things still stop
you cold under `-y`: a near-duplicate issue, and an unresolvable target. Report
and stop instead of creating.

## Workflow

**resolve target → gather context → audit → draft → confirm → create.** Never
skip the audit. Never create without an explicit OK or `-y`; the issue is
outward-facing and that gate is what makes it trustworthy.

## 1. Resolve the target

First hit wins:

1. **Explicit user input** -- a GitLab URL (issue, board, project, file) or `-R`.
   Extract hostname and project path.
2. **Project config** -- `.claude/gitlab-issue.json` at the repo root (schema below).
3. **Auto-detect** -- read origin by name, so extra remotes on a fork checkout
   cannot be mistaken for it:
   ```bash
   git remote get-url origin
   ```
   Both `git@<host>:<group>/<sub>/<repo>.git` and `https://<host>/<group>/<repo>.git`
   appear. Take the host and the path with `.git` stripped.

If the host is not a GitLab instance, or nothing resolves and the user gave no
URL, ask -- do not guess a project.

**Target every call.** Per the glab skill's "Targeting a project", every `glab`
call in this skill carries both parts, written out in full:

```bash
GITLAB_HOST=<host> glab <command> -R <group/project> ...
```

An untargeted call silently falls back to the cwd's repo or gitlab.com, so labels
and duplicates come from one project while the issue is created in another.

Then resolve the rest at runtime. Config overrides detection for **labels,
attribution, spec directory, and test gates**. For **host and project path** the
precedence list above holds: an explicit URL or `-R` outranks config.

- **Labels** -- never assume names, list what the board has:
  ```bash
  GITLAB_HOST=<host> glab label list -R <group/project> --per-page 100
  ```
  `--per-page` defaults to **30**, which silently truncates a large board and
  leads you to report a group as missing. Page with `--page N` until short.
  Infer groups from the `::` prefixes actually present (`type::`, `phase::`,
  `priority::`, `area::`, or none), and watch for **unscoped** labels standing in
  for a group -- a bare `Bug` where you expect `type::bug`. Config `labels` may
  name the groups and give per-label meanings, which is what makes the pick
  informed rather than plausible.
- **Attribution** -- the AI-disclaimer handle:
  ```bash
  GITLAB_HOST=<host> glab api user | jq -r '.username'
  ```
  `glab api` has no `--jq` flag and defaults to gitlab.com or the cwd's
  authenticated host, so both the pipe and `GITLAB_HOST` matter. Config
  `attribution` overrides. If neither resolves, **ask** -- never invent a handle,
  and never create without the disclaimer the glab skill requires.
- **Spec directory** -- first that exists: `openspec/changes/`, `specs/`,
  `docs/adr/`, `.openspec/`. Config `specDir` pins one. None: skip that audit
  step silently.
- **Test gates** -- commands that prove the work done. Read real ones from
  `justfile`/`Justfile` recipes (including `sjust`/`ajust`, the team's usual
  runner), `Makefile` targets, `package.json` or `composer.json` scripts. Config
  `testGates` pins them. Never cite a command you have not seen defined.

## 2. Gather the task context

Use what the user gave you. If the intent is genuinely unclear (bug vs feature vs
tech debt, or which part of the app), ask **one** focused question -- otherwise
proceed and let the audit fill the gaps.

## 3. Audit the project state

Run in parallel where possible. Ground every claim: don't write "the X component
does Y" unless you confirmed it.

- **Git state**:
  ```bash
  git status --short && git log --oneline -10 && git branch --show-current
  ```
  Mention work-in-progress, and don't file a task already half-done on this
  branch. Only meaningful when the target *is* the current checkout -- if it came
  from a URL or `-R`, or the cwd is not a repo, skip it and say so.

- **Open issues & MRs** -- duplicates and related work:
  ```bash
  GITLAB_HOST=<host> glab issue list -R <group/project> --search "<key terms>"
  GITLAB_HOST=<host> glab issue list -R <group/project> --per-page 100
  GITLAB_HOST=<host> glab mr list -R <group/project> --per-page 100
  ```
  Search the distinctive nouns first, then scan the recent list for context. A
  plain first page cannot carry the duplicate gate: in a 200-issue backlog the
  real duplicate is rarely in the first 30, and under `-y` the gate then passes
  silently with no human in the loop.

  Near-duplicate: **stop and tell the user**. Related issues: link them
  (`Related: #NN`).

- **In-flight specs** -- if a spec directory resolved:
  ```bash
  ls <specDir> 2>/dev/null
  ```
  Read entries matching the task area. If the task belongs inside an active
  change proposal, say so -- it may not need an issue at all.

- **Relevant source files** -- grep/read what the task touches so **Scope** names
  real paths. Exact files are what make the issue actionable.

## 4. Draft the issue

**Check for project issue templates first** -- a project that ships them has
already decided what an issue looks like, and the glab skill requires honouring
them:

```bash
GITLAB_HOST=<host> glab api projects/<url-encoded-path>/templates/issues
```

If templates exist, present the choices and ask which to use, then fill it
instead of the shapes below; under `-y` pick the one matching the task type and
say which. `glab issue create --template <name>` reads the **local** repo only,
so for a remote target fetch the body via the API and pass it as the description.

Otherwise pick by task type, matching the house style of the issues listed in
step 3 (config `bodySections` overrides). Lead `Scope` with concrete paths.

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

Always keep the disclaimer line -- the glab skill mandates it on every write. No
handle from step 1: ask for one rather than dropping the line.

## 5. Choose labels

Pick from the live set gathered in step 1. Boards typically want a **type** and a
**stage/phase** marker, plus **priority** when inferable. Scoped labels are what
put the issue in the right board column.

- Match each group to what the work *is*, using config `labels` meanings.
- Omit a group rather than guess -- no priority beats a wrong one.
- No labels on the board at all: skip this step and say so in the draft.

## 6. Confirm, then create

Show the full draft -- **title, rendered body, chosen labels** -- and wait for an
explicit OK. Incorporate edits. Only then create. With `-y`, create straight away
and show the draft alongside the resulting URL.

Write the body to a scratchpad file to keep multiline markdown intact:
```bash
GITLAB_HOST=<host> glab issue create -R <group/project> \
  --title "<concise, specific title -- no trailing period>" \
  --description "$(cat /path/to/scratchpad/issue-body.md)" \
  --label "<comma-separated labels>" \
  --yes
```

`--yes` is required: without it `glab issue create` stops at its own submit
prompt, which a non-interactive shell never answers. It suppresses glab's prompt
only -- the approval gate here is the draft you showed the user.

Drop `--label` entirely when step 5 selected none. `--label ""` reaches the API
as a label name; it is not the same as omitting the flag.

Report the resulting issue URL.

## Optional project config

`.claude/gitlab-issue.json` at the project root tunes the skill per project.
**Every key is optional**; with no file, step 1 auto-detects everything.

`host` and `projectPath` apply only when the user named no target -- a URL or `-R`
outranks them. The other keys override detection.

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
Prefer the object form where names don't explain themselves.

## Notes

- **Title style**: follow the glab skill's rules, since both load together.
  Sentence case, no trailing period, under ~60 characters, noun phrase or short
  problem statement rather than an imperative or commit-shaped subject -- e.g.
  "Session token lost on reload", not "Fix login" or "fix(auth): persist token".
- **Don't invent acceptance criteria** you can't tie to the audit. "X passes" is
  only useful if X is a real command or behavior in this repo.
- **Dry-run**: with `-n`, or when the user only wants the draft, stop after steps
  4-5 and output body + labels without calling glab.
- A `glab` auth or host error is a glab-skill concern -- hand off there rather
  than working around it.
