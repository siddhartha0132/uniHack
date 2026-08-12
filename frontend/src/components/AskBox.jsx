import { useState } from "react";
import { api } from "../api/client";

export default function AskBox({ productId }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setAnswer(null);
    try {
      const data = await api.ask(productId, q);
      setAnswer(data);
    } catch (e) {
      setAnswer({ error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") handleAsk();
  };

  return (
    <div className="ask-box card">
      <div className="ask-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <h3>Ask about this product</h3>
      </div>

      <div className="ask-row">
        <input
          className="input"
          type="text"
          placeholder="e.g. what is the operating temperature range?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button
          className="btn btn-primary btn-sm"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          style={{ flexShrink: 0 }}
        >
          {loading ? <span className="mini-spinner" /> : "Ask"}
        </button>
      </div>

      {answer && !answer.error && (
        <div className="ask-answer">
          <div className="answer-value">
            {answer.answer}
            {answer.confidence !== undefined && (
              <span className="answer-conf">
                {Math.round(answer.confidence * 100)}% confidence
              </span>
            )}
          </div>
          {answer.reasoning && (
            <p className="answer-reasoning">{answer.reasoning}</p>
          )}
        </div>
      )}

      {answer?.error && (
        <div className="ask-error">{answer.error}</div>
      )}

      <style>{`
        .ask-box { margin-top: 20px; }
        .ask-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 14px;
        }
        .ask-header h3 {
          font-family: var(--font-display);
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-secondary);
          font-weight: 600;
        }
        .ask-row {
          display: flex;
          gap: 8px;
        }
        .ask-answer {
          margin-top: 14px;
          padding: 14px;
          border: 1px solid var(--teal-dim);
          background: rgba(63,193,169,0.04);
          border-radius: var(--radius);
          animation: slideUp 200ms var(--ease);
        }
        .answer-value {
          font-family: var(--font-display);
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          flex-wrap: wrap;
        }
        .answer-conf {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--teal);
          font-weight: 400;
        }
        .answer-reasoning {
          margin-top: 8px;
          font-size: 12.5px;
          color: var(--text-secondary);
          line-height: 1.6;
        }
        .ask-error {
          margin-top: 12px;
          padding: 10px 12px;
          border-radius: var(--radius);
          border: 1px solid var(--red-dim);
          color: var(--red);
          font-size: 12.5px;
          font-family: var(--font-mono);
        }
        .mini-spinner {
          display: inline-block;
          width: 12px; height: 12px;
          border: 2px solid rgba(7,20,18,0.3);
          border-top-color: #071412;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
      `}</style>
    </div>
  );
}
