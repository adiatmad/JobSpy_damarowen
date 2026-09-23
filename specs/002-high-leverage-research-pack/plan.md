# Implementation Plan: High-Leverage Research Pack

## Approach

1. Add a pure-Python `opportunity.py` module for deterministic research queries and Markdown rendering.
2. Add a small Streamlit research-pack panel to the existing results flow.
3. Extend the restored Panduan Pencarian with the evidence-first research workflow.
4. Add unit tests before merge.
5. Keep the existing retrieval/ranking/storage architecture unchanged.

## Design constraints

- No new runtime dependency.
- No LLM or paid API.
- No automatic web fetching from the research-pack helper itself; generated queries are optional manual research leads.
- No history-based ranking changes.
- No automatic application/outreach behavior.

## Verification

- Run the full test suite.
- Manually search a real location and verify existing Nafkah and source-health behavior.
- Select one result and download the research pack.
- Confirm missing salary or evidence is shown as unknown/gap rather than inferred.
