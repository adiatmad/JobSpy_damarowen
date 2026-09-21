# Implementation Plan

## Architecture

```text
Streamlit UI
    ↓
Search Engine
    ├── JobSpy source adapters
    └── optional SearXNG discovery
            ↓
      optional Crawl4AI rendering
            ↓
Validation / freshness / normalization
            ↓
Deduplication / identity
            ↓
Deterministic evidence scoring
            ↓
Nafkah enrichment
            ↓
SQLite Job Memory
```

## Design decisions

1. Keep Streamlit thin: no source-specific scraping logic in `app.py`.
2. Keep `search_engine.py` responsible for orchestration and source health.
3. Keep `pipeline.py` responsible for validation, normalization, deduplication, and financial enrichment.
4. Keep `intelligence.py` deterministic and history-independent.
5. Keep SQLite behind `JobStore` so persistence can change later without changing search/scoring logic.
6. Treat SearXNG as discovery, not proof of vacancy validity.
9. Use **Teman Cari Kerja** as the product name; retain **JobSpy** only when referring to the underlying structured source adapter/library.
7. Treat Crawl4AI as a bounded browser fallback, not the default transport.
8. Keep browser-discovery dependencies optional so the core remains easy to install and test.

## Quality gates

- Unit tests cover location identity, freshness, deduplication, deterministic scoring, source health, persistence, and optional discovery boundaries.
- CI runs the core test suite on Python 3.12.
- No external search service or browser is required for CI.
- The merge candidate must have no dead Novelty/history-ranking code.
- Manual smoke test must confirm a real search still produces source URLs, freshness filtering, financial context, and editable application status.
