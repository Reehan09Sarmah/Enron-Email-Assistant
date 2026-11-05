# Decision records

One file per major decision, named `NNNN-short-slug.md` (copy `0000-template.md`). A decision is written **after Rex chooses and before the code is written**.

Rules:
- The "Why" section is written by Claude in simple language from what Rex said (his short quote is kept). If Rex's reasoning is wrong, Claude corrects it in the file and explains the fix. Rex does not have to write or approve the wording (standing instruction, 2026-10-18).
- Claude's recommendation and whether Rex followed it are always recorded.
- Decisions that affect quality, cost or safety say how we would measure that the choice was wrong.
- Decisions are never edited away. If one changes, write a new file and mark the old one `superseded by NNNN`.
- Decisions from the earlier JobFit project were removed in the reset; they are kept only in the local git tag `v1-jobfit-archive`, which is never pushed.

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| 0001 | Project choice: permission-aware Enron mail assistant | accepted | 2026-10-22 |
| 0002 | Local parquet reader: pyarrow 26.0.0 | accepted | 2026-10-22 |
| 0003 | Progress bars with tqdm 4.70.1 | accepted | 2026-11-02 |
| 0004 | Requirements and limits set now | accepted | 2026-11-06 |
| 0005 | Data: search EnronQA now, full raw corpus later | accepted | 2026-11-06 |
| 0006 | Storage of the frozen dataset: Parquet via pyarrow | accepted | 2026-11-06 |
