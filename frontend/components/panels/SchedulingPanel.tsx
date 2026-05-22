'use client';

import React, { useEffect, useState } from  'react';
import GlassCard from  '@/components/ui/GlassCard';
import { useApp } from '@/context/AppContext';
import { APIClient } from '@/services/api';
import type { ReasoningTrace } from '@/types';

/** Parse slot string into date and time components */
function parseSlot(slot: string): { date: string; time: string } {
  // Try common formats: "2025-12-20 10:30", "Dec 20 10:30 AM", "December 20 10:30", etc.
  const dateTimeMatch = slot.match(/(\d{4}-\d{2}-\d{2}|\w+\s+\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)/i);
  
  if (dateTimeMatch) {
    let datePart = dateTimeMatch[1];
    const timePart = dateTimeMatch[2];
    
    // Convert month names to ISO date if needed
    if (!/\d{4}-\d{2}-\d{2}/.test(datePart)) {
      const now = new Date();
      const monthYear = new Date(`${datePart} 2025`);
      if (!isNaN(monthYear.getTime())) {
        const year = now.getFullYear();
        const month = String(monthYear.getMonth() + 1).padStart(2, '0');
        const day = String(monthYear.getDate()).padStart(2, '0');
        datePart = `${year}-${month}-${day}`;
      }
    }
    
    return { date: datePart, time: timePart.toUpperCase().includes('AM') || timePart.toUpperCase().includes('PM') 
      ? timePart 
      : timePart.substring(0, 5) };
  }
  
  // Fallback: just split on space
  const parts = slot.trim().split(/\s+/);
  return {
    date: parts[0] ?? slot,
    time: parts[1] ?? '00:00',
  };
}

/** Play audio from base64 or fallback to browser TTS */
async function playAudio(
  base64Audio: string,
  fallbackText: string,
  language: string,
  onStart?: () => void,
  onEnd?: () => void
): Promise<void> {
  try {
    onStart?.();
    const binaryString = atob(base64Audio);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
    const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    
    return new Promise<void>((resolve) => {
      audio.onended = () => {
        URL.revokeObjectURL(url);
        onEnd?.();
        resolve();
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        // Fallback to browser TTS
        speakText(fallbackText, language);
        onEnd?.();
        resolve();
      };
      audio.play().catch(() => {
        URL.revokeObjectURL(url);
        speakText(fallbackText, language);
        onEnd?.();
        resolve();
      });
    });
  } catch {
    speakText(fallbackText, language);
    onEnd?.();
  }
}

