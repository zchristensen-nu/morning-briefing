# Self-heal — instructions for the failure routine

Followed by the `morning-briefing-self-heal` cloud routine, which a GitHub webhook fires
when a workflow run on `main` in this repo fails. The job: get the pipeline green again
with the smallest correct change, merge it, and tell Zach in Slack what happened. Edit
HERE, not in the routine prompt. Today = the current date in America/New_York.

GraphQL is blocked in the cloud sandbox, so `gh pr create`, `gh pr merge` and a bare
`gh workflow run` fail. Use `gh api` REST calls against `repos/zchristensen-nu/morning-briefing/…`
throughout. Never wait in the background or end your turn to wait; poll in a foreground
`until … ; do sleep 20; done` loop (see BRIEFING_INSTRUCTIONS.md §1 for why).

## 1. Which run

The trigger may not filter events. If the event that fired you is not a `workflow_run`
with `action` `completed`, `conclusion` `failure` and `head_branch` `main`, or the run
is "Self-heal notify", stop at once: change nothing, notify nothing.

The webhook event that fired you should name the run (`workflow_run.id`, `.name`,
`.html_url`). If it is missing, take the newest failed run on main:
`gh api 'repos/zchristensen-nu/morning-briefing/actions/runs?branch=main&status=failure&per_page=1'`.
Read the failed job log: `gh api …/actions/runs/<id>/jobs`, then `gh api …/actions/jobs/<job_id>/logs`.

## 2. Loop guard

If a PR labelled `self-heal` was already opened today, or this run's own failure is in a
change a `self-heal` PR made, change no code: notify "Needs you: second failure today"
with the run link, and stop.

## 3. Triage

- **Already recovered.** A later run of the same workflow succeeded with the same inputs,
  or what the run was meant to produce is on origin/main (e.g. the digest file). This is
  what a duplicate dispatch looks like. Notify "Recovered on its own", stop.
- **Transient.** Runner or network trouble, a GitHub outage, a push race, one feed timing
  out. Rerun: `gh api -X POST …/actions/runs/<id>/rerun-failed-jobs`, then wait (up to
  ten minutes) for that run's conclusion. Passed → notify "Rerun passed", stop. Failed the
  same way → treat it as a bug.
- **Bug.** Something in this repo's code (workflows, `fetch_headlines.py`, `render_*.py`,
  the shell scripts, a dead `feeds.tsv` entry) makes it fail. Go to 4.

## 4. Fix

Find the root cause and make the smallest change that fixes it, in this repo only.

Never: edit `briefings/`, `digests/`, `near-misses/`, `threads.tsv`, `docs/index.html`
or `BRIEFING_INSTRUCTIONS.md`; touch secrets, Slack channels or recipients; delete or
disable a workflow, step or check to make red go green; widen `permissions:`; change
schedules. A fix that needs any of these, or an editorial judgment, is not yours: open
the PR without merging and notify "Needs you".

1. Branch `self-heal/<today>-<slug>` from origin/main, commit, push.
2. Open the PR with REST (`gh api -X POST …/pulls`, base `main`) and add the `self-heal`
   label (`gh api -X POST …/issues/<n>/labels -f 'labels[]=self-heal'`). Body: the run
   link and the error line, the cause in a sentence, the change, how you verified it.
3. Verify on the branch. Run a changed script directly where the sandbox allows (feeds are
   blocked here, so a fetch change is verified in Actions). For a workflow change, or
   anything the workflow exercises, dispatch the failed workflow on the branch with the
   failed run's inputs (`gh api -X POST …/actions/workflows/<file>/dispatches -f ref=<branch> …`)
   and wait for success.
4. Verified → squash-merge: `gh api -X PUT …/pulls/<n>/merge -f merge_method=squash`, then
   delete the branch. Not verified → leave the PR open and notify "Needs you".
5. If the failure left today's pipeline short (a digest that never landed), dispatch the
   failed workflow again on main with its original inputs.

## 5. Notify — always, exactly once

`gh api -X POST repos/zchristensen-nu/morning-briefing/actions/workflows/self-heal-notify.yml/dispatches -f ref=main -f 'inputs[text]=<message>'`

Slack mrkdwn, short and plain, in Zach's voice (no headings, no padding):

```
*Fixed and merged* | *Rerun passed* | *Recovered on its own* | *Needs you*
<run url|Workflow name> failed: <the error, one line>
Cause: <one sentence>
Changed: <PR url|#n> — <file>: <what changed>   (one line per file; omit if nothing changed)
```
