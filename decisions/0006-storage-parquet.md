# 0006: Storage of the frozen dataset: Parquet via pyarrow

- **Status:** accepted
- **Date:** 2026-11-06
- **Phase / component:** data / storage format
- **Builds on:** 0002 (pyarrow reader), 0005 (data)
- **Unblocks:** the build script that writes the frozen dataset
- **Design doc sections updated:** §3 Data

## The decision needed
In what file format the frozen dataset (the emails, their owners and holder lists) is stored.

## Context
The data is read in batches because the laptop has 7.7 GB RAM with about 1.8 GB free (rule 9). The EnronQA files are already Parquet, and decision 0002 already added pyarrow.

## What was studied first
No study card. Sizes from `docs/DATA_NOTES.md`: the four EnronQA Parquet files total 666,346,042 bytes.

## Estimates (if relevant)
Not measured yet.

## Options considered
### Option A: Parquet via pyarrow
- What it is: typed columns, compressed, stored in files.
- Makes easy: it is already our tool, it keeps column types, it is compressed, and it is fast to scan in batches.
- Makes hard later: a lookup by id needs a small in-memory map, because Parquet is not built for single-row lookups.
- How it fails: lookups at query time are too slow or use too much memory once search exists.

### Option B: SQLite
- What it is: one database file, queried with SQL (standard library, from memory, unchecked).
- Makes easy: lookups by id and joins are direct.
- Makes hard later: a second storage tool next to the Parquet files we already have, and row-by-row scans are slower for analysis.
- How it fails: writing the whole dataset into it adds a step that Parquet does not need.

### Option C: JSON Lines
- What it is: one JSON object per line in a text file.
- Makes easy: readable, no library.
- Makes hard later: no column types, larger files, slower scans.
- How it fails: type mistakes go unnoticed and the files are slow to read in batches.

## How we would know it was wrong
Query-time lookups are too slow or too memory-hungry once search exists.

## Claude's recommendation
Option A.

## Decision (Rex)
Option A, Parquet. Followed recommendation: yes. Rex did not give a reason of his own.

## Why
Rex chose Parquet without giving his own reason. The reasons below are Claude's, taken from the earlier project brief: it is already our tool, it is typed, compressed, and fast to scan in batches. Lookups by id need a small in-memory map.

## Dissent, if any
None.

## Consequences
The frozen dataset is written with pyarrow. A small id-to-row map is kept in memory for lookups.

## Revisit when
Lookups by id at query time turn out too slow or too memory-hungry.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the next phase gate._
