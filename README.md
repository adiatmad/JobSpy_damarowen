# JobSpy — Personal Job Intelligence

JobSpy started as a Streamlit scraper. It is now being evolved into a **personal-first job-search intelligence tool**: discover jobs, normalize them, remember what has been seen, rank evidence-based matches, compare financial context, and track applications.

The same core is designed to remain deployable at $0 for personal use and to be usable by others later without prematurely building a multi-user SaaS stack.

## Current architecture

```text
Streamlit UI
    ↓
Search Engine
    ↓
Source adapters / JobSpy
    ↓
Validation + freshness + deduplication
    ↓
Explainable evidence ranking
    ↓
Nafkah financial context
    ↓
SQLite Job Memory / application tracker
```

### Main modules

- `app.py` — Streamlit presentation layer
- `scraper.py` — framework-agnostic JobSpy execution, retry and timeout handling
- `search_engine.py` — source orchestration and source-health reporting
- `pipeline.py` — validation, freshness filtering, URL normalization, deduplication and Nafkah enrichment
- `intelligence.py` — deterministic, explainable job ranking
- `storage.py` — SQLite persistence for jobs, sightings, application status and search/source history
- `utils.py` — presentation helpers and existing search utilities
- `tests/` — automated regression tests

## Runtime

The current supported runtime is **Python 3.12**. `python-jobspy==1.1.82` currently requires NumPy 1.26.3, so the project pins the compatible stack rather than allowing dependency resolution to wander into a source-build failure.

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

Actual scraper attempt counts are persisted; a timeout is not silently reported as a successful second attempt.

## Freshness and deduplication

When a freshness window is requested, listings with a known posting date outside that window are removed. Listings with unknown dates are excluded by default because the application should not pretend that an unverified date satisfies a freshness requirement; the UI provides an explicit opt-in if the user wants them.

Job URLs are normalized to remove common tracking parameters. Exact URL/title/company duplicates are removed, while near-duplicate matching is deliberately conservative so different vacancies such as multiple Management Trainee departments at one company are not casually merged.

## Ranking philosophy

The current `Match Score` is deliberately **not an AI claim**. It uses only evidence present in the current search request and job result:

- keyword coverage in the title
- additional keyword evidence in the description
- location match or mismatch
- posting freshness

Application history, sightings, and novelty are **not relevance evidence** and do not change the Match Score. They remain in Job Memory / the application tracker where they belong.

The implementation follows a useful pattern from the OpenJev/SemIf projects without depending on either project: keep decisions structured, auditable, and explicit about their evidence instead of generating prose and parsing it back into logic. Those projects are references for architecture, not runtime dependencies for JobSpy.

Future CV/skills matching can be added later, but the system should never pretend to know a candidate's suitability without evidence.

## Nafkah financial context

The UI retains the original **Nafkah** integration from `main`: UMR and estimated cost-of-living references are fetched from the Nafkah dataset with an offline fallback. These figures are contextual benchmarks, not guaranteed salary or personal-budget advice.

The result table and CSV expose the financial fields again, and the UI links to the Nafkah simulator for deeper cost-of-living exploration.

## Running locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

For tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
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
- [x] Freshness filtering
- [x] Conservative URL/title/company deduplication
- [x] Nafkah financial context restored
- [x] Automated tests / CI
- [x] Keep relevance scoring independent from application history

### Intelligence
- [ ] Near-duplicate/repost identity across different source URLs
- [ ] Better freshness/repost signals
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

Borrowed selectively from the reference projects and our Spec Kit / Anti-Slop workflow:

- **Define the job before changing code.**
- **Collect evidence before making a claim.**
- **Evidence over cleverness.**
- **Prefer typed/structured decisions over generated text that must be parsed.**
- **Source failures are first-class data.**
- **Cheap retrieval before expensive browser automation.**
- **No source-specific scraping logic in the UI.**
- **Every useful result should be traceable to a source.**
- **Keep historical tracking separate from current-search relevance.**
- **Do not build multi-user infrastructure before real usage requires it.**
- **Do not add features merely because they are technically interesting.**
