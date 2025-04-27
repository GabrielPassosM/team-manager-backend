from fastapi import FastAPI

from api import admin

app = FastAPI(
    title="Team Manager Backend",
    version="1.0.0",
)

app.include_router(admin.router)


@app.get("/", status_code=200)
async def index():
    return {"Hello": "World"}
