---
name: sf-writing-style
description: 'Canonical SparkFabrik writing style. MUST be loaded before composing, rewriting, or sending human-facing prose, including GitHub/GitLab issue and PR/MR titles or descriptions, comments, reviews, Slack messages and progress updates, changelogs, release notes, incident updates, docs, READMEs, ADRs, onboarding guides, and documents for clients (offers, studies, reports, decks, talks), in English or Italian. Trigger for operational requests such as "create an issue", "open or update a PR or MR", "post a Slack message", "write a comment", or "send an update", even when writing is only part of a larger CLI, API, MCP, connector, or webhook action. Do not trigger for code, logs, command output, quoted source text, or ordinary chat replies. Requires short, plain text focused on what changes; no implementation stories, padding, or AI slop.'
---

# SparkFabrik writing style

Rules for every human-facing prose artifact the agent writes: READMEs, docs, onboarding guides, issue and PR/MR titles and descriptions, comments, reviews, Slack messages, progress updates, changelogs, release notes, incident updates, ADRs, and review notes. For worked before/after rewrites, see [references/examples.md](references/examples.md).

## Short artifacts come first

Apply these rules whenever you draft or send a title, description, comment, review, changelog, or release note, including through the API. These rules take priority over the general document formatting below.

Before drafting, rewriting, or publishing a PR/MR description, read [references/pr-mr-descriptions.md](references/pr-mr-descriptions.md) completely and apply it. Its scale and coverage rules override the default length guidance below for complex, cross-cutting, or breaking changes.

Before writing text that GitHub, GitLab, or Slack will render, read [references/platforms.md](references/platforms.md). Each platform renders Markdown, references, and tables differently.

- **Content.** PR/MR descriptions lead with what changes, understandable without the task conversation. Add one sentence of context only when omitting it would make the change hard to understand or review. Issues state the problem and wanted result. Comments answer the point. Changelog entries state one change each.
- **Length.** Let the change determine the layout; a small fix can fit in one sentence. Default maximum: 80 words for an uncomplicated PR/MR description, 120 for an issue, 60 for a comment, and one sentence per changelog entry. These are team defaults, not targets or public standards. Preserve essential information even when it needs more words. The PR/MR reference governs complex descriptions. Attribution and reference lines do not count.
- **Leave out.** No implementation details, even in a single sentence: file paths, internal function names, internal variables, source lines, test counts, diagnoses, or proposed fixes. Omit workarounds, investigation history, rejected approaches, and repeated summaries. Keep public interface names, commands, configuration keys, and identifiers only when they help a reviewer understand the contract or a required user action. Do not move omitted detail into unsolicited comments.
- **Select facts.** Investigation notes and the diff are input, not a checklist to summarize. For an issue, keep the symptom and wanted result. For a PR/MR, keep the changed behavior, essential context and required action. For a comment, answer only the question.
- **Evidence.** Use only supplied facts or results you observed. Omit unknowns. An error does not establish side effects, data loss, partial success, or affected environments. Do not invent causes, sample values, test cases, or reproduction results.
- **Plain English.** Use familiar words and concrete verbs. Keep necessary technical names exact. No invented jargon or padding. Use complete sentences in prose; parallel bullet items may be short phrases.
- **Layout.** Open with the main change. Bold a short key phrase, not a whole sentence. Put distinct features or changes in bullets instead of a comma-packed paragraph. Use headings only to separate useful sections, not generic labels like "MR description". One uncomplicated behavior change needs no list; a feature with several visible parts should list those parts. No empty sections, mandatory headings, bullet counts, or minimum length. State each fact once; do not restate the fix as its opposite in the old behavior unless the comparison is needed.
- **Emphasis and identifiers.** Readers scan issues and comments as much as descriptions. Bold the two to five words a scanning reader must not miss, such as the problem, the wanted result, a required action, or a deadline, and leave the rest of the sentence plain. A label such as `**Wanted:**` also works. Show every identifier you keep as code, following the sentence-level rules below. Formatting never justifies keeping an identifier the reader does not need.
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

Patterns that make a text read as machine-written, in English and Italian. Each one is fine once in a long text; a draft that leans on them reads generated. Write the alternative instead:

