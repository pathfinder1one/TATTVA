'use client';

import { useState, useRef } from 'react';
import { uploadDocument, indexDocument } from '@/lib/api';
import { soundEngine } from '@/lib/soundEffects';
import { IconReport, IconArcReactor, IconLightning } from './StarkIcons';

export default function EvidenceIngestionModal({ caseId, isOpen, onClose, onIngested }) {
  const [selectedCategory, setSelectedCategory] = useState('FIR');
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [notes, setNotes] = useState('');
  const [uploadState, setUploadState] = useState('idle'); // 'idle' | 'uploading' | 'indexing' | 'success' | 'error'
  const [statusMessage, setStatusMessage] = useState('');
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const categories = [
    { id: 'FIR', label: 'FIR / Police Complaint', icon: '📄', formats: '.pdf, .docx, .txt' },
    { id: 'CDR', label: 'Call Detail Record (CDR)', icon: '📡', formats: '.csv, .xlsx' },
    { id: 'FINANCIAL', label: 'Financial / Hawala Ledger', icon: '💳', formats: '.csv, .xlsx, .json' },
    { id: 'SURVEILLANCE', label: 'Surveillance & OSINT Dump', icon: '🕵️', formats: '.txt, .docx, .json' },
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      soundEngine?.playBlip();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      soundEngine?.playBlip();
    }
  };

  const handleUploadAndIndex = async () => {
    if (!file || !caseId) return;

    try {
      setUploadState('uploading');
      setStatusMessage('Encrypting & computing SHA-256 evidence hash...');
      soundEngine?.playProcessCommand();

      // Step 1: Upload raw document
      const docRecord = await uploadDocument(caseId, file);
      
      // Step 2: Index into Qdrant & parse specialized entities
      setUploadState('indexing');
      setStatusMessage('Decomposing structure & indexing vectors into Qdrant neural memory...');
      
      await indexDocument(caseId, docRecord.document_id);

      setUploadState('success');
      setStatusMessage('Evidence successfully ingested and ready for multi-agent DAG traversal.');
      soundEngine?.playSuccess();

      setTimeout(() => {
        if (onIngested) onIngested(docRecord);
        onClose();
        // Reset state
        setFile(null);
        setUploadState('idle');
      }, 1400);

    } catch (err) {
      console.error('Evidence Ingestion Error:', err);
      setUploadState('error');
      setStatusMessage(err.message || 'Failed to ingest evidence document.');
      soundEngine?.playThreatAlert();
    }
  };

  return (
    <div className="riva-settings-modal">
      <div className="riva-settings-backdrop" onClick={onClose} />
      <div className="riva-settings-card" style={{ maxWidth: '620px' }}>
        
        {/* Header */}
        <div className="riva-settings-header">
          <div className="riva-settings-title">
            <IconReport size={18} color="var(--arc-cyan)" />
            <span>UNIVERSAL EVIDENCE INGESTION STATION // MHA NCRB</span>
          </div>
          <button className="riva-settings-close" onClick={onClose}>✕</button>
        </div>

        {/* Category Selection Tabs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label className="riva-settings-label">1. SELECT EVIDENCE CLASSIFICATION</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                className={`riva-option-pill ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '15px' }}>{cat.icon}</span>
                  <div>
                    <span className="riva-option-name">{cat.label}</span>
                    <span className="riva-option-desc">{cat.formats}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Drag and Drop Zone */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label className="riva-settings-label">2. EVIDENCE FILE PAYLOAD</label>
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${dragActive ? 'var(--arc-cyan)' : 'var(--border-stark)'}`,
              borderRadius: '12px',
              padding: '24px 20px',
              textAlign: 'center',
              background: dragActive ? 'rgba(0, 240, 255, 0.08)' : 'rgba(2, 6, 20, 0.6)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt,.csv,.xlsx,.json"
            />
            
            {file ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '24px' }}>📎</span>
                <span style={{ fontFamily: 'var(--font-stark)', fontSize: '13px', fontWeight: 700, color: 'var(--arc-cyan)' }}>
                  {file.name}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: '#94a3b8' }}>
                  {(file.size / 1024).toFixed(1)} KB · READY FOR FORENSIC HASHING
                </span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '50%',
                  background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  <IconLightning size={16} color="var(--arc-cyan)" />
                </div>
                <div style={{ fontFamily: 'var(--font-stark)', fontSize: '12px', fontWeight: 600, color: '#f1f5f9' }}>
                  Drag & Drop FIR / CDR / Bank Statements here or <span style={{ color: 'var(--arc-cyan)', textDecoration: 'underline' }}>Browse</span>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: '#64748b' }}>
                  Supports PDF, CSV, Excel, Word DOCX, JSON (Max 50MB per document)
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Officer Context / Notes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label className="riva-settings-label">3. INVESTIGATING OFFICER (IO) MEMO (OPTIONAL)</label>
          <input
            type="text"
            className="terminal-input"
            style={{
              padding: '8px 12px',
              background: 'rgba(2, 6, 20, 0.7)',
              border: '1px solid var(--border-stark)',
              borderRadius: '8px',
              fontSize: '11px',
            }}
            placeholder="e.g. CDR seizure from Suspect Handset (IMEI 3569...) under Panchnama #04"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Live Progress Feedback */}
        {uploadState !== 'idle' && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            background: uploadState === 'error' ? 'rgba(244, 63, 94, 0.12)' : uploadState === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(0, 240, 255, 0.08)',
            border: `1px solid ${uploadState === 'error' ? '#f43f5e' : uploadState === 'success' ? '#10b981' : 'var(--arc-cyan)'}`,
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: uploadState === 'error' ? '#f43f5e' : uploadState === 'success' ? '#10b981' : 'var(--arc-cyan)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}>
            {uploadState === 'uploading' || uploadState === 'indexing' ? (
              <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
            ) : uploadState === 'success' ? (
              <span>✓</span>
            ) : (
              <span>✕</span>
            )}
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 4 }}>
          <button
            type="button"
            onClick={onClose}
            className="directive-pill"
            style={{ padding: '8px 16px' }}
          >
            CANCEL
          </button>
          
          <button
            type="button"
            disabled={!file || uploadState === 'uploading' || uploadState === 'indexing'}
            onClick={handleUploadAndIndex}
            style={{
              padding: '8px 22px',
              background: !file ? 'rgba(255, 255, 255, 0.05)' : 'linear-gradient(135deg, #0284c7 0%, #00f0ff 100%)',
              color: !file ? '#64748b' : '#020617',
              border: 'none',
              borderRadius: '20px',
              fontFamily: 'var(--font-stark)',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '1px',
              cursor: !file ? 'not-allowed' : 'pointer',
              boxShadow: file ? '0 0 20px rgba(0, 240, 255, 0.5)' : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            {uploadState === 'uploading' ? 'UPLOADING...' : uploadState === 'indexing' ? 'INDEXING...' : 'INGEST EVIDENCE'}
          </button>
        </div>

      </div>
    </div>
  );
}
