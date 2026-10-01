---
name: release-rules-and-audit
description: Decide and enforce which sensitive values and documents can be released automatically, only with approval, or never; answer "who have we sent X to" from the audit log; rotate the encryption key. Vault Keeper skill.
---
# Release Rules and Audit Log

## Rules per item
| rule (what the owner sees) | meaning | defaults |
|---|---|---|
| `auto` (Fill freely) | filled/attached without asking | EIN, resale/sales-tax ID, DUNS, W-9, EIN letter, incorporation docs |
| `approve` (Ask me each time) | only after the owner names this item for this form | bank name/address/account/routing, insurance certificate, bank letter, date of birth |
| `never` (Never share) | never filled or attached, whatever a form asks | SSN, signature image, financial statements, trade references |

The owner sets the rules when entering values (`encrypted-company-docs`). Only change one yourself when the owner asks.

## Enforcement is code, not instructions
The form filler (`vendor-forms`) reads the vault and refuses `approve` items unless they're named in `--approve`, and never fills `never` items. Items with no rule default to `approve`. Documents follow the same rules in `open-doc` (`--approved` for ask-each-time). Its test (`scripts/test_formfill.py`) proves both.

## Who got what
Each release is a row in `ops/audit.jsonl` (time, form, recipient, item name, rule). Values are never logged. Anything the owner doesn't recognize is a possible leak. Say so plainly.

## Key rotation (yearly, or when a laptop or person leaves)
`$FF rotate` creates a new age key, re-encrypts the vault and every document, and keeps the old key as `age.key.old`. Check that `$FF keys` and `$FF open-doc` still work. Delete that file only after the owner confirms everything opens, and after they've replaced the recovery key in their password manager.
