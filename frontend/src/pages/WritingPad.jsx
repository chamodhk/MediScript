import { useState, useRef, useEffect } from "react";

// ── Inline SVG Icons ──────────────────────────────────────────────────────────
const PulseIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="#2563eb" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);
const GridIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
    <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
  </svg>
);
const PenIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="2" x2="22" y2="6"/>
    <path d="M7.5 20.5 19 9l-4-4L3.5 16.5 2 22z"/>
  </svg>
);
const PlusCircleIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/>
    <line x1="8" y1="12" x2="16" y2="12"/>
  </svg>
);
const BellIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
);
const LogoutIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);
const ChevronLeftIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
);
const ChevronDownIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"/>
  </svg>
);
const BoldIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
    <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
  </svg>
);
const ItalicIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="4" x2="10" y2="4"/>
    <line x1="14" y1="20" x2="5" y2="20"/>
    <line x1="15" y1="4" x2="9" y2="20"/>
  </svg>
);
const ListIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="8" y1="6" x2="21" y2="6"/>
    <line x1="8" y1="12" x2="21" y2="12"/>
    <line x1="8" y1="18" x2="21" y2="18"/>
    <line x1="3" y1="6" x2="3.01" y2="6"/>
    <line x1="3" y1="12" x2="3.01" y2="12"/>
    <line x1="3" y1="18" x2="3.01" y2="18"/>
  </svg>
);
const OrderedListIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="10" y1="6" x2="21" y2="6"/>
    <line x1="10" y1="12" x2="21" y2="12"/>
    <line x1="10" y1="18" x2="21" y2="18"/>
    <path d="M4 6h1v4"/>
    <path d="M4 10h2"/>
    <path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>
  </svg>
);
const HeadingIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 4v16M18 4v16M6 12h12"/>
  </svg>
);
const AlignLeftIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="17" y1="10" x2="3" y2="10"/>
    <line x1="21" y1="6" x2="3" y2="6"/>
    <line x1="21" y1="14" x2="3" y2="14"/>
    <line x1="13" y1="18" x2="3" y2="18"/>
  </svg>
);
const SearchIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);
const TrashIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
);
const FileTextIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
  </svg>
);
const DollarCircleIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v2m0 8v2M9 9a3 3 0 0 1 6 0c0 2-3 3-3 3m0 0v1"/>
  </svg>
);
const AlertCircleIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);
const ClockIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);
const AlertOctagonIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);
const LightningIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
);

