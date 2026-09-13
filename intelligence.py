"""Explainable, deterministic job-ranking heuristics.

This is intentionally not an AI match score yet. It only scores evidence that
is actually present in the search request/result, so the UI never invents fit.
"""

import re

import pandas as pd


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9+#.-]+", str(value).lower()) if len(token) > 1}


def score_jobs(df: pd.DataFrame, search_term: str, location: str = "") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    result = df.copy()
    query_tokens = _tokens(search_term)
    location_tokens = _tokens(location)
    scores, reasons = [], []
    for _, row in result.iterrows():
        title_tokens = _tokens(row.get("title", ""))
        text_tokens = _tokens(f"{row.get('title', '')} {row.get('description', '')} {row.get('location', '')}")
        title_hits = len(query_tokens & title_tokens)
        text_hits = len(query_tokens & text_tokens)
        location_hit = bool(location_tokens & _tokens(row.get("location", ""))) if location_tokens else False
        remote = str(row.get("Work Type", "")).lower() == "remote"
        score = 0
        why = []
        if query_tokens:
            score += min(60, int((title_hits / len(query_tokens)) * 60))
            score += min(20, int((text_hits / len(query_tokens)) * 20))
            if title_hits:
                why.append("keyword cocok di judul")
            elif text_hits:
                why.append("keyword muncul di deskripsi")
        if location_hit:
            score += 15
            why.append("lokasi cocok")
        if remote:
            score += 5
            why.append("remote")
        scores.append(min(100, score))
        reasons.append("; ".join(why) if why else "bukti kecocokan terbatas")
    result["Match Score"] = scores
    result["Why Match"] = reasons
    return result.sort_values(["Match Score", "date_posted"], ascending=[False, False], na_position="last").reset_index(drop=True)
