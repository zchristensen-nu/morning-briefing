#!/usr/bin/env python3
"""Pull all Morning Briefing feeds and print a raw headline digest (markdown).

Usage: python3 fetch_headlines.py [--hours N]
Default lookback: 48h; Mondays automatically stretch to Friday noon.
"""
import argparse
import base64
import concurrent.futures
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

FEEDS_FILE = Path(__file__).parent / "feeds.tsv"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


GNEWS = "https://news.google.com"
RESOLVE_BUDGET = 420  # seconds for the whole digest; whatever is left keeps no link
_blocked = threading.Event()  # Google is refusing us: stop asking


def _http(url, data=None, timeout=12):
    headers = dict(UA)
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _usable(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    return url.startswith("http") and "." in host and not host.endswith(("google.com", "gstatic.com"))


def resolve_google_link(link):
    """Google News redirect link -> the publisher's own article URL, or "" if it can't be had."""
    m = re.search(r"/articles/([^/?#]+)", link)
    if not m:
        return ""
    gid = m.group(1)
    # Older ids carry the URL inside the base64 payload itself.
    try:
        raw = base64.urlsafe_b64decode(gid + "=" * (-len(gid) % 4))
        hit = re.search(rb"https?://[\x21-\x7e]+", raw)
        if hit and _usable(hit.group().decode()):
            return hit.group().decode()
    except Exception:
        pass
    # Newer ids are opaque: the article page carries a signature and timestamp that
    # Google's own front end trades for the real URL.
    for attempt in range(3):
        if _blocked.is_set():
            return ""
        try:
            page = _http(f"{GNEWS}/rss/articles/{gid}")
            sg = re.search(r'data-n-a-sg="([^"]+)"', page)
            ts = re.search(r'data-n-a-ts="([^"]+)"', page)
            if not (sg and ts):
                return ""
            inner = json.dumps([
                "garturlreq",
                [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
                 "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
                gid, int(ts.group(1)), sg.group(1)])
            body = urllib.parse.urlencode(
                {"f.req": json.dumps([[["Fbv4je", inner, None, "generic"]]])}).encode()
            out = _http(f"{GNEWS}/_/DotsSplashUi/data/batchexecute", data=body)
            for row in json.loads(out.split("\n\n", 1)[1]):
                if len(row) > 2 and row[1] == "Fbv4je" and row[2]:
                    url = json.loads(row[2])[1]
                    return url if _usable(url) else ""
            return ""
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                if attempt == 2:
                    _blocked.set()
                time.sleep(5 * (attempt + 1))
                continue
            return ""
        except Exception:
            time.sleep(1)
    return ""


def resolve_links(items):
    """Fill in i["link"] for every search item, in feed order, inside the time budget."""
    todo = {}
    for i in items:
        if "news.google.com" in i["link"]:
            todo.setdefault(i["link"], []).append(i)
    deadline = time.monotonic() + RESOLVE_BUDGET

    def work(link):
        return link, ("" if time.monotonic() > deadline else resolve_google_link(link))

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for link, url in ex.map(work, list(todo)):
            done += bool(url)
            for i in todo[link]:
                i["link"] = url
    return done, len(todo)


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
            parts = line.split("\t")
            section, outlet, url = parts[:3]
            # 4th col is metadata: thread dates, or filter=edu on broad publisher
            # feeds that carry an outlet's whole output rather than its education desk
            meta = parts[3] if len(parts) > 3 else ""
            feeds.append((section, outlet, url, "filter=edu" in meta))
    return feeds


def fetch(feed):
    section, outlet, url, hours, edu_only = feed
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
    if edu_only:
        kw = re.compile(r"\b(universit|college|campus|student|higher ed|tuition|"
                        r"undergrad|faculty|professor|academic|academia|dean|provost|"
                        r"enrol|admission|scholarship|alumni|degree|graduate)", re.I)
        items = [i for i in items if kw.search(i["title"] + " " + i["desc"])]
    return section, outlet, items, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    hours = args.hours or lookback_hours(now)
    cutoff = now - timedelta(hours=hours)

    feeds = [(s, o, u, hours, f) for s, o, u, f in load_feeds()]
    sections = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for section, outlet, items, err in ex.map(fetch, feeds):
            if err:
                print(f"## [{section}] {outlet}\nFEED ERROR: {err}\n", file=sys.stderr)
                continue
            # keep feed order: Google News is relevance-ranked, direct feeds chronological.
            # Date-sorting here buries relevant stories under fresh off-topic matches.
            # national outlets get a deeper cap: their feeds carry more noise, so
            # a genuine education story can sit below 20 on relevance rank.
            cap = 35 if section == "HigherEd" else 20
            fresh = [i for i in items if i["when"] is None or i["when"] >= cutoff][:cap]
            if fresh:
                sections.append((section, outlet, fresh))

    # Search results arrive as Google redirect links, which are dead ends for a reader.
    # Trade each for the publisher's URL here, where the network is open: the curating
    # agent's sandbox cannot reach news sites and its web search rarely finds same-day
    # articles (12 of 16 entries ran without a link on 2026-11-12).
    resolved, wanted = resolve_links([i for _, _, fresh in sections for i in fresh])

    print(f"# Raw headline digest — {now.strftime('%A, %B %d, %Y %H:%M UTC')} (lookback {hours:.0f}h)")
    print("# The line under a headline is the article's own URL: use it as-is.")
    print(f"# Search links resolved to publisher URLs: {resolved} of {wanted}."
          + (" Google refused further lookups part-way." if _blocked.is_set() else ""))
    print("# An item with no URL could not be resolved: find it by searching the exact")
    print("# headline plus the outlet's domain.\n")
    seen = set()
    for section, outlet, fresh in sections:
        print(f"## [{section}] {outlet}")
        for i in fresh:
            key = i["title"].lower()[:80]
            dupe = " (DUPLICATE — appeared above)" if key in seen else ""
            seen.add(key)
            when = i["when"].strftime("%a %b %d %H:%M") if i["when"] else "undated"
            src = f" | source: {i['source']}" if i["source"] else ""
            # a repeat's URL is already printed under its first appearance
            link = f"\n  {i['link']}" if i["link"] and not dupe else ""
            print(f"- {i['title']} ({when}{src}){dupe}{link}")
            if i["desc"]:
                print(f"  > {i['desc']}")
        print()


if __name__ == "__main__":
    main()
