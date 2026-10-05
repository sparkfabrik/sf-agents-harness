---
name: drupal-migrate-detect-version
description: "Detect the Drupal version of the source migration database (Drupal 7 vs Drupal 8+, with the exact core major when the source codebase is available). Use after discovering the database connection with drupal-migrate-db-discover. Checks for version-specific table signatures."
---

# Detect Source Drupal Version

Determine whether the source migration database is Drupal 7 or Drupal 8+ by checking for version-specific table signatures.

> This is the **Drupal-source sub-step** of `drupal-migrate-detect-source`. Run it only
> once that gate has established the source technology is Drupal. For a WordPress or
> other-CMS source it does not apply.

---

## Prerequisites

- Source database connection verified (`drupal-migrate-db-discover`)
- You have the `db_key` / `drush_option` from the discovery step

---

## Steps

### Step 1 — Read project configuration

Read `.agents/references/migrate/project-config.md` for the source database key
and any schema name. Use the `drush_option` from `drupal-migrate-db-discover` output (e.g.
`--database={db_key}`). Do not hardcode a project's db key here.

### Step 2 — Query for version-specific tables

The signature is the field-metadata storage mechanism: D7 keeps field configs in the
`field_config_instance` table; D8+ stores them PHP-serialized in the `config` table.
Run against the source database:

```sql
SELECT IF(
  EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'field_config_instance'),
  'drupal7',
  IF(EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'config'), 'drupal8+', 'unknown')
) AS source_version;
```

Execute via (substitute the `{drush_option}` from Step 1):

```bash
docker compose run --rm <tools-container> ash -c "drush sql:query {drush_option} \"SELECT IF(EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'field_config_instance'), 'drupal7', IF(EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'config'), 'drupal8+', 'unknown')) AS source_version;\""
```

### Step 3 — Determine the core major (optional, Drupal 8+ with codebase only)

The database does not record the core major: `core.extension` lists enabled modules and
`system.site` holds site settings, neither carries a core version. Read it from the
delivered code instead (`project-config.md` → "Source codebase path"):

```bash
# Drupal::VERSION constant
grep -m1 "const VERSION" <codebase>/web/core/lib/Drupal.php
# or the locked package
jq -r '.packages[] | select(.name == "drupal/core") | .version' <codebase>/composer.lock
```

Report the major as `core_major` (8, 9, 10, 11). For a **DB-only** source, report
`drupal8+` and state that the exact major is unknown.

### Step 4 — Report results

Output:

```
Source Drupal version: {version}
- Drupal 7: field metadata in the field_config_instance table
- Drupal 8+: field metadata PHP-serialized in the config table (core major from the codebase, or unknown for DB-only)
```

If `unknown`, warn:

> "⚠️ Could not detect Drupal version — neither `field_config_instance` (D7) nor `config` (D8+) tables were found. This may not be a standard Drupal database."

Then **STOP** and ask the user to confirm the source system.

---

## Output

- **source_version**: `drupal7`, `drupal8+`, or `unknown`
- **core_major** _(optional)_: `8`, `9`, `10`, or `11`, only when the codebase is available
- **field_query_strategy**: `field_config_instance` (D7) or `config_table` (D8+)

---

## Guardrails

- This skill only detects the version — it does not query field data
- If version is unknown, stop and ask the user for clarification
- Use `DATABASE()` function instead of hard-coding the schema name when possible
