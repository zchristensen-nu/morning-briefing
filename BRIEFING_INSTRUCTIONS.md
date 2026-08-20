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

**Publisher feeds now carry the Tier 1 stories.** WSJ (US news + opinion), NYT (education,
opinion, US, business), the Economist, AP, CSM, NPR, the Guardian and Inside Higher Ed all
publish working RSS, and those entries arrive with a real, canonical article URL that needs
no verification. This is the primary source of Tier 1 coverage — read those sections first
and hardest. The Google News `site:` queries are a supplement, not the backbone: they
return an outlet's general firehose and their links are dead redirects.

**Reading the digest.** It runs 1,200-1,500 lines. Read it in chunks with offset/limit —
about 250 lines at a time is safe. Entries that came from a publisher feed carry a usable
URL; entries from a news search carry none, because Google's redirect links are dead ends
and the canonical URL has to be found by headline search regardless (step 3).

**Never end a run with work outstanding.** This is a scheduled, headless session: nothing
resumes it, so anything left pending is simply lost. If you delegate reading or extraction
to subagents, wait for every one of them to report before continuing, and do not finish the
run until the briefing is written, the page is rendered and the commit is pushed. A run
that stops mid-way produces no briefing at all, which is worse than any imperfect one.
On 2026-08-20 a run ended while two extraction subagents were still working and delivered
nothing.

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

**Outlets are tiered, and the tiers are not interchangeable.**

- **Tier 1** — New York Times, Wall Street Journal, Washington Post, Financial Times, The
  Atlantic, Bloomberg, The Economist, The Guardian, BBC, NPR, AP, Reuters, The Times (UK),
  The New Yorker, Forbes, Christian Science Monitor, Nature, USA Today, Newsweek.
- **Tier 2 (regional)** — the campus-city outlets in feeds.tsv: Boston Globe, Charlotte
  Observer, Seattle Times, SF Chronicle, LA Times, Miami Herald, Tampa Bay Times, CalMatters,
  Globe and Mail, Toronto Star, CBC, Press Herald, Mainebiz, Virginia Mercury, the city
  business journals, and public-radio affiliates (WBUR, WFAE, KQED, WUSF, Maine Public, VPM).
- **Trade press** — Inside Higher Ed, The Chronicle of Higher Education, Times Higher
  Education, Higher Ed Dive.

**Higher Ed News is a Tier 1 section.** Trade press is capped at **2 entries** there, and
only after Tier 1 is genuinely exhausted. The regional section may lead with one Inside
Higher Ed and one Times Higher Education highlight as usual — that is **2 more, and that is
the ceiling**.

Hard caps across the whole briefing:
- **No more than 4 trade-press entries in total**, and no more than 3 from any one trade
  outlet. Nine Inside Higher Ed entries in one briefing, as happened on 2026-08-20, is a
  failed run.
- **No more than 3 entries from any single outlet**, Tier 1 included.

MANDATORY CHECK before writing the file: count every entry by outlet and by tier. If the
trade-press total exceeds 4, if any outlet exceeds 3, or if Higher Ed News carries more
than 2 trade-press entries, the selection has failed — go back and re-read the Tier 1 feed
sections and the topic sweeps in the digest before trying again.

When the obvious stories run out, fill to 10 in this order — never by inventing, never by
padding with stories that fail the skip rules:
1. Second-tier items from the MAJOR outlets already in the digest: stories that passed the
   relevance test but lost out to stronger ones. Read those feed sections again in full —
   good stories sit below the top of a noisy feed.
2. The topic sweeps in the digest ([Topic] sections). These are the most reliable way to
   find major-outlet coverage, because Google's `site:` operator returns an outlet's
   general firehose rather than its education stories — a paywalled major's best piece
   often appears ONLY in a topic sweep, credited to that outlet.
3. The ACE headlines page (step 1) for anything from NYT/WSJ/Bloomberg the feeds missed.
4. Labeled opinion, editorial and analysis from major outlets (still never as the lead).
5. A wider regional net for the regional section: any campus-city outlet in feeds.tsv,
   including business journals and public radio, on university-adjacent business, real
   estate, workforce or city politics.
6. Stretch to 48 hours for major-outlet stories that did not appear in a previous briefing.
7. Only now, trade press — and no more than the 2-entry cap allows.

If a section still cannot reach 10 after all seven, publish what genuinely qualifies and
record in production notes how many were found and which steps were tried. A short honest
section beats a padded one, and a section padded with trade press is worse than a short one.

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
story, pick the strongest outlet. **The same event never gets two entries** — not in the
same section, and not one in Higher Ed News and another in the regional section. On
2026-08-20 the UNC System's answer to Secretary McMahon ran twice, once from Inside Higher
Ed and once from WFAE; that is one story, so pick one outlet and drop the other.

Read the **last five files** in `briefings/`, not just the most recent, and do not repeat a
story from any of them unless there is a significant new development.

**Story waves count as one story, capped at one entry per week.** When a single federal
action, ruling or policy prompts a run of institutions to respond one after another, each
response is not a new story. Recent examples: state systems answering McMahon's "call to
action" (Florida on 08-19, UNC on 08-20 — the second should not have run), DOJ opening
Title VI investigations at successive universities, universities joining the same amicus
brief. Give the wave one entry, then leave it alone for a week unless something materially
new happens: a court ruling, a reversal, a refusal, the first institution to break ranks,
or a development with a direct Northeastern angle. Continuing coverage of the same wave
belongs in threads.tsv, where it is tracked, not in the briefing every morning.

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
