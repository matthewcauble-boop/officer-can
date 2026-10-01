---
name: model-bake-offs
description: Run the same private labeled set through each candidate model (a small or local model, a hosted classifier, a larger LLM) and compare accuracy, coverage at the confidence floor, latency, and cost per 1,000 decisions. Cost Manager skill. Use for "which model should we use", "is the bigger model worth it", "what does this cost".
---
# Model Bake-Offs With Cost

## Run
Write `tools/bakeoff.py` once: it reads the user-labeled rows from `ops/labels.jsonl` (spot checks and corrections, not automatic labels), sends each one to every candidate with **the same prompt and the same categories**, and records answer, confidence, latency and tokens. Rules (`archive-the-noise`) run first for every candidate, so it's like for like. Prices come from each provider's current price page. Note the date you read it.

**Before sending the eval set to any hosted backend, get the user's explicit OK.** It's their real mail. With no OK, compare on a synthetic or redacted set, and say so in the results.

## Read the results
| column | meaning |
|---|---|
| `accuracy` | right answers / all items (the model forced to answer everything) |
| `coverage_at_floor` | share of items it's confident enough to decide alone |
| `accuracy_at_floor` | how often it's right on those. **This is the safety number.** |
| `latency_ms_median` | per decision |
| `usd_per_1000_decisions` | from reported tokens × price |

## Decide
1. Drop any backend whose `accuracy_at_floor` is under the bar (97–99%).
2. Of the rest, prefer the one that gives the most coverage per dollar. Everything it doesn't cover goes to the next tier (another backend, then the user).
3. A cascade often wins: local model first (free), a hosted model only for what local isn't sure about, and the user last. Estimate the blended cost from each tier's coverage.
4. Write the recommendation with the numbers and date into `ops/watch.md` or a short report, and re-run monthly or whenever categories change.
