# Data notes

Facts about the EnronQA data and the Gemini API. Each fact says how it was checked. Nothing here is a decision.

## Source and version
- Paper: EnronQA, arXiv 2505.00263 (checked). It builds on the 2015 Enron release: 517,401 emails from 150 users.
- Paper's cleaning steps: 517k, then MinHash dedup 228k, subset removal 193k, quality filters 103.5k, language and NSFW filters about 102.6k. Some emails were added back, giving 103,638 emails and 528,304 question-answer pairs. The paper does not say how inboxes were chosen, whether mail is shared across inboxes, or how attachments are handled.
- Dataset used: Hugging Face `MichaelR207/enron_qa_0922`, the repo named in the paper's footnote (checked with the Hugging Face API, 2026-10-22).
- Commit sha: `c0b3a9190fd970e83cfbe7d399a08860e43e221e`, last modified 2024-09-22.
- Downloaded: 2026-10-22, by hand from the browser, to `data/raw/enron_qa_0922/` (git-ignored). Never edit the files there.
- Licence: not stated on the dataset repo (no licence field). The paper is CC BY 4.0, but that covers the paper, not necessarily the data. The Library of Congress warns that privacy rights may apply to the original corpus.
- Raw Kaggle CSV: not chosen as a data source (Rex, 2026-10-22). It is only probed by checks R1 to R6; see "Raw Kaggle data" below.
- Hugging Face discussions (read 2026-10-22, all 4 open):
  - #1: the owner (MichaelR207) says `include_email` is a leftover of an unpublished training experiment, randomly assigned, and can be ignored for retrieval.
  - #2: asks about "singlehop and multihop" questions (not read).
  - #3: "Licensing doubts". Two users ask whether the data is CC BY 4.0 like the paper. No reply from the owner.
  - #4: asks the same 73.8k vs 103,638 question as us. No reply.

## Files and hashes
Total download size 666,346,042 bytes, equal to the size the Hugging Face API reports. Each file starts and ends with the parquet marker `PAR1`. All four SHA-256 hashes equal the LFS sha256 values the Hugging Face API lists for the commit above (checked 2026-10-22), so the files are exactly the published ones.

| File | Bytes | SHA-256 |
|---|---|---|
| `dev-00000-of-00001.parquet` | 174,127,294 | `3661cb585657061c156a408b201afbb4adf94d2e20fd41cc172c26c582800185` |
| `test-00000-of-00001.parquet` | 161,772,154 | `9684fe7d459195ca0873616a28956a9498c88e819c0d2cd7f5196f14513143ee` |
| `train-00000-of-00002.parquet` | 152,601,618 | `9b1de19cd552d19625f691e21101028965099b8e98b24b896ef3e6e078f4c447` |
| `train-00001-of-00002.parquet` | 177,844,976 | `873329b234e713342dee769413d4974962e8a525dc50dfea5fbd15fc25b4af0a` |

## Structure
One row = one email plus its questions. There are 12 columns (checked with pyarrow 26.0.0, 2026-10-22):

