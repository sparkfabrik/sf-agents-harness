---
name: code-security-audit
description: 'Multi-stack code security audit workflow for web applications and APIs. Use when the user wants to perform a security audit, find vulnerabilities, run security scans, check for XSS/CSRF/injection issues, harden an application, or investigate a malicious npm, PyPI, or Packagist dependency / supply-chain compromise. Also use when the user mentions "code security", "security review", "pen test", "vulnerability scan", "OWASP", "semgrep", "trivy", "gosec", "govulncheck", "phpcs", "phpstan", "psalm", "drupal-check", "composer audit", "npm audit", "pip-audit", "malicious package", "compromised dependency", "supply chain attack", "typosquatting", "lockfile IOC", "install script malware", "PyPI compromise", or "Packagist compromise".'
---

# Code Security Audit Skill

Structured multi-phase security audit for web applications and APIs. The skill
discovers the project's stacks and existing tools, augments coverage with
Docker-based scanners when needed, and uses the LLM to perform a deep manual
review guided by scan findings.

**Open-source tools only** -- no commercial licenses required.

Known malicious-package incidents need extra handling. Advisory-driven scanners
such as `npm audit`, `trivy`, `grype`, and `pip-audit` are still useful, but
they can miss fresh malicious publishes until the ecosystem catches up. When
the user is asking about a named package compromise or supply-chain campaign,
pair the normal audit with exact-version and IOC-based triage.

## Before you start

1. Ask the user whether they want a **full audit** (all phases) or a
   **scan-only** run (Phases 1--4 only, skip Phase 5 manual review). If the
   request is about a known malicious package incident, ask whether they want a
   focused incident triage only or that triage folded into the full/scan-only
   audit.
2. Agree on **scope boundaries** upfront: application code, infrastructure
   config, CI/CD, dependencies, or all.
3. For package-compromise investigations, explicitly confirm whether the scope
   is repo-only or also includes developer-environment artifacts such as
   repo-local or home-directory `.claude/` and `.vscode/` paths.

## Phase 1 -- Discovery

Before running any scanners, read the project to understand what stacks are
present and what tools are already available.

### Stack detection

Detect which language stacks are present by searching the repository, not just
the root. Monorepos and nested apps are common. Ignore dependency and build
directories such as `node_modules/`, `vendor/`, `.git/`, `dist/`, `build/`,
`coverage/`, and `.code-security-audit/`. Record the path of every manifest you
find:

| Config file                                      | Detected stack |
| ------------------------------------------------ | -------------- |
| `composer.json`                                  | PHP            |
| `go.mod`                                         | Go             |
| `package.json`                                   | Node.js        |
| `pyproject.toml`, `requirements.txt`, `setup.py` | Python         |
| `*.tf`, `Dockerfile`, `docker-compose.yml`       | IaC            |

Detect Drupal as a sub-type of PHP when a discovered `composer.json` contains
`drupal/core` or `drupal/core-recommended` as a dependency.

A project may contain multiple stacks (e.g. PHP backend + Node.js frontend).
Detect all of them and note which paths belong to each stack.

### Tool configuration discovery

Check for existing tool configuration files across the repository to determine
which security-relevant tools the project already has set up:

| Config file                           | Tool available                        |
| ------------------------------------- | ------------------------------------- |
| `phpstan.neon` or `phpstan.neon.dist` | phpstan                               |
| `.phpcs.xml` or `phpcs.xml.dist`      | phpcs                                 |
| `psalm.xml` or `psalm.xml.dist`       | psalm                                 |
| `grumphp.yml`                         | grumphp (orchestrates multiple tools) |
| `.eslintrc*` or `eslint.config.*`     | eslint                                |
| `.golangci.yml`                       | golangci-lint                         |

When a tool is found with project configuration, record it as available for
Phase 3 together with the path where it applies. Use the project's own
configuration when running it.

### Tool invocation method

Ask the user how project-native tools should be invoked. Do not attempt to
auto-detect the execution environment -- projects use a wide range of setups.

