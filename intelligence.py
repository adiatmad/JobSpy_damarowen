"""Explainable, deterministic job-ranking heuristics."""

from __future__ import annotations

import re

import pandas as pd

BROAD_LOCATIONS = {"indonesia", "indonesian", "id"}
LOCATION_STOPWORDS = {"area", "city", "kota", "kabupaten", "province", "provinsi", "indonesia"}
KNOWN_CITIES = (
    "jakarta", "surabaya", "bandung", "medan", "semarang", "yogyakarta",
    "tangerang", "bekasi", "depok", "bogor", "makassar", "palembang",
    "batam", "pekanbaru", "malang", "denpasar", "balikpapan", "samarinda",
    "banda aceh", "banjarmasin", "pontianak", "manado", "padang", "jambi",
    "bandar lampung", "mataram", "kupang", "solo", "surakarta",
)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.-]+", str(value).lower())
        if len(token) > 1 and token not in LOCATION_STOPWORDS
    }


def _canonical_city(value: str) -> str | None:
    """Extract a known Indonesian city without treating shared region words as a match."""
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
    for city in sorted(KNOWN_CITIES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(city)}\b", text):
            if city == "surakarta" and "solo" in text.split():
                return "solo"
            return "solo" if city == "surakarta" else city
    return None


def _location_matches(requested: str, actual: str) -> tuple[bool, bool]:
    """Return (matches, explicit_mismatch), preferring city identity over token overlap."""
    requested_raw = str(requested or "").lower().strip()
    actual_raw = str(actual or "").lower().strip()
    if not requested_raw:
        return False, False
    if any(re.search(rf"\b{re.escape(item)}\b", requested_raw) for item in BROAD_LOCATIONS):
        return True, False
    if not actual_raw:
        return False, False

    requested_city = _canonical_city(requested_raw)
    actual_city = _canonical_city(actual_raw)
    if requested_city and actual_city:
        return (True, False) if requested_city == actual_city else (False, True)
    if requested_city and not actual_city:
        return False, False

    requested_tokens = _tokens(requested_raw)
    actual_tokens = _tokens(actual_raw)
    if not requested_tokens or not actual_tokens:
        return False, False
    if requested_tokens <= actual_tokens:
        return True, False
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


def _relevance(title_hits: int, description_hits: int, query_tokens: set[str]) -> tuple[str, int, str | None]:
    if not query_tokens:
        return "Unknown", 0, None
    coverage = title_hits / len(query_tokens)
    if title_hits == len(query_tokens):
        return "Strong", 55, "keyword lengkap di judul"
    if title_hits > 0:
        return "Partial", max(20, int(coverage * 55)), "sebagian keyword di judul"
    if description_hits > 0:
        return "Weak", min(15, int((description_hits / len(query_tokens)) * 15)), "keyword muncul di deskripsi"
    return "Weak", 0, None


def score_jobs(df: pd.DataFrame, search_term: str, location: str = "") -> pd.DataFrame:
    """Rank jobs only from evidence in the query/result; no history-based scoring."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    result = df.copy()
    query_tokens = _tokens(search_term)
    scores, reasons, relevance_labels, location_labels = [], [], [], []

    for _, row in result.iterrows():
        title_tokens = _tokens(row.get("title", ""))
        description_tokens = _tokens(row.get("description", ""))
        location_match, location_mismatch = _location_matches(location, row.get("location", ""))
        freshness, freshness_reason = _freshness_points(row.get("posted_age_hours", pd.NA))
        title_hits = len(query_tokens & title_tokens)
        description_hits = len(query_tokens & description_tokens)
        relevance, relevance_points, relevance_reason = _relevance(title_hits, description_hits, query_tokens)
        score = relevance_points
        why = []
        if relevance_reason:
            why.append(relevance_reason)
        if title_hits == 0 and description_hits == 0 and query_tokens:
            score = min(score, 30)
        if location_match:
            score += 20
            why.append("lokasi cocok")
            location_labels.append("Match")
        elif location_mismatch:
            score -= 25
            why.append("lokasi berbeda")
            location_labels.append("Mismatch")
        elif location and not str(row.get("location", "")).strip():
            why.append("lokasi tidak diketahui")
            location_labels.append("Unknown")
        else:
            location_labels.append("Unknown")
        score += freshness
        if freshness_reason:
            why.append(freshness_reason)
        elif str(row.get("date_posted", "Unknown")) == "Unknown":
            why.append("tanggal tidak diketahui")
        if str(row.get("Work Type", "")).lower() == "remote":
            why.append("remote")

        scores.append(max(0, min(100, score)))
        reasons.append("; ".join(why) if why else "bukti kecocokan terbatas")
        relevance_labels.append(relevance)

    result["Match Score"] = scores
    result["Relevance"] = relevance_labels
    result["Why Match"] = reasons
    result["Location Match"] = location_labels
    return result.sort_values(["Match Score", "posted_age_hours", "date_posted"], ascending=[False, True, False], na_position="last").reset_index(drop=True)
