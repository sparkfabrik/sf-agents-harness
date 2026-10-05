---
name: drupal-migrate-ecosystem-map
description: 'Produce the as-is ecosystem document for a migration into Drupal — the external systems the source site integrates with today (CRM, mailing, form back-ends, analytics, payment, single sign-on). Captures each integration''s direction, mechanism, and the data that crosses the boundary, with a topology diagram. Use during Phase 1 as-is analysis when asked to "map the integrations", "what external systems does the site talk to", "document the ecosystem", or "find the CRM/mail/forms hooks". Writes as-is/ecosystem.md per the drupal-migrate-analysis-docs skill.'
---

# Ecosystem map (as-is)

Document the external systems the source integrates with, as frozen facts. Each
integration is a migration risk and a stakeholder dependency: it must be re-pointed,
replaced, or dropped, and several need a contract only an external party can supply.

## Prerequisites

- `drupal-migrate-detect-source` + `drupal-migrate-db-discover` have run.
- `drupal-migrate-platform-audit` ideally done (the plugin/module inventory names the
  integration extensions).
- Read `drupal-migrate-analysis-docs` and `mermaid-diagrams` before writing.

## Steps

### Step 1 — Read config + recover

Read `project-config.md`. Check for an existing `as-is/ecosystem.md`; update/cite rather
than rewrite. Use the db-discover access method for queries.

### Step 2 — Enumerate integrations from evidence

Find integrations from three sources, not from assumption:

- **The extension inventory** (from platform-audit) — CRM connectors, mail/newsletter
  plugins, form back-ends, analytics/tag managers, payment, SSO.
- **The codebase** (if delivered) — outbound HTTP endpoints, API base URLs, OAuth/
  client-credential config, embedded SDKs (e.g. Stripe.js, FilePond), iframe embeds.

  ```bash
  grep -rEi "https?://[a-z0-9.-]+\.(com|net|io|azurewebsites\.net)" <codebase> --include="*.php" --include="*.js" 2>/dev/null | sort -u
  grep -rEi "client_id|client_secret|api_key|oauth|odata|webhook" <codebase> 2>/dev/null
  ```

- **Stored config in the DB** — connector settings, API endpoints, list IDs.

### Step 3 — Characterise each integration

For each external system, record:

- **System** and **purpose** (CRM lead capture, newsletter, residual forms, …).
- **Direction** — outbound (site → system), inbound, or bidirectional.
- **Mechanism** — direct API (which protocol), a bridge service, an embedded SDK, an
  iframe.
- **Data crossing the boundary** — what fields/entities, and any credentials' location.
- **Confidence** — confirmed from code/DB vs inferred; flag unknowns as stakeholder
  questions (don't resolve them here).

### Step 4 — Topology diagram

Add a Mermaid topology diagram (via `mermaid-diagrams`): the source site in the centre,
external systems around it, solid edges for primary data flows and dotted edges for
secondary ones, custom bridges visually distinct. Follow with a short "Reading the
diagram" legend.

### Step 5 — Write the doc

Write `doc/Migrate/as-is/ecosystem.md` per `drupal-migrate-analysis-docs`: status
header, the diagram + legend, and a table per integration. Add the row to
`as-is/README.md`. Keep target/replacement decisions out — frozen as-is only.

## Output

- `doc/Migrate/as-is/ecosystem.md` written (path reported).
- A summary listing each external system, its mechanism, and any unconfirmed item.

## Guardrails

- **Evidence-based** — every integration grounded in code, config, or a DB row; mark
  inferred items as such.
- **No replacement decisions** — that is Phase 2 mapping. Here: what talks to what,
  today.
- **Read-only**; never call an external endpoint to "test" it, and never expose
  credentials in the doc — reference where they live.
- Don't duplicate the platform inventory — reference `platform.md` for the extension list.
