'use client';

import { useCallback, useEffect, useState } from 'react';
import { APIClient } from '@/services/api';
import { Appointment, Doctor, LatencyStats, PatientInfo } from '@/types';

export function usePatientData(apiUrl: string, patientId: string) {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patient, setPatient] = useState<PatientInfo | null>(null);
  const [latencyStats, setLatencyStats] = useState<LatencyStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError(null);
    setWarnings([]);
    const client = new APIClient(apiUrl);
    const nextWarnings: string[] = [];

    const [apptRes, docRes, patientRes, latencyRes] = await Promise.all([
      client.getAppointments(patientId),
      client.getDoctors(),
      client.getPatientInfo(patientId),
      client.getLatencyStats(patientId),
    ]);

    if (apptRes?.success) {
      setAppointments((apptRes.data as Appointment[]) ?? []);
    } else {
      setAppointments([]);
      if (apptRes?.error) nextWarnings.push(`Appointments: ${apptRes.error}`);
    }

    if (docRes?.success) {
      setDoctors((docRes.data as Doctor[]) ?? []);
    } else {
      setDoctors([]);
      if (docRes?.error) nextWarnings.push(`Doctors: ${docRes.error}`);
    }

    if (patientRes?.success) {
      setPatient((patientRes.data as PatientInfo) ?? null);
    } else {
      setPatient(null);
      if (patientRes?.error) nextWarnings.push(`Patient profile: ${patientRes.error}`);
    }

    if (latencyRes?.success) {
      setLatencyStats((latencyRes.data as LatencyStats) ?? null);
    } else {
      setLatencyStats(null);
      if (latencyRes?.error) nextWarnings.push(`Latency stats unavailable`);
    }

    setWarnings(nextWarnings);
    setLoading(false);
  }, [apiUrl, patientId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const updatePreferences = useCallback(
    async (preferences: { preferred_language?: string; preferred_doctor?: string }) => {
      const client = new APIClient(apiUrl);
      const result = await client.updatePatientPreferences(patientId, preferences);
      if (!result?.success) {
        throw new Error(result?.error ?? 'Failed to update preferences');
      }
      await refresh();
    },
    [apiUrl, patientId, refresh]
  );

  return {
    appointments,
    doctors,
    patient,
    latencyStats,
    loading,
    error,
    warnings,
    refresh,
    updatePreferences,
  };
}
