# Dockerfile Templates

Template Dockerfiles for each stack. The skill uses these as a basis when
generating per-stack containers during Phase 2.

Each template installs the tools listed in the SKILL.md tool matrix for that
stack. **All tool versions are pinned.** Binary downloads are verified with
SHA-256 checksums. Package-manager installs (pip, npm, composer, go install)
use exact version constraints -- the package manager verifies integrity via its
own checksums/hashes.

> **Staleness**: The versions below were verified on the date shown. When
> generating Dockerfiles, check whether any tool is more than 90 days old. If
> so, warn the user and offer to look up the latest version via the GitHub
> Releases API before proceeding. See the staleness check instructions in
> SKILL.md Phase 2.

## Pinned versions

<!-- When updating a version: change the version, update the SHA-256 where
     applicable, and set "Last verified" to today's date. -->

| Tool                       | Version | Install method  | SHA-256 (linux/amd64) | Last verified |
| -------------------------- | ------- | --------------- | --------------------- | ------------- |
| semgrep                    | 1.156.0 | pip             | --                    | 2026-03-31    |
| trivy                      | 0.69.3  | binary tarball  | `1816b632dfe52986...` | 2026-03-31    |
| gitleaks                   | 8.30.1  | binary tarball  | `551f6fc83ea457d6...` | 2026-03-31    |
| grype                      | 0.110.0 | binary tarball  | `aaa98d27d2d7efd9...` | 2026-03-31    |
| syft                       | 1.42.3  | binary tarball  | `0d6be741479eddd2...` | 2026-03-31    |
| checkov                    | 3.2.513 | pip             | --                    | 2026-03-31    |
| phpcs                      | 3.7.2   | composer        | --                    | 2026-03-31    |
| drupal/coder               | 7.2.2   | composer        | --                    | 2026-03-31    |
| psalm                      | 6.16.1  | composer        | --                    | 2026-03-31    |
| phpstan                    | 2.1.45  | composer        | --                    | 2026-03-31    |
| drupal-check               | 1.5.0   | composer        | --                    | 2026-03-31    |
| local-php-security-checker | 2.1.3   | binary download | `db03c8c180692408...` | 2026-03-31    |
| retire.js                  | 5.4.2   | npm             | --                    | 2026-03-31    |
| gosec                      | 2.25.0  | binary tarball  | `ca099f42e37bc8f9...` | 2026-03-31    |
| govulncheck                | 1.1.4   | go install      | --                    | 2026-03-31    |
| bandit                     | 1.9.4   | pip             | --                    | 2026-03-31    |
| pip-audit                  | 2.10.0  | pip             | --                    | 2026-03-31    |

Full SHA-256 checksums (for copy-paste into Dockerfiles):

```text
# trivy 0.69.3 (trivy_0.69.3_Linux-64bit.tar.gz)
1816b632dfe529869c740c0913e36bd1629cb7688bd5634f4a858c1d57c88b75

# gitleaks 8.30.1 (gitleaks_8.30.1_linux_x64.tar.gz)
551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb

# grype 0.110.0 (grype_0.110.0_linux_amd64.tar.gz)
aaa98d27d2d7efd9317c6a1ad6d9b15f3e65bab320e7d03bde41e251387bb71c

# syft 1.42.3 (syft_1.42.3_linux_amd64.tar.gz)
0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509

# gosec 2.25.0 (gosec_2.25.0_linux_amd64.tar.gz)
ca099f42e37bc8f98ae54c23238e2b81b973c6d6a60c25c34da03f0292af0f32

# local-php-security-checker 2.1.3 (local-php-security-checker_linux_amd64)
db03c8c1806924081093fb6e3f752597a6d2ed6aea4621365e87e69d4814fd6c
```

## Universal container

Handles cross-cutting scanners: SAST (multi-language), dependency CVEs,
secret detection, SBOM generation, and IaC misconfiguration.

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# semgrep (pinned)
RUN pip install --no-cache-dir semgrep==1.156.0

# trivy (pinned + checksum verified)
RUN curl -sSfL https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_Linux-64bit.tar.gz \
    -o /tmp/trivy.tar.gz \
    && echo "1816b632dfe529869c740c0913e36bd1629cb7688bd5634f4a858c1d57c88b75  /tmp/trivy.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
    && rm /tmp/trivy.tar.gz

# gitleaks (pinned + checksum verified)
RUN curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
    -o /tmp/gitleaks.tar.gz \
    && echo "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  /tmp/gitleaks.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && rm /tmp/gitleaks.tar.gz

