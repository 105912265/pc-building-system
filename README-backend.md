# Phase 5 — MySQL backend starter

This is the first backend milestone only. It does not replace your Streamlit app, modify the MySQL schema, or migrate CSV data.

## Setup (Windows PowerShell)

1. Copy the `backend/` folder and `requirements-backend.txt` and `.env.example` into the root of your PC-Builder repository (alongside `app.py`).
2. Create and activate a virtual environment if needed:
   `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
3. Install dependencies: `python -m pip install -r requirements-backend.txt`
4. Copy `.env.example` to `.env`: `Copy-Item .env.example .env`
5. Edit `.env` with the actual MySQL username, password, and port shown in Workbench. 3307 is a suggested port from your previous setup; verify it.
6. Add `.env` and `.venv/` to your existing `.gitignore`. NEVER commit database passwords.
7. Ensure MySQL Server is running and the `pc_building_system` schema exists.
8. Start the API from the repository root: `python -m uvicorn backend.main:app --reload`

## Test in a browser

- `http://127.0.0.1:8000/` — backend up
- `http://127.0.0.1:8000/health/db` — MySQL connection and row count (25 for the supplied dump)
- `http://127.0.0.1:8000/components` — MySQL components as JSON
- `http://127.0.0.1:8000/components?category=GPU&manufacturer=NVIDIA` — basic category/brand filter
- `http://127.0.0.1:8000/components?category=GPU&min_price=500&max_price=1100` — price filter
- `http://127.0.0.1:8000/docs` — interactive FastAPI docs

## Important

Do not import the supplied SQL dump into an existing populated database unless you intentionally want to restore that snapshot: the dump includes `DROP TABLE IF EXISTS` statements.

For the next milestone, reconcile the CSV benchmark/wattage fields with the MySQL `component.specifications` JSON and `benchmark` tables before replacing existing recommendation-engine loaders.
