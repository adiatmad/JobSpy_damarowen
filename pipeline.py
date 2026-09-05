def calculate_match_score(df: pd.DataFrame, target_skills_str: str, exclude_skills_str: str = "") -> pd.DataFrame:
    """Menghitung skor kecocokan & Prioritas Lamaran secara aman."""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Pastikan kolom dasar ada
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
