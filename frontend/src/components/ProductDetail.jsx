import ScoreHeader from "./ScoreHeader";
import EvidenceLedger from "./EvidenceLedger";
import ClassificationCard from "./ClassificationCard";
import RelatedGraph from "./RelatedGraph";
import AskBox from "./AskBox";
import ExportPanel from "./ExportPanel";
import ReliabilityPanel from "./ReliabilityPanel";
import AuditTimeline from "./AuditTimeline";

export default function ProductDetail({ product, onReview, loading }) {
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
      <div className="detail-panel" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="detail-empty">
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <p className="eyebrow" style={{ textAlign: "center", margin: 0 }}>no product selected</p>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 700, textAlign: "center", margin: "8px 0 14px" }}>
            Select a product or run the demo
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-secondary)", textAlign: "center", lineHeight: 1.75, maxWidth: 520, margin: "0 auto", textWrap: "balance" }}>
            The demo dataset is a Siemens PLC SKU sourced from three genuinely disagreeing sources — a technical datasheet, a manufacturer product page, and a distributor ERP export. Watch the arbitration engine resolve conflicts with full evidence.
          </p>
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
