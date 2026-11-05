# How to run the data scripts

Rex runs these himself. Claude only tests them on tiny fake files.

1. Open PowerShell in `E:\PROJECTS\Email Assistant`.
2. Use `.\.venv\Scripts\python.exe` directly. No activation is needed.
3. Install the libraries (once, and again after `requirements.txt` changes):
   `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. Before a big run:
   - Close Chrome and other heavy apps, and keep the laptop plugged in.
   - Open Task Manager and watch the Memory column for `python.exe`.
   - Ctrl+C stops a run safely. The index file is only replaced when a run finishes.
5. The raw CSV must be at `data\raw\enron_kaggle\emails.csv`. Run in this order, each as
   `.\.venv\Scripts\python.exe -m scripts.data_checks.<name>`:
   1. `raw_index --limit-rows 20000` (trial run, should take seconds)
   2. `raw_index` (full run; builds the index and the CSV's SHA-256)
   3. `raw_shape`
   4. `raw_copies`
   5. `join_to_enronqa`
   6. `question_overlap` (reads the EnronQA files only, not the index)
   7. `body_copies` (R5; reads the index and the EnronQA dev `path` column). It needs
      the `folder` column, so rerun step 2 once first if the index was built before
      2026-11-02.
   8. `body_diff` (R6; streams the whole CSV like `raw_index`, so close heavy apps
      first). Takes `--block-mb` too. Comparing 200 pairs can take a few minutes.
6. If `raw_index` says a message is bigger than the block, rerun it with `--block-mb 32`.
   If memory for `python.exe` goes above 1 GB, press Ctrl+C and tell Claude in the chat.
7. Results are saved as JSON in `data\reports\`. The index is `data\work\raw_index.parquet`
   and can be rebuilt at any time.

## Running R5 and R6 (copy and paste)
Do the checks above first. Close heavy apps, then run these in order from
`E:\PROJECTS\Email Assistant`:

1. Rebuild the index (needed once, it adds the `folder` column; about 90 seconds):
   `.\.venv\Scripts\python.exe -m scripts.data_checks.raw_index`
2. R5, body copies (fast, reads only the index and the EnronQA dev `path` column):
   `.\.venv\Scripts\python.exe -m scripts.data_checks.body_copies`
3. R6, body diff (reads the whole CSV again, about 90 seconds, then compares 200 pairs):
   `.\.venv\Scripts\python.exe -m scripts.data_checks.body_diff`

R5 saves `data\reports\body_copies.json` and R6 saves `data\reports\body_diff.json`.
R6 never prints or saves email text; open the example keys it lists to look yourself.
If R5 says "The index has no column ['folder']", redo step 1.

## Running R7 (date_gaps)
Close heavy apps first. It needs the index from `raw_index` (built after 2026-11-02 is fine). It reads the CSV once, so it takes about a minute.

`.\.venv\Scripts\python.exe -m scripts.data_checks.date_gaps`

It prints counts only and saves `data\reports\date_gaps.json`, which also holds example row numbers per gap bucket. If it says "The index does not match the CSV", rerun `raw_index`. It takes `--block-mb` like `raw_index`.
