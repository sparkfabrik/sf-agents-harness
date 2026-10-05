---
name: drupal-migrate-db-discover
description: "Discover and validate the source database connection for a migration into Drupal. Use after drupal-migrate-detect-source, at the start of any source-database analysis, or whenever a later drupal-migrate-* step needs to confirm the source DB is reachable. Reads the project config for the connection and the read-only access method (drush for a Drupal source; wp db query / ddev / mysql for WordPress; generic for another CMS), then tests connectivity. Source-agnostic — does not assume drush."
---

# Discover Source Database Connection

Find and validate the source database connection used for content migration. The source
may be Drupal, WordPress, or another CMS — the **access method** comes from
`drupal-migrate-detect-source` and project-config, not from an assumption that the
source is Drupal.

## Project Configuration

The authoritative connection values (database key/prefix, access method, host, special
notes) come from the project config — read it instead of hardcoding:
**`.agents/references/migrate/project-config.md`** → "Source System Overview" and
"Database Connection".

A project may define **more than one** source database. If so, project-config
names which is primary; use a non-primary key only when the user explicitly asks for it.

If that file does not exist, fall back to the defaults below.

## Source-access method (resolve before querying)

Use the read-only method established by `drupal-migrate-detect-source`. **Never default
to drush, and never use a read-write `mysql` invocation.**

| Source / environment         | Read-only access method                                     | Connection identifier |
| ---------------------------- | ----------------------------------------------------------- | --------------------- |
| Drupal, project drush runner | `<runner> "drush sql:query --database=<db_key> '<SELECT>'"` | `db_key`              |
| WordPress under DDEV         | `ddev wp db query '<SELECT>'`                               | table prefix          |
| WordPress with wp-cli        | `wp db query '<SELECT>'`                                    | table prefix          |
| Raw dump in a DB container   | read-only `mysql`/`mariadb` client against the import       | schema name           |

Every later skill that queries the source uses the method confirmed here. Substitute it
wherever the skills below show a `drush sql:query` example for a Drupal source.

## Defaults (used only when project-config has no Database Connection section)

**Drupal source** (drush access):

- **Database key**: `migrate` (Drupal convention)
- **Drush option**: `--database=migrate`
- **Settings files to check** (in order; standard Drupal docroot — adjust the docroot
  prefix to the project, e.g. `web/` or `src/drupal/web/`):
  1. `web/sites/default/settings.local.php`
  2. `web/sites/default/settings.php`

**WordPress source** (wp-cli / DDEV access):

- **Table prefix**: from `wp-config.php` `$table_prefix` (multisite subsites add a
  numeric suffix, e.g. `wp_2_`).
- **Access**: `ddev wp db query '<SELECT>'` under DDEV, else `wp db query '<SELECT>'`.

## Steps

### Step 1 — Read project configuration

Read `.agents/references/migrate/project-config.md` if it exists. Extract:

- The source technology and access method (from `drupal-migrate-detect-source`)
- Database key (Drupal) or table prefix (WordPress) and which DB is primary
- The runner / option for the access method
- Any special connection notes (feature flags, required containers, auth caveats)

### Step 2 — Locate the connection (branch by source)

**Drupal source** — confirm the `$databases` array entries that define the source DB:

```bash
grep -n "databases\[" web/sites/default/settings.local.php 2>/dev/null
grep -n "databases\[" web/sites/default/settings.php 2>/dev/null
```

Look for any `$databases['<key>']` entry whose key is **not** `default` — the
`default` key is the local Drupal database, not the source. The source key is
often interpolated from an env variable rather than a literal string, so also
match the keys named in project-config. If multiple non-default keys are found and
project-config does not say which is the source, list them and ask the user.

**WordPress source** — confirm the prefix and (for multisite) the per-site suffix:

```bash
grep -n "table_prefix" wp-config.php 2>/dev/null
```

The DB is reached through `wp`/`ddev`, not a settings key — the identifier is the table
prefix, not a `$databases` key.

### Step 3 — Test connectivity (with the resolved access method)

Run a trivial read with the method from the access-method table above — substitute the
project's runner:

```bash
# Drupal
<runner> "drush sql:query --database=<db_key> 'SELECT 1'"
# WordPress (DDEV)
ddev wp db query 'SELECT 1'
```

If the connection fails, the source DB may require enabling (e.g. a `MIGRATE_ENABLE`
flag, a separate DB container, or starting the DDEV project). Check project-config for
the enable steps before reporting failure.

### Step 4 — Report results

**If connection succeeds**, output (fill the fields for the actual source):

```
✅ Source database connection verified
- Source: <wordpress | drupal7 | drupal8+ | other>
- Identifier: <db_key (Drupal) | table prefix (WordPress)>
- Access method: <drush sql:query | ddev wp db query | wp db query | mysql>
- Query command template: <the exact read-only command to run a SELECT>
```

**If connection fails**, report the error and ask the user:

> "The source database connection failed. Check the source DB is enabled and the
> connection settings (see project-config.md). Error: {error_message}"

Then **STOP** — do not proceed with analysis until the database is reachable.

## Output

- **db_key**: the database key name
- **drush_option**: the drush CLI option (`--database=<db_key>`)
- **connection_command_template**: template for running queries against the source DB
- **connection_status**: `connected` or `failed`

## Guardrails

- **Use the project's configured read-only access method** (from
  `drupal-migrate-detect-source` / project-config): `drush sql:query` for Drupal,
  `wp db query` / `ddev wp db query` for WordPress, a read-only `mysql` client only for a
  raw dump. Never run a read-write `mysql` invocation against the source.
- **Never assume drush** — a WordPress or other-CMS source uses a different runner.
- If settings/config files are not found, ask the user for the connection details.
- If multiple non-default database keys exist and the project config is silent, ask the user which one to use.
- Do not modify settings.php, wp-config.php, or any source file.
