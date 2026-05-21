export interface Appointment {
  id: string;
  doctor_name: string;
  specialty: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
  created_at: string;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  working_hours: string;
  available_slots: Record<string, string[]>;
}

export interface ReasoningTrace {
  intent: string;
  confidence: number;
  entities: Record<string, unknown>;
  reasoning: string;
}

export interface LatencyMetrics {
  total_latency_ms: number;
  breakdown: Record<string, number>;
}

export interface LatencyStats {
  avg_total_latency: number;
  min_latency: number;
  max_latency: number;
  metrics_count: number;
}

export interface PatientInfo {
  patient_id: string;
  preferred_language: string;
  preferred_doctor?: string;
  interaction_count: number;
  last_interaction?: string;
  conversation_summary?: string;
}

export interface SessionInfo {
  session_id: string;
  patient_id: string;
  language: string;
  context?: Record<string, unknown>;
  state?: string;
  transcript?: string;
  last_response?: string;
  detected_language?: string;
}

export interface CampaignTask {
  id: string;
  patient_id: string;
  campaign_type: 'reminder' | 'follow_up' | 'vaccination';
  scheduled_at: string;
  status: 'scheduled' | 'confirmed' | 'rescheduled' | 'rejected' | 'completed';
  message?: string;
}

export type WebSocketMessage =
  | { type: 'session_start'; session_id: string; message?: string }
  | { type: 'transcript'; text: string; language?: string; confidence?: number }
  | {
      type: 'reasoning_trace';
      intent: string;
      confidence: number;
      entities: Record<string, unknown>;
      reasoning: string;
    }
  | { type: 'response'; text: string; language?: string; audio?: string | null }
  | { type: 'latency_metrics'; total_latency_ms: number; breakdown: Record<string, number> }
  | { type: 'error'; message: string };

export type PipelineStage =
  | 'speech'
  | 'stt'
  | 'language'
  | 'llm'
  | 'tools'
  | 'tts'
  | 'audio'
  | 'idle';

export type VoiceStatus =
  | 'initializing'
  | 'ready'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'error'
  | 'disconnected';
