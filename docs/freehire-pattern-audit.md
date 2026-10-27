# freehire pattern audit for Teman Cari Kerja

**Status:** repository-level design audit; no runtime behavior changed by this document.

## Decision

Use `strelov1/freehire` as a source of narrowly scoped design patterns, not as an architecture to transplant. The repository's documented architecture is a Go monolith with PostgreSQL, Meilisearch, workers, and a web client. Teman Cari Kerja is a Python/Streamlit personal tool whose core deliberately uses JobSpy and SQLite without mandatory external services. Copying freehire's service topology would be disproportionate.

Reviewed references:
- [freehire architecture](https://github.com/strelov1/freehire/blob/main/docs/architecture.md)
- [freehire feature reference](https://github.com/strelov1/freehire/blob/main/docs/features.md)
- [Teman Cari Kerja README](https://github.com/adiatmad/JobSpy_damarowen/blob/main/README.md)
- [Local Job Memory retrieval PR #15](https://github.com/adiatmad/JobSpy_damarowen/pull/15)

## Pattern-by-pattern decision

| freehire pattern | JobSpy state observed | Decision |
|---|---|---|
| Provider adapters normalize into a common posting shape | JobSpy adapters and a separate pipeline already normalize, validate, freshness-filter, and deduplicate results. | **Keep current boundary.** Audit individual source failure/field contracts when a real defect is demonstrated; do not rewrite adapters. |
| Curated dictionaries for location, work mode, seniority, skills, and specialization | The current pipeline has a small known-city canonicalizer for fingerprints and passes through Work Type. The reviewed code does not demonstrate a maintained, evidence-backed taxonomy for seniority/skills. | **Potential future improvement, not ready for a broad implementation.** First define a small taxonomy and labeled examples. Unknown must remain unknown; never silently infer seniority or skill tags from weak text. |
| Stable job identity and idempotent ingestion | URL normalization, fingerprints, conservative deduplication, and SQLite records already exist. | **Do not replace identity logic.** Add regression examples only where an actual false merge or missed duplicate is demonstrated. |
| Durable job lifecycle and history | SQLite Job Memory stores sightings and application status. PR #15 proposes FTS5 retrieval over that memory. | **Finish and verify existing work first.** Do not build a second history/search subsystem. |
| Evidence-backed ghost-job signal | The current README explicitly excludes repost guesses/history-based scoring and says memory must not silently alter Match Score. | **Do not add a ghost-job verdict or ranking penalty.** If later justified, show raw observations (first/last seen, sighting count, source/date differences) separately from ranking, label them as clues, and test false-positive cases. |
| Search and facets backed by curated taxonomy | Current UI/search is a personal job-search workflow, not a large public catalogue. | **Defer.** Taxonomy upkeep and false negatives are real costs; implement only when the user's search examples show repeatable value. |
| Outboxes, worker fleet, PostgreSQL, Meilisearch, LLM enrichment | These solve freehire's production scale and multi-surface needs. | **Irrelevant to current scope.** No evidence supports adding them to the personal Streamlit app. |

## Highest-value next steps

1. Keep the local Job Memory retrieval change isolated and make its regression suite pass before merging. During this audit, PR #15's latest observed GitHub Actions run failed because the re-upsert test expected `GIS Analyst` not to match after changing the title to `Senior GIS Analyst`. That expectation is inconsistent with lexical AND search: both query terms still exist. The test has been corrected to remove those terms from the updated title/description; its new CI run must finish before the fix can be called verified.
2. Collect representative Indonesian and English job-title/location/work-mode examples from actual search results before defining any classification dictionary.
3. If the taxonomy experiment proceeds, require deterministic outputs, explicit unknowns, field-level evidence, and tests for ambiguous terms (e.g. “remote” appearing in a company name or description rather than describing work mode).
4. Keep freshness, evidence completeness, and source health separate from candidate-fit ranking. A missing field is a gap, not proof of a bad vacancy.

## Explicit non-goals

- Port freehire's stack or service architecture.
- Add LLMs, embeddings, vector databases, or paid APIs merely to imitate freehire.
- Label an employer or vacancy as fraudulent based on age or repeated sightings alone.
- Change Match Score using Job Memory history.
- Guess missing salary, seniority, location, or work mode.
- Add a broad taxonomy without labeled examples and an acceptance test set.

## Acceptance gate for any follow-up implementation

A follow-up is justified only if it:
- solves a demonstrated failure in real search results;
- has a small, documented input/output contract;
- preserves unknown/ambiguous values rather than guessing;
- has deterministic unit tests including counterexamples;
- does not change Match Score or persistence semantics unless a separate spec explicitly authorizes it;
- passes the full pytest suite and a Streamlit smoke test; and
- is reviewed as a minimal diff before merge.
