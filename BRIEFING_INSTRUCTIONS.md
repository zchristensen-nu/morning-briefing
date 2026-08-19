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

**Thread follow-ups must cite an in-window article — never the thread's original story.**
When a running thread produces fresh developments, the entry's headline, URL, and summary
must all come from an article PUBLISHED INSIDE TODAY'S WINDOW covering the new
development. Linking the original announcement (which already ran in a previous briefing)
with a summary noting it "has since drawn debate" is a duplicate, not a follow-up. If the
only fresh coverage is minor or opinion-only and the story already ran, skip it.
Mechanical check: NYT/WaPo/Guardian URLs carry the publication date in their path
(`/2026/08/11/`) — if that date is outside the window, the article is out of window no
matter what the feed's timestamp said.

## 4b. Notion trends sync (cloud runner, mandatory — BEFORE curating)

The media relations team manages trends in the Notion hub ("The Morning Briefing",
page id `3bf489d4-fca0-8125-adb6-d358827f3872`) in a "Trends" database (data source
`collection://24b84433-a891-467e-9309-4caaa5e17c48`). **Notion is the team's interface;
threads.tsv remains the machine copy. Sync both directions every run:**

- INTO threads.tsv, before curating: fetch the Trends database. A row with Status
  "Active" that has no matching threads.tsv line is a team-added trend — write a tight
  Google News query for it (fill the row's empty Query URL back into Notion), set
  opened=today, and add the line. A row set to "Retired" whose thread still exists in
  threads.tsv means the team stopped it — delete the line (leave the Notion row as the
  team set it).
- BACK to Notion, after curating: update each row's Last hit date to match threads.tsv;
  for threads the agent opens, create a row (Status Active, all fields filled); for
  threads the agent retires, set the row's Status to "Retired" (never delete team-visible
  rows). Keep Notes current when a thread's situation changes materially.
- SOURCES table (data source `collection://6a5231cc-ef3e-43c0-a319-d14bfdce4af2`) is a
  read-only reference listing every feed in feeds.tsv and how it is pulled. Touch it only
  when feeds.tsv itself changes: add, edit or remove the matching row so it stays accurate.

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

a. Run `python3 render_page.py briefings/YYYY-MM-DD.md > /tmp/page.html` and publish
/tmp/page.html with the Artifact tool, passing
`url=https://claude.ai/code/artifact/faca981e-c281-4ef3-aace-b056cb04e90a` and favicon 📰
so the existing artifact updates in place at its stable link. Always update that exact
artifact, never create a new one.

The page it renders has four tabs: today's briefing (with the copy button), Tracked
stories (from threads.tsv), Sources (from feeds.tsv), and Archive (every earlier file in
briefings/). Those three tables are generated from the repo files, so they stay correct on
their own — no extra step.

b. Create the briefing page in the Notion hub: a child page of the hub page
(`3bf489d4-fca0-8125-adb6-d358827f3872`) titled "The Morning Briefing | Month D, YYYY"
with icon 📰, containing the full briefing (bold outlet names, linked headlines,
one-line summaries, italic tagline and footer), then a `---` divider and a short
**Production notes (not for email)** paragraph. This is where the team reads it daily.
If this is a manual re-run, UPDATE the existing page for today (replace its content)
rather than creating a second page.

c. Commit: `git add briefings/ threads.tsv && git commit -m "Morning Briefing YYYY-MM-DD" && git push`.
Do not commit digests or /tmp files.

## 7-alt. Publish (local scheduled task)

Same as 7, plus: run `sh draft_email.sh briefings/YYYY-MM-DD.md` to place a recipient-less
draft in Outlook, and send the briefing file to the user with a proactive notification.

## Hard rules

Never send email or messages anywhere — the team sends the newsletter manually. Never
add recipients to anything. The deliverables are the committed briefing file and the
updated artifact.
