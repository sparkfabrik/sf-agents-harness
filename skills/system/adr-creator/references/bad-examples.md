# Bad ADR Examples (Anti-Patterns)

These examples demonstrate common mistakes when writing ADRs. Each is followed by
an explanation of what went wrong and how to fix it. **Never produce ADRs that look
like these.**

---

## Anti-Pattern 1: Bullet-list ADR

```markdown
# 5. Redis for caching layer

Date: 2026-03-25

## Status

Accepted

## Context

- Site gets 50k requests/hour during peak
- Database cache adds 200ms latency per request
- Need caching solution
- Evaluated Redis and Memcached

## Decision

We will use Redis as the caching backend, replacing Drupal's default database cache.

Redis was chosen over Memcached because:

- We also need queue processing
- Redis supports both caching and queues
- Memcached doesn't support queues

## Consequences

- Page load latency drops significantly
- Redis serves as shared backend for caching and queue processing
- Additional infrastructure dependency is introduced
- Team needs operational knowledge for Redis
- Drupal's `redis` contrib module required
```

### What went wrong

- **Bullet lists everywhere.** Nygard explicitly says: "Bullets are acceptable
  only for visual style, not as an excuse for writing sentence fragments." This
  ADR reads like meeting notes, not a document for a future developer.
- **Context is a feature list, not a narrative.** It lists facts but doesn't
  explain the tension between them. Why is 200ms a problem? What trade-offs
  exist? A future reader gets data points but no story.
- **Decision mixes in justification.** "Redis was chosen over Memcached because…"
  belongs in the Context section. The Decision should state _what_ was decided,
  not re-argue _why_.
- **Consequences are all one-liners.** No exploration of how each consequence
  affects the project. "Additional infrastructure dependency" — so what? What
  does that mean in practice?

### How to fix it

Rewrite each section as prose paragraphs. The Context should read like a brief
narrative explaining the situation and tensions. The Decision should be a clear
statement of action. The Consequences should explore implications in full
sentences, covering what gets better, what gets harder, and what stays the same.

---

## Anti-Pattern 2: Advocacy masquerading as context

```markdown
# 7. Choosing the Best Framework: Next.js

Date: 2026-03-25

## Status

Accepted

## Context

We needed to pick a modern, well-supported framework for our frontend. Next.js is
the most popular React framework with the best deployment story. It has the largest
community, the most tutorials, and the strongest company backing (Vercel). React
Server Components are the future of web development, and Next.js is the only
framework that supports them properly.

Remix is a decent alternative but lacks the deployment integration. SvelteKit
requires learning a completely new language which would be impractical.

## Decision

We will use Next.js with the App Router.

## Consequences

Next.js will allow us to build faster, deploy easier, and maintain the application
with less effort. The team is already familiar with React so there's no learning
curve. Vercel gives us automatic deployments and preview environments.
```

### What went wrong

- **Title is a sentence, not a noun phrase.** "Choosing the Best Framework:
  Next.js" narrates an action and pre-judges the outcome. A proper title would
  be "Next.js with App Router for Frontend."
- **Context is a sales pitch.** "Most popular," "best deployment story,"
  "strongest company backing," "the future of web development" — these are
  opinions, not forces. The Context should describe facts and tensions
  neutrally, even if the eventual decision seems obvious.
- **Alternatives are dismissed, not explored.** "Remix lacks deployment
  integration" and "SvelteKit requires learning a completely new language" are
  oversimplifications presented as conclusions. Context should describe what
  each alternative offers and let the tensions speak for themselves.
- **Consequences are only positive.** "Build faster, deploy easier, maintain
  with less effort" — no honest accounting of trade-offs. What about Vercel
  vendor lock-in? App Router's learning curve? Larger bundle sizes vs Svelte?
  Every decision has downsides; omitting them makes the ADR useless for future
  reassessment.
- **Decision is too terse.** One sentence with no detail about scope, deployment
  target, or version expectations. A future developer doesn't know if this
  means self-hosted Next.js or Vercel-deployed, Pages Router or App Router
  (despite the title), or what React version is expected.

### How to fix it

Rename the title to a neutral noun phrase. Rewrite the Context to present each
alternative's strengths and weaknesses factually, naming the specific tensions
(team experience vs innovation, deployment convenience vs vendor coupling).
Expand the Decision to include deployment strategy and scope. Add negative and
neutral consequences alongside the positives.

---

## Anti-Pattern 3: Passive voice and vague decision

```markdown
# 12. Database Selection

Date: 2026-01-15

## Status

Accepted

## Context

A database needs to be selected for the project. Various options were considered
including PostgreSQL, MySQL, and SQLite. It was determined that the requirements
include JSON support, full-text search, and scalability.

## Decision

PostgreSQL has been selected as the database. It was felt that this would be the
best option given the requirements.

## Consequences

- The database will support JSON
- Full-text search will be available
- The team will need to learn PostgreSQL
```

### What went wrong

- **Passive voice throughout.** "A database needs to be selected," "it was
  determined," "PostgreSQL has been selected," "it was felt" — who decided?
  Who determined? Passive voice hides ownership and reads like a bureaucratic
  memo. Nygard's format demands active voice: "We will use PostgreSQL."
- **Context is procedural, not descriptive.** It describes the decision-making
  process ("options were considered," "it was determined") instead of the forces
  at play. Context should explain _why_ the decision matters, not _how_ the
  meeting went.
- **Decision is backward-looking.** "Has been selected" is past tense and
  passive. The Decision section should be forward-looking and active: "We will
  migrate to PostgreSQL" or "We will use PostgreSQL 16 as the primary database."
- **Consequences are bullet fragments restating requirements.** "The database
  will support JSON" isn't a consequence — it's a requirement that was already
  mentioned. Consequences should describe what _changes_ as a result of the
  decision: migration effort, new operational requirements, doors opened or
  closed.

### How to fix it

Rewrite in active voice with the team as subject. Replace procedural context
with a description of the forces (data complexity, search needs, team skills).
Make the decision forward-looking and specific. Write consequences as prose
paragraphs exploring real impacts — both positive and negative.

---

## Quick Reference: Common Mistakes

| Mistake                                | Why It's Bad                                        | Fix                                        |
| -------------------------------------- | --------------------------------------------------- | ------------------------------------------ |
| Bullet-list sections                   | Encourages sentence fragments, loses narrative flow | Write full paragraphs                      |
| Advocacy in Context                    | Biases the reader, makes reassessment harder        | State facts and tensions neutrally         |
| Only positive consequences             | Hides trade-offs, useless for future decisions      | Always include negatives and neutrals      |
| Passive voice in Decision              | Hides ownership, sounds bureaucratic                | Use "We will…" with active verbs           |
| Sentence/verb titles                   | Hard to scan, pre-judges the outcome                | Use short noun phrases                     |
| Mixing justification into Decision     | Muddies the boundary between why and what           | Keep "why" in Context, "what" in Decision  |
| One-sentence Decision                  | Leaves scope ambiguous                              | Include enough detail for a future reader  |
| Restating requirements as Consequences | Adds no information                                 | Describe what changes, not what was wanted |
