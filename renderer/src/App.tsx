import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Topics } from './pages/Topics';
import { ScriptEditor } from './pages/ScriptEditor';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="app-nav">
          <Link to="/" className="nav-logo">
            Documentary Studio
          </Link>
          <div className="nav-links">
            <Link to="/" className="nav-link">
              Dashboard
            </Link>
            <Link to="/topics" className="nav-link">
              Topics
            </Link>
            <Link to="/scripts" className="nav-link">
              Scripts
            </Link>
          </div>
        </nav>

        <main className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/topics" element={<Topics />} />
            <Route path="/scripts" element={<ScriptEditor />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

