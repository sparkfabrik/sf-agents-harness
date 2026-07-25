# Findings and engagement schema

Both tracks emit findings in the same shape so `build-report.py` can merge them.
The schema is intentionally minimal. Unknown extra fields are ignored by the
builder, so a track may attach extra context without breaking the report.

All files are UTF-8 JSON.

## engagement.json

One object describing the engagement. Written once, before the tracks run.

```json
{
  "project": "Acme Drupal Platform",
  "target": "https://staging.example.com",
  "date": "2026-06-11",
  "scope": "Drupal application code, dependencies, and the staging web surface.",
  "out_of_scope": "Third-party SSO, payment provider, CDN origin.",
  "stacks": ["PHP/Drupal 10", "Node.js 22"],
  "tracks": ["VA", "PT"],
  "authorization": "Signed engagement letter ENG-2026-014, staging only, rate-limited.",
  "va_summary": "Static scans and code review across the Drupal codebase and dependencies.",
  "pt_summary": "Authenticated DAST and targeted exploitation against staging."
}
```

| Field           | Type     | Required | Notes                                                                 |
| --------------- | -------- | -------- | --------------------------------------------------------------------- |
| `project`       | string   | yes      | Display name.                                                         |
| `target`        | string   | no       | Live target URL (PT). Empty for VA-only.                              |
| `date`          | string   | yes      | `YYYY-MM-DD`.                                                         |
| `scope`         | string   | yes      | What was assessed.                                                    |
| `out_of_scope`  | string   | no       | Explicitly excluded surface.                                          |
| `stacks`        | string[] | no       | Detected stacks/versions.                                             |
| `tracks`        | string[] | yes      | Subset of `["VA", "PT"]` that ran.                                    |
| `authorization` | string   | no       | Reference for PT authorization. Required when `tracks` includes `PT`. |
| `va_summary`    | string   | no       | 1-3 sentence VA executive summary.                                    |
| `pt_summary`    | string   | no       | 1-3 sentence PT executive summary.                                    |

## va-findings.json and pt-findings.json

A JSON array of finding objects. Same shape for both files; the `track` field
distinguishes them.

```json
[
  {
    "id": "PT-001",
    "title": "Anonymous SQL injection via JSON:API filter",
    "severity": "critical",
    "track": "PT",
    "category": "SQL injection",
    "tool": "sqlmap",
    "location": "https://staging.example.com/jsonapi/node/article?filter[x]=1",
    "cwe": "CWE-89",
    "cve": "CVE-2026-9082",
    "description": "The JSON:API filter parameter is injectable on the PostgreSQL-backed site (SA-CORE-2026-004).",
    "impact": "Unauthenticated database read; full content and user table exfiltration.",
    "evidence": "sqlmap confirmed boolean-based blind and UNION injection. Verified manually: extracted users.name. See pt/artifacts/sqlmap/.",
    "recommendation": "Apply Drupal core security update SA-CORE-2026-004 immediately. Restrict JSON:API write/filter exposure.",
    "status": "open",
    "artifacts": ["pt/artifacts/sqlmap/log", "pt/artifacts/nuclei.json"]
  }
]
```

| Field            | Type     | Required | Notes                                                                               |
| ---------------- | -------- | -------- | ----------------------------------------------------------------------------------- |
| `id`             | string   | yes      | Unique within the file. Convention: `VA-001`, `PT-001`.                             |
| `title`          | string   | yes      | Short, specific.                                                                    |
| `severity`       | enum     | yes      | `critical` \| `high` \| `medium` \| `low` \| `info`.                                |
| `track`          | enum     | yes      | `VA` \| `PT`. Must match the file.                                                  |
| `category`       | string   | yes      | e.g. `SQL injection`, `XSS`, `CVE`, `Access control`, `Secret leak`.                |
| `tool`           | string   | yes      | Scanner that found it, or `manual review`.                                          |
| `location`       | string   | yes      | `file:line` for VA; URL/parameter for PT.                                           |
| `cwe`            | string   | no       | e.g. `CWE-89`.                                                                      |
| `cve`            | string   | no       | e.g. `CVE-2026-9082`, or a Drupal `SA-CORE-...` reference.                          |
| `description`    | string   | yes      | What the issue is.                                                                  |
| `impact`         | string   | yes      | What an attacker achieves.                                                          |
| `evidence`       | string   | yes      | Snippet, request/response, or scanner excerpt. For PT, include verification status. |
| `recommendation` | string   | yes      | Concrete fix, with the patched version where applicable.                            |
| `status`         | enum     | no       | `open` (default) \| `fixed`.                                                        |
| `artifacts`      | string[] | no       | Paths (relative to engagement dir) to raw evidence files.                           |