# grype (pinned + checksum verified)
RUN curl -sSfL https://github.com/anchore/grype/releases/download/v0.110.0/grype_0.110.0_linux_amd64.tar.gz \
    -o /tmp/grype.tar.gz \
    && echo "aaa98d27d2d7efd9317c6a1ad6d9b15f3e65bab320e7d03bde41e251387bb71c  /tmp/grype.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/grype.tar.gz -C /usr/local/bin grype \
    && rm /tmp/grype.tar.gz

# syft (pinned + checksum verified)
RUN curl -sSfL https://github.com/anchore/syft/releases/download/v1.42.3/syft_1.42.3_linux_amd64.tar.gz \
    -o /tmp/syft.tar.gz \
    && echo "0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509  /tmp/syft.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/syft.tar.gz -C /usr/local/bin syft \
    && rm /tmp/syft.tar.gz

# checkov (pinned)
RUN pip install --no-cache-dir checkov==3.2.513

COPY scan.sh /usr/local/bin/scan
RUN chmod +x /usr/local/bin/scan

WORKDIR /src
ENTRYPOINT ["scan"]
```

### Universal scan.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

SKIP="${SKIP_TOOLS:-}"
OUTPUT="/output"
MANIFEST="$OUTPUT/manifest.json"

mkdir -p "$OUTPUT"

tools_json="[]"

run_tool() {
  local name="$1"; shift
  if echo ",$SKIP," | grep -qi ",$name,"; then
    tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': 'already run in Phase 3'})
json.dump(t, sys.stdout)")
    return
  fi
  echo "Running $name..."
  "$@"
  local ec=$?
  local outfile="$name.json"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': $ec, 'outputFile': '$outfile', 'status': 'success' if $ec == 0 else 'error'})
json.dump(t, sys.stdout)")
}

run_tool "semgrep" semgrep scan --config auto --json --output "$OUTPUT/semgrep.json" /src
run_tool "trivy" trivy fs --format json --severity HIGH,CRITICAL --output "$OUTPUT/trivy.json" /src
run_tool "gitleaks" gitleaks detect --source /src --report-format json --report-path "$OUTPUT/gitleaks.json"
run_tool "grype" sh -c "grype dir:/src -o json > $OUTPUT/grype.json"
run_tool "syft" sh -c "syft dir:/src -o json > $OUTPUT/syft.json"

# checkov: only if IaC files exist
if ls /src/*.tf /src/Dockerfile /src/docker-compose.yml /src/k8s/ 2>/dev/null | head -1 > /dev/null; then
  run_tool "checkov" sh -c "checkov -d /src -o json > $OUTPUT/checkov.json 2>&1"
else
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': 'checkov', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': 'no IaC files detected'})
json.dump(t, sys.stdout)")
fi

echo "$tools_json" | python3 -c "
import sys, json
tools = json.load(sys.stdin)
manifest = {'stack': 'universal', 'tools': tools}
json.dump(manifest, sys.stdout, indent=2)
" > "$MANIFEST"

echo "Done. Results in $OUTPUT/"
```

## PHP container

For PHP and Drupal projects. Includes dependency auditing, coding standards,
static analysis with taint tracking, and Drupal-specific checks.

```dockerfile
FROM php:8.3-cli

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# phpcs + Drupal coding standards (pinned)
RUN composer global require \
    "squizlabs/php_codesniffer:3.7.2" \
    "drupal/coder:7.2.2" \
    --no-interaction --no-progress \
    && /root/.composer/vendor/bin/phpcs --config-set installed_paths /root/.composer/vendor/drupal/coder/coder_sniffer

# psalm (pinned)
RUN composer global require "vimeo/psalm:6.16.1" --no-interaction --no-progress

# phpstan (pinned)
RUN composer global require "phpstan/phpstan:2.1.45" --no-interaction --no-progress

# drupal-check (pinned)
RUN composer global require "mglaman/drupal-check:1.5.0" --no-interaction --no-progress

# local-php-security-checker (pinned + checksum verified)
RUN curl -sSfL https://github.com/fabpot/local-php-security-checker/releases/download/v2.1.3/local-php-security-checker_linux_amd64 \
    -o /usr/local/bin/local-php-security-checker \
    && echo "db03c8c1806924081093fb6e3f752597a6d2ed6aea4621365e87e69d4814fd6c  /usr/local/bin/local-php-security-checker" | sha256sum -c - \
    && chmod +x /usr/local/bin/local-php-security-checker

ENV PATH="/root/.composer/vendor/bin:${PATH}"

COPY scan.sh /usr/local/bin/scan
RUN chmod +x /usr/local/bin/scan

WORKDIR /src
ENTRYPOINT ["scan"]
```

