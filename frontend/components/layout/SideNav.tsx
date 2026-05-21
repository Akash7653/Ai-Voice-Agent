'use client';

import React, { useState } from  'react';
import { AppView, useApp } from  '@/context/AppContext';
import VoiceAgentSelector from  '@/components/VoiceAgentSelector';
import ModeSwitcher from  '@/components/ModeSwitcher';

const links: { id: AppView; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '◉' },
  { id: 'voice', label: 'Voice Agent', icon: '◎' },
  { id: 'appointments', label: 'Appointments', icon: '▣' },
  { id: 'patients', label: 'Patients', icon: '◇' },
  { id: 'campaigns', label: 'Campaigns', icon: '◈' },
  { id: 'analytics', label: 'Analytics', icon: '▤' },
];

export default function SideNav() {
  const { view, setView } = useApp();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`z-40 hidden flex-col border-r border-slate-800/80 bg-slate-950/90 backdrop-blur-xl lg:flex ${
        collapsed ? 'w-[72px]' : 'w-60'
      } transition-all duration-200`}
    >
      <div className="flex items-center justify-between border-b border-slate-800/80 p-4">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from -cyan-400 to-blue-600 text-sm font-bold">
            2C
          </div>
          {!collapsed && (
            <div>
              <div className="truncate text-sm font-semibold text-white">2Care.ai</div>
              <div className="text-[10px] text-slate-500">Voice Healthcare</div>
            </div>
          )}
        </div>
        <button
          type="button"
          aria-label="Toggle sidebar"
          onClick={() => setCollapsed((c) => !c)}
          className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          {collapsed ? '»' : '«'}
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-auto px-2 py-4">
        {links.map((l) => (
          <button
            key={l.id}
            type="button"
            onClick={() => setView(l.id)}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
              view === l.id
                ? 'bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-500/30'
                : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
            }`}
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-slate-800/80 text-xs">
              {l.icon}
            </span>
            {!collapsed && <span>{l.label}</span>}
          </button>
        ))}
      </nav>

      <div className="space-y-3 border-t border-slate-800/80 p-4">
        {!collapsed && (
          <div>
            <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Voice Agent
            </div>
            <VoiceAgentSelector onChange={() => {}} />
          </div>
        )}
        <div className="flex items-center justify-between gap-2">
          {!collapsed && <span className="text-[10px] text-slate-500">Theme</span>}
          <ModeSwitcher />
        </div>
      </div>
    </aside>
  );
}
