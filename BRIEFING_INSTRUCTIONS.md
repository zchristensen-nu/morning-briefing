# The Morning Briefing — canonical run instructions

Single source of truth for compiling The Morning Briefing, the daily higher education
and global campus news digest for senior leaders at Northeastern University. Followed
by both the cloud routine and the local scheduled task; edit HERE, not in run prompts.
Today's date = the current date in America/New_York.

## 1. Fetch

**Cloud runner: use the pre-fetched digest.** The cloud sandbox's egress proxy blocks
news domains, so do NOT try to fetch feeds there. A GitHub Action ("Fetch morning
digest", 12:10 UTC weekdays) runs the fetcher and commits `digests/YYYY-MM-DD.md` to
this repo ~20 minutes before the routine fires. Read today's digest from `digests/`.
If today's digest is missing or stale (GitHub cron schedules are best-effort and
sometimes skip), re-trigger it yourself — `gh workflow run fetch-digest.yml`, wait
~90 seconds, `git pull` — and note the missed schedule in production notes. Only if
that also fails, fall back to WebSearch-based discovery — but budget carefully: the
cloud session has a hard cap of 200 WebSearch calls, and link verification (step 3)
needs ~20 of them, so never spend more than ~150 on discovery.

**Local runner: fetch live.** Run `python3 fetch_headlines.py > /tmp/digest.md
2>/tmp/feed_errors.txt` from the repo root. It pulls ~50 RSS feeds defined in
`feeds.tsv` (outlets, topics, cities) and `threads.tsv` (running stories), filtered to
the last 24 hours (72 on Mondays to cover the weekend), preserving Google News
relevance order. Note any FEED ERROR lines for production notes.

**ACE backstop (mandatory):** hard-paywalled outlets — especially WSJ opinion/features —
are poorly indexed by Google News. Fetch ACE's Higher Education Headlines page
(https://www.acenet.edu/News-Room/Pages/Higher-Education-Headlines.aspx; if fetching is
blocked or 404s, web-search "ACE higher education headlines today") and scan for
NYT/WSJ/Bloomberg stories inside the window that the digest missed. Verify each via a
headline search before use.

## 2. Curate

Two sections only: **Higher Ed News** then **Global Campus/Regional News** (loosely grouped
by campus city: Boston, London, Oakland/Bay Area, Seattle, New York, Vancouver, Toronto,
Portland ME, Arlington VA, Miami/Tampa, Charlotte — not every city every day).

**Each section carries AT LEAST 10 stories.** The briefing is a candidate list the media
relations team hand-picks from, not a finished cut. **Order each section strongest first**,
so editing down means deleting from the bottom.

When the obvious stories run out, fill to 10 in this order — never by inventing, never by
padding with stories that fail the skip rules:
1. Second-tier items already in the digest from approved outlets: stories that passed the
   relevance test but lost out to stronger ones.
2. Higher-ed trade press: Chronicle of Higher Education, Inside Higher Ed, Higher Ed Dive,
   Times Higher Education.
3. More labeled opinion, editorial and analysis than the usual one or two (still never as
   the lead).
4. A wider regional net: any campus-city outlet in feeds.tsv, including business journals
   and public radio, on university-adjacent business, real estate, workforce or city
   politics.
5. Stretch to 48 hours for stories that did not appear in a previous briefing.

If a section still cannot reach 10 after all five, publish what genuinely qualifies and
record in production notes how many were found and which steps were tried. A short honest
section beats a padded one.

Inclusion test: would a Northeastern senior leader want to know this before their first
meeting? Strong yes: federal policy and court rulings on higher ed; Trump admin/DOJ
actions against universities; AI's impact on campuses, graduates, and the workforce
(including general AI-industry news); student loans and affordability; value-of-a-degree
analyses; international students and visa/immigration policy (including H-1B); college
closures and mergers; UK university finances; university leadership news; graduate/
entry-level job market and internships; research funding; campus antisemitism/free
speech/DEI developments; university-adjacent business and real-estate stories; notable
city politics/economy stories in campus cities.

Skip: athletics (unless major institutional/legal issue), K-12 with no higher-ed angle,
rankings older than a week, pure human-interest, single-small-institution stories with
no broader relevance.

House curation practice (learned from published briefings):
- The regional section usually LEADS with one Inside Higher Ed highlight and one Times
  Higher Education (or Times UK) highlight when available, before the city items.
- Labeled opinion content is a regular feature, not an exception: expect 1–2 op-eds,
  editorials, or podcasts per briefing from approved outlets (WSJ opinion, Globe
  editorials on workforce/education, USA Today podcasts). Never LEAD the Higher Ed
  section with one.
- Cap any single story at one entry (two if a distinct analysis piece adds real value).

Approved sources: major national/international outlets, the regional outlets in feeds.tsv,
public-radio affiliates (WBUR, WFAE, KQED, WUSF, Maine Public), city business journals,
and (sparingly) Inside Higher Ed / Times Higher Education. Never: .edu sites, .gov press
releases, PR wires, aggregator or syndication mirrors (find the original outlet).

## 3. Link hygiene

