# Shopfitting Costing App

Cost estimation, bill of materials, and cutting lists for shopfitting projects, built around five manufacturing typologies (Horizontal Box, Vertical Box, Flat Framework, Area Cladding, Framing Lines) instead of a per-product-name catalog. See `SHOPFITTING_APP_BUILD_NOTES.md` for the full design history and decisions.

## Status: Live

Deployed and running in production.

- **Live app**: https://web-production-f0083.up.railway.app
- **GitHub repo**: https://github.com/markbrunoconnect-a11y/shopfitting-costing-app
- **Railway project**: `diligent-imagination` (services: `web` + `Postgres`, own dedicated database - no collision risk with other apps)
- **Build**: plain `Dockerfile` at repo root (Railway's Railpack/Nixpacks auto-builders proved unreliable for this repo - inconsistent Python module resolution across build layers - so we switched to an explicit `python:3.13-slim` image for full control)
- Materials seeded: 54 materials + labour rate from `Shopfitting_Master_Price_List_Merged.xlsx`, loaded via `backend/scripts/seed_materials.py` run against production through Railway's Console tab

Backend, frontend, and deployment are all done. What's left is calibration - see "Open items" below.

## Running locally

```
cd backend
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./shopfitting_dev.db
alembic upgrade head
python scripts/seed_materials.py "../Shopfitting_Master_Price_List_Merged.xlsx"
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` for the interactive API, or `http://localhost:8000/` for the actual frontend.

## What's built

- **Models**: User, Material, Project, Item, Component, Setting (`backend/app/models.py`)
- **Typology engines**: `backend/app/typologies.py` - pure functions, one per typology, corrected against the bugs found in the source document (no margin/VAT, no cross-row reference errors, retains per-panel dimensions for cutting lists)
- **Cutting/yield logic**: `backend/app/cutting.py` - deterministic orientation and sheet-count calculation, replaces the manual "which way do I cut this" decision
- **Material rate resolution**: `backend/app/pricing.py` - converts a material's supplied cost (e.g. R850/sheet) into the per-m2 or per-linear-metre rate the typology engine needs, refusing to guess if dimension data is missing
- **API**: `backend/app/routers/` - auth, materials (full CRUD, no code/redeploy needed to update prices), projects, items (create with typology components, cost-analysis, cutting-list)
- **Migrations**: Alembic from day one, not `create_all()`, per the lesson learned from Engineering-Management-App's schema-drift incident. Current revision: `0003`.
- **Consumables markup**: `consumables_pct` Setting (default 5%), applied as a flat percentage of each component's material cost to cover screws/glue/sealant/tape/sandpaper - items not individually priced anywhere else. Editable via Settings, same as wastage_factor. See `component_service._finalize_costs()`.
- **Labour costing (revised)**: labour cost is no longer hours x rate. Each **Item** now has a `fixture_category` (Modular / Standard Joinery / Bespoke-Premium, reference label only) and a `labour_multiplier` (the actual number used), set at Add Item time. Labour cost = material cost x that multiplier. Suggested starting multipliers, from Mark's own research: Modular 0.5x-0.8x, Standard Joinery 1.0x, Bespoke/Premium 1.5x-2.0x - all editable per item, not locked to the category. This replaced the original hours-based formulas (`labour_hours` fields are still computed and stored for reference, but no longer drive cost) because those formulas were placeholder guesses from the source document with no real shop timing data behind them.

## Open items (calibration, not architecture)

Nothing structural is missing - these are all "plug in real numbers" tasks:

- **Wastage factor** (currently 10%, `wastage_factor` Setting) and **kerf** (3.5mm, `kerf_mm` Setting) are Mark's own supplied defaults from earlier in the build - not yet stress-tested against real jobs.
- **Consumables markup** (5%, `consumables_pct` Setting) is a rough industry-common starting figure, not a shop-specific measurement. Revisit after a few real jobs.
- **Labour multipliers** are per-item and editable, but the suggested default numbers (0.65 / 1.0 / 1.75) haven't been validated against Mark's actual costed jobs yet - worth checking the app's estimate against a few real quotes once there's a backlog of completed jobs to compare against.
- **"Separate Top"** (stone/solid-surface counters) is still a manual add-on, not its own typology.
- Some materials in the merged price list are still missing dimension data (notably the edge-banding roll and finishing-liquid items lack the length/volume needed to compute a per-metre or per-unit rate) - the app surfaces a clear error naming the exact missing field for any material used before this is fixed, rather than silently guessing. Fix these in the Materials screen as they come up.

## Useful ops notes for next time

- Railway's Settings > Deploy > "Custom Start Command" field silently overrides everything else (Procfile, `RAILPACK_START_CMD` variable) - if a deploy behaves unexpectedly, check that field first.
- Production migrations run automatically on every deploy (the Dockerfile's `CMD` runs `alembic upgrade head` before starting uvicorn) - no manual migration step needed after a normal `git push`.
- To run something one-off against production data (like the materials seed script), use Railway's Console tab on the `web` service - it's a real shell inside the running container.
