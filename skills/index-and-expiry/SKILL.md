---
name: index-and-expiry
description: Maintain files/index.csv (one row per filed document, with expiry dates read off certificates) and warn 30 days before a certificate, audit or insurance document expires. File Clerk skill. Use for "what do we have from X", "where's the COA for lot Y", "what expires soon".
---
# Index and Expiry Watch

## `files/index.csv` columns
`filed_at, doc_date, counterparty, doc_type, area, ref, path, source_name, thread_id, sender, expires, manufacturer, notes`

## Adding a row
- One row per filed file, written in the same commit as the file.
- **Expiry:** for `certificate`, `audit_report`, and insurance documents, find the expiry on page 1 ("valid until", "expiration date", "expires", "certificate valid through"). Write it as `YYYY-MM-DD`. If there are two dates and it's unclear which one, leave it blank and queue a question. Never guess an expiry.

## Answering questions
- "What do we have from Acme?": filter by counterparty and group by doc_type, newest first.
- "COA for lot 2291?": match `ref`. If there's no hit, search `source_name` and notes. Say plainly when it isn't on file.

## Expiry sweep (run inside `twice-daily-sweep`)
- Anything expiring within 30 days: tell the Chief of Staff with the counterparty and document, and suggest a chase (`chase-until-complete`) for the renewed copy.
- Already expired and still the latest of its kind for that counterparty: flag it, because a partner may reject it.
- A renewed copy supersedes the old row. Keep both rows and add `superseded_by` in notes.
