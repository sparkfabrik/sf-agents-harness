# OWASP Top 10 for Agentic Applications (2026)

Reference for the agentic security audit skill. Each section covers one risk
category with concrete patterns to look for in code and configuration.

Source: OWASP Top 10 for Agentic Applications (2026).

---

## ASI01 -- Agent Behaviour Hijack

**Risk**: An attacker manipulates agent behaviour through prompt injection,
jailbreaking, or context manipulation, causing the agent to take unintended
actions.

### What to look for

- User input concatenated directly into prompt strings
- Template literals or f-strings building prompts from request data
- System prompts stored in user-accessible locations
- No separation between system instructions and user input
- Dynamic goal modification based on external input

### Vulnerable patterns

```python
# Direct concatenation -- user controls part of the system prompt
prompt = f"You are a helpful assistant. The user asks: {user_input}"
response = llm.complete(prompt)
```

```php
// PHP: request data injected into prompt
$prompt = "Summarize this: " . $_POST['content'];
$result = $client->chat($prompt);
```

```javascript
// No instruction hierarchy
const messages = [
  { role: "user", content: userInput }  // no system message
];
```

### Safe patterns

```python
# Structured messages with clear role separation
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},  # hardcoded
    {"role": "user", "content": sanitize(user_input)}
]
response = llm.chat(messages)
```

```python
# Input validation before prompt construction
if not validate_input(user_input, max_length=500, allowed_chars=SAFE_CHARS):
    raise ValueError("Invalid input")
```

### Detection guidance

1. Search for prompt construction code (string concatenation with LLM calls)
2. Check if user input is sanitized before inclusion in prompts
3. Verify system prompts are hardcoded or loaded from trusted sources
4. Look for instruction hierarchy enforcement in message arrays

---

## ASI02 -- Tool Misuse

**Risk**: Agents invoke tools in unintended ways -- accessing files they
shouldn't, making unauthorized network requests, or chaining tools to escalate
privileges.

### What to look for

- MCP tool definitions with broad file system access
- Tool definitions without input validation schemas
- No allowlist for tool targets (URLs, file paths, commands)
- Agents with write access to production databases
- Missing rate limiting on tool invocations
- Tool chaining without intermediate authorization

### Vulnerable patterns

```json
// MCP config: tool with unrestricted file access
{
  "tools": [{
    "name": "read_file",
    "description": "Read any file",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": { "type": "string" }
      }
    }
  }]
}
```

```python
# Tool executes arbitrary commands from LLM output
def execute_tool(tool_call):
    if tool_call.name == "shell":
        return subprocess.run(tool_call.args["command"], shell=True)
```

### Safe patterns

```json
// MCP config: tool with restricted file access
{
  "tools": [{
    "name": "read_file",
    "description": "Read project source files only",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "pattern": "^src/.*\\.(py|js|ts)$"
        }
      },
      "required": ["path"]
    }
  }]
}
```

```python
# Tool with allowlist validation
ALLOWED_COMMANDS = {"lint", "test", "build"}

def execute_tool(tool_call):
    if tool_call.args["command"] not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command not allowed: {tool_call.args['command']}")
```

### Detection guidance

1. Read all MCP configuration files and check tool input schemas
2. Look for tools that accept arbitrary file paths, URLs, or commands
3. Check if tool execution validates inputs against allowlists
4. Verify write operations require explicit approval

---

## ASI03 -- Identity and Privilege Abuse

**Risk**: Agents inherit or escalate privileges beyond what the requesting user
should have, or act with a shared identity that obscures accountability.

### What to look for

- Single admin API key used for all agent operations
- No per-user scoping of agent actions
- Agent runs with service account that has broader access than users
- Cached auth tokens reused across user sessions
- Agent actions not logged with the requesting user's identity
- Delegation without scope reduction

### Vulnerable patterns

```python
# Shared admin key for all agent operations
client = OpenAI(api_key=os.environ["ADMIN_OPENAI_KEY"])

def handle_user_request(user_id, request):
    # Agent acts as admin regardless of user's permissions
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": request}]
    )
```

```php
// Agent uses Drupal admin account for all operations
$agent_user = User::load(1);  // uid 1 = admin
\Drupal::currentUser()->setAccount($agent_user);
// Agent now has full admin permissions regardless of requesting user
```