If the repository has multiple app roots with different wrappers, collect one
invocation method per relevant root instead of assuming one global prefix.

Present examples to guide the user:

- Directly: `phpcs .`
- Via vendor binaries: `./vendor/bin/phpcs .`
- Via a wrapper: `ddev exec phpcs .`, `lando phpcs .`, `docker compose exec php phpcs .`
- Via a task runner: `make phpcs`, `task phpcs`

The user's answer becomes the invocation prefix for all Phase 3 tool runs.

### CI config scanning

Read CI configuration files (`.gitlab-ci.yml`, `.github/workflows/*.yml`) to
identify security scanning already performed in CI pipelines.

Report CI-discovered scanners as informational context. Do **not** skip
scanning based on CI configuration alone -- CI results are typically not
available locally.

### Discovery report

After completing detection, present a structured report to the user:

```markdown
## Discovery Report

**Detected stacks**:

- PHP/Drupal at `src/drupal/composer.json`
- Node.js at `src/storybook/package.json`

**Available tools**:

- phpcs (via `src/drupal/.phpcs.xml`)
- phpstan (via `src/drupal/phpstan.neon`)

**CI scanning**: semgrep (GitLab CI), trivy (GitLab CI)

**How should I run project-native tools?**
Examples: directly, ./vendor/bin/, ddev exec, make, docker compose exec ...
If different app roots need different wrappers, list one per path.

> [user response]
```

Wait for the user to confirm the report and provide the tool invocation method
before proceeding to Phase 2.

### Known-incident IOC triage

When the user is asking whether the repository or developer environment is
affected by a named malicious package or supply-chain campaign, do a focused
IOC sweep after the discovery report is confirmed and before you treat generic
scanner results as sufficient. Read `references/supply-chain-security.md`
before running this path.

1. If the organization already has a maintained incident scanner or playbook,
   prefer running it and report it as an additional scanner in the summary. Do
   not vendor that external script into this skill or rewrite it blindly.
2. Sweep every manifest and lockfile path found during discovery (root and
   nested workspaces), not only the repository root.
3. Check for exact compromised package names and versions in lockfiles and
   installed dependency trees when present.
4. Review manifests for suspicious Git or URL dependencies, unexpected
   `optionalDependencies`, override blocks, and install-time lifecycle hooks
   such as `preinstall`, `install`, `postinstall`, and `prepare`.
5. Check repo-local `.claude/` and `.vscode/` persistence paths by default.
   Here, repo-local means paths physically inside the current repository root;
   do not follow symlinks or mounted paths outside that root. Only scan
   home-directory equivalents if that scope was explicitly approved.
6. Review CI workflows and publishing pipelines for the trust-boundary patterns
   used by the campaign, such as `pull_request_target`, overly broad
   `id-token: write`, cache poisoning risk, or unpinned third-party actions.
7. Review git history for suspicious authors, unexpected dependency-only bumps,
   IOC filenames, or workflow changes that line up with the incident.
8. Treat IOC triage as complementary to advisory-based scanners. A clean
   `npm audit`, `trivy`, or `grype` result does not clear a named malicious
   publish on its own.

## Phase 2 -- Generate scan containers

Based on the discovery results, generate per-stack Dockerfiles and scan scripts.
Each detected stack gets its own container with only the relevant tools. A
separate "universal" container handles cross-cutting scanners.

First, check that Docker is available. If it is not:

1. Inform the user that Docker-augmented scanning (Phase 4) will be skipped.
2. List which tools will not be available.
3. Proceed directly to Phase 3 using only project-native tools.

### Base image selection

| Stack     | Base image             |
| --------- | ---------------------- |
| Universal | `python:3.12-slim`     |
| PHP       | `php:8.3-cli`          |
| Node.js   | `node:22-slim`         |
| Go        | `golang:1.22-bookworm` |
| Python    | `python:3.12-slim`     |

### Output directory structure

Write all generated files to `.code-security-audit/`:

