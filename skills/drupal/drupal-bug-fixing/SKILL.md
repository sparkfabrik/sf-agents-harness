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
needed for the failure. Minimise on a disposable copy: a test fixture, or a clone
of the site and its database. Uninstalling a module deletes its configuration and
data, so keep the user's working site intact; Phase 4 reruns the original scenario
there.

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

### Where the issues live

Most projects keep their issues on drupal.org. Some moved them to GitLab work items
on `git.drupalcode.org`, and their drupal.org queue stops getting new issues. Check
which case applies before searching: `drupalorg project:issues <project> --limit=1`
prints "Project uses GitLab work items" for a moved project. Without the CLI,
confirm the current tracker from an explicit migration notice or an `api-d7`
issue lookup returning a `new_url`; an empty or stale queue alone is not evidence
of a move. Search the current tracker and the old drupal.org queue for issues
from before the move.

### Search

Search the full history of the queue, across all statuses, by title and by the error
message or function name:

- **drupal.org queue:** the issue queue page
  `https://www.drupal.org/project/issues/<project>?text=<terms>&status=All`, which
  searches titles and bodies, and a web search such as
  `"<message>" site:www.drupal.org/project/<project>/issues`. The page sometimes
  answers with a bot challenge; when it does, rely on the web search.
- **GitLab work items:**
  `https://git.drupalcode.org/api/v4/projects/project%2F<project>/issues?search=<terms>`,
  which searches titles and descriptions, and a web search such as
  `"<message>" site:git.drupalcode.org/project/<project>`.

The `drupalorg issue:search` command reads only the most recently changed issues on
drupal.org and matches titles, so an empty result from it proves nothing. Use it as
a quick extra check, never as the only search.

### Read candidates and releases

Check once whether the [`drupalorg` CLI](https://github.com/mglaman/drupalorg-cli) is
available: `command -v drupalorg`, or its MCP tools (`issue_show`, `mr_list` and the
rest) loaded in the session. When it is, load its own skill
(`drupalorg skill:get drupalorg-cli`) and pass `--format=llm` to every read command
that accepts it (`project:release-notes` prints text only). When it is not, use the
right column. In the CLI, a work item takes `<project>#<IID>` instead of a node ID.

| Lookup                        | With the CLI                                                          | Without the CLI                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| drupal.org issue and comments | `drupalorg issue:show <nid> --with-comments`                          | `https://www.drupal.org/api-d7/node.json?nid=<nid>` and `https://www.drupal.org/api-d7/comment.json?node=<nid>` |
| GitLab work item              | `drupalorg issue:show <project>#<IID> --with-comments`                | `https://git.drupalcode.org/api/v4/projects/project%2F<project>/issues/<IID>`; its comments need a GitLab token |
| MRs for a drupal.org issue    | `drupalorg mr:list <nid> --state=all`, then `mr:diff` and `mr:status` | `https://git.drupalcode.org/api/v4/projects/project%2F<project>/merge_requests?state=all&search=<nid>`          |
| MRs for a work item           | `drupalorg mr:list <project>#<IID> --state=all`                       | `https://git.drupalcode.org/api/v4/projects/project%2F<project>/issues/<IID>/related_merge_requests`            |
| Releases                      | `drupalorg project:releases <project>` (latest per branch only)       | `https://updates.drupal.org/release-history/<project>/current` (every release)                                  |
| Release notes                 | `drupalorg project:release-notes <project> <version>`                 | `https://www.drupal.org/project/<project>/releases/<version>`                                                   |

To find every release between the installed version and the latest, use the release
history feed: the CLI lists only the latest release of each branch. Release notes
list the issue numbers they fix, so search them for the issue's number.

Done when you have searched the full queue by title and by the error message, read
every candidate issue with its MRs, and checked the release notes of every release
newer than the installed one. Report the verdict first (the path below and the
issue, release or patch it rests on), then the evidence.

### Paths

Take the first path that applies:

1. **Fixed in a newer release.** Propose updating the package, naming the release that
   carries the fix. The update follows the project's dependency update procedure, for
   example a `drupal-composer-update` skill where one is installed.
2. **A patch or MR exists and applies to the installed version.** Check the patch
   against the installed version first; a patch made for another branch can fail or
   apply in the wrong place. Then carry it through `cweagans/composer-patches`, as a
   file saved in the project:
   - **Save the file locally.** Composer never points at a remote URL: drupal.org
     attachments can change, and an MR diff moves with every push. For an MR,
     download `https://git.drupalcode.org/project/<project>/-/merge_requests/<iid>.diff`.
     Check that the file starts with diff headers (`diff --git` or `---`/`+++`), not
     HTML.
   - **Name it after the issue.** Follow the project's patch naming convention. When
     it has none, use `<NID>_CM<n>.patch` for a patch attached to comment `<n>`,
     `<NID>_MR<iid>.patch` for an MR, and `<project>-<IID>_MR<iid>.patch` for an MR
     on a GitLab work item. Store it next to the project's existing patches.
   - **Describe the entry with the issue.** Key the patch entry with the issue
     number and title, such as `#<NID>: <issue title>` or
     `<project>#<IID>: <title>`.
   - **Leave composer to the user.** Applying the patch needs `composer install` or
     `composer update`. Hand that step to the user unless they already approved
     it, then rerun the red check.
3. **A patch exists but no longer applies.** Rebase it onto the installed version
   with the `drupal-rebase-mr` skill, then apply it as in path 2.
4. **Nothing exists.** Write the fix in the module or core itself, to contrib MR
   quality: Drupal coding standards, a test in the module's own test suite, and a
   draft issue summary (problem, steps to reproduce, proposed resolution). Carry it
   in the project as a local patch, as in path 2. Drupal.org's
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
