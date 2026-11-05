# Design doc: permission-aware Enron mail assistant

_Living document, written like an engineering RFC. Each section is filled in when the decision that owns it is accepted, and links to that decision. Nothing here is written ahead of a decision. Sections still empty show where the design is not yet settled._

**Status:** skeleton (2026-10-22). **Owner:** Rex. **Decisions:** see `decisions/README.md`.

## 1. Problem and context
_(from Decision 0001; see `docs/PROJECT_BRIEF.md`, "Business context")_

## 2. Goals and non-goals
- Goals: _pending (requirements decision)_
- Non-goals: _pending_

## 3. Requirements
### 3.1 Functional (user stories)
_pending_
### 3.2 Non-functional targets (each with a number and how it is measured)
| Property | Target | Measured by | Decision |
|---|---|---|---|
| Cross-user leakage | 0 documents | leakage suite, CI gate | 0001 (fixed requirement) |
| Retrieval quality | _pending_ | | |
| Latency per query (p50 / p95) | _pending_ | | |
| Cost per query | _pending_ | | |
| Injection success rate | _pending_ | | |
| Indexing time / memory on the laptop | _pending_ | | |

## 4. Constraints and back-of-envelope estimates
_Corpus size, chunk counts, vector memory, embedding time (Colab vs CPU), API calls per eval run vs free-tier quota. Each estimate shows its arithmetic and is later checked against a real measurement._

## 5. Data
### 5.1 Source, version, licence, manifest
### 5.2 Data contract (schema, invariants, verified properties)
### 5.3 Access model (who may see which email)
### 5.4 Splits (dev / test / LLM-eval subset)

## 6. Architecture
### 6.1 Overview diagram
_Offline (ingest and index) path vs online (query) path; trust boundaries marked._
### 6.2 Components and interfaces
_Each component's input/output contract, so implementations can be swapped and compared (e.g. one retriever interface, many retrievers)._

## 7. Key flows
### 7.1 Ingest and index
### 7.2 Answer a question
### 7.3 Draft a reply (consequential action, approval)

## 8. Retrieval design
_Chunking, indexes, fusion, reranking, filters; the comparison table and why the chosen config won._

## 9. Access control design
_Where enforcement happens and why; how identity is bound; leakage tests._

## 10. Generation, grounding and the agent loop
_Provider interface, loop, state, stop conditions, citations, grounding check._

## 11. Security
_Threat model, trust boundaries, defence layers with before/after numbers, PII redaction, secrets._

## 12. Evaluation
_Metrics, datasets, judge and its calibration, gates._

## 13. Observability and operations (LLMOps)
_Trace schema, cost and latency accounting, caching, quotas, CI._

## 14. Failure modes
| Failure | Effect | Detection | Mitigation |
|---|---|---|---|

## 15. Alternatives considered
_One line per rejected option, linking to its decision._

## 16. Open questions and risks
