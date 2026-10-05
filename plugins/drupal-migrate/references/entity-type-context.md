# Entity-Type Context — Drupal 8+ Migration Reference

Shared reference for all `drupal-migrate-*` skills. When a skill requires entity-type-specific
table names, column names, or logic, resolve variables from the tables below.

---

## Variable Resolution Table

| Variable              | `node`                | `paragraph`                              | `taxonomy_term`                  | `media`                       | `user`                |
| --------------------- | --------------------- | ---------------------------------------- | -------------------------------- | ----------------------------- | --------------------- |
| `{main_table}`        | `node_field_data`     | `paragraphs_item_field_data`             | `taxonomy_term_field_data`       | `media_field_data`            | `users_field_data`    |
| `{base_table}`        | `node`                | `paragraphs_item`                        | `taxonomy_term_data`             | `media`                       | `users`               |
| `{id_column}`         | `nid`                 | `id`                                     | `tid`                            | `mid`                         | `uid`                 |
| `{uuid_column}`       | `uuid` (in `node`)    | `uuid` (in `paragraphs_item`)            | `uuid` (in `taxonomy_term_data`) | `uuid` (in `media`)           | `uuid` (in `users`)   |
| `{bundle_column}`     | `type`                | `type`                                   | `vid`                            | `bundle`                      | —                     |
| `{field_data_prefix}` | `node__`              | `paragraph__`                            | `taxonomy_term__`                | `media__`                     | `user__`              |
| `{config_prefix}`     | `field.field.node.`   | `field.field.paragraph.`                 | `field.field.taxonomy_term.`     | `field.field.media.`          | `field.field.user.`   |
| `{storage_prefix}`    | `field.storage.node.` | `field.storage.paragraph.`               | `field.storage.taxonomy_term.`   | `field.storage.media.`        | `field.storage.user.` |
| `{status_column}`     | `status`              | — _(use `drupal-migrate-verify-active`)_ | `status`                         | `status`                      | `status`              |
| `{has_direct_url}`    | ✓                     | ✗ _(resolve via parent node)_            | ✗ _(resolve via parent node)_    | ✗ _(resolve via parent node)_ | ✗ _(skip)_            |

> **UUID location**: UUIDs are always in `{base_table}`, **never** in `{main_table}`.
> Query: `SELECT uuid FROM {base_table} WHERE {id_column} = ?`

---

## Base Fields Per Entity Type

These fields exist on every entity of the given type. They are NOT stored in
`{field_data_prefix}` tables — they live directly in `{main_table}` or `{base_table}`.
A column that exists is not a column that holds a value: mark **Required ✓** only for
columns the entity cannot be saved without (`title`, `name`, `langcode`, `status`,
`uid`, `created`, `changed`, `uuid`), and **measure population** of the others
(`description__value`, `sticky`, `promote`, `weight`, `mail`) with
`drupal-migrate-field-population` instead of asserting 100%.

### `node`

| Field    | Column     | Table             |
| -------- | ---------- | ----------------- |
| Title    | `title`    | `node_field_data` |
| Status   | `status`   | `node_field_data` |
| Language | `langcode` | `node_field_data` |
| Created  | `created`  | `node_field_data` |
| Changed  | `changed`  | `node_field_data` |
| Author   | `uid`      | `node_field_data` |
| Sticky   | `sticky`   | `node_field_data` |
| Promoted | `promote`  | `node_field_data` |
| UUID     | `uuid`     | `node`            |

### `paragraph`

| Field        | Column              | Table                        |
| ------------ | ------------------- | ---------------------------- |
| Language     | `langcode`          | `paragraphs_item_field_data` |
| Created      | `created`           | `paragraphs_item_field_data` |
| Status       | `status`            | `paragraphs_item_field_data` |
| Parent ID    | `parent_id`         | `paragraphs_item_field_data` |
| Parent type  | `parent_type`       | `paragraphs_item_field_data` |
| Parent field | `parent_field_name` | `paragraphs_item_field_data` |
| UUID         | `uuid`              | `paragraphs_item`            |

### `taxonomy_term`

| Field       | Column               | Table                      |
| ----------- | -------------------- | -------------------------- |
| Name        | `name`               | `taxonomy_term_field_data` |
| Status      | `status`             | `taxonomy_term_field_data` |
| Language    | `langcode`           | `taxonomy_term_field_data` |
| Description | `description__value` | `taxonomy_term_field_data` |
| Weight      | `weight`             | `taxonomy_term_field_data` |
| UUID        | `uuid`               | `taxonomy_term_data`       |

### `media`

| Field    | Column     | Table              |
| -------- | ---------- | ------------------ |
| Name     | `name`     | `media_field_data` |
| Status   | `status`   | `media_field_data` |
| Language | `langcode` | `media_field_data` |
| Created  | `created`  | `media_field_data` |
| Changed  | `changed`  | `media_field_data` |
| Author   | `uid`      | `media_field_data` |
| UUID     | `uuid`     | `media`            |

### `user`

| Field   | Column    | Table              |
| ------- | --------- | ------------------ |
| Name    | `name`    | `users_field_data` |
| Status  | `status`  | `users_field_data` |
| Mail    | `mail`    | `users_field_data` |
| Created | `created` | `users_field_data` |
| Changed | `changed` | `users_field_data` |
| UUID    | `uuid`    | `users`            |

---

## "Active" Definition Per Entity Type

| Entity type     | How to count active instances                                                                         |
| --------------- | ----------------------------------------------------------------------------------------------------- |
| `node`          | `SELECT COUNT(DISTINCT nid) FROM node_field_data WHERE type = '{bundle}' AND status = 1`              |
| `paragraph`     | Use `drupal-migrate-verify-active` — active = attached to a published parent node's current revision  |
| `taxonomy_term` | `SELECT COUNT(DISTINCT tid) FROM taxonomy_term_field_data WHERE vid = '{bundle}' AND status = 1`      |
| `media`         | `SELECT COUNT(DISTINCT mid) FROM media_field_data WHERE bundle = '{bundle}' AND status = 1`           |
| `user`          | `SELECT COUNT(DISTINCT uid) FROM users_field_data WHERE status = 1` (users rarely filtered by bundle) |

---

## Value Column Suffix Patterns

Use these to infer field types from `INFORMATION_SCHEMA` column inspection:

| Suffix(es)                                   | Inferred field type                |
| -------------------------------------------- | ---------------------------------- |
| `_value` only                                | `string` / `text_long` / `boolean` |
| `_value` + `_format`                         | `text_formatted_long`              |
| `_target_id` + `_target_revision_id`         | `entity_reference_revisions`       |
| `_target_id` only                            | `entity_reference`                 |
| `_uri` + `_title` + `_options`               | `link`                             |
| `_target_id` + `_alt` + `_width` + `_height` | `image`                            |
| `_date` or `_value` (datetime storage)       | `datetime`                         |
| `_lat` + `_lng`                              | `geofield`                         |

---

## URL Resolution Strategy Per Entity Type

| Entity type     | Resolution strategy                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `node`          | Direct — resolve `path_alias` for `/node/{nid}`                                                                                      |
| `paragraph`     | Indirect — use parent node IDs from `drupal-migrate-parent-context` / `drupal-migrate-verify-active`, then resolve parent node URLs  |
| `taxonomy_term` | Indirect — find published nodes referencing this term via `{entity_type}__{field_name}` tables, then resolve those node URLs         |
| `media`         | Indirect — find published nodes referencing this media entity via `{entity_type}__{field_name}` tables, then resolve those node URLs |
| `user`          | Skip — no public URL. Note "N/A — no public URL"                                                                                     |
