# Tasks: Render Free Deployment

Input: Design documents from `specs/001-render-free-migration/`

Prerequisites: `plan.md`, `spec.md`, `research.md`, `quickstart.md`

## Phase 1: Deployment Foundation

- [X] T001 Add `.python-version` pinned to Python 3.13 at repository root.
- [X] T002 Bound major dependency versions in `requirements.txt` without changing application dependencies.
- [X] T003 Add `render.yaml` defining a Free Python Web Service with the Streamlit build/start commands.

## Phase 2: Render Validation

- [ ] T004 Deploy `render-migration` as a Render Free Web Service and record the deployment URL.
- [ ] T005 Verify the Streamlit application starts successfully from a clean Render deployment.
- [ ] T006 Run a representative single-site search and record success, duration, and any scraper error.
- [ ] T007 Run a representative multi-site search and record success, duration, and any resource/runtime error.
- [ ] T008 Verify CSV export from a search that returns results.
- [ ] T009 Verify behavior after Render Free idle suspension and cold start.
- [ ] T010 If a supported site is blocked, test proxy configuration where appropriate and classify the failure as external blocking versus application/runtime failure.

## Phase 3: Evidence-Based Follow-up

- [ ] T011 Review the validation evidence against `spec.md` success criteria.
- [ ] T012 If concrete performance/resource bottlenecks are observed, create a separate feature specification for optimization or architecture decoupling; do not expand this migration scope implicitly.
- [ ] T013 If the migration is stable, update the README deployment documentation with the validated Render deployment path and known limitations.

## Dependencies

- T001-T003 are deployment prerequisites and are complete on `render-migration`.
- T004 depends on T001-T003.
- T005-T010 depend on T004.
- T011 depends on T005-T010.
- T012 and T013 depend on T011.

## Implementation Strategy

1. Finish deployment validation before touching application architecture.
2. Keep failures attributable: separate hosting/runtime issues from job-site blocking.
3. Only after evidence is collected, decide whether to optimize or keep the minimal migration.
