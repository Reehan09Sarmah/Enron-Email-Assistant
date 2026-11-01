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
6. If `raw_index` says a message is bigger than the block, rerun it with `--block-mb 32`.
   If memory for `python.exe` goes above 1 GB, press Ctrl+C and tell Claude in the chat.
7. Results are saved as JSON in `data\reports\`. The index is `data\work\raw_index.parquet`
   and can be rebuilt at any time.
