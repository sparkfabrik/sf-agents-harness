---
name: adr-creator
description: >
  Create Architecture Decision Records (ADRs) following Michael Nygard's format
  through a guided conversational workflow. Use this skill whenever the user
  mentions ADR, architecture decision, architectural decision record, wants to
  document a technical decision, or asks to record a design choice. Also trigger
  when the user says things like "let's document this decision", "we should
  write this down as an ADR", "create a new ADR", or "I want to record why we
  chose X". Even if the user just says "new decision" or "document this choice"
  in a project context, this skill is likely what they need.
---

# ADR Creator

A guided workflow for creating Architecture Decision Records following
[Michael Nygard's format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

ADRs are short text files that capture architecturally significant decisions —
those that affect structure, non-functional characteristics, dependencies,
interfaces, or construction techniques. Each record describes forces at play and
a single decision in response, making the motivation behind past decisions
visible to everyone on the team, present and future.

## Workflow overview

1. **Detect environment** — find the ADR directory and check for `adr-tools`
2. **Gather context** — ask the user about forces and constraints
3. **Capture the decision** — what was decided and why
4. **Check for superseded ADRs** — does this replace a previous decision?
5. **Explore consequences** — positive, negative, and neutral outcomes
6. **Confirm status** — proposed, accepted, deprecated, or superseded
7. **Create the file** — using `adr-tools` or manually

## Step 1: Detect the environment

Before asking any questions, figure out the lay of the land.

### Check for adr-tools

```bash
which adr 2>/dev/null && adr help || echo "NOT_INSTALLED"
```

If `adr-tools` is **not installed**, tell the user:

> I noticed `adr-tools` isn't installed. It's a lightweight CLI that manages
> ADR numbering and linking automatically. Want me to help install it?

If they say yes, see `references/adr-tools-setup.md` for installation
instructions per platform. If they decline, proceed with manual file creation —
the skill works either way.

### Find the ADR directory

Look for an existing ADR directory. Common locations:

```bash
find . -maxdepth 3 -type d \( -name "adr" -o -name "ADR" -o -name "decisions" \) 2>/dev/null | head -5
```

Also check for existing ADR files:

```bash
find . -maxdepth 4 -name "*.md" -path "*/adr/*" -o -name "*.md" -path "*/ADR/*" -o -name "*.md" -path "*/decisions/*" 2>/dev/null | head -10
```

If found, scan existing ADRs to determine:

- The current numbering (so the next ADR gets the right number)
- The naming convention used (e.g., `0001-title.md` vs `adr-001-title.md`)
- A brief summary of each existing ADR (title + status) — you'll need this
  when asking whether the new decision supersedes anything

If no ADR directory exists, ask the user where to create one. The Nygard
convention is `doc/adr/` but many projects use `doc/ADR/`, `docs/decisions/`,
or `architecture/decisions/`. Respect whatever the project already uses.

If using `adr-tools` and no directory exists:

```bash
adr init <chosen-directory>
```

### Bootstrap: the first ADR

When initializing ADRs in a project that has none, the very first record
(ADR 1) should always be the meta-decision "Record architecture decisions".
If using `adr-tools`, `adr init` creates this automatically. When working
manually, create it with this standard content:

```markdown
# 1. Record architecture decisions

Date: YYYY-MM-DD

## Status

Accepted

## Context

We need to record the architectural decisions made on this project.

## Decision

We will use Architecture Decision Records, as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

## Consequences

See Michael Nygard's article, linked above. For a lightweight ADR toolset, see Nat Pryce's [adr-tools](https://github.com/npryce/adr-tools).
```

Then proceed to create ADR 2 for the user's actual decision.

## Mermaid diagrams

ADRs can include [Mermaid](https://mermaid.js.org/) diagrams in the Context
and/or Decision sections when a visual would help a future reader understand
the architecture. This is especially useful for:

- Component interaction flows (sequence diagrams)
- System boundaries and dependencies (flowcharts, C4-style)
- State machines or decision trees
- Before/after comparisons of architecture changes

Wrap diagrams in a fenced code block with the `mermaid` language tag. Keep them
focused — a diagram that needs a paragraph of explanation to understand is too
complex. If the decision involves structural changes, consider asking the user
whether a diagram would help clarify the Context or Decision.

## Step 2: Gather context (the "Context" section)

The Context section describes forces at play — technological, political, social,
and project-local. The language should be **value-neutral**, simply describing
facts. Forces are often in tension and should be called out as such.

Ask the user:

> What's the situation or problem that led to this decision? Think about the
> technical constraints, team needs, or project requirements that are creating
> tension.

Guide them toward specifics:

- What technology or architectural area does this affect?
- What constraints or requirements are driving this?
- Were there alternatives considered? (These become forces in the Context)
- Is there tension between competing concerns (e.g., performance vs simplicity)?

The Context section should read like a fair, factual description of the
situation — not an argument for the decision. Think of it as setting the stage
so a future reader understands what pressures existed.

## Step 3: Capture the decision

The Decision section states the team's response to the forces described in
Context. It should use **active voice** and **full sentences**: "We will …"

Ask the user:

> What decision was made? Please describe it as concretely as you can — what
> will be built, adopted, changed, or removed.

Help them frame it in active voice if needed. The decision should be specific
enough that a future developer can understand exactly what was chosen, but not
so detailed that it duplicates implementation docs.

## Step 4: Check for superseded ADRs

Present the list of existing ADRs (titles and statuses) and ask:

> Does this new decision replace, override, or significantly change any of
> these previous decisions?

If yes, identify which ADR(s) are affected. When creating the new ADR:

- If using `adr-tools`: use `adr new -s <number> "Title"` which automatically
  handles the cross-referencing
- If manual: add "Supersedes [ADR N](link)" to the new ADR's Status section,
  and update the old ADR's Status to "Superseded by [ADR M](link)"

## Step 5: Explore consequences

The Consequences section describes the resulting context after applying the
decision. **All consequences should be listed** — positive, negative, and
neutral. This is not a sales pitch for the decision; it's an honest accounting
of what changes.

Ask the user:

> What are the consequences of this decision? Think about:
>
> - What becomes easier or better?
> - What becomes harder or more complex?
> - What new constraints does this introduce?
> - Does this open doors for future changes, or close them?

Consequences of one ADR often become the context for future ADRs — this is
expected and healthy.

## Step 6: Confirm status

Ask the user:

> What's the status of this decision?

Offer these options:

- **Proposed** — stakeholders haven't agreed yet
- **Accepted** — the team has agreed and will proceed
- **Deprecated** — the decision is being phased out (rare for new ADRs)
- **Superseded** — replaced by another decision (rare for new ADRs)

For most new ADRs, the answer will be Proposed or Accepted.

## Step 7: Write the ADR

### Title

ADR titles are **short noun phrases** — not sentences, not verbs. They describe
_what_ was decided, not the action of deciding.

Good: "LDAP for Multitenant Integration"
Good: "Deployment on Ruby on Rails 3.0.10"
Bad: "We decided to use LDAP"
Bad: "Choosing a deployment platform"

### Creating the file

**With adr-tools:**

```bash
# Simple new ADR
adr new "Title of the decision"

# Superseding ADR N
adr new -s N "Title of the decision"
```

This creates the numbered file and opens it. Write the content into the
generated template.

**Without adr-tools (manual):**

Determine the next number from existing files. Create the file following the
project's naming convention (typically `NNNN-kebab-case-title.md`).

### Document format

The document should be one or two pages long, written as if having a
conversation with a future developer. Use **full sentences organized into
paragraphs**. Bullets are acceptable for visual style, but not as an excuse for
writing sentence fragments.

```markdown
# N. Title as Short Noun Phrase

Date: YYYY-MM-DD

## Status

[Proposed | Accepted | Deprecated | Superseded]

[If superseding: Supersedes [ADR N](relative-link)]
[If superseded: Superseded by [ADR M](relative-link)]

## Context

[Value-neutral description of forces at play. Full sentences, full paragraphs.
Describe the tension between competing concerns.]

## Decision

[Active voice: "We will..." Concrete description of what was chosen.]

## Consequences

[All consequences — positive, negative, and neutral. Honest accounting of
what changes as a result of this decision.]
```

### After creation

- Show the user the full ADR content for review
- Ask if they want to adjust anything
- If using `adr-tools`, mention they can run `adr list` to see all ADRs

## Writing guidelines

**Before writing any ADR, read both `references/good-examples.md` and
`references/bad-examples.md`.** These contain annotated examples showing
exactly what to do and what to avoid. Use them as your quality standard.

The following rules come directly from
[Nygard's original article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
and are **non-negotiable**:

- **Value-neutral context**: The Context section describes facts, not arguments.
  It lays out forces without advocating for the decision. Even if the choice
  seems obvious, present the alternatives fairly.
- **Active voice decisions**: "We will use X" not "X was chosen" or "It was
  decided to use X". Active voice makes ownership clear. The Decision section
  must always be forward-looking.
- **Complete consequences**: List negative and neutral consequences alongside
  positive ones. A decision that only has upsides either wasn't analyzed
  carefully or isn't being recorded honestly. Consequences of one ADR very
  likely become the context for subsequent ADRs.
- **Short noun phrase titles**: The title names the decision, it doesn't
  narrate it. Think of it as a label for quick scanning. Not a sentence, not
  a verb phrase.
- **Full sentences in paragraphs**: Write each ADR as if it is a conversation
  with a future developer. This requires good writing style, with full
  sentences organized into paragraphs. **Bullets are acceptable only for
  visual style, not as an excuse for writing sentence fragments.** (Nygard:
  "Bullets kill people, even PowerPoint bullets.")
- **Bite-sized**: One to two pages. If it's longer, the decision might need to
  be split into multiple ADRs. Nobody reads large documents.
- **Numbers are permanent**: ADRs are numbered sequentially and monotonically.
  Numbers are never reused. If a decision is reversed, keep the old record but
  mark it as superseded — it's still relevant to know what _was_ the decision.
- **Keep justification in Context, not Decision**: The Context describes _why_
  (the forces); the Decision states _what_ (the response). Don't re-argue
  the rationale inside the Decision section.
- **Don't restate requirements as consequences**: "The database will support
  JSON" is a requirement. A consequence is what _changes_ as a result:
  migration effort, new operational needs, doors opened or closed.
