---
name: threaded-replies
description: The one correct way to put a reply (with or without attachments) into the right email thread as a draft, and the policy gate that must pass before anything auto-sends. Negotiator skill.
---
# Replies That Stay in Thread

## Drafting
- Create the draft **as a reply to the newest message** (`replyToMessageId` or equivalent). The client then sets `threadId`, `In-Reply-To` and `References`. A new-message draft with a matching subject does **not** thread.
- **Never edit an existing draft to add attachments.** Many mail APIs rebuild the draft on update, which drops attachments and can sever the thread. Delete it and create a new one instead.
- Attachments: inline base64 works for small files (under ~15 KB is safe in most tool calls). For bigger files, use a server-side path that builds the reply from repo files (for example a GitHub Action or n8n node that reads the original message's headers and attaches by path). Confirm the attachment from that job's log, not by assumption.
- Files over 25 MB can't be attached. Share a link instead. If they arrived as download links (for example iCloud Mail Drop), forwarding the original email carries the links.
- Never overwrite or delete a draft you didn't create. The user may have started one.
- **Pick the recipient by role, not by who wrote last.** A billing contact can't answer an artwork or quality question. If the right person isn't on the thread, say so to the user and suggest who to address (or a new thread to them) instead of sending it to whoever is there.

## The send gate (only if `autonomy.auto_send_enabled: true`)
Send without asking only if **all** pass. Otherwise leave the draft and tell the user.
1. Existing thread, and the sender is a known contact (`existing_threads_only`, `known_senders_only`).
2. Not a negotiation draft (`hat-in-hand-asks` drafts never auto-send). No `$`, no amounts, no prices, and no commitment phrases ("we will", "confirm the order", "agree", "approve", "by <date>").
3. At most `max_sentences` sentences. Attachments only from the standard packet or `files/Quality/`.
4. Rate limits: `max_sends_per_hour`, `max_sends_per_day` (count from `ops/runs.jsonl`).
5. The thread isn't an FYI or shipment confirmation. Those need no reply at all.
6. Kill switch `AUTO_SEND_ENABLED` env var isn't `false`.
Log every send and every refusal (with the failed rule) to `ops/runs.jsonl`.

## When the user says "send"
Send the exact draft they approved, by draft id. Then read the sent message back and confirm its recipients and attachments.
