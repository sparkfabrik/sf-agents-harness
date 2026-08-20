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

If the target resolves to a GitHub project, **stop** and use the `gh` skill
instead. This applies to the auto-detected case only: a GitLab URL in the prompt
wins over the current repo's remote, so a GitLab target given explicitly from
inside a GitHub-hosted checkout is valid work, not a reason to bail.

## Arguments

Invocation shape:

```
/create-gitlab-issue [-y|--yes] [-n|--dry-run] [-R group/project] [gitlab-url] <task description>
```

| Flag | Effect |
|------|--------|
| `-y`, `--yes`, `yes` | **Auto-confirm.** Run the full audit, then create without waiting for an OK. Print the draft you used and the resulting URL. |
| `-n`, `--dry-run` | **Draft only.** Stop after step 5, never call `glab issue create`. |
| a GitLab URL | Target override -- see step 1. |
| `-R <group/project>` | Target override for a project path with no URL. |

**Options are recognized only in the leading run of arguments.** Consume them
from the front while each token matches; the first token that doesn't begins the
task description, and from there everything is prose -- a flag-looking token
inside it is part of the task, not an option. So `-n` in
"Document the `-n` flag in the README" is text, not a dry-run request.

A bare project path is **never** inferred from a slash: a task description often
opens with one (`/create-gitlab-issue src/auth token is not persisted across
reloads` is about `src/auth`, it does not target it). Only a full GitLab URL, or
a path passed explicitly after `-R`, counts as a target.

`-R` takes the next token as its value, so consume the pair together while
scanning the leading run.

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
3. **Auto-detect** -- read the origin remote by name, so extra remotes on a fork
   checkout cannot be mistaken for it:
   ```bash
   git remote get-url origin
   ```
   Both forms appear: `git@<host>:<group>/<sub>/<repo>.git` and
   `https://<host>/<group>/<repo>.git`. Take the host and the full path with the
   `.git` suffix stripped.

If the host is not a GitLab instance, or no remote resolves and the user gave no
URL, ask -- do not guess a project.

### Carry the target on every call

Once resolved, **every** `glab` call in this skill is targeted explicitly, per the
glab skill's "Targeting a project" section:

```bash
GITLAB_HOST=<host> glab <command> -R <group/project> ...
```

An untargeted call falls back to the current directory's repo, or to gitlab.com.
That is the failure that makes an audit worthless without looking wrong: labels
and open issues come from the local project while the issue is created in the
target one, so duplicate detection means nothing and the labels do not exist on
the board being written to. The shorthand `<target>` below stands for the
`GITLAB_HOST=... -R ...` pair; write it out in full on every real invocation.

Then resolve the rest at runtime. For **labels, attribution, spec directory, and
test gates**, config overrides detection. For **host and project path** the
precedence list above stands: an explicit URL or `-R` from the user outranks
`host`/`projectPath` in config.

- **Labels** -- never assume label names. List what the board really has:
  ```bash
  GITLAB_HOST=<host> glab label list -R <group/project> --per-page 100
  ```
  `--per-page` defaults to **30**, so the bare command silently truncates a large
  board and leads you to report that a label group does not exist. Raise it, and
  page with `--page N` until a short page comes back.
  Infer the groups from the `::` prefixes actually present (a project may use
  `type::`, `phase::`, `priority::`, `area::`, or none at all), and note that
  some boards mix in **unscoped** labels for a group -- e.g. a bare `Bug` label
  where you would expect `type::bug`. Use what the board has, not what you
  expect. Config `labels` may name the groups and give per-label meanings, which
  is what lets you pick correctly rather than plausibly.
- **Attribution** -- the AI-disclaimer handle:
  ```bash
  GITLAB_HOST=<host> glab api user | jq -r '.username'
  ```
  `glab api` has no `--jq` flag, and it defaults to gitlab.com or the current
  directory's authenticated host, so both the pipe and `GITLAB_HOST` matter: the
  bare call can return an identity from the wrong instance. Config `attribution`
  overrides the result. If neither resolves, **ask the user for the handle** and
  never invent one. Do not fall back to creating the issue without the
  disclaimer: the glab skill requires it on every write.
