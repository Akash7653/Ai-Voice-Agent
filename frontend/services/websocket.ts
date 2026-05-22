/**
 * Enhanced WebSocket service with:
 * - Auto reconnect
 * - Exponential backoff
 * - Heartbeat ping/pong
 * - Binary audio streaming
 * - Connection recovery
 * - Safe JSON parsing
 * - Production-ready WebSocket support
 */

export interface WebSocketConfig {
  maxRetries?: number;
  retryDelayMs?: number;
  heartbeatIntervalMs?: number;
  connectionTimeoutMs?: number;
}

export class EnhancedWebSocket {
  private ws: WebSocket | null = null;
  private url: string;

  private config: Required<WebSocketConfig>;

  private retryCount = 0;

  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  private connectionTimeout: ReturnType<typeof setTimeout> | null = null;

  private isManualClose = false;

  private messageHandlers: Map<string, (data: any) => void> =
    new Map();

  private errorHandlers: ((error: Error) => void)[] = [];

  private reconnectHandlers: (() => void)[] = [];

  private disconnectHandlers: (() => void)[] = [];

  constructor(url: string, config: WebSocketConfig = {}) {
    this.url = url;

    this.config = {
      maxRetries: config.maxRetries ?? 5,
      retryDelayMs: config.retryDelayMs ?? 1000,
      heartbeatIntervalMs:
        config.heartbeatIntervalMs ?? 30000,
      connectionTimeoutMs:
        config.connectionTimeoutMs ?? 10000,
    };
  }

  /**
   * Connect to WebSocket
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.isManualClose = false;

        this.ws = new WebSocket(this.url);

        /**
         * Connection timeout
         */
        this.connectionTimeout = setTimeout(() => {
          reject(
            new Error('WebSocket connection timeout')
          );
        }, this.config.connectionTimeoutMs);

        /**
         * Connected
         */
        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');

          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
          }

          this.retryCount = 0;

          this.startHeartbeat();

          this.reconnectHandlers.forEach((handler) =>
            handler()
          );

          resolve();
        };

        /**
         * Incoming messages
         */
        this.ws.onmessage = (event) => {
          try {
            /**
             * Ignore binary messages here
             */
            if (typeof event.data !== 'string') {
              return;
            }

            const data = JSON.parse(event.data);

            /**
             * Heartbeat pong
             */
            if (data.type === 'pong') {
              console.debug(
                '[WebSocket] Pong received'
              );
              return;
            }

            /**
             * Route message
             */
            const handler = this.messageHandlers.get(
              data.type
            );

            if (handler) {
              handler(data);
            } else {
              console.warn(
                `[WebSocket] No handler for message type: ${data.type}`
              );
            }
          } catch (error) {
            console.error(
              '[WebSocket] Failed to parse message:',
              event.data
            );
          }
        };

        /**
         * Error handling
         */
        this.ws.onerror = () => {
          console.error('[WebSocket] Connection error');

          this.errorHandlers.forEach((handler) =>
            handler(
              new Error('WebSocket connection error')
            )
          );
        };

        /**
         * Connection closed
         */
        this.ws.onclose = () => {
          console.warn('[WebSocket] Connection closed');

          this.stopHeartbeat();

          this.disconnectHandlers.forEach((handler) =>
            handler()
          );

          /**
           * Auto reconnect
           */
          if (
            !this.isManualClose &&
            this.retryCount < this.config.maxRetries
          ) {
            this.retryCount++;

            const delay =
              this.config.retryDelayMs *
              Math.pow(2, this.retryCount - 1);

            console.log(
              `[WebSocket] Reconnecting in ${delay}ms (${this.retryCount}/${this.config.maxRetries})`
            );

            this.reconnectTimer = setTimeout(() => {
              this.connect().catch(console.error);
            }, delay);
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

      console.debug(
        `[WebSocket] Sent audio: ${audioData.byteLength} bytes`
      );
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Send JSON message
   */
  sendMessage(type: string, data: any = {}): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type,
          ...data,
        })
      );
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Register message handler
   */
  onMessage(
    type: string,
    handler: (data: any) => void
  ): void {
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
   * Check connection state
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Graceful close
   */
  close(): void {
    this.isManualClose = true;

    this.stopHeartbeat();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }

    if (this.ws) {
      this.ws.close();
    }

    console.log('[WebSocket] Closed manually');
  }

  /**
   * Heartbeat ping
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage('ping');

        console.debug(
          '[WebSocket] Heartbeat ping'
        );
      }
    }, this.config.heartbeatIntervalMs);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);

      this.heartbeatTimer = null;
    }
  }
}

/**
 * Create production-safe websocket URL
 */
export function createWebSocketUrl(
  apiUrl: string,
  patientId: string
): string {
  const wsProtocol = apiUrl.startsWith('https')
    ? 'wss'
    : 'ws';

  return `${wsProtocol}://${apiUrl.replace(
    /^https?:\/\//,
    ''
  )}/ws/voice/${patientId}`;
}