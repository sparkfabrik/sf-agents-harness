---
name: agentic-security-audit
description: 'Audit AI agent configurations, instruction files, and LLM integration code for security risks mapped to the OWASP Top 10 for Agentic Applications (2026). Use when the user wants to audit agentic security, review AI instruction files, check MCP configs, assess prompt injection risks, or evaluate LLM integration trust boundaries. Also use when the user mentions "agentic security", "AI audit", "instruction file review", "MCP security", "prompt injection", "OWASP agentic", "agent trust boundaries", or "AI supply chain".'
---

# Agentic Security Audit Skill

Structured audit for AI agent configurations and LLM integration code. The skill
discovers AI-related files and dependencies, reviews them against the OWASP Top
10 for Agentic Applications (ASI01-ASI10), and produces a markdown report.

This skill is **complementary** to the `security-assessment` skill. That skill audits
application code and the live surface (SQL injection, XSS, dependency CVEs, DAST).
This skill audits the AI integration layer: instruction files, tool configurations,
prompt construction, and trust boundaries.

**Primarily LLM-driven** -- automated tooling for agentic security is still
nascent. The audit relies on structured manual review guided by reference files.

## Before you start

1. Ask the user whether they want a **full audit** (all phases) or a
   **discovery-only** run (Phase 1 only, to understand the AI footprint).
2. Agree on **scope boundaries** upfront: instruction files only, tool configs,
   LLM integration code, or all.

## Phase 1 -- Discovery

Scan the project to identify AI/agentic integration points. Read files directly
-- no tools to invoke in this phase.

### AI instruction file detection

Scan the project for known AI instruction file patterns:

| Pattern                                          | Tool / Purpose                |
| ------------------------------------------------ | ----------------------------- |
| `.github/copilot-instructions.md`                | GitHub Copilot instructions   |
| `AGENTS.md`                                      | Multi-tool agent instructions |
| `.cursorrules`                                   | Cursor AI rules               |
| `.cursorignore`                                  | Cursor AI ignore patterns     |
| `.opencode/` directory                           | OpenCode config and skills    |
| `.aider.conf.yml`                                | Aider configuration           |
| `.mcp.json`, `mcp.config.*`                      | MCP server configurations     |
| `**/SKILL.md`                                    | Custom agent skills           |
| `**/prompts/**`, `**/*.prompt`, `**/*.prompt.md` | Prompt templates              |

### LLM SDK dependency detection

Check package manager files for LLM-related dependencies:

| Dependency                   | Language         | Indicates                     |
| ---------------------------- | ---------------- | ----------------------------- |
| `openai`                     | Python / Node.js | OpenAI API integration        |
| `anthropic`                  | Python / Node.js | Anthropic API integration     |
| `langchain`, `langchain-*`   | Python / Node.js | LangChain agent framework     |
| `llamaindex`, `llama-index`  | Python           | LlamaIndex RAG framework      |
| `crewai`                     | Python           | CrewAI multi-agent framework  |
| `autogen`, `pyautogen`       | Python           | AutoGen multi-agent framework |
| `drupal/ai`, `drupal/openai` | PHP (Composer)   | Drupal AI modules             |
| `@modelcontextprotocol/*`    | Node.js          | MCP SDK                       |

### Vector DB and RAG detection

Check for vector database or retrieval-augmented generation dependencies:

`chromadb`, `pinecone-client`, `weaviate-client`, `pgvector`, `qdrant-client`,
`milvus`, `faiss-cpu`, `faiss-gpu`.

When found, flag ASI06 (Memory Poisoning) as applicable.

### LLM credential detection

Check `.env`, `.env.example`, `.env.local` and similar files for LLM API
credential patterns: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`GOOGLE_AI_API_KEY`, `AZURE_OPENAI_*`, `HUGGINGFACE_TOKEN`.

- **Critical finding**: actual credential values committed to version control.
- **Informational**: `.env.example` with placeholder values (indicates LLM usage,
  not a credential leak).

### Applicability mapping

Based on discovery results, determine which OWASP Agentic Top 10 categories
apply:

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

### Discovery report

Present a structured summary of all findings:

1. AI instruction files found (with file paths)
2. LLM SDK dependencies detected
3. Vector DB / RAG dependencies detected
4. LLM credential indicators found
5. Applicable OWASP Agentic Top 10 categories

Ask the user to confirm before proceeding to Phase 2.

## Phase 2 -- Review

Work through each applicable OWASP Agentic Top 10 category. For each category,
read the relevant files identified in discovery and check against the patterns
in the reference file `references/owasp-agentic-top10.md`.

### Instruction file audit (dedicated sub-section)

Before working through the ASI checklist, audit each instruction file found in
discovery using the patterns in `references/instruction-file-audit.md`. Check
each file for:

- **Overly permissive scope** -- unrestricted file/command access without
  boundaries
