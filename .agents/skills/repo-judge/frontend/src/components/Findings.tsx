import { useState } from 'react';
import { RepoJudgeFinding, RepoJudgeEvidence } from '../types';
import { AlertTriangle, Info, MapPin } from 'lucide-react';

function EvidenceDisplay({ ev }: { ev: RepoJudgeEvidence }) {
  return (
    <div className="mt-2 p-3 rounded" style={{ background: 'var(--bg-main)', borderLeft: '3px solid var(--text-muted)' }}>
      <div className="flex items-center gap-2 mb-1">
        <span className="badge badge-info">{ev.source_type}</span>
        {ev.file_path && (
          <span className="mono text-sm text-muted flex items-center gap-1">
            <MapPin size={12}/> 
            {ev.file_path}
            {(ev.line_start || ev.line_end) ? `:${ev.line_start || ''}-${ev.line_end || ''}` : ''}
          </span>
        )}
      </div>
      <p className="text-sm m-0">{ev.description}</p>
    </div>
  );
}

export default function Findings({ findings, allEvidence }: { findings: RepoJudgeFinding[], allEvidence: RepoJudgeEvidence[] }) {
  const [sevFilter, setSevFilter] = useState<string>('All');

  const severities = ['All', 'Critical', 'High', 'Medium', 'Low', 'Info'];
  
  const filtered = findings.filter(f => sevFilter === 'All' || f.severity === sevFilter);

  const getSeverityBadge = (sev: string) => {
    switch(sev) {
      case 'Critical': return 'badge-critical';
      case 'High': return 'badge-high';
      case 'Medium': return 'badge-medium';
      case 'Low': return 'badge-low';
      default: return 'badge-info';
    }
  };

  return (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Findings</h2>
        <div className="flex gap-2">
          {severities.map(s => (
            <button 
              key={s} 
              className={`filter-btn ${sevFilter === s ? 'active' : ''}`}
              onClick={() => setSevFilter(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      
      {filtered.length === 0 ? (
        <div className="card text-center text-muted py-8">No findings match this filter.</div>
      ) : (
        <div className="flex flex-col gap-4">
          {filtered.map(f => (
            <div key={f.id} className="card">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  {['Critical', 'High'].includes(f.severity) ? <AlertTriangle size={20} className="text-critical" style={{ color: 'var(--color-critical)' }} /> : <Info size={20} className="text-muted" />}
                  <h3 className="text-lg font-bold">{f.title}</h3>
                </div>
                <div className="flex gap-2">
                  <span className={`badge ${getSeverityBadge(f.severity)}`}>{f.severity}</span>
                  <span className="badge badge-info">{f.category}</span>
                </div>
              </div>
              
              <div className="text-sm font-semibold text-muted mb-2">{f.classification}</div>
              
              <p className="mb-2"><strong>Explanation:</strong> {f.explanation}</p>
              <p className="mb-2 text-muted"><strong>Impact:</strong> {f.impact}</p>
              <p className="mb-4"><strong>Recommendation:</strong> {f.recommendation}</p>
              
              {f.evidence_ids.length > 0 && (
                <div className="border-t pt-3">
                  <strong className="text-sm text-muted uppercase tracking-wider mb-2 block">Supporting Evidence</strong>
                  {f.evidence_ids.map(eid => {
                    const ev = allEvidence.find(e => e.id === eid);
                    return ev ? <EvidenceDisplay key={eid} ev={ev} /> : <div key={eid} className="text-sm text-muted">Evidence {eid} not found.</div>;
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
