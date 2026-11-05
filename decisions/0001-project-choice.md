# 0001: Project choice: permission-aware Enron mail assistant

- **Status:** accepted
- **Date:** 2026-10-22
- **Phase / component:** P1 Scope / project choice (made in Rex's planning chat with Claude, before this session)

## The decision needed
Which resume-worthy project to build over 2 to 3 weeks that teaches RAG with measured retrieval, AI security, AI system design, LLM evaluation and LLMOps, and runs on Rex's 6-year-old laptop with Flash-class API models.

## Context
JobFit (resume-fit agent, archived at tag `v1-jobfit-archive`) had too little data. A maintainer assistant over a public repo was planned next but not started. Rex wants a project that shows larger companies he can handle RAG over large data, and that he has not built before (he has built AutoDev, an agent eval harness, and an MLOps platform, now on hold). Hardware: i5-1135G7, no CUDA GPU. Models: Gemini or Grok Flash-class via API.

## What was studied first
In the planning chat: the business problem (assistants over company mail; oversharing; EchoLeak, CVE-2025-32711), what EnronQA provides, why retrieval and leakage evals can run with zero LLM calls, and an honest list of risks.

## Options considered
### Option A: Permission-aware Enron mail assistant
- What it is: an assistant over 150 Enron inboxes with access control inside retrieval, citations, injection defences and measured results.
- Makes easy: real documented problems; a labelled QA set (EnronQA: ~103k emails, ~528k QA pairs); a strict, LLM-free leakage metric; real personal data, so redaction matters; strong signal for AI platform, security and enterprise roles.
- Makes hard later: messy email data (quoted replies, forwards); "one inbox = one user" is a simplified permission model; licence of the QA set unclear.
- How it fails: cleaning eats the budget, or EnronQA turns out to be unusable.

### Option B: Literature-review assistant resistant to hidden prompts in papers
- What it is: cited answers over arXiv papers, detecting hidden instructions placed in papers (reported in 2025).
- Makes easy: personal motivation, ties to the PhD goal, huge free data.
- Makes hard later: PDF parsing cost; no permissions story; labels must be built.
- How it fails: time goes to parsing; weaker system-design signal.

### Option C: Open-source maintainer assistant
- What it is: agent over one public repo's code, docs, issues and PRs.
- Makes easy: free noisy labels from issue-to-PR links; real untrusted input.
- Makes hard later: code domain overlaps AutoDev; less distinctive.
- How it fails: looks like one more coding assistant.

### Option D: SEC filings analyst (FinanceBench)
- What it is: RAG over company filings, scored on a public 150-question benchmark.
- Makes easy: an external score to compare with published baselines.
- Makes hard later: security story is artificial because filings are trusted.
- How it fails: strong on retrieval, thin on security.

## Claude's recommendation
Option A for AI platform, security and enterprise roles; Option B if personal motivation and the PhD link matter more. Recommendation only.

## Decision (Rex)
Option A. Followed recommendation: yes (the first of the two recommended paths). The MLOps platform project is on hold.

## Why
Rex, original: "Let us do the Enron assistant."

In simple words: this project rests on problems that real companies have actually faced (assistants that overshare, and emails that hijack the assistant), so every feature has a reason beyond a checklist. It comes with labelled questions, so retrieval quality can be measured from day one, and its most important safety property (no user ever sees another user's mail) can be tested exactly, with no AI judge. Caution that comes with it: the strength of this project is the measured numbers and the trade-off reasoning, not the word "enterprise", so it must be presented as a measured prototype.

## Dissent, if any
None. Risks stated up front: time (placement season), data cleaning, unverified licence for EnronQA, a simplified permission model, and Flash-class models being weak judges.

## Consequences
Starts a new project; earlier JobFit decisions do not apply. P1 begins with a data gate (EnronQA source, licence, fields). Personal-data redaction becomes a standing rule. All designs must fit CPU-only local compute and Flash-model API quotas.

## Revisit when
EnronQA is unusable (licence or format), data cleaning exceeds its budget by more than 2 hours, or the leakage gate cannot be made reliable.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the P1 phase gate._