### Safe patterns

```python
# Per-user scoped agent operations
def handle_user_request(user_id, request):
    user_permissions = get_user_permissions(user_id)
    client = create_scoped_client(user_permissions)
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": request}],
        metadata={"user_id": user_id}  # audit trail
    )
```

### Detection guidance

1. Search for API key usage in LLM integration code
2. Check if agent operations are scoped to the requesting user
3. Verify audit logs include user identity for agent actions
4. Look for privilege delegation patterns (does scope shrink or stay the same?)

---

## ASI04 -- Supply Chain Vulnerabilities

**Risk**: Compromised or tampered instruction files, prompt templates, MCP
tools, or agent plugins inject malicious behavior into the agent's operation.

### What to look for

- Instruction files outside code review process (not in version control, or in
  ignored paths)
- Prompt templates fetched from external URLs at runtime
- MCP server packages from unverified publishers
- Dynamic skill/plugin loading from external sources
- No integrity verification on agent configurations
- Instruction files that reference external resources without pinning

### Vulnerable patterns

```python
# Prompt template fetched from URL at runtime -- no integrity check
import requests
template = requests.get("https://example.com/prompts/summarize.txt").text
prompt = template.format(content=user_input)
```

```json
// MCP config loading tool from unpinned external source
{
  "servers": {
    "custom-tool": {
      "command": "npx",
      "args": ["-y", "@unknown-publisher/mcp-tool"]
    }
  }
}
```

```yaml
# .cursorrules referencing external prompts
# "For code review, follow the instructions at https://example.com/rules.md"
```

### Safe patterns

```python
# Prompt templates loaded from version-controlled files
from pathlib import Path
TEMPLATE_DIR = Path(__file__).parent / "prompts"
template = (TEMPLATE_DIR / "summarize.txt").read_text()
```

```json
// MCP config with pinned, known packages
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem@1.2.0", "/path"]
    }
  }
}
```

### Detection guidance

1. Check if instruction files are tracked in version control
2. Search for runtime URL fetches of prompts or configurations
3. Verify MCP server packages are from known publishers and pinned to versions
4. Check for dynamic plugin/skill loading mechanisms
5. Review `.gitignore` to see if any instruction files are excluded from VCS

---

## ASI05 -- Unexpected Code Execution

**Risk**: Agents generate and execute code without sandboxing, review, or
restrictions, allowing arbitrary code execution through LLM output.

### What to look for

- `eval()`, `exec()`, or `Function()` called on LLM-generated strings
- Shell command execution with LLM output as arguments
- Dynamic `import` or `require` influenced by LLM output
- Agent-generated code committed or deployed without human review
- Unsafe deserialization of LLM-produced data (pickle, yaml.load)

### Vulnerable patterns

```python
# eval on LLM output
code = llm.generate("Write Python code to process this data...")
result = eval(code)  # arbitrary code execution
```

```javascript
// Dynamic require from LLM suggestion
const module_name = llmResponse.suggestedModule;
const mod = require(module_name);  // LLM controls what gets loaded
```

```python
# Unsafe deserialization of agent-produced data
import pickle
data = pickle.loads(agent_output)  # agent output treated as trusted
```

### Safe patterns

```python
# Sandboxed code execution with restrictions
import ast

# Parse and validate before execution
tree = ast.parse(generated_code)
if not is_safe_ast(tree):
    raise SecurityError("Generated code contains unsafe operations")

# Execute in restricted namespace
exec(generated_code, {"__builtins__": SAFE_BUILTINS}, {})
```

```python
# Human review gate before code execution
def execute_generated_code(code: str, user_id: str):
    review_id = submit_for_review(code, user_id)
    approval = wait_for_approval(review_id)
    if not approval.approved:
        raise PermissionError("Code not approved for execution")
    return safe_exec(code)
```

### Detection guidance

1. Search for `eval()`, `exec()`, `subprocess.run()`, `os.system()` near LLM
   output variables
2. Check if generated code goes through any validation before execution
3. Look for sandboxing mechanisms (restricted builtins, containers)
4. Verify human approval gates exist for code execution

