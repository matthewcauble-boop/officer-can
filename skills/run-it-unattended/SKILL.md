---
name: run-it-unattended
description: Schedule the specialists so they run without the user — triage every few minutes, the sweep twice a day — on a scheduler that actually fires, with every company fact read from config and every path failing closed. Technical Director skill. Use for "run it without me", "schedule it", "why didn't it run".
---
# Run It Unattended

## Pick a scheduler that fires
| Job | Needs | Good options |
|---|---|---|
| Triage + labels + drafts | every 5–30 min | n8n (self-hosted has no execution cap), a cron job on an always-on box, a small cloud function on a timer |
| Twice-daily sweep | 2× a day, a conversation with the user | a scheduled agent session (e.g. a Claude Code routine) so the report lands in chat |
| Nightly learning | once a day | any of the above |

Two traps:
- **GitHub Actions `schedule` is not a clock.** On a busy repo, runs arrive hours late or not at all. Fine for "nightly-ish", wrong for "every 30 minutes". If you use Actions for triage, trigger it with `workflow_dispatch` from a real scheduler.
- **Hosted automation plans have execution quotas.** Running out stops triage silently. Track the quota like a budget (`budgets-and-kill-switches`) and know which of your workflows burns it.

## Shape of the triage job
1. Find what's new: `in:anywhere after:<last-run-epoch> -in:sent -in:drafts`. Never `newer_than:<n>m` in Gmail (that's months).
2. Skip threads that already carry an `OfficerCan/*` label, the user's own messages, and threads with any draft (yours or theirs).
3. Load `config/` at run time: categories, profile, floors. No company facts inside the job's code or workflow nodes.
4. `archive-the-noise` rules, then `sort-every-email`, then route by `action`.
5. Drafts: only through the guarded path from `set-up-officer-can` Phase 3 and `threaded-replies`.
6. Log one row per thread to `ops/runs.jsonl`: time, thread, category, confidence, action, cost.

## Reliability rules (each one has cost real downtime)
1. **Fail closed.** Any error labels the thread `OfficerCan/NeedsYou`. It never sends and never drafts half an answer.
2. **Classify once.** Label every processed thread so the next run skips it.
3. **Keep a replay mode.** Run the job against a list of past message ids, print what it would do, write nothing. Use it after every change.
4. **Guard the prompt.** The classifier prompt must end with the email content. After any edit, assert that block is still there, or everything quietly becomes `other`.
5. **In n8n, never splice raw JSON into an `={{ }}` expression.** A literal `}}` ends the template and the node fails with "invalid syntax". Generate workflows from config with a builder script and assert on the built JSON.
6. **Secrets stay in the scheduler's secret store** (repo secrets, env files with mode 600). Never in the repo, a log or chat.
7. **One automation per inbox.** If an older system still triages the same mailbox, it will label and draft too. Turn it off, or make each skip what the other has labeled.

## Deploying changes
Keep the job's code or workflow JSON in the ops repo. Diff it, replay it, then deploy. Write the schedule and where it runs into `ops/SETUP-NOTES.md`.
