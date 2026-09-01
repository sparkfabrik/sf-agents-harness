# Drupal Penetration Testing Runbook (Docker-based)

Internal procedure for assessing a Drupal site we own or are authorized to test. All tooling runs in Docker, no host installs. Output is structured (JSON/SARIF/HTML) so it can be archived and fed into CI.

> Last reviewed: June 2026. Tool versions and image names verified at that date.

---

## 0. Pre-engagement (mandatory)

Do not start until all of these are true:

1. **Written authorization** for the exact target scope (domains, IPs, subdomains).
1. **Target is staging**, not production, unless production testing is explicitly authorized and rate-limited. Active scans (ZAP full scan, sqlmap, nuclei fuzzing) generate load and can write/delete data.
1. **Backup taken** of DB and files before any active phase.
1. **Out-of-scope list** documented (third-party SSO, payment providers, shared infra, CDN origin).
1. **Maintenance window** agreed if testing touches production.

Record the authorized scope at the top of the engagement notes. Anything outside it is off-limits.

---

## 1. Prerequisites

- Docker Engine 24+ (or Podman with `docker` alias).
- Outbound network to the target.
- A working directory per engagement, e.g. `./engagement-<client>-<date>/`. All reports land here.

```bash
export TARGET="https://staging.example.com"
export WORKDIR="$(pwd)/engagement"
mkdir -p "$WORKDIR/reports"
```

Pin image tags for reproducibility. `latest` is acceptable for ad-hoc runs but pin before archiving results.

---

## 2. Phase 1: Recon and fingerprinting

Map the surface before touching anything Drupal-specific.

### nmap (ports and services)

```bash
docker run --rm -v "$WORKDIR/reports:/out" instrumentisto/nmap \
  -sV -sC -T4 -oA /out/nmap-$(date +%F) staging.example.com
```

### httpx (live hosts, tech, headers)

```bash
echo "$TARGET" | docker run --rm -i projectdiscovery/httpx:latest \
  -title -tech-detect -status-code -server -json -o /dev/stdout \
  > "$WORKDIR/reports/httpx.json"
```

### WhatWeb (technology fingerprint)

```bash
docker run --rm guidelacour/whatweb \
  whatweb -a 3 "$TARGET"
```

Goal of this phase: confirm it is Drupal, identify the web server, CDN/WAF in front (Varnish, Cloudflare, Cloud Armor), exposed ports, and TLS posture. WAF/CDN presence changes how the later phases behave.

---

## 3. Phase 2: Drupal enumeration

### droopescan (version and module/theme enumeration)

```bash
docker run --rm -v "$WORKDIR/reports:/out" \
  python:3.12-slim sh -c \
  "pip install -q droopescan && droopescan scan drupal -u $TARGET -t 16 --output json" \
  > "$WORKDIR/reports/droopescan.json"
```

> **Caveat.** droopescan (`SamJoan/droopescan`, PyPI 1.16.0) is reliable for fingerprinting and enumeration but its version-detection fingerprints are weak on Drupal 10/11. Treat the reported version as a hint, not ground truth, and confirm manually (CHANGELOG, composer metadata, `/core/CHANGELOG.txt` if exposed). Do not derive vulnerability conclusions from its version output alone.

Useful manual checks alongside it:

- `/CHANGELOG.txt`, `/core/CHANGELOG.txt` (often disabled, worth checking).
- `/user/login`, `/user/register` (registration policy, enumeration).
- `/admin` redirect behavior.
- `/jsonapi`, `/jsonapi/node/article` (JSON:API exposure).
- `/sites/default/files/` directory listing.
- `/web.config`, `.htaccess` leakage, `composer.json`/`composer.lock` exposure.

---

## 4. Phase 3: Template-based vulnerability scan (Nuclei)

Nuclei is the repeatable baseline. Ships Drupal and CVE templates, outputs JSON/SARIF, drops straight into CI.

