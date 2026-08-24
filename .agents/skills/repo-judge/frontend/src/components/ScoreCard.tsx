import { RepoJudgeOverall } from '../types';

export default function ScoreCard({ overall }: { overall: RepoJudgeOverall }) {
  const getScoreColor = (score: number) => {
    if (score >= 75) return 'var(--color-success)';
    if (score >= 50) return 'var(--color-medium)';
    return 'var(--color-critical)';
  };

  return (
    <div className="card mb-4 text-center">
      <div className="text-muted font-semibold uppercase tracking-wide text-sm mb-2">Overall Score</div>
      <div className="text-4xl font-bold font-mono" style={{ color: getScoreColor(overall.score) }}>
        {overall.score} / 100
      </div>
      <div className="mt-4 text-main">{overall.assessment}</div>
    </div>
  );
}
