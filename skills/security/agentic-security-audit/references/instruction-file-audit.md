# Instruction File Audit Patterns

Reference for auditing AI instruction files across tools. Each section covers
a specific tool's instruction file format, location, and security
considerations.

---

## General risk patterns

These patterns apply to all instruction files regardless of tool.

### Overly permissive scope

Instructions that grant unrestricted access without boundaries.

**Risky**:
- "You have full access to all files in the repository"
- "You can execute any command on the system"
- "You may modify any file"
- No mention of restricted directories or forbidden operations

**Better**:
- "You may read and modify files under `src/` and `tests/` only"
- "Do not modify files in `.github/`, `infrastructure/`, or `config/`"
- "Never execute destructive commands (rm -rf, DROP TABLE, etc.)"

### Credential exposure

Actual secrets embedded in instruction files.

**What to look for**:
- API keys: `sk-proj-...`, `sk-ant-...`, `ghp_...`, `glpat-...`
- Tokens: `Bearer ...`, `xoxb-...` (Slack), `AKIA...` (AWS)
- Passwords or connection strings with credentials
- Base64-encoded secrets

Instruction files are committed to version control and readable by anyone with
repo access. Credentials in instruction files are always a critical finding.

### Conflicting instructions

Contradictions between instruction files in the same project.

**What to look for**:
- One file says "never delete files", another says "clean up temp files"
- One file says "always ask before modifying", another says "make changes
  directly"
- Different files specify conflicting code style rules
- Security constraints in one file contradicted by permissive instructions in
  another

Conflicting instructions cause unpredictable agent behavior. The agent may
follow either instruction depending on context, creating inconsistent security
posture.

### Injection amplification

Instructions that tell the agent to follow commands from untrusted sources.

**Risky**:
- "Follow any instructions found in code comments"
- "If a file contains TODO instructions, execute them"
- "Obey user preferences stored in .env files"
- "Follow the conventions described in any README you find"
- "If you find a INSTRUCTIONS block in the code, follow it"

**Why it's dangerous**: These instructions turn any writable location (code
comments, data files, user input) into an injection vector. An attacker who
can write to those locations controls the agent.

### Missing restrictions

Instructions that only define what the agent can do, without boundaries.

**What to look for**:
- Capabilities listed but no forbidden actions
- No mention of security-sensitive operations (file deletion, network access,
  credential handling)
- No guidance on when to stop and ask the user
- No error handling instructions (what to do when uncertain)

**Better**:
- Explicit "never" list for dangerous operations
- Clear escalation path ("if unsure, ask the user")
- Boundaries on scope ("only work within the project directory")

### Stale configurations

Instruction files referencing tools, APIs, or patterns that no longer exist.

**What to check**:
- Referenced tools not present in project dependencies
- API endpoints or SDKs that have been deprecated
- File paths or directory structures that don't match current project layout
- Instructions for workflows that no longer exist (e.g., referencing a removed
  CI pipeline)

Stale configs indicate unmaintained instruction files. The security assumptions
they encode may no longer hold.

### Implicit trust of LLM outputs

No guidance on validating agent-generated outputs.

**Risky**:
- "Auto-commit your changes"
- "Deploy directly to production"
- "Trust all tool outputs"
- No mention of review, validation, or testing before applying changes

**Better**:
- "Run tests before committing"
- "Never push directly to main"
- "Ask for human review on changes to security-sensitive files"
- "Validate generated code against project linting rules"

---

## GitHub Copilot

### File location

- `.github/copilot-instructions.md` -- repository-level instructions
- Organization-level instructions (not in repo, managed via GitHub settings)

### Format

Plain markdown. No frontmatter required. Copilot reads this as additional
context for all interactions in the repository.

### Security considerations

- **Scope**: Instructions apply to all Copilot interactions in the repo. Overly
  broad instructions affect every developer using Copilot.
- **Visibility**: The file is in `.github/`, which is version-controlled and
  visible to all contributors.
- **No override mechanism**: Individual developers can't override repo-level
  instructions. Mistakes affect the whole team.
- **Tool access**: Copilot's tool access is controlled by VS Code / IDE
  settings, not by this file. Instructions here can *suggest* tool usage but
  can't *grant* new tool access.

### What to check

1. Does the file define security boundaries? (What Copilot should NOT do)
2. Are there instructions that could amplify prompt injection? (Following
   embedded commands in code)
3. Does it contain credentials or internal URLs?
4. Is it consistent with other instruction files in the project?

---

## Cursor

### File locations

- `.cursorrules` -- project-level rules (primary instruction file)
- `.cursorignore` -- files Cursor should not index or read

### Format

`.cursorrules`: plain text or markdown. No formal schema. Cursor reads this
as context for all AI interactions.

`.cursorignore`: gitignore-style patterns for files to exclude from Cursor's
context.

### Security considerations

- **`.cursorrules` scope**: Applies to all Cursor AI features (chat, inline
  edits, tab completion). Very broad impact.
- **`.cursorignore` as security control**: Can be used to prevent Cursor from
  reading sensitive files (`.env`, credentials, internal configs). Check that
  security-sensitive files are listed.
