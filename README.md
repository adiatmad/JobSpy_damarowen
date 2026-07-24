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

- Set **Location**, **Country**, and (optionally) a keyword in the sidebar.
- Pick which job sites to search.
- Click **Search jobs**.
- Expand **"Per-site results"** to see how many jobs each site returned, or why a site failed.
- Once results appear, click **Download results as CSV** to save them.

## Searching without a keyword

The keyword field is optional. Leave it blank to get all valid postings for your location and
"posted within X hours" filter, with no title/keyword restriction. This works natively for
**LinkedIn, Indeed, ZipRecruiter, JobStreet, and Glassdoor**.

**Google is the one exception.** Google's scraper needs an actual search phrase to send to Google
Jobs — it can't browse by location alone. When you leave the keyword blank and Google is selected,
the app automatically builds a query behind the scenes (e.g. `"jobs in Jakarta since yesterday"`)
so Google still gets a valid, working search instead of breaking.

## How this version handles unreliable sites

Each site is now searched **separately**, one at a time, instead of one combined request. This
means:

- If one site fails or times out, the others still return their results — you never lose LinkedIn
  or Indeed results just because Glassdoor or Google had a problem.
- The **"Per-site results"** panel shows exactly how many jobs came from each site, or the specific
  error, instead of one generic failure message.
- Each site gets up to 2 attempts (with a short pause in between) and a 60-second timeout before
  it's marked as failed.

**Glassdoor and Indonesia:** the `python-jobspy-damarowen` library has no Glassdoor domain
configured for Indonesia at all — searching it with Indonesia selected always fails. The app
checks this automatically (by asking the library itself which countries it supports) and disables
the Glassdoor checkbox with an explanation whenever the country field isn't one Glassdoor covers.
Change the country to somewhere Glassdoor does support (e.g. Singapore, USA) and the checkbox
re-enables on its own.

**Google and JobStreet:** these sites actively try to block automated scraping, and Streamlit
Community Cloud's shared IP addresses get flagged more often than a home connection would. The app
retries each site and reports the real error (timeout vs. blocked vs. simply no results), but this
is a best-effort improvement — occasional failures on these two are a limitation of scraping those
platforms from a cloud server, not a bug in this app, and can't be fully guaranteed away.

## Good to know

- Scraping now takes a bit longer since sites are queried one at a time with retries rather than
  all at once — expect roughly 10–90 seconds depending on how many sites you pick.
- If a site returns few or no results, try again later, reduce "Results per site," or check the
  per-site results panel for the specific reason.
- If you ever want to change something (like the default location), edit `app.py` on GitHub
  directly (click the pencil icon on the file), commit the change, and Streamlit Cloud will
  redeploy automatically.

## Running it on your own computer (optional)

If you later install Python, you can also run this locally instead of on Streamlit Cloud:

```
pip install -r requirements.txt
streamlit run app.py
```
