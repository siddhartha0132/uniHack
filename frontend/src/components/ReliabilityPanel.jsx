import { useState, useEffect } from "react";
import { api } from "../api/client";

const DEFAULT_PRIORS = {
  datasheet: 0.95,
  catalog_pdf: 0.85,
  manufacturer_website: 0.80,
  distributor_erp: 0.70,
  image_label: 0.75,
};

export default function ReliabilityPanel() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && !data) {
      setLoading(true);
      api
        .getReliability()
        .then((res) => {
          if (res && res.static_priors) {
            setData(res);
          } else {
            setData({ static_priors: DEFAULT_PRIORS, learned_weights: {} });
          }
        })
        .catch(() => {
          setData({ static_priors: DEFAULT_PRIORS, learned_weights: {} });
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [open, data]);

  const staticPriors = (data && data.static_priors) || DEFAULT_PRIORS;
  const learnedWeights = (data && data.learned_weights) || {};

  const all = Object.keys(staticPriors).map((source_type) => ({
    source_type,
    static: staticPriors[source_type] ?? null,
    learned: learnedWeights[source_type] ?? null,
  }));

  return (
    <div className="rel-panel card">
      <button className="rel-toggle" onClick={() => setOpen((o) => !o)}>
        <div className="rel-toggle-left">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Learned reliability weights</span>
          <span className="rel-badge">Phase 5</span>
        </div>
        <svg className={`rel-chevron ${open ? "open" : ""}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {open && (
        <div className="rel-body">
          <p className="rel-note">
            Bayesian Beta distribution weights learned from human approve/edit/reject actions.
            As you review attributes, source reliability dynamically adapts from static priors toward actual observed accuracy.
          </p>
          {loading && !data && <div className="skeleton" style={{ height: 80, borderRadius: "6px" }} />}
          {data && (
            <table className="rel-table">
              <thead>
                <tr>
                  <th>Source type</th>
                  <th>Static prior</th>
                  <th>Learned weight</th>
                  <th>Delta</th>
                </tr>
              </thead>
              <tbody>
                {all.map(({ source_type, static: s, learned: l }) => {
                  const delta = l !== null && s !== null ? l - s : null;
                  return (
                    <tr key={source_type}>
                      <td><code>{source_type}</code></td>
                      <td>{s !== null ? (s * 100).toFixed(0) + "%" : "—"}</td>
                      <td className="learned-cell">
                        {l !== null ? (
                          <span style={{ color: "var(--teal)", fontWeight: 600 }}>
                            {(l * 100).toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-faint" style={{ color: "var(--text-faint)" }}>
                            no reviews yet
                          </span>
                        )}
                      </td>
                      <td>
                        {delta !== null ? (
                          <span style={{ color: delta > 0 ? "var(--teal)" : delta < 0 ? "var(--red)" : "var(--text-faint)" }}>
                            {delta > 0 ? "+" : ""}{(delta * 100).toFixed(1)}%
                          </span>
                        ) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      <style>{`
        .rel-panel { margin-top: 20px; padding: 0; overflow: hidden; }
        .rel-toggle {
          width: 100%; display: flex; align-items: center;
          justify-content: space-between; padding: 14px 18px;
          background: none; border: none; cursor: pointer;
          color: var(--text-primary); font-family: var(--font-body);
          transition: background var(--duration-fast) var(--ease);
        }
        .rel-toggle:hover { background: rgba(255,255,255,0.02); }
        .rel-toggle-left { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13px; }
        .rel-badge {
          font-family: var(--font-mono); font-size: 10px;
          padding: 2px 6px; border-radius: 10px;
          background: rgba(232,163,61,0.12); color: var(--amber);
          border: 1px solid var(--amber-dim);
        }
        .rel-chevron { color: var(--text-faint); transition: transform var(--duration-fast) var(--ease); }
        .rel-chevron.open { transform: rotate(180deg); }
        .rel-body { padding: 0 18px 16px; border-top: 1px solid var(--border-soft); }
        .rel-note {
          font-size: 12px; color: var(--text-secondary);
          line-height: 1.6; padding: 12px 0;
          font-family: var(--font-mono);
        }
        .rel-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
        .rel-table th {
          text-align: left; padding: 6px 10px;
          font-family: var(--font-mono); font-size: 10px;
          text-transform: uppercase; letter-spacing: 0.05em;
          color: var(--text-faint); border-bottom: 1px solid var(--border-soft);
        }
        .rel-table td { padding: 8px 10px; border-bottom: 1px solid var(--border-soft); }
        .rel-table td:first-child code { font-family: var(--font-mono); font-size: 12px; color: var(--teal); }
        .learned-cell { font-weight: 600; }
        .rel-table tr:last-child td { border-bottom: none; }
      `}</style>
    </div>
  );
}
