---
name: drupal-migrate-resolve-examples
description: "Resolve live URLs for example nodes from the source Drupal database — one representative node per parent bundle. Compulsory step in every full source analysis. Does NOT take screenshots (use drupal-migrate-live-screenshots for that)."
---

# Resolve live example URLs

Resolves at least one representative live URL per parent node bundle for a given source paragraph (or entity) bundle. This is a **required, automatic step** — no user confirmation needed.

---

## Inputs

Required context (available from prior skills in the analysis workflow):

- Source bundle name (the bundle being analysed)
- Parent node bundles and example node IDs (from `drupal-migrate-parent-context` + `drupal-migrate-verify-active`)
- Project config from `.agents/references/migrate/project-config.md` — check for a `## Live URL Resolution` section that may override the default resolution strategy below

---

## Entity-Type Context

Before running any query, resolve entity-type-specific variables from:
**`.agents/references/migrate/entity-type-context.md`**

Use `{has_direct_url}` and `{base_table}` from that reference to determine the resolution strategy.

---

## Steps

### Step 0 — Entity-type guard

Pick the resolution strategy for the entity type from
**`.agents/references/migrate/entity-type-context.md`** → "URL Resolution Strategy
Per Entity Type". In short: `node` is direct, `paragraph` / `taxonomy_term` / `media`
resolve indirectly via parent/referencing nodes, and `user` is skipped (no public URL).

If `user`, output "N/A — no public URL" and stop. For all other types, continue.

### 1. Check for project-specific URL resolution

Read `.agents/references/migrate/project-config.md`. If it defines a `## Live URL Resolution` section with a custom method (e.g., `endpoint`, `json_file`, `url_pattern`), **follow those instructions instead of the default steps below**.

If no custom method is defined, proceed with the **default Drupal path_alias strategy**.

---

### Default strategy — Drupal `path_alias` table

#### 2. Select representative node IDs

**For `node` entity type** — pick one published node per bundle:

```sql
SELECT DISTINCT n.nid
FROM node_field_data n
WHERE n.type = '{node_bundle}'
  AND n.status = 1
ORDER BY n.nid ASC
LIMIT 1;
```

**For `paragraph` entity type** — use the parent node IDs already identified by `drupal-migrate-parent-context` / `drupal-migrate-verify-active`. Pick one published parent node per parent bundle.

**For `taxonomy_term` and `media` entity types** — both resolve the same way: find a published node that references the entity. Substitute per type:

| Entity type     | `{ref_id_column}` | `{ref_source_table}`       | `{ref_bundle_column}` |
| --------------- | ----------------- | -------------------------- | --------------------- |
| `taxonomy_term` | `tid`             | `taxonomy_term_field_data` | `vid`                 |
| `media`         | `mid`             | `media_field_data`         | `bundle`              |

```sql
-- Step A: enumerate every node reference field. No field name is known yet, so
-- list all `*_target_id` columns in node__field_* tables; each row yields one
-- candidate `{field_name}` (strip the `node__` prefix from TABLE_NAME).
SELECT TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME LIKE 'node\_\_field\_%'
  AND COLUMN_NAME LIKE '%\_target\_id'
ORDER BY TABLE_NAME;

-- Step A2: keep only candidates whose storage targets the requested entity type.
-- Node, term and media IDs overlap, so a numeric join alone cannot tell a node
-- reference holding 7 from term 7. Read the target type from the storage config
-- (one row per candidate; `{field_name}` without the `node__` prefix):
SELECT name, data
FROM config
WHERE name = CONCAT('field.storage.node.', '{field_name}')
  AND data LIKE CONCAT('%s:11:"target_type";s:', LENGTH('{entity_type}'), ':"', '{entity_type}', '"%');
-- Keep the candidate only when this returns a row. Discard the others.

-- Step B: test each remaining candidate in turn against the requested bundle; stop
-- on the first query that returns rows. Join the bundle's source table to the
-- reference table and filter there, so any referenced entity of the bundle
-- qualifies; limit only the resulting nodes.
SELECT DISTINCT n.nid, n.type
FROM node_field_data n
JOIN node__{field_name} f ON f.entity_id = n.nid AND f.revision_id = n.vid
JOIN {ref_source_table} r ON r.{ref_id_column} = f.{field_name}_target_id
WHERE r.{ref_bundle_column} = '{bundle}'
  AND n.status = 1
LIMIT 3;
```

