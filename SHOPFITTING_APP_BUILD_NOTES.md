# Shopfitting Costing App — Build Reference (v3)

Status: Backend and frontend both built and verified locally (see README.md in this folder for how to run it). Models, Alembic migrations, the five typology cost engines, cutting-list yield/orientation logic, the full API, and a working single-page UI all run end-to-end against a test database seeded with real data from the merged Master Price List. Deployment (new GitHub repo + Railway project) is the only thing not started. This document lets Claude pick the project back up with full context, without re-running the discussion. Supersedes the v1 notes (which were based on replicating the five tabs of the original Excel tool item-by-item — see "What Changed" below).

Source material:
- `Shopfitting Costing Tool 1 - Revision D.xlsx` (Mark's original tool) — used for its Master Price List rates and as the origin of the manufacturing-typology insight.
- `instructions on setting up excel.docx` (a manufacturing-typology Excel design Mark worked out with another AI) — the basis for the v2 architecture below. Mark originated the manufacturing-standpoint idea himself; the document formalizes it into five parametric typologies with draft formulas.

## What Changed From v1

v1 planned item-type templates modeled directly on the existing Excel tabs (Drawer Box, Steel Table, Cupboard & Shelving, Plaster Board Wall, Construction Cost) — meaning a new custom template had to be reverse-engineered from a spreadsheet every time a new product type came up.

v2 replaces that with five fixed manufacturing typologies that between them approximate ~80-95% of shopfitting products, classified by *how it's made* rather than *what it's called*. This is a closed, uniform set instead of an open-ended list, and is the architecture to build against going forward.

## The Five Manufacturing Typologies

1. **Horizontal Box** (open-back/open-front carcass) — counters, reception desks, cash wraps, workbenches, pedestals.
   Inputs: Length, Height, Depth (mm); Material; Separate Top? (Y/N); No. of Drawers.
2. **Vertical Box** (five-sided carcass, optional door) — wall/floor cabinets, towers, wardrobes, lockers.
   Inputs: Width, Height, Depth (mm); Material; No. of Internal Shelves; Enclosure Doors? (Y/N).
3. **Flat Framework** (linear steel/timber skeleton, no sheet boxing) — clothing rails, mobile trolleys, shelving legs, table frames.
   Inputs: Width, Height, Depth (mm); Profile material; Internal Cross-Rails count; Mobile Wheels? (Y/N).
4. **Area Cladding** (flat 2D coverage over a substructure) — slatwall, acoustic panels, suspended ceilings, drywall linings.
   Inputs: Width, Height (mm); Substructure base; Face material; Complexity (Standard/High); Perimeter Edging? (Y/N).
5. **Architectural Framing Lines** (heavy perimeter track holding glass/door infill) — shopfronts, glass partitions, entryway systems.
   Inputs: Opening Width, Opening Height (mm); Framing profile; Glass spec; Door mechanism (None/Manual/Automatic); No. of Mid-Mullions.

Each typology has its own deterministic formula set (surface area or linear run → secondary quantities like edging/joints/glazing → labour hours → cost). All are pure arithmetic — no AI/vision judgment anywhere in the calculation.

## Multi-Typology Items (the "LEGO" Rule)

A single real-world item can be a combination of typologies — e.g. a counter with a glass display case (Horizontal Box + Vertical Box), or a shelving bay (Flat Framework + Area Cladding). This maps directly onto the existing Item → Component data model: one **Item** can contain multiple **Components**, each priced by its own typology. No new data model needed — this validates the structure already planned.

## Corrections to Make When Encoding These Formulas

The source document's formulas are a good starting logic but were drafted in Excel and have real issues worth fixing at the code stage, not carrying forward:

- **Confirmed bug**: the compiled Horizontal Box edging formula referenced the wrong row's depth (`C3` instead of `C2`) — a copy-paste transcription error. In code, this class of bug can't happen once values are named variables instead of spreadsheet cell coordinates, but it's a reminder to verify every formula against its own inputs rather than assuming the document is error-free.
- **Scope conflict**: the source document's final "Quoted Price" formulas bake in a 30% margin and 15% VAT. That contradicts the app's agreed scope — **this app computes cost only**; markup and VAT are a separate manual step outside the app, same as the original ConstructTrack-style shopfitting design decision. Stop the calculation at cost; don't build margin/VAT into the app.
- **Granularity**: the source formulas collapse each typology into one aggregate m² or linear-metre total, which is fine for a fast quote but not enough for a real cutting list — a saw operator needs each panel's individual width and height. The individual terms inside each formula (e.g. `B×C` for a side panel, `A×B` for a back panel) already are those individual panel dimensions. When building in code, keep each named panel as its own line item rather than summing to one number — this gives the same fast cost total *and* a properly itemized cutting list from a single calculation, at no extra cost.
- **Placeholder numbers**: wastage multipliers (1.15, 1.10, 1.12, 1.08, 1.05), hourly labour rates (R280/R320/R350), and hardware kit prices (drawer kits, hinge kits, castor kits, door mechanism kits) in the source document are generic guesses, not Mark's real numbers. These need to be replaced with actual shop figures before the app produces trustworthy costs. This is a data-calibration task, not a design blocker.

## How This Connects to the Cutting List / Yield Work Already Done

The typology formulas tell you *how much* board area or linear stock a component needs — they don't by themselves tell you how many actual sheets to buy or how to orient each panel on a sheet. That's still handled by the yield/orientation logic already agreed on separately: once a component's typology formula produces its individual panel dimensions (per the granularity point above), those panel dimensions feed into the same deterministic yield calculation — compute yield both orientations against the chosen material's sheet size, pick the better one, apply a kerf allowance — to produce the actual cutting list and sheet count. Both pieces are needed and both are pure math: typology formulas decompose an item into named panels; yield logic packs those panels onto real stock sheets.

## Data Model (updated)

- **Project**: id, name, project_number, sponsor, client_info, expected_delivery_date, special_instructions, created_at
- **Item**: id, project_id, name/description, quantity, drawing_file (optional, reference-only)
- **Component**: id, item_id, typology (Horizontal Box / Vertical Box / Flat Framework / Area Cladding / Framing Lines), typology_inputs (the specific dimensions/dropdowns/counts for that typology), derived_panels (the individual named panel dimensions computed from the typology formula, e.g. "Side Panel: 600x900mm x2")
- **Material** (master rate table, imported/editable, decoupled from app code): id, name, category (board/profile/glass/substructure/etc.), rate, unit (per m² or per linear metre), sheet_length_mm, sheet_width_mm, thickness_mm — seeded from the original Master Price List, extended with the new document's rate categories (steel profiles, glass, slatwall, aluminium track, etc.)

Dimensions remain manually entered per job (confirmed earlier: no fixed formula links overall size to panel size across arbitrary custom jobs) — but now entry happens through five uniform, compact typology forms instead of open-ended freeform panel entry, directly addressing the earlier "too much clutter" concern.

## Key Design Decisions (carried over, still valid)

- **Cutting orientation**: calculated automatically via yield math (component dimension along sheet length vs. width, pick the better yield). No manual button, no AI/vision.
- **Kerf allowance**: small default constant (~3-4mm, to be confirmed), subtracted per cut in the yield calc, overridable per material.
- **Grain/pattern direction**: not handled in v1; rare, handled manually offline if it comes up.
- **Drawing upload**: reference/record only, stored with the item for assemblers. Not used to auto-fill dimensions.
- **Labour cost**: hours × a standard burden rate (confirmed to be a single consistent rate across the business, not itemized by individual pay rate) — note the source document uses different rates per typology (R280 joinery, R320 welding/site, R350 glazing); confirm with Mark whether that differentiation is real or should collapse to one rate.
- **Special instructions for assemblers**: out of scope, handled by separate assembly documents.
- **Branding on outputs**: deferred, cheap to add later.
- **Master Price List / Database**: must be maintainable without touching app code, following the same header-matched import pattern already built for ConstructTrack's Gantt import.
- **Multi-user / multi-project**: build for growth from day one.
- **Pure cost model**: app output is cost only, no markup/quotation logic (see "Corrections" above — this now explicitly overrides the source document's margin/VAT formulas).

## Outputs (v1)

1. Cost Analysis — per item unit cost, aggregated to a project total.
2. Cutting List — per item, built from each component's derived panel list plus yield/orientation logic.

## Open Items to Resolve Before/During Build

- Confirm real wastage factors, labour rates, and hardware/kit costs to replace the source document's placeholders.
- Confirm whether labour rate genuinely varies by typology (joinery vs. welding vs. glazing/site work) or should be one flat burden rate as previously stated — these two answers currently conflict and need reconciling.
- Decide the kerf constant default.
- Build out the Database/Material Master seed data, merging the original Master Price List with the new document's rate categories (steel profiles, glass, aluminium track, slatwall, substructure materials).
- Confirm the "Separate Top" case (e.g. stone counter tops) — the source document explicitly leaves this as a manual, separate calculation outside the tool. Decide whether to formalize stone/solid-surface tops as their own simple typology or keep it manual.
- Validate each typology's panel decomposition (which named panels exist, e.g. bottom panel presence/absence in Horizontal Box) against real shop practice before coding it as ground truth.

## Tech Stack Recommendation

Unchanged from v1: FastAPI + SQLAlchemy + PostgreSQL, deployed on Railway, Alembic migrations from day one, its own dedicated database and repo — matching the pattern already working for ConstructTrack and Engineering-Management-App.

## Deferred / Future Ideas (not v1)

- AI-assisted dimension pre-fill from drawings, as an assistive/human-confirmed layer, once the core manual-entry workflow is proven.
- Multi-item sheet-nesting optimization across a whole project.
- Branding on printed outputs.
- Grain-direction material flag, if it becomes a recurring issue.
- Formalizing "Separate Top" (stone/solid-surface) as its own typology if it comes up often enough to be worth automating.

## How to Resume This Work

Point Claude at this file, the original `Shopfitting Costing Tool 1 - Revision D.xlsx`, and `instructions on setting up excel.docx`, and say what you want to start on — e.g. "let's nail down the real labour rates and wastage factors" or "let's design the database schema for the five typologies." No need to re-explain the background; it's all here.
