---
name: sf-writing-style
description: 'Canonical SparkFabrik writing style. MUST be loaded before composing, rewriting, or sending human-facing prose, including GitHub/GitLab issue and PR/MR titles or descriptions, comments, reviews, Slack messages and progress updates, changelogs, release notes, incident updates, docs, READMEs, ADRs, and onboarding guides. Trigger for operational requests such as "create an issue", "open or update a PR or MR", "post a Slack message", "write a comment", or "send an update", even when writing is only part of a larger CLI, API, MCP, connector, or webhook action. Do not trigger for code, logs, command output, quoted source text, or ordinary chat replies. Requires short, plain text focused on what changes; no implementation stories, padding, or AI slop.'
---

# SparkFabrik writing style

Rules for every human-facing prose artifact the agent writes: READMEs, docs, onboarding guides, issue and PR/MR titles and descriptions, comments, reviews, Slack messages, progress updates, changelogs, release notes, incident updates, ADRs, and review notes. For worked before/after rewrites, see [references/examples.md](references/examples.md).

## Short artifacts come first

Apply these rules whenever you draft or send a title, description, comment, review, changelog, or release note, including through the API. These rules take priority over the general document formatting below.

- **Content.** PR/MR descriptions lead with what changes, understandable without the task conversation. Add one sentence of context only when omitting it would make the change hard to understand or review. Issues state the problem and wanted result. Comments answer the point. Changelog entries state one change each.
- **Length.** Let the change determine the layout; a small fix can fit in one sentence. Default maximum: 80 words for a PR/MR description, 120 for an issue, 60 for a comment, and one sentence per changelog entry. These are team defaults, not targets or public standards. Preserve essential information even when it needs more words. Attribution and reference lines do not count.
- **Leave out.** No implementation details, even in a single sentence: file paths, function names, internal variables, source lines, test counts, diagnoses, or proposed fixes. Omit workarounds, investigation history, rejected approaches, and repeated summaries. Keep an identifier only when it names the changed interface or a required user action. Do not move omitted detail into unsolicited comments.
- **Select facts.** Investigation notes and the diff are input, not a checklist to summarize. For an issue, keep the symptom and wanted result. For a PR/MR, keep the changed behavior, essential context and required action. For a comment, answer only the question.
- **Evidence.** Use only supplied facts or results you observed. Omit unknowns. An error does not establish side effects, data loss, partial success, or affected environments. Do not invent causes, sample values, test cases, or reproduction results.
- **Plain English.** Use familiar words and concrete verbs. Keep necessary technical names exact. No invented jargon or padding. Use complete sentences in prose; parallel bullet items may be short phrases.
- **Layout.** Open with the main change. Bold a short key phrase, not a whole sentence. Put distinct features or changes in bullets instead of a comma-packed paragraph. Use headings only to separate useful sections, not generic labels like "MR description". One uncomplicated behavior change needs no list; a feature with several visible parts should list those parts. No empty sections, mandatory headings, bullet counts, or minimum length. State each fact once; do not restate the fix as its opposite in the old behavior unless the comparison is needed.
- **Supporting evidence.** Include supplied screenshots when they clarify a visible change; label before/after only when both are supplied. Include a short, verified validation result when it helps assess the change. Do not dump commands, logs, or test counts, or invent screenshots or results.
- **Exceptions.** Include essential breaking changes and required user actions. Expand only for these essentials, essential context, necessary validation, explicitly requested detail, or required template fields, using the fewest words needed. A direct question about how or why deserves a direct answer.

Before posting, read the actual outgoing text. Cut every sentence that does not state the change, problem, answer, essential context, required action, or useful verified evidence. Remove code locations and test inventories unless explicitly requested. Check each factual claim against the final diff and current evidence; remove stale claims when scope changes. Describe this diff; omit already-merged changes and workflow history unless explicitly requested. Can a reader outside the conversation identify what changes, any required action, and what was actually verified? Then check the length and remove repetition. Reading the diff is required; narrating it is not. Rewrite commit-generated descriptions before posting. Return the description itself, without code fences, block quotes, or commentary about omitted details unless requested.

Example of a small fix: "Rejects empty passwords with a validation message instead of returning a 500 error."

Example of a feature with several visible parts (copy the layout, not these facts):

> Adds **export controls**:
>
> - Date-range selection.
> - CSV download.

The lead sentence names the feature; the bullets name its parts. The description remains short without becoming a bare paragraph.

Public guidance behind these rules is listed in [references/writing-principles.md](references/writing-principles.md). Read it when reviewing the rules, not for routine drafting.

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
- **Summary outros.** "In conclusion", "Overall", "To summarize". Just stop.
- **Hype symmetry.** "not only X but also Y", "whether you're X or Y", decorative triads ("fast, reliable, and scalable") unless each item is a load-bearing fact.
- **Enthusiasm markers.** Exclamation points, emoji decoration, "Great question".

## Air: paragraphs and whitespace

- One idea per paragraph. One to three sentences, then a blank line.
- A paragraph over three sentences gets split, or restructured into a list.
- Blank line before and after every heading, list, and code block.
- Prefer a full stop over a subordinate-clause chain. Two short sentences beat one long one.

