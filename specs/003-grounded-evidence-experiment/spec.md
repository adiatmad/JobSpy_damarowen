# Spec 003 — Grounded Evidence Extraction Experiment

## Status

Experiment only. No production integration.

## Problem

Job descriptions contain useful requirements and work-type evidence in unstructured text. JobSpy currently relies on deterministic observable fields and should not replace those guarantees with probabilistic inference.

## Goal

Measure whether grounded extraction with LangExtract provides materially better structured evidence than a small deterministic baseline, without changing JobSpy ranking, eligibility, freshness, or vacancy-validity logic.

## Scope

Extract only facts explicitly stated in the job description:

- skills / tools
- minimum years of experience
- education requirements
- work arrangement
- location requirements
- salary information when explicitly stated
- employment type when explicitly stated

Each extracted item must retain source evidence/span information when the provider supports it.

## Non-goals

- candidate matching
- eligibility decisions
- vacancy verification
- company strategy inference
- hiring-intent inference
- automatic application decisions
- replacing deterministic JobSpy scoring
- requiring Gemini or another specific model provider

## Experiment design

Use 20–30 real job descriptions collected from JobSpy's existing workflow. Freeze the dataset before comparison.

For each description:

1. Run the deterministic baseline.
2. Run LangExtract with the same fixed schema.
3. Compare normalized facts against a human-reviewed reference set.
4. Record precision, recall, unsupported claims, grounding quality, latency, and operational cost.
5. Review every disagreement manually.

## Decision rule

LangExtract may proceed to an optional feature only if the experiment shows a meaningful improvement in evidence recall/coverage without introducing unacceptable unsupported claims or operational cost.

A good-looking demo is not sufficient evidence.

## Safety boundary

LangExtract output is evidence, not truth. Production code must never use an extraction result by itself to mark a job eligible, verified, current, or suitable.
