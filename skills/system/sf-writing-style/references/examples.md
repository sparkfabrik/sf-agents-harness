# Short, plain writing examples

Keep the result. Delete the story. Examples omit attribution and reference lines; include them when required.

## PR or MR description

Before:

> The catalogue stops listing vendors per model. It lists models and rules; each run resolves the vendors from OpenRouter metadata. The catalogue JSON removes operators from all models. Terraform adds twelve preconditions, the resolver check changes, and the README documents which fields reviewers can edit. Apply publishes a new secret version and disables version 7.

After:

> Model vendors are now selected automatically from OpenRouter using the catalogue’s rules. Applying this change publishes a new secret version and disables version 7.

The secret change remains because it affects deployment. File names and validation counts do not explain the result.

## Small fix

> Empty passwords now show a **validation message** instead of returning a server error.

One change needs one sentence. Do not manufacture sections or bullets.

## Several visible changes

> Adds an **animated standby state** when no sessions are running:
>
> - Rotating standby message.
> - Stardate display.
> - Scanning animation.

Place a supplied screenshot after the description. The opening states the feature; the bullets explain its visible parts without repeating the opening.

## Required action and validation

> Sessions now expire after **30 minutes of inactivity**.
>
> **Required action:** Replace `SESSION_TTL_SECONDS` with `SESSION_TIMEOUT_MINUTES` before deploying.
>
> **Validation:** Confirmed that active sessions remain open and inactive sessions expire.

Include the validation sentence only when those checks were performed and their result helps the reviewer. Do not replace it with a test count or an implementation walkthrough.

## Essential context

> Keeps invoice downloads available for closed accounts. Customers must still be able to retrieve their billing records.

The second sentence explains a requirement that the behavior alone does not reveal. Include it only when that requirement is supplied or verified. Do not add the investigation history.

## Final scope

Original plan: add customer search and a date filter. Final diff: customer search only. Search was verified manually.

> Adds **customer search** to the dashboard.
>
> **Validation:** Confirmed that searching by customer name returns matching customers.

Describe the final change. The abandoned date filter does not belong in the description.

## Issue

Before:

> During an investigation of the authentication flow, we identified an edge case involving empty password submissions. The current implementation allows the request to reach the password verification layer, where it causes an unhandled exception. We should explore introducing an early validation guard to improve the user experience and prevent this failure mode.

After:

> Submitting an empty password returns a 500 error. Show a validation message instead.

The issue states the trigger, actual result, and wanted result. It does not prescribe an implementation. Even one sentence naming the validator and source line is unnecessary.

## Status comment

Before:

> Following further investigation, I have now implemented the necessary adjustments to the validation logic and updated the corresponding regression coverage. The previously observed failure mode no longer reproduces, and all checks are now passing successfully.

After:

> Fixed empty-password validation. All tests pass.

Use this wording only when the fix and test result are confirmed. Do not invent evidence to make a short comment sound complete.

## Changelog entry

Before:

> Improved the robustness of login validation by introducing an early guard clause, consolidating error handling, and adding regression tests for the empty-password edge case.

After:

> Fixed a login error when submitting an empty password.

## Required user action

Before:

> This change removes the legacy environment-variable compatibility shim in favor of a single canonical connection-string configuration surface, simplifying the underlying configuration resolution path.

After:

> Database connections now require `DATABASE_URL`. Replace `DB_HOST`, `DB_USER`, and `DB_PASSWORD` before deploying.

Brevity must not hide a breaking change or the action needed to use it.

## Direct question about implementation

Question:

> Why validate the password before calling the authentication service?

Answer:

> The service throws on an empty password. Validating first lets us return a field error.

Answer the question directly. A request for an explanation permits the needed how or why, not the entire investigation history.
