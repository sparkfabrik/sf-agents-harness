---
name: auto-format-doc
description: >
  Auto-format files after creating or modifying them using external formatters
  managed by Just recipes (sjust/ajust). Use this skill whenever you write,
  create, or edit a Markdown file (.md). Also use when the user mentions
  "format markdown", "prettier", "format-md", "format-md-check",
  "auto-format", "auto-format-doc", or asks you to fix or check Markdown
  formatting. This skill applies even if you are not explicitly asked to
  format -- any time a .md file is written or modified, run the formatter on it.
---

# Auto Format

Coding agents should not format files by hand. Instead, after creating or
modifying a file, run the appropriate external formatter. This keeps formatting
consistent across the project and avoids drift between human-written and
agent-written files.

Currently supported: **Markdown (.md)** via Prettier.

## When to run

After **every** Write or Edit operation that produces or modifies a `.md` file,
run the format command on that file. This includes:

- Creating a new Markdown file
- Editing an existing Markdown file
- Renaming or moving a Markdown file (format the new path)

Do **not** attempt to format Markdown content yourself (e.g., adjusting line
length, reflowing paragraphs, fixing list indentation). The formatter handles
all of that. Focus on content; let the tool handle style.

## Platform detection

The command runner depends on the operating system. Detect the platform once
at the start of your session and reuse the result:

```bash
if [[ "$(uname)" == "Linux" ]]; then
    JUST_CMD="ajust"
else
    JUST_CMD="sjust"
fi
```

## Formatting commands

### Markdown (.md)

Try the Just recipe first. If it fails, follow [Error handling](#error-handling)
before falling back to the `npx` equivalent:

**Preferred (Just recipe):**

```bash
$JUST_CMD format-md <path> [<path> ...]
```

**Fallback (direct npx):**

```bash
npx --yes prettier@3 --write <path> [<path> ...]
```

The fallback runs the exact same command the Just recipe uses under the hood,
so the result is identical. The key thing is that the agent always tries the
Just recipe first -- it may carry project-specific Prettier configuration or
version pins -- and only resorts to `npx` when that fails.

- Pass the **specific file path(s)** you just wrote or edited.
- You can pass multiple paths in a single call if you modified several files.
- Do **not** run the command without a path argument -- that would format every
  Markdown file in the project, which is slow and noisy.

**Example -- single file:**

```bash
$JUST_CMD format-md docs/setup.md
```

**Example -- multiple files in one task:**

```bash
$JUST_CMD format-md README.md docs/setup.md CHANGELOG.md
```

### Checking without writing

To verify whether files are correctly formatted without modifying them, use the
check variant. Use the same error-handling sequence as for formatting:

**Preferred:**

```bash
$JUST_CMD format-md-check <path> [<path> ...]
```

**Fallback:**

```bash
npx --yes prettier@3 --check <path> [<path> ...]
```

This exits with a non-zero status if any file is not formatted. It is useful
when the user asks you to verify formatting, in CI pipelines, or before
committing to confirm everything is clean. It never writes to disk.

## Error handling

In Codex only, inspect a failed Just recipe before trying direct `npx`. If the
failure indicates sandbox-denied network or cache access (for example,
`EAI_AGAIN` while contacting the npm registry, `operation not permitted`, or
permission denied under `~/.npm`), rerun the same Just command with Codex sandbox
escalation. This applies to both `format-md` and `format-md-check`, whether the
platform uses `ajust` or `sjust`. If the retry succeeds, formatting is done. If
escalation is unavailable or denied, report the access limit and continue the
task; direct `npx` in the same sandbox has the same access problem.

For other failures, including a missing Just command or recipe, try the direct
`npx` fallback. In agents other than Codex, keep the existing Just-then-`npx`
sequence for every failure.

If both the Just recipe and the `npx` fallback fail (e.g., Node.js is not
installed at all), **warn the user and continue**. Formatting is cosmetic -- a
failure should not block the task.

Example warning:

> Markdown formatting failed (neither `$JUST_CMD format-md` nor
> `npx prettier` succeeded). The file content is correct but may not match the
> project's formatting conventions. You can run the formatter manually later.

## Rules summary

1. After writing or editing any `.md` file, format it: try `$JUST_CMD format-md <path>` first. In Codex, retry sandbox access failures with escalation; otherwise fall back to `npx --yes prettier@3 --write <path>`.
2. Always pass explicit file paths -- never run without arguments.
3. Never format Markdown by hand -- delegate to the command.
4. Always try the Just recipe first; use the `npx` fallback for non-sandbox failures, or for every failure outside Codex.
5. If formatting remains unavailable, report the cause and move on.