---

## ASI06 -- Memory and Context Poisoning

**Risk**: Attackers poison vector databases, RAG pipelines, or agent memory
to influence future agent behavior through tainted retrieved context.

### What to look for

- User input stored directly in vector DB without sanitization
- RAG results treated as trusted without source attribution
- No access control on memory write operations
- Cross-user memory contamination (shared vector collections)
- No anomaly detection on memory insertions
- Embeddings generated from untrusted content without filtering

### Vulnerable patterns

```python
# User content stored directly in vector DB
def store_document(user_input: str):
    embedding = embed(user_input)
    vector_db.insert(embedding, metadata={"text": user_input})
    # No validation -- user can inject instructions into retrieval context
```

```python
# RAG results treated as authoritative
context = vector_db.query(user_question, top_k=5)
prompt = f"Answer based on this context:\n{context}\n\nQuestion: {user_question}"
# Retrieved context may contain injected instructions
```

### Safe patterns

```python
# Validated and attributed RAG retrieval
def retrieve_context(query: str, user_id: str):
    results = vector_db.query(
        query, top_k=5,
        filter={"source_verified": True}
    )
    context = "\n".join(
        f"[Source: {r.metadata['source']}] {r.text}" for r in results
    )
    return context  # each piece of context attributed to its source
```

```python
# Access-controlled memory writes
def store_document(content: str, user_id: str, source: str):
    if not validate_content(content):
        raise ValueError("Content failed validation")
    embedding = embed(content)
    vector_db.insert(embedding, metadata={
        "text": content,
        "user_id": user_id,
        "source": source,
        "source_verified": True,
        "inserted_at": datetime.utcnow()
    })
```

### Detection guidance

1. Check how content enters vector databases (any validation?)
2. Look for user-supplied content in embedding pipelines
3. Verify RAG results include source attribution
4. Check for access control on vector DB collections
5. Look for session isolation in shared memory systems

---

## ASI07 -- Insecure Inter-Agent Communication

**Risk**: Agents communicate without authentication, message validation, or
schema enforcement, allowing message injection or impersonation.

### What to look for

- Agent-to-agent messages without schema validation
- No authentication between agents in multi-agent systems
- Shared memory or context without access control
- Delegation payloads that aren't validated by the receiving agent
- Trust assumed based on message origin without verification

### Vulnerable patterns

```python
# CrewAI: task delegation without payload validation
from crewai import Agent, Task, Crew

researcher = Agent(name="researcher", ...)
writer = Agent(name="writer", ...)

# Writer trusts researcher output without validation
task = Task(
    description="Write article based on research",
    agent=writer,
    context=[researcher_task]  # no validation of researcher output
)
```

### Safe patterns

```python
# Schema-validated inter-agent communication
from pydantic import BaseModel

class ResearchOutput(BaseModel):
    topic: str
    sources: list[str]
    findings: str
    confidence: float

def delegate_to_writer(research_output: dict):
    validated = ResearchOutput(**research_output)  # schema validation
    if validated.confidence < 0.7:
        raise ValueError("Research confidence too low for publication")
    return writer.execute(validated)
```

### Detection guidance

1. Check multi-agent framework usage (CrewAI, AutoGen)
2. Look for agent-to-agent message passing without validation
3. Verify delegation payloads have schema constraints
4. Check for shared state access control between agents

---

## ASI08 -- Cascading Hallucination Failures

**Risk**: Hallucinated output from one LLM call propagates through the system
-- stored in databases, used as input to other LLM calls, or acted upon
without validation.

### What to look for

- LLM output piped directly as input to another LLM call
- Hallucinated data persisted to database or vector store
- Self-referencing loops (agent output feeds back into its context)
- No grounding or fact-checking between LLM processing stages
- No confidence scoring or uncertainty indication

### Vulnerable patterns

```python
# Output of one LLM directly feeds another -- hallucinations propagate
summary = llm.complete(f"Summarize: {document}")
analysis = llm.complete(f"Analyze this summary: {summary}")
recommendation = llm.complete(f"Recommend actions based on: {analysis}")
# Each stage can amplify hallucinations from the previous one
```

