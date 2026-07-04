# Shopfitting Costing App

Cost estimation, bill of materials, and cutting lists for shopfitting projects, built around five manufacturing typologies (Horizontal Box, Vertical Box, Flat Framework, Area Cladding, Framing Lines) instead of a per-product-name catalog. See `SHOPFITTING_APP_BUILD_NOTES.md` for the full design history and decisions.

## Status

Backend and a working frontend are both built and verified locally: models, Alembic migrations, the five typology cost engines, cutting-list yield/orientation logic, the full API, and a single-page UI (login/register, project dashboard, add-item configurator with typology-driven dropdowns, materials admin screen, cost analysis, cutting list) served directly by the backend at `/`. Not deployed yet - that's the next and final step (new GitHub repo, new Railway project with its own dedicated Postgres database).

## Running locally

```
cd backend
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./shopfitting_dev.db
alembic upgrade head
python scripts/seed_materials.py "../Shopfitting_Master_Price_List_Merged.xlsx"
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` for the interactive API - useful for testing before the frontend exists.

## What's built

- **Models**: User, Material, Project, Item, Component, Setting (`backend/app/models.py`)
- **Typology engines**: `backend/app/typologies.py` - pure functions, one per typology, corrected against the bugs found in the source document (no margin/VAT, no cross-row reference errors, retains per-panel dimensions for cutting lists)
- **Cutting/yield logic**: `backend/app/cutting.py` - deterministic orientation and sheet-count calculation, replaces the manual "which way do I cut this" decision
- **Material rate resolution**: `backend/app/pricing.py` - converts a material's supplied cost (e.g. R850/sheet) into the per-m2 or per-linear-metre rate the typology engine needs, refusing to guess if dimension data is missing
- **API**: `backend/app/routers/` - auth, materials (full CRUD, no code/redeploy needed to update prices), projects, items (create with typology components, cost-analysis, cutting-list)
- **Migrations**: Alembic from day one, not `create_all()`, per the lesson learned from Engineering-Management-App's schema-drift incident

## What's not built yet

- Deployment (new GitHub repo, new Railway project with its own dedicated Postgres database)
- Real wastage factors, kerf value, and hardware costs beyond the seeded defaults (labour rate R350/hr and kerf 3mm are seeded; wastage multipliers are the source document's generic placeholders, hardcoded as defaults inside each typology function in `typologies.py`)
- The "Separate Top" (stone/solid-surface counters) case - still a manual add-on, not its own typology
- Materials in the merged price list still needing their dimension data filled in before they can be used in a calculation (notably the edge-banding roll and finishing-liquid items, which are missing the length/volume needed to compute a per-metre or per-unit rate) - the app will surface a clear error naming the exact missing field for any material used before this is fixed, rather than silently guessing
