---
name: twice-daily-sweep
description: The Chief of Staff's recurring pass — run each specialist over what changed, update ops/watch.md, and report only what needs the user, in chat (never a digest email). Use when a scheduled sweep fires, or when the user asks "what needs me" / "run the sweep".
---
# Twice-Daily Sweep

Schedule it morning and late afternoon (cron, a Claude Code routine, or n8n). Each run:

1. **Mail, everything, not just the inbox:** `in:anywhere after:<last sweep>` minus newsletters, plus anything labeled `OfficerCan/NeedsYou`, plus the list of drafts (to see which ones the user has sent since last time). For any thread that moved, read the **newest** messages in full. Hand new threads to the Inbox Clerk (`sort-every-email`).
2. **Drafts:** for each draft we created, is it still unsent? If it's older than 2 days and still relevant, remind the user once. If it vanished, find the sent version and read what was actually sent (the user may have edited it) before updating the watch list.
3. **Files and expiry:** File Clerk's expiry sweep (`index-and-expiry`).
4. **Checklists:** Compliance Chaser: which items closed, which chases are due (`chase-until-complete`).
5. **Questions:** drain `ops/questions.jsonl` (`ask-dont-guess`).
6. **Costs:** Cost Manager's budget check (`budgets-and-kill-switches`). Mention it only if something crossed 80%.
7. **Update `ops/watch.md`:** one bullet per open item (who, what, since when, next step, ids). Remove resolved items and stamp the date at the top. This file is the memory between sweeps.

## Report (in chat)
- Lead with decisions, most urgent first, 1–3 sentences each **with a recommendation**.
- Then "drafts waiting on you" (one line each) and anything filed or completed.
- Nothing needs the user? Say so in one line. Don't pad it.
- Push a phone notification only when there's something to act on today.

## Never
- Send a digest email.
- Remind about the same thing more than once per sweep, or keep pushing after the user has said to stop.
- Conclude "no reply yet" from an inbox-only search.
