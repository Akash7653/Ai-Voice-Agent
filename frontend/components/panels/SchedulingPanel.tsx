'use client';

import React, { useEffect, useState } from  'react';
import GlassCard from  '@/components/ui/GlassCard';
import { useApp } from '@/context/AppContext';
import { APIClient } from '@/services/api';
import type { ReasoningTrace } from '@/types';

export default function SchedulingPanel({
  suggestedSlots,
  conflictMessage,
  reasoning,
  onActionComplete,
}: {
  suggestedSlots: string[];
  conflictMessage?: string;
  reasoning?: ReasoningTrace | null;
  onActionComplete?: () => void;
}) {
  const { apiUrl, patientId } = useApp();
  const client = new APIClient(apiUrl);
  const hasSlots = suggestedSlots.length > 0;
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [doctors, setDoctors] = useState<Array<any>>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<any>(null);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        // If agent didn't provide doctor info, fetch active doctors as fallback
        if (!reasoning?.entities?.doctor_id) {
          const specialty = reasoning?.entities?.specialty;
          const res = await client.getDoctors(specialty ?? undefined);
          if (mounted && res?.success) {
            setDoctors(res.data ?? []);
          }
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      mounted = false;
    };
  }, [reasoning]);

  const speakText = (text: string, lang = 'en') => {
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch (e) {
      // ignore
    }
  };

  const handleBook = async (slot: string) => {
    if (busy) return;
    setBusy(true);
    setMessage(null);

    // Expect reasoning.entities to contain doctor_id, doctor_name, specialty
    const entities = reasoning?.entities ?? {};
    const payload = {
      patient_id: patientId,
      doctor_id: entities.doctor_id ?? entities.doctor ?? 'unknown',
      doctor_name: entities.doctor_name ?? entities.doctor ?? 'Doctor',
      specialty: entities.specialty ?? 'General',
      appointment_date: slot.split(' ')[0] ?? slot,
      appointment_time: slot.split(' ')[1] ?? slot,
    };

    try {
      // if user selected a doctor override payload
      if (selectedDoctor) {
        payload.doctor_id = selectedDoctor.id ?? selectedDoctor.doctor_id ?? payload.doctor_id;
        payload.doctor_name = selectedDoctor.name ?? selectedDoctor.doctor_name ?? payload.doctor_name;
      }

      const res = await client.createAppointment(payload);
      if (res?.success) {
        const okMsg = `Appointment booked for ${slot}`;
        setMessage(okMsg);

        // request server-side TTS and play
        try {
          const tts = await client.generateTTS(okMsg, reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            const b64 = (tts as any).audio;
            const binaryString = atob(b64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
            const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);
            const a = new Audio(url);
            a.play().catch(() => speakText(okMsg, reasoning?.language ?? 'en'));
            a.onended = () => URL.revokeObjectURL(url);
          } else {
            speakText(okMsg, reasoning?.language ?? 'en');
          }
        } catch {
          speakText(okMsg, reasoning?.language ?? 'en');
        }

        onActionComplete?.();
      } else {
        const err = res?.error ?? 'Unable to book slot';
        setMessage(String(err));
        try {
          const tts = await client.generateTTS(String(err), reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            const b64 = (tts as any).audio;
            const binaryString = atob(b64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
            const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);
            const a = new Audio(url);
            a.play().catch(() => speakText(String(err), reasoning?.language ?? 'en'));
            a.onended = () => URL.revokeObjectURL(url);
          } else {
            speakText(String(err), reasoning?.language ?? 'en');
          }
        } catch {
          speakText(String(err), reasoning?.language ?? 'en');
        }
      }
    } catch (e: any) {
      setMessage(String(e?.message ?? e ?? 'Booking failed'));
      try {
        await client.generateTTS('Booking failed, please try again', reasoning?.language ?? 'en');
      } catch {
        speakText('Booking failed, please try again', reasoning?.language ?? 'en');
      }
    }

    setBusy(false);
  };

  return (
    <GlassCard title="Scheduling" icon="📅" highlight="rose">
      {conflictMessage && (
        <p className="text-xs text-amber-200/90 leading-relaxed">{conflictMessage}</p>
      )}
      {/* Doctor selection fallback */}
      {(!reasoning?.entities?.doctor_id || doctors.length > 0) && (
        <div className="mb-2">
          <label className="text-xs text-slate-400">Doctor</label>
          <div className="mt-1">
            <select
              value={selectedDoctor?.id ?? ''}
              onChange={(e) => {
                const d = doctors.find((x) => (x.id ?? x.doctor_id) === e.target.value);
                setSelectedDoctor(d ?? null);
              }}
              className="w-full rounded-lg bg-white/5 border border-white/5 p-2 text-sm text-slate-200"
            >
              <option value="">Use agent suggestion</option>
              {doctors.map((d) => (
                <option key={d.id ?? d.doctor_id} value={d.id ?? d.doctor_id}>
                  {d.name ?? d.doctor_name} — {d.specialty}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
      {hasSlots ? (
        <div>
          <p className="text-xs text-rose-400/70 mb-2">Alternative slots (from agent response)</p>
          <ul className="space-y-2">
            {suggestedSlots.map((slot) => (
              <li key={slot} className="flex items-center justify-between">
                <span className="text-sm text-rose-200">• {slot}</span>
                <div className="flex gap-2">
                  <button
                    className="px-3 py-1.5 text-xs rounded-lg bg-emerald-500/20 text-emerald-200"
                    onClick={() => handleBook(slot)}
                    disabled={busy}
                  >
                    Book
                  </button>
                  <button
                    className="px-3 py-1.5 text-xs rounded-lg bg-yellow-500/20 text-yellow-200"
                    onClick={async () => {
                      // Reschedule uses appointment id from reasoning.entities
                      const apptId = reasoning?.entities?.appointment_id;
                      if (!apptId) {
                        setMessage('No appointment selected to reschedule');
                        return;
                      }
                      setBusy(true);
                      try {
                        const [date, time] = slot.split(' ');
                        const r = await client.rescheduleAppointment(apptId, {
                          appointment_date: date,
                          appointment_time: time,
                        });
                        if (r?.success) {
                          const ok = `Appointment rescheduled to ${slot}`;
                          setMessage(ok);
                          try {
                            const tts = await client.generateTTS(ok, reasoning?.language ?? 'en');
                            if (tts?.success && (tts as any).audio) {
                              const b64 = (tts as any).audio;
                              const binaryString = atob(b64);
                              const len = binaryString.length;
                              const bytes = new Uint8Array(len);
                              for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
                              const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
                              const url = URL.createObjectURL(blob);
                              const a = new Audio(url);
                              a.play().catch(() => speakText(ok, reasoning?.language ?? 'en'));
                              a.onended = () => URL.revokeObjectURL(url);
                            } else {
                              speakText(ok, reasoning?.language ?? 'en');
                            }
                          } catch {
                            speakText(ok, reasoning?.language ?? 'en');
                          }
                          onActionComplete?.();
                        } else {
                          setMessage(r?.error ?? 'Reschedule failed');
                        }
                      } finally {
                        setBusy(false);
                      }
                    }}
                    disabled={busy}
                  >
                    Reschedule
                  </button>
                  <button
                    className="px-3 py-1.5 text-xs rounded-lg bg-rose-500/20 text-rose-200"
                    onClick={async () => {
                      const apptId = reasoning?.entities?.appointment_id;
                      if (!apptId) {
                        setMessage('No appointment selected to cancel');
                        return;
                      }
                      setBusy(true);
                      try {
                        const c = await client.cancelAppointment(apptId);
                        if (c?.success) {
                          const ok = 'Appointment cancelled';
                          setMessage(ok);
                          try {
                            const tts = await client.generateTTS(ok, reasoning?.language ?? 'en');
                            if (tts?.success && (tts as any).audio) {
                              const b64 = (tts as any).audio;
                              const binaryString = atob(b64);
                              const len = binaryString.length;
                              const bytes = new Uint8Array(len);
                              for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
                              const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
                              const url = URL.createObjectURL(blob);
                              const a = new Audio(url);
                              a.play().catch(() => speakText(ok, reasoning?.language ?? 'en'));
                              a.onended = () => URL.revokeObjectURL(url);
                            } else {
                              speakText(ok, reasoning?.language ?? 'en');
                            }
                          } catch {
                            speakText(ok, reasoning?.language ?? 'en');
                          }
                          onActionComplete?.();
                        } else {
                          setMessage(c?.error ?? 'Cancel failed');
                        }
                      } finally {
                        setBusy(false);
                      }
                    }}
                    disabled={busy}
                  >
                    Cancel
                  </button>
                </div>
              </li>
            ))}
          </ul>
          {message && <p className="mt-2 text-sm text-slate-300">{message}</p>}
        </div>
      ) : (
        <p className="text-xs text-slate-500">
          Conflict detection and alternative slots appear when the agent suggests them in the response.
        </p>
      )}
    </GlassCard>
  );
}
