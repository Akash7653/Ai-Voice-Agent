'use client';

import React from  'react';
import { Appointment } from  '@/types';

export default function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const statusClass =
    appointment.status === 'scheduled'
      ? 'bg-cyan-400/15 text-cyan-200'
      : appointment.status === 'completed'
        ? 'bg-emerald-400/15 text-emerald-200'
        : 'bg-rose-400/15 text-rose-200';

  return (
    <div className="glass-panel p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className="font-semibold text-white">{appointment.doctor_name}</p>
          <p className="text-xs text-slate-400">{appointment.specialty}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${statusClass}`}>
          {appointment.status}
        </span>
      </div>
      <div className="text-xs text-slate-400 space-y-0.5">
        <p>{appointment.appointment_date}</p>
        <p>{appointment.appointment_time}</p>
      </div>
      <p className="text-[10px] text-slate-600 mt-2">
        Reschedule or cancel via voice — agent uses tool orchestration, not hardcoded UI responses.
      </p>
    </div>
  );
}
