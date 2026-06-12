#!/usr/bin/env python3
"""Build a combined VA + PT security assessment HTML report.

Reads engagement metadata and one or both track findings files (VA, PT),
validates them against the schema in references/findings-schema.md, and renders
a single standalone HTML file from report-template.html.

Standard library only. No third-party dependencies.

Usage:
  build-report.py --engagement engagement.json \
                  [--va va-findings.json] [--pt pt-findings.json] \
                  --out report.html [--template report-template.html]
"""

import argparse
import html
import json
import os
import re
import sys
from typing import NoReturn

SEVERITIES = ["critical", "high", "medium", "low", "info"]
SEV_RANK = {s: i for i, s in enumerate(SEVERITIES)}
REQUIRED_FINDING_FIELDS = [
    "id", "title", "severity", "track", "category",
    "tool", "location", "description", "impact", "evidence", "recommendation",
]


def die(msg) -> NoReturn:
    sys.stderr.write("build-report: error: %s\n" % msg)
    sys.exit(1)


def load_json(path, what):
    if not os.path.isfile(path):
        die("%s file not found: %s" % (what, path))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        die("%s is not valid JSON (%s): %s" % (what, path, exc))


def validate_findings(data, expected_track, path):
    if not isinstance(data, list):
        die("%s must be a JSON array, got %s" % (path, type(data).__name__))
    seen = set()
    for i, f in enumerate(data):
        if not isinstance(f, dict):
            die("%s[%d] is not an object" % (path, i))
        fid = f.get("id", "<index %d>" % i)
        for field in REQUIRED_FINDING_FIELDS:
            if not f.get(field):
                die("finding %s in %s is missing required field '%s'" % (fid, path, field))
        if f["severity"] not in SEVERITIES:
            die("finding %s has invalid severity '%s' (expected one of %s)"
                % (fid, f["severity"], ", ".join(SEVERITIES)))
        if f["track"] != expected_track:
            die("finding %s has track '%s' but is in the %s file"
                % (fid, f["track"], expected_track))
        if fid in seen:
            die("duplicate finding id '%s' in %s" % (fid, path))
        seen.add(fid)
    return data


def esc(value):
    return html.escape(str(value if value is not None else ""))


def counts_by_severity(findings):
    c = {s: 0 for s in SEVERITIES}
    for f in findings:
        c[f["severity"]] += 1
    return c


def render_meta(eng):
    rows = []

    def row(label, key):
        val = eng.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            rows.append("<tr><th>%s</th><td>%s</td></tr>" % (esc(label), esc(val)))

    row("Project", "project")
    row("Date", "date")
    row("Target", "target")
    row("Scope", "scope")
    row("Out of scope", "out_of_scope")
    row("Stacks", "stacks")
    row("Tracks run", "tracks")
    row("Authorization", "authorization")
    return "\n".join(rows)


def render_summary_cards(eng, va, pt, tracks):
    cards = []
    if "VA" in tracks:
        text = eng.get("va_summary") or "Vulnerability assessment of the codebase: static scanning, dependency CVEs, and manual code review."
        cards.append(
            '<div class="panel summary"><h3>Vulnerability Assessment (VA)</h3>'
            '<p>%s</p><p class="count">%d findings.</p></div>'
            % (esc(text), len(va))
        )
    if "PT" in tracks:
        text = eng.get("pt_summary") or "Penetration test against the running target: recon, template/CVE scanning, authenticated DAST, and targeted exploitation."
        cards.append(
            '<div class="panel summary"><h3>Penetration Testing (PT)</h3>'
            '<p>%s</p><p class="count">%d confirmed findings.</p></div>'
            % (esc(text), len(pt))
        )
    return "\n".join(cards)


