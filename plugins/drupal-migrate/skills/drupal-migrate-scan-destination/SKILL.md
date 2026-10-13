---
name: drupal-migrate-scan-destination
description: 'Scan destination Drupal config YAML and project analysis documents to propose source-to-destination field mappings for a migration, and pick the destination bundle/component for a source''s data. Use after querying source fields, when you need to know which destination bundle/fields a source bundle maps to — "what does this paragraph map to", "propose mappings for X", "which paragraph type fits this section", or before writing a migration''s process section. When Playwright is enabled and the source is a website, it can navigate the source page (local copy or live) to read its layout and match each section to the closest destination paragraph type. Read-only; never edits config.'
---

# Scan Destination Fields and Propose Mappings

Scan the destination Drupal configuration files to find the target bundle's
fields and propose source-to-destination field mappings. This is read-only
analysis — it produces proposals, it never writes config or migration YAML.

When the destination component is unclear — typically which **paragraph type** a
source page section should become — and Playwright is enabled, this skill can
navigate the rendered source page and match each visible layout section to the
closest destination paragraph type before mapping fields (see "Visual component
matching").

## Prerequisites

- Source fields queried (`drupal-migrate-query-fields`)
- Knowledge of the destination entity type and bundle (or a way to determine it)
- _(optional)_ Playwright available — the `playwright-cli` skill or a Playwright MCP
  server. Enables visual component matching; if absent, that method is skipped and the
  config/document methods are used instead.

## Input

- **dest_entity_type**: destination entity type (`node`, `paragraph`, `taxonomy_term`, `media`, `user`)
- **dest_bundle**: destination bundle machine name
- **source_fields**: list of source fields (from `drupal-migrate-query-fields`)

If no destination bundle is given, resolve it in this order — projects map
bundles differently, so don't guess:

1. Check the component-mapping CSVs / analysis documents declared in
   `.agents/references/migrate/project-config.md` → **Reference Documentation**.
   These often state the source→destination bundle directly. Read the CSV path from
   there — never hardcode a filename.
2. List available destination bundles from the project's config sync directory
   (path per `project-config.md`):
   ```bash
   ls {config_sync_dir}/core.entity_form_display.{dest_entity_type}.*.yml 2>/dev/null \
     | sed 's/.*\.\(.*\)\.default\.yml/\1/' | sort -u
   ```
3. **Visual component matching** _(when Playwright is enabled and the source is a
   website)_ — navigate the rendered source page, read its layout sections, and match
   each to the closest destination paragraph type. See the section below. Use this when
   the destination is a paragraph/component whose right type is not obvious from the
   documents, especially for page-builder content where one source page yields several
   paragraphs.
4. Ask the user to pick one, or record that mapping is TBD.

## Resolving config file prefixes

The `{config_prefix}` (field instance configs) and `{storage_prefix}` (field
storage configs) per entity type come from the shared reference — read it
instead of hardcoding the prefix pattern:
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".

The config sync directory itself is a project value — read it from
`.agents/references/migrate/project-config.md` → **Migration Infrastructure — Where To
Look**, together with `{migration_module_dir}` and `{theme_components_dir}`. Below,
`{config_sync_dir}` is that directory.

## Visual component matching (Playwright, optional)

Use this to pick the destination **component** for a source page section — usually which
paragraph type a section becomes — by looking at the rendered source page instead of
guessing from a field list. It informs the bundle/component choice; field mapping
(Steps 1–5) follows once the target bundle is chosen.

**Gate.** Only run this when Playwright is available (the `playwright-cli` skill or a
Playwright MCP server) **and** the source is a website. If neither is true, skip this
method and fall back to the document/config resolution — note that you did.

### A — Resolve a representative source URL

Prefer a **local copy** of the source site to avoid hitting production (e.g. the DDEV /
local URL in `project-config.md` → Source System). Otherwise use the live URL:

- Resolve one representative page for the source bundle with
  `drupal-migrate-resolve-examples` (it returns one live URL per parent bundle).
- For a WordPress source, the local copy's path mirrors the live permalink.

### B — Read the rendered layout

Navigate the URL with Playwright and read the page structure, not just a picture:

- Capture the rendered DOM outline (section/header/article/`<div class>` blocks, in
  order) and a screenshot. Reuse `drupal-migrate-live-screenshots` for the screenshot
  rather than re-implementing capture.
- Identify discrete layout **sections** top to bottom and name each by what it is, e.g.
  hero/banner, intro/rich-text body, card or teaser grid, accordion/FAQ, tab set, media
  gallery/carousel, quote/testimonial, stats/key-facts, logo wall, CTA block, embedded
  form. Record each section's distinguishing traits (repeating items, heading + image +
  link, collapsible rows, …) — those traits drive the match.

### C — Catalogue the destination paragraph types

List the destination paragraph bundles and what each renders, so the match is grounded:

```bash
ls {config_sync_dir}/core.entity_form_display.paragraph.*.yml 2>/dev/null \
  | sed 's/.*\.paragraph\.\(.*\)\.default\.yml/\1/' | sort -u
```

