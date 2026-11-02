# Progress

Updated: 2026-11-02

## The order we work in
1. Project choice: done (decision 0001)
2. Check the data: in progress
3. Requirements: what success means, in numbers
4. Data decision
5. Access rule: who may see which email
6. Evaluation plan
7. Rough sizes and costs
8. Design
9. Build in small measured steps

## Next step
Rex reruns raw_index (the index gained a `folder` column), then runs R5 and R6 (docs/HOW_TO_RUN.md; close heavy apps for both) and reviews the results.

## Decisions
| # | Title | Date |
|---|---|---|
| 0001 | Project choice: permission-aware Enron mail assistant | 2026-10-22 |
| 0002 | Local parquet reader: pyarrow 26.0.0 | 2026-10-22 |
| 0003 | Progress bars with tqdm 4.70.1 | 2026-11-02 |

## Results log
One line per measured result: date, data version (commit `c0b3a91`), check, number.
- 2026-10-31, c0b3a91, C1 rows_well_formed: 221,316 rows read, 0 of 15 rules broken.
- 2026-10-31, c0b3a91, C2 file_relationship: same 73,772 keys and emails in all splits; FINDING 3,106 question fingerprints in more than one split.
- 2026-10-31, c0b3a91, C3 duplicate_emails (dev only): 73,772 unique emails, 0 duplicate groups, with or without the File: line.
- 2026-10-31, c0b3a91, C4 ids_and_headers: all headers well formed; FINDING median emails per user is 240.5 (not 244), and path repeats 147,544 times across all splits (each split repeats the same emails).
- 2026-11-02, c0b3a91 + raw CSV (SHA-256 a605f0a2…): raw_index: 517,401 rows indexed, 85.1 s, peak 815 MB.
- 2026-11-02, c0b3a91, R1 raw_shape: 517,401 rows, 150 users, 100% have Message-ID, Date and From, 95.8% have To; per user 35 / 1,652 / 28,465; 0 empty messages.
- 2026-11-02, c0b3a91, R2 raw_copies: FINDING all 517,401 Message-IDs are unique, so they cannot link copies across mailboxes.
- 2026-11-02, c0b3a91, R3 join_to_enronqa: all 73,772 keys match a raw file value; FINDING 0 bodies identical, also after collapsing whitespace; EnronQA holds 14.3% of the raw messages.
- 2026-11-02, c0b3a91, R4 question_overlap: FINDING the 3,106 shared questions all sit on different emails (0 on the same email in two splits); 2,389 on 2 emails, 564 on 3-5, 104 on 6-10, 49 on more than 10.

## Open questions
- The GitHub remote is still named `JobFit`. Reuse it (rename on GitHub) or start a new repo? Nothing is pushed until Rex decides.
- Ideas from the earlier plan, to reconsider during requirements, not decided: compare at least 4 search setups; MCP server; approval step before any action; automatic checks on every push; at least 15 prompt-injection test emails; AI-judge calibrated against Rex's labels.

## Small calls
- `requirements.txt` holds `pyarrow==26.0.0` (decision 0002).
- `.env` key names: `GEMINI_API_KEY_PAID` and `GEMINI_API_KEY_STUDENT`. `.env` is git-ignored; `.env.example` is tracked.
- Raw data sits in `data/raw/enron_qa_0922/`, covered by the `/data/` rule in `.gitignore`. It was downloaded by hand so no download library was added.
- Decision 0001 still says "no CUDA GPU". The laptop has an NVIDIA MX330 with 2 GB VRAM, too weak to plan around. Decisions are not edited, so this line is the correction.
- `scripts/data_checks/`: shared reader and fingerprints in `common.py`, printing and JSON saving in `report.py`, one file per check. `report.py` is an extra file beyond the plan, so `common.py` keeps one purpose.
- Checks read from `data/raw/enron_qa_0922/` (files sit directly in that folder). C4 reports per-split uniqueness next to the all-rows figure, to show where repeats come from.
- The 1.4 GB raw Kaggle file now sits at `data/raw/enron_kaggle/emails.csv`, covered by `/data/`, so `git add -A` no longer hangs on it. Commits still name their paths.
- `data/work/` holds rebuildable caches (the raw index). Git-ignored through `/data/`.
- Raw probe scripts R1-R4: `raw_csv.py` (reader from Rex's plan), `raw_index.py`, `raw_shape.py`, `raw_copies.py`, `join_to_enronqa.py`, `question_overlap.py`. Extra file `index_tables.py` holds the Message-ID grouping and buckets shared by R2 and R3. `expect_zero`, `info` and `share_row` moved into `report.py` for the new files; the older checks keep their own copies.
- `raw_index` skips the CSV SHA-256 in a trial run (`--limit-rows`) so a trial takes seconds.
- R3 unmatched paths are sorted into named patterns (trailing dot, maildir/ prefix, backslashes, letter case, unknown user folder) by trying each fix and looking the result up in the index.
- R4 reads all three EnronQA splits, not only dev, because it follows up the C2 finding.
- The raw CSV is expected at `data/raw/enron_kaggle/emails.csv` (path set in `common.py`).
- R5 `body_copies.py` and R6 `body_diff.py` were tested only on synthetic files in a temp folder (now deleted); they have not run on real data. R1-R4 ran on real data (Rex, 2026-11-02).
- The raw index gained a `folder` column (the middle of the file value), because R5 needs it for sent folders. Rex must rerun `raw_index` once. `read_index_table` now stops with a clear message when a column is missing.
- R5 also reads the `path` column of the EnronQA dev file, to know which index rows are dev emails. It counts "other users" by distinct users per body, as R3 does for Message-IDs.
- R6 picks its 200 positions among the dev rows with seed 42 (R3 matched all dev keys) and reports keys missing from the raw CSV as a FINDING. It cuts bodies with the same functions as R3 and `raw_index`. Length ratio is EnronQA chars / raw chars. Prefix, suffix, containment and similarity use whitespace-collapsed text. A pair with equal collapsed text counts as "EnronQA contained in raw". `SequenceMatcher` runs with `autojunk=False`, which is exact but can be slow on a few very long bodies.
- R6 saves per-pair numbers and (user, path) in its JSON, never text.

## Hours
| Date | Hours | What |
|---|---|---|
