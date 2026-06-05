## ADDED Requirements

### Requirement: Detect AI instruction files in the project

The skill SHALL scan the project for known AI instruction file patterns and report all found files.

The following file patterns SHALL be detected:

| Pattern                                          | Tool / Purpose                |
| ------------------------------------------------ | ----------------------------- |
| `.github/copilot-instructions.md`                | GitHub Copilot                |
| `AGENTS.md`                                      | Multi-tool agent instructions |
| `.cursorrules`                                   | Cursor AI                     |
| `.cursorignore`                                  | Cursor AI ignore patterns     |
| `.opencode/` directory                           | OpenCode config and skills    |
| `.aider.conf.yml`                                | Aider configuration           |
| `.mcp.json`, `mcp.config.*`                      | MCP server configurations     |
| `**/SKILL.md`                                    | Custom agent skills           |
| `**/prompts/**`, `**/*.prompt`, `**/*.prompt.md` | Prompt templates              |

#### Scenario: Drupal project with Copilot and MCP

- **WHEN** the project contains `.github/copilot-instructions.md` and `.mcp.json`
- **THEN** the skill SHALL list both files in the discovery report as AI instruction files

#### Scenario: No AI instruction files found

- **WHEN** the project contains no recognized AI instruction files
- **THEN** the skill SHALL report that no instruction files were detected and note that ASI04 (supply chain) review of instruction files will be skipped

### Requirement: Detect LLM SDK dependencies

The skill SHALL check package manager files for LLM-related dependencies.

The following dependency indicators SHALL be checked:

| Dependency                   | Language       | Indicates                     |
| ---------------------------- | -------------- | ----------------------------- |
| `openai`                     | Python/Node.js | OpenAI API integration        |
| `anthropic`                  | Python/Node.js | Anthropic API integration     |
| `langchain`, `langchain-*`   | Python/Node.js | LangChain agent framework     |
| `llamaindex`, `llama-index`  | Python         | LlamaIndex RAG framework      |
| `crewai`                     | Python         | CrewAI multi-agent framework  |
| `autogen`, `pyautogen`       | Python         | AutoGen multi-agent framework |
| `drupal/ai`, `drupal/openai` | PHP (Composer) | Drupal AI modules             |
| `@modelcontextprotocol/*`    | Node.js        | MCP SDK                       |

#### Scenario: PHP project with Drupal AI module

- **WHEN** `composer.json` contains `drupal/ai` in `require`
- **THEN** the skill SHALL report LLM integration detected via Drupal AI module

#### Scenario: No LLM dependencies

- **WHEN** no LLM-related dependencies are found in any package manager file
- **THEN** the skill SHALL note that no LLM SDK dependencies were detected

### Requirement: Detect vector DB and RAG dependencies

The skill SHALL check for vector database or RAG-related dependencies that indicate memory/retrieval systems an agent may use.

Dependencies to check: `chromadb`, `pinecone-client`, `weaviate-client`, `pgvector`, `qdrant-client`, `milvus`, `faiss-cpu`, `faiss-gpu`.

#### Scenario: Project with ChromaDB

- **WHEN** `requirements.txt` or `pyproject.toml` contains `chromadb`
- **THEN** the skill SHALL report RAG/vector DB integration detected and flag ASI06 (Memory Poisoning) as applicable

### Requirement: Detect LLM API credentials in environment files

The skill SHALL check `.env`, `.env.example`, `.env.local` and similar files for LLM API credential patterns without reading actual secret values.

Patterns to detect: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_AI_API_KEY`, `AZURE_OPENAI_*`, `HUGGINGFACE_TOKEN`.

The skill SHALL flag actual credential values committed to version control as a critical finding. The skill SHALL treat `.env.example` with placeholder values as informational (indicates LLM usage, not a credential leak).

#### Scenario: Real API key committed

- **WHEN** `.env` is tracked by git and contains `OPENAI_API_KEY=sk-proj-...`
- **THEN** the skill SHALL flag this as a critical finding (credential exposure to agents)

#### Scenario: Example file with placeholders

- **WHEN** `.env.example` contains `OPENAI_API_KEY=your-key-here`
- **THEN** the skill SHALL note LLM API usage detected but not flag it as a credential leak

### Requirement: Produce a discovery report

After detection, the skill SHALL present a structured discovery report listing all found AI instruction files, LLM dependencies, vector DB dependencies, credential indicators, and which OWASP Agentic Top 10 categories are applicable to this project.

The skill SHALL ask the user to confirm before proceeding to the review phase.

#### Scenario: Mixed AI integration project

- **WHEN** discovery finds `.github/copilot-instructions.md`, `openai` in package.json, and `.mcp.json`
- **THEN** the skill SHALL present a report listing all findings and mark ASI01-ASI05 and ASI09 as applicable
