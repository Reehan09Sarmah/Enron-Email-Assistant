# Progress

_Updated by Claude Code at the end of every session and after every finished slice. Rex can edit freely._

**Project:** permission-aware Enron mail assistant (Decision 0001). Fresh start on 2026-10-22; the earlier JobFit project is archived at git tag `v1-jobfit-archive`.
**How we work:** like a senior team. Requirements first, then a living design doc (`docs/DESIGN.md`), then decisions that each build on earlier ones (the ladder below), then small measured slices of code.
**Current phase:** P0 Reset and setup
**Budget:** 42 h planned, 0 h spent
**Last session:** none yet on this project
**Next session starts with:** run the data validity checks with pyarrow, one small check at a time (first: invariants, then exact duplicates). Rex pastes his two Gemini keys into `.env` and reads each key's tier and limits in AI Studio. Then Rex studies card S01 (already issued) and says `ready` for the Q1 check question.

## Carried over from the archived project (knowledge, not decisions)
Rex learned these on 2026-10-18; check with a question instead of issuing a card.
- **MCP lesson 1:** why MCP exists; host / client instance / server (one client instance per server); stdio framing (one JSON message per line, logs to stderr, stdout clean, shutdown by closing stdin); `tools/call` on the wire; JSON-RPC `error` vs tool result `isError: true`; statelessness in spec 2026-07-28 (no `initialize` handshake; per-request `_meta` carries version and capabilities).
- **MCP lesson 2:** tools are model-controlled, resources application-driven, prompts user-controlled.
- **Read previously:** spec 2026-07-28 (overview, changelog, architecture, basic, stdio, tools, resources, prompts); `mcp` 2.x docs (tools, `ToolError` vs `MCPError`, stdio, client transports). Re-read before relying on a detail.
- **Design ideas worth reusing (each still needs a decision here):** tools accept names/IDs from an allow-list, never raw paths; untrusted text fenced in labelled tags with fence-breaking tags removed, plus a size cap; fencing marks text as data but does not make it safe; regex filters and LLM judges are signals, not walls; the approval gate is the backstop for consequential actions.
- **Environment, kept as is by Rex's choice (2026-10-22), not re-decided:** Windows 11, Python 3.14.7, `.venv`, `mcp` 2.3.0 pinned in `requirements.txt`. Every *new* dependency is still a decision. Laptop (checked 2026-10-22): i5-1135G7 (4 cores / 8 threads), Intel Iris Xe plus NVIDIA GeForce MX330 (2 GB, too weak to plan around; the earlier "no GPU" note was wrong), 7.7 GB RAM (1.8 GB free at check time), E: has ~68 GB free. Google Colab (GPU) is available to Rex for bulk jobs such as embedding the corpus.

