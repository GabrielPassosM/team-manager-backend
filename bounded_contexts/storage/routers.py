from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from bounded_contexts.storage.exceptions import FailedUploadStorage
from bounded_contexts.storage import service
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token

router = APIRouter(prefix="/bucket", tags=["Storage"])


@router.post("/upload-emblem")
async def upload_emblem_image(
    file: UploadFile = File(...),
    current_user: User = Depends(validate_user_token),
) -> str:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    try:
        public_url = await service.upload_team_emblem(file, str(current_user.team_id))
        return public_url
    except Exception:
        raise FailedUploadStorage()


@router.post("/upload-player-image/{player_id}")
async def upload_player_image(
    player_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(validate_user_token),
) -> str:
    try:
        public_url = await service.upload_player_image(
            file, str(current_user.team_id), str(player_id)
        )
        return public_url
    except Exception:
        raise FailedUploadStorage()
