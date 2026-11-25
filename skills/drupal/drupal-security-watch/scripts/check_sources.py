#!/usr/bin/env python3
"""Print recent Drupal core release tags, security advisories and PSAs.

Usage: check_sources.py [--since-hours N] [--psa-days N]

Reads public, unauthenticated sources:
- git.drupalcode.org GitLab API: tags of project/drupal (core releases).
- drupal.org api-d7: nodes of type "sa" (core and contrib advisories), with
  the affected version range and the risk vector.
- drupal.org PSA RSS feed: announcements of upcoming releases.

Output is plain text, newest first. Each source is fetched on its own: a
source that fails prints an "UNAVAILABLE" line and the others still report.

Exit codes:
- 0: a tag or an advisory was published inside --since-hours, even when
  another source failed.
- 1: nothing was published and every source answered.
- 2: nothing was found but at least one source failed, so the check is
  incomplete.

A recent PSA alone does not change the exit code; it is printed so the
caller can report "announced, not released".
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = {"User-Agent": "Mozilla/5.0 (drupal-security-watch)"}
TAGS_URL = (
    "https://git.drupalcode.org/api/v4/projects/project%2Fdrupal/"
    "repository/tags?order_by=updated&per_page=20"
)
SA_URL = (
    "https://www.drupal.org/api-d7/node.json"
    "?type=sa&sort=created&direction=DESC&limit=20"
)
PSA_RSS = "https://www.drupal.org/security/psa/rss.xml"

# Risk vector keys of the drupal.org security risk calculator.
VECTOR_HELP = {
    "AC": "access complexity",
    "A": "authentication (None = anonymous can exploit)",
    "CI": "confidentiality impact",
    "II": "integrity impact",
    "E": "exploit (Exploit = public exploit exists)",
    "TD": "target distribution",
}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fmt(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="minutes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since-hours", type=float, default=24)
    parser.add_argument("--psa-days", type=float, default=7)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=args.since_hours)
    psa_since = now - timedelta(days=args.psa_days)
    found = False
    failed = []

    def fetch(name, url, parse):
        try:
            return parse(get(url))
        except Exception as exc:  # noqa: BLE001
            failed.append(name)
            print(f"UNAVAILABLE: {name} ({url}): {exc}")
            return None

    print(f"Checked at {fmt(now)}")

    print(f"\n== Core tags since {fmt(since)} ==")
    tags = fetch("core tags", TAGS_URL, json.loads) or []
    for tag in tags:
        # Annotated tags carry their own creation time, which is when the
        # release was tagged; the commit can be older than the release.
        stamp = tag.get("created_at")
        note = ""
        if not stamp:
            stamp = tag["commit"]["created_at"]
            note = "\t(commit date: the tag has no timestamp)"
        created = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if created >= since:
            found = True
            print(f"{tag['name']}\t{fmt(created)}{note}")
    if tags:
        print(f"latest tag: {tags[0]['name']}")

    print(f"\n== Security advisories since {fmt(since)} ==")
    sas = fetch("security advisories", SA_URL, lambda body: json.loads(body)["list"]) or []
    for node in sas:
        created = datetime.fromtimestamp(int(node["created"]), timezone.utc)
        if created < since:
            continue
        found = True
        print(f"{node['title']}\t{fmt(created)}\t{node['url']}")
        affected = node.get("field_affected_versions")
        if affected:
            print(f"  affected: {affected}")
        vector = node.get("field_sa_criticality")
        if vector:
            print(f"  risk vector: {vector}")
    if sas:
        print(f"latest SA: {sas[0]['title']}")

    print(f"\n== PSAs since {fmt(psa_since)} ==")
    psa_xml = fetch("PSA feed", PSA_RSS, lambda body: body) or ""
    items = re.findall(
        r"<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>",
        psa_xml,
        re.S,
    )
    for title, link, pub in items:
        published = parsedate_to_datetime(pub)
        if published >= psa_since:
            print(f"{title}\t{fmt(published)}\t{link}")

    print("\nRisk vector keys: " + "; ".join(f"{k}={v}" for k, v in VECTOR_HELP.items()))
    if failed:
        print(f"\nIncomplete check, unavailable: {', '.join(failed)}")
    if found:
        return 0
    return 2 if failed else 1


if __name__ == "__main__":
    sys.exit(main())
