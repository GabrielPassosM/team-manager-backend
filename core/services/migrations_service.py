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

        head_rev = script.get_current_head()

        if current_rev == head_rev:
            return {"pending": False, "current_revision": current_rev}
        else:
            revisions = []
            for rev in script.walk_revisions():
                if not current_rev or rev.revision > current_rev:
                    revisions.append(
                        {
                            "revision": rev.revision,
                            "message": rev.doc,
                        }
                    )

            return {
                "pending": True,
                "current_revision": current_rev,
                "head_revision": head_rev,
                "pending_migrations": list(reversed(revisions)),
            }
