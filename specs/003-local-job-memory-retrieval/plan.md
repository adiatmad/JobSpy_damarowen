# Implementation Plan: Local Job Memory Retrieval

## Approach

1. Extend `JobStore` with an FTS5 virtual table maintained alongside `jobs`.
2. Use `job_url` as the stable FTS row identity and keep the canonical job record in `jobs`.
3. Add deterministic query tokenization/escaping so user input cannot accidentally become raw FTS syntax.
4. Add retrieval APIs:
   - `search_memory`
   - `get_company_history`
   - `describe_memory`
   - `rebuild_memory_index`
5. Add a Job Memory UI search panel showing retrieval results and `Showing N of M`.
6. Keep retrieval separate from `score_jobs` and Research Pack generation.
7. Add tests before declaring the feature complete.

## Data model

FTS searchable fields:

- title
- company
- location
- source
- description
- work_type
- application_status

Stable identity:

- `job_url`

The FTS table is an index, not a second source of truth.

## Verification

- Run the full test suite.
- Verify a new in-memory/temporary SQLite database can initialize FTS5.
- Insert and re-upsert representative jobs.
- Verify exact company filtering and source/status/work-type filters.
- Verify total count is independent of the display limit.
- Verify existing Match Score tests remain unchanged.
- Verify the UI exposes retrieval relevance as retrieval relevance, never as Match Score.
