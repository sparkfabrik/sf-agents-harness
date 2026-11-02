# Severity classification

Severity gates whether a postmortem is required and how urgent the response is.
The template uses **low / medium / high / critical** in its `severity`
frontmatter field. Use those values.

| Severity     | Definition                                                                                                                    | Examples                                                                            |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **critical** | System down. Core services unavailable, users fully blocked, or data at risk. Takes priority over everything until resolved.  | Full outage, checkout down, data loss/corruption, security breach                   |
| **high**     | Major disruption without a full outage. A key feature is broken or a large user group is affected. Limited workarounds exist. | Login failing for a region, search returning errors, payments degraded              |
| **medium**   | Affects functionality without blocking core use. Degraded performance or a non-critical feature misbehaving.                  | Slow page loads, one non-critical feature broken, elevated but tolerable error rate |
| **low**      | Minimal practical impact. Cosmetic issues, edge cases, or a small number of users. Handled alongside planned work.            | UI glitch, typo, rare edge-case bug                                                 |

Mapping to the common SEV / P scheme, if a customer or upstream tool uses it:
critical = SEV1/P1, high = SEV2/P2, medium = SEV3/P3, low = SEV4/P4.

## When a postmortem is required

Write one when any of these applies:

- **critical** or **high** severity.
- Data loss of any kind.
- On-call intervention was needed (rollback, traffic rerouting).
- Resolution time exceeded the agreed threshold.
- The incident was found manually rather than by monitoring.
- A near-miss worth capturing before it becomes an outage.

For **low** / **medium** incidents and near-misses, a shorter write-up is enough:
keep Summary, Impact, Timeline, Root causes, and Action items, and omit the
deeper-analysis sections (Detection, What went well/poorly, resolution detail).
