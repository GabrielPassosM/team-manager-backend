from sqlmodel import Session
from starlette.responses import JSONResponse

from bounded_contexts.terms_of_use.exceptions import TermsNotFound
from bounded_contexts.terms_of_use.models import TermsOfUse
from bounded_contexts.terms_of_use.repo import (
    UserTermsAcceptanceWriteRepo,
    TermsOfUseReadRepo,
)
from bounded_contexts.terms_of_use.schemas import AcceptTermsData
from bounded_contexts.user.exceptions import UserNotFound
from bounded_contexts.user.repo import UserReadRepo, UserWriteRepo
from core.services.auth import create_refresh_token


def accept_terms_of_use(
    acceptance_data: AcceptTermsData, session: Session
) -> JSONResponse:
    user = UserReadRepo(session).get_by_id(acceptance_data.user_id)
    if not user:
        raise UserNotFound()

    if not TermsOfUseReadRepo(session).get_by_version(acceptance_data.terms_version):
        raise TermsNotFound()

    UserTermsAcceptanceWriteRepo(session).create_without_commit(
        acceptance_data.user_id, acceptance_data.terms_version
    )

    user.terms_accepted_version = acceptance_data.terms_version
    UserWriteRepo(session).save(user, user.id)  # commit happens here

    response = JSONResponse(
        content=acceptance_data.model_dump(mode="json"), status_code=200
    )

    # Create and set refresh token in response because is part of login flow
    return create_refresh_token(
        response, user.id, acceptance_data.is_demo_user, session
    )


def get_active_terms_of_use(session: Session) -> TermsOfUse:
    active_terms = TermsOfUseReadRepo(session).get_active_terms_of_use()

    if not active_terms:
        raise TermsNotFound()

    return active_terms