Google News items carry news.google.com redirect URLs. For every included story, find the
canonical article URL by web-searching the exact headline plus outlet domain, and verify
the publication date is inside the window. Direct-feed items (NYT Education, NPR,
Guardian, Inside Higher Ed) already have real URLs. Never include a news.google.com link;
never fabricate a URL. **If a canonical URL cannot be found for an otherwise important
story from a major outlet, KEEP the story** — include it with the best available
attribution and flag it prominently in production notes for a manual link fix. Dropping
significant stories over link resolution is worse than a link the team fixes in 10 seconds.

## 4. De-duplicate

The digest marks repeated headlines with (DUPLICATE); when several outlets cover one
story, pick the strongest outlet. Check the most recent file in `briefings/` and do not
repeat a story from it unless there is a significant new development.

**If a briefing file for today already exists, this run is a rebuild.** Overwrite that file
rather than creating another, and de-duplicate against the PREVIOUS day's briefing — never
against today's, which is your own earlier output, not a published edition.

**Thread follow-ups must cite an in-window article — never the thread's original story.**
When a running thread produces fresh developments, the entry's headline, URL, and summary
must all come from an article PUBLISHED INSIDE TODAY'S WINDOW covering the new
development. Linking the original announcement (which already ran in a previous briefing)
with a summary noting it "has since drawn debate" is a duplicate, not a follow-up. If the
only fresh coverage is minor or opinion-only and the story already ran, skip it.
Mechanical check: NYT/WaPo/Guardian URLs carry the publication date in their path
(`/2026/08/11/`) — if that date is outside the window, the article is out of window no
matter what the feed's timestamp said.

## 5. Threads (mandatory)

`threads.tsv` is agent-maintained; its header documents the format
(`Thread <TAB> Name <TAB> query URL <TAB> opened=YYYY-MM-DD last_hit=YYYY-MM-DD`).
After curating: (a) update last_hit to today for every thread with a genuine new
development; (b) delete threads that clearly resolved or whose last_hit is >14 days old;
(c) add a thread for any story that has appeared on 2+ days or in 3+ outlets AND is an
unresolved process (lawsuit, investigation, sale/merger, leadership search, legislation,
protest wave, financial crisis) — write a tight Google News RSS query (quote proper
nouns + story keywords, keep when:2d and country hl/gl/ceid params); (d) record
opened/retired threads in production notes.

## 6. Write

Write the briefing to `briefings/YYYY-MM-DD.md` (today's date). Format exactly:

- First line: `**The Morning Briefing | Month D, YYYY**`
- Then: `*The Morning Briefing is a curated collection of the day's relevant news.*`
- Then `**Higher Ed News**`, then entries. Each entry is three paragraphs:
  `**Outlet Name**`, then `[Headline](URL)` optionally followed by a label like
  `(Op-ed)` / `(Editorial)` / `(Podcast)`, then a one-sentence summary (omit only if
  the headline is fully self-explanatory).
- Then `**Global Campus/Regional News**`, same entry format.
- Footer (italic): `*Please visit NGN's "[In The Press](https://news.northeastern.edu/in-the-media/)" section to view Northeastern's most recent press mentions, updated weekly.*`
  and `*To get in touch with the media relations team, please contact us at [media@northeastern.edu](mailto:media@northeastern.edu).*`
- Then a `---` line and `*Production notes (not for email): ...*` listing threads
  opened/retired, stories kept with unresolved links, stories cut and why, feed errors.

## 7. Publish (cloud routine)

a. Rebuild the team's page:
`python3 render_page.py briefings/YYYY-MM-DD.md > docs/index.html`

That one file is the whole site. GitHub Pages serves it from the `docs/` folder on `main`
at https://zchristensen-nu.github.io/morning-briefing/ — the push in step b is what
publishes it, and Pages redeploys within a minute or two. The page carries a noindex
directive and `docs/robots.txt` blocks crawlers, but **the URL is publicly reachable by
anyone who has it**: never put anything in a briefing you would not want public. Everything
in it is already-published news, which is what makes this acceptable.

The page has five tabs: today's briefing (with the copy button), Tracked stories (from
threads.tsv), Sources (from feeds.tsv), Archive (every earlier file in briefings/), and How
it works (the team's documentation, held in the DOCS string in render_page.py — keep it
accurate when these rules change). The tables are generated from the repo files, so they
stay correct on their own.

Do not publish an Artifact. The team reads the Pages URL.

b. Record the near-misses. Write `near-misses/YYYY-MM-DD.md` — three to five stories you
genuinely considered and left out, one per line, in Slack mrkdwn:

`• <URL|Headline> — Outlet — one short clause on why it was cut`

These get posted as a thread reply under the Slack notification, so the team can pull one
back in if they disagree. Only real candidates belong here: stories that passed the
relevance test but lost on space, were beaten by a stronger outlet on the same story, or
had an unresolvable link. Do not pad it with items that failed the skip rules, and write
nothing (skip the file) on a day when nothing was genuinely close.

c. Commit and push:
`git add briefings/ threads.tsv docs/ near-misses/ && git commit -m "Morning Briefing YYYY-MM-DD" && git push`
Do not commit digests or /tmp files.

## 7-alt. Publish (local scheduled task)

Same as 7, plus: run `sh draft_email.sh briefings/YYYY-MM-DD.md` to place a
recipient-less draft in Outlook, and send the briefing file to the user with a proactive
notification.

## Hard rules

Never send email or messages anywhere — the team sends the newsletter manually. Never
add recipients to anything. The deliverables are the committed briefing file and the
updated page at docs/index.html.
