---
date: [YYYY-MM-DD]
owner: [name, e-mail]
customer: [name]
severity: [low|medium|high|critical]
---

<!--
Blameless postmortem. Describe systems, processes, and the decisions that made
sense at the time, not the people involved. The goal is to learn and prevent
recurrence, never to assign fault.

Fill in what the incident warrants and delete sections that do not apply. Lower
severity incidents and near-misses can keep just Summary, Impact, Timeline, Root
causes, and Action items.
-->

**Owner:** [Name]

**Responders (other than Owner):**

- [Name]
- [Name]

**Customer:** [Name]

**Start date/time:** [YYYY-MM-DD HH:MM] (UTC)

**End date/time:** [YYYY-MM-DD HH:MM] (UTC)

**Title:** [Short, like a board issue title]

## Summary

[Two to four sentences a non-expert can follow: what broke, who was affected, for
how long, and how it was resolved. Write this last, after the details are clear.]

## Impact

Quantify the impact; prefer numbers over adjectives.

- **Duration:** [total user-visible impact, e.g. 47 minutes]
- **Users/customers affected:** [count or percentage]
- **Scope:** [components, applications, regions, features affected]
- **Business impact:** [failed requests, revenue, SLA/SLO or error-budget burn]
- **Data impact:** [loss, corruption, or exposure — or explicitly "none"]

## Timeline

Chronological order, UTC. Cover detection, escalation, mitigation, and
resolution, and link the evidence (metric, graph, chat) behind each entry.

| Time (UTC) | Event                                       |
| ---------- | ------------------------------------------- |
| HH:MM      | [trigger / change deployed]                 |
| HH:MM      | [first customer impact begins]              |
| HH:MM      | [alert fires / issue detected] (TTD marker) |
| HH:MM      | [incident declared, responders engaged]     |
| HH:MM      | [mitigation applied] (TTM marker)           |
| HH:MM      | [full resolution confirmed] (TTR marker)    |

Optional detection/response metrics derived from the timeline: time to detect
(TTD), time to mitigate (TTM), time to resolve (TTR).

## Detection

- How was the incident detected? [alert, customer report, manual observation]
- Did monitoring catch it? If not, why not, and what would have caught it sooner?

## Root cause and contributing factors

Prefer contributing factors over a single root cause; most incidents result from
several interacting conditions. Use the Five Whys on the primary failure, pushing
each answer until it reaches a system or process condition (never a person).

**Five Whys**

1. Why did [the failure] happen? → [because ...]
2. Why did [that] happen? → [because ...]
3. Why did [that] happen? → [because ...]
4. Why did [that] happen? → [because ...]
5. Why did [that] happen? → [root condition]

**Contributing factors**

- [factor 1 — e.g. missing validation on config input]
- [factor 2 — e.g. alert threshold set too high to warn earlier]
- [factor 3 — e.g. rollback runbook was out of date]

## Resolution and recovery

[The mitigations and the full fix that stopped the impact and restored service,
in order. Note anything still being monitored.]

## What went well / what went poorly

- **Went well:** [fast detection, clear ownership, effective mitigation]
- **Went poorly:** [slow detection, unclear runbook, noisy alerts]
- **Got lucky:** [conditions that limited impact but cannot be relied on]

## Action items

Every item must be specific, owned by one named person, due-dated, and tracked
with a linked issue. Prefer preventative fixes over one-off remediation.

| Action                                                  | Type     | Owner  | Due        | Tracking |
| ------------------------------------------------------- | -------- | ------ | ---------- | -------- |
| [concrete change, e.g. add schema validation to config] | Prevent  | @owner | YYYY-MM-DD | #issue   |
| [e.g. lower alert threshold to catch spikes earlier]    | Detect   | @owner | YYYY-MM-DD | #issue   |
| [e.g. update and test rollback runbook]                 | Mitigate | @owner | YYYY-MM-DD | #issue   |

## Notes and references

- [Tracker issue](https://gitlab.example.com/project-name/board/-/issues/000)
- [Other notes…]