```
.code-security-audit/
├── universal/
│   ├── Dockerfile
│   ├── scan.sh
│   └── output/
│       ├── manifest.json
│       └── <tool>.json ...
├── php/
│   ├── Dockerfile
│   ├── scan.sh
│   └── output/
│       ├── manifest.json
│       └── <tool>.json ...
└── node/          (if applicable)
    ├── Dockerfile
    ├── scan.sh
    └── output/
        ├── manifest.json
        └── <tool>.json ...
```

### Dockerfile generation

Generate a Dockerfile for each detected stack and for the universal container.
Use the templates in `references/dockerfile-templates.md` as a basis.

All tool versions are pinned in the templates. Binary downloads include SHA-256
checksum verification. Before generating Dockerfiles:

1. **Check the version table** in `references/dockerfile-templates.md`. Look at
   the "Last verified" date for each tool relevant to the detected stacks.
2. **If any tool is older than 90 days**, warn the user and offer to look up
   the current version via `curl -s https://api.github.com/repos/<owner>/<repo>/releases/latest | jq -r .tag_name`.
3. **If the user accepts a newer version**, update the version (and checksum
   for binary downloads) in the generated Dockerfile. Do NOT modify the
   template file itself -- the template serves as the known-good baseline.
4. **Record which versions were used** -- you will need this for the audit
   report (see "Tools and coverage" in the Final report section).

Each Dockerfile installs only the tools relevant to its stack (see tool matrix
below). The generated `scan.sh` runs each tool in sequence. Minimal readiness
checks are allowed (e.g. checking whether `vendor/` or `go.sum` exists before
running tools that need them, or detecting IaC files before running checkov),
but the script should not contain complex branching logic.

### scan.sh generation

Each scan script SHALL:

1. Run each tool with JSON output where supported.
2. Write output to `/output/<tool-name>.json`.
3. Continue to the next tool even if one fails (capture exit code).
4. Check dependency readiness before running tools that need it:
   - PHP: skip psalm and phpstan if `/src/vendor/` does not exist.
   - Node.js: skip tools requiring `node_modules/` if it does not exist.
   - Go: skip gosec/govulncheck if `go.sum` is missing.
5. Accept a `SKIP_TOOLS` environment variable (comma-separated tool names)
   to skip tools already run in Phase 3.
6. Write `/output/manifest.json` as its final step.

### manifest.json format

```json
{
  "stack": "php",
  "tools": [
    {
      "name": "composer-audit",
      "exitCode": 0,
      "outputFile": "composer-audit.json",
      "status": "success"
    },
    {
      "name": "psalm",
      "exitCode": null,
      "outputFile": null,
      "status": "skipped",
      "reason": "vendor/ not found -- run composer install first"
    },
    {
      "name": "phpcs",
      "exitCode": null,
      "outputFile": null,
      "status": "skipped",
      "reason": "already run in Phase 3"
    }
  ]
}
```

## Phase 3 -- Project-native scans

Run tools already configured in the project using the invocation method provided
by the user in Phase 1. This respects the project's own rulesets and exclusions.

For each tool discovered in Phase 1:

1. Run it with JSON output when available.
2. Capture findings.
3. Record which tools ran successfully -- these will be skipped in Phase 4.

Use the user-provided invocation prefix. For example, if the user said
`ddev exec`, run `ddev exec phpcs --report=json .` rather than `phpcs --report=json .`.

If no project-native tools were discovered, skip to Phase 4.

## Phase 4 -- Docker-augmented scans

Build and run the containers generated in Phase 2. These fill coverage gaps --
tools the project does not already have.

### Tool matrix

Pick scanners based on the detected stack. The universal container always runs.

