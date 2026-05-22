/*
 * Voice WebSocket client
 */

import { WebSocketMessage } from  '@/types';

export class VoiceClient {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private onMessage: (message: WebSocketMessage) => void = () => {};
  private onError: (error: string) => void = () => {};
  private onClose: () => void = () => {};
  private onConnectedCallback: () => void = () => {};

  constructor(
    private apiUrl: string,
    private patientId: string
  ) {
    this.apiUrl = apiUrl.replace('http', 'ws');
  }

  async connect(): Promise<string> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.apiUrl}/ws/voice/${this.patientId}`;
        console.log('Attempting WebSocket connection to:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);

        const connectionTimeout = setTimeout(() => {
          if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
            this.ws?.close();
            reject(new Error('WebSocket connection timeout after 10 seconds'));
          }
        }, 10000);

        this.ws.onopen = () => {
          clearTimeout(connectionTimeout);
        
          console.log('WebSocket connected successfully');
        
          this.onConnectedCallback();
        
          if (this.sessionId) {
            resolve(this.sessionId);
          }
        };

        this.ws.onmessage = (event) => {
          clearTimeout(connectionTimeout);
          const message = JSON.parse(event.data) as WebSocketMessage;

          if (message.type === 'session_start') {
            this.sessionId = message.session_id;
            resolve(this.sessionId);
          }

          this.onMessage(message);
        };

        this.ws.onerror = (error) => {
          clearTimeout(connectionTimeout);
          console.error('WebSocket error:', error);
          this.onError('WebSocket connection failed');
          reject(new Error('WebSocket error: Failed to establish connection'));
        };

        this.ws.onclose = () => {
          clearTimeout(connectionTimeout);
        
          console.log('WebSocket closed');
        
          this.ws = null;
        
          this.onClose();
        };
      } catch (error) {
        console.error('WebSocket connection exception:', error);
        reject(error);
      }
    });
  }

  async sendAudioChunk(audioData: ArrayBuffer): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(audioData);
  }

  async endAudio(): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(new ArrayBuffer(0));
  }

  onMessageReceived(handler: (message: WebSocketMessage) => void): void {
    this.onMessage = handler;
  }

  onErrorReceived(handler: (error: string) => void): void {
    this.onError = handler;
  }

  onConnectionClosed(handler: () => void): void {
    this.onClose = handler;
  }
  onConnected(handler: () => void): void {
    this.onConnectedCallback = handler;
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}

export type ApiResult<T = unknown> =
  | { success: true; data: T; [key: string]: unknown }
  | { success: false; error: string };

type FetchOptions = RequestInit & { throwOnError?: boolean };

export class APIClient {
  constructor(private baseUrl: string) {}

  private async fetchWithErrorHandling(
    url: string,
    options?: FetchOptions
  ): Promise<ApiResult> {
    const throwOnError = options?.throwOnError ?? false;
    const { throwOnError: _, ...fetchOpts } = options ?? {};

    try {
      const response = await fetch(url, fetchOpts);

      if (!response.ok) {
        const err = new Error(`HTTP ${response.status}: ${response.statusText}`);
        if (throwOnError) throw err;
        console.warn(`API call failed for ${url}:`, err.message);
        return { success: false, error: err.message };
      }

      return (await response.json()) as ApiResult;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed';
      if (throwOnError) throw error;
      console.warn(`API call failed for ${url}:`, message);
      return { success: false, error: message };
    }
  }

  async getAppointments(patientId: string, status?: string): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/appointments/${patientId}`);
    if (status) {
      url.searchParams.append('status', status);
    }

    return this.fetchWithErrorHandling(url.toString());
  }

  async createAppointment(payload: any): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/appointments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async rescheduleAppointment(appointmentId: string, payload: any): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/appointments/${appointmentId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async cancelAppointment(appointmentId: string): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/appointments/${appointmentId}`, {
      method: 'DELETE',
    });
  }

  async getDoctors(specialty?: string): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/doctors`);
    if (specialty) {
      url.searchParams.append('specialty', specialty);
    }

    return this.fetchWithErrorHandling(url.toString());
  }

  async getPatientInfo(patientId: string): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/patient/${patientId}`);
  }

  async updatePatientPreferences(patientId: string, preferences: any): Promise<ApiResult> {
    return this.fetchWithErrorHandling(
      `${this.baseUrl}/api/patient/${patientId}/preferences`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
        throwOnError: true,
      }
    );
  }

  async getSessionInfo(sessionId: string): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/session/${sessionId}`);
  }

  async getLatencyStats(patientId: string, limit: number = 100): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/latency-stats/${patientId}`);
    url.searchParams.append('limit', limit.toString());

    return this.fetchWithErrorHandling(url.toString());
  }

  async generateTTS(text: string, language: string = 'en', sessionId?: string): Promise<any> {
    return this.fetchWithErrorHandling(`${this.baseUrl}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language, session_id: sessionId }),
    });
  }
}
