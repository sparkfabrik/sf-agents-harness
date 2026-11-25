#!/usr/bin/env python3
"""Print recent Drupal core release tags, security advisories and PSAs.

Usage: check_sources.py [--since-hours N] [--psa-days N]

Reads public, unauthenticated sources:
- git.drupalcode.org GitLab API: tags of project/drupal (core releases).
- drupal.org api-d7: nodes of type "sa" (core and contrib advisories), with
  the affected version range and the risk vector.
- drupal.org PSA RSS feed: announcements of upcoming releases.

Output is plain text, newest first. Exit code is 0 when a tag or an
advisory was published inside --since-hours, 1 when nothing was, 2 on error.
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

    try:
        tags = json.loads(get(TAGS_URL))
        sas = json.loads(get(SA_URL))["list"]
        psa_xml = get(PSA_RSS)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR fetching sources: {exc}", file=sys.stderr)
        return 2

    print(f"Checked at {fmt(now)}")

    print(f"\n== Core tags since {fmt(since)} ==")
    for tag in tags:
        created = datetime.fromisoformat(tag["commit"]["created_at"])
        if created >= since:
            found = True
            print(f"{tag['name']}\t{fmt(created)}")
    if tags:
        print(f"latest tag: {tags[0]['name']}")

    print(f"\n== Security advisories since {fmt(since)} ==")
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
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
