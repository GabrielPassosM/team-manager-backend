from uuid import UUID

from pydantic import BaseModel

from core.schemas import BaseSchema


class AcceptTermsData(BaseModel):
    user_id: UUID
    terms_version: int


class TermsOfUseResponse(BaseSchema):
    id: UUID
    version: int
    content: str
    is_active: bool
