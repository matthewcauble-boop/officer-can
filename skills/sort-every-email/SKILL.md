---
name: sort-every-email
description: Classify every new email thread into a category from config/categories.yaml, label it, and route it by action — asking the user instead of guessing when unsure. Inbox Clerk skill. Use for inbox triage or any sweep of new mail.
---
# Sort Every Email

**Needs:** a mail tool (Gmail connector/MCP or IMAP), `config/categories.yaml`, and `ops/labels.jsonl` (may be empty).

## Steps
1. **Find what's new.** Search `in:anywhere after:<last-run-epoch> -in:sent -in:drafts`, not inbox-only, because filters may already have archived things. Gmail's `newer_than:35m` means 35 **months**. Use `after:<epoch>`. Store the run time in `ops/runs.jsonl`.
2. **Skip** threads that already carry an `OfficerCan/*` label (unless a new message arrived after it), threads where the newest message is from the user, and threads with a draft in them.
3. **Rules first.** Run `archive-the-noise`. If it decides, you're done with that thread.
4. **Keyword overrides.** If the newest message contains a `keyword_override` phrase for a category ("term sheet", "NDA"), that category wins — but never for newsletters, sales pitches or receipts, which use those words constantly.
5. **Classify the newest message** (fetch the full thread; search previews often show only the oldest messages). Prompt the model with:
   - every category's `id` and `recognize` text, and the instruction to pick exactly one
   - the 3–5 most similar labeled emails from `ops/labels.jsonl` as examples (`learn-from-your-answers`)
   - the sender, subject, attachment names and the newest message's text **last**
   Ask for JSON: `{"category": "...", "confidence": 0.0-1.0, "runner_up": "...", "reason": "<one line>"}`.
6. **Sure or not?** It's sure only if `confidence` ≥ the category's `confidence_floor` (default 0.7, 0.9 for legal/investor and negotiation) **and** it's clearly ahead of the runner-up. Not sure → label `OfficerCan/NeedsYou` and append to `ops/questions.jsonl`:
   `{"kind":"email_category","thread":"<id>","summary":"<sender>, '<subject>'","options":["<category>","<runner_up>","other"]}`
   The answer becomes a label (`ask-dont-guess`), so the same kind of email is decided alone next time.
7. **Label** `OfficerCan/<category>` and **route** by `action` (the Inbox Clerk's table). Pass the thread id and category along.
8. **Log** one row per thread to `ops/runs.jsonl`: time, thread, category, confidence, action.

## Watch-outs
- Auto-replies and "noted, thanks" aren't answers. They're `fyi_update`, not a reply to what we asked.
- Meeting invites carry the time only in the calendar attachment, not the body. Read it from there if you need it, and don't draft replies to invites.
- A thread that moved since the last sort gets re-sorted on its newest message only.
- To add a category, edit `categories.yaml`. The model reads the `recognize` text; no retraining needed.
