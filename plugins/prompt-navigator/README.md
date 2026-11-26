# prompt-navigator

A Claude Code mod that lists your prompts in a side pane. Press one to scroll the conversation to it.

- Run `/prompts` to open the pane; run it again to close it.
- Each prompt is numbered and wraps to as many rows as it needs, up to 8.
- A short reply such as `yes please` also shows what it answered (`← Want me to build one?`): the last question or sentence of the assistant message before it.
- **○ replies** (or `r`) shows the assistant's text messages under each prompt; press one to jump to it.
- The entry for the topmost message on screen in the conversation is colored, and follows as you scroll. Pick the color as **Highlight color** in `/config`; `/prompts colors` shows the colors you can pick.
- **↓ bottom** (or `b`) stays at the foot of the pane and scrolls the list and the conversation to the end.
- The list opens at the newest prompt. Scroll with the mouse wheel, or focus the pane with `ctrl+x tab` and use the arrows, PgUp/PgDn and Home/End.
- Tool results, slash-command echoes and system notifications are left out.

## Haiku summaries

Turn on **Haiku summaries** in `/config` to add a one-line summary (`✦ …`) under each finished exchange, written by Claude Haiku from the prompt and the replies around it. Each exchange is summarized once and the summaries are kept across sessions. Each summary is one small Haiku request and counts toward `/cost`. It is off by default.

The pane docks beside the conversation in fullscreen mode; outside it, it opens inline.

## Install

At the Claude Code prompt:

```
/plugin marketplace add sparkfabrik/sf-agents-harness
/plugin install prompt-navigator@sf-agents-harness
```

To run it from a local checkout instead:

```
claude --plugin-dir plugins/prompt-navigator
```

It needs Claude Code 2.1.332 or later, the version it was tested with.
