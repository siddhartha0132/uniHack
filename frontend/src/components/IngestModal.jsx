import { useState, useRef } from "react";
import { api } from "../api/client";

const INITIAL_SOURCE = {
  source_id: "source_1",
  source_type: "",
  format: "",
  raw_content: "",
  file: null,
  fileName: "",
};

const SOURCE_TYPES = [
  { value: "datasheet", label: "Datasheet" },
  { value: "manufacturer_website", label: "Manufacturer Website" },
  { value: "distributor_erp", label: "Distributor ERP" },
  { value: "catalog_pdf", label: "Catalog PDF" },
  { value: "image_label", label: "Image / Label" },
];

export default function IngestModal({ onClose, onSuccess }) {
  const [productName, setProductName] = useState("");
  const [productId, setProductId] = useState("");
  const [sources, setSources] = useState([{ ...INITIAL_SOURCE }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const overlayRef = useRef(null);
  const fileInputRefs = useRef({});

  const updateSource = (i, field, value) => {
    setSources((prev) =>
      prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s))
    );
  };

  const handleFileSelect = (i, file) => {
    if (!file) return;
    const name = file.name.toLowerCase();

    // 1. Auto-detect format from file
    let detectedFormat = "text";
    if (name.endsWith(".csv")) {
      detectedFormat = "csv";
    } else if (name.endsWith(".pdf")) {
      detectedFormat = "pdf";
    } else if (name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg")) {
      detectedFormat = "image";
    }

    // 2. Auto-suggest source type if not already picked
    let autoType = sources[i].source_type;
    if (!autoType) {
      if (name.includes("datasheet")) autoType = "datasheet";
      else if (name.includes("website") || name.includes("product")) autoType = "manufacturer_website";
      else if (name.includes("erp") || name.includes("distributor")) autoType = "distributor_erp";
      else if (name.includes("catalog") || name.endsWith(".pdf")) autoType = "catalog_pdf";
      else if (name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg")) autoType = "image_label";
    }

    const isTextOrCsv =
      name.endsWith(".txt") ||
      name.endsWith(".csv") ||
      name.endsWith(".json") ||
      file.type.startsWith("text/");

    if (isTextOrCsv) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSources((prev) =>
          prev.map((s, idx) =>
            idx === i
              ? {
                  ...s,
                  source_id: file.name.replace(/\.[^/.]+$/, "") || `source_${i + 1}`,
                  file: file,
                  fileName: file.name,
                  format: detectedFormat,
                  source_type: autoType || s.source_type,
                  raw_content: e.target.result,
                }
              : s
          )
        );
      };
      reader.readAsText(file);
    } else {
      setSources((prev) =>
        prev.map((s, idx) =>
          idx === i
            ? {
                ...s,
                source_id: file.name.replace(/\.[^/.]+$/, "") || `source_${i + 1}`,
                file: file,
                fileName: file.name,
                format: detectedFormat,
                source_type: autoType || s.source_type,
                raw_content: s.raw_content || `[Attached file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)]`,
              }
            : s
        )
      );
    }
  };

  const addSource = () => {
    setSources((prev) => [
      ...prev,
      {
        source_id: `source_${prev.length + 1}`,
        source_type: "",
        format: "",
        raw_content: "",
        file: null,
        fileName: "",
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
    const hasFiles = sources.some((s) => s.file);
    for (const s of sources) {
      if (!s.file && !s.raw_content.trim()) {
        setError(`Please choose a file or paste content for source ${s.fileName || s.source_id}.`);
        return;
      }
    }
    setError(null);
    setLoading(true);
    try {
      let result;
      if (hasFiles) {
        const formData = new FormData();
        formData.append("product_name", productName.trim());
        formData.append("product_id", productId.trim());
        sources.forEach((s) => {
          formData.append("source_ids", s.source_id || "source");
          formData.append("source_types", s.source_type || "datasheet");
          if (s.file) {
            formData.append("files", s.file);
          } else {
            const blob = new Blob([s.raw_content], {
              type: s.format === "csv" ? "text/csv" : "text/plain",
            });
            formData.append("files", blob, `${s.source_id || "source"}.${s.format === "csv" ? "csv" : "txt"}`);
          }
        });
        result = await api.ingestUpload(formData);
      } else {
        result = await api.ingest({
          product_name: productName.trim(),
          product_id: productId.trim(),
          sources: sources.map((s) => ({
            source_id: s.source_id || "source",
            source_type: s.source_type || "datasheet",
            format: s.format || "text",
            raw_content: s.raw_content,
          })),
        });
      }
      onSuccess(result);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemoData = () => {
    setProductName("SIMATIC S7-1200 CPU 1214C");
    setProductId("6ES7214-1AG40-0XB0");
    setSources([
      {
        source_id: "source_a_datasheet",
        source_type: "datasheet",
        format: "text",
        raw_content: `SIEMENS SIMATIC S7-1200 CPU 1214C
Technical Datasheet — Document No. 6ES7214-1AG40-0XB0
Page 24 — Technical specifications

Supply voltage: rated 24 V DC, operating range 20.4 V DC to 28.8 V DC
Digital inputs: 14 x 24 V DC
Digital outputs: 10 x relay, 2 A
Weight: approximately 1.35 kg (including front connectors)
Ambient temperature during operation: -20 C to +60 C
Degree of protection: IP20
Work memory: 100 KB
Communication: PROFINET, Ethernet
Dimensions (W x H x D): 110 mm x 100 mm x 75 mm`,
        file: null,
        fileName: "source_a_datasheet.txt",
      },
      {
        source_id: "source_b_website",
        source_type: "manufacturer_website",
        format: "text",
        raw_content: `Product page — siemens.com/simatic-s7-1200
SIMATIC S7-1200, CPU 1214C

Compact PLC for small to medium automation tasks.
Input voltage: 24V DC
Weight: 1.2 kg
Operating temperature: -20C to 60C
Protection class: IP20
Digital I/O: 14 DI / 10 DO
Ethernet interface: yes, PROFINET supported
Memory: 100 KB work memory

Buy now or find a distributor near you.`,
        file: null,
        fileName: "source_b_website.txt",
      },
      {
        source_id: "source_c_distributor_erp",
        source_type: "distributor_erp",
        format: "csv",
        raw_content: `sku,description,voltage,weight_kg,temp_range,protection,memory_kb
6ES7214-1AG40-0XB0,SIMATIC S7-1200 CPU 1214C PLC,24VDC,1.4,-20 to 55 C,IP20,100`,
        file: null,
        fileName: "source_c_distributor_erp.csv",
      },
    ]);
    setError(null);
  };

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div className="modal-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="modal-box ingest-modal">
        <div className="modal-header">
          <div>
            <p className="eyebrow">Product Ingestion</p>
            <h2>Enter Demo Data / Sources</h2>
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

          {/* Sources list */}
          <div className="sources-head">
            <span className="form-label">Attached Sources ({sources.length})</span>
            <button type="button" className="btn btn-ghost btn-sm" onClick={addSource}>
              + Add Source
            </button>
          </div>

          <div className="sources-list">
            {sources.map((src, i) => (
              <div key={i} className="source-card">
                <div className="source-card-header">
                  {/* File Selector */}
                  <div className="file-pick-container">
                    <input
                      type="file"
                      ref={(el) => (fileInputRefs.current[i] = el)}
                      style={{ display: "none" }}
                      accept=".pdf,.txt,.csv,.jpg,.jpeg,.png,.json"
                      onChange={(e) => handleFileSelect(i, e.target.files[0])}
                    />
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost file-choose-btn"
                      onClick={() => fileInputRefs.current[i]?.click()}
                      title="Select file from your computer"
                    >
                      📁 {src.fileName ? "Change" : "Choose File"}
                    </button>
                    <span className={`file-name-label ${src.fileName ? "has-file" : ""}`}>
                      {src.fileName || "No file chosen"}
                    </span>
                  </div>

                  {/* Source Type Dropdown */}
                  <select
                    className="input source-type-select"
                    value={src.source_type}
                    onChange={(e) => updateSource(i, "source_type", e.target.value)}
                  >
                    <option value="">-- Choose Type --</option>
                    {SOURCE_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>

                  {/* Format Indicator/Select */}
                  <select
                    className="input format-select"
                    value={src.format}
                    onChange={(e) => updateSource(i, "format", e.target.value)}
                    title="Auto-detected format"
                  >
                    <option value="">-- File Type --</option>
                    <option value="text">TXT / Text</option>
                    <option value="csv">CSV</option>
                    <option value="pdf">PDF</option>
                    <option value="image">Image</option>
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
                      : "Paste raw text or select a file (.pdf, .txt, .csv, image) above."
                  }
                  value={src.raw_content}
                  onChange={(e) => updateSource(i, "raw_content", e.target.value)}
                />
              </div>
            ))}
          </div>

          {error && <div className="ingest-error">{error}</div>}

          <div className="modal-footer">
            <div style={{ display: "flex", gap: "8px", marginRight: "auto" }}>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={addSource}
                style={{ border: "1px solid var(--border)" }}
              >
                + Add Source
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleLoadDemoData}
                style={{ color: "var(--teal)", border: "1px solid var(--teal-dim)" }}
              >
                📋 Load Demo Sources
              </button>
            </div>
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={loading}>
              Cancel
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
          .ingest-modal { position: relative; max-width: 660px; }
          .modal-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 20px;
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
            padding: 12px;
            background: var(--bg-subtle);
            display: flex;
            flex-direction: column;
            gap: 10px;
          }
          .source-card-header {
            display: grid;
            grid-template-columns: 1.4fr 1.3fr 100px auto;
            gap: 8px;
            align-items: center;
          }
          .file-pick-container {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 2px 8px;
            min-height: 34px;
            overflow: hidden;
          }
          .file-choose-btn {
            border: 1px solid var(--border-soft) !important;
            padding: 3px 8px !important;
            font-size: 11px !important;
            white-space: nowrap;
            flex-shrink: 0;
          }
          .file-name-label {
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-faint);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .file-name-label.has-file {
            color: var(--teal);
            font-weight: 600;
          }
          .source-type-select { font-size: 12px; }
          .format-select { font-size: 12px; }
          .source-content { min-height: 90px; font-size: 12px; font-family: var(--font-mono); }
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
            align-items: center;
            gap: 10px;
            padding-top: 12px;
            border-top: 1px solid var(--border-soft);
            flex-wrap: wrap;
          }
          .spinner {
            display: inline-block;
            width: 13px; height: 13px;
            border: 2px solid rgba(7,20,18,0.3);
            border-top-color: #071412;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
          }
          @media (max-width: 600px) {
            .form-row-2 { grid-template-columns: 1fr; }
            .source-card-header { grid-template-columns: 1fr 1fr; }
          }
        `}</style>
      </div>
    </div>
  );
}