def render_matrix(va, pt, tracks):
    va_c = counts_by_severity(va)
    pt_c = counts_by_severity(pt)
    show_va = "VA" in tracks
    show_pt = "PT" in tracks
    head = "<tr><th>Severity</th>"
    if show_va:
        head += '<th class="n">VA</th>'
    if show_pt:
        head += '<th class="n">PT</th>'
    head += '<th class="n">Combined</th></tr>'

    body = []
    for s in SEVERITIES:
        combined = va_c[s] + pt_c[s]
        cells = '<td><span class="pill %s">%s</span></td>' % (s, s)
        if show_va:
            cells += '<td class="n">%d</td>' % va_c[s]
        if show_pt:
            cells += '<td class="n">%d</td>' % pt_c[s]
        cells += '<td class="n">%d</td>' % combined
        body.append("<tr>%s</tr>" % cells)

    total_cells = "<td>Total</td>"
    if show_va:
        total_cells += '<td class="n">%d</td>' % len(va)
    if show_pt:
        total_cells += '<td class="n">%d</td>' % len(pt)
    total_cells += '<td class="n">%d</td>' % (len(va) + len(pt))
    body.append('<tr class="total">%s</tr>' % total_cells)
    return head + "\n" + "\n".join(body)


def render_finding(f):
    parts = []
    parts.append('<div class="panel finding %s" data-severity="%s" data-track="%s">'
                 % (f["severity"], f["severity"], esc(f["track"])))
    parts.append('<div class="row-head">')
    parts.append('<span class="pill %s">%s</span>' % (f["severity"], f["severity"]))
    parts.append('<span class="fid">%s</span>' % esc(f["id"]))
    parts.append('<h4>%s</h4>' % esc(f["title"]))
    parts.append('<span class="badge">%s</span>' % esc(f["track"]))
    if f.get("status") == "fixed":
        parts.append('<span class="fixed-tag">&#10003; Fixed</span>')
    parts.append("</div>")

    parts.append("<dl>")

    def field(label, value, mono=False):
        if value:
            v = '<code class="inline">%s</code>' % esc(value) if mono else esc(value)
            parts.append("<dt>%s</dt><dd>%s</dd>" % (esc(label), v))

    field("Category", f.get("category"))
    field("Tool", f.get("tool"))
    field("Location", f.get("location"), mono=True)
    refs = " ".join(x for x in [f.get("cwe"), f.get("cve")] if x)
    field("Reference", refs)
    parts.append("</dl>")

    def block(label, value, pre=False):
        if value:
            inner = "<pre>%s</pre>" % esc(value) if pre else "<p>%s</p>" % esc(value)
            parts.append('<p class="field-h">%s</p>%s' % (esc(label), inner))

    block("Description", f.get("description"))
    block("Impact", f.get("impact"))
    block("Evidence", f.get("evidence"), pre=True)
    block("Recommendation", f.get("recommendation"))

    arts = f.get("artifacts") or []
    if arts:
        links = " ".join('<code class="inline">%s</code>' % esc(a) for a in arts)
        parts.append('<p class="field-h">Artifacts</p><p>%s</p>' % links)

    parts.append("</div>")
    return "\n".join(parts)


def render_findings(va, pt):
    allf = sorted(va + pt, key=lambda f: (SEV_RANK[f["severity"]], f["track"], f["id"]))
    if not allf:
        return '<p class="empty">No findings recorded.</p>'
    return "\n".join(render_finding(f) for f in allf)


