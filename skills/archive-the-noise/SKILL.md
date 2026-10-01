---
name: archive-the-noise
description: Deterministic rules that settle the obvious mail before any model call — newsletters, receipts, out-of-office replies, calendar invites, emoji reactions, security alerts — plus mail filters so the noise never reaches the inbox. Inbox Clerk skill.
---
# Archive the Noise

About one email in five needs no model at all. Write these rules as a small function in `tools/` (`classify(sender, subject, text, headers) -> category or None`) and run it before anything else.

| Pattern | Category | Action |
|---|---|---|
| `List-Unsubscribe` header, bulk-sender addresses (`newsletter@`, `mail.*`, `@substack.com`, `@beehiiv.com`…) | `newsletter` | ARCHIVE |
| `Auto-Submitted` header, "out of office", "automatic reply" | `fyi_update` | LABEL_ONLY |
| Subjects starting "Invitation:", "Accepted:", "Updated invitation:", "Canceled event:", or a `text/calendar` part | `scheduling` | LABEL_ONLY |
| Reactions ("reacted to your message"), message recalls | `fyi_update` | LABEL_ONLY |
| New sign-in, unrecognized device, verification codes | `system_alert` | LABEL_ONLY, keep in inbox |
| Receipts from the user's own payment processor and SaaS tools | `transactional` | ARCHIVE |

## Mail filters (set once, with the user's OK)
Offer to create filters for senders the user never needs to see: receipts, SaaS notifications, newsletters. Filter → label `OfficerCan/Archive`, skip inbox. List the exact senders and ask before creating. Filters are hard to spot later.

## Rules
- Rules only ever **label or archive**. They never draft, send or delete.
- `system_alert` stays in the inbox. Security notices must be seen.
- A newsletter that mentions "term sheet" or "due diligence" is still a newsletter. Bulk-mail signals beat keyword overrides.
- If a rule fires on something the user later says was real mail, narrow or remove that pattern and note the correction in `ops/labels.jsonl`.
