---
name: drupal-migrate-verify-active
description: 'Verify active vs orphaned paragraph instances by checking them against the current published revision of their parent nodes. Use after drupal-migrate-parent-context, before sizing a paragraph bundle''s migration scope, when asked "how many of this paragraph are actually in use", or when total DB count and real usage may diverge because of orphaned revisions. Canonical source of the paragraph "active" count.'
---

# Verify Active vs Orphaned Paragraph Instances

Compare total paragraph instances against those referenced by the **current published revision** of their parent nodes. Paragraphs detached from a node, or left behind by an old node revision, still exist in the DB — this skill separates the in-use ones from the orphans.

This is the **canonical source of the paragraph "active" count**. `drupal-migrate-count-instances` defers to this skill for paragraphs because they have no meaningful status column of their own — a paragraph is "active" only insofar as a published parent points at it from its current revision.

## Prerequisites

- Source DB connection verified (`drupal-migrate-db-discover`)
- Parent context identified (`drupal-migrate-parent-context`)
- Applies to **paragraph** entity types only — nodes, taxonomy terms, media and users don't have the orphan problem (they carry their own `{status_column}`)

## Resolving table and column names

All D8+ table/column variables come from the shared reference — read it instead
of hardcoding:
**`.agents/references/migrate/entity-type-context.md`** → "Variable Resolution Table".
`{main_table}` resolves per entity type, so the queries below use the **`node`**
column for the parent (`node_field_data`, `nid`, `vid`) and the **`paragraph`**
column for the paragraph (`{para_table}` = `{main_table}` of `paragraph`).
`{field_data_prefix}` is the `node__` reference-table prefix from the same table.

The paragraph "active" rule itself is recorded there too, under
"Active Definition Per Entity Type", which points back to this skill.

Check `.agents/references/migrate/project-config.md` for the drush database
option and any project-specific table-name overrides before querying.

## Input

- **bundle**: the paragraph bundle machine name
- **parent_field_name**: the field on the parent entity that references this paragraph (from `drupal-migrate-parent-context`)
- **child_ref_field** _(nested only)_: the parent paragraph's `entity_reference_revisions` field that holds this bundle (from `drupal-migrate-parent-context` / `drupal-migrate-detect-container`)
- **total_instances**: total count from `drupal-migrate-count-instances`

## Steps

### Step 1 — Count active instances against published content

For each parent field identified by `drupal-migrate-parent-context`, run the query
below. It joins the paragraph to its referencing node **on both `entity_id` and
`revision_id`**, so only paragraphs attached to the node's _current_ revision are
counted — historical revisions are excluded.

```sql
SELECT n.type AS node_bundle,
  COUNT(DISTINCT p.id)  AS active_instances,
  COUNT(DISTINCT n.nid) AS parent_nodes
FROM {main_table} n
JOIN {field_data_prefix}{parent_field_name} ref
  ON ref.entity_id = n.nid AND ref.revision_id = n.vid
JOIN {para_table} p
  ON p.id = ref.{parent_field_name}_target_id
WHERE p.type = '{bundle}' AND n.status = 1
GROUP BY n.type;
```

> **Key**: the `ref.revision_id = n.vid` join is what restricts the count to the
> **current** node revision. Drop it and you re-introduce orphaned revisions.

**Drupal 7 differences.** The shared reference is D8+. On a D7 source (Paragraphs 7.x)
substitute: `node` for `{main_table}` (columns `nid`, `vid`, `type`, `status`);
`field_data_{parent_field_name}` for `{field_data_prefix}{parent_field_name}`, joined
on `ref.entity_id = n.nid AND ref.revision_id = n.vid AND ref.entity_type = 'node'`;
`paragraphs_item` for `{para_table}` (columns `item_id`, `revision_id`, `bundle`); and
the reference columns `{parent_field_name}_value` (item id) and
`{parent_field_name}_revision_id`. Nested paragraphs (Step 2) use the same
`field_data_{child_ref_field}` form with `entity_type = 'paragraphs_item'`.

### Step 2 — Handle nested paragraphs

If the paragraph's parent is another paragraph (not a node directly), start from the
published node, follow `{parent_field_name}` to the parent paragraph **at the revision
the node references**, then follow the parent's `{child_ref_field}` at that same
revision. Do not infer membership from `child.parent_id`: a child removed from the
parent's current revision keeps its `parent_id` in `paragraphs_item_field_data` and
would be counted as active.

```sql
SELECT n.type AS node_bundle,
  COUNT(DISTINCT child.id)  AS active_instances,
  COUNT(DISTINCT n.nid) AS parent_nodes
FROM {main_table} n
JOIN {field_data_prefix}{parent_field_name} ref
  ON ref.entity_id = n.nid AND ref.revision_id = n.vid
JOIN {para_table} parent
  ON parent.id = ref.{parent_field_name}_target_id
JOIN paragraph_revision__{child_ref_field} cref
  ON cref.entity_id = parent.id
 AND cref.revision_id = ref.{parent_field_name}_target_revision_id
JOIN {para_table} child
  ON child.id = cref.{child_ref_field}_target_id
WHERE child.type = '{bundle}' AND n.status = 1
GROUP BY n.type;
```

For deeper nesting, repeat the `parent → cref` pair once per level, always joining the
next level's field table on the `*_target_revision_id` selected one level up.

> Use the **`paragraph_revision__`** table for the child reference, not `paragraph__`.
> `paragraph__{field}` holds only the default-revision rows; when the published node
> references a container revision that is not the default one (for example a moderated
> draft is ahead), the join against `paragraph__` finds nothing and marks every child as
> orphaned. `paragraph_revision__{field}` holds one row set per revision, so the
> `target_revision_id` predicate selects exactly the referenced one.

### Step 3 — Compute orphaned count

```
orphaned = total_instances - SUM(active_instances across all parent fields)
```

### Step 4 — Report results

```
#### Active vs orphaned — `{bundle}`

| | Total in DB | Active (published) | Orphaned |
|---|---|---|---|
| `{bundle}` | {total} | **{active}** | {orphaned} |
```

If orphaned > 0:

> ⚠️ {orphaned} orphaned instances from old or detached node revisions — excluded from migration scope.

## Output

- **active_instances**: paragraph instances in currently published node revisions
- **orphaned_instances**: paragraph instances NOT in current published revisions
- **breakdown_by_node_type**: active instances per parent node bundle

## Guardrails

- Always join on BOTH `entity_id` AND `revision_id` to match the **current** revision — joining on `entity_id` alone re-counts orphaned revisions.
- Filter `n.status = 1` to count only published nodes.
- The active count is the **authoritative migration scope** — use this number, not the raw DB total.
- If the reference table `{field_data_prefix}{parent_field_name}` doesn't exist, list `INFORMATION_SCHEMA` candidates and inform the user — don't silently report 0.
- Run queries via `drush sql:query` with the source database option from `project-config.md`.
- This skill applies to paragraphs only.
