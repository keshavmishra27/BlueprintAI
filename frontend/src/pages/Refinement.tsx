import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { applyRefinement } from '../api/refinements';
import { getDecision } from '../api/decisions';
import type { Decision } from '../types/api';

const Refinement = () => {
  const { id } = useParams<{ id: string }>();
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [d0, setD0] = useState<Decision | null>(null);
  const [d1, setD1] = useState<Decision | null>(null);

  // Fetch D0 on mount (mocked)
  useEffect(() => {
    const fetchD0 = async () => {
      const result = await getDecision('1c854183-05a8-4e60-9903-8ed73ea8dad7');
      setD0(result);
    };
    fetchD0();
  }, []);

  const handleRefine = async () => {
    setStatus('loading');
    setErrorMessage('');
    try {
      // Mocking the call to applyRefinement
      const result = await applyRefinement('1c854183-05a8-4e60-9903-8ed73ea8dad7', id || null, 'Mock Exploration', [], 'MISMATCH detected');
      setD1(result);
      setStatus('success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to refine architecture');
      setStatus('error');
    }
  };

  if (!d0) return <div>Loading base decision...</div>;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>Architecture Refinement</h1>

      {!d1 ? (
        <div className="card">
          <h2 className="card-title">Detected gaps in Repository</h2>
          <div className="mb-4 flex-col gap-2">
            <div className="flex gap-2 items-center">
              <span className="badge error">MISMATCH</span>
              <span>PostgreSQL → MongoDB</span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="badge warning">MISSING</span>
              <span>Redis</span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="badge info">UNKNOWN</span>
              <span>Monitoring</span>
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleRefine}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Generating D1...' : 'Generate refined architecture'}
          </button>

          {status === 'error' && (
            <div style={{ color: 'red', marginTop: '0.5rem', fontSize: '0.875rem' }}>
              {errorMessage}
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <h2 className="card-title">Why was D1 generated?</h2>
          <div className="grid grid-cols-2 gap-4 mb-4" style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
            <div>
              <div className="metric-label mb-2"><span className="badge warning">MISSING</span></div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}><li>Redis</li></ul>
            </div>
            <div>
              <div className="metric-label mb-2"><span className="badge error">MISMATCH</span></div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}><li>PostgreSQL → MongoDB</li></ul>
            </div>
            <div>
              <div className="metric-label mb-2"><span className="badge success">PRESERVED</span></div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}><li>FastAPI</li></ul>
            </div>
            <div>
              <div className="metric-label mb-2"><span className="badge info">UNKNOWN</span></div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}><li>Monitoring deployment</li></ul>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 style={{ margin: '0 0 1rem 0' }}>D0</h3>
              <div className="metric-value mb-4" style={{ fontSize: '1.5rem', color: '#fbbf24' }}>
                Alignment: {Math.round((d0.alignment || 0) * 100)}%
              </div>
              <div className="flex-col">
                {d0.architecture.components.map((c, i) => (
                  <div key={i} className="component-item">
                    <span>{c.name}</span>
                    {c.name === 'PostgreSQL' && <span style={{ color: '#ef4444' }}>✗</span>}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 style={{ margin: '0 0 1rem 0' }}>D1</h3>
              <div className="metric-value mb-4" style={{ fontSize: '1.5rem', color: '#34d399' }}>
                Alignment: {Math.round((d1.alignment || 0) * 100)}%
              </div>
              <div className="flex-col">
                {d1.architecture.components.map((c, i) => (
                  <div key={i} className="component-item">
                    <span>{c.name}</span>
                    <span style={{ color: '#10b981' }}>✓</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Refinement;
