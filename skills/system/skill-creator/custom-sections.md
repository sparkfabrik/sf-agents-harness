---

## Non-Claude coding agents (OpenCode, GitHub Copilot CLI, etc.)

The core skill-creator workflow -- draft, test via subagents, review with the user, improve, repeat -- works with any coding agent that supports skills. Throughout this document, read "Claude Code" as your current agent and "subagent" as your parallel task mechanism (e.g., the Task tool in OpenCode).

When the instructions say "run claude-with-access-to-the-skill on test prompts", use your agent's subagent/task system -- do not shell out to `claude -p`.

### Bundled script compatibility

| Script                                                 | Portable | Notes                                                                                                                    |
| ------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `generate_review.py`                                   | Yes      | Use `--static <path>` for headless environments                                                                          |
| `quick_validate.py`                                    | Yes      | Requires `pyyaml`                                                                                                        |
| `package_skill.py`                                     | Yes      | No external dependencies                                                                                                 |
| `run_eval.py`, `run_loop.py`, `improve_description.py` | No       | Depend on Claude's `--output-format stream-json` event schema, not just the `-p` flag. A binary alias is not sufficient. |

For description optimization, skip the scripts and apply the principles manually: write pushy descriptions with specific trigger keywords, test with edge-case queries, and iterate based on observed triggering behavior.

### Running test cases with OpenCode

Instead of `claude -p`, use `opencode run` to execute test prompts. Always use `github-copilot/gpt-4.1` for eval runs — do not use premium models (claude-opus, o1, etc.) for iterative skill testing to avoid unnecessary costs.

```bash
opencode run --model github-copilot/gpt-4.1 --pure "<prompt>" 2>&1
```

Key flags:

- `--pure` — runs without external plugins, for reproducible results
- `--model` — always use `github-copilot/gpt-4.1` for evals
- `--format json` — outputs NDJSON events for programmatic parsing

#### OpenCode JSON event schema

When using `--format json`, OpenCode emits newline-delimited JSON. The relevant event types for skill evaluation:

| Event `type`  | Description                       | Key fields                                      |
| ------------- | --------------------------------- | ----------------------------------------------- |
| `step_start`  | Agent turn begins                 | `sessionID`, `messageID`                        |
| `tool_use`    | Tool call (including skill loads) | `tool`, `callID`, `state.input`, `state.output` |
| `text`        | Assistant text output             | `text`                                          |
| `step_finish` | Agent turn ends                   | `reason`, `tokens`, `cost`                      |

To detect whether a skill was triggered, look for a `tool_use` event where `tool == "skill"` and `state.input.name` matches the skill name:

```python
import json

def check_skill_triggered(output: str, skill_name: str) -> bool:
    for line in output.strip().split("\n"):
        try:
            event = json.loads(line)
            if (event.get("type") == "tool_use"
                and event.get("part", {}).get("tool") == "skill"
                and event.get("part", {}).get("state", {}).get("input", {}).get("name") == skill_name):
                return True
        except json.JSONDecodeError:
            continue
    return False
```

#### Example: manual eval loop with OpenCode

```bash
# Run a test prompt against a skill
opencode run --model github-copilot/gpt-4.1 --pure --format json \
  "First, load the my-skill skill. Then: <task prompt>" 2>&1 | tee output.jsonl

# Check if the skill was triggered
python3 -c "
import json, sys
for line in open('output.jsonl'):
    e = json.loads(line)
    if e.get('type') == 'tool_use' and e.get('part',{}).get('tool') == 'skill':
        print('Skill triggered:', e['part']['state']['input']['name'])
"
```

The bundled `run_eval.py` and `run_loop.py` scripts are not yet compatible with OpenCode's event schema. Until adapted, run evals manually using the pattern above or via subagents (Task tool).
