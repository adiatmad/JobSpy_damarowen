# Feature Specification: freehire Pattern Audit

**Feature Branch**: `docs/freehire-pattern-audit`
**Created**: 2026-10-18
**Status**: Complete as a documentation-only audit

## Goal

Evaluate freehire patterns against Teman Cari Kerja's current architecture and record which ideas are reusable, already implemented, premature, or out of scope.

## User stories

### P1 — Avoid duplicate or disproportionate engineering

As the maintainer, I need an evidence-backed comparison so that I can reuse useful patterns without importing architecture or features that do not fit a personal Streamlit/SQLite tool.

**Acceptance scenarios**
- Given the current README and relevant source modules, when a pattern is reviewed, then the audit records the existing implementation and a clear adopt/defer/reject decision.
- Given a pattern that conflicts with an explicit project boundary, when it is evaluated, then the audit records the conflict and does not recommend silently overriding that boundary.

### P2 — Identify a safe next experiment

As the maintainer, I need concrete criteria for a future classification or evidence-signal improvement so that it can be tested without pretending uncertain data is fact.

**Acceptance scenarios**
- Unknown or ambiguous fields remain unknown.
- Any future taxonomy requires labeled examples and counterexample tests.
- Any future history signal remains separate from Match Score unless a new spec explicitly changes that contract.

## Constraints

- Documentation-only change; no runtime behavior, dependencies, schemas, ranking, or UI change.
- Existing source adapters, normalization, deduplication, Job Memory, Research Pack, and optional discovery remain unchanged.
- The audit must distinguish verified repository facts from proposed future work.

## Non-goals

- Porting freehire's architecture.
- Implementing a broad skills/seniority/location taxonomy in this audit.
- Implementing ghost-job scoring or labels.
- Changing Job Memory or ranking behavior.
