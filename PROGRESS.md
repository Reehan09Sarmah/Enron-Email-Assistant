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
Check the data one small check at a time (C1 to C4 first). Rex pastes his two Gemini keys into `.env` himself.

## Decisions
| # | Title | Date |
|---|---|---|
| 0001 | Project choice: permission-aware Enron mail assistant | 2026-10-22 |
| 0002 | Local parquet reader: pyarrow 26.0.0 | 2026-10-22 |

## Results log
One line per measured result: date, data version, check, number.

## Open questions
- The GitHub remote is still named `JobFit`. Reuse it (rename on GitHub) or start a new repo? Nothing is pushed until Rex decides.
- Ideas from the earlier plan, to reconsider during requirements, not decided: compare at least 4 search setups; MCP server; approval step before any action; automatic checks on every push; at least 15 prompt-injection test emails; AI-judge calibrated against Rex's labels.

## Small calls
- `requirements.txt` holds `pyarrow==26.0.0` (decision 0002).
- `.env` key names: `GEMINI_API_KEY_PAID` and `GEMINI_API_KEY_STUDENT`. `.env` is git-ignored; `.env.example` is tracked.
- Raw data sits in `data/raw/enron_qa_0922/`, covered by the `/data/` rule in `.gitignore`. It was downloaded by hand so no download library was added.
- Decision 0001 still says "no CUDA GPU". The laptop has an NVIDIA MX330 with 2 GB VRAM, too weak to plan around. Decisions are not edited, so this line is the correction.

## Hours
| Date | Hours | What |
|---|---|---|
