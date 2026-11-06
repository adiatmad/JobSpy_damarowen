# Teman Cari Kerja — Engineering Constitution

## I. Evidence-first job information
A search result is evidence of a listing, not proof that a vacancy is still open, legitimate, or suitable. User-facing claims must reflect the source and verification level.

## II. Deterministic and explainable behavior
Ranking, freshness, identity, deduplication, and source-health outcomes must remain deterministic and explainable. Behavioral changes require explicit acceptance criteria and regression tests.

## III. Honest source health
Distinguish success, empty, blocked, rate-limited, timeout, parser error, network error, and generic error. Record actual attempts. A failed source must never be silently reported as an empty successful search.

## IV. Local-first privacy
Keep job history and memory local by default. Do not add telemetry, background uploads, or external processing of personal history without explicit user approval and a documented security review.

## V. Optional integrations stay optional
The core search workflow must not require an LLM, API key, browser service, or external infrastructure unless a specification explicitly changes the product contract.

## VI. Small, testable changes
Prefer vertical red-green-refactor slices, public-interface tests, cohesive modules, and minimal diffs. Avoid speculative abstractions and dependency growth.

## VII. Honest delivery
Inspect the final diff and run relevant tests. Report actual commands, results, skipped checks, and unverified live-source behavior.

## Governance
Use the existing `specs/` feature artifacts as the durable record. Amend this constitution only when the product-wide contract changes.
