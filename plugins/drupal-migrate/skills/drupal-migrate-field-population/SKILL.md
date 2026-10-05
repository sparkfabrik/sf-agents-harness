---
name: drupal-migrate-field-population
description: "Measure field population percentages for a source entity bundle — for each field, count how many active instances actually contain data, so fields at 0% can be flagged as non-migration candidates. Use after querying fields with drupal-migrate-query-fields, when deciding which fields are worth migrating."
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
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".

Check `.agents/references/migrate/project-config.md` → "Database Connection"
for the drush database option and any project-specific table-name overrides.

## Steps

### Step 1 — Query population for each field

For each field, pick the value column for its type, then count populated rows.
Field-type → value-suffix mapping lives in the shared reference — read it instead of guessing:
**`.agents/references/migrate/entity-type-context.md`** → "Value Column Suffix Patterns".

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
`entity_id` / `entity_type` / `bundle` rather than the `{field_data_prefix}` form.
Join on `field_data_{field_name}.entity_id = {id_column}` and filter
`entity_type = '{entity_type}'`; the value-suffix logic is otherwise the same.

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