| Tool                           | Container | Scope                                     | When to use                             |
| ------------------------------ | --------- | ----------------------------------------- | --------------------------------------- |
| **semgrep**                    | universal | SAST (multi-language)                     | Always                                  |
| **trivy**                      | universal | Dependency CVEs, FS, config               | Always -- runs `trivy fs .` on the repo |
| **gitleaks**                   | universal | Secret detection in git history           | Always                                  |
| **grype**                      | universal | Dependency CVE matching                   | Always                                  |
| **syft**                       | universal | SBOM generation                           | Always                                  |
| **checkov**                    | universal | IaC misconfiguration                      | When IaC files detected                 |
| **composer audit**             | php       | PHP dependency CVEs                       | PHP projects                            |
| **phpcs** (drupal/coder)       | php       | Drupal coding standards + security sniffs | PHP/Drupal projects                     |
| **psalm** (taint analysis)     | php       | Data flow / taint tracking                | PHP projects (needs vendor/)            |
| **phpstan**                    | php       | Static analysis with security extensions  | PHP projects (needs vendor/)            |
| **drupal-check**               | php       | Deprecated API + Drupal-specific checks   | Drupal projects                         |
| **local-php-security-checker** | php       | Symfony advisory DB                       | PHP projects                            |
| **npm audit**                  | --        | Node.js dependency CVEs                   | Node.js (runs directly, ships with npm) |
| **retire.js**                  | node      | Known-vulnerable JS libraries             | Node.js projects                        |
| **gosec**                      | go        | Go-specific SAST                          | Go projects                             |
| **govulncheck**                | go        | Go dependency CVEs                        | Go projects                             |
| **bandit**                     | python    | Python SAST                               | Python projects                         |
| **pip-audit**                  | python    | Python dependency CVEs                    | Python projects                         |

Known malicious-package incidents need more than advisory feeds. `npm audit`,
`trivy`, `grype`, and similar tools may stay clean for hours or days after a
malicious publish. For named incidents, always combine the tool matrix with the
IOC triage workflow above.

### Running the containers

```bash
# Build
docker build -t code-security-audit-universal .code-security-audit/universal/
docker build -t code-security-audit-php .code-security-audit/php/

# Run (can be parallel for different stacks)
docker run --rm \
  -v "$(pwd)":/src:ro \
  -v "$(pwd)"/.code-security-audit/universal/output:/output \
  code-security-audit-universal

docker run --rm \
  -v "$(pwd)":/src:ro \
  -v "$(pwd)"/.code-security-audit/php/output:/output \
  -e SKIP_TOOLS=phpcs,phpstan \
  code-security-audit-php
```

Pass `SKIP_TOOLS` with tools already run successfully in Phase 3.

Containers for different stacks can be built and run in parallel.

### Running the scans (command reference)

```bash
# Universal
semgrep scan --config auto --json .
trivy fs --format json --severity HIGH,CRITICAL .
gitleaks detect --source /src --report-format json --report-path /output/gitleaks.json
grype dir:/src -o json
syft dir:/src -o json
checkov -d /src -o json

# PHP / Drupal
composer audit --format=json
phpcs --standard=Drupal,DrupalPractice --report=json .
psalm --taint-analysis --output-format=json
phpstan analyse --error-format=json
drupal-check --no-progress .
local-php-security-checker --format=json

# Node.js
npm audit --json
retire --outputformat json --outputpath /output/retire.json

# Go
gosec -fmt json ./...
govulncheck -json ./...

# Python
bandit -r . -f json
pip-audit --format=json
```

### Handling missing tools

Tools are provided by the generated Docker containers. If Docker is not
available, the skill falls back to Phase 3 results only and Phase 5 manual
review. The audit still happens -- just with less automated coverage.

When Docker is available but a tool fails inside the container, the
manifest.json records the failure. The skill reports it to the user and
continues with available results.

Never silently skip a scanner -- the user must see what ran, what was skipped,
and why (via the manifest).

### Scan summary format

After all scans complete (Phase 3 + Phase 4), consolidate results from all
sources into a unified summary. Include the source (project-native or Docker
container) for each scanner.

