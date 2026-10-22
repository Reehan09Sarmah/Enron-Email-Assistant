# 0002: Local parquet reader: pyarrow

- **Status:** accepted
- **Date:** 2026-10-22
- **Phase / component:** P0/P1 data validity check, and later P2 data freeze / parquet reader
- **Builds on:** 0001 (project choice); Rex's direction "EnronQA only" (formal data decision is Q2, not yet made)
- **Unblocks:** the full data checks (invariants, duplicates, split integrity, label checks, access facts); the P2 frozen copy and manifest
- **Design doc sections updated:** none yet (§5.1 and §5.2 are owned by Q2; this decision only adds a tool)

## The decision needed
Which library, if any, to add so the project can read the EnronQA parquet files locally.

## Context
EnronQA is 4 parquet files (666 MB compressed, about 1.3 GB in memory, 12 columns, 3 splits of 73,772 rows). The laptop has 7.7 GB RAM with about 1.8 GB free, so every check must read only the columns it needs, in small batches. The Hugging Face Viewer API only supports small samples and needs the network. A new dependency is a major decision under `CLAUDE.md`.

## What was studied first
No formal study card (S02 was drafted and dropped by Rex's request). In-session: a short comparison of pyarrow and duckdb, and an example of how parquet stores data by column, row groups and a footer index. The check question was not asked. Read: Arrow v26.0.0 docs for `ParquetFile.iter_batches` (verified), DuckDB 2.0 docs for parquet pushdown (verified), PyPI JSON for wheels (2026-10-22). Unverified: duckdb's memory behaviour; install-testing of duckdb on Python 3.14.

## Estimates
`email` column per split: 73,772 × about 2,270 characters ≈ 167 MB of text. Batches of 5,000 rows ≈ 11 MB of email text per batch. All 12 columns of train ≈ 665 MB in memory (Viewer).

## Options considered
### Option A: pyarrow 26.0.0
- What it is: the reference Arrow/Parquet library; Apache-2.0; 29 MB Windows wheel for Python 3.14; no required dependencies on PyPI (verified).
- Makes easy: documented streaming with `iter_batches(batch_size, row_groups, columns)`; explicit control over memory; can also write the frozen copy in P2.
- Makes hard later: low level, so checks are hand-written Python (no SQL).
- How it fails: a check that forgets `columns` or `batch_size` loads far too much; bounded memory across a whole scan is a design inference, not a stated guarantee, so we measure it.

### Option B: duckdb 2.0.0
- What it is: an embedded SQL engine that queries parquet files directly; 15 MB wheel (tag cp312-abi3).
- Makes easy: short SQL for counts and duplicates; column and filter pushdown (verified).
- Makes hard later: memory limits not stated on the docs page read; release one day old (2026-10-21); a second tool to explain.
- How it fails: an unbounded group-by or join over text could use a lot of RAM.

### Option C: no new dependency (Viewer API and Colab)
- What it is: the approach used so far.
- Makes easy: nothing to install.
- Makes hard later: samples only, needs the network, Colab code lives outside the repo, P2 cannot rebuild the frozen copy offline.
- How it fails: results we cannot reproduce.

## How we would know it was wrong
Peak memory above 1 GB on any single check, a check taking longer than 2 minutes, or hand-written checks needing far more code than the same check in SQL.

## Claude's recommendation
Option A, pinned to `==26.0.0`: most predictable memory behaviour, a documented streaming call that is easy to explain, and it is also useful in P2.

## Decision (Rex)
Option A, pyarrow. Followed recommendation: yes.

## Why
Rex, original: "Go with A, pyarrow."

Rex gave no reason of his own, so none is put in his mouth here. The reasons below are the ones in the brief that he accepted: with a laptop that has 1.8 GB of free RAM, we need to say exactly which columns and how many rows each check reads, and pyarrow's documented batch reading lets us do that. The price is that we write the checks by hand, which also makes them easier to explain. To be completed when Rex gives his own reason (asked at the phase gate).

## Dissent, if any
None.

## Consequences
Adds one dependency, `pyarrow==26.0.0`, to `requirements.txt`. Every check must pass `columns=` and a batch size. We measure peak memory of each check and log it. Checks that SQL would shorten (counts, duplicates) are written as loops; if that proves costly, reopen with duckdb.

## Revisit when
Any trigger under "How we would know it was wrong", or if P2 shows pyarrow cannot write the frozen copy we need.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the P1 phase gate._
