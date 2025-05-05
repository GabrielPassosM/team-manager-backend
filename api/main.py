from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

from api.admin import router as admin_router
from bounded_contexts.team.routers import router as team_router
from bounded_contexts.user.routers import router as user_router
from core import settings

security = HTTPBasic()

app = FastAPI(
    title="Team Manager Backend",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(admin_router)
app.include_router(team_router)
app.include_router(user_router)


@app.get("/", status_code=200)
async def index():
    return {"Hello": "World"}


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
