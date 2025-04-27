# zero_networks_ha
Home Assignment for Data Engineer position

# 🚀 SpaceX Launches Ingestion and Aggregation Pipeline

This project fetches the latest SpaceX launch data from the SpaceX API, enriches it with simulated fields, stores it into PostgreSQL, and exposes an aggregation view for analytics through Trino.
It is fully containerized using Docker Compose for easy setup and reproducibility.
---

## 📦 Architecture Overview

| Component | Purpose |
|:---|:---|
| **PostgreSQL** | Stores raw SpaceX launch data |
| **Trino** | Provides a SQL query engine over PostgreSQL |
| **Ingestion Service** | Fetches, enriches, and inserts launch data |
| **Analytics Queries** | Runs additional analytical queries on stored data |

---

## 📂 Project Structure

```text
zero_networks_ha/
├── docker/
│   └── trino/
│       └── etc/
│           └── catalog/
│               └── postgres.properties
│   └── docker-compose.yml
├── sql/
│   └── analytics_queries.py
├── src/
│   ├── Dockerfile
│   ├── ingestion.py
│   ├── requirements.txt
│   └── ingestion.log
├── .gitignore
├── README.md
```

## 🐳 Docker Compose Setup (PostgreSQL + Trino)

This project uses **Docker Compose** to spin up a local data environment with:

- **PostgreSQL** – for storing raw and aggregated SpaceX data  
- **Trino** – for querying PostgreSQL via SQL 

