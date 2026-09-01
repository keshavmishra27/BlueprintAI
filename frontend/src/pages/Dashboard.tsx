import { Link } from 'react-router-dom';

const Dashboard = () => {
  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Your Architecture Decisions</h1>

      <div className="card">
        <h2 className="card-title">Hospital Overcrowding Predictor</h2>
        <div className="grid grid-cols-3 mb-4">
          <div>
            <div className="metric-label">Alignment</div>
            <div className="metric-value" style={{ color: '#34d399' }}>81%</div>
          </div>
          <div>
            <div className="metric-label">Status</div>
            <div className="metric-value"><span className="badge success">RECOMMEND</span></div>
          </div>
          <div>
            <div className="metric-label">Version</div>
            <div className="metric-value">D1</div>
          </div>
        </div>
        <Link to="/ideas" className="btn btn-primary">View Architecture</Link>
      </div>

      <div className="card">
        <h2 className="card-title">E-commerce Recommendation System</h2>
        <div className="grid grid-cols-3 mb-4">
          <div>
            <div className="metric-label">Alignment</div>
            <div className="metric-value" style={{ color: '#fbbf24' }}>63%</div>
          </div>
          <div>
            <div className="metric-label">Status</div>
            <div className="metric-value"><span className="badge warning">HOLD_FOR_REVIEW</span></div>
          </div>
          <div>
            <div className="metric-label">Version</div>
            <div className="metric-value">D0</div>
          </div>
        </div>
        <Link to="/repositories" className="btn btn-primary">Inspect Gaps</Link>
      </div>
    </div>
  );
};

export default Dashboard;
