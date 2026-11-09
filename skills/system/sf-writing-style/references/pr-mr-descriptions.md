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

## Show a preview

Add a preview only when it shows a reviewer the result faster than the diff does. Most changes need none: a refactor, a dependency update, a test, or an internal change is already clear from the diff. Judge each change on its own.

A preview can help in cases like these:

- **Generated or rendered output.** For a template, a manifest, or a plan, show the changed part of the output in a `diff` block.
- **API change.** Show one request and its response in `http` or `json` blocks.
- **Log or message format.** Show two or three lines of the new output.
- **Migration.** Show the dry-run or plan output when it is short, never rows of data.
- **Visible interface change or rendered template.** Add a screenshot only when layout or rendering is the point and text cannot show it.

One case always gets a preview. When a PR/MR adds a command-line command, subcommand, or task-runner target, or a flag that changes what a command prints, add a short `### Example` section with the invocation and its output in a fenced `console` block.

Put the preview after the bullets and before the issue reference. Use `### Example` for a command and `### Preview` for anything else.

Every preview follows these rules:

- **Real only.** Use supplied material, or capture the preview from a run of the changed code. Never invent, mock up, or write an illustrative preview. If you cannot produce it, leave it out without comment.
- **Text first.** Text can be searched, quoted, and read by a screen reader. Use an image only when layout, color, or rendering is the point. Write a diagram as a `mermaid` block.
- **Before and after.** Show both only when both were captured, the first from the base branch and the second from this change. Otherwise show the result alone.
- **Trim.** Keep the part a reviewer needs. Replace temporary or machine-specific paths with `~`. Collapse anything longer than about 20 lines in a `<details>` block.
- **Clean.** Before you paste or upload, remove tokens, passwords, keys, cookies, personal data, customer data, and internal hostnames the reader does not need. Capture screens with demo data. Open each image and check all of it, including browser tabs, the address bar, and the terminal prompt. An uploaded file is hard to delete.
- **Stay on the platform.** Upload images with the hosting platform's own attachment feature. For a private repository, first confirm that uploads require authentication; the `gh` and `glab` skills show how. If you cannot confirm it, do not upload: use a text preview, or give the user the image path to attach. Never use an external image host, a paste service, or another repository. Do not commit an image to the branch only to show it.
- **Alt text.** Give every image alt text that says what it shows, such as "Customer list with the date filter open".
- **Capture with what exists.** Use the tools the project or environment already has, such as a headless browser or the test suite's screenshots. Do not add a dependency to produce a preview.
- **One is enough.** Add one preview per change, or two for a before and after pair.

The preview is an allowed expansion beyond the default word limits, like validation evidence.

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
- Test counts, full command lists, logs, and generated reports, except a short preview.
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

### New command

Adds a **`report export`** subcommand that writes report data to a file.

- **`--format`** accepts `csv` or `json`.
- **`--since`** limits the export to rows after a date.

#### Example

```console
$ app report export --format csv --since 2026-01-01
Exported 128 rows to ~/reports/report-2026-01-01.csv
```

Closes #42

### Generated output

Sets a **memory limit** on the worker container.

#### Preview

```diff
 resources:
   limits:
+    memory: 512Mi
```

Closes #42

### Visible change

Adds a **date filter** to the customer list.

#### Preview

![Customer list with the date filter open](/uploads/<hash>/customer-list-date-filter.png)

Closes #42

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
- Is a preview present only when it helps, and is it real, trimmed, and free of secrets and personal data?
- Did stale, out-of-scope, and file-level narration get removed?
