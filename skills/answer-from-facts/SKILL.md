---
name: answer-from-facts
description: Draft a short reply to a routine request using only what's on file in company-profile.yaml (facts, contacts, standard_packet); anything not on file becomes a question for the user instead of a guess. Negotiator skill.
---
# Answer From the Facts Sheet

## Steps
1. **Read the whole thread**, newest message last. Write down each thing they asked, one line each.
2. **Look each ask up** in `company-profile.yaml`: `facts` (shipping account, receiving addresses and hours, COA email, payment terms, certifications on file), `contacts`, `company`, `standard_packet`, and `files/index.csv` for documents on file.
3. **Sort the asks:**
   - All answered from file: draft the reply.
   - Some answered: draft what's on file, and add each gap to `ops/questions.jsonl` (`{"kind":"reply_gap","thread":...,"ask":"<their question>"}`). Hold the draft until the user answers. Don't send half an answer.
   - Price, quantity, lead time, payment terms or a quality problem: that's a negotiation. Switch to `hat-in-hand-asks`.
   - Legal, investor or contract matters: don't draft. Label `OfficerCan/NeedsYou` with a one-line summary.
4. **Write like the owner.** Copy the length and tone of `mailbox.voice_sample`: greeting, two to five sentences, sign-off. No markdown, no bullet lists, no "I hope this finds you well". State facts plainly ("Receiving is Mon–Fri 8–4, appointment only").
5. **Attach** documents they asked for that are on file (`files/Quality/...`, or the packet via `tax-forms-and-packet`).
6. **Save as a threaded draft** (`threaded-replies`) with the `mailbox.cc_on_every_reply` addresses cc'd.

## Never
- Invent a fact, date, lot number or document.
- Confirm we "have" something unless it's in `files/index.csv`.
- Apologize for delays we didn't cause, or promise follow-ups on the user's behalf.
