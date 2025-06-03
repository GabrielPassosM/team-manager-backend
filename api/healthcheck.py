import sys

from fastapi import APIRouter, Depends
from sqlmodel import Session
from sqlalchemy import text

from infra.database import get_session

router = APIRouter(tags=["Healthcheck"])


@router.get("/database-check", status_code=200)
async def database_startup_check(session: Session = Depends(get_session)):
    try:
        session.exec(text("SELECT 1"))
    except Exception:
        return {"status": "waiting connection"}
    return {"status": "ready"}


@router.get("/status", status_code=200)
async def status(session: Session = Depends(get_session)):
    query = text(
        """
            SELECT 
                (SELECT COUNT(*) FROM pg_stat_activity) AS active_connections,
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections
        """
    )

    result = session.exec(query)
    row = result.fetchone()
    return {
        "active_connections": row.active_connections,
        "max_connections": row.max_connections,
        "python_version": sys.version,
    }
