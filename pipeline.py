import re
import pandas as pd
from rapidfuzz import fuzz

def validate_jobs(jobs: pd.DataFrame, hours_old: int) -> pd.DataFrame:
    """Membersihkan lowongan yang tidak lengkap atau kadaluwarsa."""
    if jobs.empty:
        return jobs

    for col in ("title", "company"):
        if col in jobs.columns:
            jobs = jobs[jobs[col].notna() & (jobs[col].astype(str).str.strip() != "")]

    if "job_url" in jobs.columns:
        jobs = jobs[jobs["job_url"].notna() & (jobs["job_url"].astype(str).str.strip() != "")]

    if hours_old and hours_old > 0 and "date_posted" in jobs.columns:
        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(hours=int(hours_old))
        parsed_dates = pd.to_datetime(jobs["date_posted"], errors="coerce")
        stale_mask = parsed_dates.notna() & (parsed_dates < cutoff)
        jobs = jobs[~stale_mask]

    return jobs

def detect_ats_friendly(url: str) -> str:
    """Mendeteksi apakah link mengarah langsung ke portal ATS cepat."""
    if not isinstance(url, str) or not url:
        return "Standard Form"
    url_lower = url.lower()
    ats_domains = ["greenhouse.io", "lever.co", "smartrecruiters.com", "bamboohr.com", "workable.com"]
    for domain in ats_domains:
        if domain in url_lower:
            return "⚡ Quick Apply (ATS)"
    return "Standard Form"

def categorize_work_type(row) -> str:
    """Mengkategorikan sistem kerja menjadi Remote, Hybrid, atau On-site."""
    is_remote = str(row.get("is_remote", "")).lower()
    location = str(row.get("location", "")).lower()
    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()

    if is_remote in ["true", "1"] or "remote" in location or "remote" in title:
        return "🌐 Remote"
    elif "hybrid" in location or "hybrid" in title or "hybrid" in description[:300]:
        return "🏢 Hybrid"
    return "📍 On-site"

def deduplicate_jobs(df: pd.DataFrame, threshold: float = 85.0) -> pd.DataFrame:
    """Menggabungkan lowongan serupa menggunakan Fuzzy Matching."""
    if df.empty:
        return df

    df["clean_title"] = df["title"].astype(str).str.lower().str.strip()
    df["clean_company"] = df["company"].astype(str).str.lower().str.strip()
    
    # Hapus duplikat persis lebih awal
    df = df.drop_duplicates(subset=["clean_title", "clean_company", "location"]).copy()

    indices_to_drop = set()
    rows = df.to_dict('records')
    n = len(rows)

    for i in range(n):
        if i in indices_to_drop:
            continue
        for j in range(i + 1, n):
            if j in indices_to_drop:
                continue

            comp_sim = fuzz.ratio(rows[i]["clean_company"], rows[j]["clean_company"])
            title_sim = fuzz.ratio(rows[i]["clean_title"], rows[j]["clean_title"])

            if comp_sim >= threshold and title_sim >= threshold:
                indices_to_drop.add(j)

    cleaned_df = df.drop(index=list(indices_to_drop)).copy()
    cleaned_df.drop(columns=["clean_title", "clean_company"], inplace=True)
    return cleaned_df

def calculate_match_score(df: pd.DataFrame, target_keywords_str: str, exclude_keywords_str: str) -> pd.DataFrame:
    """Menghitung tingkat kecocokan skill dan menyaring kata kunci yang dihindari."""
    if df.empty:
        return df

    target_keywords = [k.strip() for k in target_keywords_str.split(",") if k.strip()]
    exclude_keywords = [k.strip().lower() for k in exclude_keywords_str.split(",") if k.strip()]

    # Filter Exclude Keywords
    if exclude_keywords:
        pattern = "|".join([re.escape(k) for k in exclude_keywords])
        df = df[~df["title"].astype(str).str.lower().str.contains(pattern, regex=True)].copy()

    if not target_keywords or df.empty:
        df["Match Score"] = 100
        df["Matched Skills"] = "Semua Tampil"
        return df

    scores = []
    matched_list = []

    for _, row in df.iterrows():
        title = str(row.get("title", "")).lower()
        desc = str(row.get("description", "")).lower()

        found_in_title = 0
        found_in_desc = 0
        matched_words = []

        for kw in target_keywords:
            kw_clean = kw.lower()
            pattern = r'\b' + re.escape(kw_clean) + r'\b'
            
            in_t = bool(re.search(pattern, title))
            in_d = bool(re.search(pattern, desc))

            if in_t or in_d:
                matched_words.append(kw)
                if in_t:
                    found_in_title += 1
                elif in_d:
                    found_in_desc += 1

        total_possible = len(target_keywords) * 2
        earned = (found_in_title * 2) + (found_in_desc * 1)
        score_percentage = int((earned / total_possible) * 100) if total_possible > 0 else 0
        
        scores.append(score_percentage)
        matched_list.append(", ".join(matched_words) if matched_words else "Tidak ada")

    df["Match Score"] = scores
    df["Matched Skills"] = matched_list
    df = df.sort_values(by="Match Score", ascending=False)
    return df