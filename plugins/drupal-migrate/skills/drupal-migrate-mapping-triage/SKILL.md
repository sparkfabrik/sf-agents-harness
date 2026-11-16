---
name: drupal-migrate-mapping-triage
description: 'Produce the to-be mapping document that bridges a documented source onto the Drupal target — the triage step between as-is analysis and implementation. Maps each source module/plugin to a Drupal disposition (core / contrib / custom module / drop), maps the source content model onto target content types (direct reuse, many-to-one collapse, target-with-no-source, source-with-no-target), and records the open questions to stakeholders and the migration risks that block a confident solution. Use during Phase 2 when asked to "map the source onto Drupal", "triage the modules/plugins", "map the content model", "what maps to what", or "what are the open questions and risks". Writes an OpenSpec change per the drupal-migrate-analysis-docs skill; it stops before proposing the implementation.'
---

# Mapping triage (to-be bridge)

Bridge the documented as-is to the Drupal target. This is the decision-bearing
middle of the migration: it turns frozen source facts into "where each piece lands",
and it isolates the unknowns as stakeholder questions so the solution proposal that
follows rests on confirmed facts, not assumptions.

It **stops before proposing the implementation** (Migrate pipelines, module code, recipe
application) — those are Phase 3, and several mappings depend on answers only
stakeholders can give.

## Prerequisites

- The as-is is documented: `platform.md` (extension inventory), `ecosystem.md`
  (integrations), `content-inventory.md` + the data-model doc (content model),
  `drupal-migrate-codebase-scan` disposition, IA/liveness. If a needed dimension is missing, run that
  Phase 1 skill first, or stop and request it.
- The **destination** content model is known (or its source is): the target Drupal site's
  config, or a shared recipe/package it consumes. Reconcile against it — don't invent
  target types.
- Read `drupal-migrate-analysis-docs` and `mermaid-diagrams` before writing.

## Steps

### Step 1 — Read config + recover the corpus

Read `project-config.md` and the full as-is corpus. Cite as-is facts by reference; never
re-measure or restate them. Recover any prior `decisions.md` / `considerations.md`.

### Step 2 — Thread 1: module/plugin mapping

Map each **active** source module/plugin (from `platform.md`, activation-verified) to one
Drupal disposition, grouped:

| Disposition       | Meaning                                                                                                                     |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **native (core)** | Drupal core already covers it — no module needed.                                                                           |
| **contrib**       | A contrib module replaces it — name the module.                                                                             |
| **custom module** | Genuine custom behaviour — becomes a custom Drupal module (cross-reference the `drupal-migrate-codebase-scan` disposition). |
| **drop**          | Platform-handled, source-topology-only (e.g. multisite tooling), migration tooling, or a security item — not carried.       |

Reconcile the contrib list against the **destination's existing baseline** (the shared
recipe/corporate site often already ships Metatag, Redirect, Pathauto, etc.) — don't
propose adding what's already there.

### Step 3 — Thread 2: content-architecture mapping

Map the source content model (post types / content types + the real model — ACF groups,
paragraphs) onto **target content types**. Classify each edge:

- **direct reuse** — source type → an existing target type, fields largely align.
- **collapse (many→one)** — several source types/groups/sites fold into one target type;
  flag this as usually the dominant, highest-risk migration.
- **target with no source** — a target type the source has no content for → likely
  skipped (confirm).
- **source with no target** — a source construct with no clean target → new paragraph on
  an existing type, or a net-new extension.

Flag any field-level gap on a collapse target as a dedicated risk (it cascades).

### Step 4 — Diagrams

Add Mermaid diagrams (via `mermaid-diagrams`), each with a "Reading the diagram" legend:
the module dispositions (grouped flowchart), and the source→target content map (flowchart
with a thick edge marking the dominant collapse, dotted edges for unconfirmed mappings).

### Step 5 — Open questions + risks

- **Open questions to stakeholders** — every mapping that depends on an external answer,
  with the owner in brackets. These block the solution proposal; record them, do **not**
  answer them.
- **Risks** — the field-level gap on the dominant collapse, externally-blocked custom
  modules, any security finding, data that needs a non-trivial transform (e.g.
  serialized values needing a programmatic walk), and SEO-weighted redirects.

### Step 6 — Write as an OpenSpec change

Per `drupal-migrate-analysis-docs`, a reviewable mapping has a review/approval lifecycle,
so it is an **OpenSpec change** (`openspec/changes/<name>/`), not a plain doc — or the
plain-markdown stand-in that skill defines when the project has no `openspec/`. Write the
current-state mapping with the diagrams, threads, open questions, and risks; mark
implementation explicitly out of scope. Record agreed directions in
`doc/Migrate/decisions.md` and working hypotheses in `considerations.md`, and link the
change from the `doc/Migrate/README.md` index.

## Output

- The mapping OpenSpec change written (path reported), with diagrams, dispositions, open
  questions, and risks.
- A summary: the module disposition counts, the content-mapping highlights (especially
  the dominant collapse), the top risks, and the blocking stakeholder questions.

## Guardrails

- **Map only documented as-is facts** — reference the as-is corpus; if a fact is missing,
  go get it (Phase 1) rather than guessing.
- **Reconcile against the real destination baseline** — never invent target types or
  propose contrib modules the target already ships.
- **Stop before implementation** — no Migrate YAML, plugin code, or task breakdown; those
  are Phase 3.
- **Record open questions, don't resolve them** — stakeholder-owned answers are inputs to
  the later proposal.
- **Don't duplicate** — cite `platform.md`, `ecosystem.md`, the data-model doc, and the
  `drupal-migrate-codebase-scan` disposition rather than restating them.
