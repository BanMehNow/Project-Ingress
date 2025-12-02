from fastapi import APIRouter, UploadFile, File, HTTPException, Form
# ↑ FastAPI routing & form/file handling.

from typing import Dict, Any
# ↑ Used for type hints in helper functions.

import io
import json
import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup
# ↑ Libraries used for parsing CSV/JSON/HTML/PDF and making HTTP requests.

from ..services.session_store import new_session, get_session
# ↑ In-memory session store for saving raw bytes + metadata.

from ..models.preview import PreviewResponse
# ↑ Response model used by the frontend for consistent preview structure.

router = APIRouter(prefix="/ingest", tags=["ingest"])
# ↑ Groups all ingestion-related endpoints under /ingest/*.


# -------- helpers --------

def _df_preview(df: pd.DataFrame, max_rows: int = 10) -> Dict[str, Any]:
    # ↑ Converts a DataFrame into a lightweight preview.
    df = df.reset_index(drop=True)
    return {
        "columns": list(map(str, df.columns)),
        # ↑ Convert column names to strings for JSON safety.

        "sample": df.head(max_rows).to_dict(orient="records"),
        # ↑ First N rows converted to list of dictionaries.
    }


def _detect_from_filename(name: str) -> str:
    # ↑ Very simple extension-based file type detection.
    n = (name or "").lower()
    if n.endswith(".csv"):
        return "csv"
    if n.endswith(".json"):
        return "json"
    if n.endswith(".html") or n.endswith(".htm"):
        return "html"
    if n.endswith(".pdf"):
        return "pdf"
    return "unknown"


def _parse_bytes(data: bytes, detected: str) -> Dict[str, Any]:
    """
    Return a lightweight preview (columns + sample rows)
    from raw bytes for multiple formats.
    """

    # CSV
    if detected == "csv":
        df = pd.read_csv(io.BytesIO(data))
        return _df_preview(df)

    # JSON (array, object, or nested JSON)
    if detected == "json":
        try:
            df = pd.read_json(io.BytesIO(data))
        except ValueError:
            # fallback: maybe JSON object, need to normalise
            obj = json.loads(data.decode("utf-8", errors="ignore"))
            df = pd.json_normalize(obj)
        return _df_preview(df)

    # HTML (prefer tables; fallback to <li> text extraction)
    if detected == "html":
        try:
            tables = pd.read_html(io.BytesIO(data))
            if tables:
                return _df_preview(tables[0])
        except Exception:
            pass

        # fallback: extract list items
        soup = BeautifulSoup(data, "lxml")
        items = [li.get_text(strip=True) for li in soup.select("li")]
        df = pd.DataFrame({"item": items})
        return _df_preview(df)

    # PDF (prefer first table on first page; fallback to raw text lines)
    if detected == "pdf":
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if not pdf.pages:
                raise HTTPException(400, "PDF has no pages")

            p0 = pdf.pages[0]
            table = p0.extract_table()

            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                return _df_preview(df)

            # fallback: text lines
            text = p0.extract_text() or ""
            lines = [ln for ln in text.splitlines() if ln.strip()]
            df = pd.DataFrame({"line": lines})
            return _df_preview(df)

    # unknown type → last-ditch attempt: treat as CSV
    try:
        df = pd.read_csv(io.BytesIO(data))
        return _df_preview(df)
    except Exception:
        return {"columns": [], "sample": []}
        # ↑ Fallback for absolutely unparseable content.


# ------- Data Book helpers (for the second artefact) -------

def _infer_dtype(series: pd.Series) -> str:
    """Map pandas dtypes to friendly DataBook types."""
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "string"


def _build_databook(df: pd.DataFrame, source: str) -> Dict[str, Any]:
    """
    Build a lightweight Data Book:
    - inferred schema
    - basic stats per column
    - provenance log
    """

    columns_meta = []
    for col in df.columns:
        s = df[col]
        inferred_type = _infer_dtype(s)
        non_null = int(s.notna().sum())
        nulls = int(s.isna().sum())

        # Convert sample values to strings so they are JSON-safe.
        sample_vals = [str(v) for v in s.dropna().unique()[:3]]

        col_meta: Dict[str, Any] = {
            "name": str(col),
            "inferred_type": inferred_type,
            "non_null_values": non_null,
            "null_values": nulls,
            "sample_values": sample_vals,
        }

        # add numeric min/max
        if inferred_type in ("integer", "float") and non_null > 0:
            col_meta["min"] = float(s.min())
            col_meta["max"] = float(s.max())

        columns_meta.append(col_meta)

    return {
        "source": source,
        "column_count": len(df.columns),
        "row_count": int(len(df)),
        "columns": columns_meta,
        "processing_log": [
            "Loaded into pandas DataFrame",
            "Inferred basic column types from dtypes",
            "Computed non-null counts and sample values",
        ],
    }


