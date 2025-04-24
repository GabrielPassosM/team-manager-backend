from fastapi import FastAPI


app = FastAPI(
    title="Team Manager Backend",
    version="1.0.0",
)


@app.get("/", status_code=200)
async def index():
    return {"Hello": "World"}