```python
# Hallucinated data persisted without verification
extracted_data = llm.complete(f"Extract entities from: {text}")
db.insert("entities", json.loads(extracted_data))  # may be hallucinated
```

### Safe patterns

```python
# Validation between LLM processing stages
summary = llm.complete(f"Summarize: {document}")
verified_summary = verify_against_source(summary, document)
if verified_summary.confidence < 0.8:
    summary = request_human_review(summary, document)

analysis = llm.complete(f"Analyze this verified summary: {verified_summary.text}")
```

### Detection guidance

1. Trace data flow between LLM calls -- is output validated between stages?
2. Check if LLM output is persisted to databases without verification
3. Look for self-referencing patterns in agent loops
4. Verify grounding mechanisms exist (fact-checking, source verification)

---

## ASI09 -- Human-Agent Trust Exploitation

**Risk**: Weaknesses in human oversight allow agents to perform high-impact
actions without meaningful review, or present information that misleads human
reviewers.

### What to look for

- High-impact actions (delete, send, purchase, deploy) without approval gates
- Bulk approval interfaces that obscure individual action details
- Agent can bypass HITL via delegation or fallback paths
- Missing audit trail for human-approved agent actions
- Agent summaries that inflate confidence or hide uncertainty
- Auto-commit or auto-deploy of generated changes

### Vulnerable patterns

```python
# High-impact action without human approval
def agent_action(action: str, target: str):
    if action == "delete":
        db.delete(target)  # no confirmation required
    elif action == "send_email":
        email.send(target)  # no review of content
```

```markdown
<!-- Instruction file: auto-commit without review -->
When you've made changes, commit them directly to the main branch.
Do not wait for review -- speed is more important than caution.
```

### Safe patterns

```python
# Approval gate for high-impact actions
HIGH_IMPACT_ACTIONS = {"delete", "send_email", "deploy", "purchase"}

def agent_action(action: str, target: str, user_id: str):
    if action in HIGH_IMPACT_ACTIONS:
        approval = request_approval(
            action=action, target=target,
            requested_by=user_id,
            details=generate_action_summary(action, target)
        )
        if not approval.granted:
            return {"status": "blocked", "reason": "Approval denied"}
    execute_action(action, target)
    audit_log.record(action=action, target=target, user=user_id)
```

### Detection guidance

1. List all agent-executable actions and check for approval gates on
   destructive or sensitive ones
2. Look for auto-commit, auto-deploy, or auto-send patterns in instruction files
3. Check audit trail completeness for agent actions
4. Verify human reviewers see full action details, not just summaries

---

## ASI10 -- Rogue Agents

**Risk**: Unauthorized or compromised agents join workflows, impersonate
legitimate agents, or behave outside their intended scope without detection.

### What to look for

- No agent attestation or identity verification
- Dynamic agent instantiation from untrusted configurations
- No monitoring or logging of individual agent actions
- Missing allowlist for agents that can join workflows
- No anomaly detection on agent behavior patterns
- Agents loaded from external repositories without verification

### Vulnerable patterns

```python
# Dynamic agent loading from config without verification
def load_agents(config_path: str):
    config = yaml.safe_load(open(config_path))
    agents = []
    for agent_def in config["agents"]:
        # No verification of agent source or identity
        agent = Agent(
            name=agent_def["name"],
            code=agent_def["code"]  # arbitrary code from config
        )
        agents.append(agent)
    return agents
```

### Safe patterns

```python
# Agent allowlisting and verification
ALLOWED_AGENTS = {"researcher", "writer", "reviewer"}

def load_agents(config_path: str):
    config = yaml.safe_load(open(config_path))
    agents = []
    for agent_def in config["agents"]:
        if agent_def["name"] not in ALLOWED_AGENTS:
            raise SecurityError(f"Unknown agent: {agent_def['name']}")
        if not verify_agent_signature(agent_def):
            raise SecurityError(f"Agent signature invalid: {agent_def['name']}")
        agent = create_verified_agent(agent_def)
        agents.append(agent)
    return agents
```

### Detection guidance

1. Check if multi-agent systems use agent allowlisting
2. Look for dynamic agent instantiation from external sources
3. Verify agent behavior logging and monitoring exists
4. Check for identity verification in agent registration
