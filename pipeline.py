"""Framework-agnostic normalization, freshness, deduplication and enrichment."""

from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
import requests
from rapidfuzz import fuzz

NAFKAH_RAW_URL = "https://raw.githubusercontent.com/adenaufal/nafkah/main/data/umr.json"
FALLBACK_NAFKAH = {
    "jakarta": {"umr": 5067381, "cost": 3500000},
    "surabaya": {"umr": 4725479, "cost": 2800000},
    "bandung": {"umr": 4209309, "cost": 2600000},
    "medan": {"umr": 3769082, "cost": 2400000},
    "semarang": {"umr": 3243969, "cost": 2200000},
    "yogyakarta": {"umr": 2492997, "cost": 1800000},
    "tangerang": {"umr": 4760289, "cost": 3000000},
    "bekasi": {"umr": 5219263, "cost": 3200000},
    "depok": {"umr": 4878612, "cost": 3000000},
    "bogor": {"umr": 4813988, "cost": 2900000},
    "jawa tengah": {"umr": 2036947, "cost": 1700000},
    "jawa barat": {"umr": 2057495, "cost": 1800000},
    "jawa timur": {"umr": 2165244, "cost": 1800000},
}

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "referrer", "trk", "trackingid",
}
_COMMON_COMPANY_WORDS = {"pt", "tbk", "inc", "ltd", "llc", "corp", "corporation", "co", "company"}


def normalize_job_url(value: str) -> str:
    """Normalize common tracking noise so the same job URL deduplicates reliably."""
    if not value or pd.isna(value):
        return ""
    raw = str(value).strip()
    try:
        parts = urlsplit(raw)
        if not parts.scheme or not parts.netloc:
            return raw.rstrip("/").lower()
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in _TRACKING_PARAMS]
        host = parts.netloc.lower()
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), host, path, urlencode(query), "")).lower()
    except ValueError:
        return raw.rstrip("/").lower()


def _fingerprint_text(value: str, *, company: bool = False) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token and (not company or token not in _COMMON_COMPANY_WORDS)]
    return " ".join(tokens)


def job_fingerprint(row) -> str:
    """Stable, conservative identity for repost detection across different URLs."""
    title = _fingerprint_text(row.get("title", ""))
    company = _fingerprint_text(row.get("company", ""), company=True)
    location = _fingerprint_text(row.get("location", ""))
    if not title or not company:
        return ""
    return "|".join((title, company, location))


@lru_cache(maxsize=1)
def fetch_nafkah_data() -> dict:
    """Fetch Nafkah reference data once per process; safely fall back offline."""
    try:
        response = requests.get(NAFKAH_RAW_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        formatted = {}
        for item in data:
            key = str(item.get("city", "")).strip().lower()
            if key:
                formatted[key] = {"umr": item.get("umr", 0), "cost": item.get("estimated_cost", 0)}
        return formatted or FALLBACK_NAFKAH
    except (requests.RequestException, ValueError, TypeError):
        return FALLBACK_NAFKAH


def get_clean_financial_info(location_str: str) -> tuple[str, str]:
    if not location_str or pd.isna(location_str):
        return "-", "-"
    loc_clean = str(location_str).lower()
    if "remote" in loc_clean:
        return "-", "-"
    for city_key, info in fetch_nafkah_data().items():
        if city_key in loc_clean:
            umr_fmt = f"Rp {info['umr'] / 1e6:.2f}M" if info["umr"] else "-"
            cost_fmt = f"Rp {info['cost'] / 1e6:.2f}M" if info["cost"] else "-"
            return umr_fmt, cost_fmt
    return "-", "-"


def _salary_midpoint(description: str) -> float | None:
    """Return a conservative monthly salary midpoint in rupiah when parseable."""
    if not description or pd.isna(description):
        return None
    text = str(description).lower().replace(".", "").replace(",", "")
    juta_ranges = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|–|sampai)\s*(\d+(?:\.\d+)?)\s*(?:juta|jt)", text)
    if juta_ranges:
        low, high = map(float, juta_ranges[0])
        return ((low + high) / 2) * 1_000_000
    juta_single = re.search(r"(\d+(?:\.\d+)?)\s*(?:juta|jt)", text)
    if juta_single:
        return float(juta_single.group(1)) * 1_000_000

    rp_ranges = re.findall(r"(?:rp|idr)\s*(\d+)\s*(?:-|–|sampai)\s*(?:rp|idr)?\s*(\d+)", text)
    if rp_ranges:
        low, high = map(float, rp_ranges[0])
        return (low + high) / 2
    rp_single = re.search(r"(?:rp|idr)\s*(\d+)", text)
    if rp_single:
        return float(rp_single.group(1))
    return None


