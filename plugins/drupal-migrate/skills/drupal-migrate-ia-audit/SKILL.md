---
name: drupal-migrate-ia-audit
description: 'Produce the as-is information-architecture document for a migration into Drupal — the source site''s structure and URL state today. Captures the navigation menus, the URL/permalink scheme, and the redirect + liveness state (which paths are live, redirected, or gone), and for a multisite source classifies subsite liveness. Use during Phase 1 as-is analysis when asked to "audit the IA", "map the site structure/menus", "what''s the URL/permalink structure", "build the redirect map", or "classify subsite liveness". Writes an as-is IA/liveness doc per the drupal-migrate-analysis-docs skill.'
---

# Information-architecture audit (as-is)

Document the source site's structure and URL state as frozen facts. The IA and the
live-URL set drive the menu rebuild and — critically — the redirect map: paths that
carry SEO weight must be preserved across the migration, and missing them is a
post-launch regression, not a migration bug.

## Prerequisites

- `drupal-migrate-detect-source` + `drupal-migrate-db-discover` have run (topology +
  access method).
- Read `drupal-migrate-analysis-docs` before writing.

## Steps

### Step 1 — Read config + recover

Read `project-config.md` (including any URL Scope Support Table / liveness data source).
Check for an existing IA/liveness doc; update/cite rather than rewrite.

### Step 2 — Navigation menus

Extract the menu structure:

- **WordPress:** menus are `nav_menu` terms in `{prefix}term_taxonomy`; items are
  `nav_menu_item` posts in `{prefix}posts`, assigned to their menu through
  `{prefix}term_relationships` (`object_id` = item post ID, `term_taxonomy_id` = the
  menu). Order comes from `posts.menu_order`, hierarchy from the
  `_menu_item_menu_item_parent` row in `{prefix}postmeta`. Join all three to place each
  item in the right menu before rebuilding the tree.
- **Drupal:** `menu_link_content` + menu config.

Record the top-level structure and depth — enough to rebuild navigation, not every leaf.

### Step 3 — URL / permalink scheme

Record how URLs are formed:

- **WordPress:** the permalink structure (`{prefix}options` `permalink_structure`), and
  any per-content overrides (custom permalink plugin — note whether enabled).
- **Drupal:** path-alias patterns (Pathauto) and the `path_alias` table.

This determines the alias-migration and pattern-mapping work later.

### Step 4 — Redirect + liveness state

Establish which paths are live, redirected, or gone — the redirect map's raw input:

- Existing redirects (a redirect plugin/module's table, or server config if delivered).
- **Liveness** — if the project has a liveness data source (probe CSV, support table per
  project-config), classify each path/subsite as live / redirected (301) / gone
  (404/410). For a **multisite** source, classify subsite liveness and flag anomalies
  (e.g. a subsite marked private yet serving content).

State who owns the redirect map for dismissed paths as an open question if undecided
(don't resolve it here).

### Step 5 — Write the doc

Write the IA/liveness doc under `doc/Migrate/as-is/` per `drupal-migrate-analysis-docs`
(a single doc, or split menus vs liveness if large): status header, menu structure, URL
scheme, redirect/liveness classification with counts, and raw probe data under
`as-is/data/` if voluminous. Add the row to `as-is/README.md`.

## Output

- The as-is IA/liveness doc written (path reported); raw data under `as-is/data/` if
  large.
- A summary: menu shape, URL scheme, live/redirected/gone counts, multisite liveness
  split, and any redirect-ownership open question.

## Guardrails

- **Read-only** via the db-discover method; a liveness probe of the live site is a
  read-only HTTP check, recorded with its date.
- **No redirect-strategy decisions** — Phase 2/3. Here: the current URL and liveness
  state, frozen.
- Large per-path data goes in `as-is/data/` as CSV, referenced from the doc — don't
  inline hundreds of rows.
- Don't duplicate content volumes (that's `content-inventory.md`) — reference it.
