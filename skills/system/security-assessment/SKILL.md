---
name: security-assessment
description: 'Orchestrate a full security assessment split into two tracks -- Vulnerability Assessment (VA, static code and dependency scanning) and Penetration Testing (PT, live recon and exploitation against a running target) -- then merge both into a single standalone HTML report. Use when the user wants a combined VA + PT security assessment, a security engagement report, to run both a code audit and a live pentest, or to build an HTML security report from existing VA and PT findings. Also use when the user mentions "security assessment", "VA and PT", "vulnerability assessment", "penetration testing", "pentest report", "engagement report", "combined security report", or references a Drupal pentest runbook.'
---

# Security Assessment Skill

Runs a security engagement as two independent tracks and merges their findings
into one self-contained HTML report. VA tells you what _might_ be vulnerable; PT
confirms what _is_.

- **VA -- Vulnerability Assessment**: breadth-first, non-intrusive. SAST,
  dependency CVEs, secret detection, IaC misconfiguration, and manual code
  review against the **codebase**.
- **PT -- Penetration Testing**: depth-first, intrusive. Recon, fingerprinting,
  template/CVE scanning, authenticated DAST, and targeted exploitation against a
  **running target**. Requires written authorization.

## Architecture

```
main thread (orchestrator)
├── VA track  ──►  va/va-findings.json   (+ raw scanner artifacts)
├── PT track  ──►  pt/pt-findings.json   (+ raw tool artifacts)
└── build     ──►  report.html           (merges both via bundled script)
```

If the host supports subagents, dispatch each track as a separate agent and run
them in parallel (VA on the code, PT on the target); otherwise run them
sequentially. Each track writes its own findings JSON; the main thread builds
the report at the end. The tracks share no state except the engagement directory.

## Before you start

**STOP and ask the user for the inputs below. Do not run anything until they
answer.** These targets are security-sensitive: **never auto-detect, infer, or
guess them** from the working directory, running containers, `ddev`/`docker`
state, `.env`, or CI config. Detecting a URL and scanning it without the user
naming it is wrong even if a guess looks obvious -- a wrong PT target means
scanning a system you were not authorized to touch. Ask explicitly, in your own
message, and wait for each answer. Confirm the depth (full vs targeted) **and**
the targets -- depth alone is not enough.

Ask with the structured question prompt, **one question per input**, and make
each target question **free-text so the user types the value**. The repo path,
the two URLs, and the credentials are typed in -- present them as open-entry
questions (a "Skip / none" choice is fine alongside the text field), never as a
fixed list of canned answers, and never pre-fill a detected/guessed URL as the
selectable answer. The depth choice (full vs targeted) may be a normal
multiple-choice. Ask them together (or back to back) and wait for the typed
answers:

1. **Local repository to code-scan (VA)** -- the path to the project source.
   Default to the current working directory (confirm it; don't assume silently).
   VA runs entirely against this local code; it sends no traffic anywhere.
2. **Local instance URL (PT, destructive)** -- the running build of that repo
   (e.g. a DDEV/Docker `*.loc` URL). **Ask the user for it; do not read it from
   running containers.** This disposable, fully-controlled copy is where the
   **destructive/authenticated** checks run -- authenticated ZAP active scan,
   sqlmap, Form API/JSON:API write probes -- so the client's environment is never
   mutated. Optional; also ask for a **local Drupal test account** (low privilege)
   to enable authenticated checks. Leave empty to skip destructive PT.
3. **Remote URL (PT, non-destructive)** -- the running site to run **safe** checks
   against: recon, the Nuclei template/CVE scan, security-header and
   information-disclosure checks. **The user must type this URL; never assume it
   equals the local site or a detected host.** May be any environment the user
   authorizes (staging, pre-prod, or production). Production raises the bar --
   rate-limit hard and keep strictly to non-destructive checks. Leave empty to
   skip remote PT.
4. **Remote HTTP Basic auth (optional)** -- the remote is often gated behind a
   Basic-auth realm. Ask for `user:pass`; **accept "none"**. When provided, pass
   it to the runner as `BASIC_AUTH` (sent on every request, preflighted). Keep
   credentials out of the engagement files and the report.

Then confirm:

5. **Engagement directory** -- `.security-assessment/` **at the root of the local
   repo being assessed**. Always write findings, artifacts, and the report
   inside the target project, never a temp or external path. Add
   `.security-assessment/` to the project's `.gitignore`. Record targets and
   metadata in `.security-assessment/engagement.json` (schema in
   `references/findings-schema.md`): local repo path in `scope`, the URLs in
   `target`.
6. **Destructive-on-remote gate** -- run destructive checks against the **remote**
   URL only with explicit authorization, a backup, and a window (runbook section
   0). By default destructive checks stay on the local instance and the remote
   gets non-destructive checks only. If neither PT target is given, run VA only
   and record PT as "not run".

## VA track

Enumerate vulnerabilities in the codebase without touching a live target.
Discover stacks, run project-native and Docker-augmented scanners (semgrep,
trivy, gitleaks, grype, psalm, phpstan, composer audit, gosec, govulncheck,
bandit, and more), then review by hand for what tools miss. Workflow in
`references/va-methodology.md`; contract and scan scoping (skip data dumps,
`.gitignore` handling) in `references/va-track.md`.

Write to `<engagement-dir>/va/`: `va-findings.json` (`"track": "VA"`) and raw
scanner outputs under `artifacts/`, linked from each finding.

## PT track

Confirm exploitability against the running target(s). Follow
`references/pt-runbook-drupal.md` (Drupal-focused; the recon → enumeration →
template scan → authenticated DAST → exploitation → manual-hotspot phase order
applies to any stack). Mapping rules and the **local-vs-remote target split** are
in `references/pt-track.md`.

Route checks by invasiveness: **destructive/authenticated** checks (ZAP active
scan, sqlmap, Form API/JSON:API writes) run against the **local instance** with a
local test account; **non-destructive** checks (recon, Nuclei templates, headers,
info-disclosure) run against the **remote URL**. Same codebase, so a local
exploitation finding is evidence for the deployed remote without attacking it.
Tag each finding's `evidence` with where it was confirmed (local-authenticated vs
remote-unauthenticated).