> Use **v3.8.0 or later**. Earlier versions have two template-sandbox CVEs (GHSA-29rg-wmcw-hpf4, GHSA-jm34-66cf-qpvr) patched on 18 Apr 2026. Relevant if you ever run third-party template collections.

Persist the templates dir so updates are cached:

```bash
mkdir -p "$WORKDIR/nuclei-templates"

# 1. Update templates into the persisted volume
docker run --rm -v "$WORKDIR/nuclei-templates:/root/nuclei-templates" \
  projectdiscovery/nuclei:latest -update-templates

# 2. VERIFY templates actually landed before scanning. This gate is mandatory.
count=$(find "$WORKDIR/nuclei-templates" -name '*.yaml' | wc -l)
echo "nuclei templates: $count"
[ "$count" -gt 0 ] || { echo "FATAL: 0 templates installed -- do not trust the scan"; exit 1; }

# 3. Drupal-tagged + CVE scan, reusing the populated volume
docker run --rm \
  -v "$WORKDIR/nuclei-templates:/root/nuclei-templates" \
  -v "$WORKDIR/reports:/out" \
  projectdiscovery/nuclei:latest \
  -u "$TARGET" \
  -tags drupal,cve \
  -severity low,medium,high,critical \
  -rl 50 -timeout 10 -stats -disable-update-check \
  -je /out/nuclei.json \
  -se /out/nuclei.sarif
```

`-rl 50` rate-limits to 50 req/s. Lower it against production or behind a WAF. Drop `-tags` to run the full set, but expect noise.

> **Critical gotcha (verified the hard way).** If the template volume is empty,
> Nuclei prints `Templates loaded for current scan: 0`, finishes in milliseconds
> with `Matched: 0`, and exits 0. That looks identical to a clean result but is a
> **false negative** -- nothing was tested. Always run the update as a separate
> step, then assert the on-disk template count is non-zero (step 2) before
> scanning, and confirm `Templates loaded for current scan` is in the thousands
> (a `drupal,cve` run loads ~4000) in the scan's `-stats` output. A real run sends
> thousands of requests over minutes, not one in a millisecond. `-disable-update-check`
> on the scan keeps it from re-triggering a sync that can leave the dir half-populated.

### Bundled helper: `assets/nuclei-scan.sh`

The skill ships `assets/nuclei-scan.sh`, which wraps this whole flow (update +
verify count, scan, error capture) for any target. Usage:

```bash
# targeted Drupal pass -- the Drupal-tagged templates incl. all Drupal CVEs
TAGS=drupal nuclei-scan.sh https://target/

# full drupal,cve sweep against a remote, gated, or WAF-protected host
BASIC_AUTH='user:pass' MHE=0 RL=15 C=8 TIMEOUT=20 nuclei-scan.sh https://target/
```

What the wrapper handles, and why:

- **`TYPES=http` (default).** The input is a URL, so it runs only HTTP-protocol
  templates. `tcp`/`ssl`/network templates connect to service ports (FTP,
  message brokers, dashboards, ...) a web target does not expose, so they can
  only time out -- excluding them removes that error class with no loss of web
  coverage. Set `TYPES=""` to run every protocol.
- **`BASIC_AUTH=user:pass`.** Sends `Authorization: Basic` on every request and
  preflights it -- aborts if the gate still returns 401/403, so a gated host
  can't masquerade as a clean scan.
- **`MHE=0` (`-no-mhe`).** Never skip the host on errors. A slow or rate-limited
  host otherwise hits the default 30-error limit and is dropped mid-scan
  ("unresponsive permanently"), which reads as a false clean.
- **`https://`, not `http://`.** A host that serves only HTTPS makes port-80
  probes time out and then gets dropped; the wrapper warns on `http://` targets.
- Names the container and traps `INT`/`TERM`, so Ctrl+C actually stops the scan
  (a bare `docker run` keeps running under the daemon after Ctrl+C).

