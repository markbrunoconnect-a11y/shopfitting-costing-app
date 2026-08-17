"""
Shopfitting Costing App - main application entry point.

Schema is managed by Alembic migrations (see backend/alembic/), run via
`alembic upgrade head` as part of the deploy start command - not by
create_all() here. That mistake caused a real schema-drift outage in
Engineering-Management-App and isn't being repeated.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routers import auth, materials, projects, items, settings, amalgamator

app = FastAPI(title="Shopfitting Costing App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(materials.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(amalgamator.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "Shopfitting Costing App"}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/")
@app.get("/app")
@app.get("/app/")
def serve_app():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
