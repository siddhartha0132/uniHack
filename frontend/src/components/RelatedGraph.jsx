function RelationGroup({ label, items, color }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="rel-group">
      <span className="rel-label" style={{ color }}>{label}</span>
      <ul className="rel-list">
        {items.map((r) => (
          <li key={r.id} className="rel-item">
            <code className="rel-id">{r.id}</code>
            <span className="rel-name">{r.name}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function RelatedGraph({ related }) {
  const hasAny =
    related &&
    (related.compatible_accessories?.length > 0 ||
      related.replacement_products?.length > 0 ||
      related.related_family_members?.length > 0);

  return (
    <div className="meta-card card">
      <h3>Related products</h3>

      {!hasAny && (
        <p className="text-faint" style={{ fontSize: 12.5 }}>
          No graph relationships for this product yet.
        </p>
      )}

      {hasAny && (
        <div className="rel-sections">
          <RelationGroup
            label="Family members"
            items={related.related_family_members}
            color="var(--teal)"
          />
          <RelationGroup
            label="Compatible accessories"
            items={related.compatible_accessories}
            color="var(--amber)"
          />
          <RelationGroup
            label="Replacement products"
            items={related.replacement_products}
            color="var(--text-secondary)"
          />
        </div>
      )}

      {related?.manufacturer && (
        <div className="rel-mfr">
          <span className="rel-label" style={{ color: "var(--text-faint)" }}>Manufacturer</span>
          <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{related.manufacturer}</span>
          {related.product_family && (
            <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
              {" "}· {related.product_family}
            </span>
          )}
        </div>
      )}

      <style>{`
        .rel-sections { display: flex; flex-direction: column; gap: 14px; }
        .rel-group { display: flex; flex-direction: column; gap: 6px; }
        .rel-label {
          font-family: var(--font-mono);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 500;
        }
        .rel-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }
        .rel-item { display: flex; flex-direction: column; gap: 1px; }
        .rel-id {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--teal);
          background: rgba(63,193,169,0.08);
          padding: 1px 6px;
          border-radius: 3px;
          align-self: flex-start;
        }
        .rel-name { font-size: 12.5px; color: var(--text-secondary); }
        .rel-mfr {
          margin-top: 14px;
          padding-top: 12px;
          border-top: 1px solid var(--border-soft);
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
      `}</style>
    </div>
  );
}