**Residual errors against a WAF or rate-limited edge are expected.** A WAF stalls
or drops attack-shaped requests, which Nuclei generates by design, so such a host
will show some `context deadline` / `EOF` errors. That is the edge working, not a
broken scan or missed coverage. Treat the error count as a coverage signal, not a
pass/fail gate; the targeted `TAGS=drupal` pass runs clean and is the
authoritative Drupal result.

---

## 5. Phase 4: Authenticated DAST (OWASP ZAP)

ZAP covers the dynamic, authenticated surface that template scanners miss (session handling, JSON:API/REST behind login, Form API callbacks).

> Image: `ghcr.io/zaproxy/zaproxy:stable`. The old `owasp/zap2docker-*` images are deprecated, do not use them.

### Quick baseline (unauthenticated, passive, safe to run anywhere)

```bash
docker run --rm -v "$WORKDIR/reports:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t "$TARGET" -r zap-baseline.html
```

### Full scan via Automation Framework (authenticated, active)

Define the plan as YAML so it is versioned and CI-runnable. Minimal `zap-plan.yaml`:

```yaml
env:
  contexts:
    - name: drupal
      urls:
        - "https://staging.example.com"
      includePaths:
        - "https://staging.example.com.*"
      authentication:
        method: form
        parameters:
          loginPageUrl: "https://staging.example.com/user/login"
          loginRequestUrl: "https://staging.example.com/user/login"
          loginRequestBody: "name={%username%}&pass={%password%}&form_id=user_login_form"
        verification:
          method: response
          loggedInRegex: "(/user/logout)"
          loggedOutRegex: "(/user/login)"
      users:
        - name: tester
          credentials:
            username: "TEST_USER"
            password: "TEST_PASS"
jobs:
  - type: spider
    parameters: { context: drupal, user: tester }
  - type: spiderAjax
    parameters: { context: drupal, user: tester }
  - type: activeScan
    parameters: { context: drupal, user: tester }
  - type: report
    parameters:
      template: traditional-html
      reportDir: /zap/wrk
      reportFile: zap-full-report
```

Run it:

```bash
docker run --rm -v "$WORKDIR:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -cmd -autorun /zap/wrk/zap-plan.yaml
```

Use a dedicated **test account with minimal real privileges**, never a live admin. The active scan submits forms and can mutate content.

`TEST_USER` / `TEST_PASS` in the plan above are placeholders. **Never commit real credentials.** Inject them at runtime from environment variables or a secrets manager (ZAP plan parameters support `${ENV_VAR}` substitution), and keep `zap-plan.yaml` free of literal secrets.

---

## 6. Phase 5: Targeted exploitation

Driven by what earlier phases surface. Do not run blindly.

### sqlmap (SQL injection)

Drupal core had a highly critical anonymous SQLi in May 2026 (SA-CORE-2026-004 / CVE-2026-9082, PostgreSQL-backed sites, exploited in the wild). Test any parameterized endpoint, views with arguments, JSON:API filters.

```bash
docker run --rm -v "$WORKDIR/reports:/out" \
  paoloo/sqlmap \
  -u "$TARGET/some/endpoint?id=1" \
  --batch --level 2 --risk 1 \
  --output-dir /out/sqlmap
```

Pass `--cookie` or `--headers` with a valid session for authenticated endpoints. Raise `--level`/`--risk` only with explicit authorization.

### ffuf (content and parameter discovery)

```bash
docker run --rm -v "$WORKDIR/reports:/out" \
  ghcr.io/ffuf/ffuf \
  -u "$TARGET/FUZZ" \
  -w /usr/share/seclists/Discovery/Web-Content/CMS/drupal.txt \
  -mc 200,301,302,403 \
  -o /out/ffuf.json -of json
```

(Mount a wordlist volume, e.g. SecLists, or bake it into a custom image.)

---

## 7. Drupal-specific hotspots to check manually

