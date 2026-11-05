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
Rex runs same_message_check (R8) and fills `rex_label` in the audit file (docs/HOW_TO_RUN.md); then decide 0007 (same-message rule); then the build script.

## Decisions
| # | Title | Date |
|---|---|---|
| 0001 | Project choice: permission-aware Enron mail assistant | 2026-10-22 |
| 0002 | Local parquet reader: pyarrow 26.0.0 | 2026-10-22 |
| 0003 | Progress bars with tqdm 4.70.1 | 2026-11-02 |
| 0004 | Requirements and limits set now | 2026-11-06 |
| 0005 | Data: search EnronQA now, full raw corpus later | 2026-11-06 |
| 0006 | Storage of the frozen dataset: Parquet via pyarrow | 2026-11-06 |

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
- 2026-11-02, c0b3a91, R5 body_copies: 517,401 rows hold 243,509 distinct bodies; 17,236 held by 2 or more users (500 by more than 10); 61,283 mix a sent folder with other folders; 5,252 of 73,772 dev emails (7.1%) have an exact copy with another user (lower bound).
- 2026-11-02, c0b3a91, R6 body_diff: FINDING in all 200 sampled pairs (seed 42) the raw body sits inside the EnronQA body; EnronQA is longer by 23 to 38 characters at the end (a closing line of "=" confirmed by hand on one email); similarity 0.968 / 0.986 / 1.000. EnronQA did not edit the email text (sample; exact equality not tested).
- 2026-11-06, c0b3a91 + raw CSV (SHA-256 a605f0a2…), header probe (Rex, 1,500 groups of identical body text held by 2+ users, seed 7): body only keeps 1,500 of 1,500 groups whole; body + sender + subject + date keeps 1,154 whole and splits 346 (611 copies cut off); the date text differs in 334 groups (22.3%), sender in 72 (4.8%), subject in 52 (3.5%).

## Open questions
- RESOLVED 2026-11-06: the GitHub remote. Only the Enron history is public: `main` was rebuilt as a new history and pushed to `origin` (Enron-Email-Assistant). The old remote is renamed `jobfit` and nothing is pushed to it.
- 0007: what counts as the same message. Principle agreed in discussion: when unsure, err toward denying (a leak is worse than a wrongly denied recipient). Waiting for R7.
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
- 2026-11-06: `main` was rebuilt as an orphan history (first commit = the tree of the reset commit 599dc83, then the later commits cherry-picked), so all hashes changed. The old line stays local as branch `jobfit-full-history` (no upstream) and tag `v1-jobfit-archive`; neither is ever pushed. Remotes: `origin` = Enron-Email-Assistant, `jobfit` = old JobFit repo (nothing pushed to it). Commit hashes in older lines of this file refer to the old line.
- R7 `date_gaps.py` compares the date as collapsed text (so a pure formatting difference lands in the "0 s" bucket), sender lower-cased, subject as collapsed text. Whole-hour gap buckets cover 1 to 14 hours only; a whole-hour gap of 15 to 23 hours is "other under 24 hours". Copies are cut to the 20 lowest row numbers per group, so a capped group may keep a single user. A group with fewer than 2 parsed dates goes to "fewer than 2 dates parsed". The JSON lists, per bucket, the row numbers of up to 10 example groups (all kept rows of each group). It stops with a message if an index row is missing from the CSV.
- R8 `same_message_check.py`, `same_message_audit.py` (audit CSV) and the shared `shared_groups.py` (group selection, header reading, one CSV pass). `date_gaps.py` now imports from `shared_groups.py`; its output on the synthetic test is unchanged. Groups are now ordered by first row, so example row lists are stable.
- R8 memory: the index table is released before the CSV pass and R8 keeps only fingerprints and the date as a number per copy, not the text. The real values for the audit are read in a second CSV pass limited to the 80 audit groups. The memory result is not measured (Claude may not run on real data); Rex's run will show it.
- R8 choices: reference copy = earliest copy in a folder containing "sent", else the earliest copy. Shifts are signed (copy minus reference). Remainder and shift tables use date-only groups (same sender and subject, different date text) and copies up to 14 hours from the reference. Gap bucket "whole hours 1-14" ignores the zone label. The audit sample is drawn from all groups with that gap bucket, by seed 11. Cells starting with = + - @ get a leading space so Excel does not read them as formulas. The audit file is written with a UTF-8 byte-order mark so Excel reads it correctly.
- An untracked file `data_test.py` sits in the repo root. It is not Claude's and was not touched or committed.

## Hours
| Date | Hours | What |
|---|---|---|
