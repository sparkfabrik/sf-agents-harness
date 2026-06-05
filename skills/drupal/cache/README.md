# Drupal Cache Expert - VS Code Copilot Agent

A specialized VS Code Copilot agent for Drupal 8+ HTTP Cache API, caching strategies, debugging, and performance optimization.

## Features

- **Expert Agent**: Specialized knowledge of Drupal's complete caching stack
- **Context7 MCP Integration**: Real-time access to current Drupal documentation
- **Domain-Specific Skills**: Auto-activated knowledge for cache tags, contexts, max-age, BigPipe, Varnish/CDN, debugging, and lazy builders

## Installation

### 1. Copy Files to Your Project

```bash
# Copy the entire structure to your Drupal project root
cp -r .github/ /path/to/your/drupal/project/
cp -r .vscode/ /path/to/your/drupal/project/
```

### 2. Configure Context7 MCP

The `.vscode/mcp.json` file is already configured for Context7. VS Code will prompt for your API key on first use.

#### Get API Key

1. Go to [context7.com/dashboard](https://context7.com/dashboard) for a free API key
2. Open VS Code and start the MCP server
3. Enter your API key when prompted (stored securely by VS Code)

#### Alternative: Local npx Server

If you prefer to run Context7 locally via npx, update `.vscode/mcp.json`:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "context7-api-key",
      "description": "Context7 API Key",
      "password": true
    }
  ],
  "servers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "${input:context7-api-key}"
      }
    }
  }
}
```

### 3. Start MCP Server

1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Run **MCP: List Servers**
3. Select `context7` and choose **Start Server**
4. Enter your API key when prompted

Alternatively, the server starts automatically when you use the agent in chat (if `chat.mcp.autostart` is enabled).

## Usage

### Select the Agent

1. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
2. Click the agent dropdown at the top
3. Select **drupal-cache-expert**

### Example Prompts

```
Why is my page showing X-Drupal-Dynamic-Cache: UNCACHEABLE?

How do I implement cache tags for a custom entity?

What's the difference between user.roles and user context?

My anonymous pages aren't being cached, how do I debug this?

How do I set up Varnish purging with cache tags?

Show me how to implement a lazy builder for user-specific content
```

### Skills Auto-Activation

The following skills auto-activate based on your questions:

| Skill                    | Triggers                                                    |
| ------------------------ | ----------------------------------------------------------- |
| `drupal-cache-tags`      | cache tags, invalidation, entity tags                       |
| `drupal-cache-contexts`  | cache contexts, user.roles, variations                      |
| `drupal-cache-maxage`    | max-age, time-based expiration                              |
| `drupal-dynamic-cache`   | Dynamic Page Cache, BigPipe, UNCACHEABLE                    |
| `drupal-cache-debugging` | debugging, troubleshooting, headers                         |
| `drupal-lazy-builders`   | lazy builders, placeholders, #lazy_builder                  |
| `http-cache-tools`       | curl, HTTP headers, cache inspection, SparkFabrik container |

## File Structure

```
.github/
├── agents/
│   └── drupal-cache-expert.agent.md    # Main agent definition
├── skills/
│   ├── drupal-cache-tags/
│   │   └── SKILL.md
│   ├── drupal-cache-contexts/
│   │   └── SKILL.md
│   ├── drupal-cache-maxage/
│   │   └── SKILL.md
│   ├── drupal-dynamic-cache/
│   │   └── SKILL.md
│   ├── drupal-cache-debugging/
│   │   └── SKILL.md
│   ├── drupal-lazy-builders/
│   │   └── SKILL.md
│   └── http-cache-tools/
│       └── SKILL.md                    # curl, HTTP tools, SparkFabrik context
└── copilot-instructions.md             # Global Copilot instructions

.vscode/
└── mcp.json                            # Context7 MCP configuration
```

## Handoffs

The agent supports workflow handoffs:

- **Implement Caching Changes**: Hand off to implement recommended caching improvements
- **Debug Cache Issue**: Hand off for step-by-step debugging assistance

## Requirements

- VS Code 1.102+ (MCP support is GA from this version)
- GitHub Copilot extension
- Node.js 18+ (only if using local npx server)
- Context7 API key (free tier available at context7.com/dashboard)

## Troubleshooting

### MCP Server Not Starting

1. Run **MCP: List Servers** from Command Palette
2. Select `context7` and choose **Show Output** to view logs
3. Verify your API key is correct

```bash
# Test Context7 manually (if using local server)
npx -y @upstash/context7-mcp
```

### Agent Not Appearing

1. Reload VS Code window (Ctrl+Shift+P → "Reload Window")
2. Verify `.github/agents/` directory exists
3. Check file has `.agent.md` extension

### Context7 Rate Limits

Free tier has rate limits. Get an API key from context7.com/dashboard for higher limits.

### Skills Not Activating

1. Ensure `.github/skills/` directory structure is correct
2. Check that skill `description` matches your query keywords
3. Run **MCP: Reset Cached Tools** to refresh

## Resources

- [VS Code MCP Servers Documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [VS Code Custom Agents Docs](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [VS Code Agent Skills Docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Context7 Documentation](https://context7.com/docs)
- [Context7 Drupal Library](https://context7.com/drupal/drupal)
- [Drupal Cache API](https://www.drupal.org/docs/drupal-apis/cache-api)

## License

MIT
