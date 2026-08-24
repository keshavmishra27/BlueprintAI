import type { Evidence } from "../types";

interface Props {
  evidenceList: Evidence[];
}

export default function EvidenceViewer({ evidenceList }: Props) {
  if (!evidenceList || evidenceList.length === 0) {
    return <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>No evidence available.</p>;
  }

  const getBadgeClass = (classification: string) => {
    if (classification === "verified") return "badge-verified";
    if (classification === "reasoned_assessment") return "badge-reasoned";
    if (classification === "assumption") return "badge-assumption";
    return "";
  };

  const formatClassification = (c: string) => {
    return c.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  return (
    <div style={{ marginTop: "1rem" }}>
      {evidenceList.map(ev => (
        <details key={ev.id}>
          <summary className="flex-between">
            <span>{ev.title}</span>
            <span className={`badge ${getBadgeClass(ev.classification)}`}>
              {formatClassification(ev.classification)}
            </span>
          </summary>
          <div className="evidence-content">
            <p>{ev.description}</p>
            {ev.classification === "verified" && (
              <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                {ev.source && <div><strong>Source:</strong> {ev.source}</div>}
                {ev.url && <div><strong>URL:</strong> <a href={ev.url} target="_blank" rel="noreferrer">{ev.url}</a></div>}
              </div>
            )}
          </div>
        </details>
      ))}
    </div>
  );
}
