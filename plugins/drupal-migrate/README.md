# drupal-migrate

Source-agnostic toolkit for content migrations **into Drupal** in Claude Code: a
full-lifecycle `drupal-migration-analyst` agent, atomic source-analysis skills, and a
post-migration content-verification skill. The source can be WordPress, Drupal 7,
Drupal 8+, another CMS, or a database alone.

Migration is usually a one-time effort per project — install this plugin while migrating,
uninstall it when done.

## The lifecycle

The agent guides a migration through three macro-phases (run one phase per invocation;
it re-reads the accumulated docs each run to recover prior decisions):

```
Phase 0  Source identification — source tech · single/multisite · codebase vs DB-only · DB access method
Phase 1  As-is source analysis — platform · ecosystem · content inventory · data model · IA/redirect · custom-code inventory     → doc/Migrate/as-is/
Phase 2  Mapping triage        — module/plugin mapping · content-architecture mapping · open questions · risks                  → openspec/changes/
Phase 3  Implementation        — migration issues · tech-analysis TO DO lists · Migrate pipeline scoping
```

## What's inside

**Agent**

- `drupal-migration-analyst` — autonomous full-lifecycle orchestrator. Detects the
  source, documents the as-is, triages the mapping, and scopes the implementation by
  invoking the atomic skills below and writing the doc corpus via
  `drupal-migrate-analysis-docs`.

**Phase 0 — source identification**

| Skill                           | Purpose                                                                 |
| ------------------------------- | ----------------------------------------------------------------------- |
| `drupal-migrate-detect-source`  | Gate: source tech, single/multisite, codebase-vs-DB-only, access method |
| `drupal-migrate-db-discover`    | Discover + validate the source DB connection (any access method)        |
| `drupal-migrate-detect-version` | Drupal-source sub-step: detect major version (7 vs 8+)                  |

**Phase 1 — as-is source analysis**

| Skill                              | Purpose                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------- |
| `drupal-migrate-platform-audit`    | `as-is/platform.md`: version, topology, extension inventory + activation, custom code |
| `drupal-migrate-ecosystem-map`     | `as-is/ecosystem.md`: external integrations + topology diagram                        |
| `drupal-migrate-content-inventory` | `as-is/content-inventory.md`: volumes per type, multilingual coverage                 |
| `drupal-migrate-codebase-scan`     | Custom-code disposition (replicate / replace / triage / drop / security)              |
| `drupal-migrate-ia-audit`          | Information architecture: menus, URLs, redirect + liveness                            |
| `drupal-migrate-detect-container`  | Detect group/container paragraph bundles + children (Drupal source)                   |
| `drupal-migrate-count-instances`   | Revision-safe COUNT(DISTINCT) of a bundle (Drupal source)                             |
| `drupal-migrate-verify-active`     | Determine which paragraph instances are "active"                                      |
| `drupal-migrate-query-fields`      | Inspect a bundle's field tables/columns                                               |
| `drupal-migrate-field-population`  | Measure per-field population rates                                                    |
| `drupal-migrate-parent-context`    | Resolve a paragraph's parent entity chain                                             |
| `drupal-migrate-resolve-examples`  | Resolve source node IDs to live URLs                                                  |
| `drupal-migrate-live-screenshots`  | Capture live source-page screenshots                                                  |

**Phase 2 — mapping triage**

| Skill                             | Purpose                                                                             |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| `drupal-migrate-mapping-triage`   | Bridge doc: module + content-model mapping, open questions, risks (OpenSpec change) |
| `drupal-migrate-scan-destination` | Scan the destination site for matching config                                       |

**Phase 3 — implementation**

| Skill                          | Purpose                                      |
| ------------------------------ | -------------------------------------------- |
| `drupal-migrate-tech-analysis` | Produce a technical TO DO list from an issue |

**Cross-phase**

| Skill                          | Purpose                                                              |
| ------------------------------ | -------------------------------------------------------------------- |
| `drupal-migrate-analysis-docs` | Organize the analysis doc corpus (as-is vs to-be, prose vs OpenSpec) |

**Post-migration QA skill**

- `drupal-migrate-verify-content` — navigate source + destination pages, compare content,
  check redirects (301 chains / 410 Gone), validate translations.

## Setup — the project-config file (required)

Every skill reads project-specific values (DB key, drush runner, source domains, support
table, scope rules) from a single file in the **host project**:

```
.agents/references/migrate/project-config.md
```

The skills read two files from this host path — copy both there. After
`/plugin install`, the plugin files live under the marketplace checkout in your home
directory (`PLUGIN_DIR` below); adjust the path if you installed from a local clone:

```bash
PLUGIN_DIR=~/.claude/plugins/marketplaces/sf-agents-harness/plugins/drupal-migrate
mkdir -p .agents/references/migrate

# 1. project-config.md — fill in your project's values (template provided)
cp "$PLUGIN_DIR/references/project-config.template.md" \
   .agents/references/migrate/project-config.md
# then edit project-config.md

# 2. entity-type-context.md — generic Drupal 8+ table/column maps, copy verbatim
cp "$PLUGIN_DIR/references/entity-type-context.md" \
   .agents/references/migrate/entity-type-context.md
```

`entity-type-context.md` is project-agnostic — copy it as-is (override only for a
Drupal 7 source). `project-config.md` is per-project.

A third file, `.agents/references/migrate/issue-requirements.md`, is needed only by the
"generate migration issue" flow of the analyst agent. It holds the project's migration
issue template and its fixed Definition of Done. The plugin ships no template for it
because both differ between projects: write it yourself, or let the agent ask for the
conventions when it is missing.

Without `project-config.md`, skills fall back to documented Drupal-convention defaults and
ask you for anything project-specific.

## Install

Add the `sf-agents-harness` marketplace (defined in `.claude-plugin/marketplace.json` at
the root of this repository), then install:

```
/plugin marketplace add sparkfabrik/sf-agents-harness
/plugin install drupal-migrate@sf-agents-harness
```

For a local checkout, pass the repository path instead of the GitHub slug.

## Dependencies (host project provides)

- A read-only-reachable source database. The access method depends on the source:
  `drush sql:query` for a Drupal source, `wp db query` / `ddev wp db query` for
  WordPress, a read-only `mysql` client for a raw dump — declared in `project-config.md`
  and confirmed by `drupal-migrate-detect-source`. The plugin never issues a read-write
  query against the source.
- Migration run commands (`drush migrate:*`, Robo, or Make targets) live in the host
  project — the analyst verifies results, it does not run migrations itself.
