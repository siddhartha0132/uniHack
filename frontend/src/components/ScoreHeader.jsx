function ScoreRing({ score }) {
  const radius = 44;
  const circ = 2 * Math.PI * radius;
  const fill = (score / 100) * circ;
  const color =
    score >= 75 ? "var(--teal)" : score >= 50 ? "var(--amber)" : "var(--red)";

  return (
    <div className="score-ring-wrap">
      <svg width="110" height="110" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r={radius} fill="none" stroke="var(--border-soft)" strokeWidth="7" />
        <circle
          cx="55" cy="55" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeDasharray={`${fill} ${circ}`}
          strokeDashoffset={circ / 4}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.8s var(--ease)", filter: `drop-shadow(0 0 6px ${color})` }}
        />
        <text x="55" y="50" textAnchor="middle" dominantBaseline="middle"
          fontFamily="var(--font-display)" fontWeight="700" fontSize="22" fill="var(--text-primary)">
          {score}
        </text>
        <text x="55" y="68" textAnchor="middle" dominantBaseline="middle"
          fontFamily="var(--font-mono)" fontSize="10" fill="var(--text-faint)">
          /100
        </text>
      </svg>
    </div>
  );
}

export default function ScoreHeader({ quality }) {
  const { overall_score, completeness, avg_confidence, conflicts_detected, needs_review, explanation } = quality;

  return (
    <div className="score-header card">
      <ScoreRing score={overall_score} />
      <div className="score-body">
        <div className="score-stats">
          <Stat value={`${completeness}%`} label="complete" />
          <Stat value={`${avg_confidence}%`} label="avg. confidence" />
          <Stat value={conflicts_detected} label="conflicts resolved" highlight={conflicts_detected > 0 ? "amber" : null} />
          <Stat value={needs_review.length} label="need review" highlight={needs_review.length > 0 ? "red" : null} />
        </div>
        <p className="score-explanation">{explanation}</p>
      </div>

      <style>{`
        .score-header {
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 24px;
          align-items: center;
          margin-bottom: 24px;
          border-color: var(--border);
        }
        .score-ring-wrap svg { display: block; }
        .score-body { display: flex; flex-direction: column; gap: 14px; }
        .score-stats { display: flex; gap: 24px; flex-wrap: wrap; }
        .stat { display: flex; flex-direction: column; gap: 2px; }
        .stat-value {
          font-family: var(--font-display);
          font-size: 22px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1;
        }
        .stat-value.amber { color: var(--amber); }
        .stat-value.red   { color: var(--red); }
        .stat-label {
          font-family: var(--font-mono);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-faint);
        }
        .score-explanation {
          font-size: 12.5px;
          color: var(--text-secondary);
          border-top: 1px solid var(--border-soft);
          padding-top: 12px;
          line-height: 1.6;
        }
        @media (max-width: 600px) {
          .score-header { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

function Stat({ value, label, highlight }) {
  return (
    <div className="stat">
      <span className={`stat-value ${highlight || ""}`}>{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
