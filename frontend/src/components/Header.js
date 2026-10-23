'use client';

import { useState, useEffect, useRef } from 'react';
import { checkReady, listCases, listDocuments, listAnalysisRuns } from '@/lib/api';
import NewCaseModal from './NewCaseModal';

export default function Header({ caseData, onCaseSelect }) {
  const [backendReady, setBackendReady] = useState(null);
  const [cases, setCases] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isNewCaseOpen, setIsNewCaseOpen] = useState(false);
  const [pipelineState, setPipelineState] = useState({
    ingestion: false,
    rag: false,
    synthesis: false,
    dossier: false,
  });
  const dropdownRef = useRef(null);

  useEffect(() => {
    checkReady()
      .then(() => setBackendReady(true))
      .catch(() => setBackendReady(false));

    listCases()
      .then((data) => {
        const list = Array.isArray(data) ? data : data?.cases || [];
        setCases(list);
      })
      .catch(() => {});
  }, []);

  // Dynamically update pipeline progress based on active case
  useEffect(() => {
    if (!caseData?.case_id) {
      setPipelineState({ ingestion: false, rag: false, synthesis: false, dossier: false });
      return;
    }

    Promise.all([
      listDocuments(caseData.case_id).catch(() => []),
      listAnalysisRuns(caseData.case_id).catch(() => []),
    ]).then(([docs, runs]) => {
      const docList = Array.isArray(docs) ? docs : [];
      const runList = Array.isArray(runs) ? runs : [];
      const hasDocs = docList.length > 0;
      const hasRuns = runList.length > 0;
      const hasCompleted = runList.some((r) => r.status === 'completed');

      setPipelineState({
        ingestion: hasDocs,
        rag: hasDocs && hasRuns,
        synthesis: hasRuns,
        dossier: hasCompleted,
      });
    });
  }, [caseData?.case_id]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const c = caseData;

  return (
    <header className="app-header">
      {/* Dynamic Case Classification & Selector Dropdown */}
      <div className="header-left" ref={dropdownRef} style={{ position: 'relative' }}>
        <div
          onClick={() => setIsDropdownOpen((prev) => !prev)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            cursor: 'pointer',
            padding: '4px 8px',
            borderRadius: '6px',
            transition: 'background 0.2s',
          }}
          title="Click to Switch Criminal Case Dossier"
        >
          <span className="header-case-badge" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {c?.case_number || 'SELECT CASE'}
            <span style={{ fontSize: 9, opacity: 0.8 }}>▼</span>
          </span>
          <div className="header-case-title" style={{ maxWidth: 380, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {c?.title || 'Criminal Network Analysis'}
          </div>
        </div>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              marginTop: 6,
              width: 440,
              background: 'rgba(3, 8, 26, 0.96)',
              border: '1px solid var(--border-stark-bright)',
              borderRadius: '8px',
              boxShadow: '0 15px 35px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 240, 255, 0.2)',
              backdropFilter: 'blur(16px)',
              zIndex: 9999,
              padding: '8px 0',
              maxHeight: 340,
              overflowY: 'auto',
            }}
          >
            <div
              style={{
                padding: '6px 14px',
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--arc-cyan)',
                borderBottom: '1px solid var(--border-subtle)',
                letterSpacing: 1,
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>MHA / NCRB ACTIVE CASE DOSSIERS ({cases.length})</span>
              <span>LIVE DATABASE</span>
            </div>

            {cases.length > 0 ? (
              cases.map((caseItem) => {
                const isActive = caseItem.case_id === c?.case_id;
                return (
                  <div
                    key={caseItem.case_id}
                    onClick={() => {
                      onCaseSelect?.(caseItem);
                      setIsDropdownOpen(false);
                    }}
                    style={{
                      padding: '10px 14px',
                      cursor: 'pointer',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      background: isActive ? 'rgba(0, 240, 255, 0.12)' : 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-stark)',
                          fontSize: 12,
                          fontWeight: 700,
                          color: isActive ? 'var(--arc-cyan)' : '#ffffff',
                          letterSpacing: 1,
                        }}
                      >
                        {caseItem.case_number}
                      </span>
                      {isActive && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#10b981', fontWeight: 700 }}>
                          ● ACTIVE DOSSIER
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        fontFamily: 'var(--font-stark)',
                        fontSize: 12,
                        color: 'var(--text-secondary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {caseItem.title}
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                No active cases found.
              </div>
            )}

            {/* Register New Case Action */}
            <div
              onClick={() => {
                setIsDropdownOpen(false);
                setIsNewCaseOpen(true);
              }}
              style={{
                padding: '10px 14px',
                cursor: 'pointer',
                background: 'rgba(0, 240, 255, 0.08)',
                borderTop: '1px solid var(--border-stark)',
                color: 'var(--arc-cyan)',
                fontFamily: 'var(--font-stark)',
                fontSize: 11,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                letterSpacing: 1,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(0, 240, 255, 0.16)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(0, 240, 255, 0.08)';
              }}
            >
              <span>+ REGISTER NEW CASE DOSSIER</span>
            </div>
          </div>
        )}
      </div>

      {/* Cockpit Status & Telemetry */}
      <div className="header-right">
        {/* Multi-Agent Pipeline Status Track */}
        <div className="header-pipeline-track">
          <div className={`pipeline-step ${pipelineState.ingestion ? 'active' : ''}`}>
            <span className="pipeline-step-dot" />
            <span>INGESTION</span>
          </div>
          <div className={`pipeline-step ${pipelineState.rag ? 'active' : ''}`}>
            <span className="pipeline-step-dot" />
            <span>NEURAL RAG</span>
          </div>
          <div className={`pipeline-step ${pipelineState.synthesis ? 'active' : ''}`}>
            <span className="pipeline-step-dot" />
            <span>SYNTHESIS</span>
          </div>
          <div className={`pipeline-step ${pipelineState.dossier ? 'active' : ''}`}>
            <span className="pipeline-step-dot" />
            <span>DOSSIER</span>
          </div>
        </div>

        {/* TATTVA System Status Indicator */}
        <div className="header-status-box">
          <div
            className="status-dot-pulse"
            style={{
              background: backendReady === false ? 'var(--status-threat)' : 'var(--status-verified)',
              boxShadow: `0 0 10px ${backendReady === false ? 'var(--status-threat)' : 'var(--status-verified)'}`,
            }}
          />
          <span className="status-box-text">
            {backendReady === true ? 'CORE ONLINE // 100%' : backendReady === false ? 'CORE LOCAL MODE' : 'CONNECTING...'}
          </span>
        </div>
      </div>

      {/* New Case Creation Modal */}
      <NewCaseModal
        isOpen={isNewCaseOpen}
        onClose={() => setIsNewCaseOpen(false)}
        onCaseCreated={(newCase) => {
          setCases((prev) => [newCase, ...prev]);
          onCaseSelect?.(newCase);
        }}
      />
    </header>
  );
}
