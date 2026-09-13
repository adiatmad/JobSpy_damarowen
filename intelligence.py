"""Explainable, deterministic job-ranking heuristics.

The score is deliberately conservative: it rewards evidence that is actually
present in the search request/result and penalizes obvious contradictions.
"""

from __future__ import annotations

import re

import pandas as pd

BROAD_LOCATIONS = {"indonesia", "indonesian", "id"}
LOCATION_STOPWORDS = {"area", "city", "kota", "kabupaten", "province", "provinsi", "indonesia"}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.-]+", str(value).lower())
        if len(token) > 1 and token not in LOCATION_STOPWORDS
    }


def _location_matches(requested: str, actual: str) -> tuple[bool, bool]:
    """Return (matches, explicit_mismatch) for a user-supplied location."""
    requested_tokens = _tokens(requested)
    actual_tokens = _tokens(actual)
    if not requested_tokens:
        return False, False
    if requested_tokens & BROAD_LOCATIONS:
        return True, False
    if not actual_tokens:
        return False, False
    if requested_tokens & actual_tokens:
        return True, False
    return False, True


def _freshness_points(age_hours) -> tuple[int, str | None]:
    if pd.isna(age_hours):
        return 0, None
    age = float(age_hours)
    if age <= 24:
        return 10, "baru (<24 jam)"
    if age <= 72:
        return 7, "baru (<72 jam)"
    if age <= 168:
        return 3, "masih baru (<7 hari)"
    return 0, None


def score_jobs(
    df: pd.DataFrame,
    search_term: str,
    location: str = "",
    history: dict[str, dict] | None = None,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()

    result = df.copy()
    query_tokens = _tokens(search_term)
    history = history or {}
    scores, reasons = [], []

    for _, row in result.iterrows():
        title_tokens = _tokens(row.get("title", ""))
        description_tokens = _tokens(row.get("description", ""))
        text_tokens = _tokens(f"{row.get('title', '')} {row.get('description', '')}")
        title_hits = len(query_tokens & title_tokens)
        description_hits = len(query_tokens & description_tokens)
        location_match, location_mismatch = _location_matches(location, row.get("location", ""))
        freshness, freshness_reason = _freshness_points(row.get("posted_age_hours", pd.NA))

        score = 0
        why = []

        if query_tokens:
            title_coverage = title_hits / len(query_tokens)
            # Title evidence is the strongest signal. Description overlap is
            # capped separately and only counts tokens not already explained by
            # the title, preventing the old 60+20 double-counting bug.
            score += min(55, int(title_coverage * 55))
            extra_description_hits = len(query_tokens & (description_tokens - title_tokens))
            if extra_description_hits:
                score += min(15, int((extra_description_hits / len(query_tokens)) * 15))
            if title_hits == len(query_tokens):
                why.append("keyword lengkap di judul")
            elif title_hits:
                why.append("sebagian keyword di judul")
            elif description_hits:
                why.append("keyword muncul di deskripsi")

        if location_match:
            score += 20
            why.append("lokasi cocok")
        elif location_mismatch:
            score -= 25
            why.append("lokasi berbeda")

        score += freshness
        if freshness_reason:
            why.append(freshness_reason)
        elif row.get("date_posted", "Unknown") == "Unknown":
            why.append("tanggal tidak diketahui")

        work_type = str(row.get("Work Type", "")).lower()
        if work_type == "remote":
            # Remote is useful context, not an automatic quality bonus.
            why.append("remote")

        url = str(row.get("job_url", ""))
        previous = history.get(url, {})
        seen_count = int(previous.get("seen_count", 0) or 0)
        if seen_count > 0:
            score -= min(10, seen_count * 3)
            why.append(f"sudah terlihat {seen_count}x")

        scores.append(max(0, min(100, score)))
        reasons.append("; ".join(why) if why else "bukti kecocokan terbatas")

    result["Match Score"] = scores
    result["Why Match"] = reasons
    return result.sort_values(
        ["Match Score", "posted_age_hours", "date_posted"],
        ascending=[False, True, False],
        na_position="last",
    ).reset_index(drop=True)
