import re
import requests
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# URL Data Mentah Repo Nafkah (Otomatis Sync)
NAFKAH_RAW_URL = "https://raw.githubusercontent.com/adenaufal/nafkah/main/data/umr.json"

# Data Cadangan Lokal (Mencegah App Crash jika GitHub Down)
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

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_nafkah_data() -> dict:
    """Mengambil data UMR/Biaya Hidup terbaru dari repo GitHub Nafkah secara otomatis."""
    try:
        res = requests.get(NAFKAH_RAW_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            formatted = {}
            for item in data:
                key = item.get("city", "").lower()
                formatted[key] = {
                    "umr": item.get("umr", 0),
                    "cost": item.get("estimated_cost", 0)
                }
            return formatted
    except Exception:
        pass
    return FALLBACK_NAFKAH

def get_city_financial_info(location_str: str) -> str:
    """Mencocokkan lokasi lowongan dengan data Nafkah (Kota/Provinsi)."""
    if not location_str or pd.isna(location_str):
        return "📍 Lokasi tak terdeteksi"
    
    loc_clean = str(location_str).lower()
    if "remote" in loc_clean:
        return "🌐 Full Remote (Bebas Biaya Hidup)"
    
    nafkah_db = fetch_nafkah_data()
    
    for city_key, info in nafkah_db.items():
        if city_key in loc_clean:
            umr_fmt = f"Rp {info['umr']/1e6:.2f}M" if info['umr'] else "-"
            cost_fmt = f"Rp {info['cost']/1e6:.2f}M" if info['cost'] else "-"
            return f"💰 UMR {umr_fmt} | Est. Hidup ~{cost_fmt}"
    
    return "💡 Cek Biaya Hidup di Nafkah.adenaufal.com"

def extract_real_salary(description: str) -> str:
    """Mengekstrak gaji asli jika dicantumkan di deskripsi pekerjaan."""
    if not description or pd.isna(description):
        return "🔒 Gaji Dirahasiakan"
    
    patterns = [
        r"(?:rp|IDR)\s?[\d\.\,]+\s?\-\s?(?:rp|IDR)?\s?[\d\.\,]+",
        r"\b\d{1,2}\s?-\s?\d{1,2}\s?(?:juta|jt)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, str(description), re.IGNORECASE)
        if match:
            return f"💰 {match.group(0)}"
            
    return "🔒 Gaji Dirahasiakan"

def validate_jobs(df: pd.DataFrame, hours_old: int = 0) -> pd.DataFrame:
    """Memvalidasi dan membersihkan data lowongan."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    valid_df = df.dropna(subset=["title", "job_url"]).copy()
    valid_df["title"] = valid_df["title"].astype(str).str.strip()
    valid_df["company"] = valid_df["company"].fillna("Perusahaan Tidak Disebutkan").astype(str).str.strip()
    
    return valid_df

def deduplicate_jobs(df: pd.DataFrame, threshold: int = 85) -> pd.DataFrame:
    """Menghapus lowongan duplikat antar portal kerja."""
    if df.empty:
        return df
    
    deduped_rows = []
    seen_keys = []
    
    for _, row in df.iterrows():
        key = f"{row['title']} {row['company']}".lower()
        is_duplicate = False
        
        for seen in seen_keys:
            if fuzz.ratio(key, seen) >= threshold:
                is_duplicate = True
                break
                
        if not is_duplicate:
            seen_keys.append(key)
            deduped_rows.append(row)
            
    return pd.DataFrame(deduped_rows)

def detect_ats_friendly(url: str) -> str:
    """Menandai lamaran langsung (Greenhouse/Lever/Workable)."""
    if not url or pd.isna(url):
        return "📋 Form Standar"
    
    url_str = str(url).lower()
    ats_domains = ["greenhouse.io", "lever.co", "workable.com", "bamboohr.com", "ashbyhq.com"]
    
    if any(domain in url_str for domain in ats_domains):
        return "⚡ Quick Apply (ATS)"
    return "📋 Form Standar"

def categorize_work_type(row) -> str:
    """Mengkategorikan Remote / Hybrid / On-site."""
    text = f"{row.get('title', '')} {row.get('location', '')} {row.get('description', '')}".lower()
    
    if "remote" in text or row.get("is_remote") is True:
        return "🌐 Remote"
    elif "hybrid" in text:
        return "🏢 Hybrid"
    return "📍 On-site"

def calculate_match_score(df: pd.DataFrame, target_skills_str: str, exclude_skills_str: str = "") -> pd.DataFrame:
    """Menghitung skor kecocokan, Prioritas, dan Format Kolom Ringkasan."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    
    if "Form Type" not in df.columns:
        df["Form Type"] = "📋 Form Standar"
    if "Work Type" not in df.columns:
        df["Work Type"] = "📍 On-site"
    if "Sudah Dilamar" not in df.columns:
        df["Sudah Dilamar"] = False

    target_skills = [s.strip().lower() for s in target_skills_str.split(",") if s.strip()]
    exclude_skills = [s.strip().lower() for s in exclude_skills_str.split(",") if s.strip()]
    
    scores = []
    matched_list = []
    priority_list = []
    summary_match_list = []
    summary_detail_list = []
    
    for _, row in df.iterrows():
        desc = f"{row.get('title', '')} {row.get('description', '')}".lower()
        
        has_exclude = any(re.search(rf"\b{re.escape(exc)}\b", desc) for exc in exclude_skills)
        if has_exclude:
            scores.append(0)
            matched_list.append("Dilewati (Kata yang dihindari)")
            priority_list.append("⚪ Low")
            summary_match_list.append("⚪ Low (0%) • Disaring")
            summary_detail_list.append(f"{row.get('location', 'Indonesia')} | {get_city_financial_info(row.get('location'))}")
            continue
            
        if not target_skills:
            score = 50
            matched = ["Semua Lowongan"]
        else:
            matches = [skill for skill in target_skills if re.search(rf"\b{re.escape(skill)}\b", desc)]
            score = int((len(matches) / len(target_skills)) * 100)
            matched = matches if matches else ["Tidak ada skill cocok"]
            
        scores.append(score)
        matched_str = ", ".join(matched)
        matched_list.append(matched_str)
        
        form_type = row.get("Form Type", "📋 Form Standar")
        work_type = row.get("Work Type", "📍 On-site")
        loc = row.get("location", "Indonesia")
        
        if score >= 70 and form_type == "⚡ Quick Apply (ATS)":
            prio = "🟢 High"
        elif score >= 50:
            prio = "🟡 Medium"
        else:
            prio = "⚪ Low"
            
        priority_list.append(prio)
        summary_match_list.append(f"{prio} ({score}%) • {form_type}")
        
        salary_info = extract_real_salary(row.get("description", ""))
        fin_info = get_city_financial_info(loc)
        summary_detail_list.append(f"{work_type} • {loc}\n{salary_info} | {fin_info}")
        
    df["Match Score"] = scores
    df["Matched Skills"] = matched_list
    df["Prioritas"] = priority_list
    df["Rekomendasi & Match"] = summary_match_list
    df["Detail & Finansial"] = summary_detail_list
    
    return df.sort_values(by="Match Score", ascending=False)
