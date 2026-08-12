import AttributeRow from "./AttributeRow";

export default function EvidenceLedger({ attributes, onReview }) {
  const sorted = Object.entries(attributes).sort(
    ([, a], [, b]) => a.confidence - b.confidence // lowest confidence first
  );

  return (
    <section className="evidence-ledger">
      <div className="ledger-head">
        <h2>Evidence Ledger</h2>
        <span className="ledger-hint font-mono">
          click row to expand · lowest confidence first
        </span>
      </div>

      <div className="ledger-rows">
        {sorted.map(([name, attr]) => (
          <AttributeRow key={name} name={name} attr={attr} onReview={onReview} />
        ))}
      </div>

      <style>{`
        .evidence-ledger { margin-top: 28px; }
        .ledger-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          margin-bottom: 12px;
          gap: 12px;
          flex-wrap: wrap;
        }
        .ledger-head h2 {
          font-family: var(--font-display);
          font-size: 17px;
          font-weight: 700;
        }
        .ledger-hint {
          font-size: 11px;
          color: var(--text-faint);
          letter-spacing: 0.02em;
        }
      `}</style>
    </section>
  );
}
