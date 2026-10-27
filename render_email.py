#!/usr/bin/env python3
"""Render a briefing markdown draft into house-format HTML for the email body.

Usage: python3 render_email.py briefings/YYYY-MM-DD.md > out.html
Format (matches sent newsletters): bold underlined title, italic tagline,
red bold underlined section headers, bold outlet names, bold hyperlinked headlines,
plain one-line summaries, italic footer. Production notes (below ---) excluded.
data-section / data-entry attributes are hooks for the web editor; mail clients ignore them.
"""
import re
import sys

md = open(sys.argv[1]).read().split("\n---\n")[0]  # drop production notes
# Entries sometimes come with outlet, headline and summary on consecutive lines instead of
# blank-line separated (2026-10-22, 10-26, 10-27 rendered no stories). Split them apart.
md = re.sub(r"^(\*\*[^*\n]+\*\*[^\n]*|\[[^\n]+\]\(https?://[^\n]+\)[^\n]*)\n(?=\S)", r"\1\n\n", md, flags=re.M)

F = "font-family:Calibri,Arial,sans-serif;font-size:11pt;"
out = [f'<div style="{F}color:#000">']
entries = []
section = None

def link(m):
    return f'<a href="{m.group(2)}">{m.group(1)}</a>'

for block in md.strip().split("\n\n"):
    block = block.strip()
    if not block:
        continue
    if block.startswith("**The Morning Briefing |"):
        title = block.strip("*")
        out.append(f'<p style="{F}margin:0 0 4pt"><b><u>{title}</u></b></p>')
    elif block.startswith("*") and "curated collection" in block:
        out.append(f'<p style="{F}margin:0 0 12pt"><i>{block.strip("*")}</i></p>')
    elif block in ("**Higher Ed News**", "**Global Campus/Regional News**"):
        key = section = "higher" if "Higher" in block else "global"
        out.append(f'<p data-section="{key}" style="{F}margin:14pt 0 6pt;color:#C00000"><b><u>{block.strip("*")}</u></b></p>')
    elif block.startswith("*Please visit") or block.startswith("*To get in touch"):
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, block.strip("*"))
        gap = "12pt" if block.startswith("*Please visit") else "0"  # the two footer lines sit together
        out.append(f'<p style="{F}margin:{gap} 0 0"><i>{text}</i></p>')
    elif block.startswith("**"):  # outlet name opens a new entry
        entries.append({"outlet": block.replace("**", ""), "headline": "", "summary": ""})
    elif entries and block.startswith("["):
        h = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   lambda m: f'<a href="{m.group(2)}"><b>{m.group(1)}</b></a>', " ".join(block.split("\n")))
        # bold any format label after the link, e.g. (Op-ed)
        entries[-1]["headline"] = re.sub(r"</a>\s*(\([^)]+\))$", r"</a> <b>\1</b>", h)
        out.append(entries[-1])  # placeholder position
    elif entries and entries[-1]["headline"] and not entries[-1]["summary"]:
        summary = " ".join(block.split("\n"))
        if section == "global":  # no city labels ("Boston:", "ArlingtonVA:") on regional stories
            summary = re.sub(r"^[A-Z][A-Za-z .]{1,20}: ", "", summary)
        entries[-1]["summary"] = summary

html = []
for piece in out:
    if isinstance(piece, str):
        html.append(piece)
    else:
        e = piece
        entry = f'<p data-entry style="{F}margin:0 0 10pt"><b>{e["outlet"]}</b><br>{e["headline"]}'
        if e["summary"]:
            entry += f'<br>{e["summary"]}'
        html.append(entry + "</p>")
html.append("</div>")
out = html
print("\n".join(out))
