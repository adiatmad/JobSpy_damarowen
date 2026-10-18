# Plan: Multi-source job discovery

1. Treat the pinned JobSpy v1.1.82 Site enum as the contract for available sources.
2. Centralize supported source identifiers, display labels, and concise coverage guidance in the source adapter module.
3. Expand the Streamlit selector without changing the existing per-source health pipeline.
4. Pass a dedicated google_search_term to Google's JobSpy adapter.
5. Add tests for source inventory, Google query construction, and country argument boundaries.
6. Document regional limitations and the difference between JobSpy Google results and manual Google links.
7. Run GitHub Actions and review the resulting diff before considering this change complete.
