import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import api from "../services/api";

// ── Icons (inline SVG helpers) ────────────────────────────────────────────────
const Icon = ({ d, size = 16, color = "currentColor", ...rest }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" {...rest}>
    <path d={d} />
  </svg>
);
const MicIcon = ({ size = 16, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="2" width="6" height="12" rx="3" />
    <path d="M5 10a7 7 0 0 0 14 0" />
    <line x1="12" y1="19" x2="12" y2="22" />
    <line x1="8" y1="22" x2="16" y2="22" />
  </svg>
);
const StopIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <rect x="4" y="4" width="16" height="16" rx="2" />
  </svg>
);
const FileIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);
const PulseIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="#2563eb" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);
const UserIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);
const InfoCircleIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
const RefreshIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
  </svg>
);
const ShieldIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const ClockIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);
const CheckCircleIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);
const LogoutIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);
const GridIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);
const PenIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="2" x2="22" y2="6" />
    <path d="M7.5 20.5 19 9l-4-4L3.5 16.5 2 22z" />
  </svg>
);
const LanguageIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 8 6 6" /><path d="m4 14 6-6 2-3" />
    <path d="M2 5h12" /><path d="M7 2h1" />
    <path d="m22 22-5-10-5 10" /><path d="M14 18h6" />
  </svg>
);

