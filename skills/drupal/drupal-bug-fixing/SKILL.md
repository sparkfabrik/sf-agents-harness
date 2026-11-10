---
name: drupal-bug-fixing
description: "Procedure for fixing a bug in a Drupal project: reproduce it with a check that goes red, confirm the root cause, look for a known fix on drupal.org before writing code, then make the smallest fix and lock it with a regression test. Use when the user reports something broken, failing, throwing or wrong in a Drupal site or module (core, contrib or custom), asks to debug or fix it, or when a Drupal test fails for an unknown reason."
---

# Drupal bug fixing

Fix the cause, not the symptom, and fix it where it lives. A bug in contrib or core
gets a fix in contrib or core, carried as a patch, so it can go upstream; custom code
that works around a module only moves the bug.

The phases run in order. Each one ends on its completion criterion; move to the next
only when it holds.

## Phase 1: Reproduce

Build a **red** check: one command that drives the code path of the bug and fails on
the user's exact symptom. Pick the first that fits:

1. An automated test at the seam that reaches the bug (unit, kernel, functional or
   browser test), in the project's existing test suite when it has one.
2. A drush command (`drush php:eval`, a custom drush script) that triggers the path
   and prints the wrong result.
3. A scripted HTTP request or browser step against the local site, asserting on the
   response, the DOM or the log.

Run it and watch it go red. Then **minimise**: remove data, configuration, modules
and steps one at a time, rerunning after each cut, until every remaining part is
needed for the failure.

Done when you can name one command, already run, that fails on the user's symptom
every time (or at a stable rate for an intermittent bug), and the scenario cannot
shrink further.

If you cannot build a red check, stop. Tell the user what you tried and ask for what
would make it reproducible: access to the environment where it happens, the steps,
a sample of the data (anonymised), or the log lines.

## Phase 2: Root cause

List two or three possible causes, ranked, each with a prediction you can test:
"if X is the cause, changing Y makes the check pass". Show the list to the user
before testing; they often know which one to drop.

Test one prediction at a time, changing one thing per run. Prefer a debugger
(Xdebug) at the boundary that separates the hypotheses; otherwise add logs tagged
with a unique prefix (for example `[DEBUG-7c1e]`) so cleanup is one search.

Done when one cause is confirmed by its prediction and you can say where it lives:
the project's custom code, a contrib module, or core. Note the exact file and the
installed version of the package.

## Phase 3: Upstream first (contrib or core only)

When the cause is in a contrib module or core, search upstream before writing any
code. Answer three questions: is the bug reported, does a fix exist (an MR or a
patch), and is that fix already in a release.

### Lookups

Check once whether the [`drupalorg` CLI](https://github.com/mglaman/drupalorg-cli) is
available: `command -v drupalorg`, or its MCP tools (`issue_search`, `issue_show`,
`mr_list` and the rest) loaded in the session. When it is, load its own skill
(`drupalorg skill:get drupalorg-cli`) and pass `--format=llm` to every read command that accepts it
(`project:release-notes` prints text only).
When it is not, use the web column.

Some projects moved their issues to GitLab work items, and their drupal.org queue
is empty. The CLI handles them: `drupalorg project:issues <project> --limit=1` says
"Project uses GitLab work items", and issue IDs take the form `<project>#<nid>`.
Without the CLI, treat an empty drupal.org queue as a sign of that move and search
`https://git.drupalcode.org/api/v4/projects/project%2F<project>/issues?search=<terms>`.

| Lookup                                   | With the CLI                                                          | Without the CLI                                                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Issues by title                          | `drupalorg issue:search <project> "<terms>" --status=all`             | `https://www.drupal.org/project/issues/<project>?text=<terms>&status=All`                                       |
| Issues by body (error message, function) | Web search: `"<message>" site:drupal.org/project/issues/<project>`    | Same, plus the issue queue page above, which searches bodies too                                                |
| One issue and its comments               | `drupalorg issue:show <nid> --with-comments`                          | `https://www.drupal.org/api-d7/node.json?nid=<nid>` and `https://www.drupal.org/api-d7/comment.json?node=<nid>` |
| MRs for an issue                         | `drupalorg mr:list <nid> --state=all`, then `mr:diff` and `mr:status` | `https://git.drupalcode.org/api/v4/projects/project%2F<project>/merge_requests?state=all&search=<nid>`          |
| Releases                                 | `drupalorg project:releases <project>` (latest per branch only)       | `https://updates.drupal.org/release-history/<project>/current` (every release)                                  |
| Release notes                            | `drupalorg project:release-notes <project> <version>`                 | `https://www.drupal.org/project/<project>/releases/<version>`                                                   |

The CLI issue search matches titles only, so search by error message through the
web in both cases. The drupal.org issue queue page sometimes answers with a bot
challenge; when it does, rely on the web search. To find every release between the
installed version and the latest, use the release history feed: the CLI lists only
the latest release of each branch. Release notes list the issue numbers they fix, so
search them for the issue's node ID.

Done when you have searched issues by title and by the error message across all
statuses, read every candidate issue with its MRs, and checked the release notes of
every release newer than the installed one.

### Paths

Take the first path that applies:

1. **Fixed in a newer release.** Propose updating the package, naming the release that
   carries the fix. The update follows the project's dependency update procedure, for
   example a `drupal-composer-update` skill where one is installed.
2. **A patch or MR exists and applies.** Add it through `cweagans/composer-patches`
   from a file committed to the project, with the issue link in the patch
   description. For an MR, download
   `https://git.drupalcode.org/project/<project>/-/merge_requests/<iid>.diff`; the
   live MR URL changes with every push, so composer never points at it. A patch
   attached to a drupal.org issue keeps a stable URL and can be used directly. Rerun
   the red check.
3. **A patch exists but no longer applies.** Rebase it onto the installed version
   with the `drupal-rebase-mr` skill, then apply it as in path 2.
4. **Nothing exists.** Write the fix in the module or core itself, to contrib MR
   quality: Drupal coding standards, a test in the module's own test suite, and a
   draft issue summary (problem, steps to reproduce, proposed resolution). Carry it
   in the project as a local patch through composer patches. Drupal.org's
   [policy on the use of AI when contributing](https://www.drupal.org/docs/develop/issues/issue-procedures-and-etiquette/policy-on-the-use-of-ai-when-contributing-to-drupal)
   applies to the issue and the MR. With the CLI, its `drupalorg-work-on-issue` skill
   covers the issue fork, branch and MR.

Posting anything on drupal.org (an issue, a comment, an MR, or a CLI command that
posts, such as `issue:comment`, `issue:fork` or `issue:get-access`) needs the user's
explicit OK. Without it, leave the issue summary and the patch ready for the user.

Done when the fix comes from one of the four paths, or the user chose to stop.

## Phase 4: Fix and lock

Make the smallest change that removes the confirmed cause, at the layer where it
lives. If that change is large or alters behaviour other code relies on, describe it
and ask before applying it.

1. Turn the minimised red check into a regression test where the project has a place
   for it: the project's suite for custom code, the module's suite for a contrib fix.
   If no correct place exists, say so.
2. Apply the fix and watch the check go green.
3. Rerun the original, unminimised scenario from Phase 1.
4. Run the project's QA on the changed files (the `drupal-qa` skill covers the fixes).
5. Remove every tagged debug log (search for the prefix) and every throwaway script.

List unrelated problems you noticed (code smells, other bugs, outdated modules) as
follow-ups for the user, outside this change.

Done when the check is green, the original scenario passes, QA passes on the changed
files, and no debug code is left. State the confirmed cause in the commit message or
MR description.
