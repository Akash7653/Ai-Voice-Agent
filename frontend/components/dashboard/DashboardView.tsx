'use client';

import React from 'react';
import PageHeader from '@/components/layout/PageHeader';
import PipelineDiagram from '@/components/panels/PipelineDiagram';
import GlassCard from '@/components/ui/GlassCard';
import { useApp } from '@/context/AppContext';
import { usePatientData } from '@/hooks/usePatientData';

export default function DashboardView() {
  const { setView, apiUrl, patientId } = useApp();
  const { appointments, doctors, patient, latencyStats, loading } = usePatientData(apiUrl, patientId);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status="overview" />
      <div className="flex-1 overflow-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-6xl space-y-6">
          <PipelineDiagram />

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Appointments" value={loading ? '…' : String(appointments.length)} />
            <StatCard label="Doctors" value={loading ? '…' : String(doctors.length)} />
            <StatCard
              label="Avg latency"
              value={
                latencyStats?.avg_total_latency
                  ? `${latencyStats.avg_total_latency.toFixed(0)}ms`
                  : '—'
              }
            />
            <StatCard label="Interactions" value={String(patient?.interaction_count ?? 0)} />
          </div>

          <GlassCard title="Quick start" icon="🎤" highlight="emerald">
            <p className="text-sm text-slate-400 mb-4">
              Open the Voice Agent to book, reschedule, or cancel appointments in English, Hindi, or Tamil.
              Reasoning traces and latency breakdown are shown live for evaluation.
            </p>
            <button
              type="button"
              onClick={() => setView('voice')}
              className="btn btn-primary"
            >
              Launch voice agent
            </button>
          </GlassCard>

          <div className="grid gap-4 md:grid-cols-3 text-xs text-slate-500">
            <FeatureChip title="Multilingual" desc="EN · HI · TA auto-detect" />
            <FeatureChip title="Memory" desc="Session (Redis) + persistent (PostgreSQL)" />
            <FeatureChip title="Campaigns" desc="Outbound reminders & follow-ups" />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass-panel p-4 text-center">
      <p className="text-2xl font-bold text-cyan-200">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  );
}

function FeatureChip({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="glass-panel p-3">
      <p className="font-medium text-slate-300">{title}</p>
      <p>{desc}</p>
    </div>
  );
}
