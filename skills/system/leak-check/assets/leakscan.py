#!/usr/bin/env python3
"""Scan a git change for internal information that should not leave the company.

Reads added lines only (a diff's `+` side), because the question is what this change
*introduces*, not what a repository already contains.

Exit codes:
  0  nothing found
  1  findings at or above the failure threshold
  2  usage or environment error

Severity depends on where the code is going. A container registry path is routine in
a private repository and a disclosure in a public one, so visibility is resolved
first and drives the threshold rather than the patterns.
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Patterns are grouped by what a reader outside the company would learn. Each entry:
#   (id, regex, what it discloses, whether it is sensitive even in a private repo)
#
# The list deliberately covers vendor and SaaS platforms, not only infrastructure.
# The failure that motivated it: a link to an internal knowledge-base page reached a
# public repository, because the check in use at the time looked only for hostnames,
# registry paths and service accounts, so a SaaS URL matched nothing.
PATTERNS = [
    # --- credentials: sensitive everywhere, public or not ---
    ("private-key", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY", "a private key", True),
    ("aws-key", r"\bAKIA[0-9A-Z]{16}\b", "an AWS access key id", True),
    ("github-token", r"\bgh[pousr]_[A-Za-z0-9]{16,}", "a GitHub token", True),
    ("gitlab-token", r"\bglpat-[A-Za-z0-9_\-]{16,}", "a GitLab personal access token", True),
    ("slack-token", r"\bxox[baprs]-[A-Za-z0-9\-]{10,}", "a Slack token", True),
    ("google-api-key", r"\bAIza[0-9A-Za-z_\-]{35}\b", "a Google API key", True),
    ("bearer", r"(?i)\b(?:authorization|bearer)\s*[:=]\s*['\"]?[A-Za-z0-9\-._~+/]{20,}", "a bearer token", True),
    ("generic-secret", r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "a hard-coded credential", True),

    # --- cloud resources: routine internally, disclosure publicly ---
    ("gcp-service-account", r"[a-z0-9\-]+@[a-z0-9\-]+\.iam\.gserviceaccount\.com", "a service account identity", False),
    ("artifact-registry", r"[a-z0-9\-]+-docker\.pkg\.dev/[a-z0-9\-]+/[a-z0-9\-/]+", "a container registry path", False),
    ("gcr", r"\b(?:gcr|us\.gcr|eu\.gcr|asia\.gcr)\.io/[a-z0-9\-]+", "a container registry path", False),
    ("ecr", r"\b\d{12}\.dkr\.ecr\.[a-z0-9\-]+\.amazonaws\.com", "an AWS account id and registry", False),
    ("k8s-internal-dns", r"[a-z0-9\-]+\.[a-z0-9\-]+\.svc\.cluster\.local", "an in-cluster service address", False),
    ("gcp-wif", r"projects/\d{6,}/locations/[a-z0-9\-]+/workloadIdentityPools/", "a workload identity pool", False),

    # --- SaaS and vendor platforms: the category that was missed ---
    ("saas-platform", r"https?://[a-z0-9\-.]*\.(?:peopleforce\.io|atlassian\.net|slack\.com|notion\.so|notion\.site|monday\.com|hubspot\.com|float\.com|personio\.de|bamboohr\.com|workday\.com|greenhouse\.io|lever\.co|zendesk\.com|freshdesk\.com|pipedrive\.com|okta\.com|onelogin\.com|1password\.com|lastpass\.com)\S*", "which SaaS platform the company uses, and an internal resource within it", False),
    ("self-hosted-forge", r"https?://(?:gitlab|git|jenkins|nexus|artifactory|sonarqube|grafana|kibana|prometheus|vault|argocd|harbor)\.[a-z0-9\-]+\.[a-z]{2,}\S*", "a self-hosted internal tool and its address", False),

    # --- internal network names ---
    ("internal-tld", r"\b[a-z0-9\-]+\.(?:internal|intranet|corp|lan|local|loc|test)\b(?!\.)", "an internal hostname", False),
    ("private-ip", r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b", "a private network address", False),
]

# Lines that are obviously about the pattern rather than an instance of it: a regex
# describing tokens, a comment naming a vendor, documentation of the check itself.
NOISE = re.compile(
    r"(?i)(?:^\s*[#/*]+\s*(?:e\.?g\.?|example|for instance)\b"
    r"|\bexample\.(?:com|org|net)\b"
    r"|\bYOUR[_-]?(?:TOKEN|KEY|SECRET)\b"
    r"|\bxxx+\b|<[a-z-]+>|\$\{[A-Z_]+\}|\bREDACTED\b|\bplaceholder\b)"
)


# An explicit, line-level opt-out for a line that must contain the shape: a test
# fixture, or documentation of the pattern itself. Deliberately requires writing the
# marker on the line, and every use is counted and reported — a suppression nobody
# can see is the failure this whole check exists to prevent.
IGNORE_MARK = re.compile(r"leakcheck:\s*ignore")


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def repo_visibility(cwd):
    """Return "public", "private", or "unknown".

    Resolved from the forge rather than guessed, because the whole severity model
    depends on it. A self-hosted GitLab instance is treated as private only when it
    says so; an unknown answer is reported as unknown rather than assumed safe.
    """
    remote = run(["git", "remote", "get-url", "origin"], cwd).stdout.strip()
    if not remote:
        return "unknown", ""

    if "github.com" in remote:
        slug = re.sub(r"^.*github\.com[:/]", "", remote).removesuffix(".git")
        out = run(["gh", "repo", "view", slug, "--json", "visibility"], cwd)
        if out.returncode == 0:
            try:
                v = json.loads(out.stdout)["visibility"].lower()
                return ("public" if v == "public" else "private"), remote
            except Exception:
                pass
        return "unknown", remote

    if "gitlab" in remote:
        out = run(["glab", "api", "projects/:id"], cwd)
        if out.returncode == 0:
            try:
                v = json.loads(out.stdout).get("visibility", "").lower()
                if v:
                    return ("public" if v == "public" else "private"), remote
            except Exception:
                pass
        return "unknown", remote

    return "unknown", remote


def load_allowlist(cwd):
    """Per-repository allowlist of literal strings that are legitimately present.

    A private repository documenting its own registry path needs to say it. The file
    is plain text, one string per line, `#` for comments.
    """
    path = os.path.join(cwd or ".", ".leakcheck-allow")
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def added_lines(diff_text):
    """Yield (path, lineno_in_new_file, text) for added lines of a unified diff."""
    path = None
    new_line = 0
    for raw in diff_text.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            yield path, new_line, raw[1:]
            new_line += 1
        elif not raw.startswith("-"):
            new_line += 1


def scan(diff_text, allowlist):
    findings = []
    ignored = 0
    for path, lineno, text in added_lines(diff_text):
        if IGNORE_MARK.search(text):
            ignored += 1
            continue
        if NOISE.search(text):
            continue
        if any(a in text for a in allowlist):
            continue
        for pid, pattern, discloses, always in PATTERNS:
            m = re.search(pattern, text)
            if m:
                findings.append({
                    "id": pid,
                    "path": path or "?",
                    "line": lineno,
                    "match": m.group(0)[:120],
                    "discloses": discloses,
                    "always_sensitive": always,
                })
    return findings, ignored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true", help="scan the staged change (default)")
    ap.add_argument("--range", help="scan a commit range, e.g. origin/main..HEAD")
    ap.add_argument("--repo", default=".", help="repository directory")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    cwd = args.repo
    if args.range:
        diff = run(["git", "diff", args.range], cwd)
    else:
        diff = run(["git", "diff", "--cached"], cwd)
    if diff.returncode != 0:
        print(diff.stderr.strip() or "git diff failed", file=sys.stderr)
        return 2
    if not diff.stdout.strip():
        print("leak-check: nothing to scan (no staged changes?)")
        return 0

    visibility, remote = repo_visibility(cwd)
    findings, ignored = scan(diff.stdout, load_allowlist(cwd))

    # A credential is a finding wherever it is going. Everything else is judged by
    # audience: disclosure in a public repository, a note in a private one. An
    # unresolved visibility blocks, because "we could not tell" must not read as
    # "it is fine" — the failure this skill exists for was exactly a check whose
    # message and behaviour disagreed.
    blocking = [f for f in findings if f["always_sensitive"] or visibility != "private"]
    advisory = [f for f in findings if f not in blocking]

    if args.json:
        print(json.dumps({"visibility": visibility, "remote": remote,
                          "blocking": blocking, "advisory": advisory,
                          "ignored_lines": ignored}, indent=2))
        return 1 if blocking else 0

    print(f"leak-check: repository is {visibility} ({remote or 'no origin'})")
    if ignored:
        print(f"  {ignored} line(s) carried a leakcheck:ignore marker and were skipped")
    if visibility == "unknown":
        print("  visibility could not be resolved, so anything found is reported as blocking")

    if not findings:
        print("  no internal information found in the added lines")
        return 0

    for group, label in ((blocking, "BLOCKING"), (advisory, "advisory")):
        for f in group:
            print(f"  [{label}] {f['path']}:{f['line']}  {f['id']}")
            print(f"      {f['match']}")
            print(f"      discloses {f['discloses']}")

    if blocking:
        print("\n  Do not commit these. Either remove them, or describe the resource")
        print("  without naming it. If a match is legitimate for this repository, add")
        print("  the exact string to .leakcheck-allow with a reason.")
        return 1

    print("\n  Private repository, so these are recorded rather than blocked. Check they")
    print("  belong here, and that nothing derived from this file is published, such as")
    print("  documentation copied into a public repository or a support ticket.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
