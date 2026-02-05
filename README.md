# Tracelet API

Tracelet is a universal tracking system designed to track any entities in an industrial or business workflow.  
It is **event-based**, **append-only**, and **scanner-friendly**, suitable for factories, warehouses, or any tracking application.

---

## Features

- Track **any entity** (batches, crates, products, machines, documents, etc.)
- Record **events** and **relationships** between entities
- Fully **auditable** and **traceable**
- Supports **QR codes, barcodes, RFID** (any carrier ID)
- **REST API** designed for both manual and automated scanners

---

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- Pydantic for schemas

---

## Installation

1. Clone the repo:

```bash
git clone <repo-url> tracelet-api
cd tracelet-api
```
2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate      # Linux / Mac
.venv\Scripts\activate         # Windows
```
3. Install deps:
```bash
pip install -r requirements.txt
```