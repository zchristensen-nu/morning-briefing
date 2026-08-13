#!/usr/bin/env python3
"""Wrap the house-format email HTML in the copy-paste Artifact page.

Usage: python3 render_page.py briefings/YYYY-MM-DD.md > page.html
The page shows the briefing on a white sheet exactly as it should look in
Outlook, with a Copy button that puts the rich HTML on the clipboard.
"""
import re
import subprocess
import sys
from pathlib import Path

md_path = sys.argv[1]
body = subprocess.run(
    [sys.executable, str(Path(__file__).parent / "render_email.py"), md_path],
    capture_output=True, text=True, check=True,
).stdout
title = re.sub(r"\*", "", open(md_path).readline()).strip()

print(f"""<title>The Morning Briefing</title>
<style>
  :root {{
    --ground:#FAFAF8; --ink:#1A1A1A; --muted:#6B6B6B; --border:#E4E2DD;
    --accent:#C00000; --btn-ink:#FFFFFF;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ --ground:#1C1B1A; --ink:#EDEBE8; --muted:#9C9994; --border:#3A3835; }}
  }}
  :root[data-theme="dark"] {{ --ground:#1C1B1A; --ink:#EDEBE8; --muted:#9C9994; --border:#3A3835; }}
  body {{ background:var(--ground); color:var(--ink); margin:0;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .bar {{ max-width:680px; margin:0 auto; padding:28px 20px 14px;
          display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
  .bar h1 {{ font-size:15px; font-weight:600; margin:0; letter-spacing:.01em; }}
  .bar .hint {{ color:var(--muted); font-size:13px; margin-right:auto; }}
  button {{ background:var(--accent); color:var(--btn-ink); border:0; border-radius:4px;
            font:600 13px/1 inherit; font-family:inherit; padding:9px 16px; cursor:pointer; }}
  button:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  /* The sheet is the email: always white, light-only, exactly as it pastes. */
  .sheet {{ background:#FFFFFF; color:#000; max-width:680px; margin:0 auto 48px;
            padding:36px 40px; border:1px solid var(--border); border-radius:2px; }}
  .sheet a {{ color:#0563C1; }}
</style>
<div class="bar">
  <h1>{title}</h1>
  <span class="hint">Copy, then paste straight into the Outlook email body.</span>
  <button id="copy">Copy briefing</button>
</div>
<div class="sheet" id="briefing">{body}</div>
<script>
  const btn = document.getElementById("copy");
  btn.addEventListener("click", async () => {{
    const el = document.getElementById("briefing");
    try {{
      await navigator.clipboard.write([new ClipboardItem({{
        "text/html": new Blob([el.innerHTML], {{type: "text/html"}}),
        "text/plain": new Blob([el.innerText], {{type: "text/plain"}}),
      }})]);
      btn.textContent = "Copied";
    }} catch (e) {{
      const r = document.createRange(); r.selectNodeContents(el);
      const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      document.execCommand("copy"); s.removeAllRanges();
      btn.textContent = "Copied";
    }}
    setTimeout(() => btn.textContent = "Copy briefing", 2500);
  }});
</script>""")
