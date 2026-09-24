# Loop Engineering

JobSpy adopts the useful engineering principles from Loop Engineering without adding the Loop CLI as a runtime dependency.

## Operating rules

1. **Design the loop before automating it.** Every recurring AI-assisted task needs a defined input, verifier, output, and persisted state.
2. **Start report-only.** Automation may inspect and propose changes before it is allowed to modify code or repository state.
3. **Prefer small bounded work units.** One experiment, one hypothesis, one measurable result.
4. **Verification is part of the loop.** Tests, benchmark checks, and human review are required before a change is considered successful.
5. **Persist state.** Record what was tested, what failed, and what remains unresolved so the next loop does not rediscover the same work.
6. **Escalate autonomy gradually.** L1 report-only → L2 assisted changes → L3 unattended only after the verifier has demonstrated reliability.
7. **Do not add companion tooling prematurely.** A tool is adopted only after a concrete recurring need is demonstrated.

## JobSpy application

For this repository, the loop is:

```text
SPEC → PLAN → small implementation/experiment → TEST → REVIEW → STATE update
  ↑                                                        │
  └──────────────────── next bounded loop ─────────────────┘
```

The LangExtract work follows this rule:

```text
20–30 real job descriptions
        ↓
fixed extraction schema
        ↓
baseline deterministic extraction
        ↓
optional LangExtract extraction
        ↓
compare grounded evidence
        ↓
human audit of disagreements
        ↓
KEEP / REJECT / REVISE
```

No LLM becomes part of the core runtime until the experiment demonstrates a material improvement that justifies its cost, latency, provider dependency, and failure modes.

## Current autonomy level

**L1 — report-only.** The experiment may generate measurements and recommendations. It must not alter ranking, eligibility, or vacancy validity automatically.
