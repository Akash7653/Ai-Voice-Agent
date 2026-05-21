'use client';

import React from 'react';
import { AppProvider } from '@/context/AppContext';
import SideNav from '@/components/layout/SideNav';
import MobileNav from '@/components/layout/MobileNav';

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AppProvider>
      <div className="flex min-h-screen w-full bg-[#050816] text-white">
        <SideNav />
        <main className="flex min-h-screen flex-1 flex-col overflow-hidden pb-14 lg:pb-0">
          {children}
        </main>
        <MobileNav />
      </div>
    </AppProvider>
  );
}
