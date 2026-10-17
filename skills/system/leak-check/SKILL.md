---
name: leak-check
description: 'Invoke before committing or pushing, and always before a first push to a public repository. Scans the staged change for internal information that should not leave the organisation: credentials and tokens, container registry paths, cloud service account identities, internal hostnames and private network addresses, and URLs that disclose which SaaS platforms an organisation uses or expose a self-hosted internal tool. Severity depends on repository visibility, which is resolved from the forge rather than assumed. Trigger on: "commit", "push", "open a PR/MR", "is this safe to publish", "check for leaks", or any work touching a public repository.'
---

# Leak check before committing

## Why this exists

A link to an internal knowledge-base page reached a public repository. A check *was*
in place: a grep for infrastructure strings — hostnames, the container registry path,
the service account identity. The URL matched none of them, so it went through.

The lesson is not "grep harder". It is:

1. **Internal information is wider than infrastructure.** A SaaS URL discloses which
   vendor an organisation uses and often an internal resource id inside it. So do
   ticket links, wiki pages, and self-hosted tool addresses.
2. **Severity depends on the audience.** A container registry path is unremarkable in
   a private repository and a disclosure in a public one. A check that cannot tell the
   difference either blocks routine work or waves leaks through.

Both are built into this check.

## Run it

```bash
python3 skills/system/leak-check/assets/leakscan.py                        # staged change
python3 skills/system/leak-check/assets/leakscan.py --range origin/main..HEAD
python3 skills/system/leak-check/assets/leakscan.py --json                 # for tooling
```

Exit codes: `0` clean, `1` blocking findings, `2` usage or environment error.

Run it **before** `git commit`. Once a leak is committed and pushed the options are
history rewriting or acceptance that it is published; the commit boundary is the only
cheap moment.

## What it reports

Only **added** lines are scanned. The question is what this change introduces, not
what the repository already contains.

| category | examples | blocks in |
|---|---|---|
| credentials | private keys, AWS access keys, `glpat-` / `ghp_` tokens, bearer tokens, hard-coded passwords | every repository |
| cloud resources | Artifact Registry / GCR / ECR paths, service account identities, workload identity pools, in-cluster service addresses | public, and unknown |
| SaaS platforms | wiki, HR, CRM, helpdesk and identity-provider URLs | public, and unknown |
| self-hosted tools | GitLab, Jenkins, Vault, Grafana, Artifactory, ArgoCD, Harbor addresses | public, and unknown |
| internal network | `*.corp`, `*.internal`, `*.local`, RFC1918 addresses | public, and unknown |

**Unknown visibility blocks.** When the forge cannot be asked, the check refuses
rather than assuming safety. This is not caution for its own sake: the first version
of this script printed "reported as blocking" for unknown visibility and then exited
zero, and its own self-test caught the contradiction. A check whose message and
behaviour disagree is worse than no check, because it is trusted.

## Acting on findings

**A credential**: rotate it first. It has existed in a working tree and may already
be in a shell history, an editor backup, or a CI log. Deleting the line does not
undo that.

**An internal resource in a public repository**: remove it, or describe it without
naming it. "The setup instructions are in the internal knowledge base" carries the
same meaning to a colleague and nothing to anyone else. Resist keeping a URL because
the page itself requires a login — the hostname discloses the vendor, and a page or
category id discloses structure.

**A legitimate reference**: two ways, both explicit.

For a whole repository, add the exact string to `.leakcheck-allow` in the root, one
per line, `#` for comments. A private repository documenting its own registry path
needs to state it, and the allowlist records that decision where the next reader will
find it.

For a single line that must contain the shape — a test fixture, or documentation of
the pattern itself — write `leakcheck: ignore` on that line with a reason after it.
Every use is counted and reported in the output, because a suppression nobody can see
is the failure this check exists to prevent. This skill's own fixtures use it, which
is why it can be committed to a public repository at all.

## What it does not do

It reads a diff, so it cannot judge intent, and it knows nothing about internal
systems whose names match no known shape. A bespoke service called `atlas` will not
be caught. Treat a clean result as "no known pattern matched", not as clearance, and
when a change is about to make a repository public for the first time, read the whole
diff yourself.

False positives are preferred to silence, with one deliberate exception: the noise
filter drops `example.com`, `${VAR}` references, `YOUR_TOKEN` placeholders,
`REDACTED`, and lines a comment marks as examples. A check that cries wolf gets
ignored, which is the same as not having one.

## Maintaining it

```bash
bash skills/system/leak-check/assets/selftest.sh
```

It builds throwaway repositories and asserts each case, including the ones that must
**not** fire. Add a case when adding a pattern, and add one whenever a real leak gets
through — that is the point of keeping the tests next to the check.
