# VA track -- Vulnerability Assessment

Breadth-first, non-intrusive assessment of the **codebase**. No live target is
touched. The goal is to enumerate everything that _might_ be vulnerable, so the
PT track can confirm what _is_ exploitable.

## Engine

The full scanning and review workflow is in `references/va-methodology.md`
(discovery, Docker scan containers, the scanner tool matrix, and the manual
review checklist), with per-language depth in `references/php-security.md`,
`go-security.md`, `nodejs-security.md`, and `dockerfile-templates.md`. Open-source
tools only. The track contract (below) is what matters: however the scans run,
the output is `va-findings.json` plus raw artifacts.

## Scan scope and tooling

Real Drupal projects break naive scans in two ways. Handle both, or the VA
result is either incomplete or all noise.

### 1. Large data artifacts stall the scanner

Multi-gigabyte SQL dumps, media, and fixtures (`seed/seed.sql`, `dump-*.sql`,
`*.sql.gz`) make trivy's file walker time out before it reaches any code. They
are never security-relevant. Skip them, run with a cache volume so the
vulnerability DB downloads once, raise the timeout, and pull the DB from the
ghcr repo (the default `mirror.gcr.io` is frequently throttled to a crawl):

```bash
docker run --rm \
  -v "$CODE":/src:ro -v "$OUT":/out -v "$CACHE":/root/.cache/trivy \
  aquasec/trivy:latest --timeout 15m \
  fs --scanners vuln,secret,misconfig --severity MEDIUM,HIGH,CRITICAL \
  --db-repository ghcr.io/aquasecurity/trivy-db:2 \
  --skip-files "**/*.sql,**/*.sql.gz,**/dump*.sql" \
  --skip-dirs "**/seed,**/node_modules,**/.git" \
  --format json -o /out/trivy.json /src
```

### 2. `.gitignore` is a signal, not a filter

Gitignored files are often local-only dirt (database dumps, caches, build
scratch) and safe to skip. But a gitignored **dependency manifest is not dirt**:
front-end packages (a theme's `package-lock.json`, vendored JS) compile into
built assets that ship to production even when the lockfile itself is gitignored.

Do **not** drop a dependency CVE just because its manifest is gitignored. Use
`.gitignore` only to skip data and cache artifacts. Keep every dependency
finding and flag it for human triage: _does this library end up in the deployed
bundle?_ When in doubt, treat it as in-scope.

To separate committed dependencies from local build inputs, also scan the
git-tracked tree and compare:

```bash
git -C "$REPO" archive HEAD <subpath> | tar -x -C "$CLEAN"   # tracked files only
# scan $CLEAN with the same trivy command; diff its findings against the full scan
```

Report both views, labelled: which CVEs are in committed manifests
(`composer.lock`) versus in built-but-gitignored front-end deps.

## Track contract

When VA runs, it MUST produce, under `<engagement-dir>/va/`:

1. `va-findings.json` -- every finding normalized to the schema in
   `findings-schema.md`, with `"track": "VA"`. Map each scanner finding and each
   manual-review finding to one entry.
2. `artifacts/` -- the raw scanner outputs (`semgrep.json`, `trivy.json`,
   `gitleaks.json`, `psalm.json`, etc.). Reference these files from each
   finding's `artifacts` array.

## Mapping scanner output to findings

- **Deduplicate** across scanners. semgrep, psalm, and the manual review often
  flag the same injection; merge into one finding and list the tools in
  `evidence`.
- **`location`** is `file:line` (e.g. `src/Repository/NodeRepository.php:42`).
- **`tool`** is the scanner name, or `manual review` for findings only a human
  caught.
- **CVEs** from trivy/grype/composer-audit/govulncheck go in `cve`, with the
  affected package and fixed version in `recommendation`.
- **Secrets** from gitleaks/trivy are `critical` only if a real credential is
  committed to version control. A flagged key may be fetched at build time and
  never committed (e.g. an SSO SP private key downloaded during the image
  build). Confirm with `git check-ignore` and `git log` before reporting; a
  build-time-fetched key not in VCS is a false positive, not a finding.
  Placeholders (`.env.example`) are `info`.
- **Severity** follows the shared scale in SKILL.md. A scanner's own severity is
  a hint; downgrade noise (e.g. a CVE in a dev-only dependency) and explain why
  in `description`.

## Verification

VA findings come from static analysis and carry false positives. Spot-check the
critical and high findings by reading the flagged code before they land in
`va-findings.json`. Note "confirmed by code read" or "scanner-reported, not yet
confirmed" in `evidence`.

## Boundaries

- VA does **not** send traffic to a running target -- that is the PT track.
- VA does **not** require authorization beyond access to the source code.
- A VA-only engagement is valid: pass only `--va` to `build-report.py`.
