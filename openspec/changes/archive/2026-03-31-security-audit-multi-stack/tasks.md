## 1. Restructure SKILL.md — Phase 0 Discovery

- [x] 1.1 Add Phase 0 (Discovery) section to SKILL.md before the current Phase 1, documenting the config file detection logic for all supported stacks (PHP/Drupal, Node.js, Go, Python, IaC)
- [x] 1.2 Add tool configuration discovery table (phpstan.neon, .phpcs.xml, psalm.xml, grumphp.yml, .eslintrc, etc.) to Phase 0
- [x] 1.3 Add tool invocation prompt to the discovery report — ask the user how project-native tools should be run (direct, vendor/bin, ddev exec, make, custom wrapper, etc.) with examples
- [x] 1.4 Add CI config scanning (`.gitlab-ci.yml`, `.github/workflows/*.yml`) as informational context in Phase 0
- [x] 1.5 Add discovery report format — structured summary of detected stacks, tools, and CI context — with tool invocation prompt and user confirmation before proceeding

## 2. Restructure SKILL.md — Phase 1 Split

- [x] 2.1 Rename current Phase 1 to Phase 1a (project-native tools) and document that it runs tools already configured in the project using the user-provided invocation method (command prefix or direct)
- [x] 2.2 Add Phase 1b (Docker-augmented scanning) section documenting the generated container workflow: build, run with mounted source, collect output
- [x] 2.3 Document the skip-list mechanism — Phase 1b skips tools already run successfully in Phase 1a
- [x] 2.4 Document Docker availability check — if Docker is not available, skip Phase 1b and proceed with Phase 1a results only, informing the user of reduced coverage
- [x] 2.5 Document parallel container execution for multi-stack projects

## 3. Dockerfile Generation Logic

- [x] 3.1 Add Phase 0.5 section to SKILL.md documenting the Dockerfile generation step: per-stack Dockerfiles + universal Dockerfile, written to `.security-audit/<stack>/`
- [x] 3.2 Document base image selection per stack (php:8.3-cli, node:22-slim, golang:1.22-bookworm, python:3.12-slim)
- [x] 3.3 Document tool installation instructions per stack — exact apt/pip/composer/go install commands for each tool in the tool matrix
- [x] 3.4 Create `references/dockerfile-templates.md` with template Dockerfiles for each stack (universal, PHP, Node.js, Go, Python) that the skill uses as a basis for generation
- [x] 3.5 Document scan.sh generation — linear tool invocations, JSON output to /output/, manifest.json as final step
- [x] 3.6 Document dependency readiness checks in scan.sh (vendor/ for PHP, node_modules/ for Node.js) with skip-and-report behavior

## 4. Update Tool Matrix

- [x] 4.1 Add PHP/Drupal tools to the tool matrix table: composer audit, phpcs (drupal/coder), psalm (taint analysis), phpstan, drupal-check, local-php-security-checker
- [x] 4.2 Add missing universal tools to the matrix: gitleaks, grype, syft, checkov
- [x] 4.3 Update the "Running the scans" code block with PHP tool invocation examples
- [x] 4.4 Replace the "Handling missing tools" section with the new Docker-based approach (generate Dockerfile, build, run) instead of asking the user to install tools manually

## 5. Structured Output

- [x] 5.1 Document the `.security-audit/` output directory structure in SKILL.md (per-stack subdirectories, output/, manifest.json)
- [x] 5.2 Document the manifest.json format — tool name, exit code, output file path, skip reason if applicable
- [x] 5.3 Update the "Scan summary format" to consolidate results from multiple containers into the unified summary table

## 6. PHP/Drupal Reference File

- [x] 6.1 Create `references/php-security.md` with the general PHP vulnerability patterns section: eval/preg_replace code injection, unserialize object injection, extract variable injection, include/require LFI, exec/system command injection, htmlspecialchars flags
- [x] 6.2 Add Drupal render array injection section (vulnerable #markup vs safe #plain_text, Xss::filter)
- [x] 6.3 Add Drupal SQL injection section (raw Database::query with concatenation vs parameterized :placeholder)
- [x] 6.4 Add Drupal Form API CSRF section (custom route handlers bypassing Form API token validation)
- [x] 6.5 Add Twig autoescape bypass section (|raw filter with user data)
- [x] 6.6 Add Drupal access bypass section (entity queries without accessCheck, routes missing \_permission/\_access)
- [x] 6.7 Add Drupal file handling section (public:// vs private:// for sensitive uploads)
- [x] 6.8 Add PHP scanner tool configuration section documenting invocation, key rules, and output interpretation for each PHP tool (composer audit, phpcs, psalm taint, phpstan, drupal-check)
- [x] 6.9 Add the language-specific guide entry for PHP/Drupal to SKILL.md's references list

## 7. Verification

- [x] 7.1 Verify SKILL.md is internally consistent — Phase 0 → 0.5 → 1a → 1b → 2 flow reads coherently, tool matrix matches Dockerfile templates, scan summary format handles multi-container output
- [x] 7.2 Verify all three reference files (Go, Node.js, PHP) follow the same structural pattern (vulnerable/safe pairs, "what to look for" grep patterns, tool rule references)
