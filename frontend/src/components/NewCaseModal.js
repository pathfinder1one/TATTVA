'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { createCase } from '@/lib/api';
import { soundEngine } from '@/lib/soundEffects';

const generateCaseId = () => `CASE-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;

export default function NewCaseModal({ isOpen, onClose, onCaseCreated }) {
  const [caseNumber, setCaseNumber] = useState(generateCaseId);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('NARCOTICS');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setCaseNumber(generateCaseId());
      setErrorMessage('');
    }
  }, [isOpen]);

  if (!isOpen || !mounted) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !caseNumber.trim()) {
      setErrorMessage('Please enter both Case File Number and Case Title.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    try {
      soundEngine?.playProcessCommand();
      const newCase = await createCase({
        case_number: caseNumber.trim(),
        title: title.trim(),
        description: description.trim() || `Investigation into ${title.trim()} (${category} classification).`,
      });

      soundEngine?.playSuccess();
      onCaseCreated?.(newCase);
      onClose();
    } catch (err) {
      console.error('Failed to create case:', err);
      if (err.status === 409 || err.message?.includes('409') || err.message?.includes('already exists')) {
        const nextId = generateCaseId();
        setErrorMessage(`Case ID '${caseNumber}' pehle se maujood hai! Naya ID auto-generate kar diya gaya hai.`);
        setCaseNumber(nextId);
      } else {
        setErrorMessage(err.detail || err.message || 'Failed to initialize case in database.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 9999999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        padding: '24px',
        overflowY: 'auto',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 540,
          maxHeight: 'calc(100vh - 48px)',
          overflowY: 'auto',
          margin: 'auto',
          background: 'rgba(10, 11, 15, 0.98)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '12px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.95), 0 0 35px rgba(0, 240, 255, 0.15)',
          padding: '24px 28px',
          color: '#ffffff',
          fontFamily: 'var(--font-sans)',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: 14, marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--arc-cyan)', boxShadow: '0 0 10px var(--arc-cyan)' }} />
            <h3 style={{ fontFamily: 'var(--font-stark)', fontSize: 16, fontWeight: 700, letterSpacing: 1.5, margin: 0, color: '#ffffff' }}>
              REGISTER NEW CRIMINAL INVESTIGATION DOSSIER
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: 16, cursor: 'pointer', padding: 4 }}
          >
            ✕
          </button>
        </div>

        {errorMessage && (
          <div style={{ padding: '8px 12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid #f43f5e', borderRadius: 6, color: '#fecdd3', fontSize: 11, marginBottom: 14, fontFamily: 'var(--font-mono)' }}>
            ⚠️ {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Case Number & Category */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: 5 }}>
                CASE FILE ID / NUMBER *
              </label>
              <input
                type="text"
                value={caseNumber}
                onChange={(e) => setCaseNumber(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: 'rgba(0, 0, 0, 0.6)',
                  border: '1px solid var(--border-stark)',
                  borderRadius: 6,
                  color: 'var(--arc-cyan)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: 5 }}>
                CRIME CLASSIFICATION
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: 'rgba(0, 0, 0, 0.6)',
                  border: '1px solid var(--border-stark)',
                  borderRadius: 6,
                  color: '#ffffff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="NARCOTICS">Narcotics & NDPS Cartel</option>
                <option value="HAWALA">Financial Fraud & Hawala</option>
                <option value="ORGANIZED_GANG">Organized Extortion Gang</option>
                <option value="CYBER_CRIME">Cybercrime / Phishing Cartel</option>
                <option value="TERROR_FINANCE">Terror Finance & Arms</option>
              </select>
            </div>
          </div>

          {/* Case Title */}
          <div>
            <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: 5 }}>
              CASE TITLE / OPERATION CODENAME *
            </label>
            <input
              type="text"
              placeholder="e.g. Operation Vajra: Delhi-NCR Narcotics Interception"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '9px 12px',
                background: 'rgba(0, 0, 0, 0.6)',
                border: '1px solid var(--border-stark)',
                borderRadius: 6,
                color: '#ffffff',
                fontFamily: 'var(--font-sans)',
                fontSize: 12,
                outline: 'none',
              }}
            />
          </div>

          {/* Case Description / Scope */}
          <div>
            <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: 5 }}>
              INVESTIGATION DIRECTIVE & SCOPE
            </label>
            <textarea
              rows={3}
              placeholder="Describe the criminal network, suspected jurisdictions, key FIR numbers, and objectives of the investigation..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                background: 'rgba(0, 0, 0, 0.6)',
                border: '1px solid var(--border-stark)',
                borderRadius: 6,
                color: '#ffffff',
                fontFamily: 'var(--font-sans)',
                fontSize: 12,
                outline: 'none',
                resize: 'none',
              }}
            />
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10, marginTop: 8, borderTop: '1px solid var(--border-subtle)', paddingTop: 14 }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 16px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6,
                color: 'var(--text-secondary)',
                fontSize: 11,
                fontFamily: 'var(--font-stark)',
                cursor: 'pointer',
              }}
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                padding: '8px 20px',
                background: 'var(--arc-cyan)',
                border: 'none',
                borderRadius: 6,
                color: '#020617',
                fontFamily: 'var(--font-stark)',
                fontWeight: 700,
                fontSize: 11,
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                letterSpacing: 1,
                boxShadow: '0 0 16px rgba(0, 240, 255, 0.4)',
              }}
            >
              {isSubmitting ? 'INITIALIZING DOSSIER...' : 'CREATE & INITIALIZE CASE ➔'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
