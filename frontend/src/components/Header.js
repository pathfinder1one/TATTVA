'use client';

import { useState, useEffect } from 'react';
import { checkReady } from '@/lib/api';

export default function Header({ caseData }) {
  const [backendReady, setBackendReady] = useState(null);

  useEffect(() => {
    checkReady()
      .then(() => setBackendReady(true))
      .catch(() => setBackendReady(false));
  }, []);

  const c = caseData;

  return (
    <header className="app-header">
      {/* Case Classification Info */}
      <div className="header-left">
        <span className="header-case-badge">
          {c?.case_number || 'CASE-2024-001'}
        </span>
        <div className="header-case-title">
          {c?.title || 'Apex Financial Fraud & Beneficial Ownership Audit'}
        </div>
      </div>

      {/* Cockpit Status & Telemetry */}
      <div className="header-right">
        {/* Multi-Agent Pipeline Status Track */}
        <div className="header-pipeline-track">
          <div className="pipeline-step active">
            <span className="pipeline-step-dot" />
            <span>INGESTION</span>
          </div>
          <div className="pipeline-step active">
            <span className="pipeline-step-dot" />
            <span>NEURAL RAG</span>
          </div>
          <div className="pipeline-step active">
            <span className="pipeline-step-dot" />
            <span>SYNTHESIS</span>
          </div>
          <div className="pipeline-step">
            <span className="pipeline-step-dot" />
            <span>DOSSIER</span>
          </div>
        </div>

        {/* J.A.R.V.I.S. / TATTVA System Status Indicator */}
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
    </header>
  );
}
