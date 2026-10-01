---
name: encrypted-company-docs
description: Get a company's facts in once so every vendor form fills itself — public facts in plain YAML, sensitive values and documents (EIN, tax IDs, bank details, W-9, EIN letter, insurance certificate) encrypted with age, entered by the owner, never through chat. Vault Keeper skill. Use for "set up my company info", "store our W-9", "add our bank details", "import our old forms".
---
# Encrypted Company Docs

Public facts go in `config/company-profile.yaml`. Sensitive values go in `config/secrets.yaml.age` and documents in `config/docs/*.age`, encrypted with [age](https://age-encryption.org). The key lives at `~/.config/officer-can/age.key` (mode 600), outside the repo. The repo only ever holds ciphertext. `templates/config/secrets.example.yaml` shows the shape of the decrypted file.

## The tool
The vault is built into the form filler that ships with `vendor-forms` (`scripts/formfill.py`, set up as `$FF` there). It creates the key on first use (never overwrites one) and:
- `$FF remember-fact <key>`: the owner types a sensitive value at a **hidden prompt**; it's encrypted on save. `--release auto|approve|never` sets its rule. It refuses values on the command line.
- `$FF keys`: every key with `on_file: true/false`. Never values.
- `$FF store-doc <name> <file>` / `$FF docs` / `$FF open-doc <name> <tmpdir>`: encrypt a document in, list documents, decrypt one to a temp folder **outside** the repo (it refuses a folder inside it).
- `$FF rotate`: see `release-rules-and-audit`.

## First-time setup (in this order)
1. **Import what they've already filled.** Ask for 2–5 vendor forms they've sent before (new-customer forms, credit applications, setup workbooks). For each: `$FF import <form>` lists the filled slots (labels only), you map each label to a key, then `$FF import <form> --plan plan.json` copies the values in code: public keys to `company-profile.yaml`, sensitive keys straight into the vault, without any value passing through the model or chat. Import the newest form last so its values win, and tell the user where forms disagreed. Report back in one or two lines: "Found 24 items across 5 forms; 3 to check."
2. **The owner fills the gaps themselves** with `$FF remember-fact <key>` (hidden prompt). Tell them which keys are missing (`$FF keys`); they type the values. Hidden prompts need a real terminal, so the agent can't type there: give the user the exact command to run in their own terminal window, and wait for them to say it's done.
3. **Documents:** `$FF store-doc w9 <W-9.pdf>`, likewise `ein_letter`, `incorporation`, `resale_certificate`, `certificate_of_insurance`. Then delete the plaintext copies if they sit inside the repo.
4. **Backup:** remind them once to save the age key in their password manager. Without it the vault can't be opened.

## Rules
- **Never ask for or accept a sensitive value in chat** (EIN, tax IDs, bank details, SSN, date of birth). If the user pastes one anyway, don't repeat it back or write it anywhere. Point them to the hidden prompt and suggest they delete the message.
- Never print, log or commit a decrypted value or document. To check that something is on file, use `$FF keys` or `$FF docs`.
- Never commit, print or delete the age key.
- Bank details never come from an email. Only the owner enters them.

## Later
- A form asks something new ("fax number?"): ask once, save it (public → profile, sensitive → vault), and every later form fills it.
- Someone leaves, or a laptop is lost: rotate the key (`release-rules-and-audit`).
