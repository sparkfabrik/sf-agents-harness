---
name: drupal-migrate-count-instances
description: 'Count how many instances of a Drupal entity bundle (node, paragraph, taxonomy term, media, or user) exist in a source migration database, using revision-safe COUNT(DISTINCT) queries that avoid inflation from revisions and language variants. Use this whenever migration planning needs a count — "how many X are there", "count the Y paragraphs", sizing a bundle before migrating it, or checking whether a bundle has any data at all. Reports both total and active (published) counts.'
---

# Count Source Entity Instances

Count entity instances in the source database with revision-safe `COUNT(DISTINCT)` queries.

A single entity often has many rows in its data table — one per revision × language. `COUNT(*)` therefore overcounts, sometimes by 5–70×. Counting distinct IDs is the only way to get the real number, which is why every query below uses `COUNT(DISTINCT {id_column})`.

## Prerequisites

- Source DB connection verified (`drupal-migrate-db-discover`)
- Source Drupal version detected (`drupal-migrate-detect-version`)

## Input

- **entity_type**: `node`, `paragraph`, `taxonomy_term`, `media`, or `user`
- **bundle**: the bundle machine name (node type, paragraph type, or vocabulary id)

If `entity_type` is not given, resolve it in this order — projects name bundles
differently, so don't guess from a fixed word list:

1. Check the bundle→entity-type mapping in `.agents/references/migrate/project-config.md`.
2. Otherwise infer from how the source uses the bundle (a top-level page vs. an
   embedded component vs. a category list).
3. If still ambiguous, ask the user rather than risk querying the wrong table.

## Resolving table and column names

All D8+ table/column variables (`{main_table}`, `{base_table}`, `{id_column}`,
`{bundle_column}`, `{status_column}`) come from the shared reference — read it
instead of hardcoding:
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".

Check `.agents/references/migrate/project-config.md` for any project-specific
table-name overrides.

### Drupal 7 differences

The shared reference is D8+. On a D7 source, substitute these instead:

| Entity type     | Main table           | ID column | Bundle column                                   |
| --------------- | -------------------- | --------- | ----------------------------------------------- |
| `node`          | `node`               | `nid`     | `type`                                          |
| `paragraph`     | `paragraphs_item`    | `item_id` | `bundle`                                        |
| `taxonomy_term` | `taxonomy_term_data` | `tid`     | `vid` (join `taxonomy_vocabulary.machine_name`) |
| `user`          | `users`              | `uid`     | —                                               |

## Steps

### Step 1 — Count total instances (revision-safe)

**Drupal 8+:**

```sql
SELECT {bundle_column}, COUNT(DISTINCT {id_column}) AS instances
FROM {main_table}
WHERE {bundle_column} = '{bundle}'
GROUP BY {bundle_column};
```

**Drupal 8+ (users):** `user` has no bundle column (`{bundle_column}` is `—` in the
shared reference), so the parameterized query above does not apply. Count without a
bundle predicate and skip the anonymous account:

```sql
SELECT COUNT(DISTINCT uid) AS instances
FROM users_field_data
WHERE uid > 0;
```

**Drupal 7 (nodes):**

```sql
SELECT type, COUNT(DISTINCT nid) AS instances
FROM node WHERE type = '{bundle}' GROUP BY type;
```

**Drupal 7 (users):**

```sql
SELECT COUNT(DISTINCT uid) AS instances FROM users WHERE uid > 0;
```

**Drupal 7 (taxonomy terms):**

```sql
SELECT v.name AS vocabulary, COUNT(DISTINCT td.tid) AS instances
FROM taxonomy_term_data td
JOIN taxonomy_vocabulary v ON td.vid = v.vid
WHERE v.machine_name = '{bundle}' GROUP BY v.name;
```

If the query errors with an unknown table, the name may be customized — list candidates and retry:

```sql
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME LIKE '%{entity_type}%'
ORDER BY TABLE_NAME;
```

### Step 2 — Count active (published) instances

For entity types that have a `{status_column}` (node, taxonomy_term, media),
follow the exact query in `entity-type-context.md` → "Active Definition Per Entity Type":

```sql
SELECT COUNT(DISTINCT {id_column}) AS active_instances
FROM {main_table}
WHERE {bundle_column} = '{bundle}' AND {status_column} = 1;
```

For `user` (no bundle column):

```sql
SELECT COUNT(DISTINCT uid) AS active_instances
FROM users_field_data
WHERE uid > 0 AND status = 1;
```

**Drupal 7:** the shared reference is D8+; use these instead.

```sql
-- nodes: the `node` table carries `status`
SELECT COUNT(DISTINCT nid) AS active_instances
FROM node WHERE type = '{bundle}' AND status = 1;

-- users: `users_field_data` does not exist on D7
SELECT COUNT(DISTINCT uid) AS active_instances
FROM users WHERE uid > 0 AND status = 1;
```

D7 `taxonomy_term_data` has no `status` column, so every term is published: report
`active_instances = instances` from Step 1 and note "D7 terms have no status; active =
total" in the report. D7 `media` does not exist as an entity type (files live in
`file_managed`); treat a `media` request on a D7 source as out of scope and say so.

> **Paragraphs** have no meaningful status column — "active" means attached to a
> published parent node's current revision. Use `drupal-migrate-verify-active` for that count.

### Step 3 — Report

```
Entity: {entity_type}.{bundle}
Total instances (revision-safe): {count}
Active (published) instances: {active_count}
```

If the total is 0:

> ⚠️ No instances of `{entity_type}.{bundle}` found in the source DB. Verify the bundle machine name is correct.

## Output

- **entity_type** / **bundle**: what was queried
- **instance_count**: revision-safe total
- **active_count**: published total (or "via drupal-migrate-verify-active" for paragraphs)
- **id_column**: column used for DISTINCT counting

## Guardrails

- **Never `COUNT(*)`** — always `COUNT(DISTINCT {id_column})`. Data tables hold one row per entity × revision × language, so `COUNT(*)` inflates the count.
- If the expected table doesn't exist, list `INFORMATION_SCHEMA` candidates and inform the user — don't silently report 0.
- Run queries via `drush sql:query` with the source database option.
