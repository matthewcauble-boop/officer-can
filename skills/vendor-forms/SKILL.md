---
name: vendor-forms
description: Fill any blank form — vendor onboarding, credit application, customer-setup workbook, W-9 request — in .docx, PDF (fillable or flat) or .xlsx, from the company's facts, and remember every answer so each question is asked once, ever. Ships a working script; the agent decides what each blank means, the script copies values in code, and sensitive values never pass through the model. Form Filler skill. Use for "fill out this form", "remember our fax number", "import our old forms".
---
# Fill Any Form, Remember Everything

This skill ships a working filler: `scripts/formfill.py` (with `scripts/handlers/` for Word, PDF and Excel). There's no model inside it. **You** decide what each blank means; the script finds the blanks, copies the values in, enforces the sharing rules, and remembers.

```
pip install -r $OFFICER_CAN/skills/vendor-forms/scripts/requirements.txt
FF="python $OFFICER_CAN/skills/vendor-forms/scripts/formfill.py --config config --ops ops"
```
It reads `config/company-profile.yaml` and `config/field-keys.yaml` (start from `templates/config/`), keeps sensitive values in `config/secrets.yaml.age` (encrypted, key at `~/.config/officer-can/age.key`), and writes memory to `ops/labels.jsonl` and every release of a sensitive value to `ops/audit.jsonl`. **Nothing it prints ever contains a value**: only labels, sections, key names and statuses.

## Fill a form
1. **Save the blank** to `files/Quality/<counterparty>/blank_form/<date>-<counterparty>-blank_form-<name>.<ext>`.
2. **List the blanks:** `$FF blanks <form>`. Each blank has an `id`, its `label`, the `section` it sits under, and a `key`:
   - a key with `"why": "remembered"`: answered on an earlier form. Nothing to decide.
   - `SKIP…` keys: left blank on purpose (another company's section, signatures, SSNs, "if different from above").
   - `null`: **you decide.** Run `$FF keys` for the key names, descriptions and what's on file, and pick one per blank, or `SKIP`, or `NEEDS_HUMAN`. Decide from the label and section only. If two keys fit equally well, ask the user (`ask-dont-guess`) instead of guessing.
3. **Write `plan.json`** for the blanks you decided: `{"b3": "company.phone", "b7": "SKIP", "b9": "NEEDS_HUMAN"}`. For a one-off answer that shouldn't be remembered, use `{"b12": {"value": "PO 4471"}}`.
4. **Fill:** `$FF fill <form> files/Quality/<counterparty>/filled_form/<…> --plan plan.json --recipient <their email>`.
   Every decision in the plan is **remembered** (by label and section), so the next form from anyone fills it on its own. Add `--no-remember` for a one-off.
5. **Read the report** (`counts` and `fields`):
   - `filled`: done.
   - `held_for_approval`: a sensitive value whose rule is "ask me each time" (bank details by default). Ask the user by name; if they approve, re-run with `--approve bank.account_number,bank.routing_number`.
   - `missing`: we don't have it yet. Ask the user once and save it (below), then re-run.
   - `needs_you`: several delivery locations on file, a value that didn't land cleanly, or `NEEDS_HUMAN`. Ask, then re-run.
   - `undecided`: a blank you didn't put in the plan. Decide it and re-run.
   - `left_blank` / `never_release`: stays blank. Mention it only if the form requires it.
   - `"status": "manual_review"`: a scanned form with no readable blanks. File under `files/manual-review/` and tell the user.
6. **Check it:** open the filled file and confirm the filled blanks look right. Read labels and positions, not values aloud.
7. **Hand off** to the Negotiator: reply in the same thread with the filled form (plus the W-9 packet if asked, `tax-forms-and-packet`). Mention anything left for them (signature, references) in one line.

## Remember things
- **A fact:** `$FF remember-fact company.fax --value "(555) 555-0199"`. A key that isn't in `field-keys.yaml` yet needs `--describe "Fax number"`, and is added so later forms can match it.
- **A sensitive fact** (EIN, tax IDs, bank details, anything you'd rather not have in plain text): `$FF remember-fact tax.ein` — the **user types it at a hidden prompt**. Add `--secret` for a new sensitive key, `--release auto|approve|never` to set its rule. Never pass a sensitive value with `--value` (the script refuses), and never ask for one in chat. Hidden prompts need a real terminal, so the agent can't type there: give the user the exact command to run in their own terminal window, and wait for them to say it's done.
- **A meaning:** `$FF remember-field "Remit-to Email" contact.ap.email --section "Accounts Payable"`, when the user tells you what a label means.
- **From forms they already filled:** `$FF import <old form>` lists the filled slots (labels only); write a plan `{id: key}` and run `$FF import <old form> --plan plan.json`. Public values go to the profile, sensitive ones straight into the vault, in code. Good first step when setting up: 2–5 old forms plus their W-9.

## Rules it enforces in code
- Sharing rules per sensitive value: `auto` fills, `approve` waits for `--approve`, `never` stays blank. EIN, resale ID and DUNS default to `auto`; everything else sensitive defaults to `approve`.
- Signatures, SSNs, birth dates and credit-line requests are always left blank.
- Sections about another company (co-packer, broker, parent, trade references) are left blank. Ship-to / delivery sections get the delivery address, not head office.
- A repeated row (officer #2, contact #2) is left blank after the first.
- Spreadsheet formula cells are never overwritten. PDF labels are read off the page, not the field's hidden name.
- Every release of a sensitive value is logged (key name, form, recipient, rule; never the value).

## Test it
`python $OFFICER_CAN/skills/vendor-forms/scripts/test_formfill.py` builds Word, Excel and PDF forms for a made-up company and runs the whole loop.
