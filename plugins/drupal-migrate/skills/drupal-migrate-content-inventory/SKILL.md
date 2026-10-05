---
name: drupal-migrate-content-inventory
description: 'Produce the as-is content-inventory document for a migration into Drupal — the content volumes the source holds today. Counts entities per content type / post type (published vs total), measures multilingual coverage, and for a multisite source breaks volume down per site. Use during Phase 1 as-is analysis when asked to "inventory the content", "how many posts/nodes are there", "what content types exist", or "measure the multilingual coverage". Writes as-is/content-inventory.md per the drupal-migrate-analysis-docs skill.'
---

# Content inventory (as-is)

Count what the source holds, by type, as frozen facts. The volumes size the migration
and surface the dominant types; multilingual coverage sizes the translation work.

## Prerequisites

- `drupal-migrate-detect-source` + `drupal-migrate-db-discover` have run (source tech,
  topology, access method).
- Read `drupal-migrate-analysis-docs` before writing.

## Steps

### Step 1 — Read config + recover

Read `project-config.md`. Check for an existing `as-is/content-inventory.md`;
update/cite rather than rewrite. Use the db-discover access method.

### Step 2 — Count per content type

Count published vs total per type, revision-safe:

- **WordPress:** group `{prefix}posts` by `post_type` and `post_status`:

  ```sql
  SELECT post_type, post_status, COUNT(*) AS n
  FROM {prefix}posts
  GROUP BY post_type, post_status ORDER BY n DESC;
  ```

  For multisite, repeat per blog prefix (or aggregate across blogs and note the split).

- **Drupal:** count distinct entities per bundle (reuse `drupal-migrate-count-instances`
  for the revision-safe `COUNT(DISTINCT)` pattern rather than re-deriving it).

Record the dominant types — they drive migration priority.

### Step 3 — Multilingual coverage

Establish the languages and how much content is actually translated (not just whether a
translation plugin is installed):

- **WordPress + WPML:** translated-content rows in `{prefix}icl_translations`; coverage
  per language and, for multisite, per blog.
- **Drupal:** `langcode` distribution and content-translation rows per bundle.

State coverage as numbers ("it/en on the main site + 133 subsites; per-subsite
translated-content volume unmeasured") — an unmeasured gap is itself a finding.

### Step 4 — Write the doc

Write `doc/Migrate/as-is/content-inventory.md` per `drupal-migrate-analysis-docs`:
status header, a volume table per type (published / total), a multilingual-coverage
section, and for multisite a per-site or aggregated breakdown. Add the row to
`as-is/README.md`.

## Output

- `doc/Migrate/as-is/content-inventory.md` written (path reported).
- A summary: total content volume, the dominant types, languages + coverage, and any
  unmeasured gap.

## Guardrails

- **Counts from the live DB**, revision-safe (distinct entities, not revision rows).
- **No content-type mapping** — that is Phase 2. Here: what exists and how much.
- **Read-only** via the db-discover method.
- The real content model (ACF groups, paragraph nesting, field-level detail) is the
  **data-model** doc, not this one — reference it; don't restate it here.
