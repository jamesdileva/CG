import { HashRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Topics } from './pages/Topics';
import { Research } from './pages/Research';
import { ScriptEditor } from './pages/ScriptEditor';
import { Production } from './pages/Production';
import { Publish } from './pages/Publish';
import { Analytics } from './pages/Analytics';
import './App.css';

function App() {
  return (
    <Router future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
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
            <Link to="/research" className="nav-link">
              Research
            </Link>
            <Link to="/scripts" className="nav-link">
              Scripts
            </Link>
            <Link to="/production" className="nav-link">
              Production
            </Link>
            <Link to="/publish" className="nav-link">
              Publish
            </Link>
            <Link to="/analytics" className="nav-link">
              Analytics
            </Link>
          </div>
        </nav>

        <main className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/topics" element={<Topics />} />
            <Route path="/research" element={<Research />} />
            <Route path="/scripts" element={<ScriptEditor />} />
            <Route path="/production" element={<Production />} />
            <Route path="/publish" element={<Publish />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
