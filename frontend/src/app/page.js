'use client';

import { useState, useEffect } from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import DashboardContent from '@/components/DashboardContent';
import { listCases, listDocuments, listFindings, getDocumentCertificate } from '@/lib/api';

import CriminalNetworkGraph from '@/components/CriminalNetworkGraph';
import TacticalMatrixView from '@/components/TacticalMatrixView';
import EvidenceIntelligenceView from '@/components/EvidenceIntelligenceView';
import NewCaseModal from '@/components/NewCaseModal';

function AppShell() {
  const [activePage, setActivePage] = useState('dashboard');
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [isNewCaseOpen, setIsNewCaseOpen] = useState(false);
  const [commandInput, setCommandInput] = useState('');

  // Fetch cases on mount
  useEffect(() => {
    listCases()
      .then((data) => {
        const caseList = Array.isArray(data) ? data : data?.cases || [];
        if (caseList.length > 0) {
          setCases(caseList);
          const defaultCase = caseList.find(c => c.case_number === 'CASE-2024-023') || caseList[0];
          setActiveCase(defaultCase);
        } else {
          setCases([]);
          setActiveCase(null);
        }
      })
      .catch(() => {
        setCases([]);
        setActiveCase(null);
      });
  }, []);

  // Extra state for documents/reports sub-pages
  const [subPageDocs, setSubPageDocs] = useState([]);
  const [subPageFindings, setSubPageFindings] = useState([]);
  const [certModal, setCertModal] = useState(null);

  useEffect(() => {
    if (activeCase?.case_id) {
      listDocuments(activeCase.case_id).then(d => setSubPageDocs(Array.isArray(d) ? d : [])).catch(() => setSubPageDocs([]));
      listFindings(activeCase.case_id).then(f => setSubPageFindings(Array.isArray(f) ? f : [])).catch(() => setSubPageFindings([]));
    } else {
      setSubPageDocs([]);
      setSubPageFindings([]);
    }
  }, [activeCase?.case_id]);

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <Header caseData={activeCase} onCaseSelect={setActiveCase} />

      <main className="app-main" style={{ paddingBottom: 80 }}>
        {activePage === 'dashboard' && (
          <DashboardContent
            caseData={activeCase}
            onCaseSelect={setActiveCase}
            onNavigate={setActivePage}
          />
        )}

        {activePage === 'cases' && (
          <div style={{ padding: '28px 36px', maxWidth: 900, margin: '0 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <div>
                <h2 style={{ fontFamily: 'var(--font-stark)', fontSize: 20, color: 'var(--text-primary)', letterSpacing: 1 }}>
                  CRIMINAL CASE DOSSIER REGISTRY
                </h2>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  MHA & NCRB Intelligence Database // {cases.length} Registered Case Files
                </div>
              </div>
              <button
                onClick={() => setIsNewCaseOpen(true)}
                style={{
                  padding: '9px 18px',
                  background: 'var(--arc-cyan)',
                  border: 'none',
                  borderRadius: 6,
                  color: '#020617',
                  fontFamily: 'var(--font-stark)',
                  fontWeight: 700,
                  fontSize: 11,
                  cursor: 'pointer',
                  letterSpacing: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 0 16px rgba(0, 240, 255, 0.4)',
                }}
              >
                <span>+ REGISTER NEW CASE</span>
              </button>
            </div>

            {cases.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 16 }}>
                {cases.map((c) => {
                  const isSelected = activeCase?.case_id === c.case_id;
                  return (
                    <div
                      key={c.case_id}
                      onClick={() => setActiveCase(c)}
                      style={{
                        padding: '18px 20px',
                        background: 'rgba(4, 12, 34, 0.75)',
                        border: `1px solid ${isSelected ? 'var(--arc-cyan)' : 'var(--border-stark)'}`,
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: isSelected ? '0 0 16px rgba(0, 240, 255, 0.25)' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span style={{
                          fontFamily: 'var(--font-stark)',
                          fontWeight: 700,
                          fontSize: 12,
                          color: isSelected ? 'var(--arc-cyan)' : '#38bdf8',
                          letterSpacing: 1,
                        }}>
                          {c.case_number}
                        </span>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 10,
                          padding: '2px 8px',
                          borderRadius: '3px',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#10b981',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                        }}>
                          {c.status?.toUpperCase() || 'ACTIVE'}
                        </span>
                      </div>
                      <div style={{ fontFamily: 'var(--font-stark)', fontSize: 14, fontWeight: 700, color: '#ffffff', marginBottom: 6 }}>
                        {c.title}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, maxHeight: 42, overflow: 'hidden' }}>
                        {c.description}
                      </div>

                      <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        <button
                          onClick={(e) => { e.stopPropagation(); setActiveCase(c); setActivePage('dashboard'); }}
                          style={{
                            padding: '4px 10px',
                            background: 'rgba(0, 240, 255, 0.15)',
                            border: '1px solid var(--arc-cyan)',
                            color: 'var(--arc-cyan)',
                            borderRadius: 4,
                            fontSize: 10,
                            fontFamily: 'var(--font-stark)',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          TATTVA CORE ➔
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setActiveCase(c); setActivePage('graph'); }}
                          style={{
                            padding: '4px 10px',
                            background: 'rgba(168, 85, 247, 0.15)',
                            border: '1px solid #c084fc',
                            color: '#f3e8ff',
                            borderRadius: 4,
                            fontSize: 10,
                            fontFamily: 'var(--font-stark)',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          CRIMINAL GRAPH ➔
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setActiveCase(c); setActivePage('analytics'); }}
                          style={{
                            padding: '4px 10px',
                            background: 'rgba(244, 63, 94, 0.15)',
                            border: '1px solid #f43f5e',
                            color: '#ffe4e6',
                            borderRadius: 4,
                            fontSize: 10,
                            fontFamily: 'var(--font-stark)',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          TACTICAL MATRIX ➔
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setActiveCase(c); setActivePage('documents'); }}
                          style={{
                            padding: '4px 10px',
                            background: 'rgba(16, 185, 129, 0.15)',
                            border: '1px solid #10b981',
                            color: '#d1fae5',
                            borderRadius: 4,
                            fontSize: 10,
                            fontFamily: 'var(--font-stark)',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          EVIDENCE VAULT ➔
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                No registered cases found in the database.
              </div>
            )}
          </div>
        )}

        {activePage === 'graph' && (
          <div style={{ padding: '20px 24px' }}>
            <CriminalNetworkGraph
              caseData={activeCase}
              height={760}
              onBack={() => setActivePage('dashboard')}
              onOpenCert={(cert) => setCertModal(cert)}
            />
          </div>
        )}

        {activePage === 'analytics' && (
          <div style={{ padding: '20px 24px' }}>
            <TacticalMatrixView
              caseData={activeCase}
              onNavigate={setActivePage}
              onOpenCert={(cert) => setCertModal(cert)}
            />
          </div>
        )}

        {activePage === 'documents' && (
          <div style={{ padding: '20px 24px' }}>
            <EvidenceIntelligenceView
              caseData={activeCase}
              onOpenCert={(cert) => setCertModal(cert)}
            />
          </div>
        )}

        {activePage === 'reports' && (
          <div style={{ padding: '28px 36px', maxWidth: 900, margin: '0 auto' }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ fontFamily: 'var(--font-stark)', fontSize: 20, color: 'var(--text-primary)', letterSpacing: 1 }}>
                FORENSIC CONTRADICTION & INVESTIGATION DOSSIER
              </h2>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Active Case: <strong style={{ color: 'var(--arc-cyan)' }}>{activeCase?.case_number}</strong> — {activeCase?.title}
              </div>
            </div>

            {subPageFindings.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {subPageFindings.map((finding) => (
                  <div
                    key={finding.finding_id}
                    style={{
                      padding: '16px 20px',
                      background: 'rgba(244, 63, 94, 0.05)',
                      border: '1px solid rgba(244, 63, 94, 0.35)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#f43f5e', fontWeight: 700, letterSpacing: 1 }}>
                        FLAGGED CONTRADICTION // SEVERITY: {finding.severity?.toUpperCase() || 'HIGH'}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                        CONFIDENCE: {Math.round((finding.confidence_score || 0.95) * 100)}%
                      </span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-stark)', fontSize: 14, fontWeight: 700, color: '#ffffff', marginBottom: 6 }}>
                      {finding.statement}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {finding.details || 'Identified conflicting declarations across sworn statements and official registrar records.'}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: 50, textAlign: 'center', color: 'var(--text-muted)' }}>
                No evidential contradictions currently flagged for {activeCase?.case_number || 'this case'}. Deploy the multi-agent DAG pipeline from the Dashboard to run contradiction audits.
              </div>
            )}
          </div>
        )}

        {activePage === 'settings' && (
          <div style={{ padding: '28px 36px', maxWidth: 800, margin: '0 auto' }}>
            <h2 style={{ fontFamily: 'var(--font-stark)', fontSize: 20, color: 'var(--text-primary)', letterSpacing: 1, marginBottom: 16 }}>
              SYSTEM & LEGAL COMPLIANCE CONFIGURATION
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: '16px 20px', background: 'rgba(4, 12, 34, 0.75)', border: '1px solid var(--border-stark)', borderRadius: 6 }}>
                <div style={{ fontWeight: 700, color: 'var(--arc-cyan)', fontSize: 13, marginBottom: 4 }}>Section 63 BSA & 65B IT Act Admissibility Standard</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>All uploaded evidence is SHA-256 digested and court-certified under Indian Evidence Act Section 65B & Bharatiya Sakshya Adhiniyam 2023.</div>
              </div>
              <div style={{ padding: '16px 20px', background: 'rgba(4, 12, 34, 0.75)', border: '1px solid var(--border-stark)', borderRadius: 6 }}>
                <div style={{ fontWeight: 700, color: '#10b981', fontSize: 13, marginBottom: 4 }}>FastAPI Multi-Agent Orchestrator</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Connected to port 8002. Tasks partitioned across DAG workers for RAG, entity extraction, and centrality.</div>
              </div>
              <div style={{ padding: '16px 20px', background: 'rgba(4, 12, 34, 0.75)', border: '1px solid var(--border-stark)', borderRadius: 6 }}>
                <div style={{ fontWeight: 700, color: '#f59e0b', fontSize: 13, marginBottom: 4 }}>Qdrant Vector Cluster & MongoDB Storage</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Vector collection: tattva_case_chunks. Asynchronous motor driver with tenant-isolated database access.</div>
              </div>
            </div>
          </div>
        )}

        {/* Certificate Modal on Sub-pages */}
        {certModal && (
          <div
            onClick={() => setCertModal(null)}
            style={{
              position: 'fixed', inset: 0, zIndex: 9999,
              background: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(8px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                maxWidth: 620, width: '100%',
                background: '#030a1c', border: '1px solid var(--arc-cyan)',
                borderRadius: 8, padding: 24, boxShadow: '0 0 40px rgba(0, 240, 255, 0.35)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(0, 240, 255, 0.25)', paddingBottom: 12, marginBottom: 16 }}>
                <div style={{ fontFamily: 'var(--font-stark)', fontWeight: 700, color: 'var(--arc-cyan)', fontSize: 16 }}>
                  DIGITAL EVIDENCE COURT CERTIFICATE
                </div>
                <button onClick={() => setCertModal(null)} style={{ background: 'none', border: 'none', color: '#fff', fontSize: 16, cursor: 'pointer' }}>✕</button>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 14 }}>
                Pursuant to Section 63 of Bharatiya Sakshya Adhiniyam, 2023 & Section 65B Indian Evidence Act
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                <div><strong>CERTIFICATE ID:</strong> {certModal.certificate_id}</div>
                <div><strong>DOCUMENT NAME:</strong> {certModal.filename}</div>
                <div><strong>SHA-256 HASH:</strong> <span style={{ color: 'var(--arc-cyan)', wordBreak: 'break-all' }}>{certModal.sha256_hash}</span></div>
                <div><strong>LEGAL STATUS:</strong> <span style={{ color: '#10b981' }}>{certModal.admissibility_status}</span></div>
                <div><strong>TIMESTAMP (UTC):</strong> {certModal.timestamp_utc}</div>
              </div>
            </div>
          </div>
        )}

        {/* Global New Case Registration Modal */}
        <NewCaseModal
          isOpen={isNewCaseOpen}
          onClose={() => setIsNewCaseOpen(false)}
          onCaseCreated={(newCase) => {
            setCases((prev) => [newCase, ...prev]);
            setActiveCase(newCase);
            setActivePage('dashboard');
          }}
        />
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
