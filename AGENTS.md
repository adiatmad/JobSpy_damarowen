# Agent instructions

Read this file before changing the repository. Inspect the current code, tests, README, configuration, and existing feature specs before proposing or implementing a change.

## Product and architecture constraints

- This is a personal-first job-search intelligence tool. Preserve its evidence-first scope; do not turn it into an AI career-advice platform without an explicit specification.
- A search result is not automatically a verified vacancy. Do not claim a job is current, suitable, safe, or available beyond the evidence actually collected.
- Preserve explicit source-health states (success, empty, blocked, rate-limited, timeout, parser/network/error) and real attempt counts. Never turn a failed source into an empty or successful source.
- Keep ranking deterministic and explainable. Do not add hidden model judgments or change scoring semantics without an accepted spec and regression coverage.
- Preserve the local-first job history and SQLite/FTS5 memory contracts. Treat user data as private; do not add telemetry or upload local history.
- Keep optional integrations optional. The core application must not acquire an LLM/API-key dependency merely to perform ordinary job search.

## Required engineering workflow

1. Inspect the repository state, relevant code, existing `specs/`, tests, and current behavior before editing.
2. For non-trivial work, define the user outcome, scope, non-goals, constraints, risks, and testable acceptance criteria in the existing feature-spec format. Do not create a parallel specification system.
3. Work in vertical red-green-refactor slices. Test behavior through public interfaces; avoid tests coupled to private implementation.
4. For difficult bugs, build a deterministic reproduction that fails on the reported symptom, minimise it, rank falsifiable hypotheses, instrument narrowly, and add a regression test at the correct seam.
5. Prefer cohesive modules, explicit boundaries, the smallest viable diff, and no speculative abstractions or unnecessary dependencies.
6. Review the change separately against the accepted spec and repository standards. Check for scope creep, data leakage, false vacancy claims, and altered ranking/source-health semantics.
7. Run relevant tests and inspect the final diff. Report exact commands and results; distinguish automated checks from live source behavior. Never claim a test ran when it did not.

## Quality gates

- Apply the full Anti-Slop core in `antislop.md`; reject generic copy, invented metrics, decorative UI, boilerplate, and unnecessary abstractions.
- For Streamlit UI changes, use UI/UX Pro Max when installed, while preserving the existing product direction. Check responsive behavior, keyboard/focus, empty/loading/error states, and actual interactions.
- Model multi-step work as a dependency graph; parallelise only independent tasks and keep the critical path and verification checkpoints explicit.
- Never weaken tests, silently change persisted-data formats, commit credentials, or upload local user history.
