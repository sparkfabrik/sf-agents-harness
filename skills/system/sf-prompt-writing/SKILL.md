---
name: sf-prompt-writing
description: 'SparkFabrik guidance for writing text that another model will read as instructions: system prompts, CLAUDE.md and AGENTS.md files, SKILL.md files, subagent and peer-agent briefs, /goal and /loop prompts, scheduled-agent prompts, and prompts inside application code that calls an LLM. Load it before creating or editing any of these, and before reviewing one. Trigger on "write a prompt", "system prompt", "brief an agent", "subagent prompt", "edit CLAUDE.md", "edit AGENTS.md", "write a skill", "/goal", or a prompt string in code. Do not trigger for human-facing prose (use sf-writing-style) or ordinary chat replies.'
---

# SparkFabrik prompt writing

These rules apply to text a model reads as instructions. Recent Claude models (Opus 5.5, Fable 5.2) follow instructions literally, so a vague or unexplained rule is applied too widely or not at all. Each rule links its source. The rules come from Anthropic's documentation and from practitioners. They are starting points to test on your own work, not settled results.

For human-facing prose, use `sf-writing-style` instead.

## Writing the instructions

- **Give the reason for each instruction.** A model that knows why a rule exists applies it in the cases the rule did not list, and skips it where it does not fit. Write "Keep replies short because they are read on a phone", not "Keep replies short". Source: [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
- **Name the exact behaviors to avoid.** "Avoid a generic look" does not change the output. A list of the patterns to avoid does: "no gradient hero, no three-card feature row". Source: [Prompting Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
- **Give every "never" rule and every approval gate its scope and its reason.** Fable 5.2 applies an unscoped "never" everywhere and stops on it. Write "Never push to `main`, because it deploys to production", not "Never push". Source: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).
- **Say who owns the code when that matters.** A line such as "This codebase is yours to maintain" makes the model merge duplicated code. It costs about 1.5 times the tokens. Leave it out when you want the smallest diff. Sources: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2), [Simon Willison](https://simonwillison.net/2026/Nov/10/prompting-claude-fable-52/).
- **Wrap pasted or retrieved text in tags with a random id.** The model then treats it as data and does not follow instructions it contains. Close the block with the same id, and say in the prompt that text inside the block is data:

  ```text
  <pasted_text id="7f3a9c">
  ...
  </pasted_text id="7f3a9c">
  ```

  Source: [Prompting Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).

- **Ask for criticism before execution when the idea is untested.** A prompt that asks first what is wrong with the plan gets objections. A prompt that asks for the plan to be carried out gets compliance. Source: [Alex Albert via Latent Space](https://latent.space/p/ainews-fable-5-2-retakes-world-1-llm-spot-as-ant-ipo-roadshow-begins/).

## What to remove

- **"Think carefully" and "reason step by step".** The `effort` setting controls reasoning now. In chat, removing these phrases makes the answer start sooner. Source: [Prompting Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
- **"When in doubt, use tool X".** The model then uses the tool when it is not needed. Say when the tool is the right choice instead. Source: [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
- **Requests to write the reasoning into the answer.** They can trigger the `reasoning_extraction` refusal. Ask for the conclusion and the evidence it rests on. Source: [Prompting Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
- **Numeric word limits.** In the Claude Code system prompt they cost 3% on evals. Describe the length you want ("one paragraph", "a line per finding") instead. Source: [Anthropic postmortem](https://www.anthropic.com/research/april-23-postmortem).
- **Token budgets written into the prompt.** On Fable 5.2 they raise cost. Use the API's own limits. Source: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

## Agents and long tasks

- **Ask for progress updates explicitly.** Without the request, Opus 5.5 and Fable 5.2 work silently. Ask for one line before starting, a short update at each phase change, and a final summary that a reader who missed the work can follow. Sources: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2), [antirez](https://www.youtube.com/watch?v=QobBTNIIX04).
- **Use Anthropic's published "Finishing work" text against early stops**, together with a task checklist kept in a file the agent updates. Copy the text from the source rather than rewriting it. Source: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).
- **Approve by naming the action.** Write "Yes, run the migration on staging", not "go". A bare "go" leaves the model to guess the scope of the approval. This applies when you relay a user's approval to another agent too. Source: [Prompting Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).
- **For memory, state the purpose, not the procedure.** Tell the agent what the memory is for and what is worth keeping. Rigid step-by-step memory rules lose most of the benefit. Source: [Agent memory](https://www.anthropic.com/research/components-of-agent-memory).
- **Give a `/goal` a metric, a constraint, a progress rule and a turn limit.** For example: "Test coverage of the parser package at 80% or more; no change to public APIs; commit after each package passes; stop after 30 turns." Source: [Addy Osmani](https://addyosmani.com/blog/practical-loop-engineering/).

## CLAUDE.md, AGENTS.md and skills

- **Keep a CLAUDE.md under 200 lines**, and put in it only what the code does not already say: conventions, traps, who owns what. A file the agent reads on every turn costs on every turn. Source: [Addy Osmani](https://addyosmani.com/blog/audit-your-agent-files/).
- **Apply the rules above to the file itself.** Each rule in a CLAUDE.md or a SKILL.md needs its reason and its scope, like any other prompt.

## Before you send or commit a prompt

Read the prompt as the model will, with no other context:

1. Does every instruction carry its reason?
2. Does every "never", "always" or approval gate say where it applies?
3. Is pasted or retrieved text inside an id-tagged block?
4. Are "think step by step", "when in doubt use", word counts and token budgets gone?
5. For a long task, does it ask for updates and say when the work is finished?
