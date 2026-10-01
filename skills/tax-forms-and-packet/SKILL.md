---
name: tax-forms-and-packet
description: Send the company's standard paperwork — W-9, EIN letter, incorporation documents, resale/tax-exemption certificate, certificate of insurance — decrypted just-in-time from the encrypted vault and attached to a threaded reply, following each document's release rule. Form Filler skill.
---
# Tax Forms and Company Packet

## When
"Please send your W-9", "we need your resale certificate", "send company docs to set you up", or a vendor form that asks for attachments.

## Steps
1. **Pick documents** by what was asked. Default to `standard_packet` in `company-profile.yaml` (usually `w9, ein_letter, incorporation`). Resale certificates are per-vendor in many states. If the request names a state or vendor and there's no certificate for it, ask the user.
2. **Check each release rule** (`$FF docs` lists documents and their rules; `$FF` is set up in `vendor-forms`):
   - `auto`: attach.
   - `approve`: ask the user by name ("Attach the certificate of insurance for Acme?"), then attach.
   - `never`: don't attach. Say in one line that it's available on request (financial statements, for example).
3. **Decrypt to a temp dir outside the repo**, attach, then delete:
   ```
   d=$(mktemp -d) && $FF open-doc w9 "$d" --recipient <their email>   # prints the path, never the contents
   # add --approved for an ask-each-time document once the owner has said yes
   # attach that path to the reply draft (threaded-replies), then:
   rm -rf "$d"
   ```
4. **Audit:** `open-doc` logs each release to `ops/audit.jsonl` (document name, recipient, rule; never the contents).
5. **Hand off** to the Negotiator for a threaded reply: two or three lines, with the documents attached.

## Rules
- Never commit, file or upload a decrypted document. The temp dir is deleted in the same step.
- Large attachments: if the mail tool can't inline a file, use a server-side attach method that keeps threading (see `threaded-replies`). Never rebuild the draft as a new thread.
