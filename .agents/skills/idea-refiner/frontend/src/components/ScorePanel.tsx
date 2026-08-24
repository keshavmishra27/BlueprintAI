import type { IdeaRefinerScores, RefinementType } from "../types";

interface Props {
  scores: IdeaRefinerScores;
  refinementType?: RefinementType;
}

export default function ScorePanel({ scores, refinementType }: Props) {
  const formatRefinementType = (type?: string) => {
    if (!type) return "N/A";
    return type.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  return (
    <div className="score-panel">
      <h3>Overall Improvement</h3>
      <div className="score-huge">+{scores.score_improvement}</div>
      <div className="score-delta">
        <span>{scores.weighted_original_score} → {scores.weighted_refined_score}</span>
        {refinementType && (
          <span className="badge badge-refinement">{formatRefinementType(refinementType)}</span>
        )}
      </div>
      <div style={{ marginTop: "1rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
        Coverage: {scores.original_coverage} / 8 → {scores.refined_coverage} / 8
      </div>
    </div>
  );
}