- **Throat-clearing openers and talk about the text.** "This document aims to", "Let's dive in", "As we have seen", "In today's fast-paced world", "In questo documento", "Come abbiamo visto", "Nel contesto attuale". Start with the point instead.
- **Slogans and metaphors in place of a mechanism.** A sentence that sounds like a motto: "Nothing ships without review", "Nessun rilascio avviene senza controlli", "Il codice smette di essere una scatola nera". Absolute words (nothing, every, always, niente, ogni, sempre) without the mechanism turn a process into a promise. Make the process or its owner the subject instead: "I backup sono verificati con un ripristino mensile" rather than "Nessun dato va mai perso", "The on-call engineer takes the alert within 15 minutes" rather than "Every alert gets an answer".
- **Summary outros.** "In conclusion", "Overall", "To summarize", "In sintesi". End on the last fact or the next step.
- **Closing one-liners.** A short aphorism that ends a paragraph ("Speed is a feature."). Fold it into the previous sentence as a consequence with its fact, or drop it.
- **Rhetorical bridges.** "Here's the thing", "That's where X comes in", "Ed è proprio qui che", a paragraph that ends on a question. Let the next paragraph open on its own fact.
- **Antithesis.** "It's not X, it's Y", "not only X but also Y", "Non è X, è Y". Say what Y is, directly. Keep the correction of X only when someone actually holds X.
- **Colon setups.** "The result: …", "One rule: …", "il flusso è semplice: build, deploy e verifica". Write a full sentence with a verb that carries the items. Keep colons before a bulleted or numbered list, a quote, code, and precise figures.
- **Triads and noun piles.** "fast, reliable, and scalable", "contesto, scelta del modello e sessioni". A list of abstract nouns hides what happens. Keep the items that carry a fact, and say what is done to each.
- **Enthusiasm markers.** Exclamation points, emoji decoration, "Great question".

Never ask a draft for hooks, rhetorical questions, or punchy closings, because asking for them produces these patterns.

## How SparkFabrik sounds

Write as practitioners explaining how something works in production. The reader is a capable professional deciding under constraints. Inform them; never persuade or perform.

- **Describe, do not promise.** Say what happens, who does it, with what, and when. A claim about quality, speed, or savings needs a number and its source; without one, describe the mechanism and leave the claim out.
- **Use only the facts you have.** When the source gives no mechanism, state the fact plainly and stop. Never add an explanation of how a tool works, a step, or a benefit to make a sentence sound concrete.
- **Concrete over abstract.** A named tool, step, owner, or number beats a category noun. "Merge requests run the unit tests and need one approval before merge" beats "rigorous quality processes".
- **Keep uncertainty honest.** Estimates stay estimates, unknowns are said as unknowns, and a trade-off names both options and why one was chosen.
- **Write in the language of the text.** English and Italian follow the same rules. Italian examples of the patterns are in `references/voice.md`.

Who you are writing for sets the person and the register:

| Reader                                                     | Person                                                                                                     | Register                                                                                                                                                                                         |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Colleague (Slack, issue, internal doc, README)             | First person: "I", "we", "io", "noi"                                                                       | Direct, as to a teammate. Lead with the update or the ask.                                                                                                                                       |
| Reviewer (PR/MR)                                           | The change is the subject                                                                                  | What changes, what to check, what was verified.                                                                                                                                                  |
| Upstream maintainer (drupal.org, open-source issue queues) | First person singular, as a contributor                                                                    | Follow the project's conventions and language. No company promotion.                                                                                                                             |
| Client, technical                                          | Documents: SparkFabrik in the third person, named where roles differ; elsewhere the activity or impersonal | Mechanisms, prerequisites, limits, trade-offs.                                                                                                                                                   |
| Client, executive                                          | Same as technical                                                                                          | Lead with the decision, cost, risk, and timing; the mechanism in a sentence.                                                                                                                     |
| Client email                                               | The author in the first person; address people by name                                                     | Follow the register the client uses. One request or update per email.                                                                                                                            |
| Bad news or incident update to a client                    | As in a client email                                                                                       | Impact and time window first, then what is known, what is not, and the next step with its date when you have one. No minimizing, no blame, no guessing at causes, no promise you were not given. |
| Talk                                                       | The speaker in the first person singular                                                                   | A practitioner's account; slides stay impersonal.                                                                                                                                                |

## Air: paragraphs and whitespace

- One idea per paragraph. One to three sentences, then a blank line. Documents for clients follow the paragraph rules of `references/voice.md`.
- A paragraph over three sentences gets split, or restructured into a list.
- Blank line before and after every heading, list, and code block.
- Prefer a full stop over a subordinate-clause chain. Two short sentences beat one long one.

## Lists and visual structure

- Use a list when the reader needs to compare or follow several items. Cut unnecessary items before choosing a layout.
- Use **bold lead-ins** when they help scanning. Plain bullets are enough for short feature lists. Two available shapes:
  - Label plus period: `- **The script-name contract.** Every generated app exposes ...`
  - Verb: `- **builds** each app's dev image (from its build/Dockerfile)`
- In issue checklists, including tasks and acceptance criteria, start each detailed item with a short **bold outcome** followed by a period. Use this when the item also explains scope, constraints, or acceptance criteria. Keep simple one-line checklist items plain.
- Ordered processes: introduce with a colon line ("The deploy triggers, in order:") followed by steps.
- In longer documents, a key instruction can have a bold lead-in: `**Rule of thumb:** if a file says "do not edit", edit the generator instead.`

## Sentence-level rules