def extract_real_salary(description: str) -> str:
    if not description or pd.isna(description):
        return "Gaji dirahasiakan"
    patterns = [
        r"(?:rp|IDR)\s?[\d\.\,]+\s?[-–]\s?(?:rp|IDR)?\s?[\d\.\,]+",
        r"\b\d{1,2}\s?[-–]\s?\d{1,2}\s?(?:juta|jt)\b",
        r"(?:rp|IDR)\s?[\d\.\,]+",
        r"\b\d{1,2}\s?(?:juta|jt)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, str(description), re.IGNORECASE)
        if match:
            return match.group(0)
    return "Gaji dirahasiakan"


def _parse_posted_dates(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return parsed timestamps and an age estimate in hours."""
    raw = series.astype(str).str.strip()
    parsed = pd.to_datetime(raw, errors="coerce", utc=True, format="mixed")
    date_only = raw.str.fullmatch(r"\d{4}-\d{2}-\d{2}").fillna(False)
    effective = parsed.copy()
    effective.loc[date_only & parsed.notna()] += pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    now = pd.Timestamp.now(tz="UTC")
    age_hours = (now - effective).dt.total_seconds() / 3600
    age_hours = age_hours.where(age_hours.notna(), pd.NA).clip(lower=0)
    return parsed, age_hours


def validate_jobs(
    df: pd.DataFrame,
    hours_old: int = 0,
    *,
    include_unknown_dates: bool = False,
) -> pd.DataFrame:
    """Normalize required fields and enforce the requested freshness window."""
    if df is None or df.empty or "title" not in df.columns or "job_url" not in df.columns:
        return pd.DataFrame()

    valid_df = df.dropna(subset=["title", "job_url"]).copy()
    valid_df["title"] = valid_df["title"].astype(str).str.strip()
    valid_df["job_url"] = valid_df["job_url"].map(normalize_job_url)
    valid_df = valid_df[(valid_df["title"] != "") & (valid_df["job_url"] != "")]

    if "company" not in valid_df.columns:
        valid_df["company"] = "Perusahaan Tidak Disebutkan"
    valid_df["company"] = valid_df["company"].fillna("Perusahaan Tidak Disebutkan").astype(str).str.strip()
    if "location" not in valid_df.columns:
        valid_df["location"] = ""
    valid_df["location"] = valid_df["location"].fillna("").astype(str).str.strip()

    if "date_posted" in valid_df.columns:
        parsed, age_hours = _parse_posted_dates(valid_df["date_posted"])
        valid_df["date_posted"] = parsed.dt.strftime("%Y-%m-%d").fillna("Unknown")
        valid_df["posted_age_hours"] = age_hours
    else:
        valid_df["date_posted"] = "Unknown"
        valid_df["posted_age_hours"] = pd.NA

    if hours_old and hours_old > 0:
        known = valid_df["posted_age_hours"].notna()
        fresh = known & (valid_df["posted_age_hours"] <= int(hours_old))
        if include_unknown_dates:
            fresh |= ~known
        valid_df = valid_df[fresh].copy()
    return valid_df.reset_index(drop=True)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _job_key(row) -> str:
    return f"{_clean_text(row.get('title', ''))}|{_clean_text(row.get('company', ''))}"


def _location_key(row) -> str:
    return _clean_text(row.get("location", ""))


def deduplicate_jobs(df: pd.DataFrame, threshold: int = 95) -> pd.DataFrame:
    """Remove URL/exact duplicates and conservative near-duplicates."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    kept, seen_urls, seen_keys, retained = [], set(), set(), []
    for _, row in df.iterrows():
        url = normalize_job_url(row.get("job_url", ""))
        key = _job_key(row)
        title, company, location = _clean_text(row.get("title", "")), _clean_text(row.get("company", "")), _location_key(row)
        if not url or url in seen_urls or key in seen_keys:
            continue
        duplicate = False
        for previous_title, previous_company, previous_location in retained:
            if company != previous_company or fuzz.ratio(title, previous_title) < threshold:
                continue
            if location and previous_location and fuzz.ratio(location, previous_location) < 85:
                continue
            duplicate = True
            break
        if duplicate:
            continue
        kept.append(row)
        seen_urls.add(url)
        seen_keys.add(key)
        retained.append((title, company, location))
    result = pd.DataFrame(kept).reset_index(drop=True)
    if not result.empty:
        result["job_url"] = result["job_url"].map(normalize_job_url)
    return result


def categorize_work_type(row) -> str:
    text = f"{row.get('title', '')} {row.get('location', '')} {row.get('description', '')}".lower()
    if row.get("is_remote") is True or "remote" in text or "work from home" in text or "wfh" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    return "On-site"


def _financial_signal(location: str, description: str) -> str:
    salary = _salary_midpoint(description)
    if salary is None:
        return "⚪ Gaji tidak diketahui"
    umr_text, cost_text = get_clean_financial_info(location)
    umr = next((float(x) * 1_000_000 for x in re.findall(r"Rp\s*([\d.]+)M", umr_text)), None)
    cost = next((float(x) * 1_000_000 for x in re.findall(r"Rp\s*([\d.]+)M", cost_text)), None)
    if not umr or not cost:
        return "⚪ Gaji terdeteksi; acuan lokasi tidak tersedia"
    surplus = salary - cost
    if salary < umr:
        level = "🔴 di bawah UMR"
    elif surplus >= cost:
        level = "🟢 kuat vs biaya hidup"
    else:
        level = "🟡 moderat vs biaya hidup"
    return f"{level} · estimasi gaji {extract_real_salary(description)}"


def process_job_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare presentation/export fields without owning UI state."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "Work Type" not in df.columns:
        df["Work Type"] = df.apply(categorize_work_type, axis=1)
    if "Sudah Dilamar" not in df.columns:
        df["Sudah Dilamar"] = False

    summaries, financials, salaries, umrs, costs, signals = [], [], [], [], [], []
    for _, row in df.iterrows():
        work_type, loc = row.get("Work Type", "On-site"), row.get("location", "Indonesia")
        description = row.get("description", "")
        salary = extract_real_salary(description)
        umr, cost = get_clean_financial_info(loc)
        summaries.append(f"{work_type} | {loc}\n{salary}")
        financials.append(
            f"UMR {umr} | Est. Hidup {cost}"
            if umr != "-" or cost != "-"
            else ("Remote (Biaya bervariasi)" if "remote" in str(loc).lower() else "Cek acuan di Nafkah")
        )
        salaries.append(salary)
        umrs.append(umr)
        costs.append(cost)
        signals.append(_financial_signal(loc, description))

    df["Lokasi & Gaji"] = summaries
    df["Acuan Finansial"] = financials
    df["Gaji Asli"] = salaries
    df["Info UMR"] = umrs
    df["Est. Biaya Hidup"] = costs
    df["Financial Signal"] = signals
    if "job_fingerprint" not in df.columns:
        df["job_fingerprint"] = df.apply(job_fingerprint, axis=1)
    return df
