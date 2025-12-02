from typing import List, Dict, Any, Optional
# ↑ Importing standard Python typing hints so we can describe the shape of data
#   List[str] = list of strings, Dict[str, Any] = dictionary with any values, etc.

from pydantic import BaseModel
# ↑ Pydantic is used to validate and structure data models for FastAPI responses.


class PreviewResponse(BaseModel):
    # ↑ Define a response model that FastAPI will use when returning preview data.
    #   This ensures consistent structure and automatic validation.

    session_id: str
    # ↑ Unique ID for the user’s ingestion session.
    #   Used so frontend can request exports or further steps using this session.

    source: str                   # "file" | "url"
    # ↑ Records whether the input came from a file upload or a URL fetch.

    detected_type: str            # csv | json | html | pdf | unknown
    # ↑ The system's best guess at what type of document was ingested.
    #   Helps the frontend decide how to render previews (e.g., table vs JSON view).

    columns: List[str]
    # ↑ A list of column names detected or generated during parsing.
    #   This is important for building the table structure in the UI.

    sample: List[Dict[str, Any]]
    # ↑ A preview of the first few rows/records.
    #   Usually the first 5–10 entries — shown in the frontend table so users see results immediately.

    meta: Dict[str, Any] = {}
    # ↑ Optional metadata such as file size, row count, parsing confidence, logs, etc.
    #   Default is empty because not all parsers return extra information.

    message: Optional[str] = None
    # ↑ Optional message for warnings, errors, or notes.
    #   Example: “Table detected with low confidence” or “Some rows were skipped.”
