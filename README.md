# Job Search Scraper (Streamlit App)

A simple web app that searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google, and JobStreet
for jobs, using the `python-jobspy-damarowen` library, and lets you download the results as a CSV.

No coding experience needed to run this online — just follow the steps below.

## What's in this folder

- `app.py` — the app itself
- `requirements.txt` — the list of Python packages the app needs
- `README.md` — this file

## Step 1: Create a GitHub repository

1. Go to https://github.com and log in (or create a free account).
2. Click the **+** icon top-right → **New repository**.
3. Name it something like `job-search-app`. Keep it **Public**. Click **Create repository**.

## Step 2: Upload these files

1. On your new repo's page, click **Add file → Upload files**.
2. Drag in `app.py`, `requirements.txt`, and `README.md` from this folder.
3. Scroll down, click **Commit changes**.

That's it for GitHub — you don't need `.github.io` or anything else, since this app doesn't run
as a static site. It needs to actually run Python, which is what the next step is for.

## Step 3: Deploy on Streamlit Community Cloud (free)

1. Go to https://share.streamlit.io and sign in with your GitHub account.
2. Click **Create app** (or **New app**).
3. Choose your `job-search-app` repository, branch `main`, and set **Main file path** to `app.py`.
4. Click **Deploy**.

Streamlit will install everything in `requirements.txt` automatically and give you a public URL like:

```
https://your-app-name.streamlit.app
```

Share that link with anyone — they can use the search tool right in their browser.

## Using the app

- Pick which job sites to search in the sidebar (each is a checkbox now, not a dropdown list).
- Type in a job title and location.
- Click **Search jobs**.
- After the search, expand **"Per-site results"** to see how many jobs came from each site,
  or why a site failed.
- Once results appear, click **Download results as CSV** to save them.

## How this version handles unreliable sites

The original version ran all selected sites as one combined request — if a single site errored
out, the whole search failed and you got nothing, even from sites that worked fine. This version
searches each site **separately**, so:

- If one site fails or times out, the others still return their results.
- You get a per-site breakdown (jobs found, or the specific error) instead of one generic failure.
- Each site gets up to 2 attempts with a short delay between them, and a 60-second timeout, before
  it's marked as failed.

**Glassdoor and Indonesia:** the `python-jobspy-damarowen` library has no Glassdoor domain
configured for Indonesia at all — trying to search it with Indonesia selected always errors out.
The app checks this automatically (based on the library's own supported-country list) and
disables the Glassdoor checkbox with an explanation whenever the country field isn't one Glassdoor
supports. If you change the country to somewhere Glassdoor does cover (e.g. Singapore, USA), the
checkbox re-enables on its own.

**Google and JobStreet:** these sites actively try to block automated scraping, and Streamlit
Community Cloud's shared IP addresses get flagged more often than a home connection would. The
app now retries and reports the actual error (e.g. timeout vs. blocked vs. no results), but this
is a best-effort improvement — occasional failures on these two sites are a limitation of scraping
those platforms from a cloud server, not a code bug, and can't be fully guaranteed away.

## Good to know

- Scraping can take longer now than before, since sites are queried one at a time with retries
  rather than all at once — expect roughly 10–90 seconds depending on how many sites you pick.
- If a site returns few or no results, try again later, reduce "Results per site," or check the
  per-site results panel for the specific error.
- If you ever want to change something (like the default location), edit `app.py` on GitHub
  directly (click the pencil icon on the file), commit the change, and Streamlit Cloud will
  redeploy automatically.

## Running it on your own computer (optional)

If you later install Python, you can also run this locally instead of on Streamlit Cloud:

```
pip install -r requirements.txt
streamlit run app.py
```
