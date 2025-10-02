from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.htmls.index_html import INDEX_HTML
from core import settings
from api.admin import router as admin_router
from api.healthcheck import router as healthcheck_router
from bounded_contexts.team.routers import router as team_router
from bounded_contexts.user.routers import router as user_router
from bounded_contexts.storage.routers import router as storage_router
from bounded_contexts.championship.routers import router as championship_router
from bounded_contexts.player.routers import router as player_router
from bounded_contexts.game_and_stats.game.routers import router as game_router
from bounded_contexts.game_and_stats.stats.routers import router as stats_router
from bounded_contexts.game_and_stats.availability.routers import (
    router as availability_router,
)
from infra.logger import configure_logger

security = HTTPBasic()
configure_logger()

app = FastAPI(
    title="Team Manager Backend",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

origins = [
    "http://localhost:5173",
    "https://forquilha.app.br",
    "https://www.forquilha.app.br",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(team_router)
app.include_router(user_router)
app.include_router(storage_router)
app.include_router(healthcheck_router)
app.include_router(championship_router)
app.include_router(player_router)
app.include_router(game_router)
app.include_router(stats_router)
app.include_router(availability_router)


@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.exception(f"Erro inesperado em {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno no servidor. Tente novamente mais tarde."},
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=INDEX_HTML, status_code=200)


def _verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if settings.ENV_CONFIG not in ["production", "homolog"]:
        return credentials

    if (
        credentials.username != settings.SWAGGER_USERNAME
        or credentials.password != settings.SWAGGER_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    credentials: HTTPBasicCredentials = Depends(_verify_credentials),
):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(credentials: HTTPBasicCredentials = Depends(_verify_credentials)):
    return JSONResponse(app.openapi())
