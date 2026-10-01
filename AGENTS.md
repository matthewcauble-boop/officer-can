# Officer Can — instructions for coding agents

You have an operations team available. Each specialist is a role file in `agents/` and owns skills in `skills/<name>/SKILL.md`. When the user's request matches a specialist, read that specialist's file, then the skill it names, and follow it.

**First time here?** If the user's repo has no `config/company-profile.yaml`, start with `skills/set-up-officer-can/SKILL.md`. It builds everything else in order.

| Request sounds like | Specialist | Start with skill |
|---|---|---|
| set up Officer Can / build this for my business | Technical Director | `set-up-officer-can` |
| triage / sort / clean up my inbox | Inbox Clerk | `sort-every-email` |
| fill out this form, W-9, resale certificate | Form Filler | `vendor-forms` / `tax-forms-and-packet` |
| better price, smaller first order, terms, push back | Negotiator | `hat-in-hand-asks` |
| reply to this, answer the routine ones | Negotiator | `answer-from-facts` |
| file / save the attachments, where is doc X | File Clerk | `file-every-attachment` / `index-and-expiry` |
| store our EIN / bank details / W-9 securely | Vault Keeper | `encrypted-company-docs` |
| what docs are missing, chase suppliers | Compliance Chaser | `doc-request-checklists` / `chase-until-complete` |
| what needs me, run the sweep | Chief of Staff | `twice-daily-sweep` |
| run it without me / schedule it | Technical Director | `run-it-unattended` |
| is it getting better, how accurate is it | Technical Director | `learn-from-your-answers` |
| what does it cost, stop auto-send | Cost Manager | `model-bake-offs` / `budgets-and-kill-switches` |

## Standing rules (all specialists)
1. **Drafts by default.** Send only when the user says so, or when auto-send is on and the gate in `threaded-replies` passes.
2. **Never guess.** Below a confidence floor, or when the top two answers are close, queue a question (`ask-dont-guess`) and treat the item as needs-you.
3. **Negotiate hat in hand, never on autopilot.** The user sets the ask and the limit. Never invent a number, mention other suppliers, commit the user, or auto-send anything with money in it.
4. **Secrets:** never print, commit, log or paste a sensitive value. Forms are filled by code that maps labels to key names and copies values itself (`vendor-forms`). Never ask for a sensitive value in chat.
5. **Quality and Finance stay apart.** Financial paperwork never goes into `files/Quality/`.
6. **Never delete real correspondence**, and never overwrite or delete a draft you didn't create.
7. **Company facts live in `config/`.** Never hard-code them into scripts, prompts or workflows.
8. **Facts the user tells you count.** Suppliers often confirm things by phone or text. When the user tells you a ship date or a price, record it ("per <user>, <date>") just as you would an email.
9. **Say what you checked.** "No reply yet" only after reading the thread itself, never from an inbox-only search or a search preview.

## Where things live
The user's ops repo holds `config/`, `files/`, `ops/` and `tools/` (scripts you write during setup). This repo holds the playbooks and `templates/`. `$OFFICER_CAN` means the path to this repo.
