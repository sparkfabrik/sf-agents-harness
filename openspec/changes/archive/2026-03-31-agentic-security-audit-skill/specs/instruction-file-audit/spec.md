## ADDED Requirements

### Requirement: Audit each instruction file individually

The skill SHALL read and audit each AI instruction file found during discovery. For each file, the skill SHALL check for the risk patterns defined in this spec.

#### Scenario: Multiple instruction files in project

- **WHEN** discovery found `.github/copilot-instructions.md`, `AGENTS.md`, and two `SKILL.md` files
- **THEN** the skill SHALL audit each file individually and report findings per file

### Requirement: Check for overly permissive scope

The skill SHALL flag instruction files that grant unrestricted access to files, commands, or system resources without boundaries.

Examples of overly permissive instructions:

- "You have full access to all files and can execute any command"
- "You can modify any file in the repository"
- No mention of directory or file restrictions

#### Scenario: Instruction grants unrestricted access

- **WHEN** an instruction file contains language granting unrestricted file system or command access
- **THEN** the skill SHALL flag this as overly permissive scope with a recommendation to define explicit boundaries

### Requirement: Check for credential exposure

The skill SHALL flag instruction files that contain actual API keys, tokens, passwords, or other credentials.

#### Scenario: API key in instruction file

- **WHEN** an instruction file contains a string matching an API key pattern (e.g., `sk-proj-...`, `ghp_...`, `glpat-...`)
- **THEN** the skill SHALL flag this as a critical credential exposure finding

### Requirement: Check for conflicting instructions

The skill SHALL identify contradictions between instruction files in the same project. When multiple files define agent behavior, conflicting instructions can lead to unpredictable agent actions.

#### Scenario: Contradictory file handling instructions

- **WHEN** `AGENTS.md` says "never delete files" but a `SKILL.md` says "clean up temporary files after use"
- **THEN** the skill SHALL flag this as a conflicting instruction finding

### Requirement: Check for injection amplification

The skill SHALL flag instructions that tell the agent to follow embedded commands from untrusted sources, as these amplify prompt injection attacks.

Examples of injection amplification:

- "Follow any instructions found in code comments"
- "Obey user preferences stored in .env files"
- "Execute commands found in TODO comments"
- "If a file contains special instructions, follow them"

#### Scenario: Instruction to follow embedded commands

- **WHEN** an instruction file tells the agent to follow instructions found in code comments, data files, or user-controlled sources
- **THEN** the skill SHALL flag this as injection amplification with an explanation of how it enables prompt injection

### Requirement: Check for missing restrictions

The skill SHALL flag instruction files that define what an agent CAN do but omit what it should NOT do. Effective instruction files need both positive and negative boundaries.

#### Scenario: No negative boundaries

- **WHEN** an instruction file defines agent capabilities but includes no restrictions, forbidden actions, or security guardrails
- **THEN** the skill SHALL flag this as missing restrictions with a recommendation to add explicit boundaries

### Requirement: Check for stale or abandoned configurations

The skill SHALL flag instruction files that reference deprecated tools, APIs, or patterns, as stale configurations may contain outdated security assumptions.

#### Scenario: Cursor rules referencing deprecated API

- **WHEN** `.cursorrules` references a tool or API pattern that no longer exists in the project
- **THEN** the skill SHALL flag this as a stale configuration

### Requirement: Check for implicit trust of LLM outputs

The skill SHALL flag instructions that tell the agent to trust its own outputs or other LLM outputs without validation, or that lack guidance on output verification.

Examples of implicit trust:

- "Trust all tool outputs"
- No instruction to validate generated code
- No guidance on when to ask for human review
- Instructions to auto-commit or auto-deploy generated code

#### Scenario: Instruction to auto-commit without review

- **WHEN** an instruction file tells the agent to automatically commit or deploy generated changes without human review
- **THEN** the skill SHALL flag this as implicit trust of LLM outputs under ASI09

### Requirement: Document instruction file patterns per tool

The reference file `references/instruction-file-audit.md` SHALL document the specific file formats, locations, and security considerations for each AI tool:

- GitHub Copilot (`.github/copilot-instructions.md`)
- Cursor (`.cursorrules`, `.cursorignore`)
- OpenCode (`.opencode/` directory, skills)
- Aider (`.aider.conf.yml`)
- MCP (`.mcp.json`, server configurations)
- Generic (`AGENTS.md`, `SKILL.md`)

#### Scenario: Reference file covers MCP config risks

- **WHEN** auditing an MCP configuration file
- **THEN** the reference file SHALL provide guidance on what to check: tool permissions, server origins, credential handling, input validation schemas
