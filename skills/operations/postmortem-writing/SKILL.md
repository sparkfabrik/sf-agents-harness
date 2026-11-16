---
name: postmortem-writing
description: >
  Guide engineers and product managers through writing high-quality, blameless
  postmortems for software incidents and product failures. Use this skill
  whenever the user mentions a postmortem,
  post-mortem, incident review, incident retrospective, RCA, root cause
  analysis, or wants to document an outage, incident, or product failure. Also
  trigger on phrases like "we had an outage", "write up the incident", "the site
  went down", "document what happened", "blameless retro", "five whys", "what's
  our postmortem for X", or "review this postmortem". Produces a structured
  record covering summary, impact, timeline, root cause and contributing
  factors, resolution, and owned follow-up actions.
---

# Postmortem Writing

A guided workflow for writing blameless postmortems that turn incidents into
durable learning. The output uses `templates/postmortem.md` and covers summary,
quantified impact,
timeline, detection, root cause and contributing factors, resolution, and
concrete, owned action items.

The governing principle is **blameless**: focus on systems and processes, never
on blaming people. Assume everyone acted with good intentions given the
information they had at the time. See `references/best-practices.md` for the full
rationale and language guidance, `references/severity-levels.md` for severity
classification, and `references/examples.md` for contrasting good and bad
examples.

## When to write a postmortem

Recommend one when any of these applies:

- Severity **critical** or **high** (see `references/severity-levels.md`).
- User-visible downtime or degradation beyond a threshold.
- Data loss of any kind.
- On-call intervention was needed (rollback, traffic rerouting).
- Resolution took longer than the team's agreed threshold.
- The incident was found manually, not by monitoring.
- A near-miss worth capturing before it becomes an outage.

For **low** / **medium** incidents and near-misses, keep the shorter form of the
template (Summary, Impact, Timeline, Root causes, Action items) and omit the
deeper-analysis sections.

## Workflow overview

1. **Frame it blamelessly** — set expectations before gathering details.
2. **Classify severity** — pick low/medium/high/critical and confirm a
   postmortem is warranted.
3. **Gather the facts** — metadata, impact, timeline, detection.
4. **Analyze causes** — Five Whys and contributing factors.
5. **Capture resolution and action items** — what fixed it, and what prevents recurrence.
6. **Assemble and review** — fill the template, run the quality checklist.

Work conversationally. Ask for the facts you are missing rather than inventing
them. Never fabricate timestamps, metrics, owners, or ticket numbers; leave the
template placeholders and ask the user to fill them.

## Step 1: Frame it blamelessly

Before collecting details, state the frame:

> This is a blameless postmortem. We describe systems, processes, and the
> decisions that made sense at the time, not the people involved. The goal is to
> learn and prevent recurrence, not to assign fault.

Watch the user's language throughout. If they name individuals as at fault or use
"should have" hindsight framing, reframe it toward systems. Use the reframing
table in `references/best-practices.md`.

## Step 2: Classify severity

Ask what the impact was and map it to **low / medium / high / critical** using
`references/severity-levels.md`. This value goes in the template's `severity`
frontmatter field. Confirm a postmortem is warranted (see "When to write"
above). For low/medium or near-misses, keep the shorter form of the template.

## Step 3: Gather the facts

Fill the template metadata and fact sections, asking for specifics:

- **Metadata** — date, owner (name + e-mail), customer, responders, start and
  end date/time in **UTC**, and a short board-style title.
- **Summary** — what broke, in plain language a non-expert can follow.
- **Impact** — quantify it: duration, users/customers affected (count or %),
  scope (components, applications, regions), business impact (failed requests,
  revenue, SLA/SLO or error-budget burn), and data impact (or explicitly none).
  Push back on adjectives; ask for numbers.
- **Timeline** — reconstruct in **UTC**, chronological order: contributing
  change, first impact, detection, escalation, mitigation, resolution. Ask the
  user to link evidence (metrics, graphs, chat) for each entry.
- **Detection** — how was it found? Did monitoring catch it? If not, why not?

Derive the detection/response metrics from the timeline where useful: TTD (impact
begins → detected), TTM (detected → impact stopped), TTR (impact begins → fully
resolved).

## Step 4: Analyze causes

Fill the **Root cause and contributing factors** section, preferring
**contributing factors** over a single root cause. Most incidents result from
several interacting conditions.

- Run the **Five Whys** on the primary failure, pushing each answer until it
  lands on a system or process condition the team can change (not a person).
- Then enumerate the **contributing factors** — the conditions that combined to
  allow the incident (missing validation, alert set too high, stale runbook).
- For complex incidents with many interacting causes, use a Fishbone/Ishikawa
  grouping to enumerate branches, then Five Whys per branch. See
  `references/best-practices.md`.

Guard against stopping at the first plausible cause and against blaming a person
at any "why".

## Step 5: Capture resolution and action items

- **Resolution and recovery** — the mitigations and the full fix that stopped the
  impact and restored service, in order. Note anything still being monitored.
- **What went well / poorly / got lucky** — an honest self-assessment of the
  response.
- **Action items** — every item must be specific, owned by one named person,
  due-dated, and tracked with a linked issue (the "Notes and references" section
  links the tracker issue). Prefer preventative items (remove the class of
  failure) over one-off remediation; also add detection and mitigation
  improvements. If the user gives vague items ("improve monitoring", "be
  careful"), rewrite them into specific, owned, dated, trackable actions. See the
  action-item examples in `references/examples.md`.

## Step 6: Assemble and review

Fill `templates/postmortem.md`. Write the **Summary last**, after the details are
clear, so it accurately reflects the whole record.

Ask the user where the postmortem should live (docs folder, wiki, tracker issue)
and create the file there. If unclear, save it in the repository or working
directory and tell the user the path.

### Quality checklist

Before calling it done, verify:

- [ ] Language is blameless — no individual named as at fault, no "should have".
- [ ] Severity is set to one of low/medium/high/critical.
- [ ] Summary is understandable by a non-expert and states impact and duration.
- [ ] Impact is quantified, not described with adjectives.
- [ ] Timeline is in UTC, chronological, and covers detection → resolution.
- [ ] Root cause analysis reaches system/process conditions, not people.
- [ ] Contributing factors are listed (not just a single root cause).
- [ ] Every action item is specific, has a named owner, a due date, and a
      tracking link.
- [ ] At least one preventative action item exists for a user-affecting incident.
- [ ] No fabricated timestamps, metrics, owners, or ticket numbers remain.