Never skip Step A2: a candidate of the wrong target type can still return rows by ID
collision and would yield a page that never references the requested entity. If
`drupal-migrate-query-fields` already listed the reference fields and their target types,
use that list instead of Steps A/A2.

> Prefer nodes with a clean path alias (i.e., an entry exists in `path_alias`).

**Drupal 7 differences.** The queries above are D8+. On a D7 source substitute:
`node` for `node_field_data` (same `nid`, `type`, `status` columns);
`field_data_{field_name}` for `node__{field_name}`, joined on `entity_id = n.nid`
with `entity_type = 'node'` (D7 field tables have no `revision_id` join; use
`field_revision_{field_name}` joined on `revision_id = n.vid` when revision accuracy
matters); `taxonomy_term_data` with `vid` resolved through `taxonomy_vocabulary.machine_name`
for the taxonomy source table; and the reference column `{field_name}_tid` (taxonomy)
or `{field_name}_target_id` (entityreference). In Step A enumerate columns ending in
`_tid` or `_target_id` across `field_data_field_%` tables; for Step A2 read
`field_config.type` (`taxonomy_term_reference` targets terms) and, for `entityreference`,
the `target_type` inside `field_config.data`.

#### 3. Resolve URL alias from `path_alias`

`{base_langcode}` is the source site's base content language, from
`.agents/references/migrate/project-config.md` → "Base Content Language"
(default `en` if unset).

```sql
SELECT alias
FROM path_alias
WHERE path = '/node/{nid}'
  AND langcode = '{base_langcode}'
ORDER BY id DESC
LIMIT 1;
```

If no alias is found in the base language, retry with `langcode = 'en'`, then fall back to the canonical path `/node/{nid}`.

**Drupal 7:** there is no `path_alias` table; query `url_alias` instead:

```sql
SELECT alias
FROM url_alias
WHERE source = 'node/{nid}'
  AND language IN ('{base_langcode}', 'und')
ORDER BY pid DESC
LIMIT 1;
```

D7 aliases have no leading slash; prepend `/` before building the URL.

> **UUID query** (when needed): Always use `{base_table}`, not `{main_table}`:
>
> ```sql
> SELECT uuid FROM node WHERE nid = {nid};
> ```

#### 4. Build the full URL

Combine the **site base URL** (from project config, or ask the user if unknown) with the resolved alias:

```
{base_url}{alias}
```

Example: `https://example.com/path/to/page`

If no alias is resolved after 3 candidate node IDs, mark the entry as `URL not found` and continue.

---

### 5. Output

Return a table for inclusion in the analysis report:

| Node type    | Node ID | URL                                |
| ------------ | ------- | ---------------------------------- |
| `{bundle_a}` | 42      | `https://example.com/path/to/page` |
| `{bundle_b}` | 187     | `https://example.com/another/path` |

For `paragraph`, `taxonomy_term`, and `media` entities, the table shows the **parent/referencing node**, not the entity itself. Add a note clarifying:

> "URLs resolved via parent/referencing nodes (entity type `{entity_type}` has no direct public URL)"

This table populates the **Live examples** section of the Source Analysis Report (without the Screenshot column, which is filled by `drupal-migrate-live-screenshots`).

---

## Error Handling

- **`path_alias` table missing**: On a D7 source use `url_alias` (see step 3). Otherwise fall back to canonical `/node/{nid}` paths and note the fallback in the output.
- **No alias found after 3 attempts**: Mark entry as `URL not found`. Do not block the analysis.
- **Base URL unknown**: Ask the user once: _"What is the base URL of the production source site?"_
- **No active parent nodes**: Skip URL resolution for that bundle and note it in the output.
- **No referencing nodes found** (taxonomy_term/media): Note "No published nodes reference this entity" and continue.