### PHP scan.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

SKIP="${SKIP_TOOLS:-}"
OUTPUT="/output"
MANIFEST="$OUTPUT/manifest.json"

mkdir -p "$OUTPUT"

tools_json="[]"

run_tool() {
  local name="$1"; shift
  if echo ",$SKIP," | grep -qi ",$name,"; then
    tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': 'already run in Phase 3'})
json.dump(t, sys.stdout)")
    return
  fi
  echo "Running $name..."
  "$@"
  local ec=$?
  local outfile="$name.json"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': $ec, 'outputFile': '$outfile', 'status': 'success' if $ec == 0 else 'error'})
json.dump(t, sys.stdout)")
}

skip_tool() {
  local name="$1"
  local reason="$2"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': '$reason'})
json.dump(t, sys.stdout)")
}

# composer audit (works without vendor/)
if [ -f /src/composer.lock ]; then
  run_tool "composer-audit" sh -c "cd /src && composer audit --format=json > $OUTPUT/composer-audit.json 2>&1"
else
  skip_tool "composer-audit" "composer.lock not found -- dependency audit requires lockfile"
fi

# local-php-security-checker (works without vendor/)
if [ -f /src/composer.lock ]; then
  run_tool "security-checker" sh -c "local-php-security-checker --path=/src/composer.lock --format=json > $OUTPUT/security-checker.json 2>&1"
else
  skip_tool "security-checker" "composer.lock not found -- dependency audit requires lockfile"
fi

# phpcs (works without vendor/ for basic analysis)
run_tool "phpcs" sh -c "phpcs --standard=Drupal,DrupalPractice --extensions=php,module,inc,install,theme --report=json /src > $OUTPUT/phpcs.json 2>&1"

# Tools that need vendor/ for full analysis
if [ -d /src/vendor ]; then
  run_tool "psalm" sh -c "cd /src && psalm --taint-analysis --output-format=json > $OUTPUT/psalm.json 2>&1"
  run_tool "phpstan" sh -c "cd /src && phpstan analyse --error-format=json --no-progress > $OUTPUT/phpstan.json 2>&1"
else
  skip_tool "psalm" "vendor/ not found -- run composer install first"
  skip_tool "phpstan" "vendor/ not found -- run composer install first"
fi

# drupal-check
run_tool "drupal-check" sh -c "drupal-check --no-progress --format=json /src/web/modules/custom > $OUTPUT/drupal-check.json 2>&1"

echo "$tools_json" | python3 -c "
import sys, json
tools = json.load(sys.stdin)
manifest = {'stack': 'php', 'tools': tools}
json.dump(manifest, sys.stdout, indent=2)
" > "$MANIFEST"

echo "Done. Results in $OUTPUT/"
```

## Node.js container

For Node.js backends and frontend projects.

```dockerfile
FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# retire.js (pinned)
RUN npm install -g retire@5.4.2

COPY scan.sh /usr/local/bin/scan
RUN chmod +x /usr/local/bin/scan

WORKDIR /src
ENTRYPOINT ["scan"]
```

### Node.js scan.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

SKIP="${SKIP_TOOLS:-}"
OUTPUT="/output"
MANIFEST="$OUTPUT/manifest.json"

mkdir -p "$OUTPUT"

# Note: npm audit should be run directly (Phase 3) since npm ships locally.
# This container focuses on tools the project doesn't already have.

if echo ",$SKIP," | grep -qi ",retire,"; then
  cat > "$MANIFEST" <<EOFMANIFEST
{
  "stack": "node",
  "tools": [
    {
      "name": "retire",
      "exitCode": null,
      "outputFile": null,
      "status": "skipped",
      "reason": "already run in Phase 3"
    }
  ]
}
EOFMANIFEST
else
  echo "Running retire.js..."
  retire --path /src --outputformat json --outputpath "$OUTPUT/retire.json" 2>/dev/null
  RETIRE_EC=$?

  cat > "$MANIFEST" <<EOFMANIFEST
{
  "stack": "node",
  "tools": [
    {
      "name": "retire",
      "exitCode": $RETIRE_EC,
      "outputFile": "retire.json",
      "status": "$([ $RETIRE_EC -eq 0 ] && echo 'success' || echo 'error')"
    }
  ]
}
EOFMANIFEST
fi

echo "Done. Results in $OUTPUT/"
```

