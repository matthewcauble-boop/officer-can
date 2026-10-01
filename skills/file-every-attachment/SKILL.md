---
name: file-every-attachment
description: Save each email attachment to files/Quality or files/Finance under a consistent name, classified by document type and counterparty, and commit it. File Clerk skill. Use for "file the attachments", "save this COA", or any documents_received / billing email.
---
# File Every Attachment

## Steps
1. **Download** every attachment on the newest message(s) (skip inline signature images under 20 KB, like logos and social icons).
2. **Classify the type** from the filename plus the first page's text (`pdftotext -l 1`, python-docx, openpyxl). Ask the model to pick one of: `coa, spec_sheet, sds, allergen_statement, certificate, audit_report, questionnaire, blank_form, filled_form, label, invoice, proforma, account_statement, payment_instructions, purchase_order, quote, contract, other`, with a confidence. Financial types set `area: financial`; everything else is `quality`. Not sure → queue a question with the top two types and file under `files/manual-review/` until answered.
3. **Counterparty** = the sender's company, slugged (`acme-ingredients`). Use the known slug if the domain is already in `files/index.csv`. For a supplier's manufacturer (a COA printed by a different plant), file under the supplier you buy from and note the manufacturer in the index.
4. **Name:** `<YYYY-MM-DD>-<counterparty>-<doc-type>-<ref>.<ext>`
   - date = date printed on the document, else the email date
   - ref = lot, invoice, PO, or certificate number if visible, else a short product word
   - e.g. `2026-09-18-acme-ingredients-coa-lot2291.pdf`, `2026-09-21-acme-ingredients-invoice-INV30267.pdf`
5. **Path:** `files/<Quality|Finance>/<counterparty>/<doc-type>/<name>`. Financial types (invoice, account_statement, payment_instructions, purchase_order, quote, contract) **always** go to `files/Finance/`.
6. **Never overwrite:** if the name exists and the bytes differ, add `-v2`. If they're identical, skip it. A resend of a whole package can reuse the vendor's old filenames, so check before writing.
7. **Index** the file (`index-and-expiry`), then commit with a message like `file: 2 docs from acme-ingredients (coa, spec_sheet)`.
8. **Tell the Compliance Chaser** which checklist items this might close.

## Rules
- The Quality tree may be mirrored to a shared drive for partners (co-packers, auditors). Nothing financial may land there. If in doubt, it goes in Finance.
- Keep the original filename in the index `source_name` column. Suppliers refer to it.