/** Browser TTS fallback */
function speakText(text: string, lang = 'en'): void {
  try {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  } catch {
    // ignore
  }
}

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
  const [playingSlot, setPlayingSlot] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<'info' | 'error' | 'success'>('info');
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

  const handleBook = async (slot: string) => {
    if (busy || playingSlot) return;
    setBusy(true);
    setMessage(null);
    setMessageType('info');

    try {
      const { date, time } = parseSlot(slot);
      const entities = reasoning?.entities ?? {};
      const payload = {
        patient_id: patientId,
        doctor_id: entities.doctor_id ?? entities.doctor ?? 'unknown',
        doctor_name: entities.doctor_name ?? entities.doctor ?? 'Doctor',
        specialty: entities.specialty ?? 'General',
        appointment_date: date,
        appointment_time: time,
      };

      // Use selected doctor override if provided
      if (selectedDoctor) {
        payload.doctor_id = selectedDoctor.id ?? selectedDoctor.doctor_id ?? payload.doctor_id;
        payload.doctor_name = selectedDoctor.name ?? selectedDoctor.doctor_name ?? payload.doctor_name;
      }

      const res = await client.createAppointment(payload);
      
      if (res?.success) {
        const okMsg = `Appointment booked for ${slot}`;
        setMessage(okMsg);
        setMessageType('success');
        setPlayingSlot(slot);

        try {
          const tts = await client.generateTTS(okMsg, reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            await playAudio(
              (tts as any).audio,
              okMsg,
              reasoning?.language ?? 'en',
              () => setPlayingSlot(slot),
              () => {
                setPlayingSlot(null);
                onActionComplete?.();
              }
            );
          } else {
            speakText(okMsg, reasoning?.language ?? 'en');
            setPlayingSlot(null);
            onActionComplete?.();
          }
        } catch (e) {
          console.error('TTS failed:', e);
          speakText(okMsg, reasoning?.language ?? 'en');
          setPlayingSlot(null);
          onActionComplete?.();
        }
      } else {
        const err = res?.error ?? 'Unable to book slot';
        setMessage(String(err));
        setMessageType('error');
        setPlayingSlot(slot);

        try {
          const tts = await client.generateTTS(String(err), reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            await playAudio(
              (tts as any).audio,
              String(err),
              reasoning?.language ?? 'en',
              () => setPlayingSlot(slot),
              () => setPlayingSlot(null)
            );
          } else {
            speakText(String(err), reasoning?.language ?? 'en');
            setPlayingSlot(null);
          }
        } catch {
          speakText(String(err), reasoning?.language ?? 'en');
          setPlayingSlot(null);
        }
      }
    } catch (e: any) {
      const errMsg = String(e?.message ?? e ?? 'Booking failed');
      setMessage(errMsg);
      setMessageType('error');
      speakText(errMsg, reasoning?.language ?? 'en');
    } finally {
      setBusy(false);
    }
  };

  const handleReschedule = async (slot: string) => {
    if (busy || playingSlot) return;
    
    const apptId = reasoning?.entities?.appointment_id;
    if (!apptId) {
      setMessage('No appointment selected to reschedule');
      setMessageType('error');
      return;
    }

    setBusy(true);
    setMessage(null);
    setMessageType('info');

    try {
      const { date, time } = parseSlot(slot);
      const r = await client.rescheduleAppointment(apptId, {
        appointment_date: date,
        appointment_time: time,
      });

      if (r?.success) {
        const ok = `Appointment rescheduled to ${slot}`;
        setMessage(ok);
        setMessageType('success');
        setPlayingSlot(slot);

        try {
          const tts = await client.generateTTS(ok, reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            await playAudio(
              (tts as any).audio,
              ok,
              reasoning?.language ?? 'en',
              () => setPlayingSlot(slot),
              () => {
                setPlayingSlot(null);
                onActionComplete?.();
              }
            );
          } else {
            speakText(ok, reasoning?.language ?? 'en');
            setPlayingSlot(null);
            onActionComplete?.();
          }
        } catch {
          speakText(ok, reasoning?.language ?? 'en');
          setPlayingSlot(null);
          onActionComplete?.();
        }
      } else {
        setMessage(r?.error ?? 'Reschedule failed');
        setMessageType('error');
      }
    } catch (e: any) {
      setMessage(String(e?.message ?? e ?? 'Reschedule failed'));
      setMessageType('error');
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async () => {
    const apptId = reasoning?.entities?.appointment_id;
    if (!apptId) {
      setMessage('No appointment selected to cancel');
      setMessageType('error');
      return;
    }

    if (busy || playingSlot) return;
    setBusy(true);
    setMessage(null);
    setMessageType('info');

    try {
      const c = await client.cancelAppointment(apptId);
      if (c?.success) {
        const ok = 'Appointment cancelled';
        setMessage(ok);
        setMessageType('success');
        setPlayingSlot('cancel');

        try {
          const tts = await client.generateTTS(ok, reasoning?.language ?? 'en');
          if (tts?.success && (tts as any).audio) {
            await playAudio(
              (tts as any).audio,
              ok,
              reasoning?.language ?? 'en',
              () => setPlayingSlot('cancel'),
              () => {
                setPlayingSlot(null);
                onActionComplete?.();
              }
            );
          } else {
            speakText(ok, reasoning?.language ?? 'en');
            setPlayingSlot(null);
            onActionComplete?.();
          }
        } catch {
          speakText(ok, reasoning?.language ?? 'en');
          setPlayingSlot(null);
          onActionComplete?.();
        }
      } else {
        setMessage(c?.error ?? 'Cancel failed');
        setMessageType('error');
      }
    } catch (e: any) {
      setMessage(String(e?.message ?? e ?? 'Cancel failed'));
      setMessageType('error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <GlassCard title="Scheduling" icon="📅" highlight="rose">
      {conflictMessage && (
        <p className="text-xs text-amber-200/90 leading-relaxed mb-3">{conflictMessage}</p>
      )}
      
      {/* Doctor selection fallback */}
      {(!reasoning?.entities?.doctor_id || doctors.length > 0) && (
        <div className="mb-3">
          <label className="text-xs text-slate-400">Doctor</label>
          <div className="mt-1">
            <select
              value={selectedDoctor?.id ?? ''}
              onChange={(e) => {
                const d = doctors.find((x) => (x.id ?? x.doctor_id) === e.target.value);
                setSelectedDoctor(d ?? null);
              }}
              className="w-full rounded-lg bg-white/5 border border-white/5 p-2 text-sm text-slate-200 disabled:opacity-50"
              disabled={busy || !!playingSlot}
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

      {/* Message display with color based on type */}
      {message && (
        <div
          className={`mb-3 text-sm p-2 rounded-lg ${
            messageType === 'error'
              ? 'bg-rose-500/20 text-rose-200 border border-rose-500/30'
              : messageType === 'success'
                ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-500/30'
                : 'bg-cyan-500/20 text-cyan-200 border border-cyan-500/30'
          }`}
        >
          {playingSlot && (
            <div className="inline-block mr-2">
              <span className="inline-block h-3 w-3 rounded-full bg-current animate-pulse" />
            </div>
          )}
          {message}
        </div>
      )}

      {hasSlots ? (
        <div>
          <p className="text-xs text-rose-400/70 mb-2">Suggested slots</p>
          <ul className="space-y-2">
            {suggestedSlots.map((slot) => (
              <li key={slot} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition">
                <span className="text-sm text-rose-200 flex-shrink-0">• {slot}</span>
                <div className="flex gap-1 flex-shrink-0">
                  <button
                    className="px-2 py-1 text-xs rounded-lg bg-emerald-500/20 text-emerald-200 hover:bg-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    onClick={() => handleBook(slot)}
                    disabled={busy || !!playingSlot}
                    title="Book this slot"
                  >
                    {playingSlot === slot ? '🔊' : 'Book'}
                  </button>
                  {reasoning?.entities?.appointment_id && (
                    <>
                      <button
                        className="px-2 py-1 text-xs rounded-lg bg-yellow-500/20 text-yellow-200 hover:bg-yellow-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
                        onClick={() => handleReschedule(slot)}
                        disabled={busy || !!playingSlot}
                        title="Reschedule to this slot"
                      >
                        {playingSlot === slot ? '🔊' : 'Reschedule'}
                      </button>
                      <button
                        className="px-2 py-1 text-xs rounded-lg bg-rose-500/20 text-rose-200 hover:bg-rose-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
                        onClick={handleCancel}
                        disabled={busy || !!playingSlot}
                        title="Cancel appointment"
                      >
                        {playingSlot === 'cancel' ? '🔊' : 'Cancel'}
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-xs text-slate-500">
          Suggested slots and action buttons appear when the agent identifies appointment opportunities.
        </p>
      )}
    </GlassCard>
  );
}
