---
name: drupal-migrate-field-population
description: 'Measure how full each field of a Drupal source bundle actually is: for every field, the share of active instances that hold data, so empty (0%) and near-empty fields can be flagged as non-migration candidates. Use in a migration context only: after drupal-migrate-query-fields, when asked "which fields of the source bundle are actually used", "which source fields are empty", "is field_x worth migrating", or when trimming a bundle''s field mapping. Not for checking empty fields on the site being developed. Drupal 7 and Drupal 8+ sources only.'
---

# Measure Field Population

For each field on a source bundle, measure what percentage of active instances actually contain data. A field at 0% is a non-migration candidate — it should be explicitly excluded from the migration.

## Prerequisites

- Source database connection verified (`drupal-migrate-db-discover`)
- Fields queried (`drupal-migrate-query-fields`)
- For paragraphs: active instance count from `drupal-migrate-verify-active`

## Input

- **entity_type**: `node`, `paragraph`, `taxonomy_term`, `media`, or `user`
- **bundle**: the bundle machine name
- **fields**: list of field machine names (from `drupal-migrate-query-fields`)
- **active_instances**: count of active instances (from `drupal-migrate-verify-active` for paragraphs, or `drupal-migrate-count-instances` for others)

## Resolving table and column names

All D8+ table/column variables (`{main_table}`, `{id_column}`, `{bundle_column}`,
`{field_data_prefix}`) come from the shared reference — read it instead of hardcoding:
**`<skill base directory>/../../references/entity-type-context.md`** → "Variable Resolution Table".

Check `.agents/references/migrate/project-config.md` → "Database Connection"
for the drush database option and any project-specific table-name overrides.

## Steps

**Validate inputs first.** Check every value substituted into the queries below (entity
type, bundle, field names, ids, langcode) against the patterns in
`entity-type-context.md` → "Input validation", and stop on any mismatch. Values read from
the database (field names from `config` or `INFORMATION_SCHEMA`, ids from a previous
query) are checked the same way before reuse.

### Step 1 — Query population for each field

For each field, pick the value column for its type, then count populated rows.
Field-type → value-suffix mapping lives in the shared reference — read it instead of guessing:
**`<skill base directory>/../../references/entity-type-context.md`** → "Value Column Suffix Patterns"
(D8+ table, then "Drupal 7 suffixes" for a D7 source).

**Parameterized query (all entity types, D8+):**

```sql
SELECT
  COUNT(DISTINCT m.{id_column}) AS total_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN m.{id_column} END) AS populated
FROM {main_table} m
LEFT JOIN {field_data_prefix}{field_name} f ON f.entity_id = m.{id_column}
WHERE m.{bundle_column} = '{bundle}';
```

**Users (D8+):** `user` has no `{bundle_column}` (it is `—` in the shared reference), so
the template above expands to invalid SQL. Drop the bundle predicate and skip the
anonymous account, matching the `drupal-migrate-count-instances` denominator:

```sql
SELECT
  COUNT(DISTINCT m.uid) AS total_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN m.uid END) AS populated
FROM users_field_data m
LEFT JOIN user__{field_name} f ON f.entity_id = m.uid
WHERE m.uid > 0;
```

Apply the same `WHERE m.uid > 0` predicate (no bundle filter) to the batch query below
when the entity type is `user`.

**Paragraphs (D8+):** the query above counts every paragraph row, including detached and
historical instances, while Step 2 divides by the _active_ count. Restrict the numerator to
the same active set `drupal-migrate-verify-active` uses (attached to the current revision
of a published parent node via `{parent_field_name}`), otherwise percentages can exceed
100% and orphaned data looks migratable:

```sql
SELECT
  COUNT(DISTINCT p.id) AS active_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN p.id END) AS populated
FROM node_field_data n
JOIN node__{parent_field_name} ref
  ON ref.entity_id = n.nid AND ref.revision_id = n.vid
JOIN paragraphs_item_field_data p
  ON p.id = ref.{parent_field_name}_target_id
LEFT JOIN paragraph__{field_name} f ON f.entity_id = p.id
WHERE p.type = '{bundle}' AND n.status = 1;
```

Run it once per parent field and sum the results. For nested paragraphs, replace the
`n → ref → p` chain with the traversal from `drupal-migrate-verify-active` Step 2.

> **Important**: Use `entity_id` only in the JOIN (not `revision_id`) to avoid false negatives from revision mismatches.
> Count `DISTINCT … CASE` rather than `SUM(… IS NOT NULL)`: a multi-value field has several delta rows per entity, and `SUM` would count each populated entity once per delta, inflating `populated` past `total_instances`.

**Batch optimization** — when querying many fields, combine into a single query:

```sql
SELECT
  COUNT(DISTINCT m.{id_column}) AS total_instances,
  COUNT(DISTINCT CASE WHEN f1.{field1}_{suffix} IS NOT NULL THEN m.{id_column} END) AS pop_field1,
  COUNT(DISTINCT CASE WHEN f2.{field2}_{suffix} IS NOT NULL THEN m.{id_column} END) AS pop_field2
FROM {main_table} m
LEFT JOIN {field_data_prefix}{field1} f1 ON f1.entity_id = m.{id_column}
LEFT JOIN {field_data_prefix}{field2} f2 ON f2.entity_id = m.{id_column}
WHERE m.{bundle_column} = '{bundle}';
```

> ⚠️ Batch only works well for up to ~5 fields at a time — beyond that, MySQL may produce cartesian explosion on multi-value fields. Split into groups of 3-5. `COUNT(DISTINCT … CASE)` keeps each per-field count entity-accurate even when the joins fan out.

