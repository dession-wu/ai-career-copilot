import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

const customStyles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&display=swap');

  :root {
    --bg-paper: #f4f3ef;
    --bg-sand: #e4e1d7;
    --bg-sage: #ccd1c8;
    --bg-terra: #d45d43;
    --bg-dark: #1a1a18;
    --text-main: #1a1a18;
    --text-muted: #6b6a65;
    --text-light: #f4f3ef;
    --border-subtle: #d1cfc9;
    --border-dark: #1a1a18;
    --highlight-terra: rgba(212, 93, 67, 0.15);
    --highlight-sage: rgba(181, 190, 176, 0.3);
    --font-serif: 'Newsreader', serif;
    --font-sans: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --gap: 1.5rem;
    --nav-width: 220px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background-color: var(--bg-paper);
    color: var(--text-main);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-size: 14px;
    line-height: 1.5;
  }

  .provenance-app {
    height: 100vh;
    display: flex;
    overflow: hidden;
  }

  .app-container {
    display: grid;
    grid-template-columns: var(--nav-width) 1fr 320px;
    width: 100%;
    height: 100%;
  }

  .border-r { border-right: 1px solid var(--border-subtle); }
  .border-b { border-bottom: 1px solid var(--border-subtle); }
  .border-l { border-left: 1px solid var(--border-subtle); }
  .border-t { border-top: 1px solid var(--border-subtle); }

  nav.prov-nav {
    padding: 2rem 1.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background-color: var(--bg-sand);
    border-right: 1px solid var(--border-subtle);
  }

  .logo {
    font-family: var(--font-serif);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 600;
    margin-bottom: 3rem;
    display: block;
    color: var(--text-main);
  }

  .nav-links { list-style: none; display: flex; flex-direction: column; gap: 1rem; }

  .nav-links li a {
    text-decoration: none;
    color: var(--text-muted);
    font-family: var(--font-sans);
    font-size: 0.85rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: color 0.2s;
  }

  .nav-links li a:hover, .nav-links li a.active { color: var(--text-main); }

  .nav-links li a.active::before {
    content: '→';
    font-family: var(--font-mono);
    font-size: 0.8rem;
  }

  .nav-footer {
    border-top: 1px solid var(--border-dark);
    padding-top: 1rem;
  }

  main.prov-main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    overflow-y: auto;
    position: relative;
  }

  .folio {
    position: absolute;
    top: 1rem;
    font-family: var(--font-mono);
    font-size: 0.65rem;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.1em;
  }
  .folio.left { left: 1.5rem; }
  .folio.right { right: 1.5rem; }

  section.panel {
    padding: 3rem 2.5rem;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .header-block { margin-bottom: 1rem; }

  .meta-tag {
    display: inline-block;
    border: 1px solid var(--border-dark);
    padding: 0.2rem 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.7rem;
    text-transform: uppercase;
    margin-bottom: 1rem;
  }

  .t-h2 { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; line-height: 1.1; }
  .t-h3 { font-family: var(--font-sans); font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
  .t-ui { font-family: var(--font-sans); font-size: 0.85rem; font-weight: 500; }
  .t-micro { font-family: var(--font-mono); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

  .radar-container {
    width: 100%;
    aspect-ratio: 1/1;
    max-width: 300px;
    margin: 0 auto;
    position: relative;
  }

  .radar-chart { width: 100%; height: 100%; overflow: visible; }
  .radar-grid { stroke: var(--border-subtle); stroke-width: 1; fill: none; }
  .radar-axis { stroke: var(--border-subtle); stroke-width: 1; stroke-dasharray: 2 2; }
  .radar-data-jd { stroke: var(--text-muted); stroke-width: 1.5; fill: rgba(0,0,0,0.03); }
  .radar-data-user { stroke: var(--bg-terra); stroke-width: 2; fill: var(--highlight-terra); }
  .radar-label { font-family: var(--font-mono); font-size: 10px; fill: var(--text-main); text-anchor: middle; }

  .jd-text-box {
    font-family: var(--font-serif);
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-muted);
    column-count: 2;
    column-gap: 2rem;
    text-align: justify;
  }

  mark.jd-req {
    background-color: transparent;
    border-bottom: 1px solid var(--text-main);
    color: var(--text-main);
    padding-bottom: 1px;
  }

  .engine-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    height: 100%;
  }

  .workflow-step {
    border: 1px solid var(--border-subtle);
    background: var(--bg-paper);
    position: relative;
  }

  .workflow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--border-subtle);
    background: rgba(0,0,0,0.02);
  }

  .workflow-body {
    padding: 1.5rem;
    font-family: var(--font-serif);
    font-size: 1.1rem;
    line-height: 1.5;
  }

  .connection-arrow {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 20px;
    color: var(--border-subtle);
  }

  .source-vault { border-left: 3px solid var(--bg-sage); }
  .output-resume { border-left: 3px solid var(--bg-terra); }

  mark.source-hl { background-color: var(--highlight-sage); color: inherit; padding: 0 0.2em; }
  mark.output-hl { background-color: var(--highlight-terra); color: inherit; padding: 0 0.2em; }

  .strict-rule {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--bg-terra);
    margin-top: 1rem;
  }

  aside.prov-aside {
    background-color: var(--bg-dark);
    color: var(--bg-paper);
    padding: 2rem 1.5rem;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    border-left: 1px solid var(--border-subtle);
  }

  aside.prov-aside .t-micro {
    color: rgba(255,255,255,0.5);
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
    display: block;
  }

  .kanban-item {
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
    margin-bottom: 1rem;
    background: rgba(255,255,255,0.03);
    cursor: pointer;
    transition: all 0.2s;
  }

  .kanban-item.active {
    border-color: var(--bg-terra);
    background: rgba(212, 93, 67, 0.1);
  }

  .k-title { font-family: var(--font-sans); font-weight: 500; font-size: 0.9rem; margin-bottom: 0.25rem; }
  .k-company { font-family: var(--font-serif); font-style: italic; color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 1rem; }

  .k-status {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: var(--font-mono);
    font-size: 0.65rem;
    text-transform: uppercase;
    padding: 0.2rem 0.4rem;
    background: rgba(255,255,255,0.1);
  }

  .vault-list { margin-top: 3rem; }
  .vault-item {
    padding: 0.75rem 0;
    border-bottom: 1px dashed rgba(255,255,255,0.1);
    font-family: var(--font-sans);
    font-size: 0.8rem;
    color: rgba(255,255,255,0.8);
    display: flex;
    justify-content: space-between;
  }

  .vault-item span.tag {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--bg-sage);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    font-family: var(--font-sans);
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: transparent;
    border: 1px solid var(--border-dark);
    color: var(--text-main);
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn:hover { background: var(--text-main); color: var(--bg-paper); }

  .btn-primary {
    background: var(--bg-terra);
    border-color: var(--bg-terra);
    color: #fff;
  }

  .btn-primary:hover {
    background: var(--text-main);
    border-color: var(--text-main);
  }

  .btn-dark {
    color: white;
    border-color: rgba(255,255,255,0.2);
  }

  .btn-dark:hover {
    background: rgba(255,255,255,0.1);
    color: white;
  }

  .mt-2 { margin-top: 0.5rem; }
  .mt-4 { margin-top: 1rem; }
  .mt-8 { margin-top: 2rem; }
  .mb-2 { margin-bottom: 0.5rem; }
  .mb-4 { margin-bottom: 1rem; }
  .pb-2 { padding-bottom: 0.5rem; }
  .w-full { width: 100%; }

  .text-muted { color: var(--text-muted); }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border-subtle); }
  aside.prov-aside ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); }

  .toast-overlay {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-dark);
    color: var(--bg-paper);
    padding: 0.75rem 1.5rem;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    z-index: 1000;
    border: 1px solid rgba(255,255,255,0.2);
    animation: fadeInUp 0.3s ease;
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateX(-50%) translateY(10px); }
    to { opacity: 1; transform: translateX(-50%) translateY(0); }
  }
