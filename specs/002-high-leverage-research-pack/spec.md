# Feature Specification: High-Leverage Research Pack

## Goal

Help the user turn a discovered vacancy into a small, evidence-first research task without adding an LLM, paid API, automatic outreach, or candidate-matching claims.

## User stories

1. As a job seeker, I can select one result and generate a research pack containing only evidence already present in the listing.
2. As a job seeker, I can get deterministic search queries for researching the company, role, hiring context, and current need.
3. As a job seeker, I can download the pack as Markdown for later notes.
4. As a maintainer, I can distinguish listing facts from questions that still require verification.

## Functional requirements

- Preserve listing fields when available: title, company, location, work type, posting date, source, salary-as-listed, match score, evidence coverage, evidence gaps, match explanation, and original URL.
- Never claim that a company is hiring, a vacancy is genuine, a business has an unmet need, or a person is a good fit unless the source data explicitly supports that statement.
- Generate research queries deterministically from available fields.
- Keep missing fields explicitly unknown rather than inferred.
- Work without an LLM, API key, SearXNG instance, or browser automation.
- Remain a research aid, not an application-submission or outreach automation system.

## Non-goals

- Candidate ranking beyond the existing deterministic listing score.
- Automatic outreach, applications, or founder contact.
- Automatic claims about company strategy, revenue impact, or hiring intent.
- Paid external research services.

## Acceptance criteria

- Selecting a result produces a Markdown research pack.
- Generated queries include company/role context when those fields exist.
- Unknown salary/date/evidence fields remain unknown.
- Tests cover deterministic query generation, conservative wording, and empty-input behavior.
- Existing retrieval, ranking, storage, Nafkah, SearXNG, Scrapling, Crawl4AI, and Panduan Pencarian behavior remains intact.
