'use client';

import { useCallback, useRef, useState } from 'react';
import { blobToWavArrayBuffer } from '@/lib/audioEncode';
import { VoiceClient } from '@/services/api';
import { LatencyMetrics, ReasoningTrace, WebSocketMessage } from '@/types';

/** Minimum WAV payload before sending to STT (bytes). */
export const MIN_RECORDING_BYTES = 8000;
/** Minimum recording duration (ms). */
export const MIN_RECORDING_MS = 1200;

export function useVoiceCapture() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef('audio/webm');
  const recordStartedAtRef = useRef(0);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recordingRef = useRef(false);
  const rafRef = useRef<number | null>(null);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    audioContext.createMediaStreamSource(stream).connect(analyser);
    analyserRef.current = analyser;

    let selectedMimeType = 'audio/webm;codecs=opus';
    if (!MediaRecorder.isTypeSupported(selectedMimeType)) {
      selectedMimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
    }
    mimeTypeRef.current = selectedMimeType || 'audio/webm';

    const mediaRecorder = new MediaRecorder(
      stream,
      selectedMimeType ? { mimeType: selectedMimeType } : undefined
    );

    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    // Single blob on stop — avoids invalid concatenated WebM fragments (Windows/Chrome).
    mediaRecorder.start();
    mediaRecorderRef.current = mediaRecorder;
    recordingRef.current = true;
    recordStartedAtRef.current = Date.now();
    setIsRecording(true);

    const updateAudioLevel = () => {
      if (!recordingRef.current || !analyserRef.current) return;
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(average);
      rafRef.current = requestAnimationFrame(updateAudioLevel);
    };
    updateAudioLevel();
  }, []);

  const stopRecording = useCallback((): Promise<ArrayBuffer | null> => {
    return new Promise((resolve) => {
      recordingRef.current = false;
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }

      if (!mediaRecorderRef.current) {
        setIsRecording(false);
        resolve(null);
        return;
      }

      const recorder = mediaRecorderRef.current;

      recorder.onstop = async () => {
        recorder.stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);
        setAudioLevel(0);
        mediaRecorderRef.current = null;

        const blob = new Blob(audioChunksRef.current, { type: mimeTypeRef.current });
        audioChunksRef.current = [];

        if (blob.size === 0) {
          resolve(null);
          return;
        }

        try {
          const wav = await blobToWavArrayBuffer(blob);
          console.log(
            `[Audio] Recorded ${blob.size} bytes (${mimeTypeRef.current}) → WAV ${wav.byteLength} bytes`
          );
          resolve(wav);
        } catch (err) {
          console.warn('[Audio] WAV conversion failed, sending raw blob:', err);
          resolve(await blob.arrayBuffer());
        }
      };

      if (recorder.state === 'recording') {
        recorder.requestData();
      }
      recorder.stop();
    });
  }, []);

  const getRecordingDurationMs = useCallback(
    () => (recordStartedAtRef.current ? Date.now() - recordStartedAtRef.current : 0),
    []
  );

  return { startRecording, stopRecording, isRecording, audioLevel, getRecordingDurationMs };
}

export function useVoiceWebSocket(apiUrl: string, patientId: string) {
  const clientRef = useRef<VoiceClient | null>(null);
  const connectedRef = useRef(false);
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState('auto');
  const [reasoning, setReasoning] = useState<ReasoningTrace | null>(null);
  const [latencyMetrics, setLatencyMetrics] = useState<LatencyMetrics | null>(null);
  const [responseText, setResponseText] = useState('');
  const [responseAudio, setResponseAudio] = useState<ArrayBuffer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const connect = useCallback(async () => {
    const client = new VoiceClient(apiUrl, patientId);

    client.onMessageReceived((message) => {
      if (message.type === 'session_start' && message.session_id) {
        setSessionId(String(message.session_id));
      } else if (message.type === 'transcript') {
        setTranscript(message.text);
        if (message.language) setDetectedLanguage(message.language);
      } else if (message.type === 'reasoning_trace') {
        setReasoning({
          intent: message.intent,
          confidence: message.confidence,
          entities: message.entities,
          reasoning: message.reasoning,
        });
      } else if (message.type === 'response') {
        setResponseText(message.text);
        if (message.audio) {
          const binaryString = atob(message.audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          setResponseAudio(bytes.buffer);
        }
      } else if (message.type === 'latency_metrics') {
        setLatencyMetrics({
          total_latency_ms: message.total_latency_ms,
          breakdown: message.breakdown ?? {},
        });
      } else if (message.type === 'error') {
        setError(message.message);
      }
    });

    client.onErrorReceived((err) => setError(`Service error: ${err}`));
    client.onConnectionClosed(() => {
      connectedRef.current = false;
      setIsConnected(false);
    });

    await client.connect();
    clientRef.current = client;
    connectedRef.current = true;
    setIsConnected(true);
    setError(null);
  }, [apiUrl, patientId]);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    connectedRef.current = false;
    setIsConnected(false);
  }, []);

  const sendAudioChunk = useCallback(async (audioData: ArrayBuffer) => {
    if (!clientRef.current?.isConnected()) return;
    await clientRef.current.sendAudioChunk(audioData);
  }, []);

  /** Send complete recording as one WebM blob (required for valid Whisper input). */
  const sendRecording = useCallback(async (audioData: ArrayBuffer) => {
    if (!clientRef.current?.isConnected()) return;
    await clientRef.current.sendAudioChunk(audioData);
  }, []);

  const endAudio = useCallback(async () => {
    if (!clientRef.current?.isConnected()) return;
    await clientRef.current.endAudio();
  }, []);

  const resetTurn = useCallback(() => {
    setTranscript('');
    setResponseText('');
    setResponseAudio(null);
    setReasoning(null);
    setLatencyMetrics(null);
    setError(null);
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    sendAudioChunk,
    sendRecording,
    endAudio,
    resetTurn,
    sessionId,
    transcript,
    reasoning,
    latencyMetrics,
    responseText,
    responseAudio,
    detectedLanguage,
    error,
  };
}

export function useAudioPlayback() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);

  const playAudio = useCallback(async (audioData: ArrayBuffer) => {
    try {
      const audioContext = audioContextRef.current ?? new AudioContext();
      audioContextRef.current = audioContext;
      const audioBuffer = await audioContext.decodeAudioData(audioData.slice(0));
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start(0);
      return new Promise<void>((resolve) => {
        source.onended = () => resolve();
      });
    } catch {
      const blob = new Blob([audioData], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);
      const audio = audioElRef.current ?? new Audio(url);
      audioElRef.current = audio;
      return new Promise<void>((resolve, reject) => {
        audio.onended = () => {
          URL.revokeObjectURL(url);
          resolve();
        };
        audio.onerror = reject;
        audio.play().catch(reject);
      });
    }
  }, []);

  return { playAudio };
}
