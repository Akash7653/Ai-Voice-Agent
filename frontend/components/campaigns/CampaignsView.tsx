'use client';

import React from 'react';
import PageHeader from '@/components/layout/PageHeader';
import GlassCard from '@/components/ui/GlassCard';
import { CampaignTask } from '@/types';

/** Placeholder campaigns — no GET /api/campaigns on backend yet; scheduler writes campaign_task rows */
const DEMO_CAMPAIGNS: CampaignTask[] = [
  {
    id: '1',
    patient_id: 'patient_001',
    campaign_type: 'reminder',
    scheduled_at: new Date(Date.now() + 86400000).toISOString(),
    status: 'scheduled',
    message: 'Reminder: appointment tomorrow at 10:00 AM',
  },
  {
    id: '2',
    patient_id: 'patient_001',
    campaign_type: 'follow_up',
    scheduled_at: new Date(Date.now() + 3 * 86400000).toISOString(),
    status: 'scheduled',
    message: 'Follow-up check-in 3 days post-visit',
  },
];

const STATUS_STYLES: Record<string, string> = {
  scheduled: 'bg-cyan-500/15 text-cyan-200',
  confirmed: 'bg-emerald-500/15 text-emerald-200',
  rescheduled: 'bg-amber-500/15 text-amber-200',
  rejected: 'bg-rose-500/15 text-rose-200',
  completed: 'bg-slate-500/15 text-slate-300',
};

export default function CampaignsView() {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status="outbound" />
      <div className="flex-1 overflow-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-6">
          <GlassCard title="Outbound campaign mode" icon="📞" highlight="purple">
            <p className="text-sm text-slate-400 leading-relaxed">
              The platform initiates proactive voice calls for appointment reminders, follow-up checkups,
              and vaccination reminders. The same agent handles inbound and outbound — patients can confirm,
              reschedule (&quot;move it to Friday&quot;), or politely decline. Campaign tasks are scheduled by{' '}
              <code className="text-purple-300">campaign_scheduler.py</code> (APScheduler, every 5 min).
            </p>
            <p className="text-xs text-amber-400/80 mt-2">
              Note: REST endpoint <code>GET /api/campaigns</code> is not implemented yet — showing structured demo data aligned with the DB schema.
            </p>
          </GlassCard>

          <div className="space-y-3">
            {DEMO_CAMPAIGNS.map((c) => (
              <div key={c.id} className="glass-panel p-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-white capitalize">
                    {c.campaign_type.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">{c.message}</p>
                  <p className="text-[10px] text-slate-600 mt-2">
                    Scheduled: {new Date(c.scheduled_at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded-full capitalize ${
                    STATUS_STYLES[c.status] ?? STATUS_STYLES.scheduled
                  }`}
                >
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
