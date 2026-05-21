'use client';

import React from  'react';
import PageHeader from  '@/components/layout/PageHeader';
import AppointmentCard from  '@/components/dashboard/AppointmentCard';
import GlassCard from  '@/components/ui/GlassCard';
import { useApp } from  '@/context/AppContext';
import { usePatientData } from  '@/hooks/usePatientData';

export default function AppointmentsView() {
  const { apiUrl, patientId, setView } = useApp();
  const { appointments, doctors, loading, error } = usePatientData(apiUrl, patientId);

  const scheduled = appointments.filter((a) => a.status === 'scheduled');

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status={`${scheduled.length} scheduled`} />
      <div className="flex-1 overflow-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-6xl space-y-6">
          {error && (
            <div className="glass-panel border border-rose-500/30 p-3 text-sm text-rose-200">{error}</div>
          )}

          <GlassCard title="Appointment lifecycle" icon="📋" highlight="rose">
            <p className="text-xs text-slate-400">
              Book · Reschedule · Cancel · Check availability — handled by the voice agent via tool calls.
              Conflict detection returns alternative slots in the agent response.
            </p>
            <button type="button" onClick={() => setView('voice')} className="btn btn-primary mt-2 text-sm">
              Manage via voice
            </button>
          </GlassCard>

          {loading ? (
            <p className="text-slate-500 text-sm">Loading appointments…</p>
          ) : appointments.length === 0 ? (
            <p className="text-slate-500 text-sm">No appointments yet. Use the voice agent to book one.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {appointments.map((a) => (
                <AppointmentCard key={a.id} appointment={a} />
              ))}
            </div>
          )}

          {doctors.length > 0 && (
            <GlassCard title="Doctor availability" icon="👨‍⚕️" highlight="cyan">
              <div className="space-y-3 max-h-64 overflow-auto">
                {doctors.map((d) => (
                  <div key={d.id} className="border-b border-white/5 pb-2 last:border-0">
                    <p className="text-sm font-medium text-white">{d.name}</p>
                    <p className="text-xs text-slate-400">{d.specialty} · {d.working_hours}</p>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
