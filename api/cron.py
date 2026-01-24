from fastapi import APIRouter, Depends

router = APIRouter(prefix="/cron", tags=["Cronjobs"])


@router.get("/test")
def test_cron():
    return {"status": "ok"}
