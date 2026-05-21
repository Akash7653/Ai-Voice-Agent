/**
 * Enhanced WebSocket service with reconnection and heartbeat support
 */

export interface WebSocketConfig {
  maxRetries?: number;
  retryDelayMs?: number;
  heartbeatIntervalMs?: number;
  heartbeatTimeoutMs?: number;
}

export class EnhancedWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private config: Required<WebSocketConfig>;
  private retryCount = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private errorHandlers: ((error: Error) => void)[] = [];
  private reconnectHandlers: (() => void)[] = [];
  private disconnectHandlers: (() => void)[] = [];
  private isManualClose = false;

  constructor(url: string, config: WebSocketConfig = {}) {
    this.url = url;
    this.config = {
      maxRetries: config.maxRetries ?? 5,
      retryDelayMs: config.retryDelayMs ?? 1000,
      heartbeatIntervalMs: config.heartbeatIntervalMs ?? 30000,
      heartbeatTimeoutMs: config.heartbeatTimeoutMs ?? 5000,
    };
  }

  /**
   * Connect to WebSocket with automatic reconnection
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isManualClose = false;

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.retryCount = 0;
          this.startHeartbeat();
          this.reconnectHandlers.forEach(h => h());
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const handler = this.messageHandlers.get(data.type);
            if (handler) handler(data);
          } catch (e) {
            console.error('[WebSocket] Invalid message', event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.errorHandlers.forEach(h => h(new Error('WebSocket error')));
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Closed');
          this.stopHeartbeat();
          this.disconnectHandlers.forEach(h => h());
          
          if (!this.isManualClose && this.retryCount < this.config.maxRetries) {
            this.retryCount++;
            const delay = this.config.retryDelayMs * Math.pow(2, this.retryCount - 1);
            console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.retryCount}/${this.config.maxRetries})`);
            this.reconnectTimer = setTimeout(() => this.connect().catch(console.error), delay);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Send binary audio data
   */
  sendAudio(audioData: ArrayBuffer): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
      console.debug(`[WebSocket] Sent ${audioData.byteLength} bytes`);
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Send JSON message
   */
  sendMessage(type: string, data: any = {}): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Register message handler
   */
  onMessage(type: string, handler: (data: any) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Register error handler
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * Register reconnect handler
   */
  onReconnect(handler: () => void): void {
    this.reconnectHandlers.push(handler);
  }

  /**
   * Register disconnect handler
   */
  onDisconnect(handler: () => void): void {
    this.disconnectHandlers.push(handler);
  }

  /**
   * Get connection state
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Gracefully close connection
   */
  close(): void {
    this.isManualClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.heartbeatTimer) clearTimeout(this.heartbeatTimer);
    if (this.ws) this.ws.close();
  }

  /**
   * Start heartbeat to detect stale connections
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage('ping');
        console.debug('[WebSocket] Heartbeat ping');
      }
    }, this.config.heartbeatIntervalMs);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}
