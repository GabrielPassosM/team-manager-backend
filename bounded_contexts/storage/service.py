from fastapi import UploadFile

from core.settings import TEAMS_BUCKET
from infra.supabase_sdk import supabase


async def upload_team_emblem(file: UploadFile, team_id: str) -> str:
    file_content: bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    file_path = f"{team_id}/emblem/emblem.{file_extension}"

    supabase.storage.from_(TEAMS_BUCKET).remove([file_path])

    supabase.storage.from_(TEAMS_BUCKET).upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type},
    )

    public_url = supabase.storage.from_(TEAMS_BUCKET).get_public_url(file_path)
    return public_url
