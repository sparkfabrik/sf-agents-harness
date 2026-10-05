---
name: drupal-migrate-tech-analysis
description: 'Read a Drupal content-migration issue (GitLab or GitHub, or issue content supplied directly) and produce a precise checkbox TO DO list of the technical tasks needed to implement it, grounded in the project''s actual codebase. Use when the user gives an issue number for a migration — "do a tech analysis of issue 175", "technical breakdown of #42", "what do we need for issue #N".'
---

# Technical Analysis of a Migration Issue

Read a migration issue and produce a precise, technically complete checkbox TO DO list for its implementation, grounded in the actual project codebase and the project's migration conventions.

## Project Configuration

Read `.agents/references/migrate/project-config.md` first — it supplies every project-specific value this skill needs:

- **Issue Tracker** → the tracker tool (`glab` or `gh`), its repository flag, and the auth check
- **Migration Infrastructure — Where To Look** → where custom migration modules, migration YAML, and destination config live (paths vary per project)
- **Output Language → Issue body** → the language to write the TO DO list in
- **Migration Patterns** / **Scope Exclusions** → project conventions and fields/bundles to exclude
- the **destination Drupal version** (the new site; D8+)

If that file is absent, ask the user for the issue tracker (GitLab or GitHub), the repository identifier, and the relevant code paths before proceeding. Do not hardcode another project's paths.

## Input

Either of:

- **Issue content** already fetched by the caller (for example the orchestrating agent):
  title, description, labels, milestone, comments. Use it as-is and skip Step 1.
- An **issue number** (e.g. `#175`, `175`, `issue 175`). Extract the number and proceed.

If neither is given, ask:

> "Which issue do you want to analyse? Please provide the issue number (e.g. 175 or #175)."

## Steps

### Step 1 — Fetch the issue from the configured tracker

Skip this step when the issue content was supplied in the invocation.

Read the **Issue Tracker** section of project-config.md: `{tracker_tool}` is `glab`
(GitLab) or `gh` (GitHub), `{repo_flag}` is the repository flag (e.g.
`-R "<group>/<project>"` or `--repo owner/name`). Use the matching skill (`glab` or
`gh`) and run the command for that tool only:

```bash
# GitLab
glab issue view <issue-number> --comments --per-page 50 {repo_flag} -F json

# GitHub
gh issue view <issue-number> --comments {repo_flag} --json title,body,labels,milestone,comments
```

- If the tracker section is missing, ask the user which tracker and repository to use,
  then **STOP** until answered.
- If `{tracker_tool}` is missing or returns an auth error, tell the user and suggest the
  tool's auth check (`glab auth status` / `gh auth status`), then **STOP**.
- If the issue is not found, tell the user, then **STOP**.

Parse the JSON and extract: **Title**, **Description** body, **labels**, **milestone**, all **comments**.

### Step 2 — Parse the issue sections

Migration issues usually follow a template — section names and language vary per project (check project-config.md). A common shape:

```
## Description     <context: which entity/bundle, from which source>
## Requirements    <business/functional requirements>
## To do           <existing task list, if any>
## Definition of Done   <acceptance criteria>
```

Summarise each section. Focus on:

- **Description**: what entity/bundle/content is migrated, and from which source?
- **Requirements**: the functional requirements.
- **To do**: does a task list already exist?
- **Definition of Done**: the acceptance criteria.
- **Comments**: read them all — they carry decisions, clarifications, scope changes, and field-mapping notes, and **take precedence over the description** when they refine it.

### Step 3 — Explore the codebase

Resolve the project's code locations from project-config.md → **Migration Infrastructure — Where To Look**, then run bash/glob/grep in parallel. Below, the `{…_dir}` placeholders are those project paths:

