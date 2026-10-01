---
name: budgets-and-kill-switches
description: Track monthly spend per line item (model APIs, n8n, hosting), alert at 80% of budget, watch execution quotas, and operate the switches that stop spending or auto-sending immediately. Cost Manager skill. Use for "cap spend", "what did this cost this month", "stop auto-send".
---
# Budgets and Kill Switches

## Budgets: `ops/budgets.yaml`
```yaml
month_usd:
  claude_drafting: 20
  classifier: 5           # the model that sorts mail and maps form fields
  n8n: 0                  # self-hosted; set your plan price if hosted
  hosting: 10
quotas:
  n8n_executions_month: 0   # hosted plan limit; 0 = unlimited (self-hosted)
```

## Tracking: `ops/costs.jsonl`
Append a row per source per day: `{"date","item","usd","units","source"}`, where `source` is where the number came from (API usage endpoint, invoice, or tokens × price). Model calls log their usage in `ops/runs.jsonl`. Roll those up daily.

## Check (inside every sweep)
- Month-to-date vs budget per item. At **80%**, tell the user once, with the trend and the biggest driver. At **100%**, apply that item's switch and tell them.
- Hosted execution quotas: warn at 80%. Running out silently stops triage, so treat 100% as an outage and say so plainly.
- A daily spend more than 3× the trailing average is a runaway (a loop, a retry storm). Switch it off first, then investigate.

## Kill switches (these work without approval; turning back ON needs the user)
| switch | how | effect |
|---|---|---|
| Auto-send off | `AUTO_SEND_ENABLED=false` in the scheduler's environment (+ `autonomy.auto_send_enabled: false`) | every reply becomes a draft |
| Cheaper model | point the classifier at the smaller model in config | costs drop, more questions for the user |
| Drafting off | disable the drafting step (a config flag the job reads on every run) | triage + labels continue, no drafts |
| Everything off | disable the scheduled job / workflow | nothing runs, and mail waits safely in the inbox |
Build each switch during setup and test it once with the user watching. Log every switch change to `ops/runs.jsonl` with the reason.
