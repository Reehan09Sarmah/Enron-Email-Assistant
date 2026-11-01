# Progress

Updated: 2026-10-31

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
Rex runs raw_index and R1-R4 (docs/HOW_TO_RUN.md), then reviews results.

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
- `emails.csv/` (1.4 GB raw Kaggle file) appeared in the repo folder. It is not in `.gitignore`, so a plain `git add -A` hangs on it. Not committed, not touched.
- `data/work/` holds rebuildable caches (the raw index). Git-ignored through `/data/`.
- Raw probe scripts R1-R4: `raw_csv.py` (reader from Rex's plan), `raw_index.py`, `raw_shape.py`, `raw_copies.py`, `join_to_enronqa.py`, `question_overlap.py`. Extra file `index_tables.py` holds the Message-ID grouping and buckets shared by R2 and R3. `expect_zero`, `info` and `share_row` moved into `report.py` for the new files; the older checks keep their own copies.
- `raw_index` skips the CSV SHA-256 in a trial run (`--limit-rows`) so a trial takes seconds.
- R3 unmatched paths are sorted into named patterns (trailing dot, maildir/ prefix, backslashes, letter case, unknown user folder) by trying each fix and looking the result up in the index.
- R4 reads all three EnronQA splits, not only dev, because it follows up the C2 finding.
- The raw CSV is expected at `data/raw/enron_kaggle/emails.csv` (path set in `common.py`).
- Scripts were tested only on synthetic files in a temp folder (now deleted). None has run on real data.

## Hours
| Date | Hours | What |
|---|---|---|
