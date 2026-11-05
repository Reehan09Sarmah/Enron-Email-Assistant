# Design doc: permission-aware Enron mail assistant

## 1. Problem

Companies now put AI assistants over employees' mail and documents, for example Microsoft 365 Copilot, Gemini in Google Workspace and Glean. The assistant searches the company's data, then answers. Two failures are documented:

1. Oversharing. Search over a shared index can show a user mail they should not see. Access has to be enforced inside the search, not checked afterwards.
2. Mail as an attack. EchoLeak (CVE-2025-32711, June 2025) was a prompt injection in Microsoft 365 Copilot that needed no click. An attacker's email carried hidden instructions. When the victim later asked Copilot about internal data, Copilot read that email and leaked data through an image link that loaded by itself (source: arXiv 2509.10540).

The problem: build an assistant that answers a user's questions about their own mail, accurately, with citations, without ever showing another user's mail, and without being hijacked by what an email says. Each of those properties must be shown with numbers.

## 2. Requirements
Set by decision 0004 (2026-11-06):
- Leakage: 0 in every test (fixed rule 3).
- Latency, measured on at least 150 questions on this laptop: search alone p95 at most 1 second; full answer p95 at most 12 seconds.
- Recall@10: no number yet. It is set after the keyword baseline is measured on the dev questions, as "beat the baseline by a stated margin".
- Model calls: retrieval and leakage evaluations use none; model responses are cached; each evaluation run uses one fixed model; model evaluations iterate on about 30 questions and run the full 150 at checkpoints.

## 3. Data
Set by decisions 0005 and 0006 (2026-11-06):
- Search the 73,772 EnronQA emails first (option B). Who holds a copy of each email comes from the raw Kaggle corpus. Searching the full raw corpus (517,401 messages) is a required later step (option C).
- What counts as the same message is not decided yet (open question 0007 in PROGRESS.md).
- The frozen dataset is stored as Parquet via pyarrow, with a small in-memory map for lookups by id.

## 4. Access rule
Empty until decided.

## 5. Evaluation
Empty until decided.

## 6. Sizes and costs
Free-tier Gemini limits read by Rex in AI Studio on 2026-11-06 (decision 0004; model names as he read them):

| Model | Requests per minute | Tokens per minute | Requests per day |
|---|---|---|---|
| Gemini 2.5 Flash, 3 Flash, 3.6 Flash, 3.8 Flash (each) | 5 | 250K | 20 |
| Gemini 3.5 Flash Lite | 15 | 250K | 500 |
| Gemma 4 26B | 30 | 16K | 14.4K |

Other sizes and costs are not measured yet.

## 7. Architecture
Empty until decided.

## 8. Security
Empty until decided.

## 9. Results
Empty until decided.
