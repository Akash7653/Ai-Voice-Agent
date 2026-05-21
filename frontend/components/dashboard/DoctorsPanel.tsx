'use client';

import React from 'react';
import { Doctor } from '@/types';

export default function DoctorsPanel({ doctors, compact }: { doctors: Doctor[]; compact?: boolean }) {
  if (doctors.length === 0) {
    return <p className="text-xs text-slate-500">No doctors loaded.</p>;
  }

  return (
    <div className={compact ? 'space-y-2' : 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3'}>
      {doctors.map((d) => (
        <div key={d.id} className="glass-panel p-4">
          <div className="font-semibold text-white">{d.name}</div>
          <div className="text-xs text-cyan-300/80">{d.specialty}</div>
          <div className="mt-2 text-xs text-slate-400">Hours: {d.working_hours}</div>
        </div>
      ))}
    </div>
  );
}
