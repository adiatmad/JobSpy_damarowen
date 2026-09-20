# Job Intelligence Foundation

## Intent

JobSpy is a personal-first tool for finding **valid and current job information**. The product should surface useful evidence from multiple sources without pretending that search results are automatically verified vacancies or that an AI understands candidate suitability.

## User-visible requirements

### R1 — Search
- The user can search by job keyword, location, freshness window, country, and selected JobSpy sources.
- Source failures are distinguishable from empty results.
- A result keeps its source URL so the user can inspect the original listing.

### R2 — Validity boundaries
- Results must have a non-empty title and URL before entering the normalized result set.
- A requested freshness window excludes results with known dates outside the window.
- Unknown posting dates are excluded by default when a freshness window is active.
- The application must not claim that an unknown date is current.

### R3 — Evidence-based ranking
- Match scoring uses only observable result/query evidence: title keywords, description keywords, location, freshness, and explicit work-type evidence.
- Location matching must distinguish known city mismatches.
- Ranking must be deterministic and explainable.
- Ranking must not depend on prior sightings, application history, an LLM, or a hidden candidate profile.

### R4 — Job Memory
- SQLite stores job identity, first/last sighting timestamps, sighting count, source, and application status.
- Job Memory is historical persistence, not a ranking signal.
- Application status remains user-editable and does not imply that the application was actually submitted by the system.

### R5 — Financial context
- Nafkah UMR and estimated cost-of-living data remain available as contextual benchmarks.
- Missing salary information must remain explicitly unknown.
- Financial context must never be presented as guaranteed salary or disposable income.

### R6 — Discovery extensions
- SearXNG is an optional discovery layer. It must not replace source adapters that already provide structured job data.
- Career-page discovery may use a small bounded set of benign search operators (for example `inurl:careers`, `inurl:jobs`, and hiring-page phrases); these are query heuristics, not vacancy verification rules.
- External dork/query repositories are treated as design references and source catalogs, not runtime dependencies.
- Crawl4AI is an optional browser-rendering fallback for difficult discovery pages and is never required for the core application.
- Browser automation is opt-in and bounded; normal retrieval remains the default.
- Discovered results with unknown posting dates remain subject to the normal freshness rules.

## Explicit non-goals for this iteration

- LLM/AI candidate matching
- Automatic application submission
- Multi-user authentication or SaaS infrastructure
- Paid external services
- Making every search result a "verified vacancy"
- Ranking based on prior sightings or repost guesses

## Acceptance criteria

1. The search UI contains no Novelty, Seen-before, Possible-repost, or history-based score signal.
2. Re-running the same result with different Job Memory state produces the same Match Score.
3. Jakarta vs Surabaya is an explicit location mismatch when Jakarta is requested.
4. Job Memory still records repeated sightings and application status without changing Match Score.
5. SearXNG is inactive unless `SEARXNG_URL` is configured.
6. Crawl4AI is inactive unless `JOBSPY_CRAWL4AI` is explicitly enabled and the optional dependency is installed.
7. Core tests pass without SearXNG, Crawl4AI, or any LLM/API key.
8. README and development artifacts describe these boundaries accurately.
