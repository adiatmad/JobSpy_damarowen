# Research: Render Free Deployment

Date: 2026-09-11

## Decision 1: Keep the Streamlit architecture for the first migration

Decision: Do not split the scraper into a separate API/worker during the hosting migration.

Rationale: The current application couples the Streamlit interaction with JobSpy execution. Introducing a second service would change deployment, request handling, and failure modes simultaneously. A minimal migration gives clearer evidence about what Render itself changes.

## Decision 2: Use Python 3.13

Decision: Pin the deployment interpreter to Python 3.13.

Rationale: Current JobSpy packaging supports modern Python 3 versions, and Render's current default may move independently. Pinning 3.13 reduces interpreter drift while remaining conservative for the dependency set.

## Decision 3: Bound dependency major versions

Decision: Use major-version upper bounds in `requirements.txt` rather than leaving all dependencies completely open-ended.

Rationale: A deployment migration should not accidentally become a dependency-major-version migration. Exact lockfiles can be introduced later if reproducibility requires them.

## Decision 4: Treat blocking as a separate problem

Decision: Keep proxy support and classify HTTP/Cloudflare-style failures separately from hosting failures.

Rationale: Moving from one shared cloud host to another does not guarantee a clean IP reputation with LinkedIn, Indeed, Google, JobStreet, or other sites. The scraper's external boundary remains inherently unreliable.

## Decision 5: Do not introduce persistent storage

Decision: No database or persistent disk is part of this migration.

Rationale: The current application does not require persistent server-side state for its core workflow, and Render Free storage is ephemeral.

## Evidence Sources

- Render Web Service and Free-tier documentation: https://render.com/docs/free
- Render Web Services documentation: https://render.com/docs/web-services
- Render Python version documentation: https://render.com/docs/python-version
- python-jobspy package metadata: https://pypi.org/project/python-jobspy/
