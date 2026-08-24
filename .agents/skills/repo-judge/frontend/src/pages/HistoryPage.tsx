import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAnalyses } from '../api';
import { RepoJudgeListItem } from '../types';
import { FolderGit2, Calendar, AlertCircle } from 'lucide-react';

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<RepoJudgeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAnalyses()
      .then(setAnalyses)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container mt-8 text-center text-muted">Loading analyses...</div>;
  if (error) return (
    <div className="container mt-8">
      <div className="card badge-critical" style={{ padding: '1rem', border: 'none' }}>
        <div className="flex items-center gap-2"><AlertCircle size={20}/> <strong>Error connecting to backend</strong></div>
        <p className="mt-2 text-main">Make sure the Repo Judge backend is running on port 8088.</p>
        <p className="text-muted text-sm mono">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="container mt-4">
      <h1 className="text-2xl font-bold mb-4">Analysis History</h1>
      {analyses.length === 0 ? (
        <div className="card text-center text-muted pt-4 pb-4">No analyses found. Run the Repo Judge skill first.</div>
      ) : (
        <div className="grid grid-cols-2">
          {analyses.map(a => (
            <Link to={`/report/${a.analysis_id}`} key={a.analysis_id} className="card flex flex-col gap-2" style={{ textDecoration: 'none' }}>
              <div className="flex justify-between items-center border-b pb-4">
                <div className="flex items-center gap-2 text-xl font-bold text-main">
                  <FolderGit2 size={24} className="text-muted" />
                  {a.project_name}
                </div>
                <div className={`badge ${a.overall_score >= 75 ? 'badge-success' : a.overall_score >= 50 ? 'badge-medium' : 'badge-critical'}`}>
                  Score: {a.overall_score}
                </div>
              </div>
              <div className="flex items-center gap-2 text-muted text-sm mt-2">
                <Calendar size={16} />
                {new Date(a.timestamp).toLocaleString()}
              </div>
              <div className="mono text-muted text-sm mt-2" style={{ fontSize: '11px' }}>
                ID: {a.analysis_id}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
