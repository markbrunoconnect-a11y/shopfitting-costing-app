"""
Read-only status feed for the Amalgamator (the cross-company reporting tool).

Unlike the other apps in this family, Shopfitting Costing had no existing
dashboard/reports router to reuse for a progress signal - projects here are
costing worksheets, not jobs with a lifecycle. So this endpoint does two
things the others didn't need to:

1. Reuses items.cost_analysis() for the one number that *does* already
   exist and mean something - the running total cost of everything costed
   on the project so far - rather than recalculating it separately.
2. Reads the new client_name/location/status fields added specifically for
   this integration (see models.Project and alembic/versions/0004).

Never accepts writes, and authenticates with its own single shared key (see
core/security.require_amalgamator_key) rather than a user login - the
Amalgamator has no user account here and shouldn't need one.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_amalgamator_key
from app.routers.items import cost_analysis
from app import models

router = APIRouter(prefix="/amalgamator", tags=["amalgamator"])


@router.get("/report")
def status_report(db: Session = Depends(get_db), _=Depends(require_amalgamator_key)):
    projects = db.query(models.Project).all()
    return {
        "app": "shopfitting_costing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": [_report_row(p, db) for p in projects],
    }


def _report_row(p: models.Project, db: Session):
    # cost_analysis() is a normal function underneath its route decoration -
    # its own router only requires a logged-in user at the router level, not
    # as a parameter this function reads - so it's safe to call directly.
    analysis = cost_analysis(p.id, db)
    item_count = len(analysis["items"])
    return {
        "client": p.client_name,
        "location": p.location,
        "project_name": p.name,
        "project_reference": p.project_number,
        "status": p.status,
        "delivery_date": p.expected_delivery_date.isoformat() if p.expected_delivery_date else None,
        "progress": {
            "item_count": item_count,
            "total_cost_zar": analysis["project_total"],
        },
        "source_project_id": p.id,
    }
