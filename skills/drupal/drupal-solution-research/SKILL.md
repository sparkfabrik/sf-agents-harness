---
name: drupal-solution-research
description: Research the Drupal ecosystem to find existing solutions before writing custom code — known core/contrib issues, patches, merge requests, alternative modules, and documented approaches. Uses the drupal.org api-d7 JSON API and the git.drupalcode.org GitLab API. Use this skill whenever the user asks "is there a known issue for X", "is there a patch", "has someone already solved this", "find a module that does X", pastes a PHP error or stack trace from a Drupal site, references a drupal.org issue or project URL, or asks to read a project issue and find a solution. Also trigger proactively when a bug is traced to core or a contrib module — an upstream fix probably already exists and must be checked before patching or forking locally.
---

# Drupal Solution Research

Find existing solutions to a Drupal problem before anyone writes custom code. The Drupal ecosystem is old and huge: most bugs already have an issue, many have a patch or merge request, and most feature needs have a contrib module. The job is to find them, judge their state, and recommend the best path.

## Critical constraint: how to access drupal.org

drupal.org HTML pages are behind a JavaScript client challenge — `curl` on any `www.drupal.org/...` HTML page returns a "Client Challenge" stub, not content. Do not scrape HTML. Instead:

- **Structured data** (projects, issues, comments, files): use the **api-d7 JSON API** via `curl`. It is not blocked. Full endpoint reference: `references/drupal-org-api.md` — read it before your first api-d7 call.
- **Keyword/full-text discovery**: api-d7 has no full-text search (`title=` is exact-match only). Use **WebSearch** with `site:drupal.org` queries.
- **Code, MRs, releases**: use the **git.drupalcode.org GitLab API v4** via `curl` — public, no auth needed.
- Static files (`www.drupal.org/files/...`, MR `.diff`/`.patch` URLs) download fine with `curl`.

## Workflow

### 1. Define the problem

Build a precise search profile before searching. Depending on how the problem arrives:

- **Described in the prompt**: extract symptoms, module names, Drupal version hints.
- **Project issue reference** (e.g. "read issue #123 and find a solution"): read it with the `glab` skill (or `gh` for GitHub projects) first.
- **Pasted error / stack trace**: extract the exact error message (minus site-specific paths/values), the throwing class/function, and the module it lives in (`/modules/contrib/<name>/` or `/core/` in the trace tells you the project).

The profile you want: affected project(s) (core or module machine name), 2–4 search phrases (one being the exact error string if there is one), and the symptom in one sentence.

### 2. Gather local context

If working inside a Drupal project, read versions from `composer.lock` — findings are only useful if they apply to the installed versions:

```bash
python3 -c "
import json
lock = json.load(open('src/drupal/composer.lock'))  # adjust path to project layout
for p in lock['packages']:
    if p['name'] in ('drupal/core', 'drupal/MODULE'):
        print(p['name'], p['version'])
"
```

Also note the PHP version if the error suggests a PHP-compat problem.

### 3. Search — run angles in parallel

Fire these concurrently (parallel tool calls / subagents); each finds things the others miss:

1. **Issue queue scan** (api-d7): resolve the project nid, then list its issues sorted by `changed` DESC. Scan titles for matches. For core, nid is `3060`.
2. **Web search, exact error**: WebSearch the quoted error string + "drupal". Catches issues, Stack Exchange answers, blog posts.
3. **Web search, symptom**: WebSearch `site:drupal.org` + symptom keywords. Catches issues whose title words differ from yours, change records, and documentation pages.
4. **Merge requests** (GitLab API): list the project's MRs; open MRs often hold fixes that never became "patches".
5. **Module discovery** (only for "find a module that does X" needs): WebSearch `site:drupal.org/project` + capability keywords, then verify each candidate via api-d7 (maintenance status, D-version support, last release).

### 4. Deep-dive the candidates

For each promising issue, pull the full picture via api-d7:

