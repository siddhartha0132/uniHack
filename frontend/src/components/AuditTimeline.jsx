import React, { useState } from 'react';

export default function AuditTimeline({ reviewLog = [] }) {
  const [open, setOpen] = useState(false);

  if (!reviewLog || reviewLog.length === 0) {
    return null; // Don't show if there are no reviews
  }

  return (
    <div className="audit-timeline card" style={{ marginTop: '20px' }}>
      <button 
        className="rel-toggle" 
        onClick={() => setOpen((o) => !o)} 
        style={{ width: '100%', display: 'flex', justifyContent: 'space-between', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', padding: 0 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>Conflict Audit Timeline</span>
          <span className="badge" style={{ marginLeft: '8px' }}>{reviewLog.length} events</span>
        </div>
        <svg className={`rel-chevron ${open ? "open" : ""}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {open && (
        <div className="audit-body" style={{ marginTop: '16px', borderLeft: '2px solid var(--border)', paddingLeft: '16px', marginLeft: '6px' }}>
          {reviewLog.map((log, i) => (
            <div key={i} className="audit-event" style={{ marginBottom: '16px', position: 'relative' }}>
              <div 
                style={{
                  position: 'absolute', left: '-22px', top: '4px', width: '10px', height: '10px', 
                  borderRadius: '50%', background: log.action === 'reject' ? 'var(--red)' : 'var(--teal)',
                  border: '2px solid var(--panel)'
                }} 
              />
              <div style={{ fontSize: '12px', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
                {log.reviewer || 'unknown'} • {log.action}
              </div>
              <div style={{ fontSize: '14px', fontWeight: 500, marginTop: '2px' }}>
                {log.action === 'approve' 
                  ? `Approved automated resolution for "${log.attribute.replace(/_/g, " ")}"` 
                  : log.action === 'edit'
                  ? `Corrected "${log.attribute.replace(/_/g, " ")}" to ${log.corrected_value}`
                  : `Rejected automated resolution for "${log.attribute.replace(/_/g, " ")}"`
                }
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
