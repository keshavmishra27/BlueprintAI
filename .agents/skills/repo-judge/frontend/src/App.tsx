import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HistoryPage from './pages/HistoryPage';
import ReportPage from './pages/ReportPage';
import { Shield } from 'lucide-react';

function App() {
  return (
    <Router>
      <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', background: 'var(--bg-card)' }}>
        <div className="container flex items-center justify-between" style={{ padding: '0', maxWidth: '1200px', margin: '0 auto' }}>
          <Link to="/" className="flex items-center gap-2" style={{ color: 'var(--text-main)', textDecoration: 'none' }}>
            <Shield size={24} style={{ color: 'var(--color-low)' }} />
            <span className="font-bold text-lg">Repo Judge</span>
          </Link>
          <div className="flex gap-4">
            <Link to="/" className="text-sm font-semibold">History</Link>
          </div>
        </div>
      </div>
      <Routes>
        <Route path="/" element={<HistoryPage />} />
        <Route path="/report/:id" element={<ReportPage />} />
      </Routes>
    </Router>
  );
}

export default App;
