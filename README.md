# Tracelet API

Tracelet is a universal tracking system designed to track **any entities** in an industrial or business workflow.  
It is **event-based**, **append-only**, and **scanner-friendly**, making it ideal for factories, warehouses, or any application where traceability is crucial.

---

## Features

- Track **any entity** (batches, crates, products, machines, documents, etc.)
- Record **events** and **relationships** between entities
- Fully **auditable** and **traceable**
- Supports **QR codes, barcodes, RFID** (or any carrier ID)
- **REST API** designed for both manual and automated scanners

---

## Tech Stack

- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- SQLAlchemy + Alembic
- Pydantic for data validation and schemas
- [Uvicorn](https://www.uvicorn.org/) as ASGI server

---

## Installation

1. **Clone the repository:**

```bash
git clone <repo-url> tracelet-api
cd tracelet-api

    Create and activate a virtual environment:

python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Initialize the database (Windows / Docker)

The project includes a PowerShell helper init_db.ps1 that starts a PostgreSQL Docker container (if needed) and ensures tables exist.

Important: open PowerShell as Administrator and run:

# open PowerShell as Administrator, then run:
```bash
C:/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe -File C:/path/to/tracelet-api/init_db.ps1
```
If you prefer not to use Admin elevation, you can run the script in the current session with an execution policy bypass:
```bash
powershell -ExecutionPolicy Bypass -File C:/path/to/tracelet-api/init_db.ps1
```

What the script does:

1. Ensures Docker is installed.

2. Creates/starts a tracelet-db PostgreSQL container with credentials:

        Host: localhost

        Port: 5432

        User: tracelet_user

        Password: password

        DB: tracelet_db

    Waits until Postgres accepts connections.

    Creates required tables (idempotent CREATE TABLE IF NOT EXISTS) so the API won't error with "relation does not exist".

Run the API (development)

After the DB is initialized, start the server with uv (uvicorn wrapper) or uvicorn:

# using `uv` (if you have the uv wrapper installed)
uv run app.main:app --reload --host 127.0.0.1 --port 8000

# or directly with uvicorn:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

    --reload enables automatic reload on code changes.

    The API base will be available at: http://127.0.0.1:8000

    The API routes are exposed under /api/v1/ by default.

Web UI (WebSQL)

A second small web UI (SqlTracelet / WebSQL) runs on port 8076 by default. It calls the API (configured in websql/settings.py) and provides simple HTML views:

# start both apps via the provided starter (or run individually)
# If you use the project's main entry that launches both processes:
python main.py
# or run each app separately:
uvicorn app.main:app --reload --port 8000
uvicorn websql.main:app --reload --port 8076

Navigate to:

    Dashboard / Web UI: http://127.0.0.1:8076/

    API docs (FastAPI): http://127.0.0.1:8000/docs (OpenAPI/Swagger)

Useful endpoints

    Health:
    GET http://127.0.0.1:8000/api/v1/health

    Version:
    GET http://127.0.0.1:8000/api/v1/version

    Entities (example):
    GET http://127.0.0.1:8000/api/v1/entities/
    POST http://127.0.0.1:8000/api/v1/entities/ (JSON body)

Notes & Tips

    For production, replace Docker dev credentials and secure Postgres behind proper authentication & network rules.

    Use Alembic for schema migrations in production instead of create_all.

    If you are on Windows and scripts are blocked, prefer the powershell -ExecutionPolicy Bypass -File ... approach for one-off runs.

    If you want a single command to bring everything up in dev, consider adding a docker-compose.yml that defines Postgres and a dev service.

Links

    Uvicorn — https://www.uvicorn.org/

    FastAPI — https://fastapi.tiangolo.com/

    PostgreSQL — https://www.postgresql.org/

You should now be able to visit the Web UI at http://127.0.0.1:8076/ and the API at http://127.0.0.1:8000/api/v1/.