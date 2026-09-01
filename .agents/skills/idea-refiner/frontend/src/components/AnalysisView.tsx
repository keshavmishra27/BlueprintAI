import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAnalysis } from "../api";
import type { IdeaRefinerResult } from "../types";

export default function AnalysisView() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<IdeaRefinerResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getAnalysis(id)
      .then(result => {
        setData(result);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message === "Failed to fetch" ? "Backend Offline: Unable to connect to the Product API." : err.message);
        setLoading(false);
      });
  }, [id]);

  if (loading) return <div className="state-container"><h2>Loading Decision...</h2></div>;

  if (error) {
    return (
      <div className="state-container">
        <h2>Error Loading Decision</h2>
        <p style={{ color: "var(--score-negative)" }}>{error}</p>
        <Link to="/" className="badge badge-verified" style={{ marginTop: "1rem" }}>Back to Dashboard</Link>
      </div>
    );
  }

  if (!data) return null;

  const getGovernanceColor = (severity: string) => {
    const s = severity.toLowerCase();
    if (s.includes("critical") || s.includes("high")) return "var(--score-negative)";
    if (s.includes("medium")) return "var(--score-neutral)";
    return "var(--score-positive)";
  };

  return (
    <div>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/" className="badge badge-verified">← Back to Dashboard</Link>
      </div>

      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h2>Decision Record</h2>
        <div className="grid-2">
          <div>
            <strong>Decision ID:</strong>
            <div style={{ fontFamily: 'monospace', marginTop: '0.25rem' }}>{data.id}</div>
          </div>
          <div>
            <strong>Fingerprint:</strong>
            <div style={{ fontFamily: 'monospace', marginTop: '0.25rem' }}>{data.decision_fingerprint}</div>
          </div>
          <div>
            <strong>Governance Action:</strong>
            <div style={{ marginTop: '0.25rem', fontWeight: 'bold' }}>{data.governance.action}</div>
          </div>
          <div>
            <strong>Severity:</strong>
            <div style={{ 
              marginTop: '0.25rem', 
              fontWeight: 'bold', 
              color: getGovernanceColor(data.governance.severity) 
            }}>
              {data.governance.severity}
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>Target Architecture</h2>
        <h3>Components</h3>
        {data.architecture.components.map((comp, idx) => (
          <div key={idx} style={{ 
            border: '1px solid var(--border-color)', 
            padding: '1rem', 
            borderRadius: '4px',
            marginBottom: '0.5rem',
            borderLeft: comp.unresolved ? '4px solid var(--score-neutral)' : '4px solid var(--score-positive)'
          }}>
            <div className="flex-between">
              <strong>{comp.name}</strong>
              <span className="badge">{comp.type}</span>
            </div>
            {comp.description && <p style={{ marginTop: '0.5rem' }}>{comp.description}</p>}
            {comp.unresolved && (
              <span className="badge badge-unresolved" style={{ marginTop: '0.5rem', display: 'inline-block', backgroundColor: 'var(--score-neutral)' }}>
                UNRESOLVED / Epistemic Uncertainty
              </span>
            )}
          </div>
        ))}

        <h3 style={{ marginTop: '1.5rem' }}>Decisions</h3>
        {data.architecture.decisions && data.architecture.decisions.length > 0 ? (
          data.architecture.decisions.map((dec, idx) => (
            <div key={idx} style={{ border: '1px solid var(--border-color)', padding: '1rem', borderRadius: '4px', marginBottom: '0.5rem' }}>
              <strong>{dec.name || `Decision ${idx + 1}`}</strong>
              <p style={{ marginTop: '0.5rem' }}>{dec.description || JSON.stringify(dec)}</p>
            </div>
          ))
        ) : (
          <p>No architectural decisions recorded.</p>
        )}
      </div>
    </div>
  );
}
