"""Framework-agnostic normalization and enrichment for job results."""

import re
from functools import lru_cache

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


@lru_cache(maxsize=1)
def fetch_nafkah_data() -> dict:
    """Fetch reference data once per process; safely fall back offline."""
    try:
        response = requests.get(NAFKAH_RAW_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        formatted = {}
        for item in data:
            key = str(item.get("city", "")).strip().lower()
            if key:
                formatted[key] = {
                    "umr": item.get("umr", 0),
                    "cost": item.get("estimated_cost", 0),
                }
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


def extract_real_salary(description: str) -> str:
    if not description or pd.isna(description):
        return "Gaji dirahasiakan"
    patterns = [
        r"(?:rp|IDR)\s?[\d\.\,]+\s?[-–]\s?(?:rp|IDR)?\s?[\d\.\,]+",
        r"\b\d{1,2}\s?[-–]\s?\d{1,2}\s?(?:juta|jt)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, str(description), re.IGNORECASE)
        if match:
            return match.group(0)
    return "Gaji dirahasiakan"


def validate_jobs(df: pd.DataFrame, hours_old: int = 0) -> pd.DataFrame:
    """Normalize the minimum fields required by the application."""
    if df is None or df.empty or "title" not in df.columns or "job_url" not in df.columns:
        return pd.DataFrame()
    valid_df = df.dropna(subset=["title", "job_url"]).copy()
    valid_df["title"] = valid_df["title"].astype(str).str.strip()
    valid_df["job_url"] = valid_df["job_url"].astype(str).str.strip()
    valid_df = valid_df[(valid_df["title"] != "") & (valid_df["job_url"] != "")]
    if "company" not in valid_df.columns:
        valid_df["company"] = "Perusahaan Tidak Disebutkan"
    valid_df["company"] = valid_df["company"].fillna("Perusahaan Tidak Disebutkan").astype(str).str.strip()
    if "date_posted" in valid_df.columns:
        parsed = pd.to_datetime(valid_df["date_posted"], errors="coerce", utc=True)
        valid_df["date_posted"] = parsed.dt.strftime("%Y-%m-%d").fillna("Unknown")
    else:
        valid_df["date_posted"] = "Unknown"
    return valid_df.reset_index(drop=True)


def _job_key(row) -> str:
    title = re.sub(r"\s+", " ", str(row.get("title", "")).strip().lower())
    company = re.sub(r"\s+", " ", str(row.get("company", "")).strip().lower())
    return f"{title}|{company}"


def deduplicate_jobs(df: pd.DataFrame, threshold: int = 85) -> pd.DataFrame:
    """Remove URL/exact duplicates, then use fuzzy matching as a fallback."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    kept = []
    seen_urls = set()
    seen_keys = set()
    seen_pairs = []
    for _, row in df.iterrows():
        url = str(row.get("job_url", "")).strip().lower()
        key = _job_key(row)
        if not url or url in seen_urls or key in seen_keys:
            continue
        if any(fuzz.ratio(key, previous) >= threshold for previous in seen_pairs):
            continue
        kept.append(row)
        seen_urls.add(url)
        seen_keys.add(key)
        seen_pairs.append(key)
    return pd.DataFrame(kept).reset_index(drop=True)


def categorize_work_type(row) -> str:
    text = f"{row.get('title', '')} {row.get('location', '')} {row.get('description', '')}".lower()
    if row.get("is_remote") is True or "remote" in text or "work from home" in text or "wfh" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    return "On-site"


def process_job_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare presentation/export fields without owning UI state."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "Work Type" not in df.columns:
        df["Work Type"] = df.apply(categorize_work_type, axis=1)
    if "Sudah Dilamar" not in df.columns:
        df["Sudah Dilamar"] = False
    summaries, financials, salaries, umrs, costs = [], [], [], [], []
    for _, row in df.iterrows():
        work_type = row.get("Work Type", "On-site")
        loc = row.get("location", "Indonesia")
        salary = extract_real_salary(row.get("description", ""))
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
    df["Lokasi & Gaji"] = summaries
    df["Acuan Finansial"] = financials
    df["Gaji Asli"] = salaries
    df["Info UMR"] = umrs
    df["Est. Biaya Hidup"] = costs
    return df
