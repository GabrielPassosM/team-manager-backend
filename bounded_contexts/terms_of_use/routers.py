from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette.responses import JSONResponse

from bounded_contexts.terms_of_use import service
from bounded_contexts.terms_of_use.schemas import AcceptTermsData, TermsOfUseResponse
from infra.database import get_session

router = APIRouter(prefix="/terms_of_use", tags=["Terms of Use"])


@router.post("/accept", status_code=200)
async def accept_terms_of_use(
    acceptance_data: AcceptTermsData, session: Session = Depends(get_session)
) -> JSONResponse:
    return service.accept_terms_of_use(acceptance_data, session)


@router.get("/active", status_code=200)
async def get_active_terms_of_use(
    session: Session = Depends(get_session),
) -> TermsOfUseResponse:
    terms_of_use = service.get_active_terms_of_use(session)
    return TermsOfUseResponse.model_validate(terms_of_use)