## coverage.json (optional -- "Tests performed")

A JSON array describing what each tool actually ran. Drives the report's "Tests
performed" section: green PASS rows are checks that executed and found nothing
(audit proof of breadth), and errored/incomplete checks are shown explicitly so
"attempted but not completed" is never mistaken for "clean". Pass it with
`--coverage`.

```json
[
  {
    "track": "PT",
    "tool": "nuclei",
    "category": "Full template + CVE sweep (drupal,cve, HTTP)",
    "executed": 4080,
    "findings": 0,
    "errored": 21,
    "status": "partial",
    "note": "100% of templates executed; 21 requests stalled by the edge (WAF)"
  }
]
```

| Field      | Type   | Required | Notes                                                                                                                         |
| ---------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `track`    | enum   | yes      | `VA` \| `PT`.                                                                                                                 |
| `tool`     | string | yes      | Scanner/tool name (e.g. `nuclei`, `semgrep`, `trivy`).                                                                        |
| `category` | string | yes      | The check set that ran (e.g. "PHP SAST", "Drupal templates").                                                                 |
| `executed` | int    | yes      | Number of checks/templates/rules that ran.                                                                                    |
| `findings` | int    | no       | Matches produced (default 0).                                                                                                 |
| `errored`  | int    | no       | Checks that could not complete (timeouts, connection errors).                                                                 |
| `passed`   | int    | no       | Defaults to `executed - findings - errored`.                                                                                  |
| `status`   | enum   | no       | `pass` \| `partial` \| `findings`. Auto-derived if omitted: findings>0 → `findings`; else errored>0 → `partial`; else `pass`. |
| `note`     | string | no       | Context (e.g. why some checks errored).                                                                                       |

`nuclei-scan.sh` writes a `coverage.json` entry automatically (executed/findings/
errored parsed from its run). For other tools, append an entry per scanner so the
report shows the full breadth of the audit.

## checklist.json (optional -- "Detailed test log")

A JSON array of **individual** tests, each green (ok) or red (problem). Drives the
report's "Detailed test log" section at the end -- the full enumerated audit
trail a client can scan line by line. Grouped by `(track, tool)` into collapsible
panels (groups with a problem auto-expand). Pass it with `--checklist`.

```json
[
  { "track": "PT", "tool": "nuclei", "name": "CVE-2018-7600", "result": "ok" },
  {
    "track": "PT",
    "tool": "info-disclosure probe",
    "name": "/core/install.php",
    "result": "problem",
    "detail": "reachable (200)"
  },
  {
    "track": "VA",
    "tool": "trivy",
    "name": "CVE-2026-44486",
    "result": "problem",
    "detail": "axios 1.15.0"
  }
]
```

| Field    | Type   | Required | Notes                                                              |
| -------- | ------ | -------- | ------------------------------------------------------------------ |
| `track`  | enum   | yes      | `VA` \| `PT`.                                                      |
| `tool`   | string | yes      | Groups the list (e.g. `nuclei`, `info-disclosure probe`, `trivy`). |
| `name`   | string | yes      | The individual check (template id, URL path, CVE, rule).           |
| `result` | enum   | yes      | `ok` (green) \| `problem` (red).                                   |
| `detail` | string | no       | Short context, shown after the name.                               |

`nuclei-scan.sh` writes a `checklist.json` automatically (one entry per selected
template, `problem` if it matched). For a combined report, append the PT probe
results and the VA findings (each real finding a `problem`, each clean scanner an
`ok`) into the same array.

## Validation

`build-report.py` enforces:

- Each file parses as a JSON array.
- Every finding has the required fields and a valid `severity`/`track`.
- `track` matches the file it came from (`--va` file must contain only `VA`).

On a validation error the script exits non-zero and names the offending finding
`id`, so a malformed track output fails loudly instead of producing a silently
incomplete report.
