import pandas as pd
from jobspy import scrape_jobs

def fetch_jobs_safe(site_names, search_term, location, results_wanted, hours_old):
    """
    Mengambil data lowongan per platform secara terpisah.
    Jika 1 platform error (misal LinkedIn diblokir), platform lain tetap berjalan.
    """
    all_results = []
    errors = []

    for site in site_names:
        try:
            jobs = scrape_jobs(
                site_name=[site],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_usa_only=False
            )
            if jobs is not None and not jobs.empty:
                all_results.append(jobs)
        except Exception as e:
            errors.append(f"{site.capitalize()}: {str(e)}")

    if not all_results:
        return pd.DataFrame(), errors

    combined_df = pd.concat(all_results, ignore_index=True)
    return combined_df, errors