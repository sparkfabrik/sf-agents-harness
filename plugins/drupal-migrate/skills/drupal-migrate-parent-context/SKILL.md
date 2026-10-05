---
name: drupal-migrate-parent-context
description: "Identify the parent context for a paragraph bundle in the source database — which entity types and fields reference it, and which node bundles contain it. Use after counting instances, when planning a paragraph migration and you need to know where the paragraph is embedded (top-level node field vs. nested inside another paragraph)."
---

# Identify Paragraph Parent Context

For a paragraph bundle, identify which entity types and fields reference it, and which node bundles contain it.

This is paragraph-specific: paragraphs have no public URL and no bundle-level status, so their migration scope is defined entirely by _what references them_. The `paragraphs_item_field_data` table records that link via `parent_type`, `parent_id`, and `parent_field_name`.

## Prerequisites

- Source database connection verified (`drupal-migrate-db-discover`)
- Applies to **paragraph** entity types only

## Resolving table and column names

Paragraph table/column variables (`paragraphs_item_field_data`, `id`, `type`) follow
the shared reference — read it instead of hardcoding:
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".

Check `.agents/references/migrate/project-config.md` for the drush database
option and any project-specific table-name overrides.

## Input

- **bundle**: The paragraph bundle machine name (e.g., the value queried in `drupal-migrate-count-instances`)

## Steps

### Step 1 — Identify parent types and fields

```sql
SELECT parent_type, parent_field_name, COUNT(DISTINCT id) AS instances
FROM paragraphs_item_field_data
WHERE type = '{bundle}'
GROUP BY parent_type, parent_field_name
ORDER BY instances DESC;
```

This shows:

- Which entity types reference this paragraph (e.g., `node`, or `paragraph` for nested cases)
- Which field names hold the reference (e.g., `field_<something>`)
- How many instances per parent field

### Step 2 — Identify node bundles (when parent is node)

If any `parent_type` is `node`, identify which node bundles:

```sql
SELECT n.type AS node_bundle, COUNT(DISTINCT n.nid) AS node_count
FROM node_field_data n
JOIN paragraphs_item_field_data p ON p.parent_id = n.nid AND p.parent_type = 'node'
WHERE p.type = '{bundle}'
GROUP BY n.type
ORDER BY node_count DESC;
```

### Step 3 — Handle nested paragraphs (when parent is paragraph)

If any `parent_type` is `paragraph`, this is a nested/child paragraph. Trace one level up:

```sql
SELECT parent.type AS parent_paragraph_bundle, parent.parent_type AS grandparent_type,
  COUNT(DISTINCT child.id) AS instances
FROM paragraphs_item_field_data child
JOIN paragraphs_item_field_data parent ON parent.id = child.parent_id AND child.parent_type = 'paragraph'
WHERE child.type = '{bundle}'
GROUP BY parent.type, parent.parent_type
ORDER BY instances DESC;
```

If the grandparent is a node, also identify the node bundles:

```sql
SELECT n.type AS node_bundle, COUNT(DISTINCT n.nid) AS node_count
FROM paragraphs_item_field_data child
JOIN paragraphs_item_field_data parent ON parent.id = child.parent_id AND child.parent_type = 'paragraph'
JOIN node_field_data n ON n.nid = parent.parent_id AND parent.parent_type = 'node'
WHERE child.type = '{bundle}'
GROUP BY n.type
ORDER BY node_count DESC;
```

### Drupal 7 differences

Paragraphs 7.x stores no parent columns on the item: `paragraphs_item` has `item_id`,
`revision_id`, `bundle`, `field_name`, `archived`. The host relationship lives in the
host field tables `field_data_{field_name}` (`entity_type`, `bundle`, `entity_id`,
`{field_name}_value` = item id, `{field_name}_revision_id`). Replace Steps 1–3 with:

```sql
-- Step 1 (D7): which host fields hold this bundle
SELECT field_name, COUNT(DISTINCT item_id) AS instances
FROM paragraphs_item
WHERE bundle = '{bundle}' AND archived = 0
GROUP BY field_name
ORDER BY instances DESC;

-- Step 2 (D7): host entity types and bundles, one query per field_name from Step 1
SELECT h.entity_type AS parent_type, h.bundle AS parent_bundle,
  COUNT(DISTINCT p.item_id) AS instances
FROM paragraphs_item p
JOIN field_data_{field_name} h
  ON h.{field_name}_value = p.item_id AND h.deleted = 0
WHERE p.bundle = '{bundle}'
GROUP BY h.entity_type, h.bundle
ORDER BY instances DESC;
```

A `parent_type` of `paragraphs_item` means a nested paragraph. For Step 3 (D7) take that
host row's `entity_id` as the parent item id, read its `field_name` from
`paragraphs_item`, and repeat the Step 2 query on that field to reach the grandparent;
stop when `entity_type = 'node'` and group by the node `type`.

### Step 4 — Report results

Output the parent context table (generic example shown — substitute real values):

```
#### Parent context — `{bundle}`

| Parent type | Parent field | Instances | Node bundles |
|---|---|---|---|
| `node` | `field_<reference_field>` | N | `<node_bundle_a>` (N), `<node_bundle_b>` (N) |
| `paragraph` | `field_<items>` | N | (nested in `<parent_paragraph_bundle>`) |
```

## Output

- **parent_contexts**: List of (parent_type, parent_field_name, instance_count)
- **node_bundles**: For node parents, which node bundles and how many
- **nesting_info**: For paragraph parents, the parent paragraph bundle and grandparent chain

## Guardrails

- This skill is only for paragraph entity types — skip for nodes, taxonomy terms, users
- Always use `COUNT(DISTINCT id)` for paragraph counts
- If `paragraphs_item_field_data` doesn't exist the source is Drupal 7: use the "Drupal 7 differences" queries, not a table rename (D7 has no parent columns on the item)
- Report all parent contexts, even if some have very low instance counts — this helps identify edge cases
