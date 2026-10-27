#!/usr/bin/env python3
"""Render the briefing markdown into the team-facing web page (GitHub Pages).

Usage: python3 render_page.py briefings/YYYY-MM-DD.md > docs/index.html

Styled like NGN Studio. The Briefing tab is an editor: the agent's draft is the starting
sheet; stories can be edited in place, dragged to reorder, removed (×) or added from a link
(headline from the digest when it's there, summary written by the editor). Edits persist per
browser per day and Copy takes what's on screen. Production notes and close calls sit in a
side panel. Other tabs: tracked stories (threads.tsv), sources (feeds.tsv), archive, docs. Tables are
generated from those files so they can never drift from what actually runs.
"""
import base64
import json
import re
import subprocess
import sys
import urllib.parse
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
md_path = sys.argv[1]

body = subprocess.run(
    [sys.executable, str(HERE / "render_email.py"), md_path],
    capture_output=True, text=True, check=True,
).stdout
LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="32" fill="#000"/><path d="M0,73.07V1.06H12.99L52.81,50.48V1.06h14.32V73.07h-13.2L14.32,24.18v48.89H0Z" fill="#fff" transform="translate(15.3 15.18) scale(0.21955) translate(0 -1.06)"/><path d="M240.67 1.01L240.67 8.21L264.23 8.21L243.23 29.21L248.32 34.31L269.5 13.12L269.5 37.04L276.7 37.04L276.7 1.01Z" fill="#cf2b28" transform="translate(32.49 15.18) scale(0.43880) translate(-240.67 -1.01)"/><path d="M78.46,37.06C78.46,16.01,94.36,0,115.41,0c12.46,0,23.97,5.94,31.55,16.91l-11.29,8.06c-5.62-8.48-12.94-11.72-20.26-11.72-13.1,0-22.27,9.86-22.27,23.81s9.54,23.81,22.64,23.81c11.98,0,18.72-7.05,20.36-14.69h-21.79v-12.35h36.27c.21,1.86,.26,3.98,.26,5.78,0,18.51-13.04,34.52-35.1,34.52s-37.33-16.01-37.33-37.06Z" fill="#fff" transform="translate(14.3 32.78) scale(0.22393) translate(-78.46 0)"/><path d="M162.22,73.07V1.06h12.99l39.82,49.42V1.06h14.32V73.07h-13.2l-39.61-48.89v48.89h-14.32Z" fill="#fff" transform="translate(33.57 33.34) scale(0.21955) translate(-162.22 -1.06)"/></svg>'


def browsable(rss_url):
    """Google News RSS link -> the equivalent page a person can open."""
    return rss_url.replace("/rss/search?", "/search?") if "news.google.com" in rss_url else rss_url


SECTION_LABELS = [
    ("Education.xml", "Education section"), ("/education/rss", "Education section"),
    ("1013/rss.xml", "Education topic"), ("Opinion.xml", "Opinion section"),
    ("RSSOpinion", "Opinion section"), ("RSSUSnews", "US news section"),
    ("/US.xml", "US news section"), ("Business.xml", "Business section"),
    ("latest/rss.xml", "Latest stories"), ("ap.xml", "Top news"),
    ("feeds/all", "All stories"), ("highereddive.com", "Newsroom"),
    ("rss/national", "National section"), ("wired.com/feed", "All stories"),
    ("newyorker.com/feed", "All stories"),
    ("insidehighered.com", "Full site (all of it is higher ed)"),
]


def describe(url, edu_filtered=False):
    """Plain-language summary of what a feed pulls."""
    if "news.google.com" not in url:
        label = next((v for k, v in SECTION_LABELS if k in url), "Main feed")
        if edu_filtered:
            label += ", filtered to education stories"
        return "Publisher RSS", label
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("q", [""])[0]
    q = urllib.parse.unquote_plus(q)
    q = re.sub(r"when:\d+d", "", q).strip()
    sites = re.findall(r"site:([^\s)+]+)", q)
    rest = re.sub(r"site:[^\s)+]+", "", q).replace("(", "").replace(")", "").replace('"', "")
    excl = [e.strip() for e in re.findall(r"-([A-Za-z ]+)", rest) if e.strip()]
    rest = re.sub(r"-[A-Za-z ]+", "", rest)
    words = [w.strip() for w in rest.replace(" OR ", ",").split(",") if w.strip()]
    if sites:
        text = f"{', '.join(sorted(set(sites)))} — mentioning {', '.join(words)}" if words \
            else f"{', '.join(sorted(set(sites)))} — everything published"
    else:
        text = "Any outlet — " + ", ".join(words)
    if excl:
        text += f" (excluding {', '.join(excl)})"
    return "News search", text


