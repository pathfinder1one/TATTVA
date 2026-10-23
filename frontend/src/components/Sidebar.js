'use client';

import { useTheme } from './ThemeProvider';
import { THEMES } from '@/lib/themes';
import {
  IconCrosshair,
  IconGraph,
  IconReport,
  IconArcReactor,
  IconMic,
  IconPlanning,
  IconRAG,
} from './StarkIcons';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'TATTVA AI Core', icon: IconArcReactor },
  { id: 'graph', label: 'Criminal Network Graph', icon: IconGraph },
  { id: 'analytics', label: 'Tactical Threat Matrix', icon: IconCrosshair },
  { id: 'documents', label: 'Evidence Intelligence', icon: IconRAG },
  { id: 'cases', label: 'Case Dossiers', icon: IconPlanning },
  { id: 'reports', label: 'Court Intelligence Briefs', icon: IconReport },
];

const THEME_SWATCHES = [
  { key: 'tattva', color: '#00f0ff', label: 'ARC CYAN' },
  { key: 'sentinel', color: '#38bdf8', label: 'ICE BLUE' },
  { key: 'overwatch', color: '#f59e0b', label: 'POLICE GOLD' },
  { key: 'stealth', color: '#10b981', label: 'STEALTH EMERALD' },
];

export default function Sidebar({ activePage, onNavigate }) {
  const { themeKey, switchTheme } = useTheme();

  return (
    <aside className="app-sidebar">
      {/* MHA NCRB / TATTVA Emblem */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <IconArcReactor size={20} color="#00f0ff" />
        </div>
        <div className="sidebar-brand-text">
          <div className="sidebar-brand-name">TATTVA FORENSIC</div>
          <div className="sidebar-brand-tagline">MHA · NCRB INTELLIGENCE OS</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Investigation Directory</div>
        {NAV_ITEMS.map((item) => {
          const IconComp = item.icon;
          const isActive = activePage === item.id;
          return (
            <a
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                onNavigate?.(item.id);
              }}
              href="#"
            >
              <span className="nav-icon-box">
                <IconComp size={15} color={isActive ? '#0ea5e9' : 'currentColor'} />
              </span>
              <span>{item.label}</span>
            </a>
          );
        })}

        {/* Arc Reactor Voice Trigger */}
        <div
          className="sidebar-voice-link"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('tattva-trigger-voice'));
            }
          }}
          title="Click to initialize TATTVA Core Vocal Link"
        >
          <div className="sidebar-voice-top">
            <div className="sidebar-voice-reactor">
              <IconMic size={15} color="#0ea5e9" />
            </div>
            <div>
              <div className="sidebar-voice-title">Vocal Assistant // Active</div>
              <div className="sidebar-voice-sub">Touch Core or Tap Here</div>
            </div>
          </div>
        </div>
      </nav>

      {/* Telemetry Theme Selector */}
      <div className="theme-switcher-bar">
        {THEME_SWATCHES.map((sw) => (
          <button
            key={sw.key}
            className={`theme-pill ${themeKey === sw.key ? 'active' : ''}`}
            style={{ background: sw.color, color: sw.color }}
            onClick={() => switchTheme(sw.key)}
            title={sw.label}
          />
        ))}
      </div>
    </aside>
  );
}