## Lists and visual structure

- Use a list when the reader needs to compare or follow several items. Cut unnecessary items before choosing a layout.
- Use **bold lead-ins** when they help scanning. Plain bullets are enough for short feature lists. Two available shapes:
  - Label plus period: `- **The script-name contract.** Every generated app exposes ...`
  - Verb: `- **builds** each app's dev image (from its build/Dockerfile)`
- In issue task checklists, start each detailed item with a short **bold outcome** followed by a period. Use this when the item also explains scope, constraints, or acceptance criteria. Keep simple one-line checklist items plain.
- Ordered processes: introduce with a colon line ("The deploy triggers, in order:") followed by steps.
- In longer documents, a key instruction can have a bold lead-in: `**Rule of thumb:** if a file says "do not edit", edit the generator instead.`

## Sentence-level rules

- Active voice with a concrete subject: "the script builds the image", not "the image is built by the script".
- Name the thing in backticks: file paths, commands, flags, config keys, exact error strings.
- Cut hedges and filler: basically, essentially, simply, just, actually, very, quite.
- Plain verbs: use, run, build, check (not utilize, orchestrate, facilitate).
- Prefer sentences under 20 words. Do not pack several clauses into one sentence to meet a sentence limit.
- State each fact once. Delete padding rather than redistributing it into headings or bullets.

## Structure rules

- Lead with the point. The first paragraph of a doc or section says what it is and why the reader cares. No warm-up.
- For longer documents, use one H1. Sentence-case headings, no trailing period, never skip heading levels.
- Language tag on every fenced code block.
- Tables for symmetric data only (same fields per row); lists for asymmetric items. No paragraphs inside table cells.
- Link text says where it goes ("see the sync manifest schema"), never "click here". Images get alt text that describes their purpose.

## Anti-rules: when NOT to bulletize

- **Do not shred flowing narrative into fragment confetti.** Rationale, incident stories, ADR context, and trade-off discussions read better as short paragraphs. Bulletize only parallel items.
- Use a list when distinct items are easier to scan separately, not to meet a bullet count.
- Bold lead-ins are for parallel structures. Do not bold-lead bullets that are ordinary full sentences with different grammatical shapes.
- A short description usually needs no heading. Add one only to distinguish sections such as required actions or screenshots.
- Never trade technical precision for brevity. Correctness beats compression.

## Before and after

Before:

> This change introduces a comprehensive validation layer in the login handler, updates the associated tests, and ensures that empty password submissions are handled gracefully rather than propagating an internal server error.

After:

> Rejects empty passwords with a validation message instead of returning a 500 error.

See [references/examples.md](references/examples.md) for issues, descriptions, comments, changelogs, and necessary exceptions.

## Self-check before returning any prose

1. The opening sentence states the change, problem, answer, or required action.
2. Every sentence adds a needed fact. No implementation story or repeated summary survives in a short artifact.
3. The text meets its word limit, excluding attribution and reference lines, unless an explicit exception applies. Shorter is better when the meaning stays clear.
4. Sentences use familiar words and concrete verbs. No blacklist word, invented jargon, or filler survives.
5. No em or en dash survives outside quotations and code. Paragraphs have three sentences or fewer.
6. Check that formatting makes the change easier to scan without repeating facts or adding empty sections.
7. Detailed issue checklist items have short bold outcomes; simple checklist items remain plain.
8. Check the actual outgoing body before a tool call, including text generated from commits. Do not append extra explanations in a follow-up comment.
9. If the artifact is a `.md` file, run the formatter per `auto-format-doc`. Formatting does not replace the content check.

## Interaction with other skills

This skill is the baseline for every other skill that writes prose. Whenever another skill composes, rewrites, or reviews human-facing text (issues, PRs/MRs, commits, docs, Slack messages, reports), load this skill first and apply its rules underneath that skill's specific guidance. This holds for skills from any part of the harness and for locally installed skills, not only the ones named below.

Some examples of how the baseline composes with specific skills:

- **CLI writing rules.** `gh` and `glab` include the short-artifact rules directly so they do not depend on a second skill load. Keep those rules aligned with this skill.
- **Mechanical layout.** The `auto-format-doc` skill handles mechanical markdown layout (prettier): this skill decides what the prose says and how it is structured, the formatter normalizes whitespace and syntax afterwards.
- **Domain overlays.** Skills that own a document type (issue writing, ADRs, postmortems, changelogs) add their structure and domain rules on top; this skill keeps governing the sentences inside that structure.

Document skills can require structure for ADRs, postmortems, and specifications. Their longer formats do not carry over to issues, PR/MR descriptions, comments, or changelog entries. For short artifacts, only the exceptions listed above allow extra detail.

The plain-prose override still applies: artifacts are written in complete, well-structured English even when a terse conversational style (for example a `CAVEMAN MODE ACTIVE` session reminder) is active. The terse style governs chat replies, never the artifacts. Do not toggle the style; write the artifact in full prose and resume the terse style in chat.
