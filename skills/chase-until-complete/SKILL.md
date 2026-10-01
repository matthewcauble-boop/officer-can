---
name: chase-until-complete
description: Draft short, polite chase emails for open checklist items on a fixed cadence, and escalate to the user when a supplier goes quiet. Compliance Chaser skill. Use for "chase the missing docs", "who still owes us what".
---
# Chase Until Complete

## Cadence
- First ask: when the item is created (`status: requested`).
- Chase: 5 business days after the last ask with no reply, and at most one chase per counterparty per 5 business days, covering **all** their open items in one email.
- After 2 unanswered chases: stop drafting and hand it to the user with a one-line summary ("Acme: 3 docs open since 9/18, two chases unanswered. Call Ana?").

## The chase email
- Reply **in the existing thread** where it was asked (`threaded-replies`). Don't start a new one.
- Three to five lines, friendly, specific:
  > Hi Ana, just following up on the remaining docs for the pea protein: the COA for lot 2291 and the allergen statement. Could you send those when you get a chance? Thanks!
- Name each missing item exactly as on the checklist. If something they sent was wrong, say what: "the COA we received is for lot 2280; we need lot 2291."
- No pressure tactics, no deadlines unless the user supplied one, and no mention of other suppliers.
- Draft only. The user sends, unless they've said to send chases automatically.

## Bookkeeping
Append the chase date to each item's `chases`, and log the draft id in `ops/runs.jsonl`. When a reply arrives, the Inbox Clerk routes it. Attachments go to the File Clerk, and the checklist updates from there.