`;

const LayoutDashboardIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>
  </svg>
);

const FileTextIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>
  </svg>
);

const DatabaseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>
  </svg>
);

const MessageSquareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);

const ArrowDownIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
  </svg>
);

const ShieldCheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>
  </svg>
);

const ClockIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
);

const CalendarIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>
  </svg>
);

const Navigation = ({ activeNav, setActiveNav }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboardIcon /> },
    { id: 'editor', label: 'Document Editor', icon: <FileTextIcon /> },
    { id: 'vault', label: 'Career Vault', icon: <DatabaseIcon /> },
    { id: 'interview', label: 'Interview Prep', icon: <MessageSquareIcon /> },
  ];

  return (
    <nav className="prov-nav">
      <div>
        <span className="logo">Provenance.</span>
        <ul className="nav-links">
          {navItems.map(item => (
            <li key={item.id}>
              <a
                href="#"
                className={activeNav === item.id ? 'active' : ''}
                onClick={(e) => { e.preventDefault(); setActiveNav(item.id); }}
              >
                {item.icon} {item.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
      <div className="nav-footer">
        <div className="t-micro mb-2">System Status</div>
        <div className="t-ui" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--bg-sage)' }}></div>
          Strict Mode Active
        </div>
      </div>
    </nav>
  );
};

const RadarChart = () => (
  <div className="radar-container mt-4">
    <svg viewBox="0 0 200 200" className="radar-chart">
      <circle cx="100" cy="100" r="80" className="radar-grid" />
      <circle cx="100" cy="100" r="60" className="radar-grid" />
      <circle cx="100" cy="100" r="40" className="radar-grid" />
      <circle cx="100" cy="100" r="20" className="radar-grid" />
      <line x1="100" y1="100" x2="100" y2="20" className="radar-axis" />
      <line x1="100" y1="100" x2="176" y2="75" className="radar-axis" />
      <line x1="100" y1="100" x2="147" y2="164" className="radar-axis" />
      <line x1="100" y1="100" x2="53" y2="164" className="radar-axis" />
      <line x1="100" y1="100" x2="24" y2="75" className="radar-axis" />
      <text x="100" y="12" className="radar-label">Strategy</text>
      <text x="186" y="78" className="radar-label">AI/ML</text>
      <text x="155" y="176" className="radar-label">Execution</text>
      <text x="45" y="176" className="radar-label">Data</text>
      <text x="14" y="78" className="radar-label">UX</text>
      <polygon points="100,20 160,80 140,150 60,150 40,80" className="radar-data-jd" />
      <polygon points="100,40 130,90 147,164 45,140 24,75" className="radar-data-user" />
    </svg>
    <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
      <span className="t-micro" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span style={{ width: '8px', height: '8px', background: 'var(--text-muted)' }}></span> Job Req
      </span>
      <span className="t-micro" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span style={{ width: '8px', height: '8px', background: 'var(--bg-terra)' }}></span> Your Vault
      </span>
    </div>
  </div>
);

const LeftPanel = () => (
  <section className="panel left-page border-r" style={{ position: 'relative' }}>
    <div className="folio left">Fig. 1 — Requirement Analysis</div>
    <div className="header-block mt-8">
      <div className="meta-tag">Target Profile</div>
      <h1 className="t-h2 mt-2">Senior Product Manager</h1>
      <div className="t-ui text-muted mt-2">Anthropic · San Francisco, CA</div>
    </div>
    <RadarChart />
    <div>
      <h3 className="t-h3 border-b pb-2 mb-4">Extracted Context</h3>
      <div className="jd-text-box">
        Seeking a leader to drive the development of next-generation LLM interfaces. You must have a{' '}
        <mark className="jd-req">proven track record of 0-to-1 product launches</mark> in the AI space. Requires deep cross-functional collaboration with research engineering to{' '}
        <mark className="jd-req">translate complex model capabilities into intuitive user experiences</mark>. Strong emphasis on{' '}
        <mark className="jd-req">data-driven decision making</mark> and establishing rigorous evaluation metrics.
      </div>
    </div>
  </section>
);

const RightPanel = ({ onCommit, onReject }) => (
  <section className="panel right-page" style={{ position: 'relative', backgroundColor: 'var(--bg-paper)' }}>
    <div className="folio right">Fig. 2 — Provenance Engine</div>
    <div className="header-block mt-8">
      <div className="meta-tag" style={{ borderColor: 'var(--bg-terra)', color: 'var(--bg-terra)' }}>Synthesis Mode</div>
      <h2 className="t-h2 mt-2">Resume Customization</h2>
      <div className="t-ui text-muted mt-2">Strict mapping: Vault data → Output format. No generated facts.</div>
    </div>
    <div className="engine-container mt-4">
      <div className="workflow-step source-vault">
        <div className="workflow-header">
          <span className="t-micro">Source: Master Vault ID #092</span>
          <span className="t-micro">Role: Product Lead @ Vertex</span>
        </div>
        <div className="workflow-body">
          Led team of 8 engineers to launch "<mark className="source-hl">DataFlow AI</mark>" from concept to release in 6 months. Increased user retention by{' '}
          <mark className="source-hl">24%</mark> by creating a{' '}
          <mark className="source-hl">simplified dashboard for complex data pipelines</mark>. Set up Mixpanel tracking.
        </div>
      </div>
      <div className="connection-arrow">
        <ArrowDownIcon />
      </div>
      <div className="workflow-step output-resume">
        <div className="workflow-header">
          <span className="t-micro" style={{ color: 'var(--bg-terra)' }}>Target: Resume Bullet point</span>
          <span className="t-micro">Match: 92%</span>
        </div>
        <div className="workflow-body" style={{ fontSize: '1.25rem' }}>
          Spearheaded <mark className="output-hl">0-to-1 product launch</mark> for DataFlow AI, translating{' '}
          <mark className="output-hl">complex data pipelines into intuitive dashboards</mark>, resulting in a{' '}
          <mark className="output-hl">data-driven</mark> 24% increase in user retention.
        </div>
      </div>
      <div className="strict-rule">
        <ShieldCheckIcon />
        <span>Verification: All metrics and entities traced directly to Vault source. Tone mapped to JD requirements. Zero hallucinations detected.</span>
      </div>
      <div style={{ marginTop: 'auto', display: 'flex', gap: '1rem' }}>
        <button className="btn" onClick={onReject}>Reject</button>
        <button className="btn btn-primary" style={{ flex: 1 }} onClick={onCommit}>Commit to Resume</button>
      </div>
    </div>
  </section>
);

const Sidebar = ({ activeKanban, setActiveKanban }) => {
  const kanbanItems = [
    { id: 'anthropic', title: 'Senior Product Manager', company: 'Anthropic', status: 'Tailoring Resume', isTerra: true },
    { id: 'stripe', title: 'Lead PM, Machine Learning', company: 'Stripe', status: 'Applied', icon: <ClockIcon /> },
    { id: 'vercel', title: 'Group Product Manager', company: 'Vercel', status: 'Interview Prep', icon: <CalendarIcon /> },
  ];

  return (
    <aside className="prov-aside">
      <span className="t-micro">Active Pipeline (Kanban)</span>
      {kanbanItems.map(item => (
        <div
          key={item.id}
          className={`kanban-item ${activeKanban === item.id ? 'active' : ''}`}
          onClick={() => setActiveKanban(item.id)}
        >
          <div className="k-title">{item.title}</div>
          <div className="k-company">{item.company}</div>
          {item.isTerra ? (
            <div className="k-status" style={{ color: 'var(--bg-terra)', border: '1px solid var(--bg-terra)' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--bg-terra)' }}></div>
              {item.status}
            </div>
          ) : (
            <div className="k-status">
              {item.icon} {item.status}
            </div>
          )}
        </div>
      ))}
      <div className="vault-list">
        <span className="t-micro">Vault Index Quick-Access</span>
        {[
          { label: 'Vertex Product Launch', tag: 'Exp' },
          { label: 'Q3 Growth Metrics', tag: 'Data' },
          { label: 'Conflict Resolution (STAR)', tag: 'Prep' },
        ].map((item, i) => (
          <div className="vault-item" key={i}>
            <span>{item.label}</span>
            <span className="tag">{item.tag}</span>
          </div>
        ))}
        <button className="btn btn-dark mt-4 w-full">Open Master Vault</button>
      </div>
    </aside>
  );
};

const Toast = ({ message, onDone }) => {
  useEffect(() => {
    const t = setTimeout(onDone, 2500);
    return () => clearTimeout(t);
  }, [onDone]);
  return <div className="toast-overlay">{message}</div>;
};

const DocumentEditorPage = () => {
  const [activeKanban, setActiveKanban] = useState('anthropic');
  const [toast, setToast] = useState(null);

  const handleCommit = () => setToast('✓ Committed to Resume');
  const handleReject = () => setToast('✗ Bullet Rejected');

  return (
    <>
      <main className="prov-main">
        <LeftPanel />
        <RightPanel onCommit={handleCommit} onReject={handleReject} />
      </main>
      <Sidebar activeKanban={activeKanban} setActiveKanban={setActiveKanban} />
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </>
  );
};

const OverviewPage = () => {
  const [activeKanban, setActiveKanban] = useState('anthropic');
  return (
    <>
      <main className="prov-main" style={{ display: 'flex', flexDirection: 'column' }}>
        <section className="panel" style={{ flex: 1, gridColumn: '1 / -1' }}>
          <div style={{ position: 'absolute', top: '1rem', left: '1.5rem' }} className="folio left">Fig. 0 — Overview</div>
          <div className="header-block mt-8">
            <div className="meta-tag">Dashboard</div>
            <h2 className="t-h2 mt-2">Career Overview</h2>
            <div className="t-ui text-muted mt-2">Your pipeline at a glance.</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', marginTop: '1rem' }}>
            {[
              { label: 'Active Applications', value: '3', sub: 'In pipeline' },
              { label: 'Documents Tailored', value: '7', sub: 'This week' },
              { label: 'Match Score Avg', value: '88%', sub: 'Vault alignment' },
            ].map((stat, i) => (
              <div key={i} style={{ border: '1px solid var(--border-subtle)', padding: '1.5rem' }}>
                <div className="t-micro mb-2">{stat.label}</div>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', fontWeight: 400, lineHeight: 1 }}>{stat.value}</div>
                <div className="t-micro mt-2">{stat.sub}</div>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Sidebar activeKanban={activeKanban} setActiveKanban={setActiveKanban} />
    </>
  );
};

const CareerVaultPage = () => {
  const [activeKanban, setActiveKanban] = useState('anthropic');
  const vaultEntries = [
    { id: '#092', role: 'Product Lead @ Vertex', summary: 'Led team of 8 engineers. Launched DataFlow AI. +24% retention.', tag: 'Exp' },
    { id: '#091', role: 'PM @ EarlyStartup', summary: 'Built 0-to-1 analytics product. Defined roadmap. 50k MAU.', tag: 'Exp' },
    { id: '#090', role: 'Q3 Growth Metrics', summary: 'Retention up 24%. NPS 72. Revenue +18% QoQ.', tag: 'Data' },
    { id: '#089', role: 'Conflict Resolution (STAR)', summary: 'Led cross-team alignment on roadmap conflict. Resolved in 2 sprints.', tag: 'Prep' },
  ];
  return (
    <>
      <main className="prov-main" style={{ display: 'flex', flexDirection: 'column' }}>
        <section className="panel" style={{ flex: 1, gridColumn: '1 / -1' }}>
          <div style={{ position: 'absolute', top: '1rem', left: '1.5rem' }} className="folio left">Fig. 3 — Career Vault</div>
          <div className="header-block mt-8">
            <div className="meta-tag">Master Vault</div>
            <h2 className="t-h2 mt-2">Career Vault</h2>
            <div className="t-ui text-muted mt-2">All verified experiences, metrics, and stories.</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
            {vaultEntries.map(entry => (
              <div key={entry.id} className="workflow-step source-vault">
                <div className="workflow-header">
                  <span className="t-micro">Vault {entry.id}</span>
                  <span className="t-micro">{entry.role}</span>
                </div>
                <div className="workflow-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{entry.summary}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--bg-sage)', marginLeft: '1rem', flexShrink: 0 }}>{entry.tag}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Sidebar activeKanban={activeKanban} setActiveKanban={setActiveKanban} />
    </>
  );
};

const InterviewPrepPage = () => {
  const [activeKanban, setActiveKanban] = useState('vercel');
  const [activeQ, setActiveQ] = useState(null);
  const questions = [
    { q: 'Tell me about a 0-to-1 product you launched.', ans: 'Use Vault #092 — DataFlow AI launch story. Emphasize 6-month timeline, team leadership, and 24% retention outcome.' },
    { q: 'How do you make data-driven decisions?', ans: 'Reference Q3 Growth Metrics (Vault #090). Discuss Mixpanel setup, defining success metrics upfront, and iterating based on NPS data.' },
    { q: 'Describe a conflict you resolved.', ans: 'Use STAR story from Vault #089. Roadmap conflict resolved through structured cross-team alignment sessions.' },
  ];
  return (
    <>
      <main className="prov-main" style={{ display: 'flex', flexDirection: 'column' }}>
        <section className="panel" style={{ flex: 1, gridColumn: '1 / -1' }}>
          <div style={{ position: 'absolute', top: '1rem', left: '1.5rem' }} className="folio left">Fig. 4 — Interview Prep</div>
          <div className="header-block mt-8">
            <div className="meta-tag">Interview Prep</div>
            <h2 className="t-h2 mt-2">Practice Questions</h2>
            <div className="t-ui text-muted mt-2">Vault-backed answers for Vercel · Group Product Manager.</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
            {questions.map((item, i) => (
              <div key={i} className="workflow-step" style={{ cursor: 'pointer' }} onClick={() => setActiveQ(activeQ === i ? null : i)}>
                <div className="workflow-header" style={{ cursor: 'pointer' }}>
                  <span className="t-micro">Q{i + 1}</span>
                  <span className="t-micro">{activeQ === i ? '▲ Hide' : '▼ Show Answer'}</span>
                </div>
                <div className="workflow-body">
                  <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 500, marginBottom: activeQ === i ? '1rem' : 0 }}>{item.q}</div>
                  {activeQ === i && (
                    <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', color: 'var(--text-muted)', borderTop: '1px dashed var(--border-subtle)', paddingTop: '0.75rem' }}>
                      {item.ans}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Sidebar activeKanban={activeKanban} setActiveKanban={setActiveKanban} />
    </>
  );
};

const App = () => {
  const [activeNav, setActiveNav] = useState('editor');

  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = customStyles;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  const renderPage = () => {
    switch (activeNav) {
      case 'overview': return <OverviewPage />;
      case 'editor': return <DocumentEditorPage />;
      case 'vault': return <CareerVaultPage />;
      case 'interview': return <InterviewPrepPage />;
      default: return <DocumentEditorPage />;
    }
  };

  return (
    <div className="provenance-app">
      <div className="app-container">
        <Navigation activeNav={activeNav} setActiveNav={setActiveNav} />
        {renderPage()}
      </div>
    </div>
  );
};

export default App;