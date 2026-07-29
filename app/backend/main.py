from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import customers, external, genie, jobs

app = FastAPI(title="Customer 360")

app.include_router(customers.router)
app.include_router(external.router)
app.include_router(genie.router)
app.include_router(jobs.router)


@app.get("/api/config")
def config():
    return {
        "databricks_host": os.environ["DATABRICKS_HOST"],
        "dashboard_id": os.environ["DASHBOARD_ID"],
        "genie_space_id": os.environ["GENIE_SPACE_ID"],
    }


_static = Path(__file__).parent / "static"
if _static.exists():
    app.mount("/assets", StaticFiles(directory=str(_static / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        return FileResponse(_static / "index.html")