Template scanners do not cover application logic. Verify these by hand:

- **JSON:API / REST**: exposed read/write endpoints, permission leakage on `/jsonapi/*`, unauthenticated entity enumeration.
- **Views**: contextual filters and arguments reachable by anonymous users, exposed admin views.
- **Form API**: AJAX callbacks (`/system/ajax`), `#access` bypasses, callback validation.
- **File handling**: upload endpoints, private vs public file scheme, `Cache-Control: public` on files that should be uncacheable (see SA-CORE-2025-008 class of issue).
- **Contrib modules**: cross-check installed contrib against SA-CONTRIB advisories. Recent examples include SAML SSO auth bypass and several XSS issues.
- **Cache poisoning**: HTTP header override behavior, Varnish/CDN caching of authenticated responses.
- **Twig**: who can edit templates, sandbox escape exposure (coordinated Symfony/Twig advisories shipped with SA-CORE-2026-004).

Keep core patched: highly critical Drupal advisories are routinely weaponized within hours of release.

---

## 8. CI integration (continuous regression)

Once the manual assessment is done, the repeatable parts (Nuclei + ZAP baseline) should run on a schedule against staging. Example `docker-compose.yml` for a scheduled runner or a CI job:

```yaml
services:
  nuclei:
    image: projectdiscovery/nuclei:latest
    volumes:
      - ./nuclei-templates:/root/nuclei-templates
      - ./reports:/out
    command: >
      -u ${TARGET}
      -tags drupal,cve
      -severity high,critical
      -rl 50
      -je /out/nuclei-ci.json
      -se /out/nuclei-ci.sarif

  zap-baseline:
    image: ghcr.io/zaproxy/zaproxy:stable
    volumes:
      - ./reports:/zap/wrk/:rw
    command: zap-baseline.py -t ${TARGET} -r zap-ci.html
```

In CI:

- Fail the pipeline on `high`/`critical` Nuclei findings (gate on SARIF severity).
- Upload SARIF to the code-scanning surface (GitHub/GitLab) so findings are tracked.
- Run Nuclei `-update-templates` as a pre-step so each run picks up new CVE coverage.
- Schedule nightly or weekly against staging, not on every commit (active scans are slow).

Nuclei also ships a Helm chart with a CronJob if we want this on the GKE platform instead of a CI runner.

---

## 9. Deliverables

Per engagement, collect in `reports/`:

- `nmap-*`, `httpx.json`, `whatweb` output (recon).
- `droopescan.json` (enumeration, with version caveat noted).
- `nuclei.json` + `nuclei.sarif` (template findings).
- `zap-baseline.html` and/or `zap-full-report.html` (DAST).
- `sqlmap/`, `ffuf.json` (targeted, if run).

Each finding gets: severity, affected URL/parameter, reproduction, CWE/CVE reference, remediation, and the patched Drupal/contrib version where applicable. Verify before reporting: active scanners produce false positives.

---

## Tool reference

| Tool       | Image                                        | Role                                               |
| ---------- | -------------------------------------------- | -------------------------------------------------- |
| nmap       | `instrumentisto/nmap`                        | Port/service recon                                 |
| httpx      | `projectdiscovery/httpx:latest`              | HTTP probing, tech detect                          |
| WhatWeb    | `guidelacour/whatweb`                        | Tech fingerprint                                   |
| droopescan | `python:3.12-slim` + pip                     | Drupal enumeration (version detect weak on D10/11) |
| Nuclei     | `projectdiscovery/nuclei:latest` (>= v3.8.0) | Template/CVE scan, CI baseline                     |
| OWASP ZAP  | `ghcr.io/zaproxy/zaproxy:stable`             | Authenticated DAST                                 |
| sqlmap     | `paoloo/sqlmap`                              | SQLi                                               |
| ffuf       | `ghcr.io/ffuf/ffuf`                          | Content/param fuzzing                              |
