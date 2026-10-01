---
name: ask-dont-guess
description: Turn every uncertain decision (email category, form field, document type, reply gap, expiry date) into a short multiple-choice question for the user in chat, apply the answer, and save it as a label so it's never asked again. Chief of Staff skill.
---
# Ask, Don't Guess

Officer Can's accuracy promise isn't "the model is always right". It's "**it knows when it might be wrong, and asks**". Anything below its floor, or whose top two answers are close, becomes a question instead of an action.

## The queue: `ops/questions.jsonl`
Specialists append; you drain. Each row has `kind` (`email_category`, `form_field`, `doc_type`, `reply_gap`, `expiry`, `approval`), the item (thread id, form + label, file path), a one-line `summary`, and `options` (likeliest first).

## Asking
Some questions have `"why": "spot check"`: emails it already sorted on its own, asked anyway so accuracy can be measured honestly. Ask them the same way (don't reveal its guess as "the answer"), and pass the `why` through when saving.

1. Drop questions whose item was since resolved (the user acted on the thread, the file was refiled).
2. **Rank:** approvals and anything blocking a reply first, then form fields (they block a whole form), then categories and doc types.
3. **Batch:** at most 4 at a time. Use the chat's multiple-choice UI if there is one. Otherwise number them:
   > 1. Ana at Acme, "shortages for next run": question for you, or just an update? **[Question] [Update]**
   > 2. Acme new-customer form, field "Phone": **[Purchasing phone] [Main phone] [Leave blank]**
4. Only ask what changes an action. If both answers lead to the same action, don't ask; pick it and move on.

## Applying an answer
- Do what the answer implies: relabel and route the thread, re-run the form filler (with the approval for approvals), refile the document, or finish the held draft.
- Remove the row from `ops/questions.jsonl`.
- **Save a label** to `ops/labels.jsonl` right away, so it takes effect on the next decision, e.g. `{"kind":"form_field","label":"Phone","section":"Purchasing","key":"contact.purchasing.phone","source":"user","date":"..."}` or `{"kind":"email","sender":...,"subject":...,"text":...,"label":"supplier_question","why":"<the question's why>"}`. These become the user's private eval and training set (`learn-from-your-answers`).
- **Form-field memory:** before asking about a form label, check `ops/labels.jsonl` for the same label text. If the user already answered it, use their answer without asking.

## While waiting
Every queued item is `NEEDS_YOU`. No specialist drafts, files into a final folder, or sends on it.