- **Issue node**: status, version, category, priority, body. Status decides how much to trust it — see the status-code table in `references/drupal-org-api.md`. A "Closed (fixed)" issue means: check which release contains the fix — maybe the answer is just "update the module".
- **Comments** (`comment.json?node=<nid>`): the real gold. Solutions, workarounds, "this patch works on 10.3", "duplicate of #NNN", and re-rolled patches all live in comments, not the issue body. Read them — at minimum the last ~10.
- **Attached patches**: `field_issue_files` → resolve each file entity to its download URL. Comment number for a file = its position in the chronological comment list (needed for the patch naming convention).
- **MR diff**: `https://git.drupalcode.org/project/<name>/-/merge_requests/<iid>.diff` downloads directly.

Judge compatibility explicitly: issue `field_issue_version` and MR target branch vs. the installed version from step 2. A patch for 8.x-1.x rarely applies to a 2.x module.

### 5. Report findings

Lead with the answer. The reader wants the conclusion first and the evidence available if they want to dig — not a build-up that makes them scroll to find out what to do. Put the verdict and the recommended action in the first few lines; everything below is supporting detail they can skip.

ALWAYS use this structure:

```markdown
# <one-line problem statement>

**Bottom line:** <1-2 sentences — is there an existing solution, and what should the user do? e.g. "Known core bug, fixed in 10.5.1 — update core, no patch needed." or "No known issue; this looks project-specific.">

**Do this:** <the single concrete next step: update to X / apply patch #N / install module Y / no upstream fix exists, here's why>

---

## Evidence

### 1. <title> — <kind: known issue + patch | merge request | fixed in release | alternative module | documented approach>
- **Link**: <url>  **Status**: <issue status / MR state>  **Version**: <target version>
- **Compatibility**: <applies cleanly to installed version? yes/no/untested>
- <2-3 sentences: what it is, what the comments say, caveats>

### 2. <runner-up, one entry per real alternative> ...

## Context checked
<installed core/module/PHP versions, or "not in a Drupal project" — one line>
```

Keep the top block tight: a reader who trusts you should be able to act on the first two lines alone. Do not restate the evidence in the bottom line; name the outcome and the action, and let the Evidence section carry the proof.

Rank the evidence by trust: fixed-in-release (just update) > RTBC/reviewed patch or MR > active issue with working patch per comments > workaround from comments/StackExchange > alternative module > custom code (last resort — state explicitly that nothing upstream exists). The winner is what the bottom line recommends.

Report honestly when nothing is found: an empty result ("no known issue — this looks project-specific") is a valid, useful outcome and belongs right in the bottom line. Do not pad the Evidence section with tangential links to look thorough — a reader reads padding as noise and trusts the report less.

Length discipline: the reader wants the answer at the top and as little below it as the decision needs. Default to a **short** Evidence section — the recommended solution plus at most 1-2 real alternatives, one tight paragraph each. Deeper material (contrib-culprit lists, mechanism walkthroughs, code-line citations) is opt-in: include it only when the problem genuinely requires it to act — a subtle root cause, a "which of these is it" fork, a compatibility trap — and keep it below the acting-level evidence. A finding that doesn't change the recommendation gets one line or gets cut. Two verified candidates beat six half-checked ones; a report the reader trusts and finishes beats an exhaustive one they abandon.

### 6. Apply a patch (only when the user wants to proceed)

When the recommendation is a patch/MR and the user asks to apply it, follow the SparkFabrik convention in `references/patch-workflow.md`: download the patch into `src/drupal/addons/patches/` with the `#<NID>_<CM|MR><id>.patch` naming, and add the `composer.patches.json` entry. Include the ready-to-paste snippet in the report's Recommendation section even before applying, so the user sees exactly what would change.

## Judgment notes

- An issue marked "Closed (works as designed)" still often contains the answer — the explanation of *why* it works that way, plus the supported alternative.
- Check issue `changed` dates: a 2019 patch on a module now at 3.x is archaeology, not a solution.
- Duplicates chain: comments saying "duplicate of #NNN" — follow the chain to the canonical issue before reporting.
- For core issues, also search for a **change record** (WebSearch `site:drupal.org/node` or "change record" + topic) — API changes are documented there, and the "fix" may be adapting to a deliberate change.
- Be polite to the APIs: no pagination sweeps beyond what the question needs.
