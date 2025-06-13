from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from fastapi import HTTPException
from sqlmodel import create_engine

from core import settings


def run_migrations(password: str) -> dict:
    if password != settings.MIGRATIONS_PWD:
        raise HTTPException(status_code=401, detail="Invalid password")

    try:
        base_dir = Path(__file__).resolve().parent.parent.parent
        alembic_cfg = Config(base_dir / "infra" / "alembic.ini")
        command.upgrade(alembic_cfg, "head")

        return {"message": "Migrations applied successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")


def get_pending_migrations():
    base_dir = Path(__file__).resolve().parent.parent.parent
    alembic_cfg = Config(base_dir / "infra" / "alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()

        head_revs = script.get_heads()  # pode haver mais de um head
        if current_rev in head_revs:
            return {"pending": False, "current_revision": current_rev}

        # Caminha da(s) head(s) até a current_rev
        revisions = list(script.iterate_revisions(head_revs, current_rev))

        return {
            "pending": True,
            "current_revision": current_rev,
            "head_revision": head_revs,
            "pending_migrations": [
                {
                    "revision": rev.revision,
                    "message": rev.doc,
                }
                for rev in reversed(revisions)  # do mais antigo para o mais novo
            ],
        }
