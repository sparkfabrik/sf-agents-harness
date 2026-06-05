## Purpose

Per-stack Docker container generation for security scanning -- Dockerfile templates, scan scripts, tool assignments, and container orchestration.

## Requirements

### Requirement: Generate per-stack Dockerfiles based on discovery results

The skill SHALL generate one Dockerfile per detected stack, plus one universal Dockerfile for cross-cutting scanning tools. Dockerfiles SHALL be written to `.code-security-audit/<stack>/Dockerfile`.

Each Dockerfile SHALL use a base image appropriate for the stack:

| Stack     | Base image             |
| --------- | ---------------------- |
| Universal | `python:3.12-slim`     |
| PHP       | `php:8.3-cli`          |
| Node.js   | `node:22-slim`         |
| Go        | `golang:1.22-bookworm` |
| Python    | `python:3.12-slim`     |

#### Scenario: PHP project generates PHP and universal Dockerfiles

- **WHEN** Phase 0 detected PHP as the only stack
- **THEN** the skill SHALL generate `.code-security-audit/php/Dockerfile` with PHP-specific tools
- **THEN** the skill SHALL generate `.code-security-audit/universal/Dockerfile` with semgrep, trivy, gitleaks, grype, and checkov

#### Scenario: Mixed PHP and Node.js project

- **WHEN** Phase 0 detected both PHP and Node.js stacks
- **THEN** the skill SHALL generate separate Dockerfiles for `php/`, `node/`, and `universal/`

### Requirement: Include only relevant tools per stack

Each stack Dockerfile SHALL install only tools relevant to that stack. The universal Dockerfile SHALL install cross-cutting tools.

Tool assignments:

| Container | Tools                                                                                                |
| --------- | ---------------------------------------------------------------------------------------------------- |
| Universal | semgrep, trivy, gitleaks, grype, syft, checkov                                                       |
| PHP       | composer (for audit), phpcs + drupal/coder, psalm, phpstan, drupal-check, local-php-security-checker |
| Node.js   | retire.js                                                                                            |
| Go        | gosec, govulncheck                                                                                   |
| Python    | bandit, pip-audit                                                                                    |

npm audit SHALL NOT require a Docker container because it ships with npm. If Node.js is detected, the skill SHALL run `npm audit` directly in Phase 1a.

#### Scenario: PHP Dockerfile contents

- **WHEN** generating the PHP Dockerfile
- **THEN** the Dockerfile SHALL install composer, phpcs with drupal/coder sniffs, psalm, phpstan, drupal-check, and local-php-security-checker
- **THEN** the Dockerfile SHALL NOT install any Go, Python, or Node.js tools

### Requirement: Generate a scan script per container

The skill SHALL generate a `scan.sh` script alongside each Dockerfile. The scan script SHALL be a linear sequence of tool invocations with no conditional logic -- every tool listed in the Dockerfile SHALL be invoked.

Each tool invocation SHALL:

- Request JSON output format where the tool supports it
- Write output to `/output/<tool-name>.json`
- Capture the exit code and continue to the next tool even if one fails

The scan script SHALL write a `manifest.json` as its final step, listing every tool that ran, its exit code, and the path to its output file.

#### Scenario: PHP scan script execution

- **WHEN** the PHP container runs its scan.sh
- **THEN** it SHALL run composer audit, phpcs, psalm, phpstan, and drupal-check in sequence
- **THEN** each tool's JSON output SHALL be written to `/output/`
- **THEN** a `/output/manifest.json` SHALL be written listing all tool runs and their exit codes

#### Scenario: Tool failure does not stop the scan

- **WHEN** phpcs exits with a non-zero code (indicating findings)
- **THEN** the scan script SHALL record the exit code in manifest.json
- **THEN** the scan script SHALL continue to run the remaining tools

### Requirement: Skip tools already run in Phase 1a

The skill SHALL pass a skip list to the Docker scan based on what Phase 1a already ran successfully. The scan script SHALL accept tool names to skip as arguments or environment variables.

#### Scenario: phpcs already run natively

- **WHEN** Phase 1a successfully ran phpcs using the project's configuration
- **THEN** Phase 1b SHALL instruct the PHP container to skip phpcs
- **THEN** the manifest.json SHALL list phpcs as "skipped -- already run in Phase 1a"

### Requirement: Build and run containers

The skill SHALL build each generated Dockerfile using `docker build` and run the resulting image with the project source mounted as a read-only volume and an output directory mounted for writing.

```
docker build -t code-security-audit-<stack> .code-security-audit/<stack>/
docker run --rm \
  -v $(pwd):/src:ro \
  -v $(pwd)/.code-security-audit/<stack>/output:/output \
  code-security-audit-<stack>
```

Containers for different stacks SHALL be run in parallel when possible.

#### Scenario: Docker not available

- **WHEN** Docker is not installed or the Docker daemon is not running
- **THEN** the skill SHALL skip Phase 1b entirely
- **THEN** the skill SHALL inform the user that Docker-augmented scanning was skipped and list which tools were not available
- **THEN** the skill SHALL proceed to Phase 2 using only Phase 1a results

#### Scenario: Parallel container execution

- **WHEN** both PHP and universal containers need to run
- **THEN** the skill SHALL start both containers in parallel
- **THEN** the skill SHALL wait for both to complete before proceeding to result consolidation

### Requirement: Report dependency readiness

For tools that require resolved dependencies (psalm, phpstan, gosec, govulncheck), the scan script SHALL check whether the dependency directory exists (`/src/vendor/` for PHP, `/src/node_modules/` for Node.js) and report in the manifest if a tool was skipped due to missing dependencies.

#### Scenario: vendor/ not present

- **WHEN** the PHP container runs and `/src/vendor/` does not exist
- **THEN** the scan script SHALL skip psalm and phpstan
- **THEN** the manifest.json SHALL list them as "skipped -- vendor/ not found, run composer install first"
- **THEN** the scan script SHALL still run tools that don't need vendor/ (composer audit, phpcs with limited analysis, drupal-check)
