# PR and MR descriptions

Use this reference only when drafting, rewriting, or publishing a pull request or merge request description. The parent `sf-writing-style` skill remains authoritative for voice, factual discipline, and formatting.

## Read sources in this order

1. Treat the final diff as the source of truth for scope.
2. Use the linked issue or task for purpose, constraints, and required outcomes.
3. Include only validation that was observed or supplied.
4. Use commit messages and old descriptions as hints. Remove stale or out-of-scope claims.

## Build a review map

Before drafting, make a private coverage checklist from the explicit requirements and final diff. Include the outcome, public contracts, compatibility or migration details, dependencies that enable the behavior, scope boundaries, and supplied validation. Use the checklist to protect load-bearing facts while trimming prose; do not paste it into the description.

1. State the outcome and why it matters in the opening sentence or short paragraph.
2. Group the change into reviewer-relevant themes, not files or commits.
3. Surface breaking changes, compatibility limits, migrations, rollout steps, or required actions.
4. State useful validation without command transcripts, logs, or test inventories.
5. Check that every explicit requirement, major subsystem, public contract, and scope boundary appears once.

The description should help a reviewer decide where to focus. It should not narrate how the author reached the result.

## Match the shape to the change

- **Small change.** Use one sentence. Add no heading.
- **Medium change.** Use a lead sentence or short paragraph, followed by two to five bullets when the changes are easier to scan separately.
- **Complex or breaking change.** Use a lead paragraph, then `What changes`. Add `Breaking changes`, `Rollout`, or `Validation` only when the section has useful content.

There is no hard word limit for complex descriptions. Use the shortest description that preserves the review map. The parent skill's 80-word default applies to uncomplicated changes, not as a reason to omit major scope, migration steps, or validation.

## Choose useful detail

Include details that define the public contract:

- User-visible behavior and operational impact.
- Public interfaces, commands, flags, configuration keys, and accepted values.
- Dependency or package changes that make the new contract available.
- Compatibility, migration, rollout, and rollback requirements.
- Security or data-handling consequences supported by the diff.
- Verified validation that helps assess risk.

Leave out details that make the description read like a patch inventory:

- File-by-file or commit-by-commit summaries.
- Internal function names, variables, source lines, or helper structure.
- Test counts, full command lists, logs, and generated reports.
- Investigation history, rejected approaches, and workflow narration.
- Generic tables or diagrams that do not make a complex relationship clearer.

## Examples

### Small fix

Rejects empty passwords with a validation message instead of returning a 500 error.

### Medium feature

Adds **export controls** for report data:

- Date-range selection.
- CSV download.
- Remembered export preferences.

### Complex configuration change

Moves environment routing into a single deployment configuration so each environment has one explicit target and validation contract.

#### What changes

- Replaces separate routing keys with one environment map.
- Applies the same target selection to scheduled and manual deployments.
- Limits credentials and generated configuration to the selected environment.
- Exposes the resolved target through the deployment command.

#### Breaking changes

Remove the retired keys and define the new environment map before the next deployment.

#### Validation

Verified configuration parsing and deployment selection for the supported environments.

## Final check

- Can a reader understand the outcome without the task conversation?
- Does the opening explain why the change exists?
- Does every major change group appear once?
- Does every explicit requirement and scope boundary remain visible?
- Are breaking changes and required actions easy to find?
- Is every validation claim factual and useful?
- Did stale, out-of-scope, and file-level narration get removed?
