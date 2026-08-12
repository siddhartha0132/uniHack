function ScoreDot({ score }) {
  const color =
    score >= 75 ? "var(--teal)" : score >= 50 ? "var(--amber)" : "var(--red)";
  return (
    <svg width="10" height="10" viewBox="0 0 10 10">
      <circle cx="5" cy="5" r="4" fill={color} />
    </svg>
  );
}

export default function Sidebar({ products, loading, activeId, onSelect }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <p className="eyebrow">Products</p>
        <h2>Arbitration Queue</h2>
        <p className="sidebar-sub">
          {products.length} product{products.length !== 1 ? "s" : ""} processed
        </p>
      </div>

      <div className="sidebar-list">
        {loading && (
          <>
            {[1, 2, 3].map((i) => (
              <div key={i} className="product-skeleton">
                <div className="skeleton" style={{ height: 13, width: "70%", marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 11, width: "45%" }} />
              </div>
            ))}
          </>
        )}

        {!loading && products.length === 0 && (
          <div className="empty-state">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-faint)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            <p>No products yet</p>
            <p className="empty-hint">Run the demo pipeline or ingest your own data</p>
          </div>
        )}

        {!loading &&
          products.map((p) => (
            <button
              key={p.product_id}
              className={`product-item ${p.product_id === activeId ? "active" : ""}`}
              onClick={() => onSelect(p.product_id)}
            >
              <div className="product-item-name">{p.product_name}</div>
              <div className="product-item-meta">
                <span className="meta-score">
                  <ScoreDot score={p.overall_score} />
                  {p.overall_score}
                </span>
                {p.needs_review > 0 && (
                  <span className="meta-review">{p.needs_review} to review</span>
                )}
              </div>
            </button>
          ))}
      </div>

      <style>{`
        .sidebar {
          border-right: 1px solid var(--border-soft);
          background: var(--panel);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .sidebar-head {
          padding: 20px 20px 12px;
          border-bottom: 1px solid var(--border-soft);
          flex-shrink: 0;
        }
        .sidebar-head h2 {
          font-family: var(--font-display);
          font-size: 16px;
          font-weight: 700;
          margin: 4px 0 2px;
        }
        .sidebar-sub {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-faint);
        }
        .sidebar-list {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .product-item {
          width: 100%;
          text-align: left;
          border: 1px solid var(--border-soft);
          border-radius: var(--radius);
          padding: 12px 14px;
          background: transparent;
          cursor: pointer;
          transition:
            border-color var(--duration-fast) var(--ease),
            background   var(--duration-fast) var(--ease),
            box-shadow   var(--duration-fast) var(--ease);
          color: var(--text-primary);
          font-family: var(--font-body);
        }
        .product-item:hover { border-color: var(--teal); background: rgba(63,193,169,0.04); }
        .product-item.active {
          border-color: var(--teal);
          background: rgba(63,193,169,0.08);
          box-shadow: 0 0 0 1px var(--teal-dim);
        }
        .product-item-name {
          font-weight: 600;
          font-size: 13px;
          margin-bottom: 6px;
          line-height: 1.3;
        }
        .product-item-meta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .meta-score {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          gap: 5px;
        }
        .meta-review {
          font-family: var(--font-mono);
          font-size: 10px;
          padding: 2px 7px;
          border-radius: 10px;
          background: rgba(232,163,61,0.12);
          color: var(--amber);
          border: 1px solid var(--amber-dim);
        }
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 32px 16px;
          gap: 8px;
          color: var(--text-faint);
          font-size: 13px;
        }
        .empty-hint {
          font-size: 11px;
          font-family: var(--font-mono);
          color: var(--text-faint);
          line-height: 1.5;
        }
        .product-skeleton { padding: 12px; border: 1px solid var(--border-soft); border-radius: var(--radius); }
      `}</style>
    </aside>
  );
}