def rows(path):
    out = []
    for line in (HERE / path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            out.append(parts)
    return out


DOCS = """
<h2>The morning</h2>
<p>Three things happen each weekday, with nobody at a computer. At <b>5:45</b> a script
collects the news. At <b>6:00</b> the AI agent reads what was collected and writes the
briefing. By about <b>6:20</b> it's on this page, ready to send. At <b>7:00</b>, <b>8:00</b>
and <b>9:00</b> it sweeps again for anything that has broken since: a story that clears the
same bar is added at the end of its section, and a note in the production notes says what
was added. Most sweeps add nothing. A sweep never reorders or rewrites what's already there,
and if you've started editing, new stories are merged into your copy and marked <b>New</b>.
If the 6:00 run fails, the next one writes the briefing instead.</p>

<h2>Sending it</h2>
<p>Edit the Briefing tab in place. Each story is three lines, outlet, headline and summary,
and you edit one line at a time: click any text to change it, and Enter moves you to the next
line, so a story can't come apart. Formatting is set by house style, so pasted text arrives
plain. To point a headline at a different article, paste the new link on the headline. Drag a
story by its ⠿ handle to reorder it, and press × to drop it. To add a story the agent missed,
press Enter at the end of a summary, or hover between two stories and press +, or paste the
link anywhere in the briefing. The outlet fills in, and the
headline too when the story was in the morning's digest; anything highlighted is yours to
fill in, including the one-line summary. Edits stay in your browser for the day. Then press
Copy briefing, paste into Outlook, set From to media@northeastern.edu, add the bcc lists,
send.</p>

<h2>How the news is gathered</h2>
<p>Most outlets that matter are paywalled, which is why this was assumed to be impossible.
An AI can't read a paywalled article. But the briefing never needed the article — it needs
a headline, a link and a sentence, and publishers give those away in their news feeds.
That's the same material Google News is built on.</p>
<p>Each morning the script checks 59 feeds: four publisher feeds (the New York Times, NPR,
the Guardian, Inside Higher Ed still run working education feeds), 16 searches scoped to a
single outlet each, 26 topic and campus-city searches, and one search for each running
story. The Sources tab lists all of them. It keeps only what was published in the last 24
hours, or 72 on Mondays so the weekend isn't missed — roughly 1,000 headlines. The agent
also checks the American Council on Education's daily headlines page by hand, because Wall
Street Journal opinion pieces don't surface well in search.</p>

<h2>How the stories are chosen</h2>
<p>Each section carries at least ten stories, strongest first. This is a candidate list to
hand-pick from, not a finished cut — edit down by deleting from the bottom.</p>
<p>The test is whether a Northeastern senior leader would want to know it before their
first meeting. Usually in: federal policy and court rulings, government action against
universities, AI's effect on campuses and hiring, student loans, international students and
visas, closures and mergers, UK university finances, leadership changes, research funding,
campus speech and antisemitism developments, and university-adjacent business or
city-politics stories in campus cities. Usually out: sports, K-12 with no college angle,
old rankings, human interest with no institutional angle, and single small colleges with no
wider relevance.</p>
<p>Opinion pieces, editorials and podcasts are included and labeled, never as the lead.
When several outlets cover the same thing the agent picks one, favouring the strongest
outlet. No story appears twice.</p>
<p>When the obvious stories run out, it fills to ten in a set order: second-tier items from
the same digest, then higher-ed trade press, then more labeled opinion, then a wider
regional net, then a 48-hour stretch for anything that hasn't run before. If it still can't
reach ten it publishes what qualifies and says so in the production notes rather than
padding.</p>

<h2>How the links are checked</h2>
<p>Stories found through search arrive with Google redirect links rather than real
addresses. For each story it keeps, the agent searches the exact headline to find the
article on the publisher's own site, then confirms the date falls inside the window — most
publishers put the date in the address, which makes that checkable. If it can't verify a
link for an important story it keeps the story and flags the link in the production notes.
It never invents a link.</p>

<h2>How repeats are avoided</h2>
<p>Every past briefing is kept (see the Archive tab) and the agent reads the most recent one
before finalizing. Anything that already ran is dropped unless there's a real new
development. For a story it has been tracking, the follow-up must be an article published
today, not the original announcement.</p>

<h2>How tracked stories work</h2>
<p>A tracked story is one that keeps developing: a lawsuit, a federal investigation, a
campus sale, a presidential search, a financial crisis. The agent starts tracking one when
a story has appeared across two or more days, or in three or more outlets, and is clearly
unresolved. It stops when the story concludes or two weeks pass with nothing new. The
Tracked stories tab shows what it's watching now and when each last produced news.</p>

<h2>Production notes</h2>
<p>The panel on the right of the Briefing tab shows what the agent recorded during the run:
what it cut and why, which links need a manual fix, which stories it started or stopped
tracking, and anything that failed. If a briefing looks thin, the reason is usually there.
Above the notes, <b>Close calls</b> lists stories it nearly ran; press Add to put one back.
Hide the panel with the Notes button.</p>

<h2>What it never does</h2>
<p>It never sends email, never adds recipients, never touches the distribution list. It
produces a draft; a person sends it.</p>

<h2>Worth knowing</h2>
<p><b>Judgment calls are judgment calls.</b> If it keeps including something you'd cut, or
skipping something you'd run, that's a rule to change rather than a malfunction. The rules
live in one document the agent reads every morning. Say what you want different.</p>
<p><b>Paywalled opinion and feature writing is the weak spot.</b> Search engines index it
poorly. The daily check of the ACE headlines page covers most of it, but this is where a
miss is most likely.</p>
<p><b>Search results have noisy tails.</b> Open a source and you may see results with
nothing to do with education. That's expected — results come back ranked by relevance, the
real stories sit at the top, and the agent reads all of them before choosing.</p>
<p><b>A broken search looks like a quiet news day.</b> If a search stops returning
anything, nothing announces it. That's why the source list isn't editable here.</p>
<p><b>The clock is set in UTC.</b> The run happens at 6:00 Eastern now; after the clocks
change in November it happens at 5:00 Eastern — earlier, never later, so it's always ready
before 9.</p>
"""

GROUPS = {"HigherEd": "National outlet", "Topic": "Topic sweep", "BayArea": "Oakland / Bay Area",
          "NewYork": "New York", "PortlandME": "Portland ME", "ArlingtonVA": "Arlington VA",
          "MiamiTampa": "Miami / Tampa"}

source_rows = []
for r in rows("feeds.tsv"):
    sec, name, url = r[0], r[1], r[2]
    method, covers = describe(url, len(r) > 3 and "filter=edu" in r[3])
    source_rows.append((GROUPS.get(sec, sec), name, method, covers, browsable(url)))

trend_rows = []
for parts in rows("threads.tsv"):
    meta = parts[3] if len(parts) > 3 else ""
    opened = re.search(r"opened=(\S+)", meta)
    last = re.search(r"last_hit=(\S+)", meta)
    trend_rows.append((parts[1], opened.group(1) if opened else "—",
                       last.group(1) if last else "—", browsable(parts[2])))
trend_rows.sort(key=lambda r: r[2], reverse=True)

today = Path(md_path).name
past = sorted((HERE / "briefings").glob("*.md"), reverse=True)
past = [p for p in past if p.name != today][:60]
archive_html = ""
for i, p in enumerate(past):
    head = re.sub(r"\*", "", p.read_text().splitlines()[0]).strip()
    inner = subprocess.run([sys.executable, str(HERE / "render_email.py"), str(p)],
                           capture_output=True, text=True, check=True).stdout
    archive_html += (f'<details><summary>{escape(head)}</summary>'
                     f'<div class="arch"><button class="btn outline" data-copy="a{i}">Copy</button>'
                     f'<div class="sheet" id="a{i}">{inner}</div></div></details>\n')
if not archive_html:
    archive_html = '<p class="meta">No earlier briefings yet.</p>' 


def cell(s):
    return escape(str(s))


trends_html = "\n".join(
    f'<tr><td class="k">{cell(n)}</td><td class="n">{cell(last)}</td>'
    f'<td class="n">{cell(op)}</td><td><a href="{cell(u)}">live search</a></td></tr>'
    for n, op, last, u in trend_rows)

sources_html = "\n".join(
    f'<tr><td class="k">{cell(n)}</td><td><span class="tag {"rss" if m == "Publisher RSS" else "srch"}">'
    f'{cell(m)}</span></td><td class="g">{cell(g)}</td><td class="c">{cell(c)}</td>'
    f'<td><a href="{cell(u)}">open</a></td></tr>'
    for g, n, m, c, u in source_rows)

rss_count = sum(1 for r in source_rows if r[2] == "Publisher RSS")

# House outlet names by domain, learned from past briefings, so a pasted link gets the
# same masthead the agent would use ("The Wall Street Journal", not "WSJ").
outlets = {}
for p in sorted((HERE / "briefings").glob("*.md")):
    for name, url in re.findall(r"^\*\*([^*\n]+)\*\*[^\n]*\n\n\[[^\]]+\]\((https?://[^)\s]+)\)",
                                p.read_text(), re.M):
        host = urllib.parse.urlparse(url).hostname or ""
        if "google" not in host:
            outlets[host.removeprefix("www.")] = name

# Headlines from the latest two morning digests (plus today's sweeps), so a pasted link
# usually gets its real headline. The summary is always left for the editor to write.
headlines, seen = [], set()
digests = sorted((HERE / "digests").glob("*.md"))
mornings = [d for d in digests if "-sweep-" not in d.name][-2:]
sweeps = [d for d in digests if d.name.startswith(Path(md_path).stem + "-sweep-")]
for p in sweeps[::-1] + mornings[::-1]:
    outlet, cur = "", None
    for line in p.read_text().splitlines():
        if line.startswith("## "):
            outlet, cur = re.sub(r"^## \[[^\]]*\]\s*", "", line).strip(), None
            continue
        m = re.match(r"- (.+) \(([^()]*)\)$", line)
        if m:
            src = re.search(r"source: (.+)$", m.group(2))
            cur = None
            if m.group(1) not in seen:
                seen.add(m.group(1))
                cur = {"t": m.group(1), "o": src.group(1) if src else outlet, "u": ""}
                headlines.append(cur)
        elif cur and line.startswith("  http"):
            cur["u"] = line.strip()
editor_data = json.dumps({"date": Path(md_path).stem, "outlets": outlets, "headlines": headlines},
                         separators=(",", ":")).replace("</", "<\\/")

STYLE = """
  :root {
    --chrome:#ffffff; --canvas:#f0f0f0; --dot:rgb(0 0 0 / .07); --line:#e6e6e6;
    --field:#f5f5f5; --field-hover:#ececec; --raised:#ffffff;
    --text:#1e1e1e; --text-2:#6b6b6b; --text-3:#737373;
    --sel:#C8102E; --sel-soft:rgb(200 16 46 / .1); --sel-text:#A50D26; --on-sel:#ffffff;
    --btn:#C8102E; --btn-hover:#A50D26; --warn:#f24822; --todo:#fff3bf;
    --toast:#1e1e1e; --toast-text:#ffffff;
    --shadow-art:0 1px 2px rgb(0 0 0 / .08), 0 8px 32px rgb(0 0 0 / .12);
    --shadow-pop:0 1px 3px rgb(0 0 0 / .12), 0 6px 20px rgb(0 0 0 / .16);
    --ui:"Inter", system-ui, -apple-system, sans-serif; --r:6px; --bar:48px;
  }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --chrome:#2c2c2c; --canvas:#1e1e1e; --dot:rgb(255 255 255 / .06); --line:#3a3a3a;
    --field:#383838; --field-hover:#424242; --raised:#4a4a4a;
    --text:#f5f5f5; --text-2:#b3b3b3; --text-3:#a3a3a3;
    --sel-soft:rgb(232 74 95 / .2); --sel-text:#FF8A99; --toast:#f5f5f5; --toast-text:#1e1e1e;
    --shadow-art:0 1px 2px rgb(0 0 0 / .4), 0 12px 40px rgb(0 0 0 / .5); color-scheme:dark;
  } }
  :root[data-theme="dark"] {
    --chrome:#2c2c2c; --canvas:#1e1e1e; --dot:rgb(255 255 255 / .06); --line:#3a3a3a;
    --field:#383838; --field-hover:#424242; --raised:#4a4a4a;
    --text:#f5f5f5; --text-2:#b3b3b3; --text-3:#a3a3a3;
    --sel-soft:rgb(232 74 95 / .2); --sel-text:#FF8A99; --toast:#f5f5f5; --toast-text:#1e1e1e;
    --shadow-art:0 1px 2px rgb(0 0 0 / .4), 0 12px 40px rgb(0 0 0 / .5); color-scheme:dark;
  }
  * { box-sizing:border-box; }
  [hidden] { display:none !important; }
  html, body { height:100%; }
  body { margin:0; background:var(--canvas); color:var(--text); font:400 12px/16px var(--ui);
         -webkit-font-smoothing:antialiased; display:grid; grid-template-rows:var(--bar) minmax(0, 1fr); }
  ::selection { background:var(--sel-soft); }
  :focus-visible { outline:2px solid var(--sel); outline-offset:1px; }
  svg.i { width:16px; height:16px; flex:none; fill:none; stroke:currentColor; stroke-width:1.5;
          stroke-linecap:round; stroke-linejoin:round; }

  .topbar { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:12px;
            padding:0 12px 0 14px; background:var(--chrome); border-bottom:1px solid var(--line); }
  .brand { display:flex; align-items:center; gap:10px; font-weight:600; font-size:13px;
           letter-spacing:-0.01em; min-width:0; white-space:nowrap; }
  .brand svg { width:24px; height:24px; flex:none; }
  .tabs { display:flex; gap:2px; background:var(--field); border-radius:var(--r); padding:2px; }
  .tabs button { padding:5px 12px; border:0; border-radius:4px; background:none; color:var(--text-2);
                 font:500 12px var(--ui); cursor:pointer; white-space:nowrap; }
  .tabs button:hover { color:var(--text); }
  .tabs button[aria-selected="true"] { background:var(--raised); color:var(--text);
                                       box-shadow:0 1px 2px rgb(0 0 0 / .12); }
  .top-actions { display:flex; align-items:center; justify-content:flex-end; gap:8px; min-width:0; }
  body:not([data-tab="b"]) .top-actions > * { display:none; }

  .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; height:28px;
         padding:0 10px; font:500 12px var(--ui); color:var(--text); background:transparent;
         border:1px solid transparent; border-radius:var(--r); cursor:pointer; white-space:nowrap;
         transition:background .12s; }
  .btn:hover { background:var(--field); }
  .btn.outline { border-color:var(--line); }
  .btn.primary { background:var(--btn); color:var(--on-sel); padding:0 12px; }
  .btn.primary:hover { background:var(--btn-hover); }
  .btn:disabled, .btn:disabled:hover { color:var(--text-3); background:var(--chrome); cursor:default; }
  .btn.icon { width:28px; padding:0; color:var(--text-2); }
  .btn.sm { height:24px; padding:0 8px; font-size:11px; gap:4px; }
  .btn.sm svg { width:12px; height:12px; }

  .pane { min-height:0; overflow:auto; background-color:var(--canvas);
          background-image:radial-gradient(var(--dot) 1px, transparent 1px); background-size:16px 16px; }
  .workspace { display:grid; grid-template-columns:minmax(0, 1fr) auto; min-height:0; }
  .stage { padding:40px 40px 72px; }
  .artboard { position:relative; display:grid; gap:8px; max-width:760px; margin:0 auto; }
  .frame-label { display:flex; justify-content:space-between; gap:16px; color:var(--text-2); font-size:11px; }
  .frame-label span:last-child { color:var(--text-3); font-variant-numeric:tabular-nums; }
  .hint { margin:4px 0 0; text-align:center; color:var(--text-3); font-size:11px; }
  .sheet { background:#fff; color:#000; padding:36px 48px; box-shadow:var(--shadow-art); }
  .sheet a { color:#0563C1; }

  /* Editor-only styling sits on the white sheet in both themes, so it uses fixed light values.
     The sheet previews the email: Calibri (Carlito where it isn't installed; same metrics) at
     the email's 11pt, with room to breathe. Inline email styles are only overridden here, on
     the page; Copy briefing sends the email's own markup. Rhythm: 2px between a story's lines,
     22px between stories, 28/12 around section headers. */
  #briefing { outline:none; position:relative; }
  .sheet p, .sheet p * { font-family:Calibri, Carlito, Arial, sans-serif !important; }  /* here and in the Archive */
  .sheet p { line-height:1.38; }
  #briefing > div > p:first-child { margin:0 0 2px !important; }
  #briefing > div > p:nth-child(2) { margin:0 !important; }
  #briefing [data-section] { position:relative; margin:28px 0 12px !important; }
  #briefing [data-entry] { position:relative; z-index:0; margin:0 0 22px !important; }
  /* The story you're over or in sits on a soft card; dragging lifts it. */
  #briefing [data-entry]::after { content:""; position:absolute; inset:-9px -14px; z-index:-1; border-radius:12px;
    background:#f5f5f7; opacity:0; transition:opacity .15s, background .15s, box-shadow .2s; }
  #briefing [data-entry]:hover::after { opacity:1; }
  #briefing [data-entry]:focus-within::after { opacity:1; background:#f2f2f6; }
  #briefing [data-entry].lifted { z-index:3; cursor:grabbing; }
  #briefing [data-entry].lifted::after { opacity:1; background:#fff;
    box-shadow:0 12px 32px rgb(0 0 0 / .16), 0 0 0 1px rgb(0 0 0 / .05); }
  #briefing.sorting [data-entry]:not(.lifted) { pointer-events:none; }
  #briefing.sorting { user-select:none; cursor:grabbing; }
  /* Fields: one per line of a story. inline-block keeps an emptied field clickable and lets
     the lines take their 2px; a link's underline doesn't reach into one, so the headline sets its own. */
  #briefing [data-f] { outline:none; cursor:text; }
  #briefing [data-f="outlet"], #briefing [data-f="head"], #briefing [data-f="sum"] { display:inline-block; min-width:8em; }
  #briefing [data-f="outlet"], #briefing [data-f="head"] { margin-bottom:2px; }
  #briefing [data-f="head"] { text-decoration:underline; text-underline-offset:2px; }
  #briefing [data-f]:empty::before { content:attr(data-ph); color:#a1a1a6; font-weight:400; }
  #briefing a { cursor:text; }
  #briefing [data-todo] { background:#fff3c4; border-radius:3px; box-shadow:0 0 0 2px #fff3c4; }
  /* A story a later sweep added after you started editing: an unread dot, as in Mail. */
  #briefing [data-entry].fresh::before { content:""; position:absolute; left:-33px; top:6px; width:8px; height:8px;
    border-radius:50%; background:#0a7aff; transition:opacity .15s; }
  #briefing [data-entry].fresh:hover::before, #briefing [data-entry].fresh:focus-within::before { opacity:0; }
  /* Grip and ×: out of the way until you're on a story, level with its outlet. */
  .ctl { position:absolute; top:-2px; width:24px; height:24px; padding:0; display:grid; place-items:center;
         border:0; border-radius:6px; background:none; color:#a1a1a6; cursor:pointer; opacity:0;
         transition:opacity .15s, background .15s, color .15s; }
  .ctl svg { display:block; width:14px; height:14px; }
  .grip { left:-42px; cursor:grab; touch-action:none; }
  .x { right:-42px; }
  [data-entry]:hover .ctl, [data-entry]:focus-within .ctl, .lifted .ctl, .ctl:focus-visible { opacity:1; }
  .grip:hover, .x:hover { background:#ececf0; color:#1d1d1f; }
  @media (hover: none) { .ctl { opacity:1; } }
  /* The + between stories: one floating control, positioned over whichever gap the pointer is in. */
  .adder { position:absolute; z-index:2; left:0; right:0; height:24px; margin-top:-12px; display:flex;
           align-items:center; pointer-events:none; }
  .adder::before { content:""; position:absolute; left:34px; right:34px; top:50%; height:1px; background:#d2d2d7; }
  .adder button { position:relative; pointer-events:auto; margin:0 auto; width:22px; height:22px; padding:0;
                  display:grid; place-items:center; border:0; border-radius:50%; background:#fff; color:#6e6e73;
                  cursor:pointer; box-shadow:0 0 0 1px #d2d2d7, 0 1px 2px rgb(0 0 0 / .08);
                  transition:background .15s, color .15s, box-shadow .15s; }
  .adder button:hover { background:var(--sel); color:#fff; box-shadow:none; }
  .adder button svg { width:14px; height:14px; }
  /* "Add a story" sits where the story will, the width of a story's card. */
  .slot { display:flex; align-items:center; gap:10px; height:40px; margin:-6px -14px 22px; padding:0 14px;
          background:#f5f5f7; border:1px solid transparent; border-radius:12px; color:#a1a1a6; font:13px var(--ui);
          transition:background .15s, border-color .15s, box-shadow .15s; }
  .slot:focus-within { background:#fff; border-color:rgb(200 16 46 / .45); box-shadow:0 0 0 3px rgb(200 16 46 / .1); }
  .slot input { flex:1; min-width:0; height:100%; border:0; outline:0; background:none; color:#1d1d1f; font:inherit; }
  .slot input::placeholder { color:#a1a1a6; }

  .notes { width:360px; min-height:0; overflow-y:auto; background:var(--chrome); border-left:1px solid var(--line);
           padding:12px 20px 32px; font-size:12px; line-height:18px; }
  body.notes-off .notes { display:none; }
  .notes-head { display:flex; align-items:center; justify-content:space-between; min-height:28px; }
  .notes h2 { margin:0; font-size:12px; font-weight:600; }
  .notes h3 { margin:0 0 2px; font-size:11px; font-weight:600; }
  .notes-sub { margin:2px 0 12px; color:var(--text-3); }
  .notes-body p { margin:0 0 12px; color:var(--text-2); }
  .notes code { font-size:11px; padding:1px 4px; border-radius:4px; background:var(--field); }
  .notes a { color:var(--sel-text); }
  .near { margin:4px 0 16px; padding-bottom:12px; border-bottom:1px solid var(--line); }
  .near ul { list-style:none; margin:0; padding:0; display:grid; gap:10px; }
  .near li { display:flex; gap:8px; align-items:flex-start; }
  .near li div { flex:1; min-width:0; }
  .near li a, .near li > div { font-weight:500; color:var(--text); }
  .near li span { display:block; font-weight:400; color:var(--text-3); }

  .page { max-width:860px; margin:32px auto 72px; padding:24px 28px; background:var(--chrome);
          border-radius:8px; box-shadow:0 0 0 1px var(--line); font-size:13px; line-height:18px; }
  .page h1 { margin:0 0 4px; font-size:20px; line-height:26px; font-weight:600; letter-spacing:-0.01em; }
  .meta { color:var(--text-2); margin:0 0 16px; }
  .scroll { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; }
  th { text-align:left; font-weight:600; color:var(--text-2); font-size:11px; padding:0 12px 8px 0;
       border-bottom:1px solid var(--line); white-space:nowrap; }
  td { padding:9px 12px 9px 0; border-bottom:1px solid var(--line); vertical-align:top; }
  td.k { font-weight:500; }
  td.n { font-variant-numeric:tabular-nums; white-space:nowrap; color:var(--text-2); }
  td.g, td.c { color:var(--text-2); }
  td.g { white-space:nowrap; }
  td a { color:var(--sel-text); font-weight:500; }
  .tag { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:500;
         white-space:nowrap; background:var(--field); color:var(--text-2); }
  .tag.rss { background:var(--sel-soft); color:var(--text); }
  details { border-bottom:1px solid var(--line); }
  summary { cursor:pointer; padding:11px 0; font-weight:500; }
  .arch { padding:4px 0 20px; display:grid; gap:10px; justify-items:start; }
  .arch .sheet { box-shadow:0 0 0 1px var(--line); width:100%; }
  #p-h .page { font-size:14px; line-height:22px; }
  #p-h h2 { font-size:13px; font-weight:600; margin:24px 0 6px; }
  #p-h p { margin:0 0 12px; max-width:640px; }

  .toasts { position:fixed; left:50%; bottom:20px; transform:translateX(-50%); display:grid; gap:8px;
            justify-items:center; width:max-content; max-width:calc(100% - 32px); pointer-events:none; }
  .toast { pointer-events:auto; display:flex; align-items:center; gap:12px; padding:8px 8px 8px 14px;
           background:var(--toast); color:var(--toast-text); border-radius:8px; box-shadow:var(--shadow-pop);
           font-weight:500; animation:toast-in .24s cubic-bezier(.16, 1, .3, 1); }
  .toast.plain { padding-right:14px; }
  .toast button { font:600 12px var(--ui); color:var(--sel-text); background:none; border:0;
                  padding:4px 6px; border-radius:4px; cursor:pointer; }
  @keyframes toast-in { from { opacity:0; transform:translateY(6px); } }

  @media (max-width: 960px) {
    .topbar { grid-template-columns:auto 1fr; padding:0 8px; }
    .brand span { display:none; }
    .tabs { overflow-x:auto; justify-self:start; max-width:100%; }
    .top-actions { position:fixed; z-index:2; right:16px; bottom:16px; }
    .top-actions .btn { box-shadow:var(--shadow-pop); background:var(--chrome); }
    .top-actions .btn.primary { background:var(--btn); }
    .workspace { grid-template-columns:1fr; grid-auto-rows:max-content; overflow:auto; }
    .workspace .pane { overflow:visible; }
    .notes { width:auto; border-left:0; border-top:1px solid var(--line); overflow:visible; padding-bottom:88px; }
    .stage { padding:16px 16px 24px; }
    .sheet { padding:24px 36px; }
    .grip { left:-34px; }
    .x { right:-34px; }
    #briefing [data-entry].fresh::before { left:-26px; }
    .page { margin:16px; padding:18px 16px; }
  }
"""

SCRIPT = r"""
const DATA = JSON.parse(document.getElementById("data").textContent);
const KEY = "mb:" + DATA.date;
const sheet = document.getElementById("briefing");
const board = document.getElementById("artboard");
const adder = document.getElementById("adder");
const stage = document.getElementById("stage");
const toasts = document.getElementById("toasts");
const SVG = {
  x: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
  grip: '<svg viewBox="0 0 14 14" aria-hidden="true" fill="currentColor"><circle cx="5" cy="3" r="1.2"/><circle cx="9" cy="3" r="1.2"/><circle cx="5" cy="7" r="1.2"/><circle cx="9" cy="7" r="1.2"/><circle cx="5" cy="11" r="1.2"/><circle cx="9" cy="11" r="1.2"/></svg>',
  plus: '<svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><path d="M7 2.5v9M2.5 7h9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
};

// Tabs
const tabs = [...document.querySelectorAll(".tabs button")];
for (const t of tabs) t.addEventListener("click", () => {
  for (const o of tabs) {
    o.setAttribute("aria-selected", o === t ? "true" : "false");
    document.getElementById(o.getAttribute("aria-controls")).hidden = o !== t;
  }
  document.body.dataset.tab = t.id.slice(2);
});

function toast(msg, action, onAction) {
  const el = document.createElement("div");
  el.className = "toast" + (action ? "" : " plain");
  el.append(msg);
  if (action) {
    const b = document.createElement("button");
    b.textContent = action;
    b.onclick = () => { onAction(); el.remove(); };
    el.append(b);
  }
  toasts.replaceChildren(el);
  setTimeout(() => el.remove(), 5000);
}

// Editor: the agent's draft is the starting sheet; edits live in this browser per day.
// Everything with class "ed" is an editor control and never leaves the page.
function clean(root) {
  const c = root.cloneNode(true);
  c.querySelectorAll(".ed").forEach(x => x.remove());
  // An unwritten (or emptied) summary is never copied: drop it and the line break before it.
  c.querySelectorAll("[data-entry] > span").forEach(x => {
    if (x.dataset.todo === x.textContent || !x.textContent.trim()) {
      if (x.previousSibling?.nodeName === "BR") x.previousSibling.remove();
      x.remove();
    }
  });
  c.querySelectorAll("[data-todo]").forEach(x => x.removeAttribute("data-todo"));
  // Field wiring is page-only: the email gets the same markup render_email.py writes.
  c.querySelectorAll("[data-entry] > span").forEach(x => x.replaceWith(...x.childNodes));
  c.querySelectorAll("[data-f], a[tabindex]").forEach(x => {
    for (const a of ["data-f", "data-ph", "contenteditable", "spellcheck", "tabindex"]) x.removeAttribute(a);
  });
  c.querySelectorAll("[data-entry]").forEach(x => {
    x.style.transform = x.style.transition = "";
    x.removeAttribute("class");
  });
  return c;
}
function control(cls, label, svg) {
  const b = document.createElement("button");
  b.className = "ed ctl " + cls; b.type = "button"; b.contentEditable = "false";
  b.setAttribute("aria-label", label); b.title = label; b.innerHTML = svg;
  return b;
}
const entries = () => [...sheet.querySelectorAll("[data-entry]")];
const sections = () => [...sheet.querySelectorAll("[data-section]")];
const href = e => e.querySelector("a")?.getAttribute("href") || "";
function sectionEnd(key) {
  // The last story of a section (or its header when empty).
  let el = sheet.querySelector(`[data-section="${key}"]`);
  while (el && el.nextElementSibling && el.nextElementSibling.matches("[data-entry]")) el = el.nextElementSibling;
  return el;
}
// Layout position ignores transforms, so animations in flight don't make targets jitter.
const top_ = el => sheet.getBoundingClientRect().top + el.offsetTop;
const bottom_ = el => top_(el) + el.offsetHeight;

// Each story is three fields edited one at a time: outlet, headline, summary. The sheet itself
// isn't editable, so Enter can never split a story or leave stray line breaks behind.
const FIELD = "[data-f]";
function field(el, kind, ph) {
  if (el.dataset.f) return;
  el.dataset.f = kind; el.dataset.ph = ph; el.contentEditable = "true"; el.spellcheck = true;
}
function shape(e) {
  const kids = [...e.childNodes].filter(n => !n.classList?.contains("ed"));
  const brs = kids.filter(n => n.nodeName === "BR");
  const outlet = kids.find(n => n.nodeName === "B"), a = e.querySelector("a");
  if (!outlet || !a || !brs.length) return field(e, "line", "");  // not story-shaped: edit as one block
  field(outlet, "outlet", "Outlet");
  if (!a.querySelector("b")) a.replaceChildren(Object.assign(document.createElement("b"), {textContent: a.textContent}));
  field(a.querySelector("b"), "head", "Headline");
  a.tabIndex = -1;  // the headline text is the stop, not the link around it
  let span = kids.find(n => n.nodeName === "SPAN");
  if (!span) {
    if (brs.length < 2) a.after(document.createElement("br"));
    const br2 = [...e.childNodes].filter(n => n.nodeName === "BR")[1];
    span = document.createElement("span");
    while (br2.nextSibling && !br2.nextSibling.classList?.contains("ed")) span.append(br2.nextSibling);
    br2.after(span);
  }
  field(span, "sum", "Add a one-line summary.");
}

function decorate() {
  for (const e of entries()) {
    shape(e);
    if (e.querySelector(".ctl")) continue;
    e.prepend(control("grip", "Drag to reorder, or use the arrow keys", SVG.grip));
    e.append(control("x", "Remove story", SVG.x));
  }
  const title = sheet.querySelector("div > p:first-child u"), tag = sheet.querySelector("div > p:nth-child(2) i");
  if (title) field(title, "line", "Title");
  if (tag) field(tag, "line", "Tagline");
  const n = entries().length;
  document.getElementById("count").textContent = n + (n === 1 ? " story" : " stories");
}
function save() {
  decorate();
  try { localStorage.setItem(KEY, clean(sheet).innerHTML); } catch (e) {}
  document.getElementById("state").textContent = "Edited in this browser";
  document.getElementById("reset").disabled = false;
}
const original = sheet.innerHTML;
try {
  const saved = localStorage.getItem(KEY);
  if (saved) { sheet.innerHTML = saved; document.getElementById("state").textContent = "Edited in this browser"; }
  else document.getElementById("reset").disabled = true;
} catch (e) {}

// Stories you removed, so a later sweep's re-render never brings them back.
const RKEY = KEY + ":removed";
let removed = new Set();
try { removed = new Set(JSON.parse(localStorage.getItem(RKEY) || "[]")); } catch (e) {}
function remember() { try { localStorage.setItem(RKEY, JSON.stringify([...removed])); } catch (e) {} }

// A sweep may have added stories since you started editing: merge them in, marked "New".
{
  const draft = document.createElement("div");
  draft.innerHTML = original;
  const have = new Set(entries().map(href));
  let added = 0;
  for (const d of draft.querySelectorAll("[data-entry]")) {
    const h = href(d);
    if (!h || have.has(h) || removed.has(h)) continue;
    let s = d.previousElementSibling;
    while (s && !s.matches("[data-section]")) s = s.previousElementSibling;
    const end = s && sectionEnd(s.dataset.section);
    if (!end) continue;
    d.classList.add("fresh");
    end.after(d); added++;
  }
  if (added) setTimeout(() => {
    save();
    toast(added === 1 ? "1 new story arrived since your edits. It's marked New."
                      : added + " new stories arrived since your edits. They're marked New.");
  });
}
decorate();
sheet.addEventListener("input", ev => {
  if (ev.target.closest(".ed")) return;  // typing in an add-story box isn't an edit
  const f = ev.target.closest(FIELD);
  if (f && !f.textContent) f.replaceChildren();  // drop the stray <br> browsers leave, so the placeholder shows
  ev.target.closest("[data-entry]")?.classList.remove("fresh");
  for (const t of sheet.querySelectorAll("[data-todo]"))
    if (t.textContent !== t.dataset.todo) t.removeAttribute("data-todo");
  save();
});

// Moving between fields, Notion-style. Enter goes to the next field; from a summary it opens
// "add a story" below. Arrows cross into the neighbouring field at its edge.
const fieldList = () => [...sheet.querySelectorAll(FIELD)];
function goTo(f, atStart) {
  if (!f) return;
  f.focus({preventScroll: true});
  f.scrollIntoView({block: "nearest"});
  const r = document.createRange(); r.selectNodeContents(f); r.collapse(!!atStart);
  const s = getSelection(); s.removeAllRanges(); s.addRange(r);
}
function step(f, by) { const all = fieldList(); return all[all.indexOf(f) + by]; }
function atEdge(f, end) {
  const s = getSelection();
  if (!s.rangeCount || !s.isCollapsed) return false;
  const r = document.createRange(); r.selectNodeContents(f);
  if (end) r.setStart(s.anchorNode, s.anchorOffset); else r.setEnd(s.anchorNode, s.anchorOffset);
  return r.toString() === "";
}
function onEdgeLine(f, down) {
  const s = getSelection();
  if (!s.rangeCount || !s.isCollapsed) return false;
  const c = s.getRangeAt(0).getClientRects()[0];
  if (!c) return true;  // empty field
  const box = f.getBoundingClientRect(), lh = c.height || 16;
  return down ? c.bottom > box.bottom - lh / 2 : c.top < box.top + lh / 2;
}
function enter(f) {
  if (f.dataset.f === "sum") openSlot(f.closest("[data-entry]"));
  else goTo(step(f, 1));
}
sheet.addEventListener("keydown", ev => {
  const f = ev.target.closest?.(FIELD);
  if (!f || ev.isComposing || ev.altKey || ev.ctrlKey || ev.metaKey) return;
  const k = ev.key;
  if (k === "Enter") { ev.preventDefault(); if (!ev.shiftKey) enter(f); return; }
  if (k === "Escape") { f.blur(); return; }
  if (ev.shiftKey) return;  // shift+arrows extend the selection as usual
  let to = null, start = false;
  if (k === "ArrowRight" && atEdge(f, true)) { to = step(f, 1); start = true; }
  else if (k === "ArrowLeft" && atEdge(f, false)) to = step(f, -1);
  else if (k === "ArrowDown" && onEdgeLine(f, true)) { to = step(f, 1); start = true; }
  else if (k === "ArrowUp" && onEdgeLine(f, false)) to = step(f, -1);
  else if (k === "Backspace" && atEdge(f, false)) { ev.preventDefault(); return; }  // never merges fields
  else if (k === "Delete" && atEdge(f, true)) { ev.preventDefault(); return; }
  if (to) { ev.preventDefault(); goTo(to, start); }
});
// The house format is fixed: no bold/italic shortcuts, no line breaks, no dropped-in markup.
// (Mobile keyboards send Enter only as beforeinput, so it's handled here too.)
sheet.addEventListener("beforeinput", ev => {
  const f = ev.target.closest?.(FIELD);
  if (!f) return;
  const t = ev.inputType;
  if (t === "insertParagraph" || t === "insertLineBreak") { ev.preventDefault(); enter(f); }
  else if (t.startsWith("format") || t === "insertFromDrop") ev.preventDefault();
});
sheet.addEventListener("dragover", ev => { if (ev.target.closest?.(FIELD)) ev.preventDefault(); });
sheet.addEventListener("drop", ev => { if (ev.target.closest?.(FIELD)) ev.preventDefault(); });

sheet.addEventListener("click", ev => {
  // Headlines are links: a click edits the text; Cmd/Ctrl-click opens the story.
  const link = ev.target.closest("a");
  if (link && !ev.target.closest(".ed")) {
    ev.preventDefault();
    if (ev.metaKey || ev.ctrlKey) return window.open(link.href, "_blank", "noopener");
  }
  const t = ev.target.closest("[data-todo]");
  if (t) return getSelection().selectAllChildren(t);  // typing replaces the placeholder
  const x = ev.target.closest(".x");
  if (!x) return;
  const entry = x.parentElement, parent = entry.parentNode, next = entry.nextSibling;
  const head = entry.querySelector("a")?.textContent || "story";
  flip(() => entry.remove()); removed.add(href(entry)); remember(); save();
  toast("Removed “" + (head.length > 48 ? head.slice(0, 47) + "…" : head) + "”", "Undo",
        () => { flip(() => parent.insertBefore(entry, next)); removed.delete(href(entry)); remember(); save(); });
});

// FLIP: run a DOM change, then slide every story from where it was to where it now is.
function flip(change, skip) {
  const before = new Map(entries().map(e => [e, e.getBoundingClientRect().top]));
  change();
  for (const e of entries()) {
    if (e === skip || !before.has(e)) continue;
    const d = before.get(e) - e.getBoundingClientRect().top;
    if (!d) continue;
    e.style.transition = "none"; e.style.transform = `translateY(${d}px)`;
    e.offsetHeight;  // commit the start position
    e.style.transition = "transform .18s cubic-bezier(.2, 0, 0, 1)"; e.style.transform = "";
  }
}

// Reordering: press the grip and drag (mouse, pen or touch); the story follows the pointer
// and the others slide aside. Or focus the grip and use the arrow keys.
let drag = null;
sheet.addEventListener("pointerdown", ev => {
  const g = ev.target.closest(".grip");
  if (!g || ev.button > 0) return;
  ev.preventDefault();
  const el = g.parentElement;
  drag = {el, g, grab: ev.clientY - top_(el), y: ev.clientY};
  el.classList.add("lifted"); sheet.classList.add("sorting"); adder.hidden = true;
  el.style.transition = "none";
});
function placeDragged() {
  const {el, y} = drag;
  // Where should it sit? Before the first other item whose middle is below the pointer.
  const others = [...sheet.querySelectorAll("[data-entry], [data-section]")].filter(o => o !== el);
  const first = sections()[0];
  let target = others.find(o => (top_(o) + bottom_(o)) / 2 > y);
  let move = null;
  if (!target) { const last = others[others.length - 1]; if (last !== el.previousElementSibling) move = () => last.after(el); }
  else if (target === first) { if (first.nextElementSibling !== el) move = () => first.after(el); }
  else if (target.previousElementSibling !== el) move = () => target.before(el);
  if (move) flip(move, el);
  el.style.transform = `translateY(${y - drag.grab - top_(el)}px)`;
}
// Window-level: moving the story in the DOM drops pointer capture, so the sheet can miss events.
window.addEventListener("pointermove", ev => {
  if (!drag) return;
  drag.y = ev.clientY;
  placeDragged();
  // Nudge the page when dragging near the top or bottom edge.
  const r = stage.getBoundingClientRect();
  if (ev.clientY < r.top + 48) stage.scrollTop -= 12;
  else if (ev.clientY > r.bottom - 48) stage.scrollTop += 12;
});
function endDrag() {
  if (!drag) return;
  const {el} = drag;
  drag = null;
  el.style.transition = "transform .18s cubic-bezier(.2, 0, 0, 1)"; el.style.transform = "";
  sheet.classList.remove("sorting");
  setTimeout(() => { el.classList.remove("lifted"); el.style.transition = ""; save(); }, 180);
}
window.addEventListener("pointerup", endDrag);
window.addEventListener("pointercancel", endDrag);
sheet.addEventListener("keydown", ev => {
  const g = ev.target.closest(".grip");
  if (!g || (ev.key !== "ArrowUp" && ev.key !== "ArrowDown")) return;
  ev.preventDefault();
  const e = g.parentElement, up = ev.key === "ArrowUp";
  const n = up ? e.previousElementSibling : e.nextElementSibling;
  if (!n) return;
  if (n.matches("[data-entry]")) flip(() => up ? n.before(e) : n.after(e));
  else if (n.matches("[data-section]") && (!up || n !== sections()[0])) flip(() => up ? n.before(e) : n.after(e));
  else return;  // title or footer: already at the edge
  save(); g.focus();
});

document.getElementById("reset").addEventListener("click", () => {
  if (!confirm("Discard your edits and go back to this morning's draft?")) return;
  sheet.innerHTML = original;
  try { localStorage.removeItem(KEY); localStorage.removeItem(RKEY); } catch (e) {}
  removed = new Set();
  decorate();
  document.getElementById("state").textContent = "This morning's draft";
  document.getElementById("reset").disabled = true;
});

// The + between stories. Gaps sit after each section header and after each story.
let gapAfter = null, slot = null;
function gaps() {
  const out = [];
  for (const h of sections()) {
    let el = h;
    while (el) {
      const next = el.nextElementSibling;
      const isEntry = next && next.matches("[data-entry]");
      out.push({after: el, y: isEntry ? (bottom_(el) + top_(next)) / 2 : bottom_(el) + 12});
      if (!isEntry) break;
      el = next;
    }
  }
  return out;
}
board.addEventListener("pointermove", ev => {
  if (drag || slot || ev.pointerType === "touch") return;
  const g = gaps().find(g => Math.abs(g.y - ev.clientY) < 14);
  if (!g || ev.target.closest(".ctl")) { adder.hidden = true; gapAfter = null; return; }
  gapAfter = g.after;
  adder.style.top = (g.y - board.getBoundingClientRect().top) + "px";
  adder.hidden = false;
});
board.addEventListener("pointerleave", () => { adder.hidden = true; });
adder.querySelector("button").addEventListener("click", () => { if (gapAfter) openSlot(gapAfter); });

function openSlot(after) {
  adder.hidden = true;
  slot = document.createElement("div");
  slot.className = "ed slot"; slot.contentEditable = "false";
  slot.innerHTML = SVG.plus;
  const i = document.createElement("input");
  i.type = "url"; i.placeholder = "Paste a link and press Enter · Esc to cancel";
  i.setAttribute("aria-label", "Link to the story to add");
  slot.append(i);
  after.after(slot);
  i.focus();
  const close = () => { if (slot) { slot.remove(); slot = null; } };
  const go = () => { const v = i.value; close(); addLinks(v, after); };
  i.addEventListener("paste", () => setTimeout(go));
  i.addEventListener("keydown", ev => {
    if (ev.key === "Enter") { ev.preventDefault(); go(); }
    if (ev.key === "Escape") { close(); goTo(after.querySelector?.('[data-f="sum"]')); }
  });
  i.addEventListener("blur", () => setTimeout(() => { if (slot && !i.value) close(); }, 150));
}

// Pasting a link anywhere in the sheet adds it as a story right after the one you're in.
// Pasting a link into a headline points that headline at it instead. Text always pastes plain.
sheet.addEventListener("paste", ev => {
  if (ev.target.closest(".ed")) return;
  ev.preventDefault();  // never paste markup into the sheet
  const text = ev.clipboardData.getData("text/plain").trim();
  const f = ev.target.closest?.(FIELD);
  if (!/^(https?:\/\/\S+\s*)+$/.test(text)) {
    if (f) document.execCommand("insertText", false, text.replace(/\s+/g, " "));  // keeps Cmd+Z working
    return;
  }
  if (f?.dataset.f === "head" && !/\s/.test(text)) {
    const a = f.closest("a"), was = a.getAttribute("href");
    try { a.href = new URL(text).href; } catch (e) { return; }
    removed.add(was); remember();  // so the draft's old link isn't merged back in as "New"
    f.closest("[data-entry]").classList.remove("fresh");
    save();
    return toast("Link updated for this headline.");
  }
  const node = getSelection().anchorNode;
  const here = node && (node.nodeType === 1 ? node : node.parentElement);
  let at = here && here.closest("[data-entry], [data-section]");
  // Above the first section, or in the footer: fall back to the end of the nearest section.
  if (!at) {
    const before = here && sections().filter(s => s.compareDocumentPosition(here) & Node.DOCUMENT_POSITION_FOLLOWING).pop();
    at = sectionEnd((before || sections()[0]).dataset.section);
  }
  addLinks(text, at);
});

function outletFor(url) {
  const host = url.hostname.replace(/^www\./, "");
  return DATA.outlets[host] || host;
}
function headlineFromSlug(url) {
  const seg = url.pathname.split("/").filter(Boolean)
    .sort((a, b) => b.split("-").length - a.split("-").length)[0] || url.hostname;
  return seg.replace(/\.[a-z]+$/, "").replace(/[-_]+[0-9a-f]{6,}$/i, "").replace(/[-_]+/g, " ")
            .replace(/\b\w/g, c => c.toUpperCase());
}
// Match a pasted link to a digest headline: the same address, or a headline sharing most of
// the words in the address (search results carry no address, only the headline).
const words = t => t.toLowerCase().replace(/[’'`]/g, "").split(/[^a-z0-9$]+/).filter(w => w.length > 2 && !/^[0-9a-f]{6,}$/.test(w));
const bare = u => u.replace(/^https?:\/\/(www\.)?/, "").split(/[?#]/)[0].replace(/\/$/, "");
const norm = o => (o || "").toLowerCase().replace(/^the\s+/, "").replace(/\.(com|org|net|co\.uk)$/, "");
function digestHeadline(url) {
  const hit = DATA.headlines.find(h => h.u && bare(h.u) === bare(url.href));
  if (hit) return hit.t;
  const slug = words(url.pathname.split("/").filter(Boolean)
    .sort((a, b) => b.split("-").length - a.split("-").length)[0] || "");
  if (slug.length < 3) return "";
  const outlet = norm(DATA.outlets[url.hostname.replace(/^www\./, "")]);
  let best = null, bestScore = 0;
  for (const h of DATA.headlines) {
    if (outlet && norm(h.o) && norm(h.o) !== outlet) continue;
    const tw = new Set(words(h.t));
    const score = slug.filter(w => tw.has(w)).length / slug.length;
    if (score > bestScore) { best = h; bestScore = score; }
  }
  return bestScore >= (outlet ? 0.7 : 0.85) ? best.t : "";
}
function todo(el, text) { el.textContent = text; el.dataset.todo = text; }

// A pasted link becomes a story: outlet from house names, headline from the digest when it's
// there (otherwise guessed from the address and highlighted), summary always for the editor.
function addLinks(text, at) {
  const found = (text || "").match(/https?:\/\/[^\s<>"']+/g) || [];
  if (!found.length) { if ((text || "").trim()) toast("That isn't a link. Paste a full address starting with https://"); return; }
  if (!at) return;
  let last = null;
  for (const raw of found) {
    let url;
    try { url = new URL(raw); } catch (e) { continue; }
    const tpl = sheet.querySelector("[data-entry]");
    const p = document.createElement("p");
    p.dataset.entry = "";
    p.setAttribute("style", tpl ? tpl.getAttribute("style") : "font-family:Calibri,Arial,sans-serif;font-size:11pt;margin:0 0 10pt");
    const outlet = document.createElement("b"), a = document.createElement("a"), head = document.createElement("b");
    const summary = document.createElement("span");
    a.href = url.href; a.append(head);
    outlet.textContent = outletFor(url);
    const known = digestHeadline(url);
    if (known) head.textContent = known;
    else todo(head, headlineFromSlug(url));
    todo(summary, "Add a one-line summary.");
    p.append(outlet, document.createElement("br"), a, document.createElement("br"), summary);
    const after = at;
    flip(() => after.after(p));
    at = last = p;
  }
  save();
  if (last) {
    const s = last.querySelector("span[data-todo]");
    s.focus({preventScroll: true}); getSelection().selectAllChildren(s);
  }
}

// Production notes panel: open by default, remembered per browser.
function setNotes(on) {
  document.body.classList.toggle("notes-off", !on);
  document.getElementById("notesToggle").setAttribute("aria-pressed", on);
  try { localStorage.setItem("mb:notes", on ? "on" : "off"); } catch (e) {}
}
try { if (localStorage.getItem("mb:notes") === "off") setNotes(false); } catch (e) {}
document.getElementById("notesToggle").addEventListener("click",
  () => setNotes(document.body.classList.contains("notes-off")));
document.getElementById("notesClose").addEventListener("click", () => setNotes(false));

// Close calls: pull one back into the briefing.
for (const b of document.querySelectorAll("[data-add]")) {
  if (entries().some(e => href(e) === b.dataset.add)) { b.disabled = true; b.lastChild.textContent = "Added"; }
  b.addEventListener("click", () => {
    b.disabled = true; b.lastChild.textContent = "Added";
    removed.delete(b.dataset.add); remember();
    addLinks(b.dataset.add, sectionEnd("higher"));
    toast("Added to the end of Higher Ed News. Add a summary.");
  });
}

// Copy: the edited sheet minus editor controls, as rich text for Outlook.
document.addEventListener("click", async ev => {
  const btn = ev.target.closest("button[data-copy]");
  if (!btn) return;
  const el = clean(document.getElementById(btn.dataset.copy));
  try {
    await navigator.clipboard.write([new ClipboardItem({
      "text/html": new Blob([el.innerHTML], {type: "text/html"}),
      "text/plain": new Blob([el.innerText || el.textContent], {type: "text/plain"}),
    })]);
  } catch (e) {
    document.body.append(el);
    const r = document.createRange(); r.selectNodeContents(el);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    document.execCommand("copy"); s.removeAllRanges(); el.remove();
  }
  if (btn.dataset.copy !== "briefing") return toast("Copied.");
  const missing = [...sheet.querySelectorAll("[data-entry] > span")]
    .filter(x => x.dataset.todo === x.textContent || !x.textContent.trim());
  const left = sheet.querySelectorAll("[data-todo]").length - missing.filter(x => x.dataset.todo).length;
  if (missing.length) {
    toast(`Copied, but ${missing.length === 1 ? "1 story has" : missing.length + " stories have"} no summary yet. It was copied without one.`,
          "Show", () => { missing[0].scrollIntoView({block: "center", behavior: "smooth"}); missing[0].focus({preventScroll: true}); getSelection().selectAllChildren(missing[0]); });
  } else toast(left ? `Copied. ${left} highlighted ${left === 1 ? "field still needs" : "fields still need"} a look.` : "Copied. Paste it into Outlook.");
});
"""

ICON = {
    "copy": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>',
    "reset": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>',
    "plus": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    "notes": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/></svg>',
    "close": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
}
FAVICON = ("data:image/svg+xml;base64," + base64.b64encode(
    b'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    b'<path d="M0 0V4.796H15.6936L1.70524 18.7843L5.09576 22.1815L19.204 8.06661V24H24V0H0Z" fill="#CF2B28"/>'
    b'</svg>').decode())


# Production notes (below the --- in the briefing) and the near-misses, for the side panel.
def inline(text):
    t = escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)


md_parts = Path(md_path).read_text().split("\n---\n", 1)
notes_paras = [b.strip().strip("*").strip() for b in (md_parts[1] if len(md_parts) > 1 else "").split("\n\n")]
notes_paras = [re.sub(r"^Production notes \(not for email\):\s*", "", n) for n in notes_paras if n]
# Notes are markdown-ish: drop the italics markers and turn "- item" lines into bullets.
notes_html = "\n".join("<p>" + inline(n.replace("*", "")).replace("\n- ", "<br>• ").replace("\n", " ") + "</p>"
                       for n in notes_paras) or '<p class="notes-sub">No production notes today.</p>'

near_html = ""
near_path = HERE / "near-misses" / Path(md_path).name
for line in (near_path.read_text().splitlines() if near_path.exists() else []):
    m = re.match(r"\s*•\s*(?:<(https?://[^|>]+)\|([^>]+)>|([^—]+?))\s*—\s*(.+)", line)
    if not m:
        continue
    url, head, plain, rest = m.groups()
    title_html = f'<a href="{escape(url)}">{escape(head)}</a>' if url else escape(plain.strip())
    add = (f'<button type="button" class="btn outline sm" data-add="{escape(url)}">{ICON["plus"]}Add</button>'
           if url else "")
    near_html += f'<li><div>{title_html}<span>{escape(rest)}</span></div>{add}</li>\n'
