## Context

The security-audit skill (`skills/system/security-audit/SKILL.md`) currently defines a two-phase audit workflow: Phase 1 runs automated scanners, Phase 2 does LLM-guided manual review. The tool matrix covers Go (gosec, govulncheck), Node.js (npm audit), Python (bandit), Ruby (brakeman), and universal tools (semgrep, trivy, bearer). PHP/Drupal is absent entirely.

The skill assumes tools are installed locally and handles missing tools by asking the user to install them or skip. In practice, developers rarely have cross-stack security tools installed, and on PHP/Drupal projects none of the Go-specific tools are relevant.

The skill ships with two reference files providing language-specific vulnerability patterns: `references/go-security.md` and `references/nodejs-security.md`. These are used by the LLM during Phase 2 manual review.

## Goals / Non-Goals

**Goals:**

- Support PHP/Drupal projects as a first-class stack, with dedicated tools and a reference file comparable to the existing Go and Node.js ones.
- Eliminate the requirement that scanning tools be locally installed by generating per-stack Docker containers at audit time.
- Detect what the project already has configured (phpcs, phpstan, CI pipelines, DDEV, etc.) and use those native tools first, before reaching for Docker.
- Keep the skill stack-agnostic at the core — the Phase 0 discovery and Dockerfile generation patterns should extend to new stacks without restructuring the skill.

**Non-Goals:**

- Dynamic application testing (OWASP ZAP, nikto, sqlmap) — these require a running application and are a separate concern to explore later.
- Shipping a pre-built Docker image to a registry. The skill generates and builds Dockerfiles locally. Registry hosting is a future optimization.
- Replacing the existing Phase 2 manual review workflow — it stays as-is, just receives better input from the restructured Phase 1.
- Supporting every possible PHP framework. The reference file targets Drupal specifically, with general PHP patterns. Laravel/Symfony-specific content can be added later.

## Decisions

### Decision 1: Phase 0 discovery via config file detection

The skill reads well-known config files to build a stack profile before running any tools.

Detection targets per stack:

| Stack      | Config files                                       | Tool indicators                                                        |
| ---------- | -------------------------------------------------- | ---------------------------------------------------------------------- |
| PHP/Drupal | `composer.json`, `composer.lock`                   | `phpstan.neon(.dist)`, `.phpcs.xml(.dist)`, `psalm.xml`, `grumphp.yml` |
| Node.js    | `package.json`, `package-lock.json`                | `.eslintrc*`, scripts in package.json                                  |
| Go         | `go.mod`, `go.sum`                                 | —                                                                      |
| Python     | `pyproject.toml`, `requirements.txt`, `setup.py`   | —                                                                      |
| IaC        | `*.tf`, `Dockerfile`, `docker-compose.yml`, `k8s/` | —                                                                      |

Additionally, the skill checks for execution environments:

- `.ddev/config.yaml` → tools should be run via `ddev exec`
- `.lando.yml` → tools should be run via `lando`
- `Makefile` / `Taskfile.yml` → check for existing lint/security targets
- `.gitlab-ci.yml` / `.github/workflows/*.yml` → identify what CI already scans

**Alternative considered**: Asking the user what stack they're using. Rejected because the config files are authoritative and asking adds friction.

### Decision 2: Per-stack generated Dockerfiles, not a single fat image

The skill generates one Dockerfile per detected stack, plus one for universal tools. Each uses a base image matching the stack's runtime.

| Stack     | Base image             | Stack-specific tools                                                 |
| --------- | ---------------------- | -------------------------------------------------------------------- |
| Universal | `python:3.12-slim`     | semgrep, trivy, gitleaks, grype, syft, checkov                       |
| PHP       | `php:8.3-cli`          | composer (audit), phpcs + drupal/coder, psalm, phpstan, drupal-check |
| Node.js   | `node:22-slim`         | npm (audit), retire.js                                               |
| Go        | `golang:1.22-bookworm` | gosec, govulncheck                                                   |
| Python    | `python:3.12-slim`     | bandit, pip-audit                                                    |

**Alternative considered**: Single fat image with all runtimes. Rejected because it would be 2-3 GB, include irrelevant tools, and risk tool conflicts between package managers.

**Alternative considered**: Using the universal container's base (python:3.12-slim) for all stacks and installing runtimes as needed. Rejected because PHP tools like psalm need the actual PHP runtime and extensions to resolve autoloaders and type information correctly.

### Decision 3: Generated scan.sh per container, not a generic entrypoint

