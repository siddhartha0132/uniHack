import ScoreHeader from "./ScoreHeader";
import EvidenceLedger from "./EvidenceLedger";
import ClassificationCard from "./ClassificationCard";
import RelatedGraph from "./RelatedGraph";
import AskBox from "./AskBox";
import ExportPanel from "./ExportPanel";
import ReliabilityPanel from "./ReliabilityPanel";
import AuditTimeline from "./AuditTimeline";

export default function ProductDetail({ product, onReview, loading, onOpenIngest, onRunDemo }) {
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
      <div className="detail-panel">
        <p className="eyebrow">Getting Started</p>
        <h1 className="detail-title">Product Resolution & Arbitration</h1>

        <div className="card" style={{ padding: "24px 28px", marginBottom: "24px" }}>
          <p style={{ fontSize: "14px", color: "var(--text-primary)", lineHeight: "1.6", marginBottom: "20px" }}>
            Select a product from the sidebar to inspect its evidence ledger, or run the pipeline using one of the options below:
          </p>

          <div className="action-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
            <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "18px", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "14px" }}>
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "6px" }}>
                  1. Run Demo Pipeline
                </h3>
                <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5", margin: 0 }}>
                  Instantly execute conflict arbitration on the Siemens PLC dataset across 3 conflicting sources (Datasheet, Product Page, Distributor ERP).
                </p>
              </div>
              {onRunDemo && (
                <button className="btn btn-primary btn-sm" onClick={onRunDemo} style={{ alignSelf: "flex-start" }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  Run Demo Pipeline
                </button>
              )}
            </div>

            <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "18px", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "14px" }}>
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "6px" }}>
                  2. Enter Demo Data / Custom Sources
                </h3>
                <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5", margin: 0 }}>
                  Upload your own PDF, CSV, or text files, or inspect and modify raw source inputs before triggering arbitration.
                </p>
              </div>
              {onOpenIngest && (
                <button className="btn btn-secondary btn-sm" onClick={onOpenIngest} style={{ alignSelf: "flex-start", border: "1px solid var(--border)" }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                  Enter Demo Data
                </button>
              )}
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border-soft)", paddingTop: "14px" }}>
            <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.6", margin: 0, fontFamily: "var(--font-mono)" }}>
              The demo dataset features a Siemens PLC SKU (6ES7214-1AG40-0XB0) sourced from three genuinely conflicting sources. Veritas extracts physical specifications and arbitrates true values with full evidence provenance and Bayesian reliability learning.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-panel">
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
          padding: 32px 40px;
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
