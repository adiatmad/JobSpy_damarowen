# Deployment notes

## Recommended public-hosting direction

The application is a stateful Streamlit app with SQLite Job Memory and on-demand scraping. That makes a small persistent VM a better first public host than a serverless container.

### Current recommendation

**Oracle Cloud Always Free VM + Docker + HTTPS reverse proxy/tunnel**

Why:

- persistent local storage fits the SQLite Job Memory model;
- the VM gives predictable CPU/RAM instead of Streamlit Community Cloud's shared resource limits;
- Docker keeps the runtime portable;
- the architecture can later separate the UI and scraper worker if source blocking becomes the bottleneck.

Oracle's Always Free tier currently includes up to 2 OCPUs and 12 GB RAM on an Ampere A1 instance, subject to region capacity and account eligibility.

### Important trade-off

Oracle Cloud account creation may require payment-card verification. "Free" does not necessarily mean "no card required".

### Cloud Run

Cloud Run is a useful second option when the application becomes stateless or Job Memory moves to an external database. Its free tier is attractive, but Cloud Run instances are ephemeral, so SQLite should not be treated as durable application storage there.

### Streamlit Community Cloud

Keep the current Streamlit deployment for lightweight demos/testing, not as the long-term public scraper host. Community Cloud explicitly throttles apps that hit shared resource limits, and scraping is a CPU/network-heavy workload.

## Container

The repository includes a Dockerfile so the same application can run on a VM or container platform.

For local testing:

    docker build -t teman-cari-kerja .
    docker run --rm -p 8501:8080 -e PORT=8080 teman-cari-kerja

Then open http://localhost:8501.

## Future architecture trigger

Do not add a scraper API, external database, queue, or multi-user authentication yet.

Split the UI and scraper worker only when real public usage demonstrates one of these constraints:

1. scraper source blocking caused by shared/public egress;
2. concurrent searches overload the VM;
3. Job Memory needs durable multi-instance storage;
4. multiple users need isolated data.

Until then, a single small persistent VM is the simpler system.