For each candidate bundle, read its fields (Step 1 method) and, if the project declares a
theme components directory in `project-config.md`, read that component to know how the
paragraph looks when rendered. A paragraph with `field_image` + `field_title` +
`field_cta` that renders as a banner is a hero candidate; a multi-value paragraph of
`title`+`body` rows is an accordion candidate.

### D — Match each section to the closest paragraph type

For every source section from B, propose the closest destination paragraph type by
structure + fields + rendered appearance. Rank candidates; never force a match:

```
#### Source layout → destination paragraph (`{source_page}`)

| Source section | Traits | Destination paragraph | Confidence | Notes |
|---|---|---|---|---|
| Hero banner | full-width image + H1 + CTA | `hero` | High | field_image + field_cta align |
| "Why us" grid | 3 repeating icon+title+text cards | `cards` | High | multi-value, cardinality -1 |
| FAQ | collapsible Q/A rows | `accordion` | Medium | verify nesting depth |
| Embedded form | iframe to external CRM | ❓ none | — | ecosystem item, not a paragraph |
```

A declared mapping in an analysis document still outranks a visual match — if the two
disagree, surface the conflict rather than silently overriding the document.

## Steps

### Step 1 — Read destination field configs

Find the bundle's field instance configs:

```bash
ls {config_sync_dir}/{config_prefix}{dest_bundle}.*.yml 2>/dev/null
```

For each YAML, extract:

- `field_name` (from filename or YAML key)
- `field_type` / `type`
- `label`
- `required`
- `translatable`
- `settings` (target bundles for entity references, allowed values, etc.)

Then read the matching field storage configs for cardinality:

```bash
ls {config_sync_dir}/{storage_prefix}*.yml 2>/dev/null
```

Extract `cardinality` from each storage config.

### Step 2 — Check analysis documents

Read the analysis documents declared in `project-config.md` → **Reference
Documentation** for any pre-determined mappings (component-mapping CSV and any other
mapping reference files). Cross-reference the source bundle against these — a declared mapping is
authoritative and outranks heuristic matching.

### Step 3 — Check existing migration configs

Look for existing migration YAML that already maps this source bundle, so you
don't propose a conflicting mapping. Search the migration module and config
locations declared in `project-config.md`, e.g.:

```bash
grep -rl "{source_bundle}" {migration_module_dir}/migrations/*.yml 2>/dev/null
grep -rl "{source_bundle}" {config_sync_dir}/migrate_plus.migration*.yml 2>/dev/null
```

If found, extract the field mapping from the `process` section.

### Step 4 — Propose field mappings

For each source field, propose a destination field using these rules, in
priority order:

1. **Existing migration**: an existing migration YAML already maps this field → reuse that mapping.
2. **Analysis-document match**: the component-mapping CSV specifies a mapping → use it.
3. **Exact machine-name match**: `{config_prefix}{dest_bundle}.{source_field_name}.yml` exists.
4. **Semantic / label match**: a destination field whose label or purpose closely matches.
5. **Type compatibility**: source and destination field types are compatible (infer via the "Value Column Suffix Patterns" table in `entity-type-context.md` when needed).
6. **No match**: mark `❌ No destination field found`.
7. **Uncertain**: mark `❓ To verify` and list all candidates.

Let population data (from `drupal-migrate-field-population`) inform decisions: a field
at 0% population is an exclusion candidate, not a mapping target.

### Step 5 — Report results

```
#### Proposed mapping → `{dest_bundle}`

| Source field | Destination field | Notes |
|---|---|---|
| `field_src_title`   | `title`             | Exact match by label |
| `field_src_email`   | `field_dst_email`   | Type compatible, ~48% populated |
| `field_src_linkedin`| ❌ Not migrated     | 0% populated |
| `field_src_image`   | `field_dst_image`   | ❓ Verify: source is `image`, dest is `entity_reference` to media |
```

If no destination bundle was provided or could be determined:

> "Destination mapping is TBD — no destination bundle was specified or could be determined from analysis documents."

## Output

- **dest_fields**: list of destination field objects
- **mapping_proposals**: list of (source_field, dest_field, confidence, notes)
- **unmapped_fields**: source fields with no destination match

## Guardrails

- Read-only: never create or modify config or migration files.
- Always check existing migration configs (Step 3) before proposing, to avoid conflicting mappings.
- A mapping declared in an analysis document outranks any heuristic match.
- 0%-populated source fields (per `drupal-migrate-field-population`) are exclusion candidates, not mapping targets.
- When type compatibility is uncertain, flag it `❓ To verify` rather than guessing.
- If the destination bundle can't be determined, skip mapping and report it as TBD — don't invent one.
- Visual component matching is **optional** — skip it (and say so) when Playwright is not enabled or the source is not a website; never block field mapping on it.
- Prefer a **local** copy of the source for browsing; only hit the live site read-only, and never submit forms or trigger writes while navigating.
- A visual match is a **proposal** — flag low-confidence matches and never override a mapping declared in an analysis document; surface the conflict instead.