#### Drupal 7 differences

The shared reference is D8+. On a D7 source, field tables are named
`field_data_{field_name}` (plus `field_revision_{field_name}`), keyed by
`entity_id` / `entity_type` / `bundle` rather than the `{field_data_prefix}` form, and
the entity tables differ too: take `{main_table}`, `{id_column}` and `{bundle_column}`
from the Drupal 7 table in `drupal-migrate-count-instances` → "Drupal 7 differences"
(`node`/`nid`/`type`, `paragraphs_item`/`item_id`/`bundle`,
`taxonomy_term_data`/`tid`/`vid`, `users`/`uid`), not from the D8+ reference.
`{d7_entity_type}` is the D7 name: `paragraph` → `paragraphs_item`; `node`,
`taxonomy_term` and `user` are unchanged (`media` does not exist on D7).

**Value columns differ on D7.** Take `{value_suffix}` from the "Drupal 7 suffixes" table
in `entity-type-context.md`, not from the D8+ table: `_fid` for file and image, `_tid`
for taxonomy, `_url` for link, `_nid` for node reference, `_target_id` only for
`entityreference`. The D8+ names fail with an unknown-column error on D7. The field type
comes from `field_config.type` (see `drupal-migrate-query-fields`).

Put the `entity_type` filter in the `LEFT JOIN` condition, not in `WHERE`, or entities
without a row disappear from the denominator:

```sql
SELECT
  COUNT(DISTINCT m.{id_column}) AS total_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN m.{id_column} END) AS populated
FROM {main_table} m
LEFT JOIN field_data_{field_name} f
  ON f.entity_type = '{d7_entity_type}' AND f.entity_id = m.{id_column} AND f.deleted = 0
WHERE m.{bundle_column} = '{bundle}';
```

**Taxonomy terms (D7):** `taxonomy_term_data.vid` is a numeric vocabulary id, while
`{bundle}` is the vocabulary machine name; comparing the two returns 0 rows. Join the
vocabulary table and filter on its machine name:

```sql
SELECT
  COUNT(DISTINCT m.tid) AS total_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN m.tid END) AS populated
FROM taxonomy_term_data m
JOIN taxonomy_vocabulary v ON v.vid = m.vid
LEFT JOIN field_data_{field_name} f
  ON f.entity_type = 'taxonomy_term' AND f.entity_id = m.tid AND f.deleted = 0
WHERE v.machine_name = '{bundle}';
```

**Users (D7):** the `users` table has no bundle; use `WHERE m.uid > 0` instead of the
bundle predicate.

**Paragraphs (D7):** the generic query counts detached and archived `paragraphs_item`
rows too, while the denominator is the active count, so the same >100% error applies.
Restrict the numerator to items referenced by the current revision of a published host
(`field_data_*` holds the current revision):

```sql
SELECT
  COUNT(DISTINCT p.item_id) AS active_instances,
  COUNT(DISTINCT CASE WHEN f.{field_name}_{value_suffix} IS NOT NULL THEN p.item_id END) AS populated
FROM node n
JOIN field_data_{parent_field_name} ref
  ON ref.entity_type = 'node' AND ref.entity_id = n.nid AND ref.deleted = 0
JOIN paragraphs_item p
  ON p.item_id = ref.{parent_field_name}_value AND p.bundle = '{bundle}' AND p.archived = 0
LEFT JOIN field_data_{field_name} f
  ON f.entity_type = 'paragraphs_item' AND f.entity_id = p.item_id AND f.deleted = 0
WHERE n.status = 1;
```

Run it once per host field and sum. For nested paragraphs, replace `node n` and `ref`
with the host chain from `drupal-migrate-parent-context` (Drupal 7 differences, Step 3)
and keep the final `p → f` pair.

### Step 2 — Compute percentages

For each field:

```
population_pct = ROUND(populated / active_instances * 100)
```

Classify from the **raw `populated` count**, never from the rounded percentage:

- `populated = 0` → zero-population field (exclusion candidate).
- `populated > 0` and `population_pct = 0` → display `<1%`, not `0%`. One populated
  instance out of 340 rounds to 0 but holds real content and must stay in scope.

**Denominator choice:**

- For `paragraph`: use the active count from `drupal-migrate-verify-active` (not the total from `drupal-migrate-count-instances`).
- For `node`, `taxonomy_term`, `media`, `user`: use the total from `drupal-migrate-count-instances`.

### Step 3 — Report results

Add a **Population** column to the field table:

```
#### Field population — `{bundle}` ({active_instances} active instances)

| Field | Population |
|---|---|
| `field_title` | 100% |
| `field_subtitle` | ~48% |
| `field_extra_link` | 0% |
| `field_legacy_note` | <1% |
```

Flag fields with `populated = 0`:

> "Fields at 0% population are non-migration candidates and should be explicitly excluded."

## Output

- **field_populations**: list of (field_name, populated_count, total_count, percentage)
- **zero_population_fields**: fields with `populated = 0` that are candidates for exclusion (a `<1%` field is not one)

## Guardrails

- Use `entity_id` only (not `revision_id`) in LEFT JOINs to avoid false negatives.
- Choose the correct value column based on field type (`_value`, `_target_id`, `_uri`, etc.) — see the reference.
- Run population queries in parallel where possible to minimise elapsed time.
- If a field table doesn't exist, report it as "table not found" rather than failing.
- Use the `~` prefix for percentages that are not exact (e.g., `~48%`).
- Run queries via `drush sql:query` with the source database option from `project-config.md`.