## Data facts checked in the planning chat (re-verify in P1)
- **Rex's direction (2026-10-22): EnronQA only; the raw Kaggle CSV is not used.** The formal decision (version, licence, verification) is still Q2, after Q1.
- EnronQA paper (arXiv 2505.00263, verified): built from the 2015 Enron release (517,401 emails, 150 users); cleaning went 517k, MinHash dedup 228k, subset removal 193k, quality filters 103.5k, language/NSFW filters ~102.6k, plus some emails added back, giving 103,638 emails and 528,304 QA pairs. The paper does not say how inboxes were chosen, whether mail is shared across inboxes, or how attachments are handled.
- Source (verified via the Hugging Face API, 2026-10-22): dataset `MichaelR207/enron_qa_0922`, which is the repo the paper's footnote names. Commit sha `c0b3a9190fd970e83cfbe7d399a08860e43e221e`, last modified 2024-09-22. Files: `data/train-00000-of-00002.parquet`, `data/train-00001-of-00002.parquet`, `data/dev-00000-of-00001.parquet`, `data/test-00000-of-00001.parquet` (download size 666,346,042 bytes). Fields: `email`, `questions`, `rephrased_questions`, `gold_answers`, `alternate_answers`, `incorrect_answers`, `gold_rationales`, `alternate_rationales`, `include_email`, `path`, `user`, `questions_count`.
- **Licence: not stated on the dataset repo** (no licence field); the paper is CC BY 4.0, which covers the paper, not necessarily the data. Library of Congress warns that privacy rights may apply to the original corpus. Must be resolved in Q2.
- **Hugging Face discussions (read 2026-10-22, all 4 open):** #1 the owner MichaelR207 says `include_email` is a leftover of an unpublished training experiment, randomly assigned, and can be ignored for retrieval. #3 "Licensing doubts": two users ask whether the data is CC BY 4.0 like the paper; no reply from the owner. #4 asks the same 73.8k vs 103,638 question we have; no reply. #2 asks about "singlehop and multihop" questions (not read). So the licence and the row-count gap are known, unanswered issues.
- **Viewer checks (Hugging Face Dataset Viewer API, 2026-10-22; same commit as our files):** 3 splits × 73,772 rows, 12 columns; viewer, filter, search and statistics available. The `email` and `path` length statistics are identical in all three splits, and the per-user row counts are identical in all three splits, so **the three splits contain the same 73,772 emails and divide each email's questions between them**: questions per email are train 4.52 (2 to 11), dev 1.43 (1 to 3), test 1.21 (0 to 2). Total questions = 73,772 × (4.52032 + 1.43029 + 1.2107) ≈ 528,304, which matches the paper. `user` has 150 values; emails per user range from 5 to 5,485 (median 244). Email length 767 to 89,542 characters (median 1,664). **Row-count gap explained in part:** 73,772 emails carry questions; the paper's corpus is 103,638 emails, so about 29,866 emails (29%) are not in this repo (likely those without a surviving question; unverified). Consequences: the "split" is a question split, not an email split, so dev and test search the same emails (fine for retrieval, but Q4 must split by question and must never tune on test questions); and our retrieval corpus is smaller and easier than the paper's, with no question-free distractor emails.
- **Sample check (Viewer, 2026-10-22, 6 random offsets, seed 42, 3 requests each, 14 s):** at every offset the email, path and user are identical in train/dev/test; no question text is shared between splits; all question/answer/rationale lists have equal length; path owner equals `user`; every email starts with a `Subject:` header; questions per email were 11/2/2, 5/2/2, 3/1/1 (train/dev/test), so a heavily-questioned email gives most of its questions to train. 6 of 6 pass. Too small to be a proof; the full checks need a local reader.
- **Local reader check (pyarrow 26.0.0, 2026-10-22, decision 0002):** footers of the 4 files agree with the Viewer: dev 73,772 rows in 74 row groups, test 73,772 in 74, train 36,886 + 36,886 in 37 + 37; each row group holds up to 1,000 rows (min 772). 12 columns; `email`, `path`, `user` are strings, `questions_count` is int64, the rest are lists. Streaming only `user` across all 73,772 dev rows peaked at 37 MB; one batch of 1,000 `email` values (1.94 M characters) peaked at 49 MB. So the "peak memory under 1 GB per check" criterion in 0002 holds with a wide margin at batch size 1,000 (one row group).
- **Unexplained, verify after download:** the three splits hold 73,772 rows each (221,316 total) while the paper says 103,638 emails. Check whether rows are emails or (email, user) pairs, and whether the same email appears in more than one split (dev/test leakage, Q4).
- Local path (git-ignored via `/data/`): `data/raw/enron_qa_0922/`. Never edit files there; the frozen, manifested copy is made in P2. Downloaded 2026-10-22, SHA-256 (seed for the P2 manifest):
  - `dev-00000-of-00001.parquet` 174,127,294 B `3661cb585657061c156a408b201afbb4adf94d2e20fd41cc172c26c582800185`
  - `test-00000-of-00001.parquet` 161,772,154 B `9684fe7d459195ca0873616a28956a9498c88e819c0d2cd7f5196f14513143ee`
  - `train-00000-of-00002.parquet` 152,601,618 B `9b1de19cd552d19625f691e21101028965099b8e98b24b896ef3e6e078f4c447`
  - `train-00001-of-00002.parquet` 177,844,976 B `873329b234e713342dee769413d4974962e8a525dc50dfea5fbd15fc25b4af0a`