```bash
# 3a — existing migration plugins + YAML
grep -rl "MigrateSource\|MigrateDestination\|MigrateProcessPlugin" {custom_module_dir} --include="*.php" 2>/dev/null
find {config_sync_dir} -name "migrate_plus.migration*.yml" 2>/dev/null

# 3b — destination content type / paragraph / component
ls {config_sync_dir}/core.entity_form_display.{entity_type}.{bundle}.*.yml 2>/dev/null
ls {config_sync_dir}/field.field.{entity_type}.{bundle}.*.yml 2>/dev/null
ls -d {theme_components_dir}/*{bundle_slug}*/ 2>/dev/null

# 3c — existing tests
grep -rl "{bundle}" {custom_module_dir} --include="*.php" 2>/dev/null

# 3d — existing mock / base content
find {custom_module_dir} -name "*.yml" -path "*/content/*" 2>/dev/null | xargs grep -l "{bundle}" 2>/dev/null
```

Also read the **Reference Documentation** and **Migration Patterns** sections of project-config.md for project-specific files and conventions to consult (reference-doc directory, component naming, test framework, access-control model — all project-defined).

### Step 4 — Assess migration scope and complexity

From Steps 2–3, determine what applies:

1. Source entity type and bundle
2. Destination entity type and bundle (on the destination Drupal version from project config)
3. Field mapping status (existing vs new fields)
4. Media / file handling
5. Paragraph nesting depth
6. Multilingual handling — for the project's configured languages
7. Taxonomy references that must migrate first
8. User references
9. URL alias migration
10. Access-control requirements (if the project uses an access model)

> **Note**: If a source analysis already exists (via the `drupal-migration-analyst` agent or the atomic `drupal-migrate-*` skills), reference those results instead of re-investigating.

### Step 5 — Produce the technical TO DO list

**Derive the tasks from this issue, don't emit a template.** The output is the specific work _this_ issue requires — read from its Requirements, Definition of Done, comments, and what the Step 3 codebase scan showed already exists. A field that's already configured, a migration that already exists, a capability the issue doesn't touch → no task. The right list for a small issue is a few lines; only a genuinely broad migration warrants many groups.

Write each task concretely: real machine names, field types, file paths, class names (resolved from project config — never emit the `{…}` placeholders). A reader should be able to act on a task without re-reading the issue.

Group the tasks you actually have under whatever headings fit. The checklist below is a **memory aid to test for gaps** — for each item ask "does this issue need it?" and include it only if yes. It is not a skeleton to fill in.

<details><summary>Consideration checklist (include only what the issue needs)</summary>

- **Source analysis** — run the source-analysis skills for the bundle; confirm total vs. active counts; repeat for child bundles if it's a container.
- **Destination fields/config** — new/changed fields on the destination bundle; form & view displays; new paragraph type / component / image style / media type / taxonomy.
- **Migration plugins** — source plugin; process plugins for non-trivial transforms; migration YAML; `migration_dependencies`.
- **Media & files** — files → managed files; images → media entities; URI rewriting.
- **URL aliases** — alias migration; conflict checks.
- **Multilingual** — `langcode` handling; per-language migrations (only if the project is multilingual and the issue has translated content).
- **Access control** — group/access configuration (only if the project uses one and the issue needs it).
- **Fixtures & tests** — mock content; a test in the project's framework; QA.
- **Documentation** — reference docs; common fields / roles / permissions updates.
- **Final validation** — run locally; verify in admin UI and frontend; confirm every Definition of Done item.

</details>

## Output format

```
## Technical TO DO — Issue #<iid>: <title>

> **Summary**: <2–3 sentence summary>
>
> **Source**: <entity_type>.<bundle> (D7/D8+) → **Destination**: <entity_type>.<bundle> (destination version)
> **Complexity**: Low / Medium / High — <justification>

### TO DO
(only the tasks this issue actually requires, grouped under fitting headings)
```

After presenting, add:

> ℹ️ This list was generated from the issue description and a codebase scan. Review it with the team before starting implementation.

## Guardrails

- Derive tasks from the issue's requirements + the codebase scan — don't pad with standard tasks the issue doesn't need. A small issue gets a short list.
- Be specific: use the project's actual machine names, file paths, and class names — resolve placeholders from project-config.md, never emit them literally.
- If the destination bundle can't be determined, ask the user.
- If the issue already has a TO DO list, acknowledge it and produce a more detailed version.
- Do not modify the issue — output only.
- Write the output in the language set by project-config.md → **Output Language → Issue body**.
- Run codebase-exploration queries in parallel.
- Always use the tracker tool and repository flag from project config; never assume GitLab or GitHub.