// ── Styles ────────────────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

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
    --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow: 0 4px 12px rgba(0,0,0,.08);
    --shadow-lg: 0 8px 30px rgba(0,0,0,.12);
    --radius: 10px;
    --radius-sm: 6px;
    --radius-lg: 14px;
    --font: 'DM Sans', sans-serif;
    --mono: 'JetBrains Mono', monospace;
    --nav-h: 60px;
    --sidebar-w: 280px;
  }

  body { font-family: var(--font); background: var(--bg); color: var(--text-primary); }

  /* ── Layout ── */
  .app { display: flex; flex-direction: column; min-height: 100vh; }

  /* ── Navbar ── */
  .navbar {
    height: var(--nav-h);
    background: var(--navy);
    display: flex; align-items: center;
    padding: 0 20px;
    gap: 8px;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,.25);
  }
  .nav-brand {
    display: flex; align-items: center; gap: 8px;
    font-weight: 700; font-size: 17px; color: #fff; letter-spacing: -.3px;
    margin-right: 16px;
  }
  .nav-brand .pulse-icon { background: var(--blue); border-radius: 8px; padding: 3px; }
  .nav-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: var(--radius-sm);
    font-size: 13px; font-weight: 500; cursor: pointer;
    background: transparent; border: none; color: rgba(255,255,255,.7);
    font-family: var(--font); transition: all .15s;
  }
  .nav-btn:hover, .nav-btn.active { background: rgba(255,255,255,.1); color: #fff; }
  .nav-spacer { flex: 1; }
  .nav-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #60a5fa, #818cf8);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #fff;
    border: 2px solid rgba(255,255,255,.2);
    position: relative;
  }
  .nav-avatar .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #4ade80;
    border: 2px solid var(--navy);
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

  /* ── Body Layout ── */
  .body { display: flex; flex: 1; }

  /* ── Sidebar ── */
  .sidebar {
    width: var(--sidebar-w); min-height: calc(100vh - var(--nav-h));
    background: var(--surface); border-right: 1px solid var(--border);
    padding: 20px 16px;
    display: flex; flex-direction: column; gap: 16px;
    position: sticky; top: var(--nav-h); height: calc(100vh - var(--nav-h));
    overflow-y: auto;
  }
  .sidebar-section-title {
    font-size: 10.5px; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; color: var(--text-muted);
    display: flex; align-items: center; gap: 6px; margin-bottom: 10px;
  }
  .label { font-size: 11px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }
  .input-row { display: flex; gap: 8px; }
  .input {
    flex: 1; padding: 8px 12px; border: 1.5px solid var(--border);
    border-radius: var(--radius-sm); font-family: var(--mono);
    font-size: 12px; color: var(--text-primary); background: var(--surface2);
    outline: none; transition: border-color .15s;
  }
  .input:focus { border-color: var(--blue); }
  .input::placeholder { color: var(--text-muted); }
  .btn-load {
    padding: 8px 14px; background: var(--surface); border: 1.5px solid var(--border);
    border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
    color: var(--text-primary); cursor: pointer; font-family: var(--font);
    transition: all .15s; white-space: nowrap;
  }
  .btn-load:hover { border-color: var(--blue); color: var(--blue); }

  .patient-empty {
    display: flex; flex-direction: column; align-items: center;
    padding: 24px 16px; color: var(--text-muted); gap: 8px;
    border: 1.5px dashed var(--border); border-radius: var(--radius);
    margin-top: 8px;
  }
  .patient-empty span { font-size: 12px; }

  .patient-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px; margin-top: 8px;
  }
  .patient-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; border-bottom: 1px solid var(--border-light);
  }
  .patient-row:last-child { border-bottom: none; }
  .patient-row .key { font-size: 12px; color: var(--text-secondary); display: flex; align-items: center; gap: 5px; }
  .patient-row .val { font-size: 13px; font-weight: 600; color: var(--text-primary); }

  .consent-badge {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600; color: var(--green);
    background: var(--green-light); border: 1px solid #bbf7d0;
    border-radius: 20px; padding: 5px 10px; margin-top: 10px;
  }

  .compliance-box {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 12px;
  }
  .compliance-box p { font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-top: 6px; }

  .status-box {
    background: var(--blue-light); border: 1px solid var(--blue-mid);
    border-radius: var(--radius); padding: 12px;
    font-size: 12px;
  }
  .status-box-title { font-size: 11px; font-weight: 700; color: var(--blue);
    letter-spacing: .07em; text-transform: uppercase; margin-bottom: 8px; }
  .status-row { display: flex; justify-content: space-between; padding: 4px 0;
    border-bottom: 1px solid rgba(37,99,235,.1); }
  .status-row:last-child { border-bottom: none; }
  .status-key { color: var(--text-secondary); font-size: 12px; }
  .status-val { font-size: 12px; font-weight: 600; }
  .status-val.green { color: var(--green); }
  .status-val.blue { color: var(--blue); }
  .status-val.amber { color: var(--amber); }
  .status-text { color: var(--text-secondary); line-height: 1.5; }

  .history-box {
    background: var(--blue-light); border: 1px solid var(--blue-mid);
    border-radius: var(--radius); padding: 12px;
  }
  .history-box-title { font-size: 11px; font-weight: 700; color: var(--blue);
    letter-spacing: .07em; text-transform: uppercase; margin-bottom: 6px; }
  .history-box p { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }

  .sidebar-spacer { flex: 1; }

  .sys-status-bar {
    background: var(--blue-light); border: 1px solid var(--blue-mid);
    border-radius: var(--radius); padding: 12px;
    display: flex; gap: 10px; align-items: flex-start;
    font-size: 12px; color: var(--text-secondary); line-height: 1.5;
  }
  .sys-status-bar .info-icon { color: var(--blue); flex-shrink: 0; margin-top: 1px; }

  /* ── Main ── */
  .main {
    flex: 1; display: flex; flex-direction: column;
    min-height: calc(100vh - var(--nav-h));
  }
  .main-content { flex: 1; padding: 28px 32px; }

  .page-header { margin-bottom: 24px; }
  .page-title { font-size: 26px; font-weight: 700; letter-spacing: -.4px; margin-bottom: 4px; }
  .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  .recording-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--red-light); border: 1px solid #fecaca;
    border-radius: 20px; padding: 5px 12px;
    font-size: 12px; font-weight: 700; color: var(--red);
    letter-spacing: .06em; text-transform: uppercase;
  }
  .recording-pill .pulse-dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--red);
    animation: blink 1s infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }

  /* ── Grid Layouts ── */
  .grid-1 { display: grid; grid-template-columns: 1fr; gap: 20px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

  /* ── Cards ── */
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);
    overflow: hidden;
  }
  .card-header {
    padding: 16px 20px; border-bottom: 1px solid var(--border-light);
    display: flex; align-items: center; justify-content: space-between;
  }
  .card-header-left { display: flex; align-items: center; gap: 10px; }
  .card-title { font-size: 15px; font-weight: 700; }
  .card-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
  .card-body { padding: 20px; }

  /* ── Audio Control Card ── */
  .audio-ctrl-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 32px;
    text-align: center; box-shadow: var(--shadow-sm);
  }
  .audio-ctrl-title { font-size: 17px; font-weight: 700; margin-bottom: 6px; }
  .audio-ctrl-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; }

  /* ── Buttons ── */
  .btn-start {
    display: inline-flex; align-items: center; gap: 10px;
    background: var(--blue); color: #fff;
    padding: 14px 36px; border-radius: 40px;
    font-size: 15px; font-weight: 700; border: none; cursor: pointer;
    font-family: var(--font); transition: all .2s;
    box-shadow: 0 4px 14px rgba(37,99,235,.35);
  }
  .btn-start:hover { background: #1d4ed8; transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(37,99,235,.45); }
  .btn-stop {
    display: inline-flex; align-items: center; gap: 10px;
    background: var(--red); color: #fff;
    padding: 14px 36px; border-radius: 10px;
    font-size: 15px; font-weight: 700; border: none; cursor: pointer;
    font-family: var(--font); transition: all .2s; width: 100%;
    justify-content: center; box-shadow: 0 4px 14px rgba(220,38,38,.3);
  }
  .btn-stop:hover { background: #b91c1c; }
  .btn-primary {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--blue); color: #fff; padding: 9px 18px;
    border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
    border: none; cursor: pointer; font-family: var(--font); transition: all .15s;
  }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-secondary {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--surface); color: var(--text-primary);
    padding: 9px 18px; border-radius: var(--radius-sm);
    font-size: 13px; font-weight: 600; border: 1.5px solid var(--border);
    cursor: pointer; font-family: var(--font); transition: all .15s;
  }
  .btn-secondary:hover { border-color: var(--blue); color: var(--blue); }

  /* ── Recording Console ── */
  .timer-display {
    display: flex; align-items: center; justify-content: center;
    gap: 10px; margin-bottom: 20px;
  }
  .timer-digits {
    font-size: 48px; font-weight: 300; font-family: var(--mono);
    letter-spacing: 2px; color: var(--text-primary);
  }
  .volume-status-row {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1px; background: var(--border); border-radius: var(--radius-sm);
    overflow: hidden; margin-top: 16px;
  }
  .vs-cell {
    background: var(--surface2); padding: 10px 14px;
  }
  .vs-label { font-size: 10px; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; }
  .vol-bars { display: flex; gap: 2px; align-items: flex-end; height: 18px; }
  .vol-bar {
    width: 5px; border-radius: 2px;
    background: var(--blue);
    animation: volAnim 0.6s ease-in-out infinite alternate;
  }
  .vol-bar:nth-child(1) { height: 8px; animation-delay: 0s; }
  .vol-bar:nth-child(2) { height: 14px; animation-delay: .1s; }
  .vol-bar:nth-child(3) { height: 18px; animation-delay: .2s; }
  .vol-bar:nth-child(4) { height: 12px; animation-delay: .3s; }
  .vol-bar:nth-child(5) { height: 16px; animation-delay: .4s; }
  @keyframes volAnim { to { height: 6px; opacity: .4; } }
  .status-mic { font-size: 13px; font-weight: 700; color: var(--green); }

  .sync-note {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 14px; border: 1px solid var(--border);
    border-radius: var(--radius-sm); margin-top: 12px;
    font-size: 12px; color: var(--text-secondary);
  }
  .sync-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--blue);
    animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.3);opacity:.6} }

  /* ── Transcript Panel ── */
  .transcript-empty {
    display: flex; flex-direction: column; align-items: center;
    padding: 48px 20px; gap: 12px; color: var(--text-muted); text-align: center;
  }
  .transcript-empty .icon-circle {
    width: 50px; height: 50px; border-radius: 50%;
    border: 1.5px solid var(--border); display: flex; align-items: center; justify-content: center;
  }
  .transcript-empty .empty-title { font-size: 15px; font-weight: 600; color: var(--text-secondary); }
  .transcript-empty .empty-sub { font-size: 13px; max-width: 260px; line-height: 1.5; }

  .listening-state {
    display: flex; flex-direction: column; align-items: center;
    padding: 36px 20px; gap: 12px; text-align: center;
  }
  .mic-ring {
    width: 70px; height: 70px; border-radius: 50%;
    background: var(--blue-light); border: 1.5px solid var(--blue-mid);
    display: flex; align-items: center; justify-content: center;
    animation: ringPulse 2s ease-in-out infinite;
  }
  @keyframes ringPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(37,99,235,.2); }
    50% { box-shadow: 0 0 0 12px rgba(37,99,235,0); }
  }
  .listening-title { font-size: 16px; font-weight: 700; }
  .listening-sub { font-size: 13px; color: var(--text-secondary); max-width: 280px; line-height: 1.5; }

  .transcript-text {
    padding: 16px 20px; font-size: 13.5px; line-height: 1.8;
    color: var(--text-primary); max-height: 340px; overflow-y: auto;
  }

  .reload-btn {
    display: flex; align-items: center; gap: 5px;
    background: none; border: none; cursor: pointer;
    font-size: 13px; color: var(--text-secondary); font-family: var(--font);
    padding: 4px 8px; border-radius: var(--radius-sm); transition: all .15s;
  }
  .reload-btn:hover { background: var(--surface2); color: var(--text-primary); }

  /* ── Processing State ── */
  .processing-center {
    display: flex; flex-direction: column; align-items: center;
    padding: 48px 20px; gap: 16px; text-align: center;
  }
  .spin-ring {
    width: 70px; height: 70px; position: relative;
  }
  .spin-ring svg { animation: spin 1.5s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin-inner-mic {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  }
  .progress-bar-wrap {
    width: 120px; height: 4px; background: var(--border); border-radius: 4px; overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%; background: var(--blue); border-radius: 4px;
    animation: progressFill 3s ease-in-out infinite;
  }
  @keyframes progressFill { 0%{width:0%} 60%{width:85%} 100%{width:95%} }

  /* ── AI Insights ── */
  .insights-section { padding: 16px 20px; display: flex; flex-direction: column; gap: 16px; }
  .insight-block-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }
  .insight-bullet {
    font-size: 12.5px; color: var(--text-secondary); line-height: 1.6;
    display: flex; align-items: flex-start; gap: 6px; margin-bottom: 4px;
  }
  .insight-bullet::before { content: "•"; color: var(--blue); flex-shrink: 0; margin-top: 1px; }
  .diagnosis-text { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
  .followup-item {
    display: flex; align-items: flex-start; gap: 10px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 10px 12px;
  }
  .followup-icon {
    width: 32px; height: 32px; border-radius: 50%;
    background: var(--blue-light); border: 1px solid var(--blue-mid);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .followup-title { font-size: 13px; font-weight: 600; }
  .followup-sub { font-size: 12px; color: var(--text-muted); }

  .divider { height: 1px; background: var(--border-light); margin: 4px 0; }

  /* ── Footer Bar ── */
  .footer-bar {
    height: 56px; background: var(--surface); border-top: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 28px;
    position: sticky; bottom: 0;
  }
  .footer-status {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: var(--text-secondary);
  }
  .footer-dot { width: 8px; height: 8px; border-radius: 50%; }
  .footer-dot.green { background: var(--green); }
  .footer-dot.blue { background: var(--blue); animation: pulse 2s infinite; }
  .footer-dot.amber { background: var(--amber); }
  .footer-actions { display: flex; align-items: center; gap: 10px; }

  /* ── Disclaimer ── */
  .disclaimer {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: var(--text-muted);
    padding: 8px 20px; border-top: 1px solid var(--border-light);
  }

  /* ── Made with footer ── */
  .made-with {
    background: var(--navy); color: rgba(255,255,255,.5);
    font-size: 12px; text-align: center; padding: 10px;
  }

  /* ── Tabs ── */
  .tabs { display: flex; gap: 2px; background: var(--surface2);
    border-bottom: 1px solid var(--border); padding: 0 16px; }
  .tab { padding: 10px 14px; font-size: 13px; font-weight: 500;
    color: var(--text-muted); cursor: pointer; border: none; background: none;
    border-bottom: 2px solid transparent; font-family: var(--font);
    transition: all .15s; }
  .tab.active { color: var(--blue); border-bottom-color: var(--blue); font-weight: 600; }
`;

// ── App State Enum ────────────────────────────────────────────────────────────
const STATES = { IDLE: "idle", READY: "ready", RECORDING: "recording", PROCESSING: "processing" };

// ── Main Component ────────────────────────────────────────────────────────────
export default function MediScriptDashboard() {
  const navigate = useNavigate();
  const [appState, setAppState] = useState(STATES.IDLE);
  const [patients, setPatients] = useState([]);
  const [patientId, setPatientId] = useState("");
  const [patient, setPatient] = useState(null);
  const [timer, setTimer] = useState(0);
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(false);
  const [patientsLoading, setPatientsLoading] = useState(true);
  const [consultationId, setConsultationId] = useState(null);
  const intervalRef = useRef(null);
  const { isRecording, audioBlob, startRecording: recordStart, stopRecording: recordStop, setAudioBlob } = useAudioRecorder();

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await api.get("/patients");
        setPatients(response.data || []);
      } catch (error) {
        console.error("Failed to fetch patients:", error);
        alert("Failed to load patients. Please check your connection.");
      } finally {
        setPatientsLoading(false);
      }
    };
    fetchPatients();
  }, []);

  const loadPatient = async () => {
    const selectedPatient = patients.find(p => p.id === parseInt(patientId));
    if (!selectedPatient) {
      alert("Patient not found. Please select from the list.");
      return;
    }

    try {
      setLoading(true);
      const consultationResponse = await api.post("/consultations", {
        patient_id: selectedPatient.id,
        doctor_id: 1,
      });

      if (consultationResponse.data && consultationResponse.data.id) {
        setConsultationId(consultationResponse.data.id);
        setPatient(selectedPatient);
        setAppState(STATES.READY);
      }
    } catch (error) {
      console.error("Failed to create consultation:", error);
      alert(`Failed to create consultation: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendAudioToBackend = async (audioData) => {
    if (!audioData || !consultationId) {
      console.warn("⚠️ Cannot send audio - Missing audioData or consultationId", {
        hasAudioData: !!audioData,
        consultationId
      });
      return;
    }

    setLoading(true);
    const audioSize = (audioData.size / 1024 / 1024).toFixed(2);

    console.log("🎤 AUDIO UPLOAD STARTED", {
      consultationId,
      audioFormat: audioData.type,
      audioSize: `${audioSize} MB`,
      timestamp: new Date().toLocaleTimeString()
    });

    try {
      const formData = new FormData();
      formData.append("audio", audioData, "recording.webm");

      const response = await api.post(
        `/transcription/transcribe/${consultationId}`,
        formData
      );

      console.log("✅ BACKEND RESPONSE RECEIVED", {
        status: response.status,
        hasTranscript: !!response.data.raw_transcript,
        transcriptLength: response.data.raw_transcript?.length || 0,
        hasStructured: !!response.data.structured,
        timestamp: new Date().toLocaleTimeString()
      });

      if (response.data.raw_transcript) {
        setTranscript(response.data);
      }
    } catch (error) {
      console.error("❌ TRANSCRIPTION ERROR", {
        errorMessage: error.message,
        statusCode: error.response?.status,
        detail: error.response?.data?.detail,
        timestamp: new Date().toLocaleTimeString()
      });
      alert(`Transcription failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setAudioBlob(null);
    }
  };

  const startRecording = async () => {
    setTimer(0);
    setAppState(STATES.RECORDING);
    intervalRef.current = setInterval(() => setTimer(t => t + 1), 1000);
    await recordStart();
  };

  const stopRecording = async () => {
    clearInterval(intervalRef.current);
    await recordStop();
    setAppState(STATES.PROCESSING);
  };

  useEffect(() => {
    if (audioBlob && appState === STATES.PROCESSING && consultationId && !loading) {
      sendAudioToBackend(audioBlob);
    }
  }, [audioBlob, appState, consultationId, loading]);

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const formatTime = (s) => {
    const m = Math.floor(s / 60).toString().padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  };

  const newSession = () => {
    clearInterval(intervalRef.current);
    setPatient(null);
    setPatientId("");
    setConsultationId(null);
    setTimer(0);
    setTranscript(null);
    setLoading(false);
    setAppState(STATES.IDLE);
  };

  return (
    <>
      <style>{css}</style>
      <div className="app">
        {/* ── NAVBAR ── */}
        <nav className="navbar">
          <div className="nav-brand">
            <span className="pulse-icon"><PulseIcon size={18} /></span>
            MediScript
          </div>
          <button className="nav-btn active"><GridIcon size={14} /> Dashboard</button>
          {/* <button className="nav-btn"><PenIcon size={14} /> Writing Pad</button> */}
          <div className="nav-spacer" />
          {/* Bell, New Session, and Submit removed */}
          <div className="nav-avatar">
            DR<div className="dot" />
          </div>
          <button className="nav-logout"><LogoutIcon size={15} /> Logout</button>
        </nav>

        <div className="body">
          {/* ── SIDEBAR ── */}
          <aside className="sidebar">
            {appState === STATES.IDLE && (
              <>
                <div>
                  <div className="sidebar-section-title"><UserIcon size={13} /> Patient Context</div>
                  <div className="label">Enter Patient ID</div>
                  <div className="input-row">
                    <input
                      className="input"
                      placeholder="e.g. 1, 2, 3"
                      value={patientId}
                      onChange={e => setPatientId(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && loadPatient()}
                    />
                    <button
                      className="btn-load"
                      onClick={loadPatient}
                      disabled={loading || !patientId.trim()}
                    >
                      {loading ? "Loading..." : "Load"}
                    </button>
                  </div>
                  <div className="patient-empty">
                    <UserIcon size={28} />
                    <span>No patient record loaded</span>
                  </div>
                </div>
                <div className="sidebar-spacer" />
                <div className="sys-status-bar">
                  <span className="info-icon"><InfoCircleIcon size={14} /></span>
                  <div>
                    <div style={{ fontWeight: 700, color: "#2563eb", marginBottom: 3 }}>SYSTEM STATUS</div>
                    AI Transcription Engine v4.2 is active. Audio quality is optimized for dual-speaker separation.
                  </div>
                </div>
              </>
            )}

            {(appState === STATES.READY || appState === STATES.RECORDING) && patient && (
              <>
                <div>
                  <div className="sidebar-section-title">
                    {appState === STATES.RECORDING ? "🔴 Active Patient" : <><UserIcon size={13} /> Patient Profile</>}
                    {appState === STATES.READY && (
                      <span style={{ marginLeft: "auto", fontSize: 11, background: "#dcfce7", color: "#16a34a",
                        padding: "2px 8px", borderRadius: 20, fontWeight: 700 }}>Active</span>
                    )}
                  </div>
                  <div className="patient-card">
                    <div className="patient-row">
                      <span className="key">Name</span>
                      <span className="val">{patient.name}</span>
                    </div>
                    <div className="patient-row">
                      <span className="key">Age / {appState === STATES.RECORDING ? "Gender" : "Sex"}</span>
                      <span className="val">{patient.age} / {patient.sex}</span>
                    </div>
                    <div className="patient-row">
                      <span className="key">Phone</span>
                      <span className="val">{patient.phone || "N/A"}</span>
                    </div>
                    <div className="patient-row">
                      <span className="key"><LanguageIcon size={12} /> Language</span>
                      <span className="val">{patient.preferred_language || "Not specified"}</span>
                    </div>
                  </div>
                </div>

                {appState === STATES.RECORDING ? (
                  <div>
                    <div className="sidebar-section-title"><ShieldIcon size={12} /> Compliance</div>
                    <div className="compliance-box">
                      <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 700, fontSize: 13 }}>
                        <CheckCircleIcon size={14} /> Consent Granted
                      </div>
                      <p>Patient has verbally and digitally consented to audio recording for medical transcription purposes.</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="sidebar-section-title">System Status</div>
                    <div className="status-box">
                      <div className="status-box-title">System Status</div>
                      <div className="status-row">
                        <span className="status-key">Microphone</span>
                        <span className="status-val green">Calibrated</span>
                      </div>
                      <div className="status-row">
                        <span className="status-key">Transcription Engine</span>
                        <span className="status-val green">Ready</span>
                      </div>
                      <div className="status-row">
                        <span className="status-key">Cloud Sync</span>
                        <span className="status-val blue">Encrypted</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {appState === STATES.PROCESSING && patient && (
              <div>
                <div className="sidebar-section-title"><UserIcon size={13} /> Patient Information</div>
                <div className="patient-card">
                  <div className="patient-row">
                    <span className="key">Name</span>
                    <span className="val">{patient.name}</span>
                  </div>
                  <div className="patient-row">
                    <span className="key">Age / Sex</span>
                    <span className="val">{patient.age} / {patient.sex}</span>
                  </div>
                  <div className="patient-row">
                    <span className="key">Phone</span>
                    <span className="val">{patient.phone || "N/A"}</span>
                  </div>
                  <div className="patient-row">
                    <span className="key">Language</span>
                    <span className="val">{patient.preferred_language || "Not specified"}</span>
                  </div>
                </div>
              </div>
            )}
          </aside>

          {/* ── MAIN CONTENT ── */}
          <main className="main">
            <div className="main-content">
              {/* Page Header */}
              <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h1 className="page-title">Consultation Dashboard</h1>
                  <p className="page-subtitle">
                    {appState === STATES.IDLE && "Manage your active session and review post-transcription data."}
                    {appState === STATES.READY && "Manage your active session and review post-transcription data."}
                    {appState === STATES.RECORDING && "Active Session: Physical Examination & Diagnosis"}
                    {appState === STATES.PROCESSING && "Session complete — AI is analyzing your recording."}
                  </p>
                </div>
                {appState === STATES.RECORDING && (
                  <div className="recording-pill">
                    <span className="pulse-dot" /> Recording...
                  </div>
                )}
              </div>

              {/* ── IDLE STATE ── */}
              {appState === STATES.IDLE && (
                <div className="grid-1">
                  <div className="audio-ctrl-card">
                    <h2 className="audio-ctrl-title">Consultation Audio Control</h2>
                    <p className="audio-ctrl-sub">Capture the patient interaction. High-fidelity audio will be processed for AI transcription after the session concludes.</p>
                    <button className="btn-start" onClick={() => alert("Please load a patient first!")}>
                      <MicIcon size={18} /> Start Recording
                    </button>
                  </div>
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <FileIcon size={16} />
                        <div>
                          <div className="card-title">Live Transcript</div>
                          <div className="card-sub">Post-recording AI generation</div>
                        </div>
                      </div>
                      <button className="reload-btn"><RefreshIcon size={13} /> Reload</button>
                    </div>
                    <div className="transcript-empty">
                      <div className="icon-circle">
                        <InfoCircleIcon size={20} />
                      </div>
                      <div className="empty-title">No transcription yet</div>
                      <div className="empty-sub">Begin a recording session. The AI will generate a detailed transcript once you stop the capture.</div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── READY STATE ── */}
              {appState === STATES.READY && (
                <div className="grid-2">
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <MicIcon size={15} />
                        <div className="card-title">Session Control</div>
                      </div>
                    </div>
                    <div className="card-body" style={{ textAlign: "center", padding: "40px 20px" }}>
                      <div style={{ width: 80, height: 80, borderRadius: "50%",
                        background: "#eff6ff", border: "1.5px solid #bfdbfe",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        margin: "0 auto 16px" }}>
                        <MicIcon size={32} color="#2563eb" />
                      </div>
                      <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>Ready to Start</div>
                      <div style={{ fontSize: 13, color: "#64748b", marginBottom: 24, lineHeight: 1.5 }}>
                        Press the button below to begin the post-recording AI session.
                      </div>
                      <button className="btn-start" onClick={startRecording}>
                        <MicIcon size={16} /> Start Recording
                      </button>
                    </div>
                  </div>
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <FileIcon size={16} />
                        <div className="card-title">Live Transcript</div>
                      </div>
                      <button className="reload-btn"><RefreshIcon size={13} /> Reload</button>
                    </div>
                    <div className="transcript-empty">
                      <div className="empty-sub" style={{ marginTop: 20, color: "#94a3b8" }}>
                        No transcript data available. Start recording to capture a consultation.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── RECORDING STATE ── */}
              {appState === STATES.RECORDING && (
                <div className="grid-2">
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <MicIcon size={15} color="#2563eb" />
                        <div className="card-title">Recording Console</div>
                      </div>
                    </div>
                    <div className="card-body">
                      <div className="timer-display">
                        <ClockIcon size={22} />
                        <span className="timer-digits">{formatTime(timer)}</span>
                      </div>
                      <button className="btn-stop" onClick={stopRecording}>
                        <StopIcon size={16} /> Stop Recording
                      </button>
                      <div className="volume-status-row">
                        <div className="vs-cell">
                          <div className="vs-label">Volume</div>
                          <div className="vol-bars">
                            {[1,2,3,4,5].map(i => <div key={i} className="vol-bar" />)}
                          </div>
                        </div>
                        <div className="vs-cell">
                          <div className="vs-label">Status</div>
                          <div className="status-mic">Mic Active</div>
                        </div>
                      </div>
                      <div className="sync-note">
                        <span className="sync-dot" />
                        Auto-Sync Enabled — Session data backups every 30s
                      </div>
                    </div>
                  </div>
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <FileIcon size={16} />
                        <div className="card-title">Live Transcript</div>
                      </div>
                      <button className="reload-btn"><RefreshIcon size={13} /> Reload</button>
                    </div>
                    <div className="listening-state">
                      <div className="mic-ring">
                        <MicIcon size={26} color="#2563eb" />
                      </div>
                      <div className="listening-title">Listening...</div>
                      <div className="listening-sub">Recording is in progress.</div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── PROCESSING STATE ── */}
              {appState === STATES.PROCESSING && (
                <div className="grid-3" style={{ alignItems: "start" }}>
                  <div style={{ gridColumn: "1 / 3", display: "flex", flexDirection: "column", gap: 16 }}>
                    <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div style={{ width: 40, height: 40, borderRadius: "50%", background: "#f0fdf4",
                          border: "1px solid #bbf7d0", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <MicIcon size={18} color="#16a34a" />
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 15 }}>Session Recording</div>
                          <div style={{ fontSize: 12, color: "#16a34a", display: "flex", alignItems: "center", gap: 4 }}>
                            <CheckCircleIcon size={12} /> Audio captured successfully ({formatTime(timer)})
                          </div>
                        </div>
                      </div>
                      <button className="btn-primary" onClick={newSession}>
                        <MicIcon size={14} /> Start New Recording
                      </button>
                    </div>
                    <div className="card">
                      <div className="card-header">
                        <div className="card-header-left">
                          <FileIcon size={16} />
                          <div className="card-title">Post-Session Transcription</div>
                        </div>
                      </div>
                      {transcript ? (
                        <div className="transcript-text">
                          <div style={{ marginBottom: 12 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "#0f172a" }}>
                              Raw Transcript
                            </div>
                            <p style={{ fontSize: 13, color: "#64748b", lineHeight: 1.6 }}>
                              {transcript.raw_transcript}
                            </p>
                          </div>
                          {transcript.structured && (
                            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
                              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "#0f172a" }}>
                                Structured Output
                              </div>
                              <pre style={{ fontSize: 12, background: "#f8fafc", padding: 12, borderRadius: 6, overflow: "auto", maxHeight: 300 }}>
                                {typeof transcript.structured === 'string'
                                  ? JSON.stringify(JSON.parse(transcript.structured), null, 2)
                                  : JSON.stringify(transcript.structured, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      ) : loading ? (
                        <div className="processing-center">
                          <div className="spin-ring">
                            <svg viewBox="0 0 70 70" width="70" height="70">
                              <circle cx="35" cy="35" r="30" fill="none" stroke="#bfdbfe" strokeWidth="4" />
                              <circle cx="35" cy="35" r="30" fill="none" stroke="#2563eb" strokeWidth="4"
                                strokeDasharray="80 110" strokeLinecap="round" />
                            </svg>
                            <div className="spin-inner-mic"><MicIcon size={22} color="#2563eb" /></div>
                          </div>
                          <div style={{ fontSize: 17, fontWeight: 700 }}>Transcription in progress...</div>
                          <div style={{ fontSize: 13, color: "#64748b", lineHeight: 1.6, maxWidth: 300 }}>
                            Our AI is transcribing and analyzing your medical recording.
                          </div>
                          <div className="progress-bar-wrap">
                            <div className="progress-bar-fill" />
                          </div>
                        </div>
                      ) : (
                        <div className="processing-center">
                          <div className="spin-ring">
                            <svg viewBox="0 0 70 70" width="70" height="70">
                              <circle cx="35" cy="35" r="30" fill="none" stroke="#bfdbfe" strokeWidth="4" />
                              <circle cx="35" cy="35" r="30" fill="none" stroke="#2563eb" strokeWidth="4"
                                strokeDasharray="80 110" strokeLinecap="round" />
                            </svg>
                            <div className="spin-inner-mic"><MicIcon size={22} color="#2563eb" /></div>
                          </div>
                          <div style={{ fontSize: 17, fontWeight: 700 }}>Transcription pending...</div>
                          <div style={{ fontSize: 13, color: "#64748b", lineHeight: 1.6, maxWidth: 300 }}>
                            Our AI is currently analyzing the medical context and speaker patterns from your recent session.
                          </div>
                          <div className="progress-bar-wrap">
                            <div className="progress-bar-fill" />
                          </div>
                        </div>
                      )}
                      <div className="disclaimer">
                        <InfoCircleIcon size={12} />
                        AI-generated transcripts may contain errors. Please review before finalizing.
                      </div>
                    </div>
                  </div>

                  {/* Right: AI Insights */}
                  <div className="card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <InfoCircleIcon size={15} />
                        <div className="card-title">AI Analysis Insights</div>
                      </div>
                    </div>
                    <div className="insights-section">
                      <div>
                        <div className="insight-block-title">Key Triggers Identified</div>
                        <div className="insight-bullet">Increased screen time (Occupational)</div>
                        <div className="insight-bullet">Inconsistent meal timing (Potential Hypoglycemia)</div>
                        <div className="insight-bullet">Light sensitivity (Symptomatic)</div>
                      </div>
                      <div className="divider" />
                      <div>
                        <div className="insight-block-title">Proposed Diagnosis</div>
                        <div className="diagnosis-text">
                          Episodic Migraine with Aura, potentially exacerbated by environmental stressors and nutritional gaps.
                        </div>
                      </div>
                      <div className="divider" />
                      <div>
                        <div className="insight-block-title">Recommended Follow-up</div>
                        <div className="followup-item">
                          <div className="followup-icon"><ClockIcon size={14} /></div>
                          <div>
                            <div className="followup-title">Re-evaluation in 14 days</div>
                            <div className="followup-sub">Monitor efficacy of increased dosage.</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ── FOOTER BAR ── */}
            <div className="footer-bar">
              <div className="footer-status">
                <span className={`footer-dot ${appState === STATES.RECORDING ? "blue" : appState === STATES.PROCESSING ? "amber" : "green"}`} />
                {appState === STATES.IDLE && "Ready for next patient session"}
                {appState === STATES.READY && "Ready for next patient session"}
                {appState === STATES.RECORDING && "Recording patient interaction..."}
                {appState === STATES.PROCESSING && "Analyzing audio session..."}
              </div>
              <div className="footer-actions">
                <button
                  className="btn-secondary"
                  onClick={() => {
                    if (!patient || !consultationId) {
                      alert("Please load a patient first before opening the Writing Pad.");
                      return;
                    }
                    localStorage.setItem("currentPatient", JSON.stringify(patient));
                    localStorage.setItem("currentConsultationId", consultationId.toString());
                    navigate("/prescription");
                  }}
                >
                  Open Writing Pad
                </button>
                {/* Submit button removed */}
              </div>
            </div>
          </main>
        </div>

        <div className="made-with">Made with ❤ MediScript</div>
      </div>
    </>
  );
}