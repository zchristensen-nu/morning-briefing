#!/usr/bin/env python3
"""Render the briefing markdown into the team-facing Artifact page.

Usage: python3 render_page.py briefings/YYYY-MM-DD.md > page.html

Three tabs: the briefing itself (white sheet, copy button), the tracked
stories from threads.tsv, and the source list from feeds.tsv. Tables are
generated from those files so they can never drift from what actually runs.
"""
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
title = re.sub(r"\*", "", open(md_path).readline()).strip()


def browsable(rss_url):
    """Google News RSS link -> the equivalent page a person can open."""
    return rss_url.replace("/rss/search?", "/search?") if "news.google.com" in rss_url else rss_url


def describe(url):
    """Plain-language summary of what a feed pulls."""
    if "news.google.com" not in url:
        return "Publisher RSS", "The outlet's own education feed"
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


GROUPS = {"HigherEd": "National outlet", "Topic": "Topic sweep", "BayArea": "Oakland / Bay Area",
          "NewYork": "New York", "PortlandME": "Portland ME", "ArlingtonVA": "Arlington VA",
          "MiamiTampa": "Miami / Tampa"}

source_rows = []
for sec, name, url in [(r[0], r[1], r[2]) for r in rows("feeds.tsv")]:
    method, covers = describe(url)
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
                     f'<div class="arch"><button class="copy sm" data-copy="a{i}">Copy</button>'
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

print(f"""<title>The Morning Briefing</title>
<style>
  :root {{
    --ground:#FAFAF8; --ink:#1A1A1A; --muted:#6B6B6B; --border:#E4E2DD;
    --accent:#C00000; --btn-ink:#FFFFFF; --panel:#FFFFFF; --rss:#E8F0E6; --rss-ink:#2C4A28;
    --srch:#E6EEF7; --srch-ink:#1B3F63;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ --ground:#1C1B1A; --ink:#EDEBE8; --muted:#9C9994;
      --border:#3A3835; --panel:#232221; --rss:#22301F; --rss-ink:#BFD8B8;
      --srch:#1D2B3A; --srch-ink:#B6CFE8; }}
  }}
  :root[data-theme="dark"] {{ --ground:#1C1B1A; --ink:#EDEBE8; --muted:#9C9994;
    --border:#3A3835; --panel:#232221; --rss:#22301F; --rss-ink:#BFD8B8;
    --srch:#1D2B3A; --srch-ink:#B6CFE8; }}
  body {{ background:var(--ground); color:var(--ink); margin:0;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:26px 20px 60px; }}
  .bar {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:16px; }}
  .bar h1 {{ font-size:15px; font-weight:600; margin:0; letter-spacing:.01em; }}
  .bar .hint {{ color:var(--muted); font-size:13px; margin-right:auto; }}
  button.copy {{ background:var(--accent); color:var(--btn-ink); border:0; border-radius:4px;
            font:600 13px/1 inherit; padding:9px 16px; cursor:pointer; }}
  nav {{ display:flex; gap:4px; border-bottom:1px solid var(--border); margin-bottom:20px; }}
  nav button {{ background:none; border:0; border-bottom:2px solid transparent; color:var(--muted);
            font:500 14px/1 inherit; padding:10px 14px; cursor:pointer; }}
  nav button[aria-selected="true"] {{ color:var(--ink); border-bottom-color:var(--accent); }}
  nav button:focus-visible, button.copy:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  [hidden] {{ display:none; }}
  .sheet {{ background:#FFFFFF; color:#000; padding:36px 40px; border:1px solid var(--border);
            border-radius:2px; }}
  .sheet a {{ color:#0563C1; }}
  .meta {{ color:var(--muted); font-size:13px; margin:0 0 14px; }}
  .scroll {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
  th {{ text-align:left; font-weight:600; color:var(--muted); font-size:12px;
        letter-spacing:.04em; text-transform:uppercase; padding:0 12px 8px 0;
        border-bottom:1px solid var(--border); white-space:nowrap; }}
  td {{ padding:9px 12px 9px 0; border-bottom:1px solid var(--border); vertical-align:top; }}
  td.k {{ font-weight:500; }}
  td.n {{ font-variant-numeric:tabular-nums; white-space:nowrap; color:var(--muted); }}
  td.g {{ color:var(--muted); white-space:nowrap; }}
  td.c {{ color:var(--muted); }}
  td a {{ color:var(--accent); }}
  .tag {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:11.5px;
          font-weight:500; white-space:nowrap; }}
  .tag.rss {{ background:var(--rss); color:var(--rss-ink); }}
  .tag.srch {{ background:var(--srch); color:var(--srch-ink); }}
  details {{ border-bottom:1px solid var(--border); }}
  summary {{ cursor:pointer; padding:11px 0; font-weight:500; font-size:14px; }}
  summary:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  .arch {{ padding:4px 0 20px; }}
  button.copy.sm {{ font-size:12px; padding:6px 12px; margin-bottom:10px; }}
</style>
<div class="wrap">
<div class="bar">
  <h1>{title}</h1>
  <span class="hint">Copy, then paste straight into the Outlook email body.</span>
  <button class="copy" data-copy="briefing">Copy briefing</button>
</div>
<nav role="tablist">
  <button role="tab" id="t-b" aria-controls="p-b" aria-selected="true">Briefing</button>
  <button role="tab" id="t-t" aria-controls="p-t" aria-selected="false">Tracked stories</button>
  <button role="tab" id="t-s" aria-controls="p-s" aria-selected="false">Sources</button>
  <button role="tab" id="t-a" aria-controls="p-a" aria-selected="false">Archive</button>
</nav>

<section id="p-b" role="tabpanel" aria-labelledby="t-b">
  <div class="sheet" id="briefing">{body}</div>
</section>

<section id="p-t" role="tabpanel" aria-labelledby="t-t" hidden>
  <p class="meta">{len(trend_rows)} running stories the agent follows up on every morning. It opens
  one when a story keeps developing and is unresolved, and retires it once the story concludes or
  goes quiet for two weeks. Newest activity first.</p>
  <div class="scroll"><table>
  <thead><tr><th>Story</th><th>Last news</th><th>Tracking since</th><th></th></tr></thead>
  <tbody>
{trends_html}
  </tbody></table></div>
</section>

<section id="p-s" role="tabpanel" aria-labelledby="t-s" hidden>
  <p class="meta">{len(source_rows)} sources checked every morning — {rss_count} through the
  publisher's own feed, {len(source_rows) - rss_count} through a news search, which is how
  paywalled outlets are covered. Running-story searches are listed under Tracked stories.</p>
  <div class="scroll"><table>
  <thead><tr><th>Source</th><th>How</th><th>Group</th><th>What it pulls</th><th></th></tr></thead>
  <tbody>
{sources_html}
  </tbody></table></div>
</section>

<section id="p-a" role="tabpanel" aria-labelledby="t-a" hidden>
  <p class="meta">Every briefing published so far, newest first. Click one to open it.</p>
{archive_html}
</section>
</div>
<script>
  const tabs = [["t-b","p-b"],["t-t","p-t"],["t-s","p-s"],["t-a","p-a"]];
  for (const [tid, pid] of tabs) {{
    document.getElementById(tid).addEventListener("click", () => {{
      for (const [t, p] of tabs) {{
        const on = t === tid;
        document.getElementById(t).setAttribute("aria-selected", on ? "true" : "false");
        document.getElementById(p).hidden = !on;
      }}
    }});
  }}
  document.addEventListener("click", async (ev) => {{
    const btn = ev.target.closest("button[data-copy]");
    if (!btn) return;
    const el = document.getElementById(btn.dataset.copy);
    try {{
      await navigator.clipboard.write([new ClipboardItem({{
        "text/html": new Blob([el.innerHTML], {{type: "text/html"}}),
        "text/plain": new Blob([el.innerText], {{type: "text/plain"}}),
      }})]);
    }} catch (e) {{
      const r = document.createRange(); r.selectNodeContents(el);
      const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      document.execCommand("copy"); s.removeAllRanges();
    }}
    const was = btn.textContent;
    btn.textContent = "Copied";
    setTimeout(() => btn.textContent = was, 2500);
  }});
</script>""")
