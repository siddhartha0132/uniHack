import { useState } from "react";

function confColor(conf) {
  if (conf >= 0.85) return "var(--teal)";
  if (conf >= 0.6)  return "var(--amber)";
  return "var(--red)";
}

function formatValue(attr) {
  const v = attr.resolved_value;
  const unit = attr.unit ? ` ${attr.unit}` : "";
  if (Array.isArray(v)) return `${v[0]} – ${v[1]}${unit}`;
  if (v === null || v === undefined) return "—";
  return `${v}${unit}`;
}

function EvidenceItem({ ev }) {
  return (
    <div className={`ev-item ${ev.agrees_with_resolution ? "ev-agree" : "ev-disagree"}`}>
      <div className="ev-head">
        <span className="ev-source">
          <span className="source-type-badge">{ev.source_type}</span>
          <span className="ev-loc">{ev.location}</span>
        </span>
        <span className={`ev-verdict ${ev.agrees_with_resolution ? "agree" : "disagree"}`}>
          {ev.agrees_with_resolution ? "✓ agrees" : "✗ disagrees"} —{" "}
          {Array.isArray(ev.value) ? ev.value.join("–") : ev.value}
          {ev.unit ? ` ${ev.unit}` : ""}
        </span>
      </div>
      <div className="ev-snippet">"{ev.raw_snippet}"</div>
    </div>
  );
}

export default function AttributeRow({ name, attr, onReview }) {
  const [open, setOpen] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const confPct = Math.round(attr.confidence * 100);
  const color = confColor(attr.confidence);

  const handleReview = async (action) => {
    setReviewing(true);
    try {
      await onReview(name, action);
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className={`attr-row status-${attr.status} ${open ? "open" : ""}`}>
      {/* Summary row — click to expand */}
      <button className="attr-summary" onClick={() => setOpen((o) => !o)}>
        <span className="attr-name">{name.replace(/_/g, " ")}</span>
        <span className="attr-value">{formatValue(attr)}</span>
        <div className="attr-confidence">
          <span className="conf-pct">{confPct}%</span>
          <div className="conf-bar-track">
            <div
              className="conf-bar-fill"
              style={{ width: `${confPct}%`, background: color }}
            />
          </div>
        </div>
        <span className={`badge badge-${attr.status}`}>
          {attr.status.replace(/_/g, " ")}
        </span>
        <span className={`expand-icon ${open ? "expanded" : ""}`}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </span>
      </button>

      {/* Detail drawer */}
      {open && (
        <div className="attr-detail">
          <p className="reasoning">{attr.reasoning}</p>

          <div className="ev-list">
            {attr.evidence.map((ev, i) => (
              <EvidenceItem key={i} ev={ev} />
            ))}
          </div>

          {attr.status !== "human_approved" &&
            attr.status !== "human_corrected" &&
            attr.status !== "rejected" && (
              <div className="review-actions">
                <button
                  className="btn btn-sm"
                  style={{ color: "var(--teal)", borderColor: "var(--teal-dim)" }}
                  onClick={() => handleReview("approve")}
                  disabled={reviewing}
                >
                  ✓ Approve
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleReview("reject")}
                  disabled={reviewing}
                >
                  ✗ Reject
                </button>
              </div>
            )}
        </div>
      )}

      <style>{`
        .attr-row {
          border: 1px solid var(--border-soft);
          border-left-width: 3px;
          border-radius: var(--radius);
          margin-bottom: 8px;
          background: var(--panel);
          overflow: hidden;
          transition: border-color var(--duration-fast) var(--ease), box-shadow var(--duration-fast) var(--ease);
        }
        .attr-row:hover { border-color: var(--border); }
        .attr-row.open  { box-shadow: var(--shadow-sm); }

        .status-agreed .attr-row,
        .status-agreed { border-left-color: var(--teal); }
        .status-human_approved, .status-human_corrected { border-left-color: var(--teal); }
        .status-single_source { border-left-color: var(--text-faint); }
        .status-resolved_conflict { border-left-color: var(--amber); }
        .status-unresolved_conflict, .status-rejected { border-left-color: var(--red); }

        .attr-summary {
          display: grid;
          grid-template-columns: 1fr auto auto auto auto;
          align-items: center;
          gap: 16px;
          padding: 12px 14px;
          cursor: pointer;
          width: 100%;
          background: none;
          border: none;
          color: var(--text-primary);
          font-family: var(--font-body);
          text-align: left;
          transition: background var(--duration-fast) var(--ease);
        }
        .attr-summary:hover { background: rgba(255,255,255,0.02); }

        .attr-name {
          font-weight: 600;
          font-size: 13px;
          text-transform: capitalize;
          color: var(--text-primary);
        }
        .attr-value {
          font-family: var(--font-mono);
          font-size: 13px;
          color: var(--text-primary);
          white-space: nowrap;
        }
        .attr-confidence {
          text-align: right;
          min-width: 60px;
        }
        .conf-pct {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-secondary);
        }
        .expand-icon {
          color: var(--text-faint);
          display: flex;
          align-items: center;
          transition: transform var(--duration-fast) var(--ease);
        }
        .expand-icon.expanded { transform: rotate(180deg); }

        .attr-detail {
          border-top: 1px solid var(--border-soft);
          padding: 14px 16px 16px;
          background: var(--panel-raised);
          animation: slideUp 160ms var(--ease);
        }
        .reasoning {
          font-size: 12.5px;
          color: var(--text-secondary);
          margin-bottom: 14px;
          padding-left: 12px;
          border-left: 2px solid var(--border);
          line-height: 1.6;
        }
        .ev-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
        .ev-item {
          font-family: var(--font-mono);
          font-size: 11.5px;
          padding: 8px 12px;
          border: 1px solid var(--border-soft);
          border-radius: var(--radius-sm);
          background: var(--bg);
        }
        .ev-agree   { border-left: 2px solid var(--teal-dim); }
        .ev-disagree{ border-left: 2px solid var(--red-dim); }

        .ev-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          margin-bottom: 5px;
          flex-wrap: wrap;
        }
        .ev-source { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); }
        .ev-loc    { color: var(--text-faint); }
        .source-type-badge {
          background: var(--panel-raised);
          padding: 1px 6px;
          border-radius: 3px;
          font-size: 10px;
          color: var(--text-secondary);
        }
        .ev-verdict { white-space: nowrap; }
        .agree   { color: var(--teal); }
        .disagree{ color: var(--red); }
        .ev-snippet {
          color: var(--text-primary);
          font-size: 11px;
          line-height: 1.5;
        }
        .review-actions { display: flex; gap: 8px; }
      `}</style>
    </div>
  );
}
