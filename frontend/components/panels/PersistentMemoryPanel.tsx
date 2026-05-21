'use client';

import GlassCard from '@/components/ui/GlassCard';
import { languageLabel } from '@/lib/languages';
import { PatientInfo } from '@/types';

export default function PersistentMemoryPanel({ patient }: { patient: PatientInfo | null }) {
  return (
    <GlassCard title="Persistent Memory" icon="📦" highlight="amber">
      <p className="text-[10px] text-slate-500 leading-relaxed">
        PostgreSQL patient profile — language preference, preferred doctor, interaction history across sessions.
      </p>
      {patient ? (
        <div className="space-y-2 text-xs">
          <Row label="Patient" value={patient.patient_id} />
          <Row label="Language" value={languageLabel(patient.preferred_language)} />
          <Row label="Preferred doctor" value={patient.preferred_doctor ?? '—'} />
          <Row label="Interactions" value={String(patient.interaction_count ?? 0)} />
          {patient.last_interaction && (
            <Row label="Last visit" value={new Date(patient.last_interaction).toLocaleString()} />
          )}
          {patient.conversation_summary && (
            <p className="text-slate-400 text-xs leading-relaxed border-t border-white/5 pt-2">
              {patient.conversation_summary}
            </p>
          )}
        </div>
      ) : (
        <p className="text-xs text-slate-500">No patient record loaded. Check backend seed data for patient_001.</p>
      )}
    </GlassCard>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-200 text-right">{value}</span>
    </div>
  );
}
