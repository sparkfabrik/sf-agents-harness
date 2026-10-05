---
name: drupal-migrate-detect-container
description: 'Detect whether a source paragraph bundle is a group/container that holds child paragraph entities via entity_reference_revisions fields, and list its child bundles. Use before analysing a paragraph''s fields when planning a migration — to discover nested paragraph hierarchies, e.g. "is X a container", "does the Y paragraph hold children", or to decide whether the full analysis must be repeated for child bundles. Supports both Drupal 7 and Drupal 8+ sources.'
---

# Detect Group / Container Pattern

Check whether a paragraph bundle acts as a container for child paragraph entities through `entity_reference_revisions` fields.

---

## Prerequisites

- Source database connection verified (`drupal-migrate-db-discover`)
- Source Drupal version detected (`drupal-migrate-detect-version`)

---

## Input

- **bundle**: The paragraph bundle machine name
- **source_version**: `drupal7` or `drupal8+`

---

## Resolving table and column names

The D8+ variables used below (`{config_prefix}`, `{field_data_prefix}`, `{main_table}`,
`{id_column}`) come from the shared reference — read it instead of hardcoding:
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".

For paragraphs: `{config_prefix}` = `field.field.paragraph.`, `{field_data_prefix}` = `paragraph__`.
Check `.agents/references/migrate/project-config.md` for any project-specific
table-name overrides.

---

## Steps

### Step 1 — Detect container and extract child bundles (Drupal 8+)

```sql
SELECT name, data FROM config
WHERE name LIKE CONCAT('{config_prefix}', '{bundle}', '.%')
  AND data LIKE '%entity_reference_revisions%';
```

If any rows are found, this bundle is a container. For each matching row, parse the serialized PHP `data` to extract the `target_bundles` array — these are the child paragraph bundles.

### Step 2 — Check for child-reference fields (Drupal 7)

> The shared reference is D8+. On a D7 source, paragraph fields live in
> `field_config_instance` / `field_config` (entity type `paragraphs_item`), not in `config`.

```sql
SELECT fci.field_name, fcs.type
FROM field_config_instance fci
JOIN field_config fcs ON fci.field_name = fcs.field_name
WHERE fci.entity_type = 'paragraphs_item'
  AND fci.bundle = '{bundle}'
  AND fcs.type = 'paragraphs'
  AND fci.deleted = 0;
```

### Step 3 — Count active children from published content (Drupal 8+)

For each child-reference field found. `{parent_field}` is the node field that
references this container paragraph (from `drupal-migrate-parent-context`); `{child_ref_field}`
is the container's `entity_reference_revisions` field from Step 1:

```sql
SELECT COUNT(DISTINCT c.{child_ref_field}_target_id) AS active_children
FROM {parent_table} n
JOIN {parent_ref_prefix}{parent_field} ref ON ref.entity_id = n.{parent_id} AND ref.revision_id = n.{parent_vid}
JOIN paragraph_revision__{child_ref_field} c
  ON c.entity_id = ref.{parent_field}_target_id
 AND c.revision_id = ref.{parent_field}_target_revision_id
 AND c.bundle = '{bundle}'
WHERE n.{parent_status} = 1;
```

> The `c.revision_id = ref.{parent_field}_target_revision_id` join restricts the children
> to the container revision the published node actually references. Without it, children
> removed in later container revisions are still counted. The join must read
> **`paragraph_revision__{child_ref_field}`**, not `paragraph__{child_ref_field}`: the
> latter holds only default-revision rows and returns nothing when the referenced
> container revision is not the default one.

> The `c.bundle = '{bundle}'` predicate is required too. Field tables are shared by every
> paragraph bundle that owns a field of that name (several containers often share
> `field_items`), and `{parent_field}` may reference more than one container bundle.
> Without the bundle filter the count includes children of other containers.

> This skill assumes the parent is a **node** (the case for paragraph hierarchies
> in practice). Node defaults: `{parent_table}` = `node_field_data`, `{parent_ref_prefix}`
> = `node__`, `{parent_id}` = `nid`, `{parent_vid}` = `vid`, `{parent_status}` = `status`;
> the paragraph child-reference table uses the `paragraph_revision__` prefix. If the parent is not a node,
> resolve `{parent_table}` / `{parent_ref_prefix}` / `{parent_id}` for that entity type
> from `entity-type-context.md` → "Variable Resolution Table".

### Step 4 — Report results

**If container:**

```
✅ `{bundle}` is a GROUP/CONTAINER paragraph

Child reference fields:
- `{field_name}` → targets: `{child_bundle_1}`, `{child_bundle_2}`

Active children in published content: {count}

⚠️ Repeat full analysis (count, fields, population) for each child bundle:
- `{child_bundle_1}`
- `{child_bundle_2}`
```

**If not a container:**

```
`{bundle}` is a LEAF paragraph (no child paragraph references)
```

---

## Output

- **is_container**: `true` or `false`
- **child_ref_fields**: List of field names that reference child paragraphs
- **child_bundles**: List of target child paragraph bundle names
- **active_child_count**: Number of active child instances in published content

---

## Guardrails

- Only checks for `entity_reference_revisions` fields (paragraphs references), not regular entity references
- If the bundle is a container, the calling agent should repeat the full analysis pipeline for each child bundle
- This skill detects the container relationship — it does NOT analyse the child bundles themselves
