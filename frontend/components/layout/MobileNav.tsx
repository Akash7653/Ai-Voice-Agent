'use client';

import React from 'react';
import { AppView, useApp } from '@/context/AppContext';

const items: { id: AppView; label: string }[] = [
  { id: 'dashboard', label: 'Home' },
  { id: 'voice', label: 'Voice' },
  { id: 'appointments', label: 'Appts' },
  { id: 'analytics', label: 'Stats' },
];

export default function MobileNav() {
  const { view, setView } = useApp();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-slate-800 bg-slate-950/95 backdrop-blur-lg lg:hidden">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => setView(item.id)}
          className={`flex-1 py-3 text-xs font-medium ${
            view === item.id ? 'text-cyan-300' : 'text-slate-500'
          }`}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
