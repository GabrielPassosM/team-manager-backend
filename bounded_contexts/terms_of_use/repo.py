from uuid import UUID

from sqlalchemy import delete
from sqlmodel import select

from bounded_contexts.terms_of_use.models import TermsOfUse, UserTermsAcceptance
from core.repo import BaseRepo


class TermsOfUseWriteRepo(BaseRepo):
    def create_without_commit(self, content: str, version: int) -> None:
        if self.session.exec(
            select(TermsOfUse.version).where(TermsOfUse.is_active == True)
        ).first():
            raise ValueError("An active Terms of Use version already exists.")

        terms = TermsOfUse(
            content=content,
            version=version,
            is_active=True,
        )
        self.session.add(terms)

    def deactivate_current_without_commit(self) -> None:
        active_terms = self.session.exec(
            select(TermsOfUse).where(TermsOfUse.is_active == True)
        ).first()
        if active_terms:
            active_terms.is_active = False
            self.session.add(active_terms)
            self.session.flush()


class TermsOfUseReadRepo(BaseRepo):
    def get_active_version(self) -> int | None:
        return self.session.exec(
            select(TermsOfUse.version).where(TermsOfUse.is_active == True)
        ).first()

    def get_active_terms_of_use(self) -> TermsOfUse | None:
        return self.session.exec(
            select(TermsOfUse).where(TermsOfUse.is_active == True)
        ).first()

    def get_by_version(self, version: int) -> TermsOfUse | None:
        return self.session.exec(
            select(TermsOfUse).where(TermsOfUse.version == version)
        ).first()


class UserTermsAcceptanceWriteRepo(BaseRepo):
    def create_without_commit(self, user_id: UUID, terms_version: int) -> None:
        acceptance = UserTermsAcceptance(
            user_id=user_id,
            terms_version=terms_version,
        )
        self.session.add(acceptance)

    def hard_delete_by_user_ids(self, user_ids: list[UUID]) -> None:
        self.session.exec(
            delete(UserTermsAcceptance).where(  # type: ignore
                UserTermsAcceptance.user_id.in_(user_ids)
            )
        )
