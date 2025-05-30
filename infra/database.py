from sqlmodel import create_engine, Session

from core.settings import DATABASE_URL


engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine, autoflush=False) as session:
        yield session