**_Please, make sure that Docker Compose is installed on your device before continuing.  
You can find download instructions here: [https://docs.docker.com/get-started/introduction/get-docker-desktop/](https://docs.docker.com/get-started/introduction/get-docker-desktop/)_**

## 🐳 Docker Overview

This project uses Docker and Docker Compose to orchestrate the ingestion pipeline, database, and query engine components.

### Services

| Service | Description |
|:--------|:------------|
| **PostgreSQL** | Stores raw SpaceX launch data. A database container that holds the `raw_launches` table. |
| **Trino** | A fast distributed SQL engine. Allows running analytical queries over PostgreSQL without moving data. |
| **Ingestion** | A lightweight Python app that fetches launch data from SpaceX API, enriches it with simulated fields, and loads into PostgreSQL. |

---

### Docker Compose Setup

All services are orchestrated via `docker-compose.yml` located in the `docker/` directory.

Run next command as a first step:
```bash
docker-compose -f docker/docker-compose.yml up --build
````

This command will:

- Pull or build required images (postgres, trinodb/trino:latest, and your ingestion service).
- Start services in the correct dependency order (e.g., ingestion waits for PostgreSQL).
- Mount necessary volumes and configs (e.g., Trino catalog files).
- Expose relevant ports:
  - PostgreSQL: 5432
  - Trino Web UI: 8080
  
✅ After this command:
- PostgreSQL will be running
- Trino will be running
- Ingestion will automatically fetch latest launch and insert it into the database once, then stop.

If you want to repeat ingestion to fetch new launches simply run:
````bash
docker-compose run --rm ingestion
````
It will fetch the latest launch from SpaceX API again and attempt to ingest it.
--rm will clean up the container after run
---

### 🔍 You  can Query the Data via Trino

After services are running, access the Trino Web UI at:

```bash
http://localhost:8080/ui/
```

### 🩺 Healthchecks

- **PostgreSQL**: Waits until the database is ready to accept connections.
- **Trino**: Waits until Trino is ready to accept SQL queries.
- **Ingestion**: Starts only once to ingest data and then exits gracefully (no infinite restart loops).

---

### 🌐 Environment Variables

The ingestion container uses environment variables set via `docker-compose.yml`:

| Variable            | Purpose                                  |
|---------------------|------------------------------------------|
| `POSTGRES_HOST`      | Hostname of the PostgreSQL server (`postgres`) |
| `POSTGRES_DB`        | Name of the database (`spacex`)          |
| `POSTGRES_USER`      | Username for PostgreSQL access           |
| `POSTGRES_PASSWORD`  | Password for PostgreSQL access           |


## Ingestion
### 🚀 Ingestion Pipeline: Design Choices, Assumptions, and How to Run

---

## 🧠 Design Choices and Assumptions
# 🚀 Ingestion Pipeline Details

This ingestion script is responsible for fetching, enriching, validating, storing, and aggregating SpaceX launch data automatically.

---

## 🧠 Design and Features

- **Incremental Fetching**:  
  Fetches the latest SpaceX launch from `https://api.spacexdata.com/v4/launches/latest`.

- **Simulated Enrichment**:  
  Due to lack of full payload mass and delay data from the SpaceX API:
  - A simulated **total payload mass** is generated between **2,000 and 6,000 kg** per payload.
  - A simulated **launch delay** is generated between **0 and 120 minutes**.
  
- **Metadata Injection**:  
  Adds `fetched_at_timestamp` (UTC) field to every launch to track ingestion time.

- **Idempotent Storage**:  
  Launch data is inserted into `raw_launches` table with `ON CONFLICT DO NOTHING` to prevent duplicate insertions.

- **Aggregation View Creation**:  
  After each ingestion, the pipeline automatically (re)creates an aggregated view:
  
  | Metric | Description |
  |:---|:---|
  | `total_launches` | Total launches ingested |
  | `total_successful_launches` | Number of successful launches |
  | `average_payload_mass` | Average payload mass (simulated) |
  | `average_launch_delay_minutes` | Average delay (simulated) |

- **Analytics Execution**:  
  After ingestion and view creation, analytical queries are automatically run via `run_analytics_queries()`.

- **Logging**:  
  All steps are logged both to console and to a `ingestion.log` file inside `src/` directory.

---

## 📦 Ingested Data Structure (PostgreSQL: `raw_launches` Table)

| Column | Type | Description |
|:---|:---|:---|
| `id` | TEXT | Launch unique identifier (primary key) |
| `fetched_at_timestamp` | TIMESTAMP | UTC time when data was fetched |
| `simulated_total_payload_mass_kg` | INTEGER | Simulated payload mass |
| `simulated_delay_minutes` | INTEGER | Simulated delay |
| `raw_data` | JSONB | Full original SpaceX API launch payload |

---

## 🛠 How to Run the Ingestion Pipeline

1. **Start all services** (PostgreSQL, Trino, Ingestion) with Docker Compose:
2.  After build, ingestion will automatically:
- Fetch the latest launch
- Simulate enrichment fields
- Insert into raw_launches
- Create/update launch_aggregates_view
- Run analytics queries and print output (can be easily reformat to reports, views, charts, etc)

### Important Assumptions
- One-Time Container Behavior:
  - The ingestion container runs once per execution and exits gracefully to avoid infinite loops.
- Extensibility:
The ingestion system is designed to allow easy future improvements, such as:
  - Fetching real payload mass via /payloads/{payload_id} 
  - Fetching real scheduled launch times 
  - Setting up scheduled (cron-like) ingestion jobs

📋 Example Logs
Upon running ingestion, you will see logs like:
````bash
2024-04-27 17:02:01,302 - INFO - Successfully fetched latest launch data from SpaceX API.
2024-04-27 17:02:01,500 - INFO - Launch 62dd70d5202306255024d139 inserted into database.
2024-04-27 17:02:01,700 - INFO - Aggregation view launch_aggregates_view created successfully.
2024-04-27 17:02:01,800 - INFO - Running analytics queries...
````
✅ Logs are written both to console and to src/ingestion.log.

## 📄 Notes and Future Improvements

### 🛠️ Improvement Points (TODO List)

- **Cross-Platform Docker Installation Guide**:  
  Add a short section explaining how to install Docker for different operating systems:
  - Windows / macOS: [Docker Desktop](https://docs.docker.com/get-started/introduction/get-docker-desktop/)
  - Ubuntu/Linux: `apt install docker.io` or detailed manual installation steps.

- **Instructions for Local Debugging**:  
  Provide guidelines on how to:
  - Run ingestion scripts manually outside Docker (for faster development).
  - Configure `.env` file locally for PostgreSQL connection.

- **Logging Enhancements**:  
  Improve the logging setup to:
  - Differentiate between INFO, WARNING, ERROR levels more clearly.
  - Include ingestion runtime metrics (execution time, number of records inserted).
  - Optionally send logs to external monitoring systems (e.g., Loki, Datadog).


- **Scheduled Ingestion (Batch Scheduling)**:  
  Instead of manual ingestion, implement scheduled batch runs:
  - Use **cron** (for local/Linux).
  - Or **scheduled GitHub Actions** / **Airflow** / **Kubernetes CronJobs** in cloud setups.
  - Schedule ingestion every X minutes/hours to simulate near real-time ingestion.


- **CI/CD Automation**:  
  Build a simple Continuous Integration/Deployment (CI/CD) pipeline:
  - **Run ingestion tests** automatically on every pull request.
  - **Build and push Docker images** on successful tests.
  - **Deploy to production/staging environments** automatically (optional bonus).
  - Recommended tools: GitHub Actions, GitLab CI, CircleCI, etc.


---

### 📢 Important Notes

- **Simulated Metrics**:  
  Payload mass and launch delay are generated randomly because the SpaceX API/latest does not provide this data reliably.

- **Extensible Design**:  
  The ingestion system is modular, allowing easy upgrades to:
  - Fetch real payload mass via `/payloads/:id` endpoint.
  - Handle scheduled vs actual launch delays (when SpaceX API supports it).
  - Scale horizontally to ingest many launches in parallel.

---
