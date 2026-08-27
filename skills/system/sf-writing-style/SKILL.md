---
name: sf-writing-style
description: 'Canonical SparkFabrik writing style. MUST be loaded before composing, rewriting, or sending human-facing prose, including GitHub/GitLab issue and PR/MR titles or descriptions, comments, reviews, Slack messages and progress updates, changelogs, release notes, incident updates, docs, READMEs, ADRs, and onboarding guides. Trigger for operational requests such as "create an issue", "open or update a PR or MR", "post a Slack message", "write a comment", or "send an update", even when writing is only part of a larger CLI, API, MCP, connector, or webhook action. Do not trigger for code, logs, command output, quoted source text, or ordinary chat replies. Enforces short aired paragraphs, bold lead-in lists, no em/en dashes, and no AI slop.'
---

# SparkFabrik writing style

Rules for every human-facing prose artifact the agent writes: READMEs, docs, onboarding guides, issue and PR/MR titles and descriptions, comments, reviews, Slack messages, progress updates, changelogs, release notes, incident updates, ADRs, and review notes. For worked before/after rewrites, see [references/examples.md](references/examples.md).

## Tool-mediated writing

Apply this style before sending text through `gh`, `glab`, Slack, an API, an MCP connector, or a webhook. Draft the content under these rules before invoking the external tool. Transport does not change the writing standard.

## Hard bans

- **No em dash (—) and no en dash (–), ever.** Not as a sentence connector, not in headings, lists, tables, or ranges. Rewrite with a period, comma, colon, or parentheses. For ranges write `1 to 5` or `1-5` with a plain hyphen.
- **Plain hyphen (-) is for compound words only** (read-only, first-class). Never use a spaced hyphen `-` as clause punctuation.
- **Exception: quoted material and code stay untouched.** Never edit dashes inside quotations, code blocks, or upstream text you are citing.

## Slop blacklist

Words to replace with plainer ones: delve, leverage (as a verb), utilize, robust, seamless, seamlessly, comprehensive, crucial, pivotal, foster, streamline, empower, elevate, unlock, supercharge, game-changer, cutting-edge, holistic, synergy.

Patterns to cut:

- **Throat-clearing openers.** "This document aims to", "In this section we will", "It's worth noting that", "In today's fast-paced world". Start with the point instead.
- **Reveal framing.** "the key insight", "the crux", "the smoking gun", "the core of it", "the telling detail", "load-bearing". State the fact directly; do not announce that it matters first.
- **Summary outros.** "In conclusion", "Overall", "To summarize". Just stop.
- **Hype symmetry.** "not only X but also Y", "whether you're X or Y", decorative triads ("fast, reliable, and scalable") unless each item states a distinct fact.
- **Enthusiasm markers.** Exclamation points, emoji decoration, "Great question".

## Air: paragraphs and whitespace

- One idea per paragraph. One to three sentences, then a blank line.
- A paragraph over three sentences gets split, or restructured into a list.
- Blank line before and after every heading, list, and code block.
- Prefer a full stop over a subordinate-clause chain. Two short sentences beat one long one.

## Lists with bold lead-ins

- A sentence enumerating three or more parallel things becomes a bulleted list, one item per bullet.
- Start each bullet with a **bold lead-in**. Two shapes, consistent within a list:
  - Label plus period: `- **The script-name contract.** Every generated app exposes ...`
  - Verb: `- **builds** each app's dev image (from its build/Dockerfile)`
- Ordered processes: introduce with a colon line ("The deploy triggers, in order:") followed by steps.
- Pull key takeaways into their own bold-led paragraph: `**Rule of thumb:** if a file says "do not edit", edit the generator instead.`

## Sentence-level rules

- Active voice with a concrete subject: "the script builds the image", not "the image is built by the script".
- Name the thing in backticks: file paths, commands, flags, config keys, exact error strings.
- Cut hedges and filler: basically, essentially, simply, just, actually, very, quite.
- Plain verbs: use, run, build, check (not utilize, orchestrate, facilitate).

## Structure rules

- Lead with the point. The first paragraph of a doc or section says what it is and why the reader cares. No warm-up.
- One H1 per document. Sentence-case headings, no trailing period, never skip heading levels.
- Language tag on every fenced code block.
- Tables for symmetric data only (same fields per row); lists for asymmetric items. No paragraphs inside table cells.
- Link text says where it goes ("see the sync manifest schema"), never "click here". Images get alt text that describes their purpose.

## Anti-rules: when NOT to bulletize

- **Do not shred flowing narrative into fragment confetti.** Rationale, incident stories, ADR context, and trade-off discussions read better as short paragraphs. Bulletize only parallel items.
- Two items rarely need a list; keep them in a sentence.
- Bold lead-ins are for parallel structures. Do not bold-lead bullets that are ordinary full sentences with different grammatical shapes.
- Short docs (roughly under 15 lines) need no headings.
- Never trade technical precision for brevity. Correctness beats compression.

## Before and after

Before:

> The deploy script — which is generated by the scaffolder — builds the image, pushes it to the registry and then triggers the rollout — note that it also tags the release.

After:

> The deploy script is generated by the scaffolder. It runs four steps, in order:
>
> - **builds** the image from `build/Dockerfile`
> - **pushes** it to the registry
> - **tags** the release
> - **triggers** the rollout

More pairs, including a dash-rewrite table and an over-bulletized counter-example, in [references/examples.md](references/examples.md).

## Self-check before returning any prose

1. Search the draft for `—` and `–`: zero occurrences (outside quotes and code).
2. The longest paragraph is three sentences or fewer.
3. Every enumeration of three or more parallel items is a list.
4. No blacklist word or pattern survives.
5. The opening line states the point.
6. If the artifact is a `.md` file, run the formatter on it per the `auto-format-doc` skill (`format-md` recipe, `npx prettier` fallback). Style rules govern content; the formatter owns mechanical layout.

## Interaction with other skills

This skill is the baseline for every other skill that writes prose. Whenever another skill composes, rewrites, or reviews human-facing text (issues, PRs/MRs, commits, docs, Slack messages, reports), load this skill first and apply its rules underneath that skill's specific guidance. This holds for skills from any part of the harness and for locally installed skills, not only the ones named below.

Some examples of how the baseline composes with specific skills:

- **Prose stubs.** The `gh`, `glab`, and `sf-commit-convention` skills carry a short plain-prose stub for their artifacts; this skill is the full ruleset behind those stubs.
- **Mechanical layout.** The `auto-format-doc` skill handles mechanical markdown layout (prettier): this skill decides what the prose says and how it is structured, the formatter normalizes whitespace and syntax afterwards.
- **Domain overlays.** Skills that own a document type (issue writing, ADRs, postmortems, changelogs) add their structure and domain rules on top; this skill keeps governing the sentences inside that structure.

When another skill's guidance conflicts with this baseline, the more specific skill wins for its own artifact type, but only for the rules it explicitly overrides.

The plain-prose override still applies: artifacts are written in complete, well-structured English even when a terse conversational style (for example a `CAVEMAN MODE ACTIVE` session reminder) is active. The terse style governs chat replies, never the artifacts. Do not toggle the style; write the artifact in full prose and resume the terse style in chat.
