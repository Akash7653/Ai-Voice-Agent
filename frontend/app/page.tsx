'use client';

import React from 'react';
import { useApp } from '@/context/AppContext';
import DashboardView from '@/components/dashboard/DashboardView';
import VoiceConsole from '@/components/voice/VoiceConsole';
import AppointmentsView from '@/components/dashboard/AppointmentsView';
import PatientsView from '@/components/dashboard/PatientsView';
import CampaignsView from '@/components/campaigns/CampaignsView';
import AnalyticsView from '@/components/analytics/AnalyticsView';

export default function HomePage() {
  const { view } = useApp();

  switch (view) {
    case 'dashboard':
      return <DashboardView />;
    case 'voice':
      return <VoiceConsole />;
    case 'appointments':
      return <AppointmentsView />;
    case 'patients':
      return <PatientsView />;
    case 'campaigns':
      return <CampaignsView />;
    case 'analytics':
      return <AnalyticsView />;
    default:
      return <VoiceConsole />;
  }
}
