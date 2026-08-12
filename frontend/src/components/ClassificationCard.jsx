export default function ClassificationCard({ classification }) {
  if (!classification) {
    return (
      <div className="meta-card card">
        <h3>Classification</h3>
        <p className="text-faint" style={{ fontSize: 12.5 }}>
          No classification match — ETIM/ECLASS/UNSPSC not found for this product category.
        </p>
      </div>
    );
  }

  const codes = [
    { label: "ETIM", value: `${classification.etim_class}`, name: classification.etim_class_name },
    { label: "ECLASS", value: `${classification.eclass_code}`, name: classification.eclass_name },
    { label: "UNSPSC", value: `${classification.unspsc}`, name: null },
  ];

  return (
    <div className="meta-card card">
      <h3>Classification</h3>
      <div className="cls-list">
        {codes.map((c) => (
          <div key={c.label} className="cls-row">
            <span className="cls-standard">{c.label}</span>
            <div className="cls-detail">
              <code className="cls-code">{c.value}</code>
              {c.name && <span className="cls-name">{c.name}</span>}
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .meta-card h3 {
          font-family: var(--font-display);
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--text-faint);
          margin-bottom: 14px;
          font-weight: 600;
        }
        .cls-list { display: flex; flex-direction: column; gap: 10px; }
        .cls-row {
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }
        .cls-standard {
          font-family: var(--font-mono);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: var(--text-faint);
          padding: 2px 6px;
          border: 1px solid var(--border);
          border-radius: 3px;
          flex-shrink: 0;
          margin-top: 1px;
        }
        .cls-detail { display: flex; flex-direction: column; gap: 1px; }
        .cls-code {
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--teal);
          background: rgba(63,193,169,0.08);
          padding: 1px 6px;
          border-radius: 3px;
        }
        .cls-name {
          font-size: 12px;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
