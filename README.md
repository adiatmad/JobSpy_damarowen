# JobSpy — Personal Job Intelligence

JobSpy started as a Streamlit scraper. It is now being evolved into a **personal-first job-search intelligence tool**: discover jobs, normalize them, remember what has been seen, rank evidence-based matches, and track applications.

The same core is designed to remain deployable at $0 for personal use and to be usable by others later without prematurely building a multi-user SaaS stack.

## Current architecture

```text
Streamlit UI
    ↓
Search Engine
    ↓
Source adapters / JobSpy
    ↓
Validation + deduplication
    ↓
Explainable ranking
    ↓
SQLite Job Memory
```

### Main modules

- `app.py` — Streamlit presentation layer
- `scraper.py` — framework-agnostic JobSpy execution, retry and timeout handling
- `search_engine.py` — source orchestration and source-health reporting
- `pipeline.py` — validation, deduplication and data enrichment
- `intelligence.py` — deterministic, explainable job ranking
- `storage.py` — SQLite persistence for jobs, application status and search/source history
- `utils.py` — presentation helpers and existing search utilities
- `tests/` — automated regression tests

## Why SQLite?

SQLite keeps the personal deployment simple: no database server, no subscription, no credentials, and no infrastructure to maintain. If the project eventually needs multi-user scale, the storage boundary can be replaced without redesigning the search/intelligence core.

Local database files are intentionally ignored by Git.

## Source health

A failed source is not treated as the same thing as an empty source. JobSpy records states such as:

- `SUCCESS`
- `EMPTY`
- `BLOCKED`
- `RATE_LIMITED`
- `TIMEOUT`
- `PARSER_ERROR`
- `NETWORK_ERROR`
- `ERROR`

This matters because “no jobs found” and “the website blocked us” are completely different facts.

## Ranking philosophy

The current `Match Score` is deliberately **not an AI claim**. It uses evidence present in the search request and job result (keyword/title/location/work type) and displays a short explanation such as `keyword cocok di judul`.

Future CV/skills matching can be added later, but the system should never pretend to know a candidate's suitability without evidence.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Deployment philosophy

The application should remain portable:

1. **Local PC** — best control over scraping environment and $0.
2. **Streamlit Community Cloud** — simple public deployment when its shared execution environment is sufficient.
3. **Hybrid worker architecture** — if cloud IP reputation becomes the bottleneck, the UI and scraping worker can be separated later.

The project deliberately does not require PostgreSQL, Redis, Docker, authentication, or a paid hosting provider at this stage.

## Roadmap

### Foundation
- [x] Separate scraping from Streamlit
- [x] Source-level observability
- [x] SQLite job memory
- [x] Persistent application status
- [x] Explainable baseline ranking
- [x] Automated tests / CI

### Intelligence
- [ ] Cross-search “seen before” and repost detection
- [ ] Better freshness signals
- [ ] CV/skills-based matching
- [ ] Salary normalization
- [ ] Company and source reliability signals
- [ ] Application funnel analytics

### Discovery
- [ ] Search-engine/metasearch discovery inspired by SearXNG
- [ ] Career-page discovery
- [ ] Browser-crawler fallback inspired by Crawl4AI
- [ ] Adaptive rate/concurrency controls

### Public use
- [ ] Portable storage interface
- [ ] Optional API
- [ ] Optional multi-user isolation
- [ ] Low-cost deployment profile

## Design principles

Borrowed from the reference projects that informed this architecture:

- **Evidence over cleverness.**
- **Source failures are first-class data.**
- **Cheap retrieval before expensive browser automation.**
- **No source-specific scraping logic in the UI.**
- **Every useful result should be traceable to a source.**
- **Do not build multi-user infrastructure before real usage requires it.**
- **Do not add features merely because they are technically interesting.**
