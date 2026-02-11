from fastapi import UploadFile

from core.settings import TEAMS_BUCKET, ENV_CONFIG
from infra.supabase_sdk import supabase


async def upload_team_emblem(file: UploadFile, team_id: str) -> str:
    file_content: bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    file_path = f"{team_id}/emblem/emblem.{file_extension}"

    return _make_upload(file_path, file_content, file.content_type)


async def upload_player_image(file: UploadFile, team_id: str, player_id: str) -> str:
    file_content: bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    file_path = f"{team_id}/players/{player_id}.{file_extension}"

    return _make_upload(file_path, file_content, file.content_type)


def delete_player_image_from_bucket(image_url: str) -> None:
    file_path = image_url.split(f"/{TEAMS_BUCKET}/")[-1]
    if file_path[-1] == "?":
        file_path = file_path[:-1]

    if ENV_CONFIG == "test":
        return

    supabase.storage.from_(TEAMS_BUCKET).remove([file_path])


def _make_upload(file_path: str, file_content: bytes, content_type: str) -> str:
    supabase.storage.from_(TEAMS_BUCKET).remove([file_path])

    supabase.storage.from_(TEAMS_BUCKET).upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": content_type},
    )

    public_url = supabase.storage.from_(TEAMS_BUCKET).get_public_url(file_path)
    return public_url


def delete_all_players_images(team_id: str) -> None:
    folder_path = f"{team_id}/players"

    response = supabase.storage.from_(TEAMS_BUCKET).list(folder_path)

    if not response:
        return

    files_to_remove = [
        f"{folder_path}/{file['name']}" for file in response if file.get("name")
    ]

    if files_to_remove:
        supabase.storage.from_(TEAMS_BUCKET).remove(files_to_remove)
