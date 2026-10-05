---
name: drupal-migrate-verify-content
description: 'Verify migrated content by navigating source and destination website pages, comparing content through LLM reasoning, checking HTTP redirects, and validating translations. Use this skill whenever the user asks to "verify migration", "check migrated content", "compare source and destination pages", "verify redirects", or provides a source URL to validate after migration. Also trigger when the user mentions "migration QA", "migration acceptance", "content verification", "post-migration check", or wants to confirm that content from the old site was correctly imported. This includes checking multilingual translations, verifying 301 redirect chains, and confirming 410 Gone responses for non-migrated pages.'
---

# Migration Content Verification

You are a migration QA agent. Your job is to verify that content has been correctly
migrated from the old site to the new Drupal site by **navigating both sites and comparing
what you see**, much like a human reviewer would. You use browser automation to visit
pages on both sites, then apply judgment to decide whether content was faithfully
preserved. You also verify HTTP redirects and translations.

This skill is **project-agnostic**: all project-specific values come from the project
configuration file. Read it first.

---

## Phase -1 — Load project configuration

Read **`.agents/references/migrate/project-config.md`** before anything else. Resolve
these variables from it; if the file is missing or a value is absent, ask the user and
do not guess:

| Variable                                  | Source section in project-config.md       | Example                                                                                                                                                                        |
| ----------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `{dest_runner}`                           | Content Verification → Destination runner | `docker compose run --rm <tools> ash -c` (runs `drush`/`curl` on the new site)                                                                                                 |
| `{source_query}`                          | Database Connection → Query command       | Drupal: `{dest_runner} "drush sql:query --database=<key> \"<SQL>\""`; WordPress: `ddev wp db query '<SQL>'`; other: the read-only client documented there                      |
| `{source_bases}`                          | Content Verification                      | `https://www.example.com` (+ secondary-lang domain/prefix)                                                                                                                     |
| `{dest_base_url}`                         | Content Verification                      | `https://<new-site>.loc`                                                                                                                                                       |
| `{internal_http_host}`                    | Content Verification                      | `http://<web-container>`                                                                                                                                                       |
| `{languages}` + URL rule                  | Content Verification                      | base lang + secondary lang (path prefix or separate domain)                                                                                                                    |
| `{scope_table}` + columns + status values | URL Scope Support Table                   | table `<scope_table>`; columns `<url_col>`, `<langcode_col>`, `<action_col>` ∈ {migrate, no-migrate}, `<status_col>`, `<node_id_col>`, `<content_type_col>`, `<final_url_col>` |
| `{url_map_table}` + columns _(optional)_  | Source URL Map Table                      | table `<url_map_table>`; columns `<map_source_url_col>`, `<map_langcode_col>`, `<map_dest_id_col>`, `<map_dest_type_col>`, `<map_dest_url_col>`                                |

Column names are project-defined. The `<…_col>` placeholders below stand for the names
declared in project-config.md; never assume `url`, `node_id`, `final_url` or similar.

Two execution paths, never mixed:

- **Source lookups** (`{scope_table}`, `{url_map_table}`) run through `{source_query}`,
  the read-only method `drupal-migrate-db-discover` established for the source
  (`drush sql:query --database=<key>` for a Drupal source, `wp db query` for WordPress, a
  read-only client for anything else). Project-config.md says in the "URL Scope Support
  Table" section which database holds these tables; when they live in the destination
  database, `{source_query}` for them is `{dest_runner} "drush sql:query \"<SQL>\""`.
- **Destination commands** (alias lookup via `drush php:eval`, `redirect` and `node_field_data`
  queries, container-side `curl`) always run through `{dest_runner}`, which is the new
  Drupal site's tools container and needs no source database key.

A WordPress source has no Drush database key; the skill must still work with
`{source_query}` = `wp db query` and `{dest_runner}` for the destination.

If the project defines **no scope/support table**, skip Phase 0's table lookup and instead
derive intent directly: treat a provided URL as expected-to-exist unless the user says it
should be gone, and confirm redirects/aliases against the live destination.

---

## Prerequisites

1. **Old site reachable**: every base in `{source_bases}` responds.
2. **New site reachable**: `{dest_base_url}` resolved (discovery command or user).
3. **Source lookups reachable** (only if `{scope_table}`/`{url_map_table}` are used):
   run `{source_query}` with `SELECT 1`.
4. **Destination runner works**: `{dest_runner} "drush status --field=bootstrap"`
   reports `Successful`.
5. **Browser tool available**: resolve it per "Selecting the browser tool" below.

