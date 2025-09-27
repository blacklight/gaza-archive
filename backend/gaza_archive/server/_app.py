from fastapi import FastAPI

app = FastAPI(
    title="Gaza Verified Archive API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)
