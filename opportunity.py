"""Deterministic research-pack helpers inspired by evidence-first job hunting."""

from __future__ import annotations

import re
from typing import Mapping
from urllib.parse import quote_plus


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, "")
    if value is None:
        return ""
    return str(value).strip()


def _clean_query_part(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_research_queries(row: Mapping[str, object]) -> list[str]:
    """Build search queries; never claim that any query result is evidence."""
    title = _clean_query_part(_text(row, "title"))
    company = _clean_query_part(_text(row, "company"))
    location = _clean_query_part(_text(row, "location"))

    if not title and not company:
        return []

    queries: list[str] = []
    if company:
        queries.extend(
            [
                f'"{company}" careers jobs',
                f'"{company}" "{title}"' if title else f'"{company}" jobs',
                f'"{company}" news product customers',
            ]
        )
    if title and location:
        queries.append(f'"{title}" "{location}" hiring')
    elif title:
        queries.append(f'"{title}" hiring')
    return queries


def build_research_brief(row: Mapping[str, object], search_term: str = "", search_location: str = "") -> str:
    """Render a conservative, evidence-only research brief in Markdown."""
    title = _text(row, "title") or "Unknown role"
    company = _text(row, "company") or "Unknown company"
    url = _text(row, "job_url") or ""
    source = _text(row, "site") or _text(row, "source") or "Unknown source"
    location = _text(row, "location") or "Unknown"
    posted = _text(row, "date_posted") or "Unknown"
    work_type = _text(row, "Work Type") or "Unknown"
    salary = _text(row, "Gaji Asli") or "Not stated"
    score = _text(row, "Match Score") or "Unknown"
    coverage = _text(row, "Evidence Coverage") or "Unknown"
    gaps = _text(row, "Evidence Gaps") or "Not recorded"
    why = _text(row, "Why Match") or "Not recorded"
    description = _text(row, "description")

    queries = build_research_queries(row)
    query_lines = "\n".join(f"- `{q}`" for q in queries) or "- No query could be generated from the available fields."

    evidence = [
        f"- Role: {title}",
        f"- Company: {company}",
        f"- Location: {location}",
        f"- Work type: {work_type}",
        f"- Posted: {posted}",
        f"- Source: {source}",
        f"- Salary as listed: {salary}",
        f"- Match score: {score}",
        f"- Evidence coverage: {coverage}",
        f"- Evidence gaps: {gaps}",
        f"- Why match: {why}",
    ]

    if search_term or search_location:
        evidence.append(f"- Search context: {search_term or '—'} / {search_location or '—'}")

    description_note = "Available" if description else "Missing from result"

    return "\n".join(
        [
            f"# Research Pack — {title} @ {company}",
            "",
            "> This pack separates listing evidence from research questions. It does not verify that a vacancy is genuine, open, or a good career choice.",
            "",
            "## 1. Listing evidence",
            *evidence,
            f"- Description: {description_note}",
            f"- Original listing: {url or 'Unavailable'}",
            "",
            "## 2. Questions to verify",
            "- Is the role still active on the original source?",
            "- Is the company hiring for this role directly, or through an intermediary/aggregator?",
            "- What concrete team, product, customer, or operational problem does this role support?",
            "- What evidence shows the need is current rather than a stale/reposted listing?",
            "- What would success in the first 30–90 days be expected to change?",
            "",
            "## 3. Company and role research queries",
            query_lines,
            "",
            "## 4. Evidence discipline",
            "- Treat search snippets as leads, not proof.",
            "- Prefer the original company career page, official company material, and the original job listing when verifying claims.",
            "- Record the date and URL for any external evidence you find.",
            "- Do not turn an absence of evidence into a claim that the company lacks something.",
            "",
            "## 5. High-leverage next step",
            "1. Verify the listing and company evidence.",
            "2. Identify one concrete business/team need supported by evidence.",
            "3. Check whether your own experience contains a real, verifiable example relevant to that need.",
            "4. Decide whether to apply, contact someone, or simply keep the listing in your tracker.",
        ]
    )


def build_google_research_links(row: Mapping[str, object]) -> list[tuple[str, str]]:
    """Return human-readable Google links for optional manual research."""
    return [(query, f"https://www.google.com/search?q={quote_plus(query)}") for query in build_research_queries(row)]
