import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAnalyses } from "../api";

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalyses()
      .then(data => {
        setAnalyses(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message === "Failed to fetch" ? "Backend Offline: Unable to connect to the Product API." : err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="state-container"><h2>Loading History...</h2></div>;
  }

  if (error) {
    return (
      <div className="state-container">
        <h2>Backend Unavailable</h2>
        <p style={{ color: "var(--score-negative)" }}>{error}</p>
        <p>Please ensure the Product API is running on port 8000.</p>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="state-container">
        <h2>No Analyses Found</h2>
        <p>There are no past idea refinements in the database.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Refinement History</h2>
      <ul className="dashboard-list">
        {analyses.map(item => (
          <li key={item.id} className="flex-between">
            <div>
              <strong>{item.id}</strong>
              <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                {new Date(item.created_at).toLocaleString()}
              </div>
            </div>
            <Link to={`/analysis/${item.id}`} className="badge badge-verified">View</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