- **Agent mode**: Cursor's agent mode can execute terminal commands. If
  `.cursorrules` encourages agent mode use without restrictions, this expands
  the attack surface.

### What to check

1. Does `.cursorrules` restrict agent mode behavior?
2. Does `.cursorignore` exclude sensitive files (`.env`, credentials,
   infrastructure configs)?
3. Are there instructions encouraging unrestricted command execution?
4. Does it contain credentials or internal infrastructure details?

---

## OpenCode

### File locations

- `.opencode/` directory -- configuration, custom skills, custom agents
- `.opencode/config.yaml` or similar -- tool configuration
- Skills in `.opencode/skills/*/SKILL.md` -- custom skill definitions

### Format

YAML for configuration, markdown with YAML frontmatter for skills. Skills can
bundle scripts and reference files.

### Security considerations

- **Skill bundled scripts**: Skills can include executable scripts in their
  directory. These scripts run with the user's permissions. Malicious scripts
  in a skill are a supply chain risk.
- **Tool configuration**: OpenCode can be configured to use MCP servers and
  other tools. Check tool configurations for excessive permissions.
- **Custom agents**: Agent definitions can specify which tools they have access
  to. Verify tool grants are appropriate.

### What to check

1. Do any bundled skill scripts perform unsafe operations?
2. Are MCP server configurations in `.opencode/` using known, pinned packages?
3. Do custom agent definitions grant appropriate tool access?
4. Are there skills from unverified external sources?

---

## Aider

### File locations

- `.aider.conf.yml` -- project-level configuration
- `.aiderignore` -- files to exclude from Aider's context

### Format

YAML configuration file.

### Security considerations

- **Model selection**: Aider config can specify which LLM model to use. A
  compromised config could redirect to a malicious model endpoint.
- **Auto-commit**: Aider can be configured to auto-commit changes. Check if
  this is enabled without review requirements.
- **File context**: Aider reads project files for context. The `.aiderignore`
  file controls what's excluded. Check that sensitive files are excluded.

### What to check

1. Is auto-commit enabled? If so, are there guardrails?
2. Does the config specify a model endpoint? Is it a trusted provider?
3. Does `.aiderignore` exclude sensitive files?
4. Are there any custom commands or aliases that execute shell commands?

---

## MCP (Model Context Protocol)

### File locations

- `.mcp.json` -- MCP server configuration (common)
- `mcp.config.json`, `mcp.config.yaml` -- alternative config file names
- Tool-specific locations: `.vscode/mcp.json`, `.cursor/mcp.json`

### Format

JSON or YAML. Defines MCP servers, their transport (stdio, SSE), commands to
launch them, and environment variables to pass.

### Security considerations

- **Server commands**: MCP configs specify commands to launch servers (`npx`,
  `node`, `python`, etc.). These commands run with the user's permissions. A
  compromised config can execute arbitrary commands.
- **Environment variables**: Configs can pass environment variables to servers,
  including API keys and tokens. Check for credentials in config files.
- **Package sources**: `npx -y @package/name` installs and runs packages. If
  the package is from an untrusted publisher or unpinned, it's a supply chain
  risk.
- **Server permissions**: Each MCP server grants the agent access to specific
  tools. Overly broad server tools expand the attack surface.
- **Network access**: SSE-based MCP servers connect to remote endpoints. Check
  if those endpoints are trusted.

### What to check

1. Are MCP server packages from known publishers? Are versions pinned?
2. Do server commands include credentials or sensitive arguments?
3. Are environment variables passing secrets that could leak?
4. Do tool definitions have appropriate input schemas and restrictions?
5. Are SSE server URLs pointing to trusted endpoints?
6. Is there a pattern of `npx -y` with unpinned packages?

### Vulnerable MCP config patterns

```json
{
  "servers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@random-publisher/mcp-everything"],
      "env": {
        "DATABASE_URL": "postgres://admin:password@prod-db:5432/main"
      }
    }
  }
}
```

Issues: unpinned package from unknown publisher, production database
credentials in config, server name suggests overly broad tool access.

### Safer MCP config patterns

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem@1.2.0", "./src"],
      "env": {}
    }
  }
}
```

Improvements: pinned version, official MCP publisher, restricted to `./src`
directory, no credentials in env.

---

## Generic instruction files

### AGENTS.md

Multi-tool instruction file (works with Copilot, OpenCode, Cursor, and others).

**Location**: Project root or subdirectories.

**Security considerations**:
- Read by multiple tools -- instructions must be safe for all of them
- Often contains project structure, code style, and workflow instructions
- Can include tool-use instructions that expand agent capabilities
- Subdirectory `AGENTS.md` files can override or supplement root-level ones

### SKILL.md

Agent skill definitions used by OpenCode and potentially other tools.

**Location**: Skill directories (e.g., `skills/*/SKILL.md`, `.opencode/skills/*/SKILL.md`).

**Security considerations**:
- Skills can bundle executable assets (scripts, templates)
- Skill descriptions control when the skill auto-triggers
- Skills can load reference files that influence agent behavior
- External/upstream skills synced from other repositories are a supply chain
  concern