## API provider notes for P0 (no model chosen; re-check in Q15)
- **Gemini (Google), verified from [terms](https://ai.google.dev/gemini-api/terms):** on the **unpaid** tier Google may use prompts and responses to improve its products and human reviewers may read them; the terms say not to submit sensitive, confidential or personal information. Paid (a Cloud project with billing) does not train on your data. Exception: in the EEA, Switzerland and the UK the paid terms apply to free use too. Enron mail has real people's details, so this feeds the privacy stance in Q1.
- **Gemini free-tier numbers:** the [rate-limits page](https://ai.google.dev/gemini-api/docs/rate-limits) gives no fixed free numbers; it says limits depend on your account and are shown in AI Studio. Rex reads his own limits there and we record them here.
- **Grok:** dropped; Rex has no Grok API (2026-10-22).
- **Rex's two Gemini keys (2026-10-22):** one from a student Pro account, one from a paid Pro account. Per the terms above, the API counts as paid only when the key's Cloud project has an active billing account; a consumer Pro subscription by itself does not make API use paid (verified from the terms' definition; whether either of Rex's projects has billing is unknown). Rex checks each key's tier and limits in AI Studio. Using two accounts to add up free quota may break Google's terms (from memory, unverified); check before relying on it.

## Decision ladder (Claude proposes, Rex decides; each step builds on the ones before)
Work top to bottom. A step may start only when the steps it builds on are accepted. Each accepted step updates the named section of `docs/DESIGN.md`. Decision numbers are assigned when recorded.

**Order change (Rex, 2026-10-22):** before studying Q1, confirm that EnronQA is valid and usable (the "data validity check" below). Q1 study card S01 is issued and waits until then. The check only gathers facts; the Q2 decision itself is still briefed after Q1.
- Data validity check: route chosen = local reader, pyarrow (decision 0002, accepted). Next: run the checks 4 to 7 and 10 to 11 one at a time, each small, then the 50-row hand audit; results go under "Data facts". _→ evidence for Q2._

**Stage A: Frame the system (P1). No code.**
- Q1 Requirements: user stories, goals and non-goals, non-functional targets with numbers (retrieval quality, p50/p95 latency, cost per query, leakage = 0, injection success target, laptop limits), privacy stance on free-tier APIs. _Builds on 0001. → DESIGN §2, §3._
- Q2 Data source and data contract: EnronQA only / Kaggle only / both; which EnronQA version; licence; what we verify instead of trusting "cleaned" (schema, counts, duplicates, question→email links, sample audit). _Builds on Q1. → §5.1, §5.2._
- Q3 Access model: who may see which email (own inbox; recipients of the same message; shared threads) and how that is derived from the data. _Builds on Q2. → §5.3._
- Q4 Evaluation plan: metrics and targets, dev/test split, LLM-eval subset size within quotas, leakage-suite design, what "better" means for each later decision. _Builds on Q1–Q3. → §5.4, §12._
- Q5 Back-of-envelope estimates: chunks, vector memory, embedding time (CPU vs Colab), index size, API calls per eval run. _Builds on Q1–Q4. → §4._
- Q6 High-level architecture: offline (ingest/index) vs online (query) paths, components and their interfaces (so retrievers can be swapped and compared), trust boundaries, storage format and manifest. _Builds on Q1–Q5. → §6, §7._

**Stage B: Data and measured baseline (P2–P3).**
- Q7 Storage, freeze and manifest implementation details (within Q6). _→ §5.1._
- Q8 Keyword index. _Builds on Q5, Q6. → §8._
- Q9 Access-enforcement point: pre-filter / post-filter / per-user index. _Builds on Q3, Q8. → §9._

**Stage C: Retrieval upgrades (P4).** Each is judged against the Q4 metrics and Q1 latency targets.
- Q10 Chunking. _Builds on Q2, Q4._
- Q11 Embedding model and where it runs (Colab bulk, CPU queries, same model version). _Builds on Q5, Q10._
- Q12 Vector store (must support Q9's enforcement). _Builds on Q9, Q11._
- Q13 Fusion and reranker. _Builds on Q8, Q12, Q1 latency._
- Q14 Metadata filters. _Builds on Q6._

**Stage D: Answering, agent and MCP (P5).**
- Q15 LLM provider and model (Flash-class). _Builds on Q1 cost, Q4 quotas._
- Q16 Agent loop: state, budgets, stop conditions, recovery. _Builds on Q15._
- Q17 Trace schema, token/cost/latency accounting. _Builds on Q1, Q16. → §13._
- Q18 MCP server and tool surface; how identity is bound at session start. _Builds on Q9, Q16._
- Q19 Citation format and grounding check. _Builds on Q16._
- Q20 Consequential action and approval gate. _Builds on Q18._

**Stage E: Evals (P6).**
- Q21 Judge design and calibration plan. _Builds on Q4, Q15._
- Q22 Response caching and eval runners. _Builds on Q4, Q17._

**Stage F: Security (P7).**
- Q23 Threat model and defence layers. _Builds on Q6, Q18, Q20. → §11._
- Q24 PII redaction approach. _Builds on Q2, Q23._

**Stage G: Ship (P8).**
- Q25 CI gates and thresholds. _Builds on Q4, Q22._
- Stretch (only if budget allows, Rex decides): semantic cache, model routing, Streamable HTTP, framework port.

## Phases and components
- [ ] **P0 Reset and setup** (1 h)
  - [x] Repo reset; old work archived at tag `v1-jobfit-archive`
  - [x] RAM confirmed (7.7 GB; checked by Claude 2026-10-22)
  - [x] EnronQA parquet files downloaded to `data/raw/enron_qa_0922/` (git-ignored). Verified 2026-10-22: 4 files, total 666,346,042 bytes = the size the Hugging Face API reports; each starts and ends with the parquet marker `PAR1`. All four local SHA-256 hashes equal the LFS sha256 the Hugging Face API lists for commit `c0b3a91…` (checked 2026-10-22), so the files are exactly the published ones. Rows not yet read (needs a parquet reader, a new dependency, so a decision; see Open questions).
  - [ ] API keys in `.env` (`.env` created 2026-10-22 from `.env.example` with empty values, confirmed git-ignored; Rex pastes the keys himself); free-tier quotas noted below for candidate providers (no model choice yet)
- [ ] **P1 Frame and design** (4 h): ladder Stage A (Q1–Q6); `DESIGN.md` §2–§7 drafted. Rex may run `/grill-me` on the design at the end.
- [ ] **P2 Data** (3 h): download and freeze; manifest; verify the data contract (Q2) with real checks; derive access metadata (Q3); fixed splits (Q4)
- [ ] **P3 Baseline + access control** (6 h): keyword baseline (Q8); enforcement point (Q9); leakage suite = 0; first quality and latency numbers vs Q1 targets
- [ ] **P4 Retrieval upgrades** (6 h): Q10–Q14; comparison table with quality, latency, indexing time and memory
- [ ] **P5 Agent, MCP and answers** (5 h): Q15–Q20
- [ ] **P6 Evals** (5 h): Q21–Q22; ≥ 50 hand labels; judge agreement; one-command runners
- [ ] **P7 Security** (6 h): Q23–Q24; injection suite (≥ 15, incl. EchoLeak-style exfiltration); before/after per layer; PII and secrets tests
- [ ] **P8 Ship** (6 h): Q25; cost/latency report; README with three tables; `DESIGN.md` finalised (≤ 2 pages summary at top); redacted demo; defend-it round

## Concepts studied
_Study card ID, date, topic, check result._
- S01, issued 2026-10-22: Q1 requirements and non-functional targets. Not yet studied (Rex is doing the data validity check first).

## Decisions made
_See `decisions/README.md` for the index._

## Results log
_One line per measured result: date, data version, config, metric, number. Append only._

## Estimates vs reality
_Each Q5 estimate next to the measured value once known, with a one-line note on the gap._

## In Rex's words
_One short entry per finished component: what it does and why we designed it this way. Written by Claude per Rex's standing instruction._

## Open questions / parked
- GitHub remote is still `JobFit`. Reuse it (rename on GitHub) or start a new repo? Rex's call; nothing is pushed until he decides.
- `resumes/` (Rex's own files, git-ignored) was left untouched. Not part of this project.
- `.gitignore` will need entries for the frozen data, indexes and caches once their locations are decided (`/data/` already covers anything placed under `data/`).
- **Input to Q2 (Rex, 2026-10-22): "What if mistakes in this clean dataset … snowball into our future decisions?"** Options to brief in Q2: (A) EnronQA as-is, protected by data-contract checks and a hand audit; (B) A plus the raw Kaggle corpus as an audit reference, joined through EnronQA's `path` field (join key unverified); (C) clean the raw corpus ourselves (loses EnronQA's question labels unless re-mapped; the paper reports 10–50 LLM calls per generated question, far beyond free quotas). Known risks to check: dedup may have collapsed copies of one message held by several users (affects Q3), the 50–1,000-word filter makes the corpus cleaner than real mail (affects how honest the retrieval numbers are), near-duplicates below the 0.9 threshold can make "one gold email per question" too strict (affects Q4), LLM-written questions carry label noise, and the split basis and the 221k vs 103,638 mismatch are unexplained.
- Reading the parquet files needs a parquet reader (for example `pyarrow` or `polars`), which is not installed and is a new dependency, so it is a decision with a study card. Needed for Q2's verification checks. With 7.7 GB RAM the largest file (178 MB compressed, about 1.4 GB of text in total) must be read in batches.

## Minor calls log
_One line each: what Claude decided on its own. Rex can veto._
- Hardware corrected in `CLAUDE.md` and `PROJECT_BRIEF.md` (MX330 present, 7.7 GB RAM). `decisions/0001-project-choice.md` still says "no CUDA GPU" in its Context; left as written because decisions are not edited, and this line is the correction.
- 0002 follow-through: `requirements.txt` now has `pyarrow==26.0.0` (only pyarrow was installed, no extra packages). Batch size for checks defaults to 1,000 rows to match the files' row groups. Peak-memory helper uses `ctypes` with the Windows API (no `psutil`, to avoid another dependency); it is a throwaway snippet, not a repo file.
- `.env` key names: `GEMINI_API_KEY_PAID` and `GEMINI_API_KEY_STUDENT` (Grok line removed; both were still empty when rewritten).
- Created `.env.example` (two empty key names for the candidate providers); `.env` itself is made by Rex so keys never pass through me. Checked with `git check-ignore`: `.env` ignored, `.env.example` tracked.
- Data folder `data/raw/enron_qa_0922/`: covered by the existing `/data/` rule in `.gitignore`, so no `.gitignore` change was needed. Manual browser download chosen so no new dependency (`huggingface_hub`) is added.
- Reset: deleted old files first, then copied the kit with `cp -r _reset/files/. .` so the new `0001-project-choice.md` replaced the old one cleanly; verified the copy with `diff -r` before deleting `_reset/`.

## Hours log
_Date, phase, hours (study + build), what was done._

## Session log
_Date, what was covered, what Rex should be able to explain now, one thing to revisit._
- **2026-10-22 (reset session).** Tagged `v1-jobfit-archive` (local, not pushed); deleted old decisions 0001 to 0007, `servers/`, `tests/`; installed the Enron kit (CLAUDE.md, PROGRESS.md, README.md, brief, teaching protocol, DESIGN.md skeleton, decisions index, template, new 0001); stale-reference search clean apart from deliberate history notes. No project code written. Rex should be able to explain: why the old work is retrievable (tag) and what changes in the workflow (study cards, decision ladder). Revisit: GitHub repo name (open question).
