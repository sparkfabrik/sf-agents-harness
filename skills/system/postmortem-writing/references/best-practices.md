# Postmortem best practices

Distilled domain knowledge for writing high-quality software incident and
product-failure postmortems. Sources are Google SRE, PagerDuty, Atlassian,
GitLab, Etsy (Allspaw), and incident.io. See the "Sources" section at the end.

## Blameless culture

The single most important principle. A blameless postmortem focuses on the
contributing causes of an incident **without indicting any individual or team**.
It assumes everyone involved had good intentions and did the right thing with the
information they had at the time.

- **Fix systems, not people.** "You can't 'fix' people, but you can fix systems
  and processes to better support people." Every remediation targets a system or
  process, never a person.
- **Blame drives information underground.** If people fear punishment, they hide
  the details you need to understand the failure. Removing blame lets people
  escalate and give full accounts.
- **First Story vs. Second Story** (Allspaw). A First Story treats human error as
  _the cause_ ("be more careful"). A Second Story treats human error as _the
  effect_ of deeper systemic vulnerabilities, and asks why the person's actions
  made sense to them at that moment. Always write the Second Story.
- **Just Culture redirects accountability.** Accountability is not eliminated; it
  moves from "who is at fault for the failure" to "who owns the fix," with the
  authority to improve safety.
- **Avoid hindsight bias.** Judge decisions by the information available at the
  time, not by the outcome.

### Blameless language reframing

| Blameful (avoid)                     | Blameless (use)                                                                  |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| "Engineer X deployed buggy code."    | "The CI/CD pipeline did not catch the bug before production."                    |
| "On-call was slow to respond."       | "Alert noise caused fatigue, delaying triage of the critical signal."            |
| "The team missed the warning signs." | "Warning signs weren't in the runbook, making them easy to miss under pressure." |

Phrasing to avoid entirely: naming individuals as personally responsible, "who
broke it," "should have known," and counterfactual "should have" statements.

## Canonical structure

Consensus sections across Google SRE, PagerDuty, Atlassian, and incident.io:

1. **Summary** — 2–4 sentences a non-expert understands. Write it last.
2. **Impact** — quantified (see below).
3. **Detection** — how the incident was found; did monitoring catch it.
4. **Timeline** — chronological, UTC, evidence-linked.
5. **Root cause / contributing factors** — usually multiple factors.
6. **Resolution and recovery** — mitigations and the full fix.
7. **What went well / went poorly / got lucky** — honest self-assessment.
8. **Action items** — SMART, owned, tracked.
9. **Lessons learned.**

Keep it simple. Complex templates get abandoned; incident.io's minimal viable set
is Summary → Impact → Timeline → Contributing Factors → What Went Well → Action
Items.

## Timeline

- All timestamps in **UTC**, chronological order.
- Anchor to the lifecycle: contributing factor begins → detection/alert →
  escalation → mitigation → resolution.
- Each entry should link the evidence it is drawn from (a metric, a graph, a
  chat message), not memory.
- Write it fast — start within 24 hours while context is fresh. The longer you
  wait, the more narrative replaces evidence.
- Never open a review meeting with a blank timeline; pre-populate it.

## Impact quantification

State impact in measurable terms, not adjectives:

- Users or accounts affected (count or percentage).
- Duration of user-visible impact.
- Error rate, failed/dropped requests.
- Revenue impact, SLA breaches, SLO / error-budget consumed.
- Support tickets raised (with links).
- Data impact: loss, corruption, or exposure — or explicitly "none."

## Detection and response metrics

State which metric you mean — MTTR is ambiguous.

- **TTD (Time to Detect):** impact begins → team is aware.
- **MTTA (Time to Acknowledge):** alert triggers → responder acknowledges.
- **TTM (Time to Mitigate):** detect + engage + fix (until impact stops).
- **MTTR** has four meanings — Respond, Repair, Recover, Resolve. "Time to
  Resolve" spans incident start through the root-cause fix. Name the one you use.
- **MTBF (Mean Time Between Failures):** average uptime between incidents.

Lifecycle ordering: detect → acknowledge → respond → mitigate → repair/recover →
resolve.

## Root cause analysis

Prefer **"contributing factors"** over "root cause." Failures arise from multiple
interacting conditions, not a single broken part. Single-cause framing
consistently produces weaker postmortems and weaker remediation.

