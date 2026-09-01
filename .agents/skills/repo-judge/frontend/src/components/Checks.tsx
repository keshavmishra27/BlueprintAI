import { RepoJudgeCheck } from '../types';
import { CheckCircle2, XCircle, Slash } from 'lucide-react';

export default function Checks({ checks }: { checks: RepoJudgeCheck[] }) {
  if (!checks || checks.length === 0) return null;

  const getIcon = (status: string) => {
    switch(status) {
      case 'completed': return <CheckCircle2 size={18} className="text-success" style={{ color: 'var(--color-success)' }}/>;
      case 'failed': return <XCircle size={18} className="text-critical" style={{ color: 'var(--color-critical)' }}/>;
      default: return <Slash size={18} className="text-muted" />;
    }
  };

  return (
    <div className="mb-8">
      <h2 className="text-xl font-bold mb-4">Deterministic Checks</h2>
      <div className="grid grid-cols-2">
        {checks.map(c => (
          <div key={c.name} className="card flex items-start gap-3">
            <div className="mt-1">{getIcon(c.status)}</div>
            <div style={{ flex: 1 }}>
              <div className="flex justify-between items-center mb-1">
                <strong className="font-mono">{c.name}</strong>
                <span className={`badge ${c.status === 'completed' ? 'badge-success' : c.status === 'failed' ? 'badge-critical' : 'badge-info'}`}>
                  {c.status}
                </span>
              </div>
              <p className="text-sm text-muted m-0">{c.summary}</p>
              {c.exit_code !== undefined && <div className="text-xs text-muted mono mt-2">Exit Code: {c.exit_code}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
