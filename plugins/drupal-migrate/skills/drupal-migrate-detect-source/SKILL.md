---
name: drupal-migrate-detect-source
description: "Identify the source system of a migration into Drupal before any analysis — the source technology (WordPress, Drupal 7, Drupal 8+, or another CMS), whether it is single-site or multisite, whether the full codebase is available or only a database dump, and which read-only DB access method to use (drush / wp-cli / ddev / mysql). Use as the very first step of any migration analysis, before db-discover and before any source query. Returns routing facts that every later skill depends on; writes no documentation."
---

# Detect the migration source system

Establish what the source actually is before querying or documenting anything. The
answers route the entire migration analysis: which queries are valid, whether codebase
analysis applies, how scope is bounded, and which access method every later skill must
use.

This skill **writes no docs** — it returns routing facts. The frozen as-is facts are
written later by `drupal-migrate-platform-audit` and friends.

## Prerequisites

- The host project is checked out, with the source database and/or codebase available
  somewhere the project can reach (a dump, a DDEV site, a container, a local copy).
- `.agents/references/migrate/project-config.md` if it exists.

## Steps

### Step 1 — Read project configuration

Read `.agents/references/migrate/project-config.md` → **Source System Overview** and
**Database Connection**. If it declares the source technology, single/multisite,
codebase availability, and access method, trust it and use this skill only to confirm.
If the file is absent or silent, detect from evidence below — never assume.

### Step 2 — Detect the source technology

Detect from whichever of the codebase or database is available. Prefer cheap file
signals first, then a DB-table signature.

**Codebase signals** (if a source codebase is present):

```bash
# WordPress
ls wp-config.php wp-load.php 2>/dev/null; ls -d wp-content 2>/dev/null
# Drupal 8+ (composer-based)
ls core/lib/Drupal.php composer.json 2>/dev/null
# Drupal 7
ls includes/bootstrap.inc modules/system/system.module 2>/dev/null
```

**Database table signatures** (run with the access method from Step 4; substitute the
detected runner):

| Signature table(s) present                                                | Source                  |
| ------------------------------------------------------------------------- | ----------------------- |
| `{prefix}posts`, `{prefix}options`, `{prefix}postmeta`                    | WordPress               |
| `{prefix}blogs`, `{prefix}site`, `{prefix}sitemeta` (alongside the above) | WordPress **multisite** |
| `field_config_instance`                                                   | Drupal 7                |
| `config` (PHP-serialized field metadata), `key_value`                     | Drupal 8+               |

If neither codebase nor DB matches a known signature, the source is **another CMS** or
custom — report what was found and **stop**, asking the user to confirm.

### Step 3 — Single-site vs multisite

- **WordPress:** multisite if `{prefix}blogs` / `{prefix}sitemeta` exist, or
  `wp-config.php` sets `MULTISITE`/`SUBDOMAIN_INSTALL`. Count registered sites:

  ```sql
  SELECT COUNT(*) AS registered_sites FROM {prefix}blogs;
  ```

- **Drupal:** multisite if `sites/sites.php` defines multiple site directories, or more
  than one non-default folder under `sites/` carries its own `settings.php`.

Record the count — for a multisite source it drives per-site scoping and a
subsite-liveness question downstream.

### Step 4 — Codebase availability and DB access method

Determine **what was delivered** and **how to query it**, read-only:

- **Codebase-available vs DB-only.** Is there a source codebase (custom themes/modules/
  plugins) or only a database dump? DB-only blocks `drupal-migrate-codebase-scan` and
  limits custom-code disposition to what the DB reveals (e.g. WP `active_plugins`).

- **DB access method** — pick the project's configured read-only path; do not default to
  drush:

  | Source / environment         | Read-only access method                               |
  | ---------------------------- | ----------------------------------------------------- |
  | Drupal, project drush runner | `drush sql:query --database=<key> '<SELECT>'`         |
  | WordPress under DDEV         | `ddev wp db query '<SELECT>'`                         |
  | WordPress with wp-cli        | `wp db query '<SELECT>'`                              |
  | Raw dump in a DB container   | read-only `mysql`/`mariadb` client against the import |

  Confirm the method actually runs a trivial read (e.g. `SELECT 1`) — the deeper
  connection validation is `drupal-migrate-db-discover`'s job; here you only confirm the
  method is correct.

### Step 5 — Report routing facts

```
Source system
- Technology: {wordpress | drupal7 | drupal8+ | other}
- Topology:   {single-site | multisite (N registered sites)}
- Delivery:   {full codebase + DB | DB-only | codebase-only}
- DB access:  {drush | ddev wp db query | wp db query | mysql} — confirmed SELECT 1: {yes/no}
- Table prefix / db key: {value}
```

For a Drupal source, hand off to `drupal-migrate-detect-version` for the major version.

## Output

- **source_tech**: `wordpress` | `drupal7` | `drupal8+` | `other`
- **topology**: `single` | `multisite` (+ site count)
- **delivery**: `codebase+db` | `db-only` | `codebase-only`
- **db_access_method**: the read-only runner every later skill must use
- **table_prefix** / **db_key**

## Guardrails

- **Never assume Drupal, and never assume drush** — detect from evidence; honor
  project-config when set.
- **Read-only only** — `SELECT`/read queries and read-only file access; never mutate the
  source.
- If the source matches no known signature, **stop** and ask the user to confirm the
  source system — do not force-fit it to a known CMS.
- If only a DB is available, say so explicitly; downstream codebase analysis is skipped,
  not guessed.
- This skill detects and routes — it does not produce as-is documentation.
