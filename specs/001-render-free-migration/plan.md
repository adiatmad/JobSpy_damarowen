# Implementation Plan: Render Free Deployment

Branch: `render-migration` | Date: 2026-09-11 | Spec: `specs/001-render-free-migration/spec.md`

## Summary

Migrate the existing Streamlit application from Streamlit Community Cloud to a Render Free Web Service with minimal application changes. Keep the current Streamlit UI and scraper execution model for the first deployment so that the migration tests the hosting environment rather than combining deployment migration with a broad rewrite.

## Technical Context

Language/Version: Python 3.13

Primary Dependencies: Streamlit, python-jobspy, pandas, rapidfuzz, requests

Storage: N/A; Render Free filesystem is ephemeral and the current app does not require persistent local storage.

Testing: Manual end-to-end deployment validation plus focused local/runtime checks as appropriate.

Target Platform: Render Free Web Service

Project Type: Streamlit web application

Performance Goals: Complete representative single-site searches within the existing bounded scraper timeout; preserve usability for multi-site searches sufficiently to evaluate whether further architecture changes are justified.

Constraints: Free-tier compute is limited; Render services sleep when idle; scraper sites can independently block shared hosting IPs; no persistent disk.

Scale/Scope: Small personal/public utility; initial goal is functional deployment and evidence gathering, not high-concurrency production hosting.

## Constitution Check

- Existing user workflow preserved: PASS
- Evidence before architecture: PASS; this plan intentionally validates Render before redesigning the scraper architecture.
- External scraping treated as unreliable: PASS
- Resource-aware implementation: PASS; bounded retries/timeouts and no persistent filesystem assumptions are retained.
- Test the user journey: PASS; deployment and representative search/export scenarios are defined in the specification.

## Architecture Decision

Retain the current single Streamlit process for the initial Render migration.

The current application directly executes scraping during the Streamlit interaction. This is not the ideal long-term architecture, but changing it at the same time as hosting migration would make failures difficult to attribute. If Render testing exposes CPU/memory, concurrency, or request-lifecycle limitations, a later feature can decouple the scraper into a service/worker architecture.

## Phase 0 - Research Findings

1. Render Free supports Python Web Services, requires binding to `0.0.0.0` and the supplied `$PORT`, and has constrained compute plus idle spin-down.
2. Render Free storage is ephemeral, so the application must not depend on local persistence.
3. Current JobSpy supports Python 3.10+ and proxy configuration, making Python 3.13 a conservative deployment target.
4. The current scraper already bounds each site attempt with a 60-second timeout and up to two attempts.
5. Anti-bot/IP blocking is an external dependency and will not necessarily be fixed by changing hosts.

## Phase 1 - Deployment Design

### Files

- `.python-version`: pin the deployment interpreter to Python 3.13.
- `requirements.txt`: bound major dependency versions to reduce unexpected breaking upgrades.
- `render.yaml`: declare the Render Web Service build and start commands.
- Existing application files remain unchanged during the initial migration.

### Runtime

Build command:

`pip install -r requirements.txt`

Start command:

`streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`

### Data Flow

Browser -> Streamlit on Render -> existing Streamlit scraper flow -> JobSpy -> external job sites -> pandas processing -> Streamlit results/CSV.

## Phase 2 - Validation

1. Deploy the branch to Render Free.
2. Verify the application loads.
3. Test one site first, preferably a site that historically works from shared environments.
4. Test a second site.
5. Test multi-site search.
6. Test CSV export.
7. Test a cold start after idle suspension.
8. Test proxy configuration if a site is blocked.
9. Record failures and determine whether they are deployment/resource failures or external-site blocking.

## Phase 3 - Follow-up Decision Gate

Do not refactor the architecture solely because Render is different from Streamlit Community Cloud.

Proceed to a separate optimization feature only if observed evidence shows one or more of:

- memory/CPU pressure;
- unacceptable request duration;
- poor reliability during concurrent users;
- Streamlit request lifecycle interfering with scraper execution;
- O(n²) deduplication becoming a material bottleneck;
- repeated external-data lookups becoming a material bottleneck.

## Project Structure

```text
JobSpy_damarowen/
├── app.py
├── scraper.py
├── pipeline.py
├── utils.py
├── requirements.txt
├── .python-version
├── render.yaml
└── specs/
    └── 001-render-free-migration/
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── quickstart.md
        └── tasks.md
```

## Risks

- Shared Render IP ranges may trigger job-site anti-bot controls.
- Free-tier resource limits may expose existing application inefficiencies.
- Dependency ranges may resolve to versions with behavior different from the original deployment.
- Streamlit and scraper execution remain coupled; this is intentionally accepted for the migration experiment.
