from typing import Dict, Any, Optional
# ↑ Type hints: Dict for session storage, Optional for safe returns.

from uuid import uuid4
# ↑ Generates unique session IDs so each upload/URL ingest is tracked separately.


# super-simple in-memory store (resets when server restarts)
_SESSIONS: Dict[str, Dict[str, Any]] = {}
# ↑ This dictionary holds all active sessions:
#   - key: session_id (string)
#   - value: stored payload (preview, metadata, raw bytes, etc.)
#   NOTE: Stored in RAM → disappears if server restarts.


def new_session(payload: Dict[str, Any]) -> str:
    # ↑ Create a new session and store the data inside the in-memory dict.

    sid = uuid4().hex
    # ↑ Generate a random hex string (unique session ID).

    _SESSIONS[sid] = payload
    # ↑ Save the preview/raw bytes/meta under this session ID.

    return sid
    # ↑ Return the ID so FastAPI can send it back to the client.


def get_session(sid: str) -> Optional[Dict[str, Any]]:
    # ↑ Retrieve a session payload by its ID.

    return _SESSIONS.get(sid)
    # ↑ Returns the stored data, or None if the ID doesn’t exist.
