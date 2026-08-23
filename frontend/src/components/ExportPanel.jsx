import { useState } from "react";
import { api } from "../api/client";

const FORMATS = [
  { value: "json",       label: "Generic JSON",   desc: "Flat JSON — resolved values + confidence, no internal fields" },
  { value: "akeneo_csv", label: "CSV",            desc: "Structured CSV export format for PIM/ERP systems" },
];

export default function ExportPanel({ productId }) {
  const [format, setFormat] = useState("json");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.exportProduct(productId, format);
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);

      const blob = await res.blob();
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match ? match[1] : `veritas_export.${format === "json" ? "json" : "csv"}`;

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="export-panel card">
      <div className="export-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <h3>Export to PIM / ERP</h3>
      </div>

      <div className="format-list">
        {FORMATS.map((f) => (
          <label key={f.value} className={`format-option ${format === f.value ? "selected" : ""}`}>
            <input
              type="radio"
              name="export-format"
              value={f.value}
              checked={format === f.value}
              onChange={() => setFormat(f.value)}
            />
            <div className="format-info">
              <span className="format-label">{f.label}</span>
              <span className="format-desc">{f.desc}</span>
            </div>
          </label>
        ))}
      </div>

      {error && <div className="export-error">{error}</div>}

      <button
        className="btn btn-primary btn-sm"
        onClick={handleExport}
        disabled={loading}
        style={{ alignSelf: "flex-start" }}
      >
        {loading ? (
          <>
            <span className="mini-spinner" />
            Exporting…
          </>
        ) : (
          <>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Download {FORMATS.find((f) => f.value === format)?.label}
          </>
        )}
      </button>

      <style>{`
        .export-panel { margin-top: 20px; display: flex; flex-direction: column; gap: 14px; }
        .export-header {
          display: flex; align-items: center; gap: 8px;
        }
        .export-header h3 {
          font-family: var(--font-display);
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-secondary);
          font-weight: 600;
        }
        .format-list { display: flex; flex-direction: column; gap: 8px; }
        .format-option {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 10px 12px;
          border: 1px solid var(--border-soft);
          border-radius: var(--radius);
          cursor: pointer;
          transition: border-color var(--duration-fast) var(--ease), background var(--duration-fast) var(--ease);
        }
        .format-option:hover { border-color: var(--border); }
        .format-option.selected {
          border-color: var(--teal-dim);
          background: rgba(63,193,169,0.06);
        }
        .format-option input[type="radio"] { margin-top: 2px; accent-color: var(--teal); flex-shrink: 0; }
        .format-info { display: flex; flex-direction: column; gap: 2px; }
        .format-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
        .format-desc  { font-size: 11.5px; color: var(--text-secondary); font-family: var(--font-mono); }
        .export-error {
          padding: 8px 12px;
          border-radius: var(--radius);
          border: 1px solid var(--red-dim);
          color: var(--red);
          font-size: 12.5px;
          background: rgba(224,92,58,0.06);
        }
        .mini-spinner {
          display: inline-block; width: 12px; height: 12px;
          border: 2px solid rgba(7,20,18,0.3);
          border-top-color: #071412;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
      `}</style>
    </div>
  );
}
