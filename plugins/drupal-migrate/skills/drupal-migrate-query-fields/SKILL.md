---
name: drupal-migrate-query-fields
description: 'Query the field definitions of a source entity bundle from a migration database — base fields plus configurable fields, with label, machine name, type, cardinality, required, and translatable. Use when migration planning needs a bundle''s field list, e.g. "what fields does X have in the source", "list the fields on the old site''s Y paragraph", "what''s the structure of this source content type", or before mapping a bundle to its destination. Drupal 7 (field_config_instance) and Drupal 8+ (config table) sources only.'
---

# Query Source Entity Fields

Extract field definitions for a specific entity bundle from the source migration database.

---

## Project Configuration

Before executing, read `.agents/references/migrate/project-config.md` for the
drush database option (which source DB to query) and any project-specific table-name
overrides. Run all queries via `drush sql:query` with that database option — never `mysql` directly.

---

## Prerequisites

- Source database connection verified (`drupal-migrate-db-discover`)
- Source Drupal version detected (`drupal-migrate-detect-version`)

---

## Input

- **entity_type**: `node`, `paragraph`, `taxonomy_term`, `media`, or `user`
- **bundle**: The bundle machine name
- **source_version**: `drupal7` or `drupal8+`

---

## Entity-Type Context

Before running any query, resolve entity-type-specific variables from:
**`<skill base directory>/../../references/entity-type-context.md`**

Use `{main_table}`, `{base_table}`, `{id_column}`, `{field_data_prefix}`, `{config_prefix}`, and `{storage_prefix}` from that reference.

> **UUID location**: UUIDs are always in `{base_table}`, **never** in `{main_table}`.

---

## Steps

**Validate inputs first.** Check every value substituted into the queries below (entity
type, bundle, field names, ids, langcode) against the patterns in
`entity-type-context.md` → "Input validation", and stop on any mismatch. Values read from
the database (field names from `config` or `INFORMATION_SCHEMA`, ids from a previous
query) are checked the same way before reuse.

### Step 0 — Enumerate base fields

Before querying configurable fields, list the **base fields** for the entity type.
Branch on `source_version`:

