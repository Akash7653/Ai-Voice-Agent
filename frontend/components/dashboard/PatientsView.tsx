'use client';

import React, { useState } from  'react';
import PageHeader from  '@/components/layout/PageHeader';
import GlassCard from  '@/components/ui/GlassCard';
import { useApp } from  '@/context/AppContext';
import { usePatientData } from  '@/hooks/usePatientData';
import { LANGUAGES } from  '@/lib/languages';

export default function PatientsView() {
  const { apiUrl, patientId, setPatientId } = useApp();
  const { patient, loading, updatePreferences } = usePatientData(apiUrl, patientId);
  const [editId, setEditId] = useState(patientId);
  const [lang, setLang] = useState('en');
  const [doctor, setDoctor] = useState('');
  const [saving, setSaving] = useState(false);

  React.useEffect(() => {
    if (patient?.preferred_language) setLang(patient.preferred_language);
    if (patient?.preferred_doctor) setDoctor(patient.preferred_doctor);
  }, [patient]);

  const save = async () => {
    setSaving(true);
    try {
      await updatePreferences({
        preferred_language: lang,
        preferred_doctor: doctor || undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status={patientId} />
      <div className="flex-1 overflow-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-2xl space-y-6">
          <GlassCard title="Patient ID" icon="👤" highlight="cyan">
            <p className="text-xs text-slate-500 mb-2">Default: patient_001 (seed data)</p>
            <div className="flex gap-2">
              <input
                value={editId}
                onChange={(e) => setEditId(e.target.value)}
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
              />
              <button
                type="button"
                onClick={() => setPatientId(editId.trim() || 'patient_001')}
                className="btn btn-primary text-sm"
              >
                Load
              </button>
            </div>
          </GlassCard>

          <GlassCard title="Persistent memory" icon="📦" highlight="amber">
            {loading ? (
              <p className="text-sm text-slate-500">Loading…</p>
            ) : patient ? (
              <div className="space-y-4 text-sm">
                <p className="text-slate-400">{patient.conversation_summary || 'No summary yet.'}</p>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Preferred language</label>
                  <select
                    value={lang}
                    onChange={(e) => setLang(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.label} ({l.native})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Preferred doctor</label>
                  <input
                    value={doctor}
                    onChange={(e) => setDoctor(e.target.value)}
                    placeholder="e.g. Dr. Sharma"
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white"
                  />
                </div>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="btn btn-primary w-full disabled:opacity-50"
                >
                  {saving ? 'Saving…' : 'Save preferences'}
                </button>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Patient not found in database.</p>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
