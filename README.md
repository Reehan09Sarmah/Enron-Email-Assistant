# Enron Mail Assistant (working title)

A learning project: a permission-aware AI assistant over the Enron email corpus (about 103k emails across 150 inboxes, via the EnronQA dataset). It answers a user's questions only from mail that user may see, cites every claim, treats incoming mail as untrusted, and asks for approval before any action. Every one of those properties is measured.

> **Status: just started (2026-10-22).** Nothing is built yet. This README will only describe what exists.

## Why
Assistants over company mail have two documented failure modes: showing people content they should not see, and being hijacked by instructions hidden inside an email (for example EchoLeak, CVE-2025-32711, in Microsoft 365 Copilot). This project builds a small, measured prototype that tackles both.

## Planned results
1. Retrieval quality across several setups (keyword, embeddings, hybrid, reranked).
2. Cross-user leakage: must be zero, checked on every push.
3. Prompt-injection success rate before and after each defence.

## Data note
The Enron emails are real messages from real people, released by a US regulator and widely used in research. Personal details are redacted in everything this repo shows.

## Layout
```
decisions/   one short file per design decision, with the reasons
docs/        project brief and teaching notes
PROGRESS.md  where the project stands
```

## History
This repo first held JobFit, a resume-fit agent. That version is kept at git tag `v1-jobfit-archive`.
