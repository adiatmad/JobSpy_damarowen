# Multi-source job discovery

## Problem
The search UI defaults to Indeed and LinkedIn while other supported JobSpy adapters are either hidden or absent from the source selector. Google Jobs is exposed as a manual link rather than a normal selected scraper source. This makes the product feel narrower than its installed adapter capabilities.

## Goal
Make the installed JobSpy source coverage discoverable and usable, with Google Jobs configured using its dedicated query parameter, while preserving per-source health reporting and the current deterministic validation/ranking pipeline.

## In scope
- Expose all sources supported by the pinned python-jobspy 1.1.82 release: Indeed, LinkedIn, Google, ZipRecruiter, Glassdoor, Bayt, Naukri, and BDJobs.
- Make Google Jobs a default selected source and construct its query from role and location.
- Explain regional focus in the UI; keep region-specific sources opt-in.
- Keep source health and downstream validation/deduplication behavior unchanged.
- Add deterministic tests for source inventory and query argument construction.

## Out of scope
- Adding unsupported sources such as HelloWork without a compatible dependency.
- Claiming comprehensive job coverage or vacancy validity.
- Adding new scraping dependencies, LLM ranking, automatic applications, or history-based scoring.
- Replacing JobSpy adapters with custom scrapers.

## Acceptance criteria
1. The source selector includes exactly the eight source adapters documented by the pinned JobSpy v1.1.82 source enum.
2. Defaults include Indeed, LinkedIn, and Google Jobs.
3. Google source kwargs include a dedicated google_search_term containing the role and, when provided, location.
4. Google does not receive country_indeed; only Indeed and Glassdoor receive that parameter.
5. Region-specific source labels/help make their geographic focus visible.
6. Automated tests cover source inventory and query kwargs; existing tests continue to pass.
7. No changes are merged into main as part of this task.
