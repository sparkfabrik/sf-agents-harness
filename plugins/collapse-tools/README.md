# collapse-tools

A Claude Code mod that shows tool calls collapsed in the transcript. Click the chevron to expand or collapse a call.

```
▸ Bash(npm test) ✓ 142 lines
▾ Edit(src/app.ts)   ← kept expanded by default
```

- Running calls stay expanded and collapse when they finish, unless you toggled them.
- Failed calls start collapsed with a `✗` mark; set `collapseFailed` to `false` to keep them expanded.
- The tools listed in `expandedTools` start expanded.
- Folded runs of reads and searches get a chevron that unfolds them.
- Agent calls start collapsed, hiding their nested calls, and so does the report a background subagent hands back.
- Messages from other agents stay expanded by default; see [Messages from agents](#messages-from-agents).
- Toggles reset each session.

Clicks work in fullscreen mode, including inside tmux with `set -g mouse on`. Outside fullscreen, use the command below.

## Install

At the Claude Code prompt:

```
/plugin marketplace add sparkfabrik/sf-agents-harness
/plugin install collapse-tools@sf-agents-harness
```

To run it from a local checkout instead:

```
claude --plugin-dir /path/to/plugin/collapse-tools
```

## Command

`/collapse all`, `/collapse none`, or `/collapse` (toggle between expanded and the default state).

To bind the toggle to `ctrl+x c`, add this to `~/.claude/keybindings.json`:

```json
{
  "bindings": [
    { "context": "Global", "bindings": { "ctrl+x c": "command:collapse" } }
  ]
}
```

## Settings

Edit these in `/config`:

| Option                 | Default                                                  | Effect                                        |
| ---------------------- | -------------------------------------------------------- | --------------------------------------------- |
| `enabled`              | `true`                                                   | Turn the mod off without uninstalling it      |
| `expandedTools`        | Edit, Write, NotebookEdit, AskUserQuestion, ExitPlanMode | Comma-separated tools that start expanded     |
| `collapseOwnSubagents` | `true`                                                   | Start Agent calls and their reports collapsed |
| `collapseFailed`       | `true`                                                   | Start failed tool calls collapsed             |
| `collapseOtherAgents`  | `false`                                                  | Start messages from other agents collapsed    |

## Messages from agents

Besides tool calls, the transcript shows messages that other agents send to this session. Each one is a row labelled `Message from <sender>`. Which setting collapses it depends on who sent it:

| Sender                                                                                | Setting                | Default   |
| ------------------------------------------------------------------------------------- | ---------------------- | --------- |
| A subagent this session started, handing back its final report                        | `collapseOwnSubagents` | Collapsed |
| A teammate: another agent in the same agent team                                      | `collapseOtherAgents`  | Expanded  |
| Another Claude session messaging this one (over the local socket)                     | `collapseOtherAgents`  | Expanded  |
| A channel an MCP server relays (Slack, Telegram); a person writes these, not an agent | none                   | Expanded  |

A collapsed report reads `▸ Report from <subagent> <first line>`, and a collapsed message reads `▸ Message from <sender> <first line>`.

## Develop

```
claude plugin validate .
claude plugin test .
```
