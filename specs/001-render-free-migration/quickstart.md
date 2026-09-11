# Quickstart: Render Free Deployment Validation

## Prerequisites

- GitHub access to `adiatmad/JobSpy_damarowen`.
- Render account connected to the repository.
- `render-migration` branch selected for deployment.

## Deploy

1. Create a Render Web Service from `adiatmad/JobSpy_damarowen`.
2. Select branch `render-migration`.
3. Use the Free plan.
4. If Render requests commands explicitly, use:

   Build:
   `pip install -r requirements.txt`

   Start:
   `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`

5. Deploy and wait for the build to finish.

## Validation Matrix

### Test 1 - Application startup

Expected: Public Render URL loads the Streamlit interface without an application startup exception.

### Test 2 - Single-site search

Use a modest result count and one site.

Expected: Results appear, or the UI reports a scraper/site error without taking down the application.

### Test 3 - Multi-site search

Select two or more sites.

Expected: The application completes the bounded scraping attempts and displays whatever valid results were returned.

### Test 4 - CSV export

Run a search that returns results and export CSV.

Expected: A CSV file downloads and contains the processed job records.

### Test 5 - External blocking

If a site returns 403, Cloudflare, or another anti-bot response, record the site and error.

Expected: Treat this as a candidate external IP/reputation problem, not automatically as a Render application defect.

### Test 6 - Cold start

Leave the Free service idle long enough to suspend, then open the public URL again.

Expected: The service eventually starts and serves the application again.

## Evidence to Record

- Render deployment URL
- Build success/failure
- Startup/runtime errors
- Approximate time for single-site and multi-site searches
- Which sites succeed or fail
- Whether CSV export works
- Any observable memory/CPU/resource symptoms

## Decision Rule

Keep the minimal Render migration if the application is stable enough for intended use. Create a separate optimization/specification feature only when observed evidence identifies a concrete bottleneck.
