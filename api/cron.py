from fastapi import APIRouter, Depends

router = APIRouter(prefix="/cron", tags=["Cronjobs"])


@router.post("/test")
def test_cron():
    return {"status": "ok"}
