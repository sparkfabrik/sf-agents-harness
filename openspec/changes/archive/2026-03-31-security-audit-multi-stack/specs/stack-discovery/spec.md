## ADDED Requirements

### Requirement: Detect project stacks from configuration files

The skill SHALL detect which language stacks are present in a project by reading well-known configuration files in the project root and common subdirectories.

The following mappings SHALL be used:

| Config file                                      | Detected stack |
| ------------------------------------------------ | -------------- |
| `composer.json`                                  | PHP            |
| `go.mod`                                         | Go             |
| `package.json`                                   | Node.js        |
| `pyproject.toml`, `requirements.txt`, `setup.py` | Python         |
| `*.tf`, `Dockerfile`, `docker-compose.yml`       | IaC            |

The skill SHALL detect Drupal as a sub-type of PHP when `composer.json` contains `drupal/core` or `drupal/core-recommended` as a dependency.

#### Scenario: PHP/Drupal project detection

- **WHEN** the project root contains a `composer.json` with `drupal/core-recommended` in `require`
- **THEN** the skill SHALL identify the stack as PHP with Drupal sub-type

#### Scenario: Mixed stack detection

- **WHEN** the project root contains both `composer.json` and `package.json`
- **THEN** the skill SHALL identify both PHP and Node.js as present stacks

#### Scenario: No recognized config files

- **WHEN** the project root contains no recognized configuration files for any supported stack
- **THEN** the skill SHALL inform the user that no stacks were auto-detected and ask the user to specify the stack manually

### Requirement: Discover existing tool configurations

The skill SHALL check for existing tool configuration files to determine which security-relevant tools are already available in the project.

The following tool indicators SHALL be checked:

| Config file                           | Tool available                            |
| ------------------------------------- | ----------------------------------------- |
| `phpstan.neon` or `phpstan.neon.dist` | phpstan                                   |
| `.phpcs.xml` or `phpcs.xml.dist`      | phpcs                                     |
| `psalm.xml` or `psalm.xml.dist`       | psalm                                     |
| `grumphp.yml`                         | grumphp (orchestrator for multiple tools) |
| `.eslintrc*`                          | eslint                                    |

#### Scenario: phpstan already configured

- **WHEN** the project contains a `phpstan.neon` file
- **THEN** the skill SHALL record phpstan as available with its existing configuration
- **THEN** the skill SHALL use the project's phpstan configuration when running phpstan in Phase 1a

#### Scenario: No tool configs found for detected stack

- **WHEN** the project is detected as PHP but contains no phpstan, phpcs, or psalm configuration
- **THEN** the skill SHALL note the absence in the discovery report and flag these tools as candidates for Docker-augmented scanning

### Requirement: Collect tool invocation method from user

The skill SHALL NOT attempt to auto-detect execution environments. Instead, the discovery report SHALL ask the user how project-native tools should be invoked.

The skill SHALL present common examples to guide the user:

- Directly: `phpcs .`
- Via vendor binaries: `./vendor/bin/phpcs .`
- Via a wrapper: `ddev exec phpcs .`, `lando phpcs .`, `docker compose exec php phpcs .`
- Via a task runner: `make phpcs`, `task phpcs`

The user's answer SHALL be used as the command prefix (or invocation pattern) for all project-native tool runs in Phase 1a.

#### Scenario: User specifies a command prefix

- **WHEN** the discovery report asks how tools should be invoked
- **THEN** the user provides a prefix such as `ddev exec`
- **THEN** the skill SHALL prefix all Phase 1a tool commands with `ddev exec` (e.g., `ddev exec phpcs .`)

#### Scenario: User specifies direct invocation

- **WHEN** the user responds that tools should be run directly (no prefix)
- **THEN** the skill SHALL run project-native tools without a command prefix

#### Scenario: User specifies vendor/bin path

- **WHEN** the user responds with `./vendor/bin/`
- **THEN** the skill SHALL invoke PHP tools as `./vendor/bin/phpcs .`, `./vendor/bin/phpstan analyse`, etc.

### Requirement: Detect CI-defined scanning

The skill SHALL read CI configuration files (`.gitlab-ci.yml`, `.github/workflows/*.yml`) to identify security scanning already performed in CI pipelines.

The skill SHALL report CI-discovered scanners as informational context but SHALL NOT skip Phase 1 scanning based on CI configuration alone, since CI results may not be locally available.

#### Scenario: GitLab CI with SAST stage

- **WHEN** `.gitlab-ci.yml` contains a job that runs `semgrep` or references a SAST template
- **THEN** the skill SHALL note in the discovery report that semgrep runs in CI
- **THEN** the skill SHALL still include semgrep in Phase 1 scanning

### Requirement: Produce a discovery report

After completing all detection steps, the skill SHALL present a structured discovery report to the user listing: detected stacks, available tools with their configurations, and CI scanning context.

The discovery report SHALL also ask the user how project-native tools should be invoked (see "Collect tool invocation method from user" requirement).

The skill SHALL ask the user to confirm the discovery results before proceeding to Phase 1.

#### Scenario: Discovery report for a Drupal project

- **WHEN** discovery detects PHP/Drupal stack, phpcs and phpstan configs
- **THEN** the skill SHALL present a report showing: stacks (PHP/Drupal), available tools (phpcs via .phpcs.xml, phpstan via phpstan.neon), and ask the user how to invoke these tools before proceeding
