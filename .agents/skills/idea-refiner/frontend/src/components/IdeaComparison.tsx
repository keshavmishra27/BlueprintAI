import type { IdeaVersion } from "../types";

interface Props {
  originalIdea: IdeaVersion;
  refinedIdea: IdeaVersion;
}

export default function IdeaComparison({ originalIdea, refinedIdea }: Props) {
  return (
    <div className="grid-2">
      <div className="card">
        <h3>Original Idea</h3>
        <p><strong>Concept:</strong> {originalIdea.concise_concept}</p>
        <p><strong>Target Users:</strong> {originalIdea.target_users}</p>
        <p><strong>Problem:</strong> {originalIdea.problem}</p>
        <p><strong>Solution:</strong> {originalIdea.solution}</p>
        <p><strong>Differentiation:</strong> {originalIdea.differentiation}</p>
      </div>
      
      <div className="card" style={{ border: "2px solid var(--score-positive)" }}>
        <h3>Refined Idea</h3>
        <p><strong>Concept:</strong> {refinedIdea.concise_concept}</p>
        <p><strong>Target Users:</strong> {refinedIdea.target_users}</p>
        <p><strong>Problem:</strong> {refinedIdea.problem}</p>
        <p><strong>Solution:</strong> {refinedIdea.solution}</p>
        <p><strong>Differentiation:</strong> {refinedIdea.differentiation}</p>
      </div>
    </div>
  );
}