```markdown
## Scan Results Summary

| Scanner | Source | Findings | Critical | High | Medium | Low |
| ------- | ------ | -------- | -------- | ---- | ------ | --- |
| phpcs   | native | 3        | 0        | 1    | 2      | 0   |
| semgrep | docker | 5        | 1        | 2    | 1      | 1   |
| trivy   | docker | 2        | 0        | 0    | 1      | 1   |
| psalm   | docker | 1        | 0        | 1    | 0      | 0   |
| ...     |        |          |          |      |        |     |

### Skipped tools

| Tool    | Reason                                    |
| ------- | ----------------------------------------- |
| phpstan | vendor/ not found -- run composer install |
| gosec   | not applicable (no Go stack detected)     |

### Critical / High findings

1. **[semgrep] SQL injection in buildQuery** -- `src/Repository/NodeRepository.php:42`
2. **[psalm] Tainted input in render array** -- `src/Controller/PageController.php:87`
   ...
```

If you ran an organization-maintained incident scanner or a targeted IOC sweep,
include it in the summary with a clear source such as `custom`, `native-script`,
or `manual-ioc`.

Present this summary to the user and ask whether to proceed to Phase 5.

## Phase 5 -- Manual deep review

Use scan findings as a starting point, then systematically review the
codebase for vulnerabilities that automated tools miss.

### Review checklist

Work through each category. For every finding, record the file, line number,
severity, and a concrete fix recommendation.

#### 5.1 Input validation and injection

- [ ] SQL injection (parameterized queries everywhere?)
- [ ] Command injection (shell exec with user input?)
- [ ] Path traversal (file operations with user-controlled paths?)
- [ ] Template injection (server-side template rendering with user input?)
- [ ] LDAP / XML / XPath injection (if applicable)

#### 5.2 Cross-site scripting (XSS)

- [ ] Reflected XSS (user input echoed in HTML without escaping?)
- [ ] Stored XSS (database content rendered without escaping?)
- [ ] DOM-based XSS (JS reads from URL/hash/referrer and writes to DOM?)
- [ ] Content-Security-Policy header present and restrictive?

#### 5.3 Authentication and session management

- [ ] Session tokens cryptographically random and sufficient length?
- [ ] Session cookies have `HttpOnly`, `Secure`, `SameSite` attributes?
- [ ] Session expiry and rotation on privilege change?
- [ ] Brute-force protection (rate limiting, account lockout)?
- [ ] OAuth flows validated (state parameter, redirect URI validation)?

#### 5.4 Authorization