- **Spec directory** -- probe in order and use the first that exists:
  `openspec/changes/`, `specs/`, `docs/adr/`, `.openspec/`. Config `specDir`
  pins one. If none exists, skip that audit step silently.
- **Test gates** -- the commands an implementer can run to prove the work done.
  Read the real ones from `justfile`/`Justfile` recipes (including `sjust`/`ajust`
  recipes, the team's usual runner), `Makefile` targets, `package.json` scripts,
  or `composer.json` scripts. Config `testGates` pins the preferred ones. Never
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
  already half-done on the current branch. This step only means anything when the
  target *is* the current checkout. If the target came from a URL or `-R`, or the
  cwd is not a git repository, skip it and say so rather than reporting another
  project's branch state.

- **Open issues & MRs** -- find duplicates and related work (via glab skill):
  ```bash
  GITLAB_HOST=<host> glab issue list -R <group/project> --search "<key terms>"
  GITLAB_HOST=<host> glab issue list -R <group/project> --per-page 100
  GITLAB_HOST=<host> glab mr list -R <group/project> --per-page 100
  ```
  Search first with the distinctive nouns from the task description, then scan the
  recent list for context. A plain first page cannot carry the duplicate gate: on
  a backlog of 200 open issues the real duplicate is usually not in the first 30,
  and the gate then passes silently -- which under `-y` means a second issue gets
  created with no human in the loop.

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

**Check for project issue templates first.** A project that ships templates has
already decided what an issue looks like there, and the glab skill requires
honouring them:

```bash
GITLAB_HOST=<host> glab api projects/<url-encoded-path>/templates/issues
```

If templates exist, present the choices and ask which to use, then fill that
template instead of the shapes below. Under `-y`, pick the one whose name matches
the task type and say which you picked. `glab issue create --template <name>`
loads templates from the **local** repository only, so it works when the target is
the current checkout; for a remote target, fetch the template body via the API and
pass it as the description.

With no project templates, pick by task type. Match the house style of the issues
you listed in step 3 -- if they share a section layout, follow it; config
`bodySections` overrides. Lead `Scope` with concrete file paths.

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

Always keep the AI disclaimer line: the glab skill mandates it on every write.
If no handle resolved in step 1, ask for one rather than dropping the line.

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
GITLAB_HOST=<host> glab issue create -R <group/project> \
  --title "<concise, specific title -- no trailing period>" \
  --description "$(cat /path/to/scratchpad/issue-body.md)" \
  --label "<comma-separated labels>" \
  --yes
```

`--yes` is required, not optional: without it `glab issue create` stops at its own
submit confirmation prompt, which never gets answered from a non-interactive
shell. It suppresses glab's prompt only. The approval gate in this skill is the
draft you showed the user above.

Drop the `--label` flag entirely when step 5 selected no labels. An empty
`--label ""` is sent to the API as a label name, it is not the same as omitting
it.

Report the resulting issue URL back to the user.

## Optional project config

`.claude/gitlab-issue.json` at the project root tunes the skill per project.
**Every key is optional** -- with no file at all, everything in step 1 is
auto-detected.

`host` and `projectPath` apply only when the user named no target. A URL or `-R`
in the invocation outranks them. The remaining keys override detection.

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

- **Title style**: follow the glab skill's issue-title rules, since both skills
  are loaded together. Sentence case, no trailing period, under roughly 60
  characters, and a noun phrase or short problem statement rather than an
  imperative or a commit-shaped subject -- e.g. "Session token lost on reload",
  not "Fix login" and not "fix(auth): persist session token".
- **Don't invent acceptance criteria** you can't tie to the audit. A criterion
  like "X passes" is only useful if X is a real command or behavior in this repo.
- **Dry-run**: if the user passes `-n`, or only wants the draft (to paste
  elsewhere or review), stop after step 4--5 and output the body + labels without
  calling glab.
- If `glab` reports an auth/host error, that's a glab-skill concern -- hand off
  there rather than working around it.
