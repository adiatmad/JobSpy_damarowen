# Feature Specification: Render Free Deployment

Feature Branch: `render-migration`

Created: 2026-09-11

Status: Draft

Input: Migrate the existing Streamlit Community Cloud deployment to Render Free with minimal application changes while preserving the current user workflow.

## User Scenarios & Testing

### User Story 1 - Deploy the existing app on Render Free (Priority: P1)

As the maintainer, I want the existing JobSpy Streamlit application to run on Render Free so that the application has a low-cost alternative hosting environment without requiring a major rewrite.

Why this priority: Deployment migration is the immediate goal and should be validated before deeper architectural changes.

Independent Test: Deploy the `render-migration` branch to a Render Free Web Service and load the application successfully through its public URL.

Acceptance Scenarios:

1. Given the repository branch contains the Render deployment configuration, When Render builds and starts the service, Then the Streamlit application becomes reachable through the assigned public URL.
2. Given the service is idle long enough for Render Free to suspend it, When a user opens the application again, Then the service can cold-start and become usable without manual intervention.

### User Story 2 - Preserve job-search functionality (Priority: P1)

As a user, I want to search for jobs using the existing interface so that migration does not remove the functionality I already use.

Why this priority: A successful deployment that cannot perform the existing search workflow is not a successful migration.

Independent Test: Run representative searches against one or more supported sites and verify that results are displayed and can be exported.

Acceptance Scenarios:

1. Given the application is running on Render, When a user searches a supported site such as Indeed, Then the application returns a result table or a clear scraper error.
2. Given search results are returned, When the user downloads CSV, Then the downloaded file contains the processed job results.
3. Given an external job site blocks or times out the Render request, When the scraper handles the failure, Then the application remains usable and reports the failure rather than crashing the whole session.

### User Story 3 - Validate operational limits before adopting Render (Priority: P2)

As the maintainer, I want to measure real search behavior on Render so that I can determine whether the free instance is adequate before changing the architecture further.

Why this priority: Render Free has constrained compute and ephemeral storage, while job scraping is network- and CPU-sensitive.

Independent Test: Execute progressively larger representative searches and record response time, failures, and observable resource-related symptoms.

Acceptance Scenarios:

1. Given a working deployment, When a single site is searched, Then response time and success/failure are observable.
2. Given multiple sites are selected, When the search completes or fails, Then the application remains responsive enough to diagnose the cause.
3. Given a site consistently returns blocking responses, When the same workflow is tested with an appropriate proxy, Then the result distinguishes site blocking from general hosting failure where possible.

## Functional Requirements

- FR-001: The repository MUST provide reproducible Render Web Service configuration for the application.
- FR-002: The deployment MUST use the repository's declared Python version and bounded dependency versions.
- FR-003: The application MUST bind Streamlit to the host and port supplied by the hosting environment.
- FR-004: Existing search inputs, site selection, result processing, and CSV export MUST remain available after migration.
- FR-005: Scraper timeout and retry behavior MUST remain bounded and MUST NOT be silently removed as part of the migration.
- FR-006: The migration MUST NOT require persistent local filesystem storage.
- FR-007: Deployment failures MUST be diagnosable from Render build/runtime logs and application behavior.
- FR-008: The migration MUST NOT be treated as proof that anti-bot or IP-blocking problems are solved; such failures MUST be evaluated separately from hosting capacity.

## Success Criteria

- SC-001: A clean deployment from `render-migration` starts successfully on Render Free.
- SC-002: The public application loads after initial deployment and after a Free-plan cold start.
- SC-003: At least one representative supported job site can be searched successfully, or an external blocking/error condition is clearly identified without crashing the app.
- SC-004: CSV export works for a search that returns results.
- SC-005: The migration requires no changes to the existing user-facing workflow beyond deployment/environment differences.
- SC-006: Any follow-up architecture work is justified by observed Render behavior rather than assumed limitations.

## Assumptions

- Render Free is being evaluated as an experiment, not yet declared the permanent production host.
- The current Streamlit architecture is retained initially to minimize migration risk.
- Proxy support remains available for sites that block shared hosting IP ranges.
- No database or persistent filesystem is required for the current feature set.

## Edge Cases

- Render cold starts may make the first request substantially slower than subsequent requests.
- A job site may block Render's shared IP independently of application correctness.
- A scraper may exceed the per-site timeout while other parts of the application remain healthy.
- Free-plan compute or memory constraints may become visible only with multi-site or high-result searches.
- Ephemeral filesystem behavior must not be relied upon for persistent user data.
