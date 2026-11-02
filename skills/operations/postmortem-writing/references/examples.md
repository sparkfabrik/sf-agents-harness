# Postmortem examples

Contrasting examples showing what distinguishes a high-quality, blameless
postmortem from a weak, blameful one.

## Summary

**Weak**

> The site went down for a while because someone pushed a bad config. It's fixed
> now.

Problems: no quantified impact, no duration, assigns blame ("someone"), vague.

**Strong**

> On 2026-03-12 a configuration change disabled connection pooling on the primary
> database, exhausting connections and returning HTTP 500 for roughly 12% of
> checkout requests over 47 minutes (14:03–14:50 UTC). Service was restored by
> reverting the change. No data was lost.

Why it works: non-expert-readable, quantified impact and duration, systems-focused.

## Impact

**Weak**

> A lot of users were affected and it was pretty bad.

**Strong**

> - Duration: 47 minutes (14:03–14:50 UTC)
> - Users affected: ~12% of active users attempting checkout
> - Failed requests: ~38,000 HTTP 500 responses
> - Revenue: an estimated €4,200 in abandoned checkouts
> - SLO: consumed 60% of the monthly checkout error budget
> - Data impact: none

## Timeline

**Weak**

> Around 2pm things broke, we looked into it, and eventually fixed it.

**Strong** (UTC, chronological)

> | Time (UTC) | Event                                                      |
> | ---------- | ---------------------------------------------------------- |
> | 14:00      | Config change #4821 deployed to production                 |
> | 14:03      | Checkout error rate begins climbing (first user impact)    |
> | 14:11      | Alert fires on 5xx rate (TTD = 8 min)                      |
> | 14:14      | Incident declared high severity, responders paged          |
> | 14:42      | Root of connection exhaustion identified in change #4821   |
> | 14:50      | Change reverted, error rate returns to baseline (resolved) |

## Root cause

**Weak — single cause, blameful**

> Root cause: an engineer disabled connection pooling.

**Strong — contributing factors, blameless**

> Five Whys:
>
> 1. Why did checkout return 500s? → The database refused new connections.
> 2. Why? → The connection pool was exhausted.
> 3. Why? → Config change #4821 set `pool.enabled = false`.
> 4. Why did that reach production? → The config schema has no validation for
>    pooling flags, and CI does not run a load check on config changes.
> 5. Why was it not caught in review? → The review checklist has no entry for
>    connection-pool settings.
>
> Contributing factors:
>
> - Config loader accepts `pool.enabled = false` without validation.
> - No load or connection-count check in the config deploy pipeline.
> - Alert threshold on connection count was set too high to warn earlier.

## Action items

**Weak**

> - Be more careful with config changes.
> - Improve monitoring.

Problems: not specific, no owner, no date, no tracking, targets people.

**Strong**

> | Action                                                               | Type    | Owner  | Due        | Tracking |
> | -------------------------------------------------------------------- | ------- | ------ | ---------- | -------- |
> | Add schema validation rejecting `pool.enabled = false` in production | Prevent | @alice | 2026-03-26 | #5102    |
> | Add a connection-count check to the config deploy pipeline           | Detect  | @bob   | 2026-04-09 | #5103    |
> | Lower the connection-count alert threshold to 80% of pool max        | Detect  | @carol | 2026-03-19 | #5104    |
