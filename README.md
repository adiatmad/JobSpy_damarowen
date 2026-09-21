# Teman Cari Kerja — Personal Job Intelligence

**Teman Cari Kerja** is a **personal-first job-search intelligence tool** for finding useful, current job information from multiple sources. It normalizes results, filters freshness, deduplicates listings, explains a deterministic match score, adds Nafkah financial context, and keeps a local job history.

The product goal is deliberately narrower than an AI career platform: **find and surface job information with traceable evidence**. A search result is not automatically a verified vacancy, and the app does not claim to know whether a job is suitable for a candidate beyond the evidence in the search request and listing.

## Architecture

```text
Streamlit UI
    ↓
Search Engine
    ├── JobSpy source adapters
    └── optional SearXNG discovery
            ↓
      optional Scrapling enrichment
            ↓
      optional Crawl4AI browser fallback
            ↓
Validation + freshness + URL normalization
    ↓
Conservative deduplication / job identity
    ↓
Deterministic evidence-based ranking
    ↓
Nafkah financial context
    ↓
SQLite Job Memory
```

### Main modules

- `app.py` — Streamlit presentation layer
- `scraper.py` — JobSpy execution, retry and timeout handling
- `search_engine.py` — source orchestration and source-health reporting
- `discovery.py` — optional SearXNG discovery, Scrapling enrichment, and Crawl4AI browser fallback
- `pipeline.py` — validation, freshness, URL normalization, deduplication and Nafkah enrichment
- `intelligence.py` — deterministic, history-independent job ranking
- `storage.py` — SQLite persistence for jobs, sighting history, application status, and source/search history
- `guide.py` — restored search strategy guide
- `tests/` — automated regression tests
- `specs/001-job-intelligence-foundation/` — living product spec, implementation plan, and task state

## Runtime

The supported core runtime is **Python 3.12**. `python-jobspy==1.1.82` is paired with NumPy 1.26.3 to keep dependency resolution predictable.

The core application does **not** require an LLM, API key, SearXNG instance, or browser automation.

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

Actual scraper attempt counts are persisted; a timeout is not silently reported as a successful retry.

## Freshness and validity boundaries

When a freshness window is requested, listings with a known posting date outside that window are removed. Listings with unknown dates are excluded by default because the application must not pretend that an unverified date is current.

Every retained result needs a non-empty title and URL. The original source URL remains available so the user can inspect the listing.

## Deduplication and ranking

Job URLs are normalized to remove common tracking parameters. Exact URL/title/company duplicates are removed, while near-duplicate matching is deliberately conservative so different vacancies at one company are not casually merged.

`Match Score` is **not an AI score**. It uses only observable evidence:

- keyword coverage in the title
- additional keyword evidence in the description
- location match or mismatch
- posting freshness
- explicit remote/work-type evidence

The score is deterministic and independent of Job Memory. There is intentionally no Novelty, Seen-before, Possible-repost, or history-based score penalty.

## Job Memory

SQLite stores:

- job URL and fingerprint
- title/company/location/source
- first and last sighting timestamps
- sighting count
- application status
- search/source history

Memory is for persistence and tracking; it does not silently alter the ranking of a job.

## Optional discovery extensions

### SearXNG

Set `SEARXNG_URL` to a SearXNG instance to add metasearch discovery to the normal JobSpy search. SearXNG is a **discovery layer**, not proof that a result is a valid vacancy.

SearXNG results with unknown posting dates remain subject to the normal freshness rules. If a freshness window is active, they are excluded unless the user explicitly allows unknown dates.

### Scrapling

Scrapling is an optional page-enrichment layer for discovered URLs. It is useful when the SearXNG result has only a short search snippet and the source page can provide stronger job evidence. It is explicitly opt-in and is attempted before Crawl4AI because it does not require a browser session for the normal fetch path.

Install the optional dependencies:

```bash
python -m pip install -r requirements-discovery.txt
```

Enable Scrapling explicitly:

```text
JOBSPY_SCRAPLING=1
```

Only a small bounded discovery sample is enriched. Scrapling does not replace the structured JobSpy source adapters, and enrichment does not turn a discovered page into a verified vacancy.

### Crawl4AI

Crawl4AI is an optional browser-rendering fallback for discovered pages that need JavaScript rendering. It is deliberately disabled by default. When both optional fetchers are enabled, Scrapling is tried first and Crawl4AI is used only if Scrapling fails.

Enable it explicitly:

```text
JOBSPY_CRAWL4AI=1
```

Only a small bounded discovery sample is rendered. Normal JobSpy retrieval remains the default path.

## Nafkah financial context

The UI retains the original **Nafkah** integration: UMR and estimated cost-of-living references are fetched from the Nafkah dataset with an offline fallback. These are contextual benchmarks, not guaranteed salary or disposable-income calculations.

Missing salary information remains explicitly unknown.

## Spec-driven development

This repository follows a lightweight Spec Kit-style flow for meaningful changes:

```text
specify → plan → tasks → implement → converge/review
```

The current living artifacts are under `specs/001-job-intelligence-foundation/`.

For an existing project, the important discipline is that the spec defines the intended change and its compatibility boundaries; it is not a retroactive description of every line of the existing system.

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

The application remains portable:

1. **Local PC** — maximum control over scraping environment and $0.
2. **Streamlit Community Cloud** — simple deployment when its shared execution environment is sufficient.
3. **Hybrid worker architecture** — if cloud IP reputation becomes the bottleneck, the UI and scraping worker can be separated later.

The project does not require PostgreSQL, Redis, Docker, authentication, or a paid hosting provider for the core personal workflow.

## Explicit non-goals

- LLM/AI candidate matching
- automatic application submission
- multi-user authentication or SaaS infrastructure
- paid external services
- treating every search result as a verified vacancy
- ranking jobs based on prior sightings or repost guesses

## Design principles

- **Evidence over cleverness.**
- **Source failures are first-class data.**
- **Cheap retrieval before browser automation.**
- **Optional page enrichment is bounded and opt-in.**
- **No source-specific scraping logic in the UI.**
- **Every useful result should be traceable to a source.**
- **Job Memory persists history but does not silently change ranking.**
- **Do not build multi-user infrastructure before real usage requires it.**
- **Do not add features merely because they are technically interesting.**

## AI-Assisted Development

This project was developed and/or maintained with AI assistance. AI was used to support parts of the design, implementation, documentation, and/or maintenance workflow. The human maintainer remains responsible for reviewing, validating, and approving the project's code and outputs.
