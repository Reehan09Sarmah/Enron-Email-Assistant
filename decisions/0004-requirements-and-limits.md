# 0004: Requirements and limits set now

- **Status:** accepted
- **Date:** 2026-11-06
- **Phase / component:** requirements / evaluation and cost limits
- **Builds on:** 0001 (project choice)
- **Unblocks:** 0005 (data), the evaluation plan, the choice of model
- **Design doc sections updated:** §2 Requirements, §6 Sizes and costs

## The decision needed
Which numbers the system must meet, which numbers wait until they can be measured, and how the free-tier Gemini limits shape the way we evaluate.

## Context
Fixed rule 3 already says leakage is measured and the target is zero. Nothing yet says how fast the system must be, how good retrieval must be, or how many model calls we can afford. Rex read the limits for his keys in AI Studio on 2026-11-06 (model names are as he read them, not checked by Claude):

| Model | Requests per minute | Tokens per minute | Requests per day |
|---|---|---|---|
| Gemini 2.5 Flash | 5 | 250K | 20 |
| Gemini 3 Flash | 5 | 250K | 20 |
| Gemini 3.6 Flash | 5 | 250K | 20 |
| Gemini 3.8 Flash | 5 | 250K | 20 |
| Gemini 3.5 Flash Lite | 15 | 250K | 500 |
| Gemma 4 26B | 30 | 16K | 14.4K |

## What was studied first
No study card. The limits above, and the API terms notes in `docs/DATA_NOTES.md`.

## Estimates (if relevant)
Answers need one model request per question (assumption). Running 150 questions then takes at least:
- one Flash model: 150 / 20 = 7.5 days, and 150 / 5 = 30 minutes of spacing;
- Flash Lite: 150 / 500 = 0.3 of one day, and 150 / 15 = 10 minutes;
- about 30 questions per iteration: 30 requests fit in one day on Flash Lite, but not on one 20-per-day Flash model.

Retrieval and leakage runs make no model calls, so these limits do not touch them.

## Options considered
### Option A: set every number now, including a recall target
- What it is: pick a Recall@10 figure today.
- Makes easy: a clear target.
- Makes hard later: the number would be a guess, because no baseline has been measured.
- How it fails: the target is too easy (looks good, proves little) or too hard (cannot be reached with honest tests).

### Option B: set leakage and latency now, defer recall until the baseline is measured
- What it is: leakage 0 in every test; search alone p95 at most 1 second; full answer p95 at most 12 seconds, measured on at least 150 questions on this laptop. Recall@10 is set later as "beat the keyword baseline on dev questions by a stated margin".
- Makes easy: every limit rests on a measured number, with no invented target.
- Makes hard later: recall has no goal until the baseline run exists.
- How it fails: the margin is picked after seeing results. Test questions are never used for tuning (rule 4).

### Option C: rotate freely between models and keys, also inside evaluation runs
- What it is: when one model or key hits its limit, switch to the next, as Rex intends for normal use.
- Makes easy: the daily caps rarely stop a run.
- Makes hard later: one evaluation run mixes models, so its numbers cannot be compared with another run.
- How it fails: a score changes because the model changed, not because the system did. Allowed for normal use only, with every fallback logged (see Dissent).

## How we would know it was wrong
A latency limit that the design cannot meet even in its simplest form, or an evaluation plan that needs more model calls per day than the limits allow.

## Claude's recommendation
Option B. Retrieval and leakage evaluations use zero model calls. Model responses are cached. Model evaluations run on a small fixed subset (iterate on about 30 questions, run the full 150 at checkpoints).

## Decision (Rex)
Option B with all of Claude's proposals, including the one-model-per-run rule. Followed recommendation: yes.

## Why
Rex: "I agree with all your proposals."

In simple words: the two limits that matter most can be set today (no leaks, and fast enough to use). The quality goal for search cannot be set honestly until we have measured a simple keyword search on the dev questions, so it waits. The free model limits are small, so anything that does not need a model is evaluated without one, and answers from the model are saved so they are never paid for twice.

Rex's intention: rotate between models and between his two keys as fallbacks.

## Dissent, if any
Claude raised two points once, and Rex accepted them:
- Each evaluation run uses one fixed model. Otherwise its numbers are not comparable. Fallbacks are allowed only in normal use, and every fallback must be logged.
- Using a second account to add up free quota may break Google's terms (unchecked). Check the terms before relying on it.

The choice of model is a later decision.

## Consequences
- Recall@10 has no number until the keyword baseline exists.
- Latency is measured per question on this laptop, with at least 150 questions.
- A response cache is needed before any model evaluation.
- Keys and models are never mixed inside one evaluation run.

## Revisit when
The keyword baseline has been measured (then set the recall margin), or the limits in AI Studio change.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the next phase gate._