- [ ] Broken access control (can user A access user B's data)?
- [ ] IDOR (sequential IDs exposed without ownership check)?
- [ ] Missing authorization on API endpoints?
- [ ] Privilege escalation (regular user accessing admin endpoints)?

#### 5.5 CSRF and request integrity

- [ ] CSRF tokens on all state-changing requests?
- [ ] `SameSite` cookie attribute set?
- [ ] Origin/Referer validation on sensitive endpoints?

#### 5.6 Sensitive data exposure

- [ ] Secrets in source code or config files?
- [ ] Credentials logged or exposed in error messages?
- [ ] Sensitive data in URLs (query parameters)?
- [ ] Proper TLS configuration (HSTS header)?
- [ ] PII exposure in API responses?

#### 5.7 Security headers and configuration

- [ ] `Content-Security-Policy` (restrictive, no `unsafe-inline` if possible)
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options` or CSP `frame-ancestors`
- [ ] `Strict-Transport-Security` (HSTS)
- [ ] `Referrer-Policy`
- [ ] `Permissions-Policy`
- [ ] Server version headers suppressed?

#### 5.8 Dependency and supply chain

- [ ] Known CVEs in dependencies (from scan results)?
- [ ] Exact-version IOC matches for named incidents or campaigns?
- [ ] Nested manifests and workspaces audited, not just repo root?
- [ ] Git/URL dependencies, `optionalDependencies`, `resolutions`, or `overrides` suspicious?
- [ ] Install-time lifecycle scripts (`preinstall`, `install`, `postinstall`, `prepare`) safe and expected?
- [ ] Lock file present, committed, and integrity-verified?
- [ ] Repo-local or approved home-directory `.claude/` / `.vscode/` persistence artifacts?
- [ ] Unused dependencies that expand attack surface?

#### 5.9 Error handling and logging

- [ ] Stack traces or internal details leaked to client?
- [ ] Consistent error responses (no information disclosure)?
- [ ] Security events logged (failed auth, authz violations)?
- [ ] No sensitive data in logs?

#### 5.10 Server and runtime hardening

- [ ] Read/write timeouts on HTTP server?
- [ ] Request body size limits?
- [ ] Rate limiting on authentication endpoints?
- [ ] Graceful shutdown handling?
- [ ] File upload validation (type, size, storage location)?

### Deep review process

For each checklist category:

1. **Read the relevant code** -- use grep/glob to find all instances.
2. **Cross-reference with scan findings** -- automated tools may have already
   flagged related issues.
3. **Record each finding** with:
   - **Location**: `file:line`
   - **Severity**: Critical / High / Medium / Low / Info
   - **Description**: What the vulnerability is
   - **Proof of concept**: How it could be exploited
   - **Fix recommendation**: Concrete code change

### Severity classification

| Severity     | Definition                                                                          |
| ------------ | ----------------------------------------------------------------------------------- |
| **Critical** | Remote code execution, authentication bypass, SQL injection with data exfiltration  |
| **High**     | Stored XSS, CSRF on critical actions, authorization bypass, sensitive data exposure |
| **Medium**   | Reflected XSS, missing security headers, information disclosure                     |
| **Low**      | Missing best practices, verbose errors in non-production, minor hardening gaps      |
| **Info**     | Recommendations and defense-in-depth improvements                                   |

## Final report

After Phase 5 (or after Phase 4 for scan-only runs), write a consolidated
report to `.code-security-audit/report.md`. This file is the primary deliverable of
the audit -- it must be self-contained, readable by someone who was not present
during the audit, and presentable to technical leads, clients, or auditors.

**Always write this file. Do not just print the report in the chat.**

Use the following structure:

```markdown
# Security Audit Report

|                     |                                                               |
| ------------------- | ------------------------------------------------------------- |
| **Project**         | <project name>                                                |
| **Date**            | <YYYY-MM-DD>                                                  |
| **Scope**           | <what was audited: application code, dependencies, IaC, etc.> |
| **Stacks detected** | <e.g. PHP/Drupal 10, Node.js 22>                              |
| **Audit type**      | Full (scan + manual review) / Scan-only                       |

## Executive summary

<2-4 sentences: overall security posture, number of findings by severity,
most critical risks, and a clear recommendation (e.g. "address the 2 critical
findings before the next release").>

## Methodology

This audit followed a structured multi-phase approach:

1. **Discovery** -- detected project stacks and existing tool configurations.
2. **Incident triage** -- for known malicious package campaigns, added a
   targeted IOC sweep of manifests, lockfiles, CI workflows, persistence paths,
   and git history. _(omit when not applicable)_
3. **Container generation** -- built per-stack Docker containers with
   security scanners.
4. **Project-native scans** -- ran tools already configured in the project.
5. **Docker-augmented scans** -- ran additional scanners via containers to
   fill coverage gaps.
6. **Manual review** -- LLM-guided deep review of the codebase using the
   OWASP-based checklist. _(omit if scan-only)_

## Tools and coverage

### Tools executed

| Tool    | Version | Source | Stack     | Status    |
| ------- | ------- | ------ | --------- | --------- |
| phpcs   | 3.7.2   | native | PHP       | completed |
| semgrep | 1.156.0 | docker | universal | completed |
| trivy   | 0.69.3  | docker | universal | completed |
| psalm   | 6.16.1  | docker | PHP       | completed |
| ...     |         |        |           |           |

### Tools skipped

| Tool    | Reason               |
| ------- | -------------------- |
| phpstan | vendor/ not found    |
| gosec   | no Go stack detected |

## Findings summary

| Severity  | Count  |
| --------- | ------ |
| Critical  | 0      |
| High      | 2      |
| Medium    | 5      |
| Low       | 3      |
| Info      | 4      |
| **Total** | **14** |

## Findings

### Finding 1: <title>

|              |                                             |
| ------------ | ------------------------------------------- |
| **Severity** | Critical / High / Medium / Low / Info       |
| **Location** | `path/to/file.php:42`                       |
| **Tool**     | <scanner that found it, or "manual review"> |
| **Category** | <e.g. SQL injection, XSS, access control>   |

**Description**

<What the vulnerability is. Be specific and reference the code.>

**Impact**

<What an attacker could achieve by exploiting this.>

**Evidence**

<Code snippet, scanner output, or proof of concept showing the issue.>

**Recommendation**

<Concrete fix with a code example where applicable.>

---

### Finding 2: <title>

...

_(Repeat for each finding. Order by severity -- Critical first, then High,
Medium, Low, Info.)_

## Checklist coverage

_(Include only for full audits, omit for scan-only runs.)_

Show each checklist category and its status:

| Category                                  | Status       | Notes                          |
| ----------------------------------------- | ------------ | ------------------------------ |
| 5.1 Input validation and injection        | Reviewed     | 2 findings                     |
| 5.2 Cross-site scripting (XSS)            | Reviewed     | 1 finding                      |
| 5.3 Authentication and session management | Reviewed     | No issues                      |
| 5.4 Authorization                         | Reviewed     | 1 finding                      |
| 5.5 CSRF and request integrity            | Reviewed     | No issues                      |
| 5.6 Sensitive data exposure               | Reviewed     | No issues                      |
| 5.7 Security headers and configuration    | Reviewed     | 3 findings                     |
| 5.8 Dependency and supply chain           | Reviewed     | From scan results + IOC triage |
| 5.9 Error handling and logging            | Reviewed     | 1 finding                      |
| 5.10 Server and runtime hardening         | Not reviewed | Out of scope                   |

## Recommendations

Prioritized list of next steps:

1. **Immediate** (Critical/High): <fix X, fix Y>
2. **Short-term** (Medium): <address A, address B>
3. **Ongoing** (Low/Info): <improve C, consider D>
```

After writing the report, tell the user the file path and show the executive
summary and findings summary table in the chat as a preview.

## Fixing vulnerabilities

After the report is written, ask the user whether they want to proceed with
fixes. If yes:

1. **Prioritize by severity** -- fix Critical and High first.
2. **One fix per commit** -- each vulnerability fix should be a separate,
   reviewable commit.
3. **Re-run affected scanners** after fixes to verify resolution.
4. **Update the report** -- mark fixed findings in `.code-security-audit/report.md`
   with a `**Status**: Fixed (<commit hash>)` line.

## Tips

- **Scope boundaries**: Agree with the user upfront on what's in scope
  (application code, infrastructure config, CI/CD, dependencies, or all).
- **False positives**: Automated tools produce false positives. Always verify
  findings manually before reporting them.
- **Named malicious package incidents**: Exact-version and IOC checks are
  mandatory. Advisory feeds often lag behind fresh malicious publishes.
- **Monorepos and workspaces**: Scan every discovered manifest and lockfile,
  not just the repository root.
- **Context matters**: A finding in a public-facing production app is more
  severe than the same finding in an internal tool with network restrictions.
- **Defense in depth**: Even if one control compensates for a weakness,
  recommend fixing the underlying issue.
- **Incremental audits**: For large codebases, audit module by module rather
  than everything at once.

## Language-specific guides

For detailed vulnerability patterns and scanner configurations specific to a
language or framework, see the references:

- Go applications: `references/go-security.md`
- Node.js / frontend: `references/nodejs-security.md`
- PHP / Drupal: `references/php-security.md`
- Supply-chain incident triage: `references/supply-chain-security.md`
- Dockerfile templates: `references/dockerfile-templates.md`
