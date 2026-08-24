import { useState } from 'react';
import { analyzeIdea } from '../api/decisions';
import type { Decision } from '../types/api';

const IdeaRefiner = () => {
  const [idea, setIdea] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [decision, setDecision] = useState<Decision | null>(null);

  const handleAnalyze = async () => {
    if (!idea.trim()) return;
    setStatus('loading');
    setErrorMessage('');
    try {
      const result = await analyzeIdea(idea);
      setDecision(result);
      setStatus('success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to analyze idea');
      setStatus('error');
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>Idea Refiner</h1>

      <div className="card">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
          What are you building?
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            className="input-field"
            style={{ marginBottom: 0 }}
            placeholder="e.g. Hospital overcrowding predictor..."
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
          />
          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        {status === 'error' && (
          <div style={{ color: 'red', marginTop: '0.5rem', fontSize: '0.875rem' }}>
            {errorMessage}
          </div>
        )}
      </div>

      {decision && (
        <div className="grid grid-cols-2 mt-4 gap-4">
          <div>
            <div className="card">
              <h2 className="card-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Recommended Architecture
              </h2>
              <div className="flex-col">
                {decision.architecture.components.map((comp, idx) => (
                  <div key={idx} className="component-item">
                    <span className="component-name">{comp.name}</span>
                    <span className="component-type">{comp.type}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="card-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Governance
              </h2>
              <div className="flex justify-between items-center mb-4">
                <span className={`badge ${decision.governance.action === 'RECOMMEND' ? 'success' : 'warning'}`}>
                  {decision.governance.action}
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Severity: {decision.governance.severity}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(decision.governance.scores).map(([key, val]) => (
                  <div key={key}>
                    <div className="metric-label">{key}</div>
                    <div className="metric-value" style={{ fontSize: '1.25rem' }}>{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div>
            <div className="card">
              <h2 className="card-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Why this architecture?
              </h2>
              <div style={{ lineHeight: 1.6 }}>
                {decision.architecture.decisions.map((d, i) => (
                  <div key={i} className="mb-2">
                    <strong>+ {d.choice}</strong>: {d.rationale}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="card-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Alternatives
              </h2>
              {decision.alternatives.map((alt, idx) => (
                <div key={idx} className="mb-4">
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{alt.description.split(':')[0]}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                    {alt.description.split(':')[1]}
                  </div>
                  <div className="flex gap-2">
                    {alt.architecture.components.map((c, i) => (
                      <span key={i} className="badge">{c.name}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IdeaRefiner;