// ── Styles ────────────────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Lora:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #f4f6f9;
    --surface: #ffffff;
    --surface2: #f8fafc;
    --border: #e2e8f0;
    --border-light: #f1f5f9;
    --text-primary: #0f172a;
    --text-secondary: #64748b;
    --text-muted: #94a3b8;
    --blue: #2563eb;
    --blue-light: #eff6ff;
    --blue-mid: #bfdbfe;
    --red: #dc2626;
    --red-light: #fef2f2;
    --green: #16a34a;
    --green-light: #f0fdf4;
    --amber: #d97706;
    --amber-light: #fffbeb;
    --navy: #1e2a3a;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.06);
    --shadow: 0 4px 12px rgba(0,0,0,.08);
    --radius: 10px;
    --radius-sm: 6px;
    --radius-lg: 14px;
    --font: 'DM Sans', sans-serif;
    --mono: 'JetBrains Mono', monospace;
    --editor-font: 'Lora', serif;
    --nav-h: 60px;
    --sidebar-w: 300px;
  }

  body { font-family: var(--font); background: var(--bg); color: var(--text-primary); }

  /* ── Navbar ── */
  .navbar {
    height: var(--nav-h); background: var(--navy);
    display: flex; align-items: center; padding: 0 20px; gap: 6px;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,.25);
  }
  .nav-brand {
    display: flex; align-items: center; gap: 8px;
    font-weight: 700; font-size: 17px; color: #fff; letter-spacing: -.3px;
    margin-right: 16px;
  }
  .nav-brand .pulse-wrap {
    background: var(--blue); border-radius: 8px; padding: 3px;
    display: flex; align-items: center; justify-content: center;
  }
  .nav-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: var(--radius-sm);
    font-size: 13px; font-weight: 500; cursor: pointer;
    background: transparent; border: none;
    color: rgba(255,255,255,.7); font-family: var(--font); transition: all .15s;
  }
  .nav-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
  .nav-btn.active { background: rgba(255,255,255,.12); color: #fff; }
  .nav-spacer { flex: 1; }
  .nav-new-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 16px; border-radius: 20px;
    border: 1.5px solid rgba(255,255,255,.3);
    background: transparent; color: #fff;
    font-size: 13px; font-weight: 600; cursor: pointer;
    font-family: var(--font); transition: all .2s;
  }
  .nav-new-btn:hover { background: var(--blue); border-color: var(--blue); }
  .nav-icon-btn {
    background: none; border: none; cursor: pointer;
    color: rgba(255,255,255,.7); padding: 6px; border-radius: 6px;
    transition: all .15s; display: flex;
  }
  .nav-icon-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
  .nav-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #60a5fa, #818cf8);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #fff;
    border: 2px solid rgba(255,255,255,.2); position: relative;
  }
  .nav-avatar .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #4ade80; border: 2px solid var(--navy);
    position: absolute; bottom: 0; right: 0;
  }
  .nav-logout {
    display: flex; align-items: center; gap: 5px;
    padding: 6px 12px; border-radius: var(--radius-sm);
    background: none; border: none; cursor: pointer;
    color: #f87171; font-family: var(--font);
    font-size: 13px; font-weight: 500; transition: all .15s;
  }
  .nav-logout:hover { background: rgba(248,113,113,.15); }

  /* ── Layout ── */
  .app-body { display: flex; min-height: calc(100vh - var(--nav-h)); }

  /* ── Sidebar ── */
  .sidebar {
    width: var(--sidebar-w); background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 20px 16px;
    display: flex; flex-direction: column; gap: 18px;
    position: sticky; top: var(--nav-h);
    height: calc(100vh - var(--nav-h)); overflow-y: auto;
  }

  /* Patient Card */
  .pat-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px;
  }
  .pat-title { font-size: 14px; font-weight: 700; }
  .active-badge {
    font-size: 11px; font-weight: 700; color: var(--green);
    background: var(--green-light); border: 1px solid #bbf7d0;
    padding: 2px 10px; border-radius: 20px;
  }
  .pat-field-label {
    font-size: 10px; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px;
  }
  .pat-field-val { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
  .pat-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
  .divider { height: 1px; background: var(--border); margin: 4px 0 10px; }

  /* Allergy */
  .allergy-header {
    display: flex; align-items: center; gap: 5px; margin-bottom: 8px;
    font-size: 11px; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; color: var(--red);
  }
  .allergy-tags { display: flex; gap: 6px; flex-wrap: wrap; }
  .allergy-tag {
    font-size: 11px; font-weight: 700; color: #fff;
    background: var(--red); padding: 3px 10px; border-radius: 20px;
  }

  /* Recent History */
  .section-title {
    display: flex; align-items: center; gap: 6px;
    font-size: 13px; font-weight: 700; margin-bottom: 10px;
  }
  .history-item {
    border: 1px solid var(--border); border-radius: var(--radius-sm);
    overflow: hidden; margin-bottom: 8px;
  }
  .history-item-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 12px; cursor: pointer; background: var(--surface2);
    font-size: 13px; font-weight: 500; transition: background .15s;
  }
  .history-item-header:hover { background: var(--blue-light); }
  .history-item-body {
    padding: 10px 12px; font-size: 12px; color: var(--text-secondary);
    line-height: 1.6; border-top: 1px solid var(--border);
  }

  /* Quick Phrases */
  .quick-phrase-header {
    display: flex; align-items: center; gap: 6px; margin-bottom: 10px;
    font-size: 13px; font-weight: 700; color: var(--blue);
  }
  .phrase-item {
    padding: 9px 12px; border: 1px solid var(--border);
    border-radius: var(--radius-sm); font-size: 12.5px;
    color: var(--text-secondary); cursor: pointer;
    background: var(--surface); transition: all .15s; margin-bottom: 6px;
  }
  .phrase-item:hover {
    background: var(--blue-light); border-color: var(--blue-mid);
    color: var(--blue);
  }

  /* ── Main ── */
  .main {
    flex: 1; display: flex; flex-direction: column;
    background: var(--bg);
  }
  .main-inner { flex: 1; padding: 24px 32px; max-width: 900px; width: 100%; }

  /* Back link */
  .back-link {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 13px; color: var(--blue); font-weight: 500;
    background: none; border: none; cursor: pointer;
    font-family: var(--font); padding: 0; margin-bottom: 10px;
    transition: opacity .15s;
  }
  .back-link:hover { opacity: .7; }

  /* Note Header */
  .note-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 20px;
  }
  .note-title { font-size: 26px; font-weight: 700; letter-spacing: -.4px; }
  .session-id { font-size: 12.5px; color: var(--text-muted); margin-top: 4px;
    font-family: var(--mono); }
  .note-actions { display: flex; gap: 10px; align-items: center; }

  .btn-discard {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 18px; border-radius: var(--radius-sm);
    border: 1.5px solid var(--border); background: var(--surface);
    font-size: 13px; font-weight: 600; cursor: pointer;
    font-family: var(--font); color: var(--text-primary); transition: all .15s;
  }
  .btn-discard:hover { border-color: var(--red); color: var(--red); }
  .btn-finalize {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 18px; border-radius: var(--radius-sm);
    background: var(--blue); color: #fff;
    font-size: 13px; font-weight: 600; cursor: pointer;
    font-family: var(--font); border: none; transition: all .2s;
    box-shadow: 0 4px 12px rgba(37,99,235,.3);
  }
  .btn-finalize:hover { background: #1d4ed8; }

  /* ── Editor Card ── */
  .editor-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);
    overflow: hidden; margin-bottom: 16px;
  }

  /* Toolbar */
  .toolbar {
    display: flex; align-items: center; gap: 4px;
    padding: 10px 16px; border-bottom: 1px solid var(--border);
    background: var(--surface2); flex-wrap: wrap;
  }
  .toolbar-btn {
    display: flex; align-items: center; justify-content: center;
    width: 32px; height: 32px; border-radius: var(--radius-sm);
    border: none; background: none; cursor: pointer;
    color: var(--text-secondary); transition: all .15s;
  }
  .toolbar-btn:hover { background: var(--border); color: var(--text-primary); }
  .toolbar-btn.active { background: var(--blue-light); color: var(--blue); }
  .toolbar-sep {
    width: 1px; height: 22px; background: var(--border); margin: 0 4px;
  }
  .toolbar-spacer { flex: 1; }
  .toolbar-search {
    display: flex; align-items: center; gap: 6px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 5px 10px;
  }
  .toolbar-search input {
    border: none; outline: none; font-size: 12.5px; font-family: var(--font);
    color: var(--text-primary); background: transparent; width: 100px;
  }
  .toolbar-search input::placeholder { color: var(--text-muted); }
  .autosave-label {
    font-size: 11.5px; color: var(--text-muted); white-space: nowrap; margin-left: 8px;
  }

  /* Editor Area */
  .editor-area {
    padding: 28px 32px; min-height: 380px;
    font-family: var(--editor-font); font-size: 14.5px; line-height: 1.85;
    color: var(--text-primary); outline: none;
    border: none; width: 100%; resize: none;
    background: var(--surface);
  }
  .editor-area:focus { outline: none; }

  /* Status Bar */
  .editor-status {
    display: flex; align-items: center; gap: 24px;
    padding: 10px 20px; border-top: 1px solid var(--border);
    background: var(--surface2); font-size: 11px;
    font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
    color: var(--text-muted);
  }
  .status-item { display: flex; align-items: center; gap: 5px; }
  .status-dot { width: 7px; height: 7px; border-radius: 50%; }
  .status-dot.green { background: var(--green); }
  .status-dot.blue { background: var(--blue); }
  .status-dot.amber { background: var(--amber); }

  /* ── Info Cards Row ── */
  .info-cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-bottom: 16px; }
  .info-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px;
    box-shadow: var(--shadow-sm);
  }
  .info-card-header {
    display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px;
  }
  .info-card-icon {
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .info-card-icon.blue { background: var(--blue-light); color: var(--blue); }
  .info-card-icon.green { background: var(--green-light); color: var(--green); }
  .info-card-icon.amber { background: var(--amber-light); color: var(--amber); }
  .info-card-title { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
  .info-card-body { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }

  /* ── Footer Bar ── */
  .footer-bar {
    height: 56px; background: var(--surface); border-top: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 28px; position: sticky; bottom: 0;
  }
  .footer-left {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: var(--text-secondary);
  }
  .footer-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); }
  .footer-actions { display: flex; gap: 10px; }
  .btn-secondary {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 18px; border-radius: var(--radius-sm);
    border: 1.5px solid var(--border); background: var(--surface);
    font-size: 13px; font-weight: 600; cursor: pointer;
    font-family: var(--font); color: var(--text-primary); transition: all .15s;
  }
  .btn-secondary:hover { border-color: var(--red); color: var(--red); }
  .btn-primary {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 18px; border-radius: var(--radius-sm);
    background: var(--blue); color: #fff;
    font-size: 13px; font-weight: 600; cursor: pointer;
    font-family: var(--font); border: none; transition: all .15s;
  }
  .btn-primary:hover { background: #1d4ed8; }

  /* Made with */
  .made-with {
    background: var(--navy); color: rgba(255,255,255,.5);
    font-size: 12px; text-align: center; padding: 10px;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
`;

// ── Default Editor Content ────────────────────────────────────────────────────
const DEFAULT_CONTENT = `CHIEF COMPLAINT:
Follow-up for hypertension and reported lower back pain.

HISTORY OF PRESENT ILLNESS:
Mr. Henderson is a 54-year-old male with a history of essential hypertension. He presents today complaining of localized lower back pain (4/10 intensity) that began 3 days ago after gardening. No radiation to lower extremities. No numbness or tingling.

PHYSICAL EXAMINATION:
- Vitals: BP 138/86, HR 72, Temp 98.6 F
- Musculoskeletal: Moderate tenderness over the L4-L5 paraspinal muscles. Range of motion limited in flexion.
- Neurological: Straight leg raise negative. Sensation intact.

ASSESSMENT & PLAN:
1. Lumbar Strain: Likely musculoskeletal. Advised rest and NSAIDs.
2. Hypertension: Stable on current regimen. Continue Lisinopril 20mg.`;

// ── Quick Phrases ─────────────────────────────────────────────────────────────
const QUICK_PHRASES = [
  "Vitals stable, within normal limits.",
  "Lungs clear to auscultation bilaterally.",
  "No acute distress noted.",
  "Follow up in 2-4 weeks.",
];

// ── History Items ─────────────────────────────────────────────────────────────
const HISTORY = [
  {
    date: "Oct 12", label: "Hypertension Follow-up",
    body: "Patient presented with BP 145/90. Adjusted Lisinopril to 20mg daily. Reported mild dizziness in mornings.",
  },
  {
    date: "Aug 05", label: "Annual Physical",
    body: "Routine annual exam. All labs within normal range. BMI 27.4. Discussed weight management and diet.",
  },
];

// ── Word Counter ──────────────────────────────────────────────────────────────
const countWords = (text) => text.trim().split(/\s+/).filter(Boolean).length;

// ── Component ─────────────────────────────────────────────────────────────────
export default function WritingPad({ onBack }) {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [searchVal, setSearchVal] = useState("");
  const [openHistory, setOpenHistory] = useState({ 0: true });
  const [boldActive, setBoldActive] = useState(false);
  const [italicActive, setItalicActive] = useState(false);
  const textareaRef = useRef(null);
  const [saveLabel, setSaveLabel] = useState("Draft Autosaved: 2m ago");

  // Auto-save simulation
  useEffect(() => {
    const t = setTimeout(() => setSaveLabel("Draft Autosaved: just now"), 3000);
    return () => clearTimeout(t);
  }, [content]);

  const insertPhrase = (phrase) => {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const newContent = content.slice(0, start) + "\n" + phrase + content.slice(end);
    setContent(newContent);
    setTimeout(() => {
      el.selectionStart = el.selectionEnd = start + phrase.length + 1;
      el.focus();
    }, 0);
    setSaveLabel("Draft Autosaved: just now");
  };

  const toggleHistory = (i) =>
    setOpenHistory(p => ({ ...p, [i]: !p[i] }));

  const wordCount = countWords(content);

  return (
    <>
      <style>{css}</style>
      <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>

        {/* ── NAVBAR ── */}
        <nav className="navbar">
          <div className="nav-brand">
            <span className="pulse-wrap"><PulseIcon size={18} /></span>
            MediScript
          </div>
          <button className="nav-btn" onClick={onBack}><GridIcon /> Dashboard</button>
          <button className="nav-btn active"><PenIcon /> Writing Pad</button>
          <div className="nav-spacer" />
          <button className="nav-new-btn"><PlusCircleIcon /> New Session</button>
          <button className="nav-icon-btn"><BellIcon size={18} /></button>
          <div className="nav-avatar">DR<div className="dot" /></div>
          <button className="nav-logout"><LogoutIcon /> Logout</button>
        </nav>

        <div className="app-body">
          {/* ── SIDEBAR ── */}
          <aside className="sidebar">
            {/* Patient Info */}
            <div>
              <div className="pat-header">
                <span className="pat-title">Patient Info</span>
                <span className="active-badge">Active</span>
              </div>
              <div className="pat-field-label">Full Name</div>
              <div className="pat-field-val">Robert J. Henderson</div>
              <div className="pat-row">
                <div>
                  <div className="pat-field-label">Age / Sex</div>
                  <div className="pat-field-val">54Y / Male</div>
                </div>
                <div>
                  <div className="pat-field-label">ID</div>
                  <div className="pat-field-val" style={{ fontFamily: "var(--mono)", fontSize: 12 }}>#RH-9920</div>
                </div>
              </div>
              <div className="divider" />
              <div className="allergy-header">
                <AlertOctagonIcon size={13} /> Critical Allergies
              </div>
              <div className="allergy-tags">
                <span className="allergy-tag">Penicillin</span>
                <span className="allergy-tag">Sulfa Drugs</span>
              </div>
            </div>

            {/* Recent History */}
            <div>
              <div className="section-title">
                <ClockIcon size={14} /> Recent History
              </div>
              {HISTORY.map((h, i) => (
                <div className="history-item" key={i}>
                  <div className="history-item-header" onClick={() => toggleHistory(i)}>
                    <span><span style={{ color: "var(--text-muted)", fontSize: 11 }}>{h.date}:</span> {h.label}</span>
                    <ChevronDownIcon size={14} />
                  </div>
                  {openHistory[i] && (
                    <div className="history-item-body">{h.body}</div>
                  )}
                </div>
              ))}
            </div>

            {/* Quick Phrases */}
            <div>
              <div className="quick-phrase-header">
                <LightningIcon size={14} /> Quick Phrases
              </div>
              {QUICK_PHRASES.map((p, i) => (
                <div className="phrase-item" key={i} onClick={() => insertPhrase(p)}>
                  {p}
                </div>
              ))}
            </div>
          </aside>

          {/* ── MAIN ── */}
          <main className="main">
            <div className="main-inner">
              {/* Back */}
              <button className="back-link" onClick={onBack}>
                <ChevronLeftIcon /> Back to Dashboard
              </button>

              {/* Note Header */}
              <div className="note-header">
                <div>
                  <h1 className="note-title">Clinical Consultation Note</h1>
                  <div className="session-id">Session ID: #SESS-2023-1102A</div>
                </div>
                <div className="note-actions">
                  <button className="btn-discard"><TrashIcon size={14} /> Discard</button>
                  <button className="btn-finalize"><FileTextIcon size={14} /> Finalize Note</button>
                </div>
              </div>

              {/* Editor Card */}
              <div className="editor-card">
                {/* Toolbar */}
                <div className="toolbar">
                  <button className={`toolbar-btn ${boldActive ? "active" : ""}`}
                    onClick={() => setBoldActive(v => !v)} title="Bold">
                    <BoldIcon />
                  </button>
                  <button className={`toolbar-btn ${italicActive ? "active" : ""}`}
                    onClick={() => setItalicActive(v => !v)} title="Italic">
                    <ItalicIcon />
                  </button>
                  <div className="toolbar-sep" />
                  <button className="toolbar-btn" title="Bullet List"><ListIcon /></button>
                  <button className="toolbar-btn" title="Ordered List"><OrderedListIcon /></button>
                  <div className="toolbar-sep" />
                  <button className="toolbar-btn" title="Heading"><HeadingIcon /></button>
                  <button className="toolbar-btn" title="Align Left"><AlignLeftIcon /></button>
                  <div className="toolbar-spacer" />
                  <div className="toolbar-search">
                    <SearchIcon size={13} />
                    <input placeholder="Find..."
                      value={searchVal} onChange={e => setSearchVal(e.target.value)} />
                  </div>
                  <span className="autosave-label">{saveLabel}</span>
                </div>

                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  className="editor-area"
                  value={content}
                  onChange={e => { setContent(e.target.value); setSaveLabel("Saving..."); }}
                  spellCheck={true}
                  style={{
                    fontWeight: boldActive ? 700 : 400,
                    fontStyle: italicActive ? "italic" : "normal",
                  }}
                />

                {/* Status Bar */}
                <div className="editor-status">
                  <div className="status-item">
                    <span className="status-dot green" />
                    Editor Integrity: High
                  </div>
                  <div className="status-item">
                    Word Count: {wordCount}
                  </div>
                  <div className="status-item">
                    Format: Structured SOAP Note
                  </div>
                </div>
              </div>

              {/* Info Cards */}
              <div className="info-cards">
                <div className="info-card">
                  <div className="info-card-header">
                    <div className="info-card-icon blue"><FileTextIcon size={16} /></div>
                    <div className="info-card-title">Documentation Guide</div>
                  </div>
                  <div className="info-card-body">
                    Ensure all subjective symptoms and objective findings are clearly separated per hospital protocol.
                  </div>
                </div>
                <div className="info-card">
                  <div className="info-card-header">
                    <div className="info-card-icon green"><DollarCircleIcon size={16} /></div>
                    <div className="info-card-title">Billing Compliance</div>
                  </div>
                  <div className="info-card-body">
                    Time spent in counseling: 15 minutes. Level 3 established patient visit criteria met.
                  </div>
                </div>
                <div className="info-card">
                  <div className="info-card-header">
                    <div className="info-card-icon amber"><AlertCircleIcon size={16} /></div>
                    <div className="info-card-title">Pending Actions</div>
                  </div>
                  <div className="info-card-body">
                    Lab orders for Metabolic Panel (CMP) need to be signed after exiting this screen.
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="footer-bar">
              <div className="footer-left">
                <span className="footer-dot" />
                Autosave enabled. All clinical data encrypted locally.
              </div>
              <div className="footer-actions">
                <button className="btn-secondary">Discard Changes</button>
                <button className="btn-primary">Save &amp; Exit</button>
              </div>
            </div>
          </main>
        </div>

        <div className="made-with">Made with ❤ MediScript</div>
      </div>
    </>
  );
}