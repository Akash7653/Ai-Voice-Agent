'use client';

import React from 'react';
import { useApp } from '@/context/AppContext';

const titles: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview and quick actions' },
  voice: { title: 'Voice Agent', subtitle: 'Real-time multilingual assistant' },
  appointments: { title: 'Appointments', subtitle: 'Scheduled visits and availability' },
  patients: { title: 'Patients', subtitle: 'Patient profiles and preferences' },
  campaigns: { title: 'Campaigns', subtitle: 'Outbound reminders and follow-ups' },
  analytics: { title: 'Analytics', subtitle: 'Latency and conversation metrics' },
};

export default function PageHeader({
  status,
  statusTone = 'ok',
}: {
  status?: string;
  statusTone?: 'ok' | 'warn' | 'error';
}) {
  const { view } = useApp();
  const meta = titles[view] ?? titles.voice;

  const dotClass =
    statusTone === 'error'
      ? 'bg-rose-500'
      : statusTone === 'warn'
        ? 'bg-amber-500'
        : 'bg-emerald-500';

  return (
    <header className="flex shrink-0 items-center justify-between border-b border-white/5 bg-slate-950/50 px-6 py-4 backdrop-blur-md">
      <div>
        <h1 className="gradient-text text-xl font-semibold">{meta.title}</h1>
        <p className="text-xs text-slate-400">{meta.subtitle}</p>
      </div>
      {status && (
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
          <span className={`h-2 w-2 rounded-full ${dotClass} animate-pulse`} />
          <span className="text-xs capitalize text-slate-300">{status}</span>
        </div>
      )}
    </header>
  );
}
