# PT track -- Penetration Testing

Depth-first assessment of a **running target**. The goal is to confirm
exploitability -- turn "might be vulnerable" into "is exploitable, here is the
proof."

PT is gated on authorization. Do not start until section 0 of
`pt-runbook-drupal.md` is satisfied.

## Two PT targets: local (destructive) and remote (non-destructive)

PT checks split by how invasive they are, and run against different targets so a
client's shared environment is never mutated:

- **Destructive / authenticated checks -> the LOCAL instance.** The locally built
  running site (the same code as the VA repo) is disposable and fully controlled,
  so it is the right place for tests that submit forms, write/delete content, or
  extract data: authenticated ZAP active scan, sqlmap, Form API / JSON:API write
  probes, file-upload tests. Use a dedicated **local Drupal test account** (low
  privilege). Nothing here touches the client's environment.
- **Non-destructive checks -> the REMOTE URL** (the running site the user
  provides -- any environment they authorize: staging, pre-prod, or production).
  Safe to run against a shared or live environment: recon/fingerprint, the Nuclei
  template/CVE scan, security-header and information-disclosure checks. No
  mutation, no app login required (an edge Basic-auth gate is fine via
  `BASIC_AUTH`). Against production, rate-limit hard and keep strictly to these
  non-destructive checks.

Either target is optional. Both running the same codebase means a vulnerability
demonstrated destructively on the local instance is evidence for the deployed
remote too -- without having attacked the remote. Run destructive checks against
the remote **only** with explicit authorization, a backup, and a window (runbook
section 0); otherwise keep them local.

Tag each finding's `evidence` with where it was confirmed ("local instance,
authenticated" vs "remote, unauthenticated") so the report is honest
about what was tested where.

| Check                                      | Destructive? | Default target    |
| ------------------------------------------ | ------------ | ----------------- |
| Recon / fingerprint (nmap, httpx, WhatWeb) | no           | remote            |
| Nuclei template / CVE scan                 | no           | remote            |
| Security headers, info-disclosure probes   | no           | remote            |
| droopescan enumeration                     | no           | remote (or local) |
| Authenticated ZAP active scan              | **yes**      | local             |
| sqlmap                                     | **yes**      | local             |
| Form API / JSON:API write, file upload     | **yes**      | local             |

## Engine

The PT track follows `pt-runbook-drupal.md`, the CTO-provided Docker-based
runbook. It is Drupal-focused; the phase structure is generic. Its phases:

| Phase                    | Tools                      | Produces                                              |
| ------------------------ | -------------------------- | ----------------------------------------------------- |
| 0. Pre-engagement        | --                         | Authorization, backup, scope, out-of-scope list       |
| 1. Recon / fingerprint   | nmap, httpx, WhatWeb       | `nmap-*`, `httpx.json`                                |
| 2. Enumeration           | droopescan + manual checks | `droopescan.json`                                     |
| 3. Template / CVE scan   | nuclei                     | `nuclei.json`, `nuclei.sarif`                         |
| 4. Authenticated DAST    | OWASP ZAP                  | `zap-baseline.html`, `zap-full-report.html`           |
| 5. Targeted exploitation | sqlmap, ffuf               | `sqlmap/`, `ffuf.json`                                |
| 6. Manual hotspots       | --                         | JSON:API, Views, Form API, file handling, cache, Twig |

For a non-Drupal target, keep the phase order and swap stack-specific tooling
(skip droopescan; use the relevant CMS/framework enumeration and templates).

## Track contract

When PT runs, it MUST produce, under `<engagement-dir>/pt/`:

1. `pt-findings.json` -- every confirmed finding normalized to the schema in
   `findings-schema.md`, with `"track": "PT"`.
2. `artifacts/` -- every raw tool output the runbook generates (nmap, httpx,
   droopescan, nuclei JSON+SARIF, ZAP HTML, sqlmap dir, ffuf). Reference these
   from each finding's `artifacts` array.

## Mapping runbook output to findings

- **`location`** is the affected URL and parameter
  (e.g. `https://target.example.com/jsonapi/node/article?filter[x]=1`), not a
  source line.
- **`evidence`** carries the proof: the request sent, the observed response or
  extracted data, and the tool that produced it. This is what distinguishes a PT
  finding from a VA finding -- it demonstrates impact, not just presence.
- **`tool`** is the runbook tool (`nuclei`, `zap`, `sqlmap`, `ffuf`) or
  `manual` for the section-7 hotspot checks.
- **CVEs** confirmed live (e.g. SA-CORE-2026-004 / CVE-2026-9082) are
  `critical`; cross-reference the VA finding for the same CVE if one exists.
- Map nuclei `info`/`low` template hits to `info`/`low`; only promote to
  `medium`+ when impact is demonstrated.
- **A zero-match nuclei run is only trustworthy if templates actually loaded.**
  Record the `Templates loaded for current scan` count (a `drupal,cve` run loads
  ~4000) in the finding's `evidence`. A run that loaded 0 templates is a false
  negative, not a clean result -- see the gotcha in `pt-runbook-drupal.md`.

## Verification is mandatory

Active scanners produce false positives. **Every PT finding must be verified
before it lands in `pt-findings.json`.** A nuclei or ZAP alert is a lead, not a
finding. Reproduce it, capture the request/response, and only then record it.
State the verification in `evidence` (e.g. "ZAP flagged; manually reproduced,
confirmed reflected XSS in the `q` parameter").

## Relationship to VA

- A CVE the VA track found in `composer.lock` becomes a PT finding **only when
  confirmed exploitable** against the live target. Link the two via the shared
  `cve` value -- the report groups them.
- PT may surface issues VA cannot (session handling, cache poisoning,
  authorization bypass behind login, JSON:API permission leakage). These have no
  VA counterpart and stand alone.

## Boundaries

- PT sends real traffic and can mutate data. Use a dedicated test account with
  minimal privileges, never a live admin.
- Rate-limit against production or behind a WAF (`-rl` for nuclei, lower
  sqlmap `--level`/`--risk` unless explicitly authorized to raise them).
- A PT-only engagement is valid: pass only `--pt` to `build-report.py`.
