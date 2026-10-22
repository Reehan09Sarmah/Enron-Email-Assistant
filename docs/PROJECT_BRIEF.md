# Project brief: permission-aware Enron mail assistant

**Status:** project chosen (Decision 0001, 2026-10-22). Everything below "Fixed requirements" is implemented through Rex's decisions.

## Business context
Companies now put AI assistants over employees' mail and documents (Microsoft 365 Copilot, Gemini in Google Workspace, Glean). The assistant searches the organisation's data, then answers. Two failures are documented:
1. **Oversharing:** retrieval over a shared index can surface content the asking user should not see. Access control has to be enforced inside retrieval, not checked afterwards.
2. **Mail as an attack channel:** EchoLeak (CVE-2025-32711, June 2025) was a zero-click prompt injection in Microsoft 365 Copilot. An attacker's email carried hidden instructions; when the victim later asked Copilot about internal data, Copilot retrieved that email and leaked data through an auto-loaded Markdown image link. It bypassed Microsoft's injection classifier, link redaction and content security policy. (Source: arXiv 2509.10540.)

## Problem statement
Build an assistant that answers a user's questions about their mail **accurately, with citations, without ever showing another user's mail, and without being hijacked by mail content**, and prove each of those properties with numbers.

## Proposed solution
An agent over the EnronQA corpus (~103k emails, 150 inboxes; one inbox = one user). It:
- retrieves only from mail the current user may see (access filtering inside retrieval);
- uses the best retrieval setup the measurements support (keyword, dense, hybrid, rerank, metadata filters, thread-aware handling);
- cites the exact email(s) behind every claim and refuses unsupported claims;
- treats all mail as untrusted, with layered defences and a human approval gate before any action (e.g. drafting a reply);
- is exposed through an MCP server where the user identity is fixed at session start, never a model argument;
- is observable (trace, tokens, cost, latency per query) and guarded by CI gates.

## End goal (what exists at the finish)
- A public repo whose README shows three results tables:
  1. **Retrieval quality** across ≥ 4 configurations (recall@k, MRR) on a frozen EnronQA test split.
  2. **Cross-user leakage**: number of leaked documents across an adversarial query set. Must be **0**; enforced in CI.
  3. **Injection attack success rate** before and after each defence layer, including an EchoLeak-style exfiltration attempt.
- Answer-quality numbers on a fixed subset, with an LLM judge whose agreement with Rex's hand labels is reported.
- Cost and latency per query (p50/p95) for the chosen config.
- A 2-page design doc (requirements, architecture, trade-offs, failure modes, numbers) and a short demo with personal data redacted.
- An honest framing: a **measured prototype of two real failure modes**, not an "enterprise-grade" product.

## Learning outcomes (what Rex must be able to explain and defend)
- **Retrieval at scale:** cleaning and deduplicating email (quoted replies, forwards, headers); chunking for mail and threads; BM25 vs dense vs hybrid vs reranking and when each wins; metadata filtering; recall@k, MRR, nDCG and what they hide; CPU-bound indexing costs.
- **Access control in RAG:** pre-filtering vs post-filtering vs per-user indexes; why post-filtering leaks through ranking, counts and timing; why identity must never be model-controlled.
- **Grounding:** citation design, faithfulness vs relevance, refusing unsupported claims.
- **Evals:** using a public QA set correctly (splits, leakage between dev and test), label noise, LLM-as-judge with a Flash-class model and its calibration, regression gates, eval cost control.
- **Security:** threat modelling, indirect prompt injection via mail, the lethal trifecta (private data + untrusted content + an exfiltration channel), exfiltration via links/images, layered defences, least privilege, approval gates, PII redaction, measuring attack success.
- **Agents and MCP:** the hand-written loop (decide, act, observe, stop), state, budgets, stop conditions, recovery; serving tools over MCP with session-bound identity (MCP basics carried over).
- **LLMOps:** tracing, token/cost/latency accounting, prompt versioning, response caching, provider abstraction (behind an interface, even with one provider), quotas and rate limits, CI eval gates.
- **System design:** requirements first (latency, cost, privacy), a design doc with explicit trade-offs.

