---
name: doc-request-checklists
description: Turn a documentation request (a customer/co-packer/auditor email, an outstanding-documents spreadsheet, or our own RFQ) into a per-counterparty checklist in ops/checklists/, and tick items off as files arrive. Compliance Chaser skill.
---
# Document Request Checklists

## `ops/checklists/<counterparty>.yaml`
```yaml
counterparty: acme-ingredients
requested_by: partner-copacker        # who needs these (us, or a partner we're gathering for)
source: "email 2026-09-18 'Outstanding documents'"   # or spreadsheet path
items:
  - id: coa-lot2291
    need: "COA for lot 2291"
    product: "Pea protein 80%"
    status: open          # open | requested | received | done | not_applicable
    requested_on: 2026-09-18
    file: ""              # path in files/ once filed
    chases: []            # dates chased
```

## Building one
1. Read the request **exactly as written**. One item per document per product. If they list "spec, COA, allergen statement" for three products, that's nine items.
2. Scope rule: only what was requested. Don't add documents "they'll probably want".
3. Pre-tick from `files/index.csv`: if a current, unexpired document already matches, set `status: done` with the path, and say so in your reply.
4. Items we must produce ourselves (a signed questionnaire, a letter on our letterhead) get `owner: us` and go to the user or Form Filler.

## Keeping it current
- When the File Clerk files something from that counterparty, match it to open items by doc_type + product/lot, and set `received` → `done` once filed and indexed.
- A received document that's wrong (wrong lot, expired, unsigned) stays open with a note, and the chase says what's wrong.
- When every item is `done` or `not_applicable`, tell the user it's complete and offer to send the set to whoever asked.
