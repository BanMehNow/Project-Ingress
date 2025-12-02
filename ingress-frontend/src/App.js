import React, { useState } from "react";
import "./App.css";
// ↑ React + your CSS styling for the UI.

const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI dev server
// ↑ Base URL for all backend API calls (local dev).

function App() {
  // -----------------------------
  // State
  // -----------------------------
  const [selectedFile, setSelectedFile] = useState(null);
  // ↑ Holds currently chosen file (if any).

  const [urlInput, setUrlInput] = useState("");
  // ↑ Holds URL text typed by the user.

  const [preview, setPreview] = useState(null);      // holds PreviewResponse
  // ↑ Full preview object returned by backend (columns, sample, etc.).

  const [sessionId, setSessionId] = useState(null);  // from backend
  // ↑ Session ID that links frontend to backend-stored data.

  const [loading, setLoading] = useState(false);
  // ↑ True while ingestion request is in-flight.

  const [error, setError] = useState("");
  // ↑ Error message for UI display.

  const [message, setMessage] = useState("");
  // ↑ Success/info message for UI display.

  const [isExporting, setIsExporting] = useState(false);
  // ↑ True while export request is running.

  const [exportError, setExportError] = useState("");
  // ↑ Export error message.

  // -----------------------------
  // Input handlers
  // -----------------------------
  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0] || null);
    setError("");
    setMessage("");
    // ↑ Reset messages whenever the user picks a new file.
  };

  const handleUrlChange = (e) => {
    setUrlInput(e.target.value);
    setError("");
    setMessage("");
    // ↑ Reset messages whenever the user changes the URL input.
  };

  // -----------------------------
  // Submit → call ingest/file OR ingest/url
  // -----------------------------
  const handleSubmit = async (e) => {
    e.preventDefault();
    // ↑ Stop the default form submission.

    setError("");
    setMessage("");
    setPreview(null);
    setSessionId(null);
    setExportError("");
    // ↑ Clear previous state before a new ingest.

    const hasFile = !!selectedFile;
    const hasUrl = urlInput.trim().length > 0;

    if (!hasFile && !hasUrl) {
      setError("Please choose a file or enter a URL.");
      return;
      // ↑ Basic validation: must provide at least one source.
    }

    try {
      setLoading(true);

      const formData = new FormData();
      let endpoint = "";

      if (hasFile) {
        endpoint = "/ingest/file";
        formData.append("file", selectedFile);
        // ↑ File upload path & payload.
      } else {
        endpoint = "/ingest/url";
        formData.append("url", urlInput.trim());
        // ↑ URL ingestion path & payload.
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error (${response.status}): ${text}`);
        // ↑ Surface backend errors clearly in UI.
      }

      const json = await response.json();
      // json is a PreviewResponse:
      // { session_id, source, detected_type, columns, sample, meta, message }

      setPreview(json);
      setSessionId(json.session_id || null);

      const rows = Array.isArray(json.sample) ? json.sample.length : 0;
      setMessage(`Loaded ${rows} preview row${rows === 1 ? "" : "s"}.`);
      // ↑ Friendly status showing how many rows were pulled into preview.
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------
  // Helper to compute columns/rows for table
  // -----------------------------
  const columns =
    preview && Array.isArray(preview.columns)
      ? preview.columns
      : [];
  // ↑ Safe extraction of column names from preview.

  const rows =
    preview && Array.isArray(preview.sample)
      ? preview.sample
      : [];
  // ↑ Safe extraction of preview sample rows.

  // -----------------------------
  // Export helpers
  // -----------------------------
  async function downloadFile(path, filename, fallbackExt = "txt") {
    // Generic helper for downloading any export from the backend.
    setIsExporting(true);
    setExportError("");

    try {
      const res = await fetch(`${API_BASE_URL}${path}`);

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Export failed (${res.status}): ${text}`);
      }

      const blob = await res.blob();

      let ext = fallbackExt;
      const ct = res.headers.get("content-type") || "";
      // ↑ Infer file extension from content-type if provided.

      if (ct.includes("csv")) ext = "csv";
      else if (ct.includes("json")) ext = "json";
      else if (ct.includes("pdf")) ext = "pdf";

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      // ↑ Standard blob download pattern: create hidden link and click it.
    } catch (err) {
      console.error(err);
      setExportError(err.message || "Export failed.");
    } finally {
      setIsExporting(false);
    }
  }

  const handleExportDataset = () => {
    if (!sessionId) return;
    downloadFile(`/export/${sessionId}`, `ingress_dataset_${sessionId}`, "csv");
    // ↑ Calls backend dataset export (CSV/JSON) for current session.
  };

  const handleExportDatabook = () => {
    if (!sessionId) return;
    downloadFile(
      `/export/databook/${sessionId}`,
      `ingress_databook_${sessionId}`,
      "json" // change to "pdf" if your databook export is PDF
    );
    // ↑ Calls backend databook export for current session.
  };

  // -----------------------------
  // Render
  // -----------------------------
  return (
    <div className="app">
      <header className="app-header">
        <h1>Project Ingress</h1>
        <p>URL / Document → Tidy Dataset</p>
        {/* ↑ App title + one-line description */}
      </header>

      <main className="app-main">
        {/* 1 & 2: Source selection + ingest button */}
        <form className="ingest-form" onSubmit={handleSubmit}>
          <div className="form-section">
            <h2>1. Choose a source</h2>

            <div className="field">
              <label htmlFor="file-input">Upload file (CSV, PDF, JSON, etc.)</label>
              <input id="file-input" type="file" onChange={handleFileChange} />
              {selectedFile && <small>Selected: {selectedFile.name}</small>}
              {/* ↑ Show the name of the selected file */}
            </div>

            <div className="divider">or</div>

            <div className="field">
              <label htmlFor="url-input">Paste a URL</label>
              <input
                id="url-input"
                type="text"
                placeholder="https://example.com/data"
                value={urlInput}
                onChange={handleUrlChange}
              />
            </div>
          </div>

          <div className="form-section">
            <h2>2. Ingest</h2>
            <button type="submit" disabled={loading}>
              {loading ? "Processing..." : "Run Ingress"}
            </button>
            {/* ↑ Ingest trigger; shows a spinner text while loading */}
          </div>
        </form>

        {/* Status messages */}
        <section className="status-section">
          {error && <div className="status status-error">{error}</div>}
          {message && <div className="status status-ok">{message}</div>}
        </section>

        {/* 3. Preview table */}
        <section className="results-section">
          <h2>3. Preview dataset</h2>
          {loading && <p>Loading data...</p>}
          {!loading && (!rows || rows.length === 0) && (
            <p>No data loaded yet. Submit a file or URL to see a preview.</p>
          )}

          {!loading && rows && rows.length > 0 && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => (
                    <tr key={idx}>
                      {columns.map((col) => (
                        <td key={col}>
                          {row && row[col] !== undefined && row[col] !== null
                            ? String(row[col])
                            : ""}
                          {/* ↑ Stringify values and avoid “undefined/null” in cells */}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 4. Export section */}
        {sessionId && (
          <section className="results-section">
            <h2>4. Export</h2>
            <p className="export-session">
              Current session: <code>{sessionId}</code>
            </p>

            <div className="export-buttons">
              <button onClick={handleExportDataset} disabled={isExporting}>
                Download Dataset
              </button>
              <button
                onClick={handleExportDatabook}
                disabled={isExporting}
                style={{ marginLeft: "10px" }}
              >
                Download Databook
              </button>
            </div>

            {isExporting && (
              <p className="status status-ok">Preparing export…</p>
            )}
            {exportError && (
              <p className="status status-error">Export error: {exportError}</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
// ↑ Export the root component so Vite/React can render it.