## Constraints
- **Time:** 3 weeks at ~2 h/day ≈ **42 hours**, including study time in the tutoring chat. Track hours per phase.
- **Hardware:** Intel i5-1135G7, 4 cores, Intel Iris Xe plus an NVIDIA GeForce MX330 (2 GB VRAM, too weak to plan around), Windows 11, ~68 GB free disk on E:, RAM 7.7 GB (about 1.8 GB free when checked 2026-10-22: stream or chunk large files). Bulk embedding may run on Google Colab (GPU) and be downloaded; everything per query (query embedding with the same model, reranking, filtering, indexes) runs locally on CPU. Remote: LLM.
- **Data:** Rex's direction (2026-10-22) is EnronQA only, from Hugging Face `MichaelR207/enron_qa_0922`, saved under `data/raw/enron_qa_0922/` (git-ignored). The raw Kaggle CSV is not used; the formal data decision (version, licence, verification) is Q2.
- **Models:** Gemini **Flash-class** models via API (Rex's constraint; no Grok API). Rex has two Gemini API keys from two Google accounts; whether each is on the paid or unpaid API tier, and its limits, must be read in AI Studio; design so retrieval and leakage evals need zero LLM calls.
- **Data ethics:** these are real people's emails, released via a US regulator and widely used in research. Personal details stay redacted in anything published. Sending them to a free-tier API is acceptable for public research data only; say so explicitly in the design doc.
- **Other work:** placement season; the MLOps platform project is on hold.

## Fixed requirements (acceptance criteria)
Data
- EnronQA source, version and licence verified and recorded **before** any other build work (P1 gate). If unusable, stop and bring Rex alternatives.
- Frozen local copy + manifest (source, version/commit, download date, counts, split seed). Dev/test split fixed; test is never used for tuning.

Retrieval
- ≥ 4 retrieval configurations compared on the same test split with recall@k and MRR; the chosen config justified by numbers, including indexing time and query latency on this laptop.

Access control
- Access filtering happens inside retrieval. A leakage suite (adversarial queries asking for other users' content) reports **0 leaked documents**, enforced as a CI gate.

Answers
- Every answer cites email IDs; a grounding check flags or refuses unsupported claims; its effect is measured.

Agent and MCP
- Hand-written agent loop with explicit state, stop conditions (max steps, repeat detection, budget, explicit done), deliberate failure recovery, and a trace of every step with tokens, cost and latency.
- At least one MCP server serving the mail tools; user identity bound at session start, not a tool argument.
- One consequential action (e.g. `draft_reply`, writes locally) behind a human approval gate. Nothing is ever sent.

Security
- Written threat model (assets, entry points, trust boundaries, abuse cases).
- Injection suite of ≥ 15 attacks planted in local fixture emails (including exfiltration via links/images and instruction-carrying replies), attack-success rate before and after each defence layer.
- PII redaction in outputs, traces and logs, with tests. Secrets never in context or logs, with a test.

Evals and LLMOps
- One command runs the zero-LLM evals (retrieval, leakage); another runs the cached LLM evals on a fixed subset.
- LLM judge agreement with ≥ 50 of Rex's hand labels reported.
- CI on every push: tests, retrieval regression threshold, leakage = 0.
- README with architecture diagram, the three tables, decision index; 2-page design doc.

## How we work
Like a senior team: **requirements first, then a living design doc (`docs/DESIGN.md`), then decisions that build on each other (the decision ladder in `PROGRESS.md`), then small measured slices of code.** No component is chosen before the requirement it serves has a number. Components sit behind interfaces so alternatives can be swapped and compared. Every estimate is later checked against a measurement.

## Phases and budget (Rex confirms or changes; each decision starts with a study card)
| Phase | Hours | Content |
|---|---|---|
| P0 Reset and setup | 1 | RAM confirmed; download EnronQA into the git-ignored `data/raw/`; provider keys and quota check (no model decision yet). Environment (Python, `.venv`, `mcp` 2.3.0) is kept, not re-decided |
| P1 Frame and design | 4 | Ladder Stage A, no code: requirements and targets; data source and data contract; access model; eval plan; back-of-envelope estimates; high-level architecture and interfaces. `DESIGN.md` §2–§7 drafted |
| P2 Data | 3 | Download and freeze the chosen (cleaned) data; manifest; verify the data contract with real checks; derive access metadata; fixed splits |
| P3 Baseline + access control | 6 | Keyword baseline; access-enforcement point; leakage suite = 0; first quality and latency numbers against the targets |
| P4 Retrieval upgrades | 6 | Chunking; embeddings + vector store; hybrid fusion; reranking; metadata filters; comparison table with latency and indexing cost |
| P5 Agent, MCP and answers | 5 | Provider interface; hand-written loop; MCP mail server with session-bound identity; citations; grounding check; approval-gated `draft_reply`; trace |
| P6 Evals | 5 | Fixed LLM-eval subset; answer-quality metrics; hand labels; judge calibration; eval runners; response cache |
| P7 Security | 6 | Threat model; injection suite incl. EchoLeak-style exfiltration; defence layers measured one by one; PII redaction; secrets tests |
| P8 LLMOps and ship | 6 | Cost/latency report; CI gates; README and tables; `DESIGN.md` finalised with a ≤ 2-page summary on top; redacted demo; defend-it round |

**Cut order if time slips** (Rex decides each cut): semantic cache → model routing → Streamable HTTP → metadata filters → reranking → judge calibration beyond 30 labels. **Never cut:** data gate, frozen split, leakage = 0 gate, comparison table, injection suite with before/after, approval gate, PII redaction.

## Out of scope unless Rex decides otherwise
Sending email, real authentication/SSO, multi-tenant deployment, web UI beyond a minimal demo, fine-tuning, local LLM inference. (The raw Kaggle corpus is not used; Rex's direction, 2026-10-22. Revisit only if Q2 finds EnronQA unusable.)