## Go container

For Go applications and services.

```dockerfile
FROM golang:1.22-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# gosec (pinned + checksum verified -- binary instead of go install)
RUN curl -sSfL https://github.com/securego/gosec/releases/download/v2.25.0/gosec_2.25.0_linux_amd64.tar.gz \
    -o /tmp/gosec.tar.gz \
    && echo "ca099f42e37bc8f98ae54c23238e2b81b973c6d6a60c25c34da03f0292af0f32  /tmp/gosec.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/gosec.tar.gz -C /usr/local/bin gosec \
    && rm /tmp/gosec.tar.gz

# govulncheck (pinned)
RUN go install golang.org/x/vuln/cmd/govulncheck@v1.1.4

COPY scan.sh /usr/local/bin/scan
RUN chmod +x /usr/local/bin/scan

WORKDIR /src
ENTRYPOINT ["scan"]
```

### Go scan.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

SKIP="${SKIP_TOOLS:-}"
OUTPUT="/output"
MANIFEST="$OUTPUT/manifest.json"

mkdir -p "$OUTPUT"

tools_json="[]"

run_tool() {
  local name="$1"; shift
  if echo ",$SKIP," | grep -qi ",$name,"; then
    tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': 'already run in Phase 3'})
json.dump(t, sys.stdout)")
    return
  fi
  echo "Running $name..."
  "$@"
  local ec=$?
  local outfile="$name.json"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': $ec, 'outputFile': '$outfile', 'status': 'success' if $ec == 0 else 'error'})
json.dump(t, sys.stdout)")
}

skip_tool() {
  local name="$1"
  local reason="$2"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': '$reason'})
json.dump(t, sys.stdout)")
}

if [ -f /src/go.sum ]; then
  run_tool "gosec" sh -c "cd /src && gosec -fmt json ./... > $OUTPUT/gosec.json 2>&1"
  run_tool "govulncheck" sh -c "cd /src && govulncheck -json ./... > $OUTPUT/govulncheck.json 2>&1"
else
  skip_tool "gosec" "go.sum not found -- run go mod tidy first"
  skip_tool "govulncheck" "go.sum not found -- run go mod tidy first"
fi

echo "$tools_json" | python3 -c "
import sys, json
tools = json.load(sys.stdin)
manifest = {'stack': 'go', 'tools': tools}
json.dump(manifest, sys.stdout, indent=2)
" > "$MANIFEST"

echo "Done. Results in $OUTPUT/"
```

## Python container

For Python applications and libraries.

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# bandit (pinned)
RUN pip install --no-cache-dir bandit==1.9.4

# pip-audit (pinned)
RUN pip install --no-cache-dir pip-audit==2.10.0

COPY scan.sh /usr/local/bin/scan
RUN chmod +x /usr/local/bin/scan

WORKDIR /src
ENTRYPOINT ["scan"]
```

### Python scan.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

SKIP="${SKIP_TOOLS:-}"
OUTPUT="/output"
MANIFEST="$OUTPUT/manifest.json"

mkdir -p "$OUTPUT"

tools_json="[]"

run_tool() {
  local name="$1"; shift
  if echo ",$SKIP," | grep -qi ",$name,"; then
    tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': None, 'outputFile': None, 'status': 'skipped', 'reason': 'already run in Phase 3'})
json.dump(t, sys.stdout)")
    return
  fi
  echo "Running $name..."
  "$@"
  local ec=$?
  local outfile="$name.json"
  tools_json=$(echo "$tools_json" | python3 -c "
import sys, json
t = json.load(sys.stdin)
t.append({'name': '$name', 'exitCode': $ec, 'outputFile': '$outfile', 'status': 'success' if $ec == 0 else 'error'})
json.dump(t, sys.stdout)")
}

run_tool "bandit" sh -c "bandit -r /src -f json -o $OUTPUT/bandit.json 2>&1"
run_tool "pip-audit" sh -c "cd /src && pip-audit --format=json -o $OUTPUT/pip-audit.json 2>&1"

echo "$tools_json" | python3 -c "
import sys, json
tools = json.load(sys.stdin)
manifest = {'stack': 'python', 'tools': tools}
json.dump(manifest, sys.stdout, indent=2)
" > "$MANIFEST"

echo "Done. Results in $OUTPUT/"
```
