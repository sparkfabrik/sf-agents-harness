# System Resources

Cross-cutting agents and skills not tied to a specific technology. Installed
externally via [sparkdock](https://github.com/sparkfabrik/sparkdock).

## Directory layout

```
agents/system/<agent-name>/
├── copilot/     # GitHub Copilot profile (.agent.md)
└── opencode/    # OpenCode profile (.md)

skills/system/<skill-name>/
└── SKILL.md     # Skill definition (plus optional bundled assets)
```

### Agents

System agents support multiple tools (Copilot, OpenCode). Each tool gets its
own file in a subfolder, but the prompt body is kept identical across tools --
only the YAML frontmatter differs to match each tool's configuration format.
There is no shared standard yet.

| Tool     | Install path                                |
| -------- | ------------------------------------------- |
| Copilot  | `~/.copilot/agents/<agent-name>.agent.md`   |
| OpenCode | `~/.config/opencode/agents/<agent-name>.md` |

### Skills

System skills follow the standard skill format (folder with `SKILL.md`). They
may include bundled assets such as scripts, reference data, or eval definitions.
Skills are installed to a shared standard path used by all coding agent tools:

| Install path                     |
| -------------------------------- |
| `~/.agents/skills/<skill-name>/` |

## Catalog metadata

`config/catalog.json` provides machine-readable short descriptions for all
system skills and agents. It is consumed by `sparkdock-agents-status` to display
a DESCRIPTION column in the terminal table. The schema is defined in
`config/catalog.schema.json`.

When adding or modifying a system skill or agent, update the catalog entry too.

## Available agents

- **the-analyst** -- Domain analysis and modeling agent. Turns ambiguous requirements into bounded contexts, ubiquitous language, invariants, workflows, and integration boundaries. Not a code agent.
- **the-architect** -- Conversational AI oracle for discovery, brainstorming, architecture, and general knowledge. Not a code agent.
- **the-builder** -- Test-driven development agent. Writes code, tests, and refactors with accountability. Technology-agnostic, principle-driven.
- **the-reviewer** -- Read-only implementation review agent. Compares candidate implementations, picks the best fit for the requirements, and produces severity-ordered findings with evidence.

## Available skills

- **glab** -- GitLab CLI skill for working with issues, merge requests, CI/CD pipelines, and repositories via the `glab` CLI.
- **gh** -- GitHub CLI skill for working with issues, pull requests, Actions workflows, releases, and repositories via the `gh` CLI.
- **playwright-cli** -- Browser automation with the `playwright-cli` CLI tool for web testing, screenshots, form filling, and data extraction. Synced from [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) with custom output file conventions.
- **skill-creator** -- Create, iterate, and benchmark agent skills with eval-driven workflows. Synced from [anthropics/skills](https://github.com/anthropics/skills) with custom tool-agnostic usage guidance.
- **doc-coauthoring** -- Structured workflow for co-authoring documentation, proposals, and technical specs. Synced from [anthropics/skills](https://github.com/anthropics/skills).
- **code-security-audit** -- Multi-phase code security audit workflow (discovery, container generation, native scans, Docker scans, manual review) for web applications and APIs. Open-source tools only.
- **agentic-security-audit** -- Audit AI agent configurations, instruction files, and LLM integration code for security risks mapped to the OWASP Top 10 for Agentic Applications (2026).
- **githuman** -- Review AI-generated code before committing via GitHuman Docker instances managed by Just recipes (`sjust`/`ajust`). Synced from [mcollina/githuman-skills](https://github.com/mcollina/githuman-skills) with SparkFabrik-specific commands, review workflow, and troubleshooting.
- **auto-format-doc** -- Auto-format files after creating or modifying them using external formatters managed by Just recipes (`sjust`/`ajust`). Currently supports Markdown via Prettier.
- **sf-create-agentsmd** -- Discovery-driven AGENTS.md generator and reviewer for projects following team conventions. Detects project structure, languages, package managers, task runners, and Docker setup, then generates or audits an AGENTS.md with supply chain safety, command safety policy, git workflow, and OpenSpec conventions.
- **sf-commit-convention** -- Enforce SparkFabrik commit message conventions: conventional commits (preferred) with automatic legacy format fallback via git hook detection, mandatory issue references, and `Assisted-by` AI trailer.
