#!/usr/bin/env python3
"""Render a briefing markdown draft into house-format HTML for the email body.

Usage: python3 render_email.py briefings/YYYY-MM-DD.md > out.html
Format (matches sent newsletters): bold underlined title, italic tagline,
red bold underlined section headers, bold outlet names, hyperlinked headlines,
plain one-line summaries, italic footer. Production notes (below ---) excluded.
"""
import re
import sys

md = open(sys.argv[1]).read().split("\n---\n")[0]  # drop production notes

F = "font-family:Calibri,Arial,sans-serif;font-size:11pt;"
out = [f'<div style="{F}color:#000">']
entries = []

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
        out.append(f'<p style="{F}margin:14pt 0 6pt;color:#C00000"><b><u>{block.strip("*")}</u></b></p>')
    elif block.startswith("*Please visit") or block.startswith("*To get in touch"):
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, block.strip("*"))
        out.append(f'<p style="{F}margin:12pt 0 0"><i>{text}</i></p>')
    elif block.startswith("**"):  # outlet name opens a new entry
        entries.append({"outlet": block.strip("*"), "headline": "", "summary": ""})
    elif entries and block.startswith("["):
        h = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, " ".join(block.split("\n")))
        # bold any format label after the link, e.g. (Op-ed)
        entries[-1]["headline"] = re.sub(r"</a>\s*(\([^)]+\))$", r"</a> <b>\1</b>", h)
        out.append(entries[-1])  # placeholder position
    elif entries and entries[-1]["headline"] and not entries[-1]["summary"]:
        entries[-1]["summary"] = " ".join(block.split("\n"))

html = []
for piece in out:
    if isinstance(piece, str):
        html.append(piece)
    else:
        e = piece
        entry = f'<p style="{F}margin:0 0 10pt"><b>{e["outlet"]}</b><br>{e["headline"]}'
        if e["summary"]:
            entry += f'<br>{e["summary"]}'
        html.append(entry + "</p>")
html.append("</div>")
out = html
print("\n".join(out))
