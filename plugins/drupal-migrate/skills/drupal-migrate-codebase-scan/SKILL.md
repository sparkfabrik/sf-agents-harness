---
name: drupal-migrate-codebase-scan
description: 'Scan the source codebase of a migration into Drupal and classify each custom code unit by disposition — replicate as a Drupal module, triage (needs a decision), do-not-port, or security (delete + report). Reads custom plugins/modules/themes and loose files to determine what each does and where it lands. Use during Phase 1 as-is analysis when the full source codebase is available and you are asked to "scan the custom code", "triage the plugins", "what custom code is there", or "classify the codebase". Explicitly handles the DB-only case (skips and records why). Writes the custom-code disposition into the as-is corpus per the drupal-migrate-analysis-docs skill.'
---

# Codebase scan (custom-code disposition)

Read the delivered source codebase and classify every custom code unit by what must
happen to it. This separates the one or two genuine engineering items from the long
tail of drop / triage, so Phase 2 mapping and Phase 3 scoping rest on facts about what
the code actually does.

## Prerequisites

- `drupal-migrate-detect-source` established **delivery** = codebase available. If
  delivery is **DB-only**, see Step 0.
- `drupal-migrate-platform-audit` produced the custom-code list (this skill resolves
  each item's disposition).
- Read `drupal-migrate-analysis-docs` and `mermaid-diagrams` before writing.

## Steps

### Step 0 — DB-only short-circuit

If no source codebase was delivered, **do not invent one**. Record in the as-is corpus:
"Source delivered as DB-only; custom-code disposition limited to extension names visible
in the database (`active_plugins` / `core.extension`), no source to classify." Report
that and stop — the disposition is a stakeholder/dependency item, not an analysis output.

### Step 1 — Read config + recover

Read `project-config.md`. Recover the platform-audit custom-code list and any prior
disposition notes; update/cite rather than rewrite.

### Step 2 — Read each custom unit

For each custom plugin/module/theme and loose file, read enough to know what it does —
entry points, hooks, outbound calls, stored data, bundled frontend assets:

```bash
ls -la <plugins-or-modules-dir>
# per unit: size, main file, what it hooks / calls
grep -rEi "add_action|add_filter|register_|hook_|MigrateSource|curl_exec|call_user_func" <unit> 2>/dev/null
```

Note licensed/third-party units (not custom — they map to a Drupal contrib/core
equivalent in Phase 2, not a rebuild). Note any unit whose name or behaviour looks
obfuscated or malicious.

### Step 3 — Classify by disposition

Assign each unit exactly one disposition:

| Disposition             | Meaning                                                                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **replicate-as-module** | Genuine custom behaviour with no off-the-shelf equivalent — becomes a custom Drupal module. Usually the real engineering work; flag the highest-risk one. |
| **replace-with-config** | Behaviour covered by Drupal config / a contrib module — no custom code.                                                                                   |
| **triage**              | A decision remains (carry the data or drop it?); not a blocker, but record the open question.                                                             |
| **do-not-port**         | A hack, dev convenience, or platform-handled concern — drop.                                                                                              |
| **security**            | Malware / backdoor / liability — delete and **report**, do not migrate. Treat as a security finding, not a data store.                                    |

Ground each disposition in what the code does. If a unit is externally blocked (needs a
third-party contract), say so and name the dependency.

### Step 4 — Diagram + write into the corpus

Add a grouped Mermaid diagram (via `mermaid-diagrams`): one region per disposition, the
highest-risk and security items visually distinct, and any external blocker as an edge.
Per `drupal-migrate-analysis-docs`, the **inventory** (what each unit is) is a frozen
as-is fact belonging in `platform.md`'s custom-code table; the **disposition reasoning**
is to-be analysis — record it where the drupal-migrate-analysis-docs skill places to-be content
(parent-level doc or the Phase 2 mapping change), referencing the as-is inventory rather
than copying it.

## Output

- The custom-code disposition (diagram + per-unit classification) written to the corpus
  (path reported), referencing the as-is inventory.
- A summary: the replicate-as-module item(s) and their risk, any security finding, the
  triage decisions still open.

## Guardrails

- **Read-only** — read the source files; never edit, run, or "test-execute" them. A
  suspected backdoor is reported and read statically, never run.
- **DB-only → skip + record**, never fabricate a codebase.
- **Disposition is reasoned, not assumed** — grounded in what the code does; an unknown
  unit is `triage`, not a guess.
- Keep the frozen inventory (as-is) and the disposition reasoning (to-be) in their
  correct homes per drupal-migrate-analysis-docs; don't duplicate.
