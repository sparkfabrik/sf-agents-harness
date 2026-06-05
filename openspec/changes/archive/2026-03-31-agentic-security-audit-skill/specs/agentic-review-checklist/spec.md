## ADDED Requirements

### Requirement: Review checklist maps to OWASP Agentic Top 10

The skill SHALL include a review checklist with one category per OWASP Agentic Top 10 item (ASI01 through ASI10). Each category SHALL list specific things to look for in code and configuration files.

#### Scenario: Full audit on project with LLM integration

- **WHEN** the user requests a full audit and discovery detected LLM SDK dependencies
- **THEN** the skill SHALL work through all applicable checklist categories, reading relevant code for each

### Requirement: ASI01 Behaviour Hijack review

The skill SHALL check for prompt injection vulnerabilities by examining how user input flows into LLM prompts.

Items to check:

- User input concatenated directly into prompt strings without sanitization
- System prompts that can be overridden by user messages
- No instruction hierarchy enforcement (system vs user vs assistant)
- Missing input validation before prompt construction
- Dynamic goal/instruction modification based on untrusted input

#### Scenario: User input concatenated into prompt

- **WHEN** the LLM finds code that concatenates `$_GET`, `$_POST`, or request parameters directly into an LLM prompt string
- **THEN** it SHALL flag this as a prompt injection risk under ASI01

### Requirement: ASI02 Tool Misuse review

The skill SHALL check for overly broad or unvalidated tool definitions that agents can invoke.

Items to check:

- MCP tool definitions with unrestricted file system or network access
- Tool definitions without input validation or schema constraints
- Agents with write access to databases or file systems without approval gates
- Tool chaining that could allow privilege escalation
- Missing rate limiting on tool invocations

#### Scenario: MCP config with unrestricted filesystem tool

- **WHEN** `.mcp.json` defines a tool that can read/write arbitrary file paths without restrictions
- **THEN** it SHALL flag this as a tool misuse risk under ASI02

### Requirement: ASI03 Identity and Privilege review

The skill SHALL check for agent identity and privilege boundary issues.

Items to check:

- Agent running with service account or admin credentials
- No per-user scoping of agent actions
- Cached permissions reused across sessions
- Delegation without scope reduction
- Agent actions not attributed to the requesting user in audit logs

#### Scenario: Agent uses shared admin API key

- **WHEN** LLM integration code uses a single admin-level API key for all agent operations regardless of the requesting user
- **THEN** it SHALL flag this as a privilege abuse risk under ASI03

### Requirement: ASI04 Supply Chain review

The skill SHALL check for supply chain risks in AI configurations and instruction files.

Items to check:

- Instruction files not covered by code review process
- Prompt templates loaded from external URLs at runtime
- MCP tools from untrusted or unverified sources
- No integrity checks on agent configurations
- Dynamic plugin or skill loading from unvetted repositories

#### Scenario: Prompt template fetched from external URL

- **WHEN** code fetches a prompt template from an external URL at runtime without integrity verification
- **THEN** it SHALL flag this as a supply chain risk under ASI04

### Requirement: ASI05 Unexpected Code Execution review

The skill SHALL check for code execution risks in agent configurations.

Items to check:

- Agent configured with ability to run `eval()`, `exec()`, or shell commands
- Generated code executed without sandboxing or review
- No static analysis applied to AI-generated code before execution
- Unsafe deserialization of agent-produced data
- Dynamic import or require statements influenced by LLM output

#### Scenario: Agent can execute shell commands

- **WHEN** an MCP tool or agent configuration grants shell execution capability
- **THEN** it SHALL flag this as a code execution risk under ASI05

### Requirement: ASI06 Memory and Context Poisoning review

The skill SHALL check for memory and RAG poisoning risks when vector DB or memory systems are detected.

Items to check:

- User input stored in vector DB without validation or sanitization
- RAG retrieval results treated as authoritative without source attribution
- No access control on memory read/write operations
- Cross-user memory contamination (shared memory without session isolation)
- No anomaly detection on memory insertions

#### Scenario: User input stored directly in vector DB

- **WHEN** code inserts user-provided content into a vector store without validation
- **THEN** it SHALL flag this as a memory poisoning risk under ASI06

### Requirement: ASI07 Inter-Agent Communication review

The skill SHALL check for insecure inter-agent communication when multi-agent frameworks are detected.

Items to check:

- Unsigned or unvalidated messages between agents
- No schema enforcement on delegation payloads
- Shared memory or context without access control between agents
- Agent-to-agent trust assumed without verification

#### Scenario: Multi-agent framework without message validation

- **WHEN** CrewAI or AutoGen agents pass tasks to each other without schema validation on the payload
- **THEN** it SHALL flag this as an inter-agent communication risk under ASI07

### Requirement: ASI08 Cascading Failures review

The skill SHALL check for hallucination propagation and cascading failure risks.

Items to check:

- LLM output used as input to another LLM without validation
- No grounding or fact-checking layer between LLM calls
- Hallucinated output persisted to database or memory
- Self-referencing loops where agent output feeds back into its own context
- No confidence scoring or uncertainty indicators on LLM outputs

#### Scenario: LLM output piped into another LLM

- **WHEN** the output of one LLM call is directly used as input to another without validation
- **THEN** it SHALL flag this as a cascading failure risk under ASI08

### Requirement: ASI09 Human-Agent Trust Exploitation review

The skill SHALL check for weaknesses in human oversight mechanisms.

Items to check:

- No approval gate on high-impact agent actions (deletes, sends, purchases)
- Bulk approval interfaces that obscure individual action risk
- Agent can bypass human-in-the-loop via delegation or fallback paths
- Missing audit trail for agent actions approved by humans
- Confidence inflation in agent summaries presented to reviewers

#### Scenario: No approval gate on destructive actions

- **WHEN** an agent can perform delete or send operations without requiring human confirmation
- **THEN** it SHALL flag this as a human-agent trust risk under ASI09

### Requirement: ASI10 Rogue Agents review

The skill SHALL check for rogue agent risks when dynamic agent instantiation or multi-agent systems are detected.

Items to check:

- No agent attestation or allowlisting mechanism
- Dynamic agent instantiation from untrusted sources
- No monitoring or logging of agent behavior
- Missing identity verification for agents joining workflows
- No anomaly detection on agent actions

#### Scenario: Dynamic agent loading without verification

- **WHEN** code instantiates agents from configuration files or external sources without verification
- **THEN** it SHALL flag this as a rogue agent risk under ASI10

### Requirement: Skip non-applicable categories gracefully

The skill SHALL mark categories as "Not applicable" in the report when discovery indicates they don't apply to the project, rather than silently skipping them.

#### Scenario: No vector DB in project

- **WHEN** discovery found no vector DB dependencies
- **THEN** ASI06 (Memory Poisoning) SHALL be marked "Not applicable — no vector DB or RAG integration detected" in the checklist coverage
