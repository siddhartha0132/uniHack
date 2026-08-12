import { useState, useRef } from "react";
import { api } from "../api/client";

const INITIAL_SOURCE = {
  source_id: "source_1",
  source_type: "datasheet",
  format: "text",
  raw_content: "",
};

const SOURCE_TYPES = [
  "datasheet",
  "manufacturer_website",
  "distributor_erp",
  "catalog_pdf",
  "image_label",
];

export default function IngestModal({ onClose, onSuccess }) {
  const [productName, setProductName] = useState("");
  const [productId, setProductId] = useState("");
  const [sources, setSources] = useState([{ ...INITIAL_SOURCE }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const overlayRef = useRef(null);

  const updateSource = (i, field, value) => {
    setSources((prev) =>
      prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s))
    );
  };

  const addSource = () => {
    setSources((prev) => [
      ...prev,
      {
        source_id: `source_${prev.length + 1}`,
        source_type: "datasheet",
        format: "text",
        raw_content: "",
      },
    ]);
  };

  const removeSource = (i) => {
    if (sources.length === 1) return;
    setSources((prev) => prev.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!productName.trim() || !productId.trim()) {
      setError("Product name and ID are required.");
      return;
    }
    for (const s of sources) {
      if (!s.raw_content.trim()) {
        setError(`Source "${s.source_id}" has no content.`);
        return;
      }
    }
    setError(null);
    setLoading(true);
    try {
      const result = await api.ingest({
        product_name: productName.trim(),
        product_id: productId.trim(),
        sources: sources.map((s) => ({
          source_id: s.source_id,
          source_type: s.source_type,
          format: s.format,
          raw_content: s.raw_content,
        })),
      });
      onSuccess(result);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscover = async () => {
    if (!productName.trim() || !productId.trim()) {
      setError("Product name and ID are required for auto-discovery.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await api.ingestDiscover({
        product_name: productName.trim(),
        product_id: productId.trim(),
        sources: [], // Empty sources triggers auto-discovery
      });
      onSuccess(result);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div className="modal-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="modal-box ingest-modal">
        <div className="modal-header">
          <div>
            <p className="eyebrow">New ingestion</p>
            <h2>Ingest product sources</h2>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="ingest-form">
          {/* Product identity */}
          <div className="form-row-2">
            <label className="form-group">
              <span className="form-label">Product Name</span>
              <input
                className="input"
                placeholder="e.g. SIMATIC S7-1200 CPU 1214C"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
              />
            </label>
            <label className="form-group">
              <span className="form-label">Product ID / SKU</span>
              <input
                className="input"
                placeholder="e.g. 6ES7214-1AG40-0XB0"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
              />
            </label>
          </div>

          <hr className="divider" />

          {/* Sources */}
          <div className="sources-head">
            <span className="form-label">Sources ({sources.length})</span>
            <button type="button" className="btn btn-ghost btn-sm" onClick={addSource}>
              + Add source
            </button>
          </div>

          <div className="sources-list">
            {sources.map((src, i) => (
              <div key={i} className="source-card">
                <div className="source-card-header">
                  <input
                    className="input source-id-input"
                    value={src.source_id}
                    onChange={(e) => updateSource(i, "source_id", e.target.value)}
                    placeholder="source_id"
                  />
                  <select
                    className="input"
                    value={src.source_type}
                    onChange={(e) => updateSource(i, "source_type", e.target.value)}
                  >
                    {SOURCE_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <select
                    className="input"
                    value={src.format}
                    onChange={(e) => updateSource(i, "format", e.target.value)}
                  >
                    <option value="text">text</option>
                    <option value="csv">csv</option>
                  </select>
                  {sources.length > 1 && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-icon"
                      onClick={() => removeSource(i)}
                      title="Remove source"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                      </svg>
                    </button>
                  )}
                </div>
                <textarea
                  className="input source-content"
                  placeholder={
                    src.format === "csv"
                      ? "attribute,value\nvoltage,24V DC\nweight_kg,1.35"
                      : "Paste raw text from datasheet, product page, etc."
                  }
                  value={src.raw_content}
                  onChange={(e) => updateSource(i, "raw_content", e.target.value)}
                />
              </div>
            ))}
          </div>

          {error && <div className="ingest-error">{error}</div>}

          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="button" className="btn btn-ghost" onClick={handleDiscover} disabled={loading} style={{ marginRight: 'auto', color: 'var(--teal)' }}>
              {loading ? "Searching web..." : "✨ Auto-discover from SKU"}
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" />
                  Running pipeline…
                </>
              ) : (
                "Run arbitration pipeline"
              )}
            </button>
          </div>
        </form>

        <style>{`
          .ingest-modal { position: relative; }
          .modal-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 24px;
          }
          .ingest-form { display: flex; flex-direction: column; gap: 16px; }
          .form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
          .form-group { display: flex; flex-direction: column; gap: 6px; }
          .form-label {
            font-family: var(--font-mono);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-faint);
          }
          .sources-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 4px;
          }
          .sources-list { display: flex; flex-direction: column; gap: 12px; }
          .source-card {
            border: 1px solid var(--border-soft);
            border-radius: var(--radius);
            padding: 14px;
            background: var(--bg-subtle);
            display: flex;
            flex-direction: column;
            gap: 10px;
          }
          .source-card-header {
            display: grid;
            grid-template-columns: 1fr 1fr 80px auto;
            gap: 8px;
            align-items: center;
          }
          .source-id-input { font-family: var(--font-mono); font-size: 12px; }
          .source-content { min-height: 100px; font-size: 12px; }
          .ingest-error {
            padding: 10px 14px;
            border: 1px solid var(--red-dim);
            border-radius: var(--radius);
            color: var(--red);
            font-size: 13px;
            background: rgba(224,92,58,0.06);
          }
          .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding-top: 8px;
            border-top: 1px solid var(--border-soft);
          }
          .spinner {
            display: inline-block;
            width: 13px; height: 13px;
            border: 2px solid rgba(7,20,18,0.3);
            border-top-color: #071412;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
          }
          @media (max-width: 540px) {
            .form-row-2 { grid-template-columns: 1fr; }
            .source-card-header { grid-template-columns: 1fr 1fr; }
          }
        `}</style>
      </div>
    </div>
  );
}
