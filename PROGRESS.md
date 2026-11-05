# Progress

_Updated by Claude Code at the end of every session and after every finished slice. Rex can edit freely._

**Project:** permission-aware Enron mail assistant (Decision 0001). Fresh start on 2026-10-22; the earlier JobFit project is archived at git tag `v1-jobfit-archive`.
**How we work:** like a senior team. Requirements first, then a living design doc (`docs/DESIGN.md`), then decisions that each build on earlier ones (the ladder below), then small measured slices of code.
**Current phase:** P0 Reset and setup
**Budget:** 42 h planned, 0 h spent
**Last session:** none yet on this project
**Next session starts with:** P0: ask Rex his laptop RAM and where the Kaggle Enron CSV is stored; make sure the data location is git-ignored; set up `.env` for API keys. Then P1: study card S01 for ladder step Q1 (requirements and non-functional targets).

## Carried over from the archived project (knowledge, not decisions)
Rex learned these on 2026-10-18; check with a question instead of issuing a card.
- **MCP lesson 1:** why MCP exists; host / client instance / server (one client instance per server); stdio framing (one JSON message per line, logs to stderr, stdout clean, shutdown by closing stdin); `tools/call` on the wire; JSON-RPC `error` vs tool result `isError: true`; statelessness in spec 2026-07-28 (no `initialize` handshake; per-request `_meta` carries version and capabilities).
- **MCP lesson 2:** tools are model-controlled, resources application-driven, prompts user-controlled.
- **Read previously:** spec 2026-07-28 (overview, changelog, architecture, basic, stdio, tools, resources, prompts); `mcp` 2.x docs (tools, `ToolError` vs `MCPError`, stdio, client transports). Re-read before relying on a detail.
- **Design ideas worth reusing (each still needs a decision here):** tools accept names/IDs from an allow-list, never raw paths; untrusted text fenced in labelled tags with fence-breaking tags removed, plus a size cap; fencing marks text as data but does not make it safe; regex filters and LLM judges are signals, not walls; the approval gate is the backstop for consequential actions.
- **Environment, kept as is by Rex's choice (2026-10-22), not re-decided:** Windows 11, Python 3.14.7, `.venv`, `mcp` 2.3.0 pinned in `requirements.txt`. Every *new* dependency is still a decision. Laptop: i5-1135G7, no CUDA GPU, ~68 GB free disk, RAM unknown. Google Colab (GPU) is available to Rex for bulk jobs such as embedding the corpus.

## Data facts checked in the planning chat (re-verify in P1)
- Rex has downloaded the Kaggle Enron email dataset (1.43 GB CSV; location to confirm). From memory, unverified: this is the CMU May 2015 release, ~517k raw emails, with a `file` column whose first path segment names the mailbox owner and a `message` column holding the raw email.
- EnronQA paper (arXiv 2505.00263): 103,638 emails, 528,304 QA pairs, 150 inboxes.
- Hugging Face repo `MichaelR207/enron_qa_0922`: parquet, ~666 MB total, no licence shown on the repo page (checked 2026-10-22). Other versions exist (`enron_qa_0805`, `enron_qa_0822`). Which one the paper uses, the fields, and the licence are unverified.
- **Rex's stated leaning (2026-10-22):** use a cleaned dataset (EnronQA) because cleaning raw email takes too long. This is input to Q2, not the decision itself.

## Decision ladder (Claude proposes, Rex decides; each step builds on the ones before)
Work top to bottom. A step may start only when the steps it builds on are accepted. Each accepted step updates the named section of `docs/DESIGN.md`. Decision numbers are assigned when recorded.

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
  - [ ] RAM confirmed
  - [ ] Kaggle CSV location confirmed and git-ignored
  - [ ] API keys in `.env`; free-tier quotas noted for candidate providers (no model choice yet)
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
- `.gitignore` will need entries for the frozen data, indexes and caches once their locations are decided.

## Minor calls log
_One line each: what Claude decided on its own. Rex can veto._
- Reset: deleted old files first, then copied the kit with `cp -r _reset/files/. .` so the new `0001-project-choice.md` replaced the old one cleanly; verified the copy with `diff -r` before deleting `_reset/`.

## Hours log
_Date, phase, hours (study + build), what was done._

## Session log
_Date, what was covered, what Rex should be able to explain now, one thing to revisit._
- **2026-10-22 (reset session).** Tagged `v1-jobfit-archive` (local, not pushed); deleted old decisions 0001 to 0007, `servers/`, `tests/`; installed the Enron kit (CLAUDE.md, PROGRESS.md, README.md, brief, teaching protocol, DESIGN.md skeleton, decisions index, template, new 0001); stale-reference search clean apart from deliberate history notes. No project code written. Rex should be able to explain: why the old work is retrievable (tag) and what changes in the workflow (study cards, decision ladder). Revisit: GitHub repo name (open question).
