import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import IdeaRefiner from './pages/IdeaRefiner';
import RepositoryChecker from './pages/RepositoryChecker';
import Refinement from './pages/Refinement';
import './index.css';

const Navigation = () => {
  const location = useLocation();

  return (
    <header className="navbar">
      <Link to="/" className="navbar-brand">BlueprintAI</Link>
      <nav className="nav-links">
        <Link
          to="/"
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          Dashboard
        </Link>
        <Link
          to="/ideas"
          className={`nav-link ${location.pathname === '/ideas' ? 'active' : ''}`}
        >
          New Architecture
        </Link>
        <Link
          to="/repositories"
          className={`nav-link ${location.pathname === '/repositories' ? 'active' : ''}`}
        >
          Check Repository
        </Link>
      </nav>
    </header>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ideas" element={<IdeaRefiner />} />
            <Route path="/repositories" element={<RepositoryChecker />} />
            <Route path="/refinements/:id" element={<Refinement />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
