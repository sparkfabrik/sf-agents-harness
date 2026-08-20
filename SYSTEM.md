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

- **the-architect** -- Conversational AI oracle for discovery, brainstorming, architecture, and general knowledge. Not a code agent.

## Available skills

- **glab** -- GitLab CLI skill for working with issues, merge requests, CI/CD pipelines, and repositories via the `glab` CLI.
- **gh** -- GitHub CLI skill for working with issues, pull requests, Actions workflows, releases, and repositories via the `gh` CLI.
- **create-gitlab-issue** -- Turn a short task description into a grounded GitLab issue. Audits git state, open issues and MRs, in-flight specs, and the relevant source files first, resolves host, labels, attribution, and test gates at runtime, and defers to the `glab` skill for the API calls.
- **playwright-cli** -- Browser automation with the `playwright-cli` CLI tool for web testing, screenshots, form filling, and data extraction. Synced from [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) with custom output file conventions.
- **skill-creator** -- Create, iterate, and benchmark agent skills with eval-driven workflows. Synced from [anthropics/skills](https://github.com/anthropics/skills) with custom tool-agnostic usage guidance.
- **doc-coauthoring** -- Structured workflow for co-authoring documentation, proposals, and technical specs. Synced from [anthropics/skills](https://github.com/anthropics/skills).
- **grilling** -- Stress-test a plan, decision, or idea through rounds of design-tree questions. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **grill-me** -- Explicit entry point that starts a `grilling` session to sharpen a plan or design. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **domain-modeling** -- Build and maintain domain glossaries, challenge ambiguous terminology, and record qualifying architecture decisions. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **grill-with-docs** -- Explicit entry point that combines `grilling` with `domain-modeling` to update glossaries and qualifying ADRs during the interview. Synced from [mattpocock/skills](https://github.com/mattpocock/skills).
- **security-assessment** -- Orchestrate a full security engagement split into a Vulnerability Assessment track (static code/dependency scanning, discovery, Docker scan containers, manual review) and a Penetration Testing track (live recon and exploitation against a running target), then merge both into one standalone HTML report via a bundled template and parser script. Open-source tools only.
- **agentic-security-audit** -- Audit AI agent configurations, instruction files, and LLM integration code for security risks mapped to the OWASP Top 10 for Agentic Applications (2026).
- **githuman** -- Review AI-generated code before committing via GitHuman Docker instances managed by Just recipes (`sjust`/`ajust`). Synced from [mcollina/githuman-skills](https://github.com/mcollina/githuman-skills) with SparkFabrik-specific commands, review workflow, and troubleshooting.
- **auto-format-doc** -- Auto-format files after creating or modifying them using external formatters managed by Just recipes (`sjust`/`ajust`). Currently supports Markdown via Prettier.
- **sf-container-build** -- Design, modify, review, and debug Dockerfiles and container build pipelines with explicit platform contracts, multi-platform runtime tests, supply-chain controls, cache guidance, and SparkFabrik image conventions.
- **sf-create-agentsmd** -- Discovery-driven AGENTS.md generator and reviewer for projects following team conventions. Detects project structure, languages, package managers, task runners, and Docker setup, then generates or audits an AGENTS.md with supply chain safety, command safety policy, git workflow, and OpenSpec conventions.
- **sf-commit-convention** -- Enforce SparkFabrik commit message conventions: conventional commits (preferred) with automatic legacy format fallback via git hook detection, mandatory issue references, and `Assisted-by` AI trailer.
- **sf-writing-style** -- Canonical SparkFabrik writing style for all markdown and prose artifacts: aired short paragraphs, bulleted lists with bold lead-ins, total em/en-dash ban, AI-slop blacklist, before/after rewrite examples.
- **mermaid-diagrams** -- Create clear, well-designed Mermaid diagrams in Markdown documents (READMEs, ADRs, design docs, RFCs). Covers flowcharts, sequence, ER, class, state, and C4/architecture diagrams with eight design principles and render-verify guidance.
- **spark-http-proxy** -- Configure, run, and troubleshoot the Traefik-based Spark HTTP Proxy for local development: expose containers via `VIRTUAL_HOST`/`VIRTUAL_PORT` or native `traefik.*` labels, generate browser-trusted certificates with `mkcert`, and configure `*.loc` DNS resolution.
- **postmortem-writing** -- Guide engineers and product managers through writing blameless postmortems for software incidents and product failures. Produces a structured record covering summary, quantified impact, UTC timeline, detection, root cause and contributing factors (Five Whys), resolution, and specific owned action items.
- **adr-creator** -- Guided conversational workflow for writing Architecture Decision Records in Michael Nygard's format, from context and options through the chosen decision and its consequences.
- **adversarial-verify** -- Adversarial verification of code, architecture, data, documentation, tests, and analysis via Chain-of-Verification: red-teaming, hidden behavior probing, stress techniques, tri-modal reasoning, and anti-fabrication discipline.
- **figma-bridge** -- Generic Figma access layer for other skills and workflows: URL parsing, Figma MCP tool usage, and adaptive design-token mapping that loads the project's `figma-token-mapping.md` when present and falls back to raw Figma values otherwise.
