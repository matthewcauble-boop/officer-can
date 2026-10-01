---
name: learn-from-your-answers
description: Make the system better every week from the user's own answers — each answer used immediately as an example, confidence floors re-set from real accuracy, and an honest report of how often it's right when it decides alone. Technical Director skill. Use for "is it learning", "how accurate is it on my mail", "why does it keep asking about X".
---
# Learn From Your Answers

Every answer the user gives (`ask-dont-guess`) is a labeled example in `ops/labels.jsonl`. That file is the user's private eval and training set. It never leaves their repo.

## Every answer, immediately
- **Emails:** when sorting, include the most similar labeled emails (same sender domain first, then similar subject/body) as worked examples in the classifier prompt. A sender the user has labeled twice the same way is a strong hint.
- **Form fields:** before mapping a form label, look for the same label text (and section) in `ops/labels.jsonl`. If the user answered it before, use that answer and don't ask. Each field label is asked about once, ever.
- **Corrections** ("that wasn't a pitch, it was a supplier") are labels too. A correction to a rule (`archive-the-noise`) removes or narrows the rule.

## Spot checks
Now and then, ask about an email the system sorted on its own (`"why": "spot check"`), without revealing its guess. Those answers are the only fair measure of accuracy when it decides alone. Keep them marked.

## Nightly (or weekly while volume is low)
1. Re-score every user-labeled email with the current setup, each one leaving itself out of the examples.
2. For each category, set the confidence floor to the lowest value that keeps **99% right** among the ones above it. Don't move a floor until there are 30+ answers for it.
3. Append a dated entry to `ops/model/report.md`: answers so far, right-when-deciding-alone (from spot checks), share decided alone, floors, and what changed.

## Reading the report honestly
- Always give accuracy and coverage together, with the count: "right 97% of the time when it decides alone (spot checks, n=64), deciding 70% of mail".
- Never tune on the same answers you report on.
- Questions keep coming from one category? Usually its `recognize` text in `config/categories.yaml` is vague, or two categories overlap. Rewrite the descriptions with the user before reaching for a bigger model.

## Optional: a small local model
At a few hundred labels you can train a small classifier on them to cut cost and latency (see `model-bake-offs`). Keep it only if it beats the current setup on held-out answers, and treat it as a first pass that the larger model checks when unsure.
