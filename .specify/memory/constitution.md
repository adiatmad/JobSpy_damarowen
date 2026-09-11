# JobSpy_damarowen Constitution

## Core Principles

### I. Preserve Existing User Value
Changes MUST preserve the existing job-search workflow unless a feature specification explicitly changes it. Prefer the smallest safe change over broad rewrites.

### II. Evidence Before Architecture
Technical decisions MUST be grounded in the current codebase, deployment constraints, and reproducible observations. Do not introduce infrastructure or dependencies merely because they are fashionable.

### III. Scraping Is an Unreliable External Boundary
Job-board availability, anti-bot controls, timeouts, HTTP errors, and proxy behavior MUST be treated as expected failure modes. The application MUST fail gracefully and MUST distinguish external-site blocking from application defects where practical.

### IV. Resource-Aware by Default
The application MUST remain conscious of constrained hosting resources. Expensive work should be bounded, avoid unnecessary duplication, and avoid algorithms whose cost grows unnecessarily with result volume.

### V. Test the User Journey
Every meaningful change MUST have a verifiable acceptance path covering the affected user workflow. Deployment configuration changes MUST be validated in the target environment, not only locally.

## Engineering Standards

- Keep business logic as independent from the Streamlit UI as reasonably practical.
- Pin or bound major dependency versions when deployment reproducibility benefits from it.
- Avoid adding persistent-storage assumptions to ephemeral hosting unless a persistent service is explicitly introduced.
- Prefer incremental refactoring with rollback-friendly commits.
- Documentation MUST describe important operational limitations, especially scraper blocking and hosting constraints.

## Change Governance

For non-trivial features, use the Spec Kit flow: specify -> clarify when needed -> plan -> tasks -> analyze -> implement -> converge. Small fixes may use the normal issue/PR workflow when a full specification would add more overhead than value.

The constitution is the governing project policy. A technical plan that conflicts with these principles MUST either be revised or explicitly record why an exception is justified.

Version: 1.0.0 | Ratified: 2026-09-11 | Last Amended: 2026-09-11
