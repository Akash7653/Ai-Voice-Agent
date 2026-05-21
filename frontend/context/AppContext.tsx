'use client';

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

export type AppView =
  | 'dashboard'
  | 'voice'
  | 'appointments'
  | 'patients'
  | 'campaigns'
  | 'analytics';

type AppContextValue = {
  view: AppView;
  setView: (view: AppView) => void;
  patientId: string;
  setPatientId: (id: string) => void;
  apiUrl: string;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [view, setView] = useState<AppView>('voice');
  const [patientId, setPatientId] = useState('patient_001');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const value = useMemo(
    () => ({
      view,
      setView,
      patientId,
      setPatientId,
      apiUrl,
    }),
    [view, patientId, apiUrl]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useApp must be used within AppProvider');
  }
  return ctx;
}

export function useSetView() {
  const { setView } = useApp();
  return useCallback((view: AppView) => setView(view), [setView]);
}
