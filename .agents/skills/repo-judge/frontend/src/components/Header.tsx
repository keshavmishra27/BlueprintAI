import { RepoJudgeMetadata } from '../types';
import { Layers, Calendar, Fingerprint } from 'lucide-react';

export default function Header({ meta, confidence }: { meta: RepoJudgeMetadata, confidence: string }) {
  return (
    <div className="card mb-4 border-t" style={{ borderTop: '4px solid var(--color-low)' }}>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">{meta.project_name}</h1>
          <div className="flex gap-4 mt-2 text-muted text-sm items-center">
            <span className="flex items-center gap-1"><Calendar size={14}/> {new Date(meta.timestamp).toLocaleString()}</span>
            <span className="flex items-center gap-1"><Fingerprint size={14}/> {meta.analysis_id.split('-')[0]}...</span>
            <span className="flex items-center gap-1">
              Confidence: 
              <span className={`badge ${confidence === 'High' ? 'badge-success' : confidence === 'Medium' ? 'badge-medium' : 'badge-critical'}`}>
                {confidence}
              </span>
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 justify-end text-sm font-semibold mb-1">
            <Layers size={14}/> Tech Stack
          </div>
          <div className="flex gap-2 flex-wrap justify-end max-w-sm">
            {meta.tech_stack.map(tech => (
              <span key={tech} className="badge badge-info" style={{ textTransform: 'none' }}>{tech}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
