from fastapi import APIRouter, Depends, File, UploadFile

from bounded_contexts.storage.exceptions import FailedUploadStorage
from bounded_contexts.storage.service import upload_team_emblem
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token

router = APIRouter(prefix="/bucket", tags=["Storage"])


@router.post("/upload-emblem")
async def upload_emblem_image(
    file: UploadFile = File(...),
    current_user: User = Depends(validate_user_token),
) -> str:
    if not current_user.is_admin:
        raise AdminRequired()

    try:
        public_url = await upload_team_emblem(file, str(current_user.team_id))
        return public_url
    except Exception:
        raise FailedUploadStorage()