def _load_df_for_databook(raw: bytes, detected: str, filename: str) -> pd.DataFrame:
    """
    Load a DataFrame suitable for Data Book generation.
    For feasibility → support only CSV and JSON.
    """
    if detected == "csv":
        return pd.read_csv(io.BytesIO(raw))

    if detected == "json":
        try:
            return pd.read_json(io.BytesIO(raw))
        except ValueError:
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            return pd.json_normalize(obj)

    raise HTTPException(
        400,
        f"Data Book currently supports CSV/JSON. Detected '{detected}' for {filename}.",
    )


# -------- endpoints --------

@router.post("/file", response_model=PreviewResponse)
async def ingest_file(file: UploadFile = File(...)):
    """
    Upload and ingest a file, returning a preview (columns + sample)
    and saving raw bytes into a session for later export.
    """
    raw = await file.read()
    detected = _detect_from_filename(file.filename)
    preview = _parse_bytes(raw, detected)

    # response returned to client
    public = {
        "source": "file",
        "detected_type": detected,
        "columns": preview["columns"],
        "sample": preview["sample"],
        "meta": {"filename": file.filename, "size_bytes": len(raw)},
        "message": None,
    }

    # data stored in session (includes raw bytes)
    store = {**public, "raw": raw}

    sid = new_session(store)
    return PreviewResponse(session_id=sid, **public)


@router.post("/url", response_model=PreviewResponse)
async def ingest_url(url: str = Form(...)):
    """
    Fetch a URL, auto-detect its content type, parse it,
    and return a preview while saving the raw response.
    """
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch URL: {e}")

    detected = _detect_from_filename(url)

    # Fallback: guess based on content-type header.
    if detected == "unknown":
        ct = (r.headers.get("content-type") or "").lower()
        if "json" in ct:
            detected = "json"
        elif "html" in ct:
            detected = "html"
        elif "pdf" in ct:
            detected = "pdf"
        elif "csv" in ct or "text/plain" in ct:
            detected = "csv"

    preview = _parse_bytes(r.content, detected)

    public = {
        "source": "url",
        "detected_type": detected,
        "columns": preview["columns"],
        "sample": preview["sample"],
        "meta": {"url": url, "http_status": r.status_code},
        "message": None,
    }
    store = {**public, "raw": r.content}
    sid = new_session(store)
    return PreviewResponse(session_id=sid, **public)


@router.get("/preview/{session_id}", response_model=PreviewResponse)
def get_preview(session_id: str):
    """
    Retrieve a previously stored preview by session ID.
    """
    data = get_session(session_id)
    if not data:
        raise HTTPException(404, "Session not found")
    return PreviewResponse(session_id=session_id, **data)


# -------- NEW: Data Book preview endpoint --------

@router.post("/databook/file", response_model=PreviewResponse)
async def databook_from_file(file: UploadFile = File(...)):
    """
    Upload CSV/JSON and return:
    - standard preview (columns + sample)
    - Data Book preview embedded in meta['databook']

    This is the SECOND ARTEFACT for feasibility demo.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Uploaded file is empty.")

    detected = _detect_from_filename(file.filename)

    try:
        df = _load_df_for_databook(raw, detected, file.filename)
    except HTTPException:
        # re-raise clean errors
        raise
    except Exception as e:
        raise HTTPException(400, f"Failed to build Data Book: {e}")

    preview = _df_preview(df)
    databook = _build_databook(df, source=f"file:{file.filename}")

    public = {
        "source": "file",
        "detected_type": detected,
        "columns": preview["columns"],
        "sample": preview["sample"],
        "meta": {
            "filename": file.filename,
            "size_bytes": len(raw),
            "databook": databook,   # ← NEW: embedded Data Book preview
        },
        "message": None,
    }

    store = {**public, "raw": raw}
    sid = new_session(store)
    return PreviewResponse(session_id=sid, **public)
