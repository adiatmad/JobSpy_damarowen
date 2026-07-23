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

- Pick which job sites to search in the sidebar.
- Type in a job title and location.
- Click **Search jobs**.
- Once results appear, click **Download results as CSV** to save them.

## Good to know

- Scraping can take 10–60 seconds depending on how many sites you pick and how many results you ask for.
- Job sites sometimes block or rate-limit scrapers, especially LinkedIn. If a site returns few or
  no results, try again later, reduce "Results per site," or search fewer sites at once.
- If you ever want to change something (like the default location), edit `app.py` on GitHub directly
  (click the pencil icon on the file), commit the change, and Streamlit Cloud will redeploy automatically.

## Running it on your own computer (optional)

If you later install Python, you can also run this locally instead of on Streamlit Cloud:

```
pip install -r requirements.txt
streamlit run app.py
```
