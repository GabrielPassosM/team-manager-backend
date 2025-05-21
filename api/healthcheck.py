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
