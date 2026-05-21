'use client';

import React from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Appointment } from '@/types';

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const statusClass =
    appointment.status === 'scheduled'
      ? 'bg-cyan-400/15 text-cyan-200'
      : appointment.status === 'completed'
        ? 'bg-emerald-400/15 text-emerald-200'
        : 'bg-rose-400/15 text-rose-200';

  return (
    <div className="glass-panel p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <div className="font-semibold text-white">{appointment.doctor_name}</div>
          <div className="text-xs text-slate-400">{appointment.specialty}</div>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusClass}`}>
          {appointment.status}
        </span>
      </div>
      <div className="space-y-1 text-xs text-slate-300">
        <p>{appointment.appointment_date}</p>
        <p>{appointment.appointment_time}</p>
      </div>
    </div>
  );
}

export default function AppointmentsPanel({
  appointments,
  loading,
  error,
  onRefresh,
}: {
  appointments: Appointment[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <PageHeader status={loading ? 'loading' : 'ready'} />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Your appointments</h2>
          <button type="button" onClick={onRefresh} className="btn btn-secondary text-xs">
            Refresh
          </button>
        </div>
        {error && (
          <p className="mb-4 text-sm text-amber-300">
            Could not load appointments. Is the backend running?
          </p>
        )}
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : appointments.length === 0 ? (
          <p className="text-sm text-slate-500">No appointments yet. Book one via the voice agent.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {appointments.map((a) => (
              <AppointmentCard key={a.id} appointment={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
