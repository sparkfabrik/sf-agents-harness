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
skills across all categories and system agents. It is consumed by `sparkdock-agents-status` to display
a DESCRIPTION column in the terminal table. The schema is defined in
`config/catalog.schema.json`.

When adding or modifying a system skill or agent, update the catalog entry too.

## Available agents

- **the-architect** -- Conversational AI oracle for discovery, brainstorming, architecture, and general knowledge. Not a code agent.

## Available skills

- **glab** -- GitLab CLI skill for working with issues, merge requests, CI/CD pipelines, and repositories via the `glab` CLI.
- **gh** -- GitHub CLI skill for working with issues, pull requests, Actions workflows, releases, and repositories via the `gh` CLI.
- **playwright-cli** -- Browser automation with the `playwright-cli` CLI tool for web testing, screenshots, form filling, and data extraction. Synced from [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) with custom output file conventions.
- **skill-creator** -- Create, iterate, and benchmark agent skills with eval-driven workflows. Synced from [anthropics/skills](https://github.com/anthropics/skills) with custom tool-agnostic usage guidance.
- **doc-coauthoring** -- Structured workflow for co-authoring documentation, proposals, and technical specs. Synced from [anthropics/skills](https://github.com/anthropics/skills).
- **grilling** -- Stress-test a plan, decision, or idea through rounds of design-tree questions. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **grill-me** -- Explicit entry point that starts a `grilling` session to sharpen a plan or design. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **githuman** -- Review AI-generated code before committing via GitHuman Docker instances managed by Just recipes (`sjust`/`ajust`). Synced from [mcollina/githuman-skills](https://github.com/mcollina/githuman-skills) with SparkFabrik-specific commands, review workflow, and troubleshooting.
- **auto-format-doc** -- Auto-format files after creating or modifying them using external formatters managed by Just recipes (`sjust`/`ajust`). Currently supports Markdown via Prettier.
- **sf-container-build** -- Design, modify, review, and debug Dockerfiles and container build pipelines with explicit platform contracts, multi-platform runtime tests, supply-chain controls, cache guidance, and SparkFabrik image conventions.
- **sf-create-agentsmd** -- Discovery-driven AGENTS.md generator and reviewer for projects following team conventions. Detects project structure, languages, package managers, task runners, and Docker setup, then generates or audits an AGENTS.md with supply chain safety, command safety policy, git workflow, and OpenSpec conventions.
- **sf-commit-convention** -- Enforce SparkFabrik commit message conventions: conventional commits (preferred) with automatic legacy format fallback via git hook detection, mandatory issue references, and `Assisted-by` AI trailer.
- **sf-writing-style** -- Short, plain writing for issues, PR/MR descriptions, comments, changelogs, and documents. Focus on what changes; omit implementation stories and padding. Defines how SparkFabrik sounds for each kind of reader, the patterns of machine-written text to avoid, and the voice of documents for clients, in Italian and English.
- **spark-http-proxy** -- Configure, run, and troubleshoot the Traefik-based Spark HTTP Proxy for local development: expose containers via `VIRTUAL_HOST`/`VIRTUAL_PORT` or native `traefik.*` labels, generate browser-trusted certificates with `mkcert`, and configure `*.loc` DNS resolution.
- **adr-creator** -- Guided conversational workflow for writing Architecture Decision Records in Michael Nygard's format, from context and options through the chosen decision and its consequences.
- **adversarial-verify** -- Adversarial verification of code, architecture, data, documentation, tests, and analysis via Chain-of-Verification: red-teaming, hidden behavior probing, stress techniques, tri-modal reasoning, and anti-fabrication discipline.
