#!/usr/bin/env python3
"""Pull all Morning Briefing feeds and print a raw headline digest (markdown).

Usage: python3 fetch_headlines.py [--hours N]
Default lookback: 48h; Mondays automatically stretch to Friday noon.
"""
import argparse
import concurrent.futures
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

FEEDS_FILE = Path(__file__).parent / "feeds.tsv"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def lookback_hours(now):
    # Runs each morning at 8:30: cover everything since the previous run.
    return 72 if now.weekday() == 0 else 24  # Monday reaches back to Friday 8:30


def load_feeds():
    feeds = []
    for path in (FEEDS_FILE, FEEDS_FILE.parent / "threads.tsv"):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            section, outlet, url = line.split("\t")[:3]  # 4th col = thread metadata
            feeds.append((section, outlet, url))
    return feeds


def fetch(feed):
    section, outlet, url, hours = feed
    # widen the Google News source window to cover the lookback (weekend on Mondays)
    url = url.replace("when:2d", f"when:{max(2, -(-int(hours) // 24))}d")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        return section, outlet, None, str(e)
    items = []
    for item in root.iter("item"):
        get = lambda tag: (item.findtext(tag) or "").strip()
        pub = get("pubDate")
        try:
            when = parsedate_to_datetime(pub)
        except Exception:
            when = None
        desc = unescape(re.sub(r"<[^>]+>", "", get("description")))
        # Google News suffixes " - Outlet" onto titles and repeats title in desc
        title = unescape(get("title"))
        src = (item.findtext("source") or "").strip()
        if src and title.endswith(f"- {src}"):
            title = title[: -len(f"- {src}")].strip(" -")
        if title == src or len(title) < 15 or title.lower().startswith(("log in", "subscribe", "subscription")):
            continue  # paywall/login pages indexed with junk titles
        if desc.startswith(title[:40]):
            desc = ""
        items.append({"title": title, "link": get("link"), "when": when,
                      "desc": desc[:300], "source": (src or "").strip()})
    return section, outlet, items, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    hours = args.hours or lookback_hours(now)
    cutoff = now - timedelta(hours=hours)

    feeds = [(s, o, u, hours) for s, o, u in load_feeds()]
    print(f"# Raw headline digest — {now.strftime('%A, %B %d, %Y %H:%M UTC')} (lookback {hours:.0f}h)\n")
    seen = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for section, outlet, items, err in ex.map(fetch, feeds):
            if err:
                print(f"## [{section}] {outlet}\nFEED ERROR: {err}\n", file=sys.stderr)
                continue
            # keep feed order: Google News is relevance-ranked, direct feeds chronological.
            # Date-sorting here buries relevant stories under fresh off-topic matches.
            fresh = [i for i in items if i["when"] is None or i["when"] >= cutoff][:20]
            if not fresh:
                continue
            print(f"## [{section}] {outlet}")
            for i in fresh:
                key = i["title"].lower()[:80]
                dupe = " (DUPLICATE — appeared above)" if key in seen else ""
                seen.add(key)
                when = i["when"].strftime("%a %b %d %H:%M") if i["when"] else "undated"
                src = f" | source: {i['source']}" if i["source"] else ""
                print(f"- {i['title']} ({when}{src}){dupe}\n  {i['link']}")
                if i["desc"]:
                    print(f"  > {i['desc']}")
            print()


if __name__ == "__main__":
    main()
