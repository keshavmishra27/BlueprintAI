import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import AnalysisView from "./components/AnalysisView";

function App() {
  return (
    <Router>
      <div className="container">
        <header style={{ marginBottom: "2rem" }}>
          <h1>
            <Link to="/" style={{ color: "var(--text-primary)" }}>Idea Refiner</Link>
          </h1>
        </header>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis/:id" element={<AnalysisView />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
