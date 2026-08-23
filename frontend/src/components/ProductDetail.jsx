import ScoreHeader from "./ScoreHeader";
import EvidenceLedger from "./EvidenceLedger";
import ClassificationCard from "./ClassificationCard";
import RelatedGraph from "./RelatedGraph";
import AskBox from "./AskBox";
import ExportPanel from "./ExportPanel";
import ReliabilityPanel from "./ReliabilityPanel";
import AuditTimeline from "./AuditTimeline";

export default function ProductDetail({ product, onReview, loading, onOpenIngest, onRunDemo, onBack }) {
  if (loading) {
    return (
      <div className="detail-panel">
        <div className="detail-loading">
          <div className="skeleton" style={{ height: 28, width: "55%", marginBottom: 16 }} />
          <div className="skeleton" style={{ height: 140, marginBottom: 24 }} />
          <div className="skeleton" style={{ height: 52, marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 52, marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 52 }} />
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="detail-panel" style={{ padding: "36px 44px 56px" }}>
        <div style={{ maxWidth: "860px" }}>

        {/* Hero headline */}
        <div style={{ marginBottom: "32px" }}>
          <p className="eyebrow" style={{ marginBottom: "8px", letterSpacing: "0.1em" }}>Veritas · Data Arbitration Engine</p>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "28px", fontWeight: 800, lineHeight: 1.2, margin: "0 0 12px", color: "var(--text-primary)" }}>
            Resolve product data conflicts<br/>
            <span style={{ color: "var(--teal)" }}>with traceable evidence.</span>
          </h1>
          <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.65, maxWidth: "580px", margin: 0 }}>
            Multi-source arbitration pipeline that ingests raw datasheets, product pages and ERP exports —
            then surfaces a single trusted truth with full confidence scoring and audit history.
          </p>
        </div>

        {/* 2 action cards */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>

          {/* Card 1 — Enter Demo Data */}
          <div style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderTop: "2px solid var(--teal)",
            borderRadius: "var(--radius)",
            padding: "22px",
            display: "flex", flexDirection: "column", gap: "16px"
          }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: "10px", fontWeight: 700,
                  background: "rgba(56,201,173,0.12)", color: "var(--teal)",
                  border: "1px solid var(--teal-dim)", borderRadius: "4px", padding: "2px 8px"
                }}>OPTION 1 — RECOMMENDED</span>
              </div>
              <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 8px" }}>
                Enter Demo Data
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", margin: "0 0 12px" }}>
                Load the 3 pre-built Siemens PLC sources instantly. See the product name, SKU, and all sources pre-filled — then hit <strong style={{ color: "var(--text-primary)" }}>Run arbitration pipeline</strong> to watch conflicts resolve in real-time.
              </p>
              <div style={{ fontSize: "11.5px", color: "var(--text-faint)", fontFamily: "var(--font-mono)", lineHeight: "1.8" }}>
                <div>✓ &nbsp;Best for demos &amp; presentations</div>
                <div>✓ &nbsp;Pre-loaded conflicting sources ready</div>
                <div>✓ &nbsp;See arbitration results in ~3 seconds</div>
              </div>
            </div>
            {onOpenIngest && (
              <button className="btn btn-primary btn-sm" onClick={onOpenIngest} style={{ alignSelf: "flex-start" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Enter Demo Data
              </button>
            )}
          </div>

          {/* Card 2 — Run Demo Pipeline */}
          <div style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderTop: "2px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "22px",
            display: "flex", flexDirection: "column", gap: "16px"
          }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: "10px", fontWeight: 700,
                  background: "rgba(255,255,255,0.04)", color: "var(--text-secondary)",
                  border: "1px solid var(--border)", borderRadius: "4px", padding: "2px 8px"
                }}>OPTION 2 — ONE-CLICK</span>
              </div>
              <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 8px" }}>
                Run Demo Pipeline
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", margin: "0 0 12px" }}>
                Skip setup entirely. Triggers the full arbitration pipeline in the background using the Siemens PLC dataset and shows you the resolved product card immediately.
              </p>
              <div style={{ fontSize: "11.5px", color: "var(--text-faint)", fontFamily: "var(--font-mono)", lineHeight: "1.8" }}>
                <div>✓ &nbsp;No configuration needed</div>
                <div>✓ &nbsp;Full pipeline in one click</div>
                <div>✓ &nbsp;Best to show final output quickly</div>
              </div>
            </div>
            {onRunDemo && (
              <button className="btn btn-ghost btn-sm" onClick={onRunDemo} style={{ alignSelf: "flex-start", border: "1px solid var(--border)" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Run Demo Pipeline
              </button>
            )}
          </div>
        </div>

        {/* Dataset footnote */}
        <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-soft)", borderRadius: "var(--radius)", padding: "14px 18px" }}>
          <p style={{ fontSize: "11.5px", color: "var(--text-faint)", lineHeight: "1.65", margin: 0, fontFamily: "var(--font-mono)" }}>
            <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>Demo dataset · </span>
            Siemens SIMATIC S7-1200 CPU 1214C — SKU <span style={{ color: "var(--teal)" }}>6ES7214-1AG40-0XB0</span>.
            Three conflicting sources: <em>Technical Datasheet</em>, <em>Manufacturer Product Page</em>, <em>Distributor ERP Export</em>.
            Veritas resolves weight, voltage, temperature range, and protection class conflicts with Bayesian source reliability learning.
          </p>
        </div>

        </div>{/* end max-width wrapper */}
      </div>
    );
  }

  return (
    <div className="detail-panel">
      {onBack && (
        <button
          onClick={onBack}
          style={{
            display: "inline-flex", alignItems: "center", gap: "6px",
            background: "none", border: "none", cursor: "pointer",
            color: "var(--text-secondary)", fontSize: "12.5px",
            fontFamily: "var(--font-mono)", padding: "0", marginBottom: "18px",
            transition: "color 0.15s"
          }}
          onMouseEnter={e => e.currentTarget.style.color = "var(--teal)"}
          onMouseLeave={e => e.currentTarget.style.color = "var(--text-secondary)"}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Back to home
        </button>
      )}
      <p className="eyebrow">{product.product_id}</p>
      <h1 className="detail-title">{product.product_name}</h1>

      <ScoreHeader quality={product.quality} />

      <EvidenceLedger
        attributes={product.attributes}
        onReview={(attr, action, val) => onReview(attr, action, val)}
      />

      <div className="meta-grid">
        <ClassificationCard classification={product.classification} />
        <RelatedGraph related={product.related} />
      </div>

      <AskBox productId={product.product_id} />

      <ExportPanel productId={product.product_id} />

      <AuditTimeline reviewLog={product.review_log} />

      <ReliabilityPanel />

      <div style={{ height: 40 }} />

      <style>{`
        .detail-panel {
          flex: 1;
          overflow-y: auto;
          padding: 36px 44px 56px;
          background: var(--bg-subtle);
        }
        .detail-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
          gap: 6px;
        }
        .empty-icon { margin-bottom: 16px; }
        .detail-title {
          font-family: var(--font-display);
          font-size: 26px;
          font-weight: 700;
          margin: 4px 0 24px;
          line-height: 1.2;
        }
        .meta-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-top: 24px;
        }
        .detail-loading { padding: 12px; }
        @media (max-width: 700px) {
          .detail-panel { padding: 20px; }
          .meta-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}