near_section = (f'<section class="near"><h3>Close calls</h3><p class="notes-sub">Considered and left out. '
                f'Add one to put it back at the end of Higher Ed News.</p><ul>{near_html}</ul></section>'
                if near_html else "")

title = re.sub(r"\*", "", Path(md_path).read_text().splitlines()[0]).strip()
day = title.split("|")[-1].strip()

print(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>The Morning Briefing</title>
<link rel="icon" type="image/svg+xml" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&family=Inter:wght@400;500;600&display=swap">
<style>{STYLE}</style>
</head>
<body data-tab="b">
<header class="topbar">
  <div class="brand">{LOGO}<span>The Morning Briefing</span></div>
  <nav class="tabs" role="tablist" aria-label="Views">
    <button role="tab" id="t-b" aria-controls="p-b" aria-selected="true">Briefing</button>
    <button role="tab" id="t-t" aria-controls="p-t" aria-selected="false">Tracked stories</button>
    <button role="tab" id="t-s" aria-controls="p-s" aria-selected="false">Sources</button>
    <button role="tab" id="t-a" aria-controls="p-a" aria-selected="false">Archive</button>
    <button role="tab" id="t-h" aria-controls="p-h" aria-selected="false">How it works</button>
  </nav>
  <div class="top-actions">
    <button type="button" class="btn outline" id="notesToggle" aria-pressed="true" aria-controls="notes">{ICON["notes"]}Notes</button>
    <button type="button" class="btn outline" id="reset">{ICON["reset"]}Reset</button>
    <button type="button" class="btn primary" data-copy="briefing">{ICON["copy"]}Copy briefing</button>
  </div>
</header>

<main class="workspace" id="p-b" role="tabpanel" aria-labelledby="t-b">
  <div class="pane stage" id="stage">
    <div class="artboard" id="artboard">
      <div class="adder" id="adder" hidden><button type="button" aria-label="Add a story here" title="Add a story here"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M7 2.5v9M2.5 7h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button></div>
      <div class="frame-label"><span>{escape(day)} · <span id="state">This morning's draft</span></span><span id="count"></span></div>
      <div class="sheet" id="briefing" spellcheck="true">{body}</div>
      <p class="hint">Click text to edit · Enter moves to the next line, and after a summary adds a story ·
      paste a link on a headline to change it, anywhere else to add a story · ⌘-click opens a link ·
      drag ⠿ to reorder · × removes. Edits stay in this browser until Reset.</p>
    </div>
  </div>
  <aside class="notes" id="notes" aria-label="Production notes">
    <div class="notes-head"><h2>Production notes</h2>
      <button type="button" class="btn icon" id="notesClose" aria-label="Hide notes" title="Hide notes">{ICON["close"]}</button></div>
    <p class="notes-sub">What the agent did this morning: what it cut, links it couldn't verify, threads opened or closed. Not part of the email.</p>
    {near_section}
    <section class="notes-body">{notes_html}</section>
  </aside>
</main>

<section class="pane" id="p-t" role="tabpanel" aria-labelledby="t-t" hidden><div class="page">
  <h1>Tracked stories</h1>
  <p class="meta">{len(trend_rows)} running stories the agent follows up on every morning. It opens
  one when a story keeps developing and is unresolved, and retires it once the story concludes or
  goes quiet for two weeks. Newest activity first.</p>
  <div class="scroll"><table>
  <thead><tr><th>Story</th><th>Last news</th><th>Tracking since</th><th></th></tr></thead>
  <tbody>
{trends_html}
  </tbody></table></div>
</div></section>

<section class="pane" id="p-s" role="tabpanel" aria-labelledby="t-s" hidden><div class="page">
  <h1>Sources</h1>
  <p class="meta">{len(source_rows)} sources checked every morning — {rss_count} through the
  publisher's own feed, {len(source_rows) - rss_count} through a news search, which is how
  paywalled outlets are covered. Running-story searches are listed under Tracked stories.</p>
  <div class="scroll"><table>
  <thead><tr><th>Source</th><th>How</th><th>Group</th><th>What it pulls</th><th></th></tr></thead>
  <tbody>
{sources_html}
  </tbody></table></div>
</div></section>

<section class="pane" id="p-a" role="tabpanel" aria-labelledby="t-a" hidden><div class="page">
  <h1>Archive</h1>
  <p class="meta">Every briefing published so far, newest first. Click one to open it.</p>
{archive_html}
</div></section>

<section class="pane" id="p-h" role="tabpanel" aria-labelledby="t-h" hidden><div class="page">
  <h1>How it works</h1>
{DOCS}
</div></section>

<div class="toasts" id="toasts" aria-live="polite"></div>
<script type="application/json" id="data">{editor_data}</script>
<script>{SCRIPT}</script>
</body>
</html>""")
