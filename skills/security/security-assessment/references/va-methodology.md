# VA methodology -- scanners and review

The VA engine, inlined. Open-source tools only. Drives the discovery, scanning,
and manual review that produce `va-findings.json`. Read `va-track.md` first for
the track contract, scan scoping (skip data dumps, `.gitignore` handling), and
finding-mapping rules.

## 1. Discovery

Read config files in the project root to detect stacks:

| Config file                                      | Stack        |
| ------------------------------------------------ | ------------ |
| `composer.json` (with `drupal/core*`)            | PHP / Drupal |
| `composer.json`                                  | PHP          |
| `go.mod`                                         | Go           |
| `package.json`                                   | Node.js      |
| `pyproject.toml`, `requirements.txt`, `setup.py` | Python       |
| `*.tf`, `Dockerfile`, `docker-compose.yml`       | IaC          |

Detect all stacks present (a project may be multi-stack). Note existing tool
configs (`phpstan.neon`, `.phpcs.xml`, `psalm.xml`, `.eslintrc*`,
`.golangci.yml`) and reuse the project's own rulesets when running those tools.

Ask the user how project-native tools are invoked (direct, `./vendor/bin/`,
`ddev exec`, `docker compose exec`, `make`). That prefix applies to native runs.

Read CI config (`.gitlab-ci.yml`, `.github/workflows/*.yml`) to note scanning
already in the pipeline -- informational; do not skip local scans because CI
runs them.

## 2. Scan containers (Docker-augmented)

If Docker is unavailable, skip this and run only project-native tools, then the
manual review. Otherwise generate one container per stack plus a universal one,
using `references/dockerfile-templates.md` (versions pinned, checksums verified;
check the "Last verified" dates and offer to bump anything older than 90 days).

Each `scan.sh`: run every tool with JSON output, write `/output/<tool>.json`,
continue on failure (capture exit code), skip tools whose deps are missing
(no `vendor/`, `node_modules/`, `go.sum`), accept `SKIP_TOOLS` for tools already
run natively, and write `/output/manifest.json` last. Never silently skip a
scanner -- the manifest records what ran, what was skipped, and why.

## 3. Tool matrix

| Tool                          | Stack      | Scope                                |
| ----------------------------- | ---------- | ------------------------------------ |
| semgrep                       | universal  | SAST (multi-language)                |
| trivy                         | universal  | dependency CVEs, FS, config, secrets |
| gitleaks                      | universal  | secrets in git history               |
| grype / syft                  | universal  | CVE matching / SBOM                  |
| checkov                       | universal  | IaC misconfiguration                 |
| composer audit                | PHP        | dependency CVEs                      |
| phpcs (Drupal,DrupalPractice) | PHP/Drupal | standards + security sniffs          |
| psalm `--taint-analysis`      | PHP        | data-flow / taint                    |
| phpstan                       | PHP        | static analysis                      |
| drupal-check                  | Drupal     | deprecated API + Drupal checks       |
| npm audit / retire.js         | Node.js    | dependency CVEs / known-vuln libs    |
| gosec / govulncheck           | Go         | SAST / dependency CVEs               |
| bandit / pip-audit            | Python     | SAST / dependency CVEs               |

Command reference and per-language patterns: `references/php-security.md`,
`references/go-security.md`, `references/nodejs-security.md`. Apply the trivy
invocation in `va-track.md` (skip data dumps, cached ghcr DB).

## 4. Manual review

Scan findings are the starting point; then review by hand for what tools miss.
For each finding record `file:line`, severity, and a concrete fix. Checklist:

- **Injection** -- SQL, command, path traversal, template, LDAP/XML/XPath.
- **XSS** -- reflected, stored, DOM-based; CSP present and restrictive?
- **AuthN / session** -- token entropy, cookie flags (`HttpOnly`/`Secure`/`SameSite`), expiry/rotation, brute-force protection, OAuth state/redirect validation.
- **AuthZ** -- broken access control, IDOR, missing API authz, privilege escalation.
- **CSRF** -- tokens on state-changing requests, `SameSite`, origin checks.
- **Sensitive data** -- secrets in code, credentials in logs/errors, data in URLs, TLS/HSTS, PII in responses.
- **Security headers** -- CSP, `X-Content-Type-Options`, frame-ancestors, HSTS, `Referrer-Policy`, `Permissions-Policy`, server version suppression.
- **Dependencies** -- known CVEs (from scans), pinned versions, lockfile committed.
- **Error handling / logging** -- stack-trace leakage, info disclosure, security events logged, no secrets in logs.
- **Runtime hardening** -- timeouts, body-size limits, rate limiting, upload validation.

## Severity

Use the shared scale in `SKILL.md`. A scanner's own severity is a hint:
downgrade noise (e.g. a CVE in a dev-only dependency) and say why in the
finding's `description`. Verify findings before reporting -- automated tools
produce false positives.
