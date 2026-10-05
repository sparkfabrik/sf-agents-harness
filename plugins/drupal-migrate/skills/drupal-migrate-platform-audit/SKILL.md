---
name: drupal-migrate-platform-audit
description: 'Produce the as-is platform document for a migration into Drupal — the source platform exactly as it is today. Captures the CMS version, hosting/PHP/DB engine, single-site vs multisite (with subsite count), the active module/plugin inventory with verified activation state, and the custom-code list. Use during Phase 1 as-is analysis after drupal-migrate-detect-source, when asked to "document the platform", "inventory the plugins/modules", "what version is the source", or "audit the as-is platform". Writes as-is/platform.md per the drupal-migrate-analysis-docs skill.'
---

# Platform audit (as-is)

Document the source platform as a frozen, citable fact set: version, topology, the
active extension inventory, and the custom-code list. This is **what the platform is**,
not what Drupal will do with it — dispositions and replacements are Phase 2.

## Prerequisites

- `drupal-migrate-detect-source` has run (source tech, topology, delivery, access
  method).
- `drupal-migrate-db-discover` confirmed the source DB is reachable.
- The doc layout rules: read `drupal-migrate-analysis-docs` before writing.

## Steps

### Step 1 — Read config + recover what exists

Read `project-config.md`. Per `drupal-migrate-analysis-docs`, check whether platform
facts are already recorded (`doc/Migrate/as-is/platform.md`) — if so, update/cite rather
than rewrite. Use the access method from db-discover for every query.

### Step 2 — Version, hosting, engine

Collect the version and runtime facts:

- **CMS release** — read it from delivered code or package metadata only: WordPress
  `wp-includes/version.php` (`$wp_version`); Drupal `core/lib/Drupal.php`
  (`const VERSION`) or `composer.lock` (`drupal/core`), as `drupal-migrate-detect-version`
  Step 3 does. Database values (`{prefix}options.db_version`, `core.extension`,
  `system.schema`) identify schema or extension state, not the release; never record them
  as the version. For a **DB-only** source report the exact release as `unknown` and
  record only the major detected by `drupal-migrate-detect-version`.
- **DB engine + version**, **source PHP version** (from the codebase or the delivery
  notes), **uploads/media volume** (directory size), **users count**.
- **Topology** — single vs multisite and the registered-site count (from
  `drupal-migrate-detect-source`).

Record these as a property table.

### Step 3 — Extension inventory with verified activation

List the active modules/plugins **from the live database**, not from the on-disk folder
or a hand-supplied list — folders and lists drift from what is actually enabled.

- **WordPress:** network-active plugins in `{prefix}sitemeta.active_sitewide_plugins`;
  per-site plugins in each blog's `{prefix}…options.active_plugins`. A plugin active on
  zero blogs is disabled and droppable from scope. Record reach (how many blogs) for
  multisite.
- **Drupal:** enabled modules from `core.extension` (D8+) or the `system` table (D7).

Flag licensed extensions that need manual reinstall, and any activation anomaly
(orphaned activation with no folder, a folder with no activation, version skew between
subsites).

### Step 4 — Custom-code list

If the codebase was delivered, list custom / non-standard code (custom modules,
plugins, themes, loose files), each with size and a one-line "what it is". Do **not**
decide its disposition here — that is `drupal-migrate-codebase-scan` (Phase 1
disposition) and Phase 2 mapping. If the source is **DB-only**, state that no codebase
was delivered and the custom-code list is limited to what the DB reveals (e.g. WP
`active_plugins` names without source).

### Step 5 — Write the doc

Write `doc/Migrate/as-is/platform.md` per `drupal-migrate-analysis-docs`: a status
header (`**Status:**` frozen, `**Date:**`, `**Part of:**` backlink), the property table,
the activation inventory table, and the custom-code table. Add the row to
`as-is/README.md`. Keep dispositions out — this is frozen as-is.

## Output

- `doc/Migrate/as-is/platform.md` written (path reported).
- A summary: version, topology, active-extension count, custom-code count, anomalies.

## Guardrails

- **Activation from the live DB**, never the plugin folder or an unverified list; record
  the read date.
- **No dispositions / no target mapping** — frozen as-is only.
- **Read-only** access via the db-discover method; never mutate the source.
- DB-only source → say so; do not invent a custom-code inventory.
- Don't duplicate facts the corpus already holds — reference them.
