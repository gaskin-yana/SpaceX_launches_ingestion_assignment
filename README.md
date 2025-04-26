# zero_networks_ha
Home Assignment for Data Engineer position

## 🐳 Docker Compose Setup (PostgreSQL + Trino)

This project uses **Docker Compose** to spin up a local data environment with:

- **PostgreSQL** – for storing raw and aggregated SpaceX data  
- **Trino** – for querying PostgreSQL via SQL

---

### 🧱 1. Folder Structure

```bash
docker/
├── docker-compose.yml
└── trino/
    └── etc/
        └── catalog/
            └── postgres.properties
```

### ▶️ 2. Run the Stack

From the `docker/` directory, run:

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL on port **5432**
- Start Trino on port **8080**

---

### 🧪 3. Verify Setup

#### ✅ Check Docker Containers

```bash
docker ps
```

You should see two running containers: `postgres` and `trino`.

---

Errors debug:
You need to start or restart Docker Desktop:

On your Windows machine, find and open Docker Desktop.

Wait for it to fully start — you should see:

"Docker Desktop is running"

A green light ✅

If it’s stuck or frozen:

Right-click Docker icon → Restart Docker

After it's running, retry:
```bash
docker-compose up --build
```


Metrics:
## Notes on Launch Delay Metric

The SpaceX API (`https://api.spacexdata.com/v4/launches/latest`) does not provide a separate field for the actual launch time versus the scheduled launch time.  
Typically, the `date_utc` field represents the intended scheduled launch time, and it may be updated to reflect actual launch time after execution.

For the purpose of this project:

- `date_utc` is treated as both the scheduled and actual launch time.
- No actual delay calculation is performed, and the `average_launch_delay_minutes` metric is set to `NULL` accordingly.
- In a real-world production system, enrichment from additional external feeds or manual updates would be required to accurately compute launch delays.

This approach ensures data integrity and avoids misrepresenting metrics based on incomplete source data.


TODO:
- add instalation of docker for ubuntu
- add explanation about different os
- running localy
- https://github.com/r-spacex/SpaceX-API/tree/master/docs#rspacex-api-docs, 
  - mongodn based id unique
- logging setup