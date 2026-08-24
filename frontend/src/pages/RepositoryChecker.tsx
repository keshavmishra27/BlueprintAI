import { useState } from 'react';
import { Link } from 'react-router-dom';
import { analyzeRepository } from '../api/repositories';
import type { GapReport } from '../types/api';

const RepositoryChecker = () => {
  const [repoPath, setRepoPath] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [report, setReport] = useState<GapReport | null>(null);

  const handleAnalyze = async () => {
    if (!repoPath.trim()) return;
    setStatus('loading');
    setErrorMessage('');
    try {
      // Hardcoded decisionId for demo purposes
      const result = await analyzeRepository('1c854183-05a8-4e60-9903-8ed73ea8dad7', repoPath);
      setReport(result);
      setStatus('success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to analyze repository');
      setStatus('error');
    }
  };

  const getBadgeClass = (category: string) => {
    switch (category) {
      case 'MATCH': return 'success';
      case 'MISMATCH': return 'error';
      case 'MISSING': return 'warning';
      case 'UNKNOWN': return 'info';
      default: return '';
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>Repo Checker</h1>

      <div className="card">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
          Repository (GitHub URL or Local Path)
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            className="input-field"
            style={{ marginBottom: 0 }}
            placeholder="e.g. https://github.com/user/repo..."
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
          />
          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Analyzing...' : 'Analyze Repository'}
          </button>
        </div>
        {status === 'error' && (
          <div style={{ color: 'red', marginTop: '0.5rem', fontSize: '0.875rem' }}>
            {errorMessage}
          </div>
        )}
      </div>

      {report && (
        <div className="grid grid-cols-3 mt-4 gap-4">
          <div style={{ gridColumn: 'span 1' }}>
            <div className="card">
              <h2 className="card-title">Alignment Score</h2>
              <div className="metric-value" style={{ fontSize: '3rem', color: report.alignment_score > 0.7 ? '#34d399' : '#fbbf24' }}>
                {Math.round(report.alignment_score * 100)}%
              </div>

              <div className="mt-4 flex-col gap-2">
                <div className="flex justify-between">
                  <span>MATCH</span>
                  <span style={{ fontWeight: 600 }}>{report.findings.filter(f => f.category === 'MATCH').length}</span>
                </div>
                <div className="flex justify-between">
                  <span>MISSING</span>
                  <span style={{ fontWeight: 600 }}>{report.findings.filter(f => f.category === 'MISSING').length}</span>
                </div>
                <div className="flex justify-between">
                  <span>MISMATCH</span>
                  <span style={{ fontWeight: 600 }}>{report.findings.filter(f => f.category === 'MISMATCH').length}</span>
                </div>
                <div className="flex justify-between">
                  <span>UNKNOWN</span>
                  <span style={{ fontWeight: 600 }}>{report.findings.filter(f => f.category === 'UNKNOWN').length}</span>
                </div>
              </div>

              <div className="mt-4" style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                <Link to={`/refinements/${report.id}`} className="btn btn-primary w-full">
                  Refine Architecture
                </Link>
              </div>
            </div>
          </div>

          <div style={{ gridColumn: 'span 2' }}>
            <h2 className="card-title mb-4">Evidence</h2>
            {report.findings.map((finding, idx) => (
              <div key={idx} className="gap-item">
                <div className="flex justify-between items-center mb-2">
                  <span className={`badge ${getBadgeClass(finding.category)}`}>{finding.category}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-2">
                  <div>
                    <div className="metric-label">Expected</div>
                    <div style={{ fontWeight: 500 }}>{finding.expected}</div>
                  </div>
                  <div>
                    <div className="metric-label">Detected</div>
                    <div style={{ fontWeight: 500 }}>{finding.observed}</div>
                  </div>
                </div>

                {/* Find evidence for this finding if any */}
                {report.evidence.length > 0 && finding.category !== 'MATCH' && finding.category !== 'UNKNOWN' && (
                  <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--border-color)' }}>
                    <div className="metric-label">Evidence in <strong>{report.evidence[0].file}</strong>:line {report.evidence[0].line}</div>
                    <pre>{report.evidence[0].content}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RepositoryChecker;