If any prerequisite fails, inform the user and stop. Do not work around missing infra.

### Selecting the browser tool

Do not shell out to a browser binary by default. Pick the first available tool, in the
same order `drupal-migrate-live-screenshots` → "Selecting the browser tool" uses, and keep
it for the whole run:

1. **`playwright-cli` skill** — if it is in the available skills list, invoke it and
   follow its commands (`open`, `goto`, `snapshot`, `close`). Preferred: the skill carries
   the session rules this skill relies on (one browser, close before ending).
2. **Playwright MCP server** — if a Playwright MCP is connected, use its navigate +
   snapshot tools.
3. **Another browser MCP server** (e.g. `chrome-devtools`) — use its navigate + snapshot
   tools.
4. **None detected** — prerequisite 5 fails. Stop and tell the user which tool to enable;
   do not fall back to `npx` or an arbitrary binary.

Record the selected tool in the report. The browser steps below describe the action and
show the `playwright-cli` form as the example; translate it to the MCP tool's equivalent
calls when an MCP was selected. Whatever the tool, it runs on the **host**: it must use
`{dest_base_url}` and `{source_bases}`, never `{internal_http_host}`.

---

## Input

One or more **source URLs** from the old site, or an issue reference whose body lists
example URLs. Accepted: a single URL, a list of URLs, or an issue id (use `glab`/`gh` to
fetch the body and extract URLs matching the `{source_bases}`).

### Input validation (mandatory before any query)

URLs come from users or issue bodies and are later substituted into SQL and shell
commands. Never substitute a raw value. For every URL:

1. **Match a configured base by parsed origin, not by string prefix.** Parse the URL
   into scheme, host, port and pathname. The origin (`scheme://host[:port]`) must equal
   the origin of one of `{source_bases}` exactly; `https://example.com.attacker.test`
   does not match `https://example.com` even though the string starts with it. When the
   base carries a language path prefix (`/en`), the pathname must equal it or continue
   with `/` right after it (`/en/news` matches, `/english` does not). Reject any URL that
   matches none of the bases and tell the user.
2. **Record the language.** The matched base (separate domain) or path prefix gives
   `{langcode}` for this URL, per the language URL rule in project-config.md. Use that
   `{langcode}` in every later query, alias lookup, and content check for this URL; the
   base language is only the fallback when no rule matches.
3. **Derive two paths and keep both.**
   - `{source_pathname}`: the full pathname from the parsed URL, including any language
     prefix, with leading and trailing `/` removed (`https://example.com/en/news/item/`
     → `en/news/item`). This is what the old URL looked like to the server and what
     redirects on the new site are keyed by; use it for every **destination** HTTP check.
   - `{relative_path}`: `{source_pathname}` with the matched base's language prefix
     removed (`news/item`). Use it to rebuild **source** URLs for other languages and
     to match scope/url-map rows when those tables store base-relative paths.
     The site root yields an empty string for both. Accept each value only if it is empty
     or matches `^[A-Za-z0-9/._~-]+$` (an already-decoded path with no query string).
     Stop on anything else, including quotes, `%`, `$`, backticks, spaces, or `..`.
4. **Build an exact lookup key, never a substring.** Scope and url-map rows are matched
   with `=` against the complete normalized value in the form the table stores (full URL
   `{source_url}`, or `/{source_pathname}`, or `/{relative_path}`; project-config.md →
   "URL Scope Support Table" says which). Compare both with and without a trailing `/`
   when the table is inconsistent. A `LIKE '%news/item%'` pattern also matches
   `news/item-old` and `news/item/child` and would silently pick the wrong migration
   action or destination entity. If a `LIKE` is unavoidable (unknown storage form), anchor
   it to a segment boundary (`url = '…' OR url LIKE '…/%'`) and escape `_` as `\_`.

**URL construction rule.** Every later URL is `{base}/{path}`, where `{base}`
(`{source_base}`, `{dest_base_url}`, `{internal_http_host}`) has no trailing slash and
`{path}` has no leading slash. For the root page use `{base}/`. Never concatenate a base
with a path that still starts with `/`, which produces `//path` and can be routed
differently by the server.

