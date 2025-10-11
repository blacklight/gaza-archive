import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ._ctx import get_ctx

app = FastAPI(
    title="Gaza Verified Archive API",
    description="API for accessing the Gaza Verified Archive data.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)

config = get_ctx().config
dist_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../frontend/dist")
)
assets_dir = os.path.join(dist_dir, "assets")
templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
templates = Jinja2Templates(directory=templates_dir)

app.mount("/assets", StaticFiles(directory=assets_dir), name="static")


def render_index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "accounts": list(get_ctx().db.get_accounts().values())},
    )


@app.get("/")
async def read_root(request: Request):
    return render_index(request)


# Database download endpoint
@app.get("/app.db")
async def download_database():
    return FileResponse(
        os.path.join(config.storage_path, "app.db"),
        media_type="application/octet-stream",
        filename="app.db",
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(dist_dir, "favicon.ico"))


@app.get("/media/{file_path:path}")
async def serve_media(_: Request, file_path: str = ""):
    media_root = Path(config.storage_path) / "media"
    requested_path = media_root / file_path

    # Security check - ensure we're not going outside media directory
    try:
        requested_path = requested_path.resolve()
        media_root = media_root.resolve()
        requested_path.relative_to(media_root)
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail="Not found")

    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    # If it's a file, serve it directly
    if requested_path.is_file():
        return FileResponse(requested_path)

    # If it's a directory, show directory listing
    if requested_path.is_dir():
        items = []

        # Add parent directory link if not at root
        if file_path:
            parent_path = (
                str(Path(file_path).parent)
                if Path(file_path).parent != Path(".")
                else ""
            )
            items.append(
                {
                    "name": "../",
                    "is_dir": True,
                    "path": f"/media/{parent_path}",
                    "size": "-",
                }
            )

        # List directory contents
        for item in sorted(requested_path.iterdir()):
            relative_item_path = file_path + "/" + item.name if file_path else item.name
            items.append(
                {
                    "name": item.name + ("/" if item.is_dir() else ""),
                    "is_dir": item.is_dir(),
                    "path": f"/media/{relative_item_path}",
                    "size": f"{item.stat().st_size} bytes" if item.is_file() else "-",
                }
            )

        # Generate HTML directory listing
        html_content = f"""
        <html>
        <head><title>Index of /media/{file_path}</title></head>
        <body>
        <h1>Index of /media/{file_path}</h1>
        <table style="width: 30em; max-width: 90%; border-collapse: collapse">
        <tr><th>Name</th><th>Size</th></tr>
        """

        for item in items:
            html_content += f'<tr><td><a href="{item["path"]}">{item["name"]}</a></td><td>{item["size"]}</td></tr>'

        html_content += """
        </table>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)


@app.get("/media")
async def serve_media_root(request: Request):
    return await serve_media(request, "")
