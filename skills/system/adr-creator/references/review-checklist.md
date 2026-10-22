# ADR Review Checklist

Use this checklist after drafting an ADR to validate it before finalizing. The core question: **could someone reading this for the first time understand the decision and its implications without asking follow-up questions?**

## Context

- [ ] A reader with no prior context can understand why this decision exists
- [ ] The trigger is clear -- what changed, broke, or is about to break
- [ ] No tribal knowledge is assumed -- acronyms defined, systems named explicitly
- [ ] Links to relevant ADRs, issues, or prior decisions are included where appropriate

## Decision

- [ ] The decision is specific enough to act on ("use X for Y", not "use a better approach")
- [ ] Scope is bounded -- what is included AND what is explicitly out of scope
- [ ] Constraints are explicit where possible

## Consequences

- [ ] Each consequence is concrete, not aspirational
- [ ] Both positive and negative consequences are stated
- [ ] Follow-up work is named, not scripted ("a migration is needed", not the migration steps)
- [ ] Risks are stated with mitigation strategies or acceptance rationale
- [ ] No consequence is a disguised restatement of the decision

## Durability

- [ ] Every sentence would still be true and useful after the change has shipped and been forgotten
- [ ] No commands, tool invocations, or step-by-step release, migration, or rollback sequences
- [ ] No install paths, config file names, hook or class names that merely implement the decision
- [ ] No temporary arrangements ("stays for one release", "a later release removes it")
- [ ] Anything that failed the items above was moved to a how-to, runbook, MR, or release notes, and the ADR links to it

## Meta

- [ ] Status is set correctly (`Proposed` for new ADRs)
- [ ] Date is set
- [ ] Title includes the ADR number: `# N. Title`
- [ ] Title describes the decision, not the problem
- [ ] Filename follows the `NNNN-title-with-dashes.md` convention
- [ ] Content is entirely in English

## Common Failure Modes

| Symptom                                      | Root Cause                                                          | Fix                                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| "Improve performance" as a consequence       | Vague intent                                                        | Ask: "improve which metric, by how much?"                                                        |
| Only one option mentioned                    | Decision already made, ADR is post-hoc                              | Ask: "what did you reject and why?"                                                              |
| Context reads like a solution pitch          | Skipped problem framing                                             | Rewrite context as the problem, move solution to Decision                                        |
| Consequences are all positive                | Cherry-picking                                                      | Ask: "what gets harder? what is the maintenance cost?"                                           |
| "We decided to use X" with no why            | Missing justification                                               | Ask: "why X over Y?" -- the "over Y" forces comparison                                           |
| Decision or Consequences read like a runbook | User described the rollout instead of the decision                  | Ask: "what decision do these steps implement, and why was it needed?" Move the steps to a how-to |
| Record goes stale at the next release        | Implementation state or temporary arrangements recorded as decision | Keep the commitment and its boundaries; drop paths, hooks, and "for one release" clauses         |

## Quick Scoring

Count the checked items above. This is a conversation tool, not a gate.

- **All checked**: Ship it.
- **1-3 unchecked**: Discuss the gaps. Most can be fixed quickly.
- **4+ unchecked**: The ADR needs more work. Go back to the Context-gathering step for the fuzzy areas.
