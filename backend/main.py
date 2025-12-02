from typing import Optional
# ↑ Used so parameters can be file OR url (optional types).

from io import StringIO
# ↑ Allows treating CSV text as a file-like object for pandas.

import pandas as pd
import requests
# ↑ Pandas for CSV parsing, requests for URL ingestion.

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# ↑ FastAPI application + file upload + form handling + error management.

from fastapi.middleware.cors import CORSMiddleware
# ↑ Enables React frontend (localhost:3000) to call the FastAPI backend.


# Your existing routers
from .routers import ingest
from .routers import export
# ↑ Bring in your two main feature routers:
#   - ingest → handles file/URL ingestion + previews
#   - export → handles CSV/JSON/DataBook exports


app = FastAPI()
# ↑ Create main FastAPI application instance.


# CORS so React (localhost:3000) can talk to FastAPI (localhost:8000)
origins = [
    "http://localhost:3000",
]
# ↑ Allowed origins list for browser cross-origin requests.


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Frontend allowed to access backend
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP verbs (GET, POST, etc.)
    allow_headers=["*"],          # Allow all headers
)
# ↑ Without this, the browser would block API calls due to CORS.


# Include your router modules
app.include_router(ingest.router)
app.include_router(export.router)
# ↑ These bring in /ingest/* and /export/* endpoint groups into the app.


@app.get("/")
def root():
    # ↑ Basic root endpoint to check if API is running.
    return {"message": "Project Ingress backend is running!"}


@app.get("/health")
def health():
    # ↑ Healthcheck endpoint, useful for deployment pipelines.
    return {"status": "ok"}


# ---------------------------------------------------------
# Legacy/extra generic CSV ingestion endpoint
# (Your real ingest logic now lives in routers/ingest.py)
# ---------------------------------------------------------

@app.post("/ingest")
async def ingest_endpoint(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
):
    """
    Ingest CSV from either an uploaded file OR a URL.
    Returns list-of-dicts suitable for a React table preview.

    NOTE:
    This is a simple CSV-only endpoint kept for compatibility,
    while the advanced ingestion logic (multi-format) is in /ingest/file and /ingest/url.
    """

    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or URL.")

    # ---------------------------------------------------------
    # 1. Load text from uploaded file OR URL
    # ---------------------------------------------------------
    if file is not None:
        # Handle uploaded file
        try:
            raw = await file.read()           # Read bytes from upload
            csv_text = raw.decode("utf-8")    # Decode to text
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read uploaded file: {exc}"
            )
    else:
        # Handle URL ingestion
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            csv_text = resp.text              # Raw CSV text from server
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch URL: {exc}"
            )

    # ---------------------------------------------------------
    # 2. Parse CSV with pandas
    # ---------------------------------------------------------
    try:
        df = pd.read_csv(StringIO(csv_text))
        # ↑ StringIO pretends the CSV text is a file so pandas can read it.
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"CSV parsing failed: {exc}"
        )

    if df.empty:
        return []
        # ↑ Return empty list instead of an empty DataFrame for cleaner UI usage.

    # Clean headers (quality-of-life improvement)
    df = df.rename(columns=lambda c: str(c).strip().replace("\n", " "))
    # ↑ Remove newlines/spaces from header names.

    # ---------------------------------------------------------
    # 3. Return JSON rows to React frontend
    # ---------------------------------------------------------
    return df.to_dict(orient="records")
    # ↑ Convert DataFrame → list of dicts → perfect for tables in React.
