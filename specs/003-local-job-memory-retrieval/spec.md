# Feature Specification: Local Job Memory Retrieval

## Goal

Turn existing SQLite Job Memory into a first-class, inspectable lexical retrieval layer inspired by Leviathan's structured memory contract, without changing listing truth, deterministic Match Score semantics, or introducing an LLM/vector database.

## User stories

1. As a job seeker, I can search my historical job memory by role, company, location, source, or description terms.
2. As a job seeker, I can see how many records match and how many are being shown.
3. As a job seeker, I can inspect a company's historical job records without guessing what the company is.
4. As a maintainer, I can inspect the memory schema, searchable fields, counts, and date range.
5. As a maintainer, I can update/delete job records and have retrieval stay synchronized.

## Functional requirements

- SQLite FTS5 indexes searchable job fields from the existing `jobs` table.
- FTS retrieval returns stable job identity fields plus a relevance score suitable for retrieval ordering.
- Retrieval relevance must never be used as the existing `Match Score`.
- Search supports bounded result limits and optional exact filters for company, source, work type, and application status.
- Search reports both `shown_count` and `total_count`.
- Company history uses explicit normalized company selection rather than fuzzy guessing.
- Incremental job upserts refresh the FTS index without requiring a full rebuild.
- Existing records created before this feature are indexed during initialization/migration.
- A describe operation reports record count, date range, searchable fields, and index status.
- Empty/invalid queries return an explicit empty result rather than silently returning unrelated records.
- Core behavior requires only Python's existing SQLite support; no new runtime dependency.

## Evidence boundaries

- FTS/BM25 relevance means lexical retrieval relevance, not job suitability, vacancy validity, candidate fit, or hiring intent.
- Historical sightings are evidence that the application observed records; they are not proof that a vacancy is active or that a company has a strategy.
- Company history must not infer hiring plans from counts alone.

## Non-goals

- Replacing deterministic listing ranking.
- Vector embeddings or semantic search.
- LLM summarization.
- Automatic vacancy verification.
- Automatic repost detection.
- Candidate matching.
- Automatic outreach or applications.

## Acceptance criteria

1. Existing Match Score outputs remain unchanged by Job Memory retrieval.
2. A fresh database creates the FTS index automatically.
3. An existing database is migrated/indexed automatically.
4. Upserting a job makes it searchable immediately.
5. Re-upserting a job does not create duplicate searchable records.
6. Search exposes shown vs total counts.
7. Company history requires an explicit company value and does not silently fuzzy-match multiple companies.
8. Describe reports useful memory metadata.
9. Tests cover indexing, search, filters, counts, company history, migration/rebuild, and empty queries.
10. Existing core tests continue to pass.