- **Credential exposure** -- API keys, tokens, passwords in instruction content
- **Conflicting instructions** -- contradictions between instruction files
- **Injection amplification** -- instructions to follow embedded commands from
  untrusted sources
- **Missing restrictions** -- defines what agent CAN do but omits what it
  should NOT do
- **Stale configurations** -- references deprecated tools, APIs, or patterns
- **Implicit trust** -- no validation guidance for LLM outputs, auto-commit
  without review

### ASI01 -- Agent Behaviour Hijack

Check how user input flows into LLM prompts:

- User input concatenated directly into prompt strings without sanitization
- System prompts that can be overridden by user messages
- No instruction hierarchy enforcement (system vs user vs assistant)
- Missing input validation before prompt construction
- Dynamic goal/instruction modification based on untrusted input

### ASI02 -- Tool Misuse

Check tool definitions and MCP configurations:

- MCP tool definitions with unrestricted file system or network access
- Tool definitions without input validation or schema constraints
- Agents with write access to databases or file systems without approval gates
- Tool chaining that could allow privilege escalation
- Missing rate limiting on tool invocations

### ASI03 -- Identity and Privilege Abuse

Check agent identity and privilege boundaries:

- Agent running with service account or admin credentials
- No per-user scoping of agent actions
- Cached permissions reused across sessions
- Delegation without scope reduction
- Agent actions not attributed to the requesting user in audit logs

### ASI04 -- Supply Chain Vulnerabilities

Check supply chain risks in AI configurations:

- Instruction files not covered by code review process
- Prompt templates loaded from external URLs at runtime
- MCP tools from untrusted or unverified sources
- No integrity checks on agent configurations
- Dynamic plugin or skill loading from unvetted repositories

### ASI05 -- Unexpected Code Execution

Check code execution risks in agent configurations:

- Agent configured with ability to run `eval()`, `exec()`, or shell commands
- Generated code executed without sandboxing or review
- No static analysis applied to AI-generated code before execution
- Unsafe deserialization of agent-produced data
- Dynamic import or require statements influenced by LLM output

### ASI06 -- Memory and Context Poisoning

Check when vector DB or memory systems are detected:

- User input stored in vector DB without validation or sanitization
- RAG retrieval results treated as authoritative without source attribution
- No access control on memory read/write operations
- Cross-user memory contamination (shared memory without session isolation)
- No anomaly detection on memory insertions

### ASI07 -- Insecure Inter-Agent Communication

Check when multi-agent frameworks are detected:

- Unsigned or unvalidated messages between agents
- No schema enforcement on delegation payloads
- Shared memory or context without access control between agents
- Agent-to-agent trust assumed without verification

### ASI08 -- Cascading Hallucination Failures

Check for hallucination propagation risks:

- LLM output used as input to another LLM without validation
- No grounding or fact-checking layer between LLM calls
- Hallucinated output persisted to database or memory
- Self-referencing loops where agent output feeds back into its own context
- No confidence scoring or uncertainty indicators on LLM outputs

### ASI09 -- Human-Agent Trust Exploitation

Check human oversight mechanisms:

- No approval gate on high-impact agent actions (deletes, sends, purchases)
- Bulk approval interfaces that obscure individual action risk
- Agent can bypass human-in-the-loop via delegation or fallback paths
- Missing audit trail for agent actions approved by humans
- Confidence inflation in agent summaries presented to reviewers

### ASI10 -- Rogue Agents

Check when dynamic agent instantiation or multi-agent systems are detected:

- No agent attestation or allowlisting mechanism
- Dynamic agent instantiation from untrusted sources
- No monitoring or logging of agent behavior
- Missing identity verification for agents joining workflows
- No anomaly detection on agent actions

### Non-applicable categories

For categories that don't apply based on discovery results, mark them as
"Not applicable" in the report with a brief explanation (e.g., "Not applicable
-- no vector DB or RAG integration detected"). Do not silently skip them.

## Phase 3 -- Report

Write the full audit report to `.agentic-security-audit/report.md`.

### Report structure

1. **Metadata table**: project name, date, scope, AI stacks detected, audit type
2. **Executive summary**: 2-4 sentences on overall agentic security posture
3. **Methodology**: description of the two-phase approach (discovery + review)
4. **Discovery results**: AI files found, dependencies detected, applicable
   categories
5. **Findings summary**: table with finding count per severity (Critical, High,
   Medium, Low, Info)
6. **Detailed findings**: one section per finding, ordered by severity
   (Critical first), each with:
   - Severity
   - Location (file path and line if applicable)
   - OWASP category (ASI01-ASI10)
   - Description
   - Impact
   - Evidence (code snippet or config excerpt)
   - Recommendation
7. **Checklist coverage**: table showing each ASI category, its status
   (Reviewed / Not applicable), and notes
8. **Recommendations**: prioritized list (Immediate / Short-term / Ongoing)

### After writing the report

Show the executive summary and findings summary table in the chat as a preview.
Inform the user of the full report path: `.agentic-security-audit/report.md`.
