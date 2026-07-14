# System Agents

This directory contains system agents distributed to developer workstations via
sparkdock.

## Manual Eval Matrix

These agents do not yet have a dedicated automated evaluation harness in this
repository. Keep a lightweight manual eval matrix whenever you add or revise a
system agent so the prompt contract is tested before distribution.

### the-analyst

- Should trigger: vague feature request that needs domain clarification
- Should trigger: overloaded business terms that need normalization
- Should trigger: workflow or state-transition modeling request
- Should trigger: existing code conflicts with the stated requirement
- Should not trigger: direct implementation request that belongs to The Builder
- Should not trigger: broad architecture discussion that belongs to The
  Architect

### the-builder

- Should trigger: direct implementation request with clear acceptance criteria
- Should trigger: bug fix request that needs code and tests
- Should trigger: refactor request constrained by observable behavior
- Should trigger: follow-up after analysis when implementation can start
- Should not trigger: pure domain clarification that belongs to The Analyst
- Should not trigger: read-only review request that belongs to The Reviewer

### the-reviewer

- Should trigger: single implementation with material findings
- Should trigger: single implementation with no material findings
- Should trigger: two implementations where one is clearly better
- Should trigger: two implementations with competing tradeoffs
- Should trigger: incomplete diff with insufficient static evidence
- Should not trigger: request to fix the code rather than review it

### Quality Checks

- The Analyst produces structured domain output rather than generic
  brainstorming
- The Analyst distinguishes facts, inferences, and recommendations
- The Builder writes or updates tests before implementation for maintained code
- The Builder challenges ambiguous behavior before coding
- The Reviewer reports findings before summary
- The Reviewer distinguishes proven, inferred, and unverifiable claims
- Boundary cases resolve cleanly against The Architect and The Builder
