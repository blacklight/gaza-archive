import os

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ._ctx import get_ctx

app = FastAPI(
    title="Gaza Verified Archive API",
    description="API for accessing the Gaza Verified Archive data.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)

dist_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../frontend/dist")
)
assets_dir = os.path.join(dist_dir, "assets")
templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
templates = Jinja2Templates(directory=templates_dir)

app.mount("/assets", StaticFiles(directory=assets_dir), name="static")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "accounts": list(get_ctx().db.get_accounts().values())},
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import FileResponse

    return FileResponse(os.path.join(dist_dir, "favicon.ico"))
