#!/bin/bash
set -e
python -c "from alembic.config import main; main(['upgrade', 'head'])"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