| Column | Type | Meaning |
|---|---|---|
| `email` | string | Full email text, starting with a `Subject:` header |
| `path` | string | Where the email sat in the corpus; starts with the owner's name |
| `user` | string | The inbox owner (150 values) |
| `questions` | list | Questions written about this email |
| `rephrased_questions` | list | The same questions reworded |
| `gold_answers` | list | The correct answer to each question |
| `alternate_answers` | list | Other acceptable answers |
| `incorrect_answers` | list | Wrong answers (distractors) |
| `gold_rationales` | list | Why each gold answer is right |
| `alternate_rationales` | list | Reasons for the alternate answers |
| `include_email` | list | Leftover flag from an unpublished experiment; ignore for retrieval (see discussion #1) |
| `questions_count` | int64 | Number of questions for this email |

The types of the list columns beyond "list" were not recorded.

Parquet layout (pyarrow footers, 2026-10-22): dev 73,772 rows in 74 row groups; test 73,772 rows in 74; train 36,886 + 36,886 rows in 37 + 37. Each row group holds up to 1,000 rows (smallest 772).

## Raw Kaggle data
- File: `data/raw/enron_kaggle/emails.csv` (git-ignored through `/data/`), 1,426,122,219 bytes, SHA-256 `a605f0a2ca4a4feaa557eb0f2be825914906dca816066d7e58983e7e2e8bd274` (computed by `raw_index`, 2026-11-02).
- Columns: `file` (the mailbox path) and `message` (headers and body in one string).
- Which Kaggle page it came from, its version and its licence were not recorded.
- Never edited. The scripts read it in 16 MB blocks and keep only fingerprints in `data/work/raw_index.parquet`, a cache that can be rebuilt.

## What we know
- Three splits (train, dev, test) of 73,772 rows each, 12 columns (Hugging Face Dataset Viewer API, same commit as our files; footers agree).
- The `email` and `path` length statistics are identical in all three splits, and the per-user row counts are identical in all three splits. So the three splits appear to hold the same 73,772 emails and divide each email's questions between them. The split looks like a question split, not an email split.
- Questions per email: train 4.52 (range 2 to 11), dev 1.43 (1 to 3), test 1.21 (0 to 2). Total questions = 73,772 x (4.52032 + 1.43029 + 1.2107), about 528,304, which matches the paper.
- `user` has 150 values. Emails per user range from 5 to 5,485 (median 244).
- Email length ranges from 767 to 89,542 characters (median 1,664).
- 73,772 emails carry questions; the paper's corpus is 103,638 emails. So about 29,866 emails (29%) are not in this repo. Likely they are emails without a surviving question (unchecked).
- Sample check (Viewer API, 2026-10-22, 6 random offsets, seed 42, 3 requests each, 14 seconds): at every offset the email, path and user are identical in train, dev and test; no question text is shared between splits; all question, answer and rationale lists have equal length; the path owner equals `user`; every email starts with a `Subject:` header. Questions per email were 11/2/2, 5/2/2 and 3/1/1 (train/dev/test), so a heavily questioned email gives most of its questions to train. 6 of 6 passed. This is too small to be a proof.
- Memory (pyarrow 26.0.0, decision 0002): streaming only `user` across all 73,772 dev rows peaked at 37 MB. One batch of 1,000 `email` values (1.94 million characters) peaked at 49 MB.
- The three splits hold the same 73,772 emails, so one email is one (user, path) key repeated once per split (C2, C4, 2026-10-31).
- The raw CSV has 517,401 messages from 150 users. Every message has a Message-ID, Date and From header; 95.8% have To. Emails per user: 35 / 1,652 / 28,465 (min / median / max), against 5 / 240.5 / 5,485 in EnronQA. No message and no body is empty (R1, 2026-11-02).
- Every raw Message-ID is unique, so Message-ID cannot link copies across mailboxes (R2).
- All 73,772 EnronQA (user, path) keys match one raw `file` value exactly, and raw `file` values are unique, so `path` is a working join key. EnronQA holds 73,772 of the 517,401 raw messages (14.3%) (R3).
- The EnronQA body and the raw body of the same key are never identical: 0 of 73,772, also with whitespace collapsed (R3). R6 explains this: EnronQA adds a closing line to the end of the raw body (see "Check results R5-R6").
- The same body text often sits in several mailboxes. 17,236 of 243,509 distinct bodies are held by 2 or more users, and 5,252 of the 73,772 EnronQA dev emails (7.1%) have an exact copy with another user (R5). This counts exact copies after whitespace collapse only, so it is a lower bound.
- EnronQA's cleaning chose which emails to keep but did not edit their text, so its questions and answers fit the raw text. Evidence: in all 200 sampled pairs (seed 42) the raw body sits inside the EnronQA body after whitespace collapse (R6), and Rex confirmed by hand on one email that the extra tail is only a closing line of "=" characters. Limits: a sample of 200, containment and not exact equality, and nobody has compared the questions with the raw text (unchecked).
- The 3,106 questions shared by several splits all sit on different emails, never on the same email in two splits, so there is no test-to-dev leak through them (R4).

## What we do not know yet
- Whether the EnronQA body equals the raw body plus the closing line exactly. Only containment after whitespace collapse was tested, on 200 pairs. In 3 of them the shared start covers less than 90% of the raw length, and the length gap runs from 23 to 38 characters rather than a constant 37 or 38, so something besides the closing line may differ (unchecked). Rex checked one email by hand.
- How many of the 5,252 dev emails with a copy elsewhere are real forwarded or shared copies, and how many are short or generic text that several people wrote or received separately (unchecked). This matters for the access rule, because a copy held by another user is the same text in two mailboxes.
- How many copies exist beyond the exact ones. R5 counts exact copies only, and the paper's MinHash dedup also merged near-copies. Our 243,509 distinct bodies against the paper's 228k after dedup fits that, but the comparison is unchecked.
- How the 3,106 shared questions affect scoring. Of them, 2,389 occur on 2 different emails, 564 on 3 to 5, 104 on 6 to 10 and 49 on more than 10, so generic questions exist that have no single correct email. Whether those emails are near-copies of each other is unchecked.
- Why 29,866 emails are missing from this repo, and whether they matter. Only 14.3% of the raw messages are in EnronQA.
- The licence of the data, for both EnronQA and the Kaggle file.
- Whether the paper's 50 to 1,000 word filter makes this corpus cleaner than real mail, so that retrieval numbers look better than they would on real inboxes.
- Whether near-duplicates below the paper's 0.9 threshold make "one correct email per question" too strict.
- How much label noise the LLM-written questions carry.
- Rex's question of 2026-10-22: what if mistakes in this clean dataset snowball into later decisions? The join to the raw mail exists and, on a sample of 200, the EnronQA text matches the raw text apart from the closing line, so the text itself did not drift. Label noise in the questions is a separate unknown (above).

## API keys and tiers
- Keys: Rex has two Gemini API keys, one from a student Pro account and one from a paid Pro account. Names in `.env.example`: `GEMINI_API_KEY_PAID` and `GEMINI_API_KEY_STUDENT`. The values live only in `.env`.
- Google's terms (checked at https://ai.google.dev/gemini-api/terms): on the unpaid tier Google may use prompts and responses to improve its products and human reviewers may read them, and the terms say not to submit sensitive, confidential or personal information. The paid tier (a Cloud project with billing on) does not train on your data. Exception: in the EEA, Switzerland and the UK the paid terms apply to free use too.
- A consumer Pro subscription alone does not make API use paid. The API counts as paid only when the key's Cloud project has active billing (checked in the terms' definition). Whether either of Rex's projects has billing is unknown.
- Limits: the rate-limits page (https://ai.google.dev/gemini-api/docs/rate-limits) gives no fixed free numbers. It says limits depend on the account and are shown in AI Studio. Rex reads his own limits there; they are not recorded yet.
- Using two accounts to add up free quota may break Google's terms (from memory, unchecked). Check before relying on it.
- Enron mail has real people's details, so sending it to a free-tier key is a privacy question still to be settled.

## Check results (2026-10-31)
Scripts are in `scripts/data_checks/`, run with `python -m scripts.data_checks.<name>`. Full output is saved as JSON in `data/reports/` (git-ignored). Data: commit `c0b3a91…`. Nothing was changed in `data/raw/`. A row is named (file name, row index) in these checks; no email text is printed.

**C1 rows_well_formed.** All 221,316 rows in the 4 files were read. None breaks any of the 15 rules: the 8 list columns all have the length `questions_count`; no empty email, path, user, question or gold answer; every email starts with `Subject:`; every path starts with the row's user and `/`. Peak memory 630 MB, 13 s (all 12 columns, 1,000 rows per batch). No FINDING.

**C2 file_relationship.** Train, dev and test hold the same 73,772 (user, path) keys, each key once per split, and the email text is identical in all three splits. FINDING: 3,106 question fingerprints appear in more than one split, although the 6-offset sample check on 2026-10-22 saw none. Question fingerprints per split: train 329,940, dev 104,985, test 88,865. Peak memory 487 MB, 4 s.

**C3 duplicate_emails.** Used dev only, because C2 confirmed the splits hold the same emails. All 73,772 emails are different from each other, both by full text and with the `File:` line removed: 0 duplicate groups, so 0 groups across users and 0 within one user. Peak memory 348 MB, 2 s. No FINDING.

**C4 ids_and_headers.** Inside each split, `path` and (user, path) are unique. FINDING: across all 221,316 rows they repeat 147,544 times, which is 2 x 73,772, because each split repeats the same emails (the same fact as C2). Every split has 150 users, with 5 emails minimum and 5,485 maximum per user. FINDING: the median emails per user is 240.5 (the mean of the two middle users, 237 and 244), not 244; the earlier figure of 244 was probably the upper middle value. All 221,316 emails begin with the header block Subject, Sender, Recipients, File and then a line of `=`. The `File:` value contains the row's path in 100.0% of rows. The Recipients value is empty in 0.0% and contains `@` in 97.9% (216,696 rows). Peak memory 361 MB, 3 s.

Memory note: decision 0002 set 1 GB as the limit for one check; all four stayed under it. C1 is the highest because it reads all 12 columns.

## Check results R1-R4 (2026-11-02)
Rex ran these himself; the numbers come from the JSON files in `data/reports/`. Data: EnronQA commit `c0b3a91…` and the raw Kaggle CSV above. Nothing was changed in `data/raw/`. No email text was printed.

**raw_index.** The CSV was read in 16 MB blocks into an index of fingerprints: 517,401 rows, 85.1 s, peak memory 815 MB. This also gave the file size and SHA-256 above.

**R1 raw_shape.** 517,401 rows from 150 users. All rows have a Message-ID, Date and From header (100%); 495,554 (95.8%) have a To header. Emails per user: 35 minimum, 1,652 median, 28,465 maximum. 0 empty messages and 0 empty bodies. Peak memory 103 MB, 2.7 s. No FINDING.

**R2 raw_copies.** FINDING: every Message-ID is unique (517,401 distinct in 517,401 rows), so none appears in a second row or a second mailbox. Message-ID therefore cannot link copies across mailboxes in this corpus. The paper's dedup (517k to 228k) implies copies exist, so they must carry different Message-IDs. Peak memory 513 MB, 2.1 s.

**R3 join_to_enronqa.** All 73,772 EnronQA dev (user, path) keys match a raw `file` value, with no path fix needed, and no raw `file` value is shared by two rows. FINDING: 0 of 73,772 bodies are identical, also after collapsing whitespace. R6 later explained the cause: EnronQA adds a closing line to the raw body (see "Check results R5-R6"). EnronQA holds 73,772 of the 517,401 raw messages (14.3%); the other 443,629 messages from the same 150 users are not in it. Because Message-IDs are unique, all 73,772 matched emails show 0 other users holding a copy through Message-ID. Peak memory 675 MB, 9.6 s.

**R4 question_overlap.** The 3,106 shared questions from C2 were found again. FINDING: none of them sits on the same email in two splits (0 same-key cases), so there is no leak from test to dev through them; they all sit on different emails. A shared question occurs on 2 different emails in 2,389 cases, on 3 to 5 in 564, on 6 to 10 in 104 and on more than 10 in 49. So generic questions exist that have no single correct email. Peak memory 183 MB, 18.4 s.

## Check results R5-R6 (2026-11-02)
Rex ran these himself; the numbers come from `data/reports/body_copies.json` and `body_diff.json`. No email text was printed or saved.

**R5 body_copies.** The 517,401 rows hold 243,509 distinct bodies (whitespace collapsed). 226,273 bodies sit with one user only and 17,236 are held by 2 or more users: 11,184 by 2, 4,796 by 3 to 5, 756 by 6 to 10 and 500 by more than 10. By rows, 112,123 bodies appear once, 60,451 twice, 64,663 three to five times, 5,199 six to ten times and 1,073 more than ten times. The largest group has 112 copies across 95 users; among the 10 largest groups, the one spread over the most users has 110 copies across 105 users. 11 folder names contain "sent", holding 126,846 rows, and 61,283 bodies mix a sent folder with other folders. For the 73,772 EnronQA dev emails, 68,520 have no copy with another user and 5,252 (7.1%) do: 3,570 with 1 other user, 744 with 2, 564 with 3 to 5, 226 with 6 to 10 and 148 with more than 10. Exact copies only, so this is a lower bound. Peak memory 288 MB, 3.7 s. Expected "many", and the result agrees.

**R6 body_diff.** For 200 dev keys chosen with seed 42, all found in the raw CSV, the raw body is contained in the EnronQA body in all 200 pairs after whitespace collapse (0 the other way, 0 neither). EnronQA is longer in all 200, by 23 to 38 characters; 38 is the most common gap (59 pairs), then 37 (44), 36 (34) and 35 (21), so 37 or 38 covers 103 of 200. Similarity (first 10,000 characters, 3 pairs hit that cap) is 0.968 / 0.986 / 1.000 (min / median / max). The text shared at the start reaches at least 95% of the raw length in 182 pairs (approximate, because the raw length is counted before whitespace collapse), and only 3 pairs share 30 or more characters at the end, so the extra text mostly sits at the end. Peak memory 759 MB, 39.8 s.

Confirmed by Rex by hand (2026-11-02, one email): the extra tail is a closing line of 37 "=" characters, the same separator EnronQA puts after the header. FINDING: EnronQA did not cut or rewrite email text. Its body is the raw body plus this closing line. Exact equality after removing the line was not tested; containment was tested after whitespace collapse.
