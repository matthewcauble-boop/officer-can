# Officer Can

**An operations team for your coding agent.** Give Claude Code, Codex or any coding agent these playbooks and it builds and runs the paperwork side of a small product business: sort the inbox, fill vendor forms, file every attachment, chase missing documents, negotiate with suppliers, and tell you twice a day what actually needs you.

There's no app to install and no service to sign up for. It's 9 specialists and 20 skills written as plain markdown, plus config templates. Your agent reads them, interviews you, and builds the system in your own private repo with your own mail connection.

Built by [Wonderade](https://wonderade.us), a kids' juice brand, to run its own supplier inbox: a co-packer, dozens of ingredient suppliers, QA paperwork, POs and all. Everything here comes from running that inbox for real.

## Start

```
git clone https://github.com/matthewcauble-boop/officer-can
```

**Claude Code:** open your ops repo (a new private repo is fine) and add this one as a plugin marketplace, then install `officer-can`:
```
/plugin marketplace add matthewcauble-boop/officer-can
/plugin install officer-can@officer-can
```
Or copy `agents/` and `skills/` into your project's `.claude/`.

**Codex, Cursor, Gemini CLI and others:** point the agent at `AGENTS.md`. Every skill is a plain-markdown playbook in `skills/<name>/SKILL.md`.

Then say: **"Set up Officer Can for my business."** The agent follows `skills/set-up-officer-can`: it asks about your company, writes your config, connects your mail, and turns things on one at a time, in dry-run first.

You'll need a mail connector your agent can use (a Gmail MCP server or the Gmail connector in Claude, or IMAP for other providers).

## The team

```
📁 Officer Can
│
├─ 📁 Inbox Clerk ────────── Sort Every Email · Archive the Noise
├─ 📁 Form Filler ────────── Fill Any Form, Remember Everything · Tax Forms and Company Packet
├─ 📁 Negotiator ─────────── Hat-in-Hand Asks · Answer From the Facts · Replies That Stay in Thread
├─ 📁 File Clerk ─────────── File Every Attachment · Index and Expiry Watch
├─ 📁 Vault Keeper ───────── Encrypted Company Docs · Release Rules and Audit Log
├─ 📁 Compliance Chaser ──── Document Request Checklists · Chase Until Complete
├─ 📁 Chief of Staff ─────── Ask, Don't Guess · Twice-Daily Sweep
├─ 📁 Technical Director ─── Set Up Officer Can · Run It Unattended · Learn From Your Answers
└─ 📁 Cost Manager ───────── Model Bake-Offs · Budgets and Kill Switches
```

| Specialist | Agent file | Skills |
|---|---|---|
| Inbox Clerk | `agents/inbox-clerk.md` | `sort-every-email`, `archive-the-noise` |
| Form Filler | `agents/form-filler.md` | `vendor-forms`, `tax-forms-and-packet` |
| Negotiator | `agents/negotiator.md` | `hat-in-hand-asks`, `answer-from-facts`, `threaded-replies` |
| File Clerk | `agents/file-clerk.md` | `file-every-attachment`, `index-and-expiry` |
| Vault Keeper | `agents/vault-keeper.md` | `encrypted-company-docs`, `release-rules-and-audit` |
| Compliance Chaser | `agents/compliance-chaser.md` | `doc-request-checklists`, `chase-until-complete` |
| Chief of Staff | `agents/chief-of-staff.md` | `ask-dont-guess`, `twice-daily-sweep` |
| Technical Director | `agents/technical-director.md` | `set-up-officer-can`, `run-it-unattended`, `learn-from-your-answers` |
| Cost Manager | `agents/cost-manager.md` | `model-bake-offs`, `budgets-and-kill-switches` |

## A form filler that remembers, included

The one piece that ships as code: [`skills/vendor-forms`](skills/vendor-forms). Drop in a blank vendor form (.docx, fillable or flat PDF, .xlsx) and your agent maps each blank to one of your facts; a small script copies the values in and remembers every answer, so the next form from anyone fills itself. Your EIN and bank details sit in an encrypted vault that you type into yourself, and the script never prints them. It also stores your W-9 and other documents encrypted and hands them out by your rules. No app, no account, no service.

```
pip install -r skills/vendor-forms/scripts/requirements.txt
python skills/vendor-forms/scripts/test_formfill.py      # fills sample Word, Excel and PDF forms for a made-up company
```

## What it will and won't do

- **Drafts, not sends.** Every reply is a draft you send yourself, unless you turn on auto-send for routine replies, and even then a gate in code blocks anything with money, a commitment or a price in it.
- **It asks instead of guessing.** Anything it isn't sure of becomes a one-line multiple-choice question in chat. Your answer is remembered, so the same question never comes twice.
- **No model sees a secret.** Forms are filled by mapping each *label* to a key name. Code copies the *value* from your encrypted vault. Bank details wait for your OK; signatures and SSNs are never filled; every release is logged.
- **Negotiates hat in hand.** Warm, short, questions before positions, something real offered in return, never a mention of other suppliers. You set the ask and the limit, and every number comes from you or a quote on file. Negotiation drafts are never auto-sent.
- **Quality and Finance stay apart.** Specs, COAs and certificates go in a tree you can share with a co-packer or auditor; invoices, quotes and payment instructions never do.
- **No digest emails.** It reports in chat, leads with what needs you, and says "nothing needs you" when that's true.

## Your ops repo after setup

```
config/   company-profile.yaml · categories.yaml · field-keys.yaml · secrets.yaml.age · docs/*.age
files/    Quality/<counterparty>/<doc-type>/…   Finance/<counterparty>/<doc-type>/…   manual-review/   index.csv
ops/      watch.md · questions.jsonl · labels.jsonl · audit.jsonl · runs.jsonl · costs.jsonl · budgets.yaml · checklists/
tools/    the small scripts your agent writes during setup (sweep runner, scheduled jobs)
```

Starting points for `config/` are in [`templates/config/`](templates/config). `examples/sample-inbox.jsonl` is a made-up inbox for a dry run.

## Lessons baked in

Each of these cost a real week somewhere:
- Gmail search `newer_than:35m` means 35 **months**. Use `after:<epoch seconds>`.
- Search results often show only the oldest messages of a thread. Read the newest message before deciding anything.
- Editing a draft to add an attachment can silently drop the attachment and break the thread. Delete and recreate instead.
- A drafting model will turn "the wire goes out tomorrow" in the thread into "the wire went out". Guard money and commitments in code, not just in the prompt.
- Keyword rules ("audit", "term sheet") fire on sales pitches and newsletters too. Scope them by category.
- GitHub Actions `schedule` is not a clock. Runs arrive hours late or not at all on a busy repo. Anything that must run every few minutes needs a real scheduler.
- A hosted automation plan that runs out of executions stops triage without telling anyone. Watch quotas like a budget.

## License

MIT. Use it, change it, sell what you build with it.