def render_coverage(coverage):
    """Render the 'Tests performed' section: client-facing proof of what ran.

    Each entry: {track, tool, category, executed, findings, errored, status, note}.
    status auto-derives if absent: findings>0 -> findings; errored>0 -> partial;
    else pass (green).
    """
    if not coverage:
        return ('<div class="panel"><p class="note">No coverage data recorded. '
                'Provide a coverage file (see findings-schema.md) to show which '
                'checks were executed.</p></div>')

    total_exec = total_pass = total_find = total_err = 0
    rows = []
    for c in coverage:
        executed = int(c.get("executed") or 0)
        findings = int(c.get("findings") or 0)
        errored = int(c.get("errored") or 0)
        passed = c.get("passed")
        passed = int(passed) if passed is not None else max(executed - findings - errored, 0)
        status = c.get("status") or ("findings" if findings else ("partial" if errored else "pass"))
        total_exec += executed
        total_pass += passed
        total_find += findings
        total_err += errored
        label = {"pass": "PASS", "partial": "PARTIAL", "findings": "FINDINGS"}.get(status, status.upper())
        rows.append(
            "<tr>"
            "<td>%s</td><td>%s</td><td>%s</td>"
            '<td class="n">%d</td>'
            '<td class="n%s">%d</td>'
            '<td class="n">%d</td>'
            '<td class="n">%d</td>'
            '<td><span class="pill %s">%s</span></td>'
            "</tr>"
            % (esc(c.get("track", "")), esc(c.get("tool", "")), esc(c.get("category", "")),
               executed,
               " ok" if findings == 0 else "", passed,
               findings, errored,
               esc(status), esc(label))
        )

    summary = (
        '<div class="cov-summary">'
        '<div><div class="num">%d</div><div class="lbl">checks executed</div></div>'
        '<div><div class="num green">%d</div><div class="lbl">passed (no issue)</div></div>'
        '<div><div class="num">%d</div><div class="lbl">findings</div></div>'
        '<div><div class="num">%d</div><div class="lbl">incomplete / errored</div></div>'
        "</div>"
        % (total_exec, total_pass, total_find, total_err)
    )
    head = ("<tr><th>Track</th><th>Tool</th><th>Check set</th>"
            '<th class="n">Executed</th><th class="n">Passed</th>'
            '<th class="n">Findings</th><th class="n">Errored</th><th>Status</th></tr>')
    note = ""
    if total_err:
        note = ('<p class="note">%d checks could not complete (timeouts/connection errors -- '
                'e.g. a WAF stalling attack-shaped requests). These were attempted but are '
                'not counted as passed. See the run logs in the track artifacts.</p>' % total_err)
    return '<div class="panel">%s<table class="cov">%s\n%s</table>%s</div>' % (
        summary, head, "\n".join(rows), note)


def render_checklist(checklist):
    """Detailed test log: every individual check, green (ok) or red (problem).

    Each entry: {track, tool, name, result: "ok"|"problem", detail?}. Grouped by
    (track, tool) into collapsible panels so a multi-thousand-template log stays
    navigable. Groups with any problem are expanded by default.
    """
    if not checklist:
        return ('<div class="panel"><p class="note">No per-test log provided. '
                'Pass a checklist file (see findings-schema.md) to enumerate every '
                'individual check with a pass/fail flag.</p></div>')

    groups = []
    order = []
    by_key = {}
    for c in checklist:
        key = (c.get("track", ""), c.get("tool", ""))
        if key not in by_key:
            by_key[key] = []
            order.append(key)
        by_key[key].append(c)

    for key in order:
        track, tool = key
        items = by_key[key]
        problems = [c for c in items if c.get("result") == "problem"]
        ok_n = len(items) - len(problems)
        rows = []
        # problems first, then ok
        for c in sorted(items, key=lambda x: 0 if x.get("result") == "problem" else 1):
            bad = c.get("result") == "problem"
            mark = "&#10007;" if bad else "&#10003;"
            detail = c.get("detail")
            det = '<span class="detail">%s</span>' % esc(detail) if detail else ""
            rows.append('<div class="chk %s"><span class="mark">%s</span>'
                        '<span class="id">%s</span>%s</div>'
                        % ("bad" if bad else "ok", mark, esc(c.get("name", "")), det))
        open_attr = " open" if problems else ""
        meta = "%d ok%s" % (ok_n, (" &middot; %d problem" % len(problems)) if problems else "")
        groups.append(
            '<details class="chk-group"%s><summary>%s &mdash; %s'
            '<span class="meta">%s</span></summary>'
            '<div class="chk-list">%s</div></details>'
            % (open_attr, esc(track), esc(tool), meta, "\n".join(rows))
        )
    return "\n".join(groups)


