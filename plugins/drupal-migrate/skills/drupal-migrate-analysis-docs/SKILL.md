---
name: drupal-migrate-analysis-docs
description: 'Organize the documentation produced during a Drupal content migration so it stays readable and scoped. Use whenever you are writing up, structuring, or reorganizing migration analysis — "where should this migration doc go", "structure the migration documentation", "document the source site", "the migration docs are a mess", or before creating any new migration analysis file. Defines the as-is (current-state) vs to-be (analysis/planning) split, the plain-docs vs OpenSpec-change split, the no-duplication/reference rule, and when to use Mermaid diagrams. Source-agnostic: applies to WordPress→Drupal, Drupal→Drupal, or any source.'
---

# Organize migration analysis documentation

A migration generates two kinds of writing that must not be mixed: **facts about
what the source is today** (frozen, citable) and **analysis of what the target will
be and how to get there** (evolving, decision-bearing). Mixing them produces a
single sprawling doc that is neither a reliable audit nor a usable plan. This skill
defines how to keep them separate and how to avoid re-documenting what already
exists.

Apply this whenever you create or reorganize a migration analysis document, before
the first file and every time the corpus grows.

## Principle 1 — separate as-is from to-be

Split by scope, not by topic.

- **As-is** = the current source platform as it actually is: version, plugins/modules,
  content inventory, data model, integrations, URL/redirect state. These are frozen
  audit facts. You cite them; you do not edit them once verified except to correct an
  error or record a re-measurement (with a new date).
- **To-be** = migration analysis and planning: target architecture hypotheses,
  content mapping, decisions agreed with stakeholders, dependencies, open questions,
  next steps. These evolve as the project advances.

A fact that says "WordPress runs 24 active plugins" is as-is. A statement that says
"All in One SEO maps to Metatag + Pathauto" is to-be. The first belongs in the audit;
the second in the analysis.

## The folder layout

Put the as-is set in its own subfolder, with the to-be planning at the parent level
and an index README at the top. This is the worked example from a WordPress-multisite
to Drupal migration:

```
doc/Migrate/
├── README.md            scope statement + index (as-is vs to-be)
├── considerations.md    migration considerations / working hypotheses (to-be)
├── decisions.md         decisions agreed with stakeholders (to-be)
├── dependencies.md      pending external dependencies + next steps (to-be)
└── as-is/               current source state of the art (frozen facts)
    ├── README.md        as-is index + provenance + freeze dates
    ├── platform.md      version, multisite, plugin/module inventory, custom code
    ├── ecosystem.md     external integrations (CRM, mail, forms)
    ├── content-inventory.md   volumes, content types, multilingual
    ├── <data-model>.md  the real content model (e.g. ACF, fields, paragraphs)
    ├── <liveness>.md    URL/redirect/liveness state
    └── data/            raw probe data (CSV, exports)
```

Split a long as-is write-up into one file per concern (platform / ecosystem / content
/ data-model / liveness) rather than one monolith — each is independently navigable
and citable.

## Principle 2 — prose docs vs structured proposals

Two homes, by document nature:

- **Plain markdown** under `doc/Migrate/` for prose analysis, hypotheses, decisions,
  and audit facts.
- **OpenSpec changes** (`openspec/changes/<name>/`) for structured, reviewable
  proposals: a content-type mapping, a solution design, an issue-scoped plan with
  specs and tasks. These carry their own proposal/design/tasks lifecycle.

The `doc/Migrate/README.md` index links to both, so a reader finds the structured
proposals from the prose corpus. Convention: if it has a review/approval lifecycle,
it is an OpenSpec change; if it is reference prose, it is a markdown doc.

If the host project has no `openspec/` directory, do not create one for the migration
alone: write the proposal as plain markdown under `doc/Migrate/to-be/<name>.md` with a
`**Status:** proposed | approved` header, and say in the index that it stands in for an
OpenSpec change.

## Principle 3 — never duplicate; reference instead

Before writing any fact, check whether it is already documented. If it is, link to it
— do not restate it.

1. Search the existing corpus and the wider repo:

   ```bash
   grep -rn "<the fact / term>" doc/ openspec/ README.md CLAUDE.md AGENTS.md 2>/dev/null
   ```

   Also check ADRs (`doc/ADR/`), GitLab issues, and any project-config reference docs.

2. If the fact already lives somewhere authoritative, add a one-line reference to it
   (`see [acf-data-model.md](./as-is/acf-data-model.md)`), not a copy.

3. When you move a fact, repoint every link to it (`grep -rn` the old path) and delete
   the original — never leave the same fact in two places to drift apart.

Duplicated facts diverge; a single source with references stays correct. This applies
to the skill itself: it references the `mermaid-diagrams` skill for diagram syntax
rather than restating it.

## Principle 4 — diagram to simplify reading

When a relationship is structural — source-to-target mapping, integration topology,
a decision tree, layered architecture — a diagram reads faster than prose. Use a
Mermaid diagram in the markdown, then a short "Reading the diagram" legend.

Do not re-explain Mermaid here. The **`mermaid-diagrams`** skill carries diagram type
selection, syntax, and the design principles (kill the hairball, group, encode meaning,
legend). It is not shipped by this plugin: invoke it if it is in the available skills
list, and otherwise write the diagram from your own Mermaid knowledge and keep the
legend. Typical migration diagrams: source-platform + integrations
(flowchart), custom-code disposition (grouped flowchart), source→target content
mapping (flowchart with a collapse edge where many sources map to one target).

A diagram earns its place only when it is faster to understand than the prose it
replaces. A linear "A then B then C" is a sentence, not a diagram.

## Conventions

- Every doc opens with a status header: `**Status:**`, `**Date:**`, and a `**Part of:**`
  backlink to its index README.
- As-is docs carry a freeze date; re-measurements get a new date, not a silent edit.
- The top-level README states the as-is/to-be scope split explicitly so the reader
  knows which half they are in.
- Name files by concern (`platform.md`, `ecosystem.md`), not by section number.

## Checklist before writing a migration doc

1. Is this an as-is fact or a to-be analysis? → pick the right half.
2. Does this fact already exist somewhere? → `grep` first; reference if found.
3. Is it prose analysis or a structured proposal? → markdown vs OpenSpec change.
4. Is there a structural relationship to show? → add a Mermaid diagram + legend.
5. Does the index README link to this new doc? → add the row.
