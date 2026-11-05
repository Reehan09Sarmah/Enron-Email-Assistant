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

## Running R8 (same_message_check) and filling the audit file
Close heavy apps first, and watch `python.exe` in Task Manager. It reads the CSV twice (once for all groups, once for the 80 audit groups), so it takes about 3 minutes. If memory goes above 900 MB, press Ctrl+C and tell Claude in the chat. A smaller `--block-mb 8` uses less memory but stops with a message if one email is bigger than the block.

`.\.venv\Scripts\python.exe -m scripts.data_checks.same_message_check`

It prints counts only and saves `data\reports\same_message_check.json`. It also writes `data\audit\same_message_audit.csv`, a local file with the real sender, subject, date and recipients of 80 sampled groups (30 with a whole-hour gap, 30 with another gap under 24 hours, 20 with a gap of a day or more). That file stays on your laptop (git-ignored); do not share it or paste it into the chat.

To fill it in:
1. Open `E:\PROJECTS\Email Assistant\data\audit\same_message_audit.csv` in Excel (double-click, or Excel > Data > From Text/CSV and choose UTF-8).
2. Each audit group is a block of rows with the same `audit_group` number. Read the rows of a block together and decide: are these copies of the same message, or different messages?
3. Type `same` or `different` in the `rex_label` column on the first row of each block only. Leave the other rows empty.
4. Save with Ctrl+S and choose to keep the CSV format (CSV UTF-8 if offered), then close Excel. Tell Claude in the chat that the file is filled in; Claude counts the labels without printing any text.
