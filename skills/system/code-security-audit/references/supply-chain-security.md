# Supply-Chain Security and Incident Triage

Use this reference when the user asks whether a repository or developer
environment is affected by a malicious package, typosquat, compromised
maintainer release, poisoned lockfile, or install-time malware campaign.

## Key rule

Advisory-based scanners such as `npm audit`, `pip-audit`, `composer audit`,
`trivy`, and `grype` are necessary but not sufficient. Fresh malicious
publishes often appear before any advisory exists. For named incidents, combine
the normal audit with exact-version and IOC-based triage.

## Step 1: Gather the campaign IOC set

Prefer one of these sources, in order:

1. The user-provided vendor or security advisory
2. An official GHSA, npm, PyPI, Packagist, or distro advisory
3. An organization-maintained incident scanner or playbook
4. A reputable open-source write-up with explicit IOCs

Capture the exact package names, version ranges, commit hashes, filenames,
domains, hashes, lifecycle hooks, and workflow patterns. Do not rely on memory
or on examples from previous incidents.

If the organization already maintains a scanner script, run it and report its
results as an additional scanner. Do not vendor or duplicate that script inside
this skill unless the user explicitly asks.

## Step 2: Inventory every relevant path

Search the whole repository, not just the root. Ignore dependency directories
and build outputs:

- `node_modules/`
- `vendor/`
- `.git/`
- `dist/`, `build/`, `coverage/`
- `.code-security-audit/`

Inventory at least these files and directories:

- Node.js: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
  `bun.lock`, `bun.lockb`
- PHP/Composer: `composer.json`, `composer.lock`
- Python: `pyproject.toml`, `requirements*.txt`, `poetry.lock`, `uv.lock`
- Go: `go.mod`, `go.sum`
- CI: `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `.gitlab-ci.yml`
- Persistence paths in scope: repo-local `.claude/`, `.vscode/`, and only
  home-directory equivalents if the user approved that scope

`Repo-local` means physically inside the current repository root. Do not follow
symlinks, bind mounts, or workspace shortcuts that resolve outside the
repository unless the user explicitly expanded the scope.

## Step 3: High-signal checks

### Exact package/version matches

- Search every lockfile for the exact compromised package names and versions
  from the advisory.
- Also inspect installed dependency trees if `node_modules/` or equivalent
  exists.
- Treat an exact bad version match as a high-confidence finding even if
  `npm audit` or `trivy` is still clean.

### Suspicious dependency sources

Review manifests for:

- GitHub or git dependencies: `github:`, `git+https://`, raw commit SHAs,
  tarball URLs
- Unexpected `optionalDependencies`, `overrides`, `resolutions`, or
  package-manager-specific override blocks
- Dependencies that suddenly move from registry versions to Git references

### Install-time execution

Review lifecycle hooks and install commands:

- `preinstall`
- `install`
- `postinstall`
- `prepare`

Escalate if they:

- execute downloaded code
- run `curl`, `wget`, or PowerShell download-and-exec patterns
- execute bundled JS, Python, or shell payloads from unusual locations
- invoke `bun run`, `node <payload>`, `python <payload>`, or shell shims in a
  way that does not match the package's normal behavior

### Persistence and lateral movement

Check for suspicious files or hooks in:

- repo-local `.claude/settings.json`, `.claude/*.js`, `.claude/*.mjs`
- repo-local `.vscode/tasks.json`, `.vscode/settings.json`
- git hooks or other workspace automation files

Only search `~/.claude/` and `~/.vscode/` when that scope was explicitly
approved.

### CI trust-boundary review

Look for:

- `pull_request_target`
- broad `permissions:` with `id-token: write`
- publish jobs that share runners, workspaces, or caches with untrusted PR code
- cache poisoning opportunities
- unpinned third-party actions
- checkout of attacker-controlled refs under privileged workflows

### Git history review

Inspect recent commits for:

- suspicious bot or noreply identities
- unexpected dependency-only updates
- newly added large or obfuscated files
- sudden workflow changes
- IOC filenames, domains, or commit hashes from the advisory

## Example IOC categories from past campaigns

These are pattern categories, not current or authoritative IOCs. Do not treat
them as a substitute for the campaign's actual advisory or organizational
scanner:

- unexpectedly added executable payload files or obfuscated bootstrap files
- malicious Git-based dependencies injected through `optionalDependencies`,
  override blocks, or tarball URLs
- suspicious Git commit refs or repository URLs used as dependency sources
- persistence under repo-local `.claude/` or `.vscode/`
- CI abuse patterns combining privileged PR workflows and `id-token: write`

If the user names a campaign, pull the exact filenames, hashes, domains, and
version ranges from the current advisory instead of assuming any example here
is still valid.

## False-positive discipline

Do not report a finding based on a single generic string alone.

Examples:

- `169.254.169.254` in a legitimate cloud SDK is not enough by itself
- `prepare` scripts are common; the issue is unexpected or malicious behavior
- Git dependencies are not always bad; the issue is unexplained or
  campaign-matching sources

Corroborate with package names, exact versions, file additions, workflow
changes, or other IOCs.

## Reporting

Separate results into three buckets:

- `Confirmed IOC`
- `Suspicious pattern requiring review`
- `Not found`

For each confirmed or suspicious result, record:

- location
- matched IOC or pattern
- evidence
- confidence
- remediation

## Severity guidance

- Critical: exact compromised version installed, confirmed malicious file/hash,
  confirmed persistence artifact, or attacker-controlled CI publish path
- High: suspicious workflow trust-boundary issue, malicious-looking lifecycle
  hook, or Git dependency matching the incident pattern
- Medium: incomplete or indirect IOC match that still requires follow-up
- Low/Info: hardening gaps such as missing lockfile integrity enforcement or
  over-broad workflow permissions without evidence of compromise
