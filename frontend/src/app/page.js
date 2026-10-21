'use client';

import { useState, useEffect } from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import DashboardContent from '@/components/DashboardContent';
import { listCases } from '@/lib/api';

function AppShell() {
  const [activePage, setActivePage] = useState('dashboard');
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [commandInput, setCommandInput] = useState('');

  // Fetch cases on mount
  useEffect(() => {
    const defaultCase = {
      case_id: 'case-2024-001',
      case_number: 'CASE-2024-001',
      title: 'Apex Financial Fraud & Beneficial Ownership Audit',
      description: 'Cross-document forensic investigation and contradiction audit across corporate filings, wire transfers, and offshore bank accounts.',
      status: 'active',
    };

    listCases()
      .then((data) => {
        const caseList = Array.isArray(data) ? data : data?.cases || [];
        if (caseList.length > 0) {
          setCases(caseList);
          setActiveCase(caseList[0]);
        } else {
          setCases([defaultCase]);
          setActiveCase(defaultCase);
        }
      })
      .catch(() => {
        setCases([defaultCase]);
        setActiveCase(defaultCase);
      });
  }, []);

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <Header caseData={activeCase} />

      <main className="app-main" style={{ paddingBottom: 80 }}>
        {activePage === 'dashboard' && (
          <DashboardContent caseData={activeCase} />
        )}
        {activePage === 'cases' && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            <h2 style={{ color: 'var(--text-primary)', marginBottom: 12 }}>Cases</h2>
            <p>Case management screen — coming next</p>
            {cases.length > 0 && (
              <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 400, margin: '20px auto' }}>
                {cases.map((c, i) => (
                  <div key={c.case_id || i}
                    onClick={() => { setActiveCase(c); setActivePage('dashboard'); }}
                    style={{
                      padding: '12px 16px', background: 'var(--bg-card)',
                      border: `1px solid ${activeCase?.case_id === c.case_id ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                      borderRadius: 'var(--border-radius)', cursor: 'pointer',
                      textAlign: 'left',
                    }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13 }}>{c.case_number}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.title}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {['graph', 'documents', 'reports', 'settings'].includes(activePage) && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            <h2 style={{ color: 'var(--text-primary)', marginBottom: 12, textTransform: 'capitalize' }}>{activePage}</h2>
            <p>{activePage} screen — coming next</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <ThemeProvider>
      <AppShell />
    </ThemeProvider>
  );
}
