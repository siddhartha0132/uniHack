import { useState, useEffect } from "react";
import { api } from "../api/client";

export default function Topbar({ apiOk, onRunDemo, running, onOpenIngest }) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">V</div>
        <div className="brand-text">
          <span className="brand-name">Veritas</span>
          <span className="brand-sub">Industrial Product Intelligence</span>
        </div>
      </div>

      <div className="topbar-actions">
        <span className={`api-dot ${apiOk === true ? "ok" : apiOk === false ? "err" : "checking"}`} />
        <span className={`api-label ${apiOk === true ? "ok" : apiOk === false ? "err" : ""}`}>
          {apiOk === null ? "checking API…" : apiOk ? "API connected" : "API offline — start backend"}
        </span>

        <button className="btn btn-ghost btn-sm" onClick={onOpenIngest}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          Ingest
        </button>

        <button
          className="btn btn-primary btn-sm"
          onClick={onRunDemo}
          disabled={running}
        >
          {running ? (
            <>
              <span className="spinner" />
              Running…
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Run demo pipeline
            </>
          )}
        </button>
      </div>

      <style>{`
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 24px;
          height: 58px;
          border-bottom: 1px solid var(--border-soft);
          background: var(--panel);
          backdrop-filter: blur(12px);
          flex-shrink: 0;
          position: relative;
          z-index: 10;
        }
        .brand { display: flex; align-items: center; gap: 12px; }
        .brand-mark {
          width: 32px; height: 32px;
          display: flex; align-items: center; justify-content: center;
          font-family: var(--font-display);
          font-weight: 700; font-size: 16px;
          background: linear-gradient(135deg, var(--teal), var(--teal-bright));
          color: #071412;
          border-radius: var(--radius);
          box-shadow: 0 0 16px rgba(63,193,169,0.3);
          flex-shrink: 0;
        }
        .brand-text { display: flex; flex-direction: column; line-height: 1.2; }
        .brand-name {
          font-family: var(--font-display);
          font-weight: 700; font-size: 15px;
          letter-spacing: 0.01em;
        }
        .brand-sub {
          font-family: var(--font-mono);
          font-size: 10px;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        .topbar-actions { display: flex; align-items: center; gap: 12px; }
        .api-dot {
          width: 7px; height: 7px;
          border-radius: 50%;
          background: var(--text-faint);
          flex-shrink: 0;
        }
        .api-dot.ok  { background: var(--teal); box-shadow: 0 0 6px var(--teal); animation: pulse 2s infinite; }
        .api-dot.err { background: var(--red); }
        .api-dot.checking { background: var(--amber); animation: pulse 1s infinite; }
        .api-label {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-faint);
          margin-right: 4px;
        }
        .api-label.ok  { color: var(--teal); }
        .api-label.err { color: var(--red); }
        .spinner {
          display: inline-block;
          width: 12px; height: 12px;
          border: 2px solid rgba(7,20,18,0.4);
          border-top-color: #071412;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
      `}</style>
    </header>
  );
}
