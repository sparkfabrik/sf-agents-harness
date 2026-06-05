## Context

The `security-audit` skill audits application code for traditional web security vulnerabilities (SQL injection, XSS, CSRF, dependency CVEs, etc.) using a five-phase workflow with automated scanners and LLM-guided manual review.

A growing number of codebases now include AI agent configurations — instruction files (`.github/copilot-instructions.md`, `AGENTS.md`, `.cursorrules`), MCP server configs, custom skills, and LLM integration code (prompt construction, tool definitions, RAG pipelines). These create a new attack surface that the existing skill does not address.

The OWASP Top 10 for Agentic Applications (2026) formalizes ten risk categories specific to AI/agentic systems (ASI01-ASI10). No structured audit skill exists to check for these in real codebases.

## Goals / Non-Goals

**Goals:**

- Provide a structured audit workflow for AI/agentic security concerns, complementary to the existing `security-audit` skill.
- Cover four audit areas: instruction files, tool configuration, LLM integration code, and trust boundaries.
- Map the review checklist to the OWASP Agentic Top 10 with concrete code-level patterns.
- Produce a self-contained markdown report presentable to technical leads or clients.
- Detect AI/agentic integration automatically by reading project files and dependencies.

**Non-Goals:**

- Replacing or modifying the existing `security-audit` skill. The two skills are independent and complementary.
- Automated scanning via Docker containers. This skill is primarily LLM-driven manual review — the automated tooling for agentic security is still nascent.
- Auditing the AI model itself (training data poisoning, model extraction). This skill audits the integration and configuration layer, not the model.
- Covering multi-agent orchestration platforms (Kubernetes-based agent fleets, cloud-native agent services). The focus is on developer-facing codebases.

## Decisions

### Decision 1: Two-phase workflow (Discovery + Review), not five-phase

Unlike the `security-audit` skill which has five phases (discovery, container generation, native scans, Docker scans, manual review), this skill uses a simpler two-phase approach: discovery and LLM-driven review. There's no automated scanning phase because mature automated tools for agentic security don't exist yet. Semgrep has limited prompt injection rules, but the bulk of the audit is pattern recognition in natural language instruction files and code — exactly what LLM review excels at.

A third phase (report generation) writes the findings to a file.

**Alternative considered**: Attempting to integrate semgrep or custom regex scanning for prompt injection patterns. Rejected as premature — the patterns are too varied and context-dependent for regex. The LLM review is more effective and the reference files give it the knowledge to do it well.

### Decision 2: Discovery detects AI integration from files and dependencies

The skill detects AI/agentic integration by checking for:

| Indicator                                                                    | What it means                     |
| ---------------------------------------------------------------------------- | --------------------------------- |
| `.github/copilot-instructions.md`                                            | GitHub Copilot instructions       |
| `AGENTS.md`                                                                  | Agent instructions (multi-tool)   |
| `.cursorrules` / `.cursorignore`                                             | Cursor AI configuration           |
| `.opencode/` directory                                                       | OpenCode configuration and skills |
| `.aider.conf.yml`                                                            | Aider configuration               |
| `.mcp.json`, `mcp.config.*`                                                  | MCP server configurations         |
| `SKILL.md` files in project                                                  | Custom agent skills               |
| `openai`, `anthropic`, `langchain`, `llamaindex`, `crewai` in dependencies   | LLM SDK usage                     |
| `drupal/ai`, `drupal/openai` in composer.json                                | Drupal AI modules                 |
| `chromadb`, `pinecone-client`, `weaviate-client`, `pgvector` in dependencies | Vector DB / RAG                   |
| `.env` with `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.                      | LLM API credentials               |
| Prompt template files (`prompts/`, `*.prompt`, `*.prompt.md`)                | Prompt templates                  |

Discovery does not require user input about invocation methods (unlike `security-audit`) since there are no tools to run — the LLM reads the files directly.

### Decision 3: Checklist maps 1:1 to OWASP Agentic Top 10

The Phase 2 review checklist has one category per ASI item (ASI01-ASI10). Each category includes specific things to look for in code, derived from the OWASP descriptions and adapted to the file-level patterns found in real codebases.

Not all categories will apply to every project. The skill determines applicability based on discovery results:

| Category                   | Applies when                                          |
| -------------------------- | ----------------------------------------------------- |
| ASI01 Behaviour Hijack     | LLM integration code found (prompt construction)      |
| ASI02 Tool Misuse          | MCP configs or tool definitions found                 |
| ASI03 Identity & Privilege | LLM integration with auth/session context             |
| ASI04 Supply Chain         | Instruction files, MCP configs, prompt templates      |
| ASI05 Code Execution       | Agent with code generation/execution capability       |
| ASI06 Memory Poisoning     | Vector DB dependencies or RAG pipelines               |
| ASI07 Inter-Agent Comms    | Multi-agent framework dependencies (crewai, autogen)  |
| ASI08 Cascading Failures   | LLM output used as input to another LLM/tool          |
| ASI09 Human-Agent Trust    | HITL patterns in code (approval gates, confirmations) |
| ASI10 Rogue Agents         | Multi-agent framework or dynamic agent instantiation  |

Categories that don't apply are marked "Not applicable" in the report, not silently skipped.

### Decision 4: Instruction file audit is a dedicated sub-section, not just a checklist item

Instruction files are the most novel and concrete attack surface. They deserve deeper treatment than a single checklist item under ASI04. The skill includes a dedicated section in the review that examines each instruction file for:

- Overly permissive scope (unrestricted file/command access)
- Credential exposure (API keys, tokens in instructions)
- Conflicting instructions (contradictions across files)
- Injection amplification (instructions to follow embedded commands)
- Missing restrictions (no boundaries on what agent should NOT do)
- Stale/abandoned configs (outdated tool configs still present)
- Implicit trust (no validation guidance for LLM outputs)

A reference file (`references/instruction-file-audit.md`) documents the specific patterns per tool (Copilot, Cursor, OpenCode, Aider, MCP).

### Decision 5: Report follows same structure as security-audit

The report at `.agentic-security-audit/report.md` uses the same structure as the `security-audit` report (executive summary, methodology, tools/coverage, findings summary, detailed findings, checklist coverage, recommendations). This makes reports from both skills consistent and combinable for a comprehensive audit deliverable.

## Risks / Trade-offs

**[No automated tooling]** → The skill relies almost entirely on LLM review. This means findings depend on the LLM's quality and the reference files' completeness. Mitigation: the reference files are detailed and grounded in the OWASP Agentic Top 10. As automated tools mature (semgrep rules for prompt injection, dedicated agentic SAST), they can be added as a scanning phase.

**[Rapidly evolving landscape]** → AI tooling (MCP, Copilot instructions, Cursor, etc.) changes fast. New instruction file formats and agent frameworks appear regularly. Mitigation: the discovery detection table is easy to extend. The reference files can be updated independently of the core workflow.

**[Overlap with security-audit]** → Some findings (e.g., credentials in code, missing input validation) could surface in either audit. Mitigation: clear scope boundaries. The `security-audit` skill looks at application code. This skill looks at AI integration and instruction files. If a user runs both, minor overlap in findings is acceptable and expected.

**[Instruction files are natural language]** → Unlike code, instruction files have no formal grammar. "Overly permissive scope" is a judgment call, not a binary check. Mitigation: the reference file provides concrete examples of what "too permissive" looks like, giving the LLM consistent criteria to apply.