Each container gets a generated `scan.sh` script that is a linear sequence of tool invocations — no conditional logic, no stack detection at runtime. The skill knows exactly what tools it installed in the Dockerfile, so the scan script can be a straight-line "run A, run B, run C."

Output goes to `/output/<tool>.json` (or SARIF where natively supported). A `manifest.json` is written last, listing what ran, what succeeded, what failed, and any tools that were skipped in Phase 1b because Phase 1a already ran them.

### Decision 4: Phase 1a uses project-native invocations with user-provided command prefix

If Phase 0 detects that a tool is already configured in the project, Phase 1a runs it. Rather than auto-detecting the execution environment (DDEV, Lando, custom wrappers), the discovery report asks the user how tools should be invoked. The user provides a command prefix or invocation pattern:

- `ddev exec phpcs .`
- `./vendor/bin/phpcs .`
- `docker compose exec php phpcs .`
- `make phpcs`
- Just `phpcs .` (direct)

**Alternative considered**: Auto-detecting environments by looking for `.ddev/config.yaml`, `.lando.yml`, etc. Rejected because the list of possible environments is open-ended — teams use custom Docker wrappers, Makefiles, Taskfiles, and proprietary tooling. Hardcoding specific environments creates the same brittleness problem as hardcoding specific language stacks. Asking the user is simpler, always correct, and handles any environment.

This respects the project's own rulesets and exclusions. Phase 1b (Docker) only fills gaps — tools the project doesn't already have.

The skill passes a `--skip` list to the Docker scan script based on what Phase 1a already covered.

### Decision 5: Structured output directory

All scan artifacts go under `.security-audit/`:

```
.security-audit/
├── universal/
│   ├── Dockerfile
│   ├── scan.sh
│   └── output/
│       ├── manifest.json
│       ├── semgrep.json
│       ├── trivy.json
│       └── gitleaks.json
├── php/
│   ├── Dockerfile
│   ├── scan.sh
│   └── output/
│       ├── manifest.json
│       ├── composer-audit.json
│       ├── phpcs.json
│       └── psalm.json
└── node/
    ├── Dockerfile
    ├── scan.sh
    └── output/
        ├── manifest.json
        └── npm-audit.json
```

This directory should be gitignored. The Dockerfiles are ephemeral artifacts of the audit, not project configuration (though teams could choose to commit them for CI reuse).

### Decision 6: PHP/Drupal reference file scope

The new `references/php-security.md` follows the same structure as the existing Go and Node.js references: vulnerable/safe code pairs, "what to look for" grep patterns, and tool-specific rule references.

Drupal-specific patterns to cover:

- Unsanitized render arrays (`#markup` with user input, missing `#plain_text`)
- Raw SQL via `Database::getConnection()->query()` without placeholders
- Form API CSRF (forms without proper token validation)
- `\Drupal\Component\Utility\Html::escape()` vs raw `t()` with user input
- Insecure file handling (public:// vs private:// for sensitive uploads)
- Twig autoescape bypass (`|raw` filter with user data)
- Hook implementations that bypass access checking
- Services accessed via `\Drupal::service()` without interface validation

## Risks / Trade-offs

**[Docker dependency]** → The skill now requires Docker on the developer's machine. Docker is more widely available than individual security tools, but it's not universal. Mitigation: Phase 0 checks for Docker availability. If Docker is absent, the skill falls back to Phase 1a only (project-native tools) and Phase 2 (LLM manual review). The audit still happens, just with less automated coverage. The skill clearly states what was skipped and why.

**[Build time on first run]** → Generating and building Docker images takes time (1-3 minutes per container on first build, fast on subsequent runs due to layer caching). Mitigation: The skill prints progress during builds so the user isn't staring at silence. Containers can be built in parallel.

**[Psalm taint analysis needs vendor/]** → Psalm and phpstan need resolved dependencies to work properly. If `vendor/` doesn't exist, these tools will fail or produce incomplete results. Mitigation: The manifest reports these as "skipped — vendor/ not found" and the skill advises running `composer install` first. The container mounts the source read-only and does not run `composer install` itself.

**[Semgrep duplication across containers]** → Semgrep appears in the universal container but could overlap with stack-specific scanning. Mitigation: The universal container runs semgrep with `--include` flags scoped to file types not covered by stack-specific containers. Or, semgrep only runs in the universal container with its full `--config auto` ruleset, and stack-specific containers omit it. The latter is simpler.

**[Generated Dockerfiles could drift]** → If tool versions or base images change, the generated Dockerfiles need updating. Mitigation: The Dockerfile templates are defined in the skill's reference file (`references/dockerfile-templates.md`), making them easy to update centrally. Pin tool versions in the templates.
