from infra.database import get_session
from sqlmodel import Session


class BaseRepo:
    def __init__(self, session: Session | None = None):
        if not session:
            session = get_session()
        self.session = session