- **Five Whys** — ask "why?" iteratively down the causal chain. Best for
  **linear** chains. Five is a rule of thumb, not a hard rule.
  - Worked example: service degraded → DB CPU at 100% → full table scan → new
    code queried an unindexed column → pipeline has no query-performance check →
    code review has no query-performance standard. The result is two actionable
    _process_ gaps, not "engineer error."
- **Fishbone / Ishikawa** — group causes into categories to uncover several root
  causes. Best for **complex, interrelated** incidents. Often combined with Five
  Whys (Fishbone to enumerate branches, Five Whys to drill each).
- Push each "why" until you reach a system or process condition you can change.

## Action items

Every action item must be **SMART**: Specific, Owned, Due-dated, Prioritized —
and tracked in the issue tracker with a link.

- **Specific:** "Add rate limiting to `/search` at 100 req/s," not "improve rate
  limiting."
- **Owned:** one named person, never "the team."
- **Due-dated:** a calendar date, not "soon" or "Q2."
- **Tracked:** a linked ticket with a verifiable end state and measurable success
  criteria.
- Separate **preventative** (removes the whole class of failure) from
  **mitigative** (reduces impact if it recurs) and **remediation** (one-off
  cleanup).
- Move items into the tracker immediately with owners and due dates. Suggested
  SLAs: P1 within 30 days, P2 within 60, P3 within 90.
- Google requires at least one high-priority bug for any user-affecting outage.

## When to write a postmortem

Define trigger criteria before an incident. Common gates:

- User-visible downtime or degradation beyond a threshold.
- **Data loss of any kind.**
- On-call intervention (rollback, traffic rerouting).
- Resolution time exceeding a threshold.
- A monitoring failure (found manually, not by alerting).
- Severity: many orgs mandate a postmortem for all SEV1/SEV2; Atlassian mandates
  one for every incident of SEV2 or higher.
- **Near-misses** — capture latent risk before it causes an outage.

## Anti-patterns

- **Blame** — naming individuals; produces "be more careful" conclusions instead
  of systemic fixes.
- **Vague action items** — "improve the deployment pipeline" with no owner, date,
  or ticket.
- **Team-owned action items** — no single named owner means nobody owns it.
- **Stopping at the first root cause** — forcing a single cause obscures
  systemic patterns.
- **Hindsight bias** — judging past decisions by their outcome.
- **Postmortem theater** — writing to satisfy process; if under ~50% of action
  items complete, the postmortems are not changing anything (target ≥80%).
- **Orphaned action items** — living in a doc nobody reopens, so the incident
  recurs.
- **Writing it too late** — narrative replaces evidence; reports become thin.

Program health metrics: action-item completion rate (>80%), incident recurrence
rate (<5%), time-to-publish (<48h).

## Sources

- Google SRE Book, "Postmortem Culture: Learning from Failure" (Ch. 15): https://sre.google/sre-book/postmortem-culture/
- Google SRE Workbook, "Postmortem Culture" (Ch. 10): https://sre.google/workbook/postmortem-culture/
- Lunney & Lueder, "Postmortem Action Items," USENIX ;login: Spring 2017: https://sre.google/static/pdf/login_spring17_09_lunney.pdf
- PagerDuty Postmortem Template: https://response.pagerduty.com/after/post_mortem_template/
- PagerDuty Postmortem docs: https://postmortems.pagerduty.com/
- PagerDuty/postmortem-docs (open-source template): https://github.com/PagerDuty/postmortem-docs
- Atlassian Postmortems handbook: https://www.atlassian.com/incident-management/handbook/postmortems
- Atlassian, running a blameless postmortem: https://www.atlassian.com/incident-management/postmortem/blameless
- GitLab Handbook, Incident Management (S1–S4 severity): https://handbook.gitlab.com/handbook/engineering/infrastructure/incident-management/
- Allspaw (Etsy), "Blameless PostMortems and a Just Culture": https://www.etsy.com/codeascraft/blameless-postmortems
- incident.io, SRE incident postmortem best practices: https://incident.io/blog/sre-incident-postmortem-best-practices
- Better Stack, MTTR and incident metrics: https://betterstack.com/community/guides/incident-management/mttr-and-other-incident-metrics/
- Ishikawa diagram: https://en.wikipedia.org/wiki/Ishikawa_diagram