def render_artifacts(va, pt, tracks):
    sections = []

    def collect(findings):
        seen = []
        for f in findings:
            for a in (f.get("artifacts") or []):
                if a not in seen:
                    seen.append(a)
        return seen

    if "VA" in tracks:
        arts = collect(va)
        items = "".join('<li><code class="inline">%s</code></li>' % esc(a) for a in arts) or '<li class="empty">none linked</li>'
        sections.append('<div class="panel"><p class="label">VA artifacts</p><ul class="plain">%s</ul></div>' % items)
    if "PT" in tracks:
        arts = collect(pt)
        items = "".join('<li><code class="inline">%s</code></li>' % esc(a) for a in arts) or '<li class="empty">none linked</li>'
        sections.append('<div class="panel"><p class="label">PT artifacts</p><ul class="plain">%s</ul></div>' % items)
    return "\n".join(sections)


def main():
    ap = argparse.ArgumentParser(description="Build combined VA + PT HTML report.")
    ap.add_argument("--engagement", required=True)
    ap.add_argument("--va")
    ap.add_argument("--pt")
    ap.add_argument("--coverage", help="JSON array of checks performed (Tests performed section)")
    ap.add_argument("--checklist", help="JSON array of individual tests (Detailed test log, pass/fail per item)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "report-template.html"))
    args = ap.parse_args()

    if not args.va and not args.pt:
        die("at least one of --va or --pt is required")

    eng = load_json(args.engagement, "engagement")
    if not isinstance(eng, dict):
        die("engagement file must be a JSON object")

    va = []
    pt = []
    tracks = []
    if args.va:
        va = validate_findings(load_json(args.va, "VA findings"), "VA", args.va)
        tracks.append("VA")
    if args.pt:
        pt = validate_findings(load_json(args.pt, "PT findings"), "PT", args.pt)
        tracks.append("PT")

    coverage = []
    if args.coverage:
        coverage = load_json(args.coverage, "coverage")
        if not isinstance(coverage, list):
            die("coverage file must be a JSON array")

    checklist = []
    if args.checklist:
        checklist = load_json(args.checklist, "checklist")
        if not isinstance(checklist, list):
            die("checklist file must be a JSON array")

    if not os.path.isfile(args.template):
        die("template not found: %s" % args.template)
    with open(args.template, "r", encoding="utf-8") as fh:
        template = fh.read()

    tracks_label = " + ".join(tracks) + (" assessment" if len(tracks) > 1 else " only")
    total = len(va) + len(pt)
    footer = ("Generated from %d finding(s) across %s. Standalone report -- no external assets."
              % (total, " and ".join(tracks)))

    replacements = {
        "{{PROJECT}}": esc(eng.get("project", "Untitled project")),
        "{{DATE}}": esc(eng.get("date", "")),
        "{{TRACKS_RAN}}": esc(tracks_label),
        "{{META_TABLE}}": render_meta(eng),
        "{{SUMMARY_CARDS}}": render_summary_cards(eng, va, pt, tracks),
        "{{MATRIX_TABLE}}": render_matrix(va, pt, tracks),
        "{{COVERAGE}}": render_coverage(coverage),
        "{{CHECKLIST}}": render_checklist(checklist),
        "{{FINDINGS}}": render_findings(va, pt),
        "{{ARTIFACTS}}": render_artifacts(va, pt, tracks),
        "{{FOOTER}}": esc(footer),
    }
    # Single-pass substitution: replacing tokens sequentially would let an
    # earlier value that happens to contain a later token string (e.g. a finding
    # whose text includes the literal "{{FOOTER}}" -- braces survive html.escape)
    # be re-substituted. One regex pass over the original template avoids that.
    pattern = re.compile("|".join(re.escape(token) for token in replacements))
    out = pattern.sub(lambda m: replacements[m.group(0)], template)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out)

    print("Wrote %s (%d findings: %d VA, %d PT)" % (args.out, total, len(va), len(pt)))


if __name__ == "__main__":
    main()