**Database-derived paths are untrusted too.** `{redirect_path}`, `{destination_alias}`,
`{lang_destination_alias}` and any `<final_url_col>` / `<map_dest_url_col>` value read from a table were
written by migrations and editors and are interpolated into shell commands below. Before
use, strip the leading `/` once and apply the **same allow-list** as step 3
(`^[A-Za-z0-9/._~-]+$`, or empty). Skip the path and record `FAIL — unsafe path` for
anything else (a stored `'`, `;`, `$(`, backtick or space would change the command).
Pass each completed URL to `curl` and to the browser tool as one single-quoted argument
(or as the MCP tool's URL parameter) and build the inner `{dest_runner}` command the same
way, so no shell layer re-interprets it.

---

## Workflow Overview

```
Phase 0: Resolve intent     -- What SHOULD have happened to this URL?
Phase 1: Redirect checks    -- Do all old paths land correctly?
Phase 2: Base-lang compare  -- Is the base-language content preserved?
Phase 3: Translations       -- Are other-language versions correct?
Phase 4: Non-migrate check  -- Do out-of-scope URLs return Gone?
Phase 5: Produce report     -- Structured verification output
```

---

## Phase 0 — Resolve Intent

If `{scope_table}` is defined, query it to learn the migration plan for this URL. Use the
exact lookup key from Input validation step 4 (`{lookup_key}`) and the `{langcode}`
detected there; run it through `{source_query}`:

```sql
SELECT <action_col>, <status_col>, <node_id_col>, <content_type_col>, <final_url_col>, <langcode_col>
FROM {scope_table}
WHERE (<url_col> = '{lookup_key}' OR <url_col> = '{lookup_key}/') AND <langcode_col> = '{langcode}'
LIMIT 5;
```

Select only the columns project-config.md declares; drop a column from the list when the
table has no equivalent (for example no `<content_type_col>`).

Interpret using the status values from project-config.md:

| `<action_col>` value                  | Meaning                      | Next phases       |
| ------------------------------------- | ---------------------------- | ----------------- |
| migrate value (e.g. `Migrare`)        | should have been migrated    | Phases 1, 2, 3, 5 |
| no-migrate value (e.g. `Non Migrare`) | should NOT exist on new site | Phase 4, then 5   |

No row found → tell the user the URL may be out of scope; ask how to proceed.

Also query the other-language row(s) to know which translations to expect in Phase 3.

---

## Phase 1 — Redirect Verification (migrate only)

### 1a. Resolve the destination entity

If `{url_map_table}` is defined, run through `{source_query}` with the same exact key:

```sql
SELECT <map_dest_id_col>, <map_dest_type_col>, <map_dest_url_col>
FROM {url_map_table}
WHERE <map_source_url_col> = '{lookup_key}' OR <map_source_url_col> = '{lookup_key}/'
LIMIT 5;
```

Otherwise resolve via the `<final_url_col>` / `<node_id_col>` values from Phase 0, or ask
the user. Result is the destination node ID.

### 1b. Destination URL alias

Drush core ships no path-alias command, so resolve the alias through the
`path_alias.manager` service:

```bash
{dest_runner} "drush php:eval \"print \\Drupal::service('path_alias.manager')->getAliasByPath('/node/{nid}', '{langcode}');\""
```

It prints the alias, or `/node/{nid}` itself when no alias exists for that language —
treat the latter as "alias missing" in the report. If project-config.md declares a
project-specific alias command (for example a custom Drush command), use that instead.

### 1c. Collect redirects for this entity

```bash
{dest_runner} "drush sql:query \"SELECT redirect_source__path, status_code, language FROM redirect WHERE redirect_redirect__uri = 'internal:/node/{nid}' ORDER BY language, redirect_source__path\""
```

> If the query errors with an unknown `redirect` table, the Redirect module is not
> installed on the destination. Skip redirect collection, record redirects as
> `N/A — Redirect module absent`, and continue with the remaining phases.

### 1d. HTTP-check each redirect path

For each redirect path plus the original `{source_pathname}` (the full old path,
language prefix included), check the response on the **new site** from inside the
container network (avoids SSL/DNS issues). Run two requests: the first hop alone, then
the chain followed to its end:

```bash
{dest_runner} "curl -sI -o /dev/null -w '%{http_code} %{redirect_url}' '{internal_http_host}/{redirect_path}'"
{dest_runner} "curl -sIL --max-redirs 5 -o /dev/null -w '%{num_redirects} %{http_code} %{url_effective}' '{internal_http_host}/{redirect_path}'"
```

Expected: preserved alias → first hop `200`; redirected path → first hop `301` **and**
final status `200` at the expected `url_effective`. `404` on either request = **FAIL**
(missing redirect or dead target). `301` to the wrong target, a final status other than
`200`, or `--max-redirs` exhausted (loop) = **FAIL**. Record path, expected, first-hop
code and `Location`, final code, effective URL, PASS/FAIL. Without `-L` a `301` to a
`404` looks like a pass.

---

## Phase 2 — Base-Language Content Verification (migrate only)

LLM comparison. Navigate both pages and compare substance, not structure.

### 2a. Source page (old site)

Navigate to `{source_base}/{relative_path}` with the selected browser tool and capture an
accessibility snapshot of the page. With the `playwright-cli` skill:

```bash
playwright-cli open '{source_base}/{relative_path}'
playwright-cli snapshot --filename=.playwright-cli/verify-source-base.yaml
```

Note: page title (`<h1>`/main heading), body text (main content area; ignore nav/footer/
sidebar), images (alt text, content vs decorative), links (text + href), video embeds,
meta info (dates, categories).

### 2b. Destination page (new site)

Navigate to `{dest_base_url}/{destination_alias}` in the same browser session and
capture a snapshot. With the `playwright-cli` skill:

```bash
playwright-cli goto '{dest_base_url}/{destination_alias}'
playwright-cli snapshot --filename=.playwright-cli/verify-dest-base.yaml
```

> The browser tool runs on the **host**, so it must use `{dest_base_url}`.
> `{internal_http_host}` (for example `http://web-container`) resolves only inside the
> tools container and is reserved for the container-side `curl` checks.

### 2c. Compare content

Semantic comparison. The old and new sites have different layouts, paragraph types, and
media handling. Focus on whether the **content substance** survived.

| Check         | What to look for             | PASS                                            | WARN                                       | FAIL                            |
| ------------- | ---------------------------- | ----------------------------------------------- | ------------------------------------------ | ------------------------------- |
| **Title**     | same page title/heading      | exact/near-exact                                | minor case/punctuation                     | missing or completely different |
| **Body text** | text preserved               | all meaningful text present                     | minor decorative omission                  | significant blocks missing      |
| **Images**    | content images accounted for | all present (alt/visual)                        | replaced by placeholder (flag, don't fail) | missing with no placeholder     |
| **Links**     | links preserved              | present, correct target (URL format may differ) | target changed but equivalent              | missing/broken                  |
| **Videos**    | embeds preserved             | present                                         | referenced differently but accessible      | completely missing              |
| **Documents** | downloadable files linked    | present                                         | different path, file accessible            | missing                         |

Comparison guidelines:

- **Layout differences are expected and OK.** Source-to-destination paragraph-type
  restructuring is intentional. Confirm the project's specific transformations against the
  "Migration Patterns" section of project-config.md when present.
- **Documented HTML tag transformations are intentional** — not content loss. (project-config.md may list them, e.g. `<u>`→`<em>`.)
- **Placeholder images → WARN, not FAIL** when the project uses placeholders for broken
  source files.
- **Content may be split differently.** One source paragraph → several destination
  paragraphs is fine if all text is present.
- **Minor whitespace/entity/formatting differences are OK.**

### 2d. Close browser before Phase 3

Close the browser session with the selected tool (`playwright-cli close`, or the MCP
tool's close/disconnect call).

---

## Phase 3 — Translation Verification

For each non-base language in `{languages}`:

### 3a. Is a translation expected?

From Phase 0 you know whether an other-language row exists in `{scope_table}` (or, with no
table, whether the user expects a translation). If not expected, confirm none was created:

```bash
{dest_runner} "drush sql:query \"SELECT langcode FROM node_field_data WHERE nid={dest_nid} AND langcode='<lang>'\""
```

- not expected AND absent → **PASS**
- not expected BUT present → **WARN** (investigate)
- expected → continue

### 3b. Source URL for the language

Translated pages do not share a slug (`/it/chi-siamo` ↔ `/en/about-us`), so never derive
`{lang_source_url}` by swapping the domain or language prefix on the base-language path.
Resolve the real one, in this order:

1. The other-language row(s) fetched in Phase 0 from `{scope_table}` (same
   `<node_id_col>`, `<langcode_col> = '<lang>'`): its `<url_col>` is the translation's
   source URL.
2. The `{url_map_table}` row whose `<map_dest_id_col>` is `{dest_nid}` and whose
   `<map_langcode_col>` matches.
3. If neither exists, ask the user for the translated source URL; do not guess it.

Validate the resolved URL exactly like the input (origin match, allow-list, both paths)
before using it.

### 3c. Destination URL for the language

```bash
{dest_runner} "drush php:eval \"print \\Drupal::service('path_alias.manager')->getAliasByPath('/node/{dest_nid}', '<lang>');\""
```

### 3d. Navigate + compare

Same process as Phase 2, adapted to the language — navigate and snapshot both pages with
the selected browser tool. With the `playwright-cli` skill:

```bash
playwright-cli open '{lang_source_url}'
playwright-cli snapshot --filename=.playwright-cli/verify-source-<lang>.yaml
playwright-cli goto '{dest_base_url}/{lang_destination_alias}'
playwright-cli snapshot --filename=.playwright-cli/verify-dest-<lang>.yaml
```

Apply the Phase 2 checklist.

### 3e. Language-specific redirects

```bash
{dest_runner} "drush sql:query \"SELECT redirect_source__path, status_code FROM redirect WHERE redirect_redirect__uri = 'internal:/node/{dest_nid}' AND language = '<lang>'\""
```

HTTP-check each like Phase 1d. If the `redirect` table is absent (see Phase 1c), skip this step.

---

## Phase 4 — Non-Migrate Verification

For URLs marked with the no-migrate value:

### 4a. Expected status

The `<status_col>` in `{scope_table}` says what HTTP code the old URL should return on the
new site (typically `410`).

### 4b. HTTP-check on the new site

The old URL is checked as the server saw it, language prefix included:

```bash
{dest_runner} "curl -sI -o /dev/null -w '%{http_code}' '{internal_http_host}/{source_pathname}'"
```

| Actual | Expected | Verdict                                      |
| ------ | -------- | -------------------------------------------- |
| 410    | 410      | **PASS** — correctly Gone                    |
| 404    | 410      | **FAIL** — should be 410 (map entry missing) |
| 200    | 410      | **FAIL** — page exists but shouldn't         |
| 301    | 410      | **FAIL** — redirects instead of Gone         |

---

## Phase 5 — Produce Report

### Single URL Report

```markdown
## Migration Verification: {source_url}

**Source node ID:** {node_id}
**Destination:** /node/{dest_nid} ({content_type})
**Action:** {action_value}
**Date:** {current_date}

### Redirects ({langcode})

| Old Path | Expected | Actual | Target | Status |
| -------- | -------- | ------ | ------ | ------ |

### Content ({langcode})

| Check | Status | Notes |
| ----- | ------ | ----- |

### Translations

| Language | Check | Status | Notes |
| -------- | ----- | ------ | ----- |

### Overall: {PASS|WARN|FAIL} ({summary})
```

### Batch Report

Summary table first (one row per URL: redirects / base content / translations / overall),
then individual reports. Surface FAILs and WARNs prominently.

### Overall Verdict Logic

- **PASS**: all checks pass.
- **WARN**: critical checks pass, but placeholder images or minor notes — human review
  recommended.
- **FAIL**: any redirect 404s, significant content missing, or an expected translation
  absent.

---

## Batch Mode

1. Collect all URLs (from the issue body via `glab`/`gh`, or the user's list).
2. Process sequentially (one browser at a time).
3. Produce the batch summary at the end.
4. Highlight FAILs/WARNs so they are not buried.

---

## Error Handling

- **Old page 404/500**: "Source page not accessible" — skip content compare; redirects can
  still run.
- **New page 404**: likely **FAIL** (not migrated / alias missing). Report it.
- **No scope-table row**: tell the user the URL is out of scope; ask before manual check.
- **No URL-map entry**: try `<final_url_col>` from the scope table; else "No URL mapping found".
- **Browser timeout**: report and continue; do not auto-retry.
- **Multiple scope-table matches**: show them; ask which to verify.

---

## Guardrails

- **Read-only.** No DB writes, no entity saves, no redirect creation.
- **Resolve config first.** Never hardcode domains, DB keys, or table names — read them
  from project-config.md.
- **Never skip the intent check** when a scope table exists.
- **Browser via the selected tool** — the `playwright-cli` skill when available, else a
  Playwright/browser MCP; never an ad-hoc `npx` binary. Close the browser between URLs in
  batch mode and before ending.
- **Source lookups via `{source_query}`, destination commands via `{dest_runner}`.**
  Never use the `mysql` client directly against a Drupal database.
- **Container-side `curl` via `{internal_http_host}`; browser navigation via
  `{dest_base_url}` (new site) and `{source_bases}` (old site).** The browser tool runs
  on the host and cannot resolve the internal host.
- **Exact URL matching.** No substring `LIKE` against scope or url-map tables.
- **Validate every path**, user-supplied or database-derived, before it reaches a shell.
- **Report honestly.** Ambiguous comparison → WARN, not a forced PASS/FAIL.
- **Do not fabricate content.** If a page is unreadable, say so.
