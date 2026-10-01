---
name: set-up-officer-can
description: First-run builder. Interviews the user about their business, writes their config from the templates, connects their mail, and turns on each specialist one at a time — dry run first, then live, drafts only. Technical Director skill. Use for "set up Officer Can", "build this for my business", or whenever the user's repo has no config/company-profile.yaml.
---
# Set Up Officer Can

You are building a working ops system in the **user's own private repo** (call it the ops repo). This repo only holds the playbooks. Go phase by phase. Finish and show each phase before starting the next, and never skip the dry runs.

## Phase 0 — Check the ground (5 minutes)
1. Confirm the ops repo is **private**. Company facts, labels and filed documents will live there. If it's public, stop and say so.
2. Find the mail tool you have: a Gmail MCP server / Gmail connector, or IMAP. List what it can do: search, read a thread, list drafts, create a reply draft, apply labels, download attachments. Note anything missing. A tool that can't create **reply** drafts (threaded) limits you to labeling until it's fixed.
3. Create the folders: `config/ files/Quality files/Finance files/manual-review ops/checklists tools/`. Add `.gitignore` entries for `*.key`, `secrets.yaml`, `.env`.

## Phase 1 — Interview and config (15 minutes)
Copy `templates/config/*` into `config/`. Then ask, a few questions at a time:
- Legal name, address, phone, website, entity type, year founded. → `company-profile.yaml` `company`
- Who should drafts sound like? Ask for 3–5 short emails they've sent to suppliers. → `mailbox.voice_sample`
- Addresses to cc on every reply (often a finance inbox). → `mailbox.cc_on_every_reply`
- Facts suppliers keep asking for: receiving address and hours, shipping account, COA email, payment terms, certifications on file. → `facts`
- What kinds of email they get. Walk through `categories.yaml` together; rename, drop or add categories in their words. The `recognize` text is what the model reads, so make it plain.

**Never ask for EIN, tax IDs or bank details in chat.** Those go through the vault in Phase 5.

Show the finished `company-profile.yaml` and ask for corrections. Commit.

## Phase 2 — Sort the inbox, dry run (Inbox Clerk)
Follow `sort-every-email` and `archive-the-noise` against the last ~100 threads **without labeling anything**. Show a table: sender, subject, category, confidence, action, and whether it was sure. Ask the user to correct the misses (`ask-dont-guess`). Save every correction to `ops/labels.jsonl`.

When the misses are rare, create the labels (`OfficerCan/<category>`, `OfficerCan/NeedsYou`, `OfficerCan/Archive`) and run it live on new mail. Labels only. No drafts yet.

## Phase 3 — Drafts (Negotiator)
Turn on `answer-from-facts` and `threaded-replies` for routine requests. Before going live:
- Replay 10 past emails that needed replies and show the drafts side by side with what the user actually sent. Fix the voice from the differences.
- Build the guards **in code**, not just the prompt: no draft that states something happened unless it's on file; any draft that mentions a payment, wire, invoice, price or commitment is not created and the thread goes to `NeedsYou`; long digit runs (account numbers) are stripped; a draft never says what the user thinks or where they'll be. Put placeholders like `[YOU: your call on the sample]` where only the user can answer.
- Auto-send stays **off**. Leave `autonomy.auto_send_enabled: false`.

## Phase 4 — Filing (File Clerk)
Turn on `file-every-attachment` and `index-and-expiry`. Dry run on the last 30 emails with attachments: show where each file would go and its name. Then live. Confirm with the user before anything is mirrored to a shared drive, and check the mirror only ever receives `files/Quality/`.

## Phase 5 — Vault and forms (Vault Keeper, Form Filler)
Install the form filler that ships with `vendor-forms` (`pip install -r skills/vendor-forms/scripts/requirements.txt`) and run its test once. Then:
1. Ask for 2–5 vendor forms the user already filled. Import facts from them (`encrypted-company-docs`).
2. Have the user enter sensitive values themselves at the hidden prompt (`remember-fact`) and store their W-9 and other documents (`store-doc`). Never through chat.
3. Fill one real blank form as a test and show the report (labels → key names, never values) before anything goes in a draft.

## Phase 6 — Chasing and the sweep (Compliance Chaser, Chief of Staff)
Set up `doc-request-checklists`, `chase-until-complete` and `twice-daily-sweep`. Write the first `ops/watch.md` with the user: what's open with whom, and what they're waiting on.

## Phase 7 — Run it unattended (Technical Director, Cost Manager)
Follow `run-it-unattended` to schedule triage and the sweep, and `budgets-and-kill-switches` to set budgets and test every kill switch once.

## At the end
Write `ops/SETUP-NOTES.md`: what's on, what's off, where each script lives, the schedule, the budgets, and every decision the user made. Tell the user in three lines what now runs on its own, what still waits for them, and how to turn it all off.

## Rules during setup
- One phase at a time, shown and approved.
- Dry runs never label, draft, send, file or move anything.
- If a tool is missing (no reply drafts, no attachment download), say so plainly and suggest the fix. Don't fake it with something that breaks threading.