- Active voice with a concrete subject: "the script builds the image", not "the image is built by the script".
- Name the thing in backticks: file paths, commands, flags, config keys, environment variables, hostnames and domains, ports, branch names, versions, labels, cloud project and resource names, and exact error strings. A reader then sees at a glance which words are literal values to copy or search for. Keep links, issue and PR/MR references, and people mentions out of backticks, because code formatting stops them from linking.
- Cut hedges and filler: basically, essentially, simply, just, actually, very, quite.
- Plain verbs: use, run, build, check (not utilize, orchestrate, facilitate).
- Prefer sentences under 20 words. Do not pack several clauses into one sentence to meet a sentence limit.
- State each fact once. Delete padding rather than redistributing it into headings or bullets.
- **In Italian, keep the technical terms Italian engineers say in English.** Write "dashboard", "deploy", "repository", "branch", never "cruscotto", "dispiegamento", "archivio", "ramo". Words with an ordinary Italian use stay Italian: "rilascio", "specifica", "aggiornamento". The list is in [references/glossary.md](references/glossary.md).

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

## Documents for clients

Before writing a document SparkFabrik sends to a client (offer, study, report, handover, deck, talk), in Italian or in English, read [references/voice.md](references/voice.md) and [references/glossary.md](references/glossary.md). They add:

- **Who is talking.** SparkFabrik in the third person or impersonally, never "noi" or "we"; the speaker in the first person in a talk.
- **Facts, not claims.** Facts only from a source the user gave, no marketing words, no announcements or slogans.
- **The patterns above with Italian examples**, the banned Italian openers, and how to review a draft without rewarding them.
- **Length and formatting** of a document: paragraph length, headings that name their topic, bold that carries the skim, `**Label:** text` items.
- **The vocabulary** of SparkFabrik's practice, with the concrete basis each business term needs.

Messages, issues, PR/MR descriptions, comments, READMEs, and internal docs follow this file only.

When you rewrite a sentence, keep what it says: numbers, dates, names, quotes, links, and hedges ("about", "may", "circa") stay identical.

The `scripts/` directory holds the check that the `sf-docs` plugin runs on its documents. Outside `sf-docs`, do not run it. The patterns above guide the writing, and you judge each sentence in context.

## Self-check before returning any prose

1. The opening sentence states the change, problem, answer, or required action.
2. Every sentence adds a needed fact. No implementation story or repeated summary survives in a short artifact.
3. The text meets its word limit, excluding attribution and reference lines, unless an explicit exception applies. Shorter is better when the meaning stays clear.
4. Sentences use familiar words and concrete verbs. No blacklist word, invented jargon, or filler survives.
5. No em or en dash survives outside quotations and code. Paragraphs have three sentences or fewer, except in documents for clients, which follow `references/voice.md`.
6. Check that formatting makes the change easier to scan without repeating facts or adding empty sections. The phrases a scanning reader must not miss are bold, and every kept identifier is code.
7. Detailed issue checklist items have short bold outcomes; simple checklist items remain plain.
8. Check the actual outgoing body before a tool call, including text generated from commits. Do not append extra explanations in a follow-up comment.
9. If the artifact is a `.md` file, run the formatter per `auto-format-doc`. Formatting does not replace the content check.
10. For a PR/MR description, confirm that you read and applied the required PR/MR reference.
11. For text that GitHub, GitLab, or Slack will render, confirm that you applied the platform reference.
12. No paragraph leans on the machine-written patterns listed above, and the person and register fit the reader.
13. For a document for a client, confirm that you applied `references/voice.md` and `references/glossary.md`.

## Interaction with other skills

This skill is the baseline for every other skill that writes prose. Whenever another skill composes, rewrites, or reviews human-facing text (issues, PRs/MRs, commits, docs, Slack messages, reports), load this skill first and apply its rules underneath that skill's specific guidance. This holds for skills from any part of the harness and for locally installed skills, not only the ones named below.

Some examples of how the baseline composes with specific skills:

- **CLI writing rules.** `gh` and `glab` include the short-artifact rules directly so they do not depend on a second skill load. Keep those rules aligned with this skill.
- **PR/MR descriptions.** This skill owns the task-specific reference for PR/MR descriptions. Tools and guards should load this parent skill, then follow its reference routing instead of treating the reference as another skill.
- **Client documents.** The `sf-docs` plugin (offers, documents, decks, talks) copies `references/voice.md`, `references/glossary.md` and the check from this skill and runs the check before rendering. Change them here, then sync the plugin.
- **Mechanical layout.** The `auto-format-doc` skill handles mechanical markdown layout (prettier): this skill decides what the prose says and how it is structured, the formatter normalizes whitespace and syntax afterwards.
- **Domain overlays.** Skills that own a document type (issue writing, ADRs, postmortems, changelogs) add their structure and domain rules on top; this skill keeps governing the sentences inside that structure.

Document skills can require structure for ADRs, postmortems, and specifications. Their longer formats do not carry over to issues, PR/MR descriptions, comments, or changelog entries. For short artifacts, only the exceptions listed above allow extra detail.

The plain-prose override still applies: artifacts are written in complete, well-structured prose, in the language of the text, even when a terse conversational style (for example a `CAVEMAN MODE ACTIVE` session reminder) is active. The terse style governs chat replies, never the artifacts. Do not toggle the style; write the artifact in full prose and resume the terse style in chat.