Write to `<engagement-dir>/pt/`: `pt-findings.json` (`"track": "PT"`) and raw
tool outputs (`nmap-*`, `httpx.json`, `nuclei.json/sarif`, `zap-*.html`,
`sqlmap/`, `ffuf.json`) under `artifacts/`. **Verify every PT finding before it
lands** -- active scanners produce false positives; record verification in the
`evidence` field.

## Findings and severity

Both tracks emit the **same lean finding shape** (`references/findings-schema.md`)
so the report can merge them. Raw artifacts stay native (JSON/SARIF/HTML) and are
linked as evidence; the normalized JSON is the merge layer, not a replacement.

| Severity   | Meaning                                                                          |
| ---------- | -------------------------------------------------------------------------------- |
| `critical` | RCE, auth bypass, SQLi with data exfiltration, exploited-in-the-wild CVE present |
| `high`     | Stored XSS, authorization bypass, sensitive data exposure, exploitable CVE       |
| `medium`   | Reflected XSS, missing security headers, information disclosure                  |
| `low`      | Best-practice gaps, verbose errors, minor hardening                              |
| `info`     | Defense-in-depth recommendations, observations                                   |

## Building the report

```bash
# run from the root of the project being assessed
python3 <skill-path>/assets/build-report.py \
  --engagement .security-assessment/engagement.json \
  --va .security-assessment/va/va-findings.json \
  --pt .security-assessment/pt/pt-findings.json \
  --coverage .security-assessment/coverage.json \
  --checklist .security-assessment/checklist.json \
  --out .security-assessment/report.html
```

- `--va` and `--pt` are both optional -- pass whichever tracks ran; a single-track
  run produces a single-track report and says so.
- Standard-library Python 3 only. Validates findings against the schema and
  renders one **standalone** HTML file (inline CSS/JS, opens offline, prints
  cleanly). Restyle via `assets/report-template.html`; never hand-edit the output.

The report links evidence by **relative path** (`va/artifacts/…`, `pt/artifacts/…`).
When handing the report to a client, ship the **whole `.security-assessment/`
folder** (or zip it) so those links resolve -- copying `report.html` alone leaves
the evidence links dangling.

The report contains engagement metadata, per-track executive summaries, a
severity matrix (VA vs PT vs combined), a **Tests performed** section (green
PASS rows for checks that ran and found nothing -- audit proof of breadth --
with executed counts and an explicit count of checks that could not complete), a
filterable findings list, an artifact appendix, and a **Detailed test log** -- the
full enumerated list of every individual check (e.g. all ~4000 Nuclei templates,
each probe, each dependency) flagged green (ok) or red (problem), grouped and
collapsible. After building, give the user the path and show the matrix.

Optionally pass `--coverage .security-assessment/coverage.json` (summary, "Tests
performed") and `--checklist .security-assessment/checklist.json` (per-test
green/red, "Detailed test log") -- schemas in `references/findings-schema.md`.
`nuclei-scan.sh` writes both for its run; append the other tools' entries. These
are what give a client evidence of every check executed, passed or not.

## Output layout

```
<project-root>/.security-assessment/      <- gitignored, inside the target project
├── engagement.json
├── report.html                 <- final deliverable
├── va/{va-findings.json, artifacts/}
└── pt/{pt-findings.json, artifacts/}
```

## References

- `references/va-track.md` -- VA track contract, scan scoping, finding mapping.
- `references/va-methodology.md` -- VA scanners and manual-review workflow.
- `references/{php,go,nodejs}-security.md`, `dockerfile-templates.md` -- per-language depth and pinned scan-container templates.
- `references/pt-track.md` -- PT track contract; mapping runbook output to findings.
- `references/pt-runbook-drupal.md` -- the CTO Docker-based pentest runbook.
- `references/findings-schema.md` -- `engagement.json` and findings JSON schema.
