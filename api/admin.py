from fastapi import APIRouter
from core.services import migrations_service


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/run-migrations/{password}", status_code=200)
async def run_migrations(password: str):
    return migrations_service.run_migrations(password)


@router.get("/pending-migrations")
async def check_pending_migrations():
    return migrations_service.get_pending_migrations()