- **Drupal 8+**: from the Entity-Type Context reference
  (`<skill base directory>/../../references/entity-type-context.md`, section "Base Fields Per Entity
  Type").
- **Drupal 7**: that reference does not apply (no `langcode`, `uuid`, `parent_id` or
  `created` on a D7 paragraph, for example). Use the real columns of the D7 entity tables:

  | Entity type     | Table                | Base columns                                                                                                       |
  | --------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------ |
  | `node`          | `node`               | `nid`, `vid`, `type`, `language`, `title`, `uid`, `status`, `created`, `changed`, `promote`, `sticky`, `translate` |
  | `paragraph`     | `paragraphs_item`    | `item_id`, `revision_id`, `bundle`, `field_name`, `archived`                                                       |
  | `taxonomy_term` | `taxonomy_term_data` | `tid`, `vid`, `name`, `description`, `format`, `weight`                                                            |
  | `user`          | `users`              | `uid`, `name`, `mail`, `status`, `created`, `access`, `login`, `language`                                          |

  Required on D7: `title` and `type` (node), `bundle` (paragraph), `name` and `vid`
  (term), `name` (user); the rest are optional and measured.

Include these in the field report with:

- Cardinality: `1`
- Translatable: per entity type (typically `✓` for node title, `✗` for IDs)
- Required: `✓` only for columns the entity cannot be saved without (`title`, `name`,
  `langcode`, `status`, `uid`, `created`, `changed`, `uuid`). Optional base columns such as
  `taxonomy_term_field_data.description__value`, `sticky`, `promote`, `weight`, `mail`
  are **not** required.
- Population: measure it like any other field in `drupal-migrate-field-population`
  (`COUNT(DISTINCT id) WHERE <column> IS NOT NULL AND <column> <> ''`). A column that
  exists is not a column that holds data; an empty term description must not report
  `100%`.

### Step 1 — Query field configs

**Drupal 8+** — Fetch field instance configs:

```sql
SELECT name, data FROM config
WHERE name LIKE CONCAT('field.field.', '{entity_type}', '.', '{bundle}', '.%')
ORDER BY name;
```

Parse the PHP-serialized `data` to extract:

- `label` (`s:5:"label";s:N:"..."`)
- `required` (`s:8:"required";b:1`)
- `translatable` (`s:12:"translatable";b:1`)

Then fetch field storage configs for type and cardinality:

```sql
SELECT name, data FROM config
WHERE name IN (
  SELECT CONCAT('field.storage.', '{entity_type}', '.', SUBSTRING_INDEX(name, '.', -1))
  FROM config
  WHERE name LIKE CONCAT('field.field.', '{entity_type}', '.', '{bundle}', '.%')
)
ORDER BY name;
```

Parse to extract:

- `field_type` (from storage: `s:4:"type";s:N:"..."`)
- `cardinality` (from storage: `s:11:"cardinality";i:1` or `i:-1`)

**Drupal 7** — Fetch from field_config tables. `field_config` exposes `type`,
`cardinality` and `translatable` as real columns; `label` and `required` exist only
inside the PHP-serialized `field_config_instance.data` blob, so select that blob and
parse it. D7 has no `paragraph` entity type: map `paragraph` → `paragraphs_item`
(`media` does not exist on D7; `node`, `taxonomy_term`, `user` are unchanged).

```sql
SELECT
  fci.field_name,
  fcs.type         AS field_type,
  fcs.cardinality,
  fcs.translatable,
  fci.data         AS instance_data
FROM field_config_instance fci
JOIN field_config fcs ON fci.field_name = fcs.field_name
WHERE fci.entity_type = '{d7_entity_type}'
  AND fci.bundle      = '{bundle}'
  AND fci.deleted = 0
  AND fcs.deleted = 0
ORDER BY fci.field_name;
```

Parse `instance_data` to extract `label` (`s:5:"label";s:N:"..."`) and `required`
(`s:8:"required";i:1` or `b:1`).

### Step 2 — Cross-check with INFORMATION_SCHEMA (D8+ fallback)

If parsing serialized data is ambiguous, verify field types by inspecting column names.
Field tables are per entity type, not per bundle: `{entity_type}__field_x` exists as soon
as any bundle of that type has `field_x`. Restrict the inspection to this bundle's
fields, or the report lists fields of other bundles.

**Field names known from Step 1** (the `field.field.{entity_type}.{bundle}.*` config rows
listed, only their `data` failed to parse): inspect exactly those tables.

```sql
SELECT
  REPLACE(TABLE_NAME, CONCAT('{entity_type}', '__'), '') AS field_name,
  GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION SEPARATOR ', ') AS value_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('{entity_type}__{field_1}', '{entity_type}__{field_2}')
  AND COLUMN_NAME NOT IN ('bundle','deleted','entity_id','revision_id','langcode','delta')
GROUP BY TABLE_NAME
ORDER BY TABLE_NAME;
```

**No usable config rows**: list every candidate table with the query above, replacing
the `IN (...)` predicate with `TABLE_NAME LIKE CONCAT('{entity_type}', '\_\_%')`,
then keep a table only when it holds rows for this bundle:

```sql
SELECT 1 FROM {entity_type}__{field_name} WHERE bundle = '{bundle}' LIMIT 1;
```

A field attached to the bundle but never filled has no rows and cannot be found this
way. Say so in the report: the list may miss empty fields.

Map the resulting column suffixes to field types using the **"Value Column Suffix
Patterns"** table in `<skill base directory>/../../references/entity-type-context.md` — don't
duplicate it here.

### Step 3 — Report results

Output the structured field table:

```
#### Source fields — `{bundle}`

| Label | Machine name | Field type | Cardinality | Required | Translatable |
|---|---|---|---|---|---|
| Title | `field_title` | string | 1 | ✓ | ✓ |
| Body | `field_body` | text_long | 1 | | ✓ |
| Items | `field_items` | entity_reference_revisions | unlimited | | |
```

- Use `✓` for Required/Translatable when true; leave blank otherwise
- Cardinality: use numeric value (`1`, `3`, …) or `unlimited` for `-1`

---

## Output

- **fields**: List of field objects with:
  - `label`, `machine_name`, `field_type`, `cardinality`, `required`, `translatable`

---

## Guardrails

- Support both D7 (`field_config_instance`) and D8+ (`config` table) query patterns — pick by `source_version`
- If config table parsing fails, fall back to INFORMATION_SCHEMA column inspection
- Report ALL fields, including entity reference and revision fields — these are important for understanding data relationships
- Do not skip fields even if their type cannot be fully determined — report them with a "unknown" type note
- Run queries via `drush sql:query` with the source database option — never `mysql` directly
