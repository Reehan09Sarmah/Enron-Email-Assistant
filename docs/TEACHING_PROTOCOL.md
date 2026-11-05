# Teaching protocol (study-card version)

Rex learns concepts in a **separate tutoring chat**, not in this session. This session decides *what* he needs to understand, checks that he does, then runs the decision and build steps. Run this loop for **every component** (data loader, cleaner, index, retriever, access filter, reranker, grounding check, agent loop, MCP server, approval gate, defence layer, eval runner, CI gate, and so on).

## The loop

### 1. Frame (≤ 5 lines)
Name the component, why it exists, what it connects to, and the decision(s) it needs. For retrieval, eval and guardrail components, also state **how we will know it works**: the metric, the test cases, and the current baseline number if one exists (eval-first).

### 2. Study card (instead of a lesson)
Issue a card in exactly this shape, in one fenced code block so Rex can copy it whole. Keep it **under ~30 lines**. Only include concepts Rex actually needs for the coming decision and to understand the code; check "Carried over" and "Concepts studied" in `PROGRESS.md` and do not repeat what he already knows.

```
STUDY CARD S<NN> — <component>   (project: Enron mail assistant)
Decision(s) coming: <ladder step, one line each>
Builds on: <accepted decisions this depends on, one line>
Project context (for the tutor): <2–4 lines: what exists, constraints that matter
  (CPU-only laptop, Flash-class API models, free-tier quotas, ~103k emails / 150 inboxes),
  what was already decided that this depends on>
Be clear on:
  1. <concept> — <what exactly Rex must be able to explain>
  2. ...  (3–6 items max)
Ready when you can answer:
  - <question that tests understanding, not recall>
  - <question about a trade-off or failure mode specific to this project>
Common traps: <1–3 misconceptions to watch for>
Sources I read (verified): <docs/papers/versions with sections>; unverified: <...>
```

Then stop and wait. Do not build, do not brief the decision yet.

### 3. Check (one question)
When Rex says `ready` (he may paste his notes or answers), ask **one** question from a different angle than the card's questions. If the answer is wrong or vague, name the gap in one or two lines and either give a ≤ 10-line correction or issue a short follow-up card; Rex chooses. `skip check` waives this once. Log the card as studied in `PROGRESS.md` ("Concepts studied").

### 4. Decision brief (only if a major decision is involved)
Use this exact shape:
- **Decision needed:** one sentence.
- **Builds on:** the accepted decisions and `DESIGN.md` requirements that constrain this one, and what they already rule out.
- **Estimates:** back-of-envelope numbers that bear on the choice (show the arithmetic), if any.
- **Options (2 to 4):** for each, what it is, what it makes easy, what it makes hard later, how it fails.
- **Constraints that matter here:** from `PROJECT_BRIEF.md`: budget, hardware, API quotas, learning goals.
- **How we would measure it** (when the choice affects quality, cost or safety): which number would tell us we chose wrong.
- **My recommendation:** clearly labelled as a recommendation, with reasoning. Then stop.

Rex may answer `teach me more` / `card` or choose. Ask "why this one?" and write the "why" yourself from his answer (standing instruction, `CLAUDE.md` rule 3).

### 5. Record
Write the decision file from `decisions/0000-template.md` (fill "What was studied first" with the card ID, and "Builds on" / "Unblocks"). Add it to the index in `decisions/README.md`. Update the owning section(s) of `docs/DESIGN.md` in the same step, and tick the ladder step in `PROGRESS.md`.

### 6. Build the smallest slice
- Smallest change that proves the concept works end to end.
- No extras. Anything worth doing later goes to "Open questions" in `PROGRESS.md`.
- Prefer showing raw behaviour (retrieved emails with scores, metric output, trace lines, wire messages) over describing it. Redact personal details in anything you print.

### 7. Walkthrough and verify
- Walk through the lines that carry the concept (briefly; Rex studied the theory already).
- Run it and show real output. Give Rex the command and one break-it experiment; do not block on him running it.
- Write the test that would have caught the failure mode named on the card. For retrieval, security and eval components, run the relevant eval and append the number to the Results log in `PROGRESS.md` with data version and config.

### 8. Close the loop
- Write 3 to 5 simple lines under "In Rex's words" in `PROGRESS.md` (standing instruction: you write them, not Rex). Fix wrong reasoning and explain the correction in your reply.
- Tick the component, add minor calls, log hours, set "Next session starts with".

## Session shape
- **Start:** read the four files listed in `CLAUDE.md`, restate in two lines where we are and how many budget hours are left, then either issue the next study card or continue where we stopped.
- **End:** run the full test suite (and the cheap, zero-LLM eval subset once it exists), update `PROGRESS.md`, list what Rex should now be able to explain, and one thing to revisit.

## Phase gate
A phase is done only when its components are ticked, all tests pass, the eval numbers it promised are recorded, `DESIGN.md` matches what was built (a short design review: you list any drift between the doc and the code, Rex decides how to resolve it), and Rex has answered one "defend it" question per decision made in that phase (asked as an interviewer would, with feedback). If the phase ran over budget, propose cuts from the cut list in `PROJECT_BRIEF.md`; Rex decides.

## Interview habit
Every decision file ends with a "30-second defence". Draft it in Rex's voice at the phase gate from his answer to the defend-it question.

## Style
Direct, concrete, no hype. Short paragraphs. Real code, real numbers, real (redacted) outputs. Never pad. Never flatter. If Rex is wrong, say so plainly and show why.
