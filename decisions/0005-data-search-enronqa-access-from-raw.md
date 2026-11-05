# 0005: Data: search the EnronQA emails now, the full raw corpus later

- **Status:** accepted
- **Date:** 2026-11-06
- **Phase / component:** data decision / which emails are searched and who may see them
- **Builds on:** 0001 (project choice), 0004 (requirements)
- **Unblocks:** the access rule, the evaluation plan, the build script
- **Design doc sections updated:** §3 Data

## The decision needed
Which set of emails the assistant searches, and where the information about who holds each email comes from.

## Context
EnronQA gives 73,772 emails with questions and gold answers. The raw Kaggle corpus has 517,401 messages from the same 150 users (R1). Findings so far, all measured:
- Every EnronQA (user, path) key matches one raw message exactly, so the two can be joined (R3).
- EnronQA's body is the raw body plus a closing line, on a sample of 200 (R6).
- Message-IDs are all unique, so they cannot show who holds a copy (R2).
- The same body text sits with 2 or more users in 17,236 groups, and 5,252 of the 73,772 EnronQA emails (7.1%) have an exact copy with another user. This is a lower bound (R5).
- 443,629 raw messages from the same users are not in EnronQA (R3).

## What was studied first
Checks C1 to C4 and R1 to R6 in `docs/DATA_NOTES.md`.

## Estimates (if relevant)
Option C searches 517,401 / 73,772 = 7.0 times as many emails as option B. Memory and index size for that were not measured.

## Options considered
### Option A: EnronQA only
- What it is: search the 73,772 emails and treat each as held by its one `user`.
- Makes easy: no raw data needed after the first load.
- Makes hard later: it ignores that the same text sits in other mailboxes.
- How it fails: leakage would be 0 trivially, but for about 7.1% of the emails another real holder of the same text would be wrongly denied. The test would not be hard.

### Option B: search the 73,772 EnronQA emails; who holds a copy comes from the raw corpus
- What it is: the search pile stays small and has gold questions. For each email, the list of users who hold the same message is taken from the raw corpus.
- Makes easy: questions and answers exist, so retrieval can be measured. The access problem becomes real, because copies exist.
- Makes hard later: the pile is only 14.3% of the raw mail, so retrieval looks easier than on a full inbox.
- How it fails: the rule for what counts as the same message is not decided yet (see PROGRESS open question 0007), so holder lists can be too wide or too narrow.

### Option C: search the full raw corpus (517,401 messages)
- What it is: index everything.
- Makes easy: a realistic pile with many distractors.
- Makes hard later: there are no gold questions for the 443,629 extra messages, and it is 7.0 times bigger, with an unmeasured cost on this laptop.
- How it fails: too much to learn at once; the access problem gets buried under scale.

## How we would know it was wrong
If the holder lists from the raw corpus cannot be made consistent for the 73,772 emails, or if the measured leak rate on B cannot reach 0 for a reason that scale would not change.

## Claude's recommendation
Option B now, option C afterwards. Option A is rejected.

## Decision (Rex)
Option B now, then option C as a required step. Followed recommendation: yes.

## Why
Rex: "B now, then C as a MUST improvement... It's a learning process for me. We'll tackle one issue at a time... Right now, the biggest issue is to learn how to solve the access problem - who gets which emails and how do we implement it. Then we would move onto making our search pile bigger and scale our access solution to the bigger pile. Also, then tackle problems to make retrieval better."

In simple words: the hard and important part is deciding who may see which email, so that is learned first on a pile small enough to understand, using the real copy information from the raw corpus. Making the pile bigger, and then making search better, come after the access rule works.

## Dissent, if any
None.

## Consequences
- The access rule will use holder lists built from the raw corpus, so the raw Kaggle CSV stays an input, not just a probe.
- Option C is a required later step, not an optional one.
- Retrieval numbers on B are optimistic compared with a full inbox, and must be reported with that label.

## Revisit when
Leakage is measured as 0 on option B (then start option C), or the holder lists cannot be built consistently.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the next phase gate._
