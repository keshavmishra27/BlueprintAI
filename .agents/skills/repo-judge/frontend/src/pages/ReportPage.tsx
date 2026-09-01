import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getAnalysis } from '../api';
import { RepositoryAssessment, Component } from '../types';
import Header from '../components/Header';
import ScoreCard from '../components/ScoreCard';
import Findings from '../components/Findings';
import Checks from '../components/Checks';
import { Layout, FileCode, AlertTriangle } from 'lucide-react';

function ArchitectureView({ title, components, icon }: { title: string, components: Component[], icon: React.ReactNode }) {
  if (!components || components.length === 0) return null;
  return (
    <div className="mb-8">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">{icon} {title}</h2>
      <div className="grid grid-cols-2 gap-4">
        {components.map((comp, idx) => (
          <div key={idx} className="card badge-info" style={{ border: '1px solid var(--border)', borderLeft: '4px solid var(--color-success)' }}>
            <div className="flex justify-between items-center mb-2">
              <strong className="text-lg">{comp.name}</strong>
              <span className="badge" style={{ fontSize: '0.75rem' }}>{comp.type}</span>
            </div>
            {comp.description && <p className="text-sm m-0 text-muted">{comp.description}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<RepositoryAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      getAnalysis(id)
        .then(setData)
        .catch(e => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <div className="container mt-8 text-center text-muted">Loading analysis...</div>;
  if (error) return <div className="container mt-8 card badge-critical">Error: {error}</div>;
  if (!data) return <div className="container mt-8 card">Analysis not found.</div>;

  const gapReport = data.structural.report;
  const semantic = data.semantic.report;

  return (
    <div className="container mt-4">
      <Header meta={data.metadata} confidence={semantic?.overall?.confidence || "Medium"} />

      <div className="card mb-8" style={{ borderLeft: '4px solid var(--color-brand)' }}>
        <h3 className="font-bold mb-2">Decision Context</h3>
        <div className="flex gap-8">
          <div>
            <span className="text-muted text-sm block">Decision ID</span>
            <span className="mono">{data.metadata.decision_id}</span>
          </div>
          <div>
            <span className="text-muted text-sm block">Decision Fingerprint</span>
            <span className="mono">{data.metadata.decision_fingerprint}</span>
          </div>
          {gapReport && (
            <div>
              <span className="text-muted text-sm block">Repo Fingerprint</span>
              <span className="mono">{gapReport.repository_fingerprint}</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-8 mb-8">
        {}
        <div className="card" style={{ borderLeft: '4px solid var(--color-success)' }}>
          <div className="flex justify-between items-center border-b pb-4 mb-4" style={{ borderColor: 'var(--border)' }}>
            <div>
              <h2 className="text-2xl font-bold uppercase tracking-wide m-0">Structural Analysis</h2>
              <span className="text-muted text-sm">GapEngine</span>
            </div>
            {data.structural.status !== 'success' && (
              <span className="badge badge-warning">Status: {data.structural.status}</span>
            )}
          </div>

          {data.structural.status === 'success' && gapReport ? (
            <div className="grid" style={{ gridTemplateColumns: '1fr 3fr', gap: '2rem' }}>
              <div className="text-center">
                <div className="text-muted font-bold text-sm mb-2 uppercase tracking-wide">Alignment Score</div>
                <div className="text-5xl font-bold" style={{ color: gapReport.alignment_score >= 80 ? 'var(--color-success)' : gapReport.alignment_score >= 60 ? 'var(--color-warning)' : 'var(--color-critical)' }}>
                  {gapReport.alignment_score}%
                </div>
              </div>
              <div>
                <ArchitectureView 
                  title="Target Architecture" 
                  components={gapReport.expected_architecture?.components || []} 
                  icon={<Layout size={20} className="text-muted" />} 
                />
                <ArchitectureView 
                  title="Repository Evidence (Discovered)" 
                  components={gapReport.actual_architecture?.components || []} 
                  icon={<FileCode size={20} className="text-muted" />} 
                />

                <div>
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <AlertTriangle size={20} style={{ color: 'var(--color-warning)' }} /> 
                    Structural Gaps
                  </h3>
                  <Findings findings={gapReport.findings} allEvidence={gapReport.evidence} />
                </div>
              </div>
            </div>
          ) : (
            <div className="text-muted italic">Structural report is unavailable or failed to generate.</div>
          )}
        </div>

        {}
        <div className="card" style={{ borderLeft: '4px solid var(--color-warning)' }}>
          <div className="flex justify-between items-center border-b pb-4 mb-4" style={{ borderColor: 'var(--border)' }}>
            <div>
              <h2 className="text-2xl font-bold uppercase tracking-wide m-0">Semantic Analysis</h2>
              <span className="text-muted text-sm">Repo Judge LLM</span>
            </div>
            {data.semantic.status !== 'success' && (
              <span className="badge badge-warning">Status: {data.semantic.status}</span>
            )}
          </div>

          {data.semantic.status === 'success' && semantic ? (
            <div className="grid" style={{ gridTemplateColumns: '1fr 3fr', gap: '2rem' }}>
              <div>
                 <ScoreCard overall={semantic.overall} />
              </div>
              <div>
                <h3 className="text-lg font-bold mb-4">Semantic Findings</h3>
                <Findings findings={semantic.findings} allEvidence={semantic.evidence} />
                <Checks checks={semantic.checks} />
              </div>
            </div>
          ) : (
            <div className="text-muted italic">Semantic report is unavailable or failed to generate.</div>
          )}
        </div>
      </div>
    </div>
  );
}
