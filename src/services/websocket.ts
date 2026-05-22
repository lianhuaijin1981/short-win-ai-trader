/**
 * WebSocket实时推送客户端
 * 用于接收服务端推送的盘中数据实时更新
 * 
 * 支持频道:
 * - market_index: 大盘指数实时更新
 * - stock_realtime: 个股实时行情
 * - limit_up: 涨停板动态
 * - limit_down: 跌停板动态
 * - moneyflow: 资金流向更新
 * - news: 新闻推送
 * - northbound: 北向资金
 * - system: 系统通知
 */

import { io, Socket } from 'socket.io-client';

// ── 类型定义 ──────────────────────────────────────────────────────

export type ChannelType = 
  | 'market_index'
  | 'stock_realtime'
  | 'limit_up'
  | 'limit_down'
  | 'moneyflow'
  | 'news'
  | 'northbound'
  | 'system';

export interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
  timestamp: string;
  sid?: string;
  rooms?: string[];
}

export interface WebSocketStats {
  connected_clients: number;
  rooms: Record<string, number>;
  pusher_running: boolean;
}

export type MessageHandler = (message: WebSocketMessage) => void;

// ── 配置 ──────────────────────────────────────────────────────────

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5001';

const DEFAULT_CHANNELS: ChannelType[] = ['market_index', 'system'];

const RECONNECT_INTERVAL = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

// ── WebSocket客户端类 ────────────────────────────────────────────

class WebSocketClient {
  private socket: Socket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private isManualDisconnect = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private isConnected = false;

  // 状态回调
  private onStateChange: ((connected: boolean) => void) | null = null;

  /**
   * 连接WebSocket
   */
  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.socket?.connected) {
        resolve(true);
        return;
      }

      this.isManualDisconnect = false;

      this.socket = io(WS_URL, {
        transports: ['websocket', 'polling'],
        reconnection: false, // 手动控制重连
        timeout: 10000,
      });

      // 连接成功
      this.socket.on('connect', () => {
        console.log('[WS] 连接成功');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyStateChange(true);
        
        // 启动心跳
        this.startPing();
        
        resolve(true);
      });

      // 接收系统消息
      this.socket.on('system', (data: WebSocketMessage) => {
        this.handleMessage('system', data);
      });

      // 接收各频道数据
      const channels: ChannelType[] = [
        'market_index',
        'stock_realtime',
        'limit_up',
        'limit_down',
        'moneyflow',
        'news',
        'northbound',
      ];

      channels.forEach((channel) => {
        this.socket!.on(channel, (data: WebSocketMessage) => {
          this.handleMessage(channel, data);
        });
      });

      // 实时行情响应
      this.socket.on('realtime_response', (data: WebSocketMessage) => {
        this.handleMessage('realtime_response', data);
      });

      // pong响应
      this.socket.on('pong', (data: WebSocketMessage) => {
        this.handleMessage('pong', data);
      });

      // 连接错误
      this.socket.on('connect_error', (error) => {
        console.error('[WS] 连接错误:', error);
        this.isConnected = false;
        this.notifyStateChange(false);
        this.scheduleReconnect();
        resolve(false);
      });

      // 断开连接
      this.socket.on('disconnect', (reason) => {
        console.log('[WS] 断开连接:', reason);
        this.isConnected = false;
        this.notifyStateChange(false);
        this.stopPing();
        
        if (!this.isManualDisconnect) {
          this.scheduleReconnect();
        }
      });
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualDisconnect = true;
    this.stopPing();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    this.handlers.clear();
    this.isConnected = false;
  }

  /**
   * 订阅频道
   */
  subscribe(channels: ChannelType | ChannelType[]): void {
    if (!this.socket?.connected) {
      console.warn('[WS] 未连接，无法订阅');
      return;
    }

    const channelList = Array.isArray(channels) ? channels : [channels];
    
    this.socket.emit('subscribe', { rooms: channelList });
    
    // 注册频道处理器
    channelList.forEach((channel) => {
      if (!this.handlers.has(channel)) {
        this.handlers.set(channel, new Set());
      }
    });
  }

  /**
   * 取消订阅
   */
  unsubscribe(channels: ChannelType | ChannelType[]): void {
    if (!this.socket?.connected) {
      console.warn('[WS] 未连接，无法取消订阅');
      return;
    }

    const channelList = Array.isArray(channels) ? channels : [channels];
    this.socket.emit('unsubscribe', { rooms: channelList });
  }

  /**
   * 添加消息处理器
   */
  on(channel: ChannelType | 'realtime_response' | 'pong', handler: MessageHandler): void {
    if (!this.handlers.has(channel)) {
      this.handlers.set(channel, new Set());
    }
    this.handlers.get(channel)!.add(handler);
  }

  /**
   * 移除消息处理器
   */
  off(channel: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(channel);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 清除某频道所有处理器
   */
  clearHandlers(channel: string): void {
    this.handlers.delete(channel);
  }

  /**
   * 获取实时行情
   */
  getRealtime(tsCodes: string[]): void {
    if (!this.socket?.connected) {
      console.warn('[WS] 未连接，无法获取实时行情');
      return;
    }
    this.socket.emit('get_realtime', { ts_codes: tsCodes });
  }

  /**
   * 发送心跳
   */
  private sendPing(): void {
    if (this.socket?.connected) {
      this.socket.emit('ping', {});
    }
  }

  /**
   * 启动心跳
   */
  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => {
      this.sendPing();
    }, 30000); // 30秒心跳
  }

  /**
   * 停止心跳
   */
  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  /**
   * 处理消息
   */
  private handleMessage(channel: string, data: WebSocketMessage): void {
    const handlers = this.handlers.get(channel);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`[WS] 处理${channel}消息错误:`, error);
        }
      });
    }
  }

  /**
   * 通知状态变化
   */
  private notifyStateChange(connected: boolean): void {
    if (this.onStateChange) {
      this.onStateChange(connected);
    }
  }

  /**
   * 设置状态变化回调
   */
  setStateChangeListener(listener: (connected: boolean) => void): void {
    this.onStateChange = listener;
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    if (this.isManualDisconnect) return;
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('[WS] 达到最大重连次数');
      return;
    }

    this.reconnectAttempts++;
    const delay = RECONNECT_INTERVAL * this.reconnectAttempts;
    
    console.log(`[WS] ${delay}ms后尝试重连 (${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * 获取连接状态
   */
  get connected(): boolean {
    return this.isConnected;
  }

  /**
   * 获取Socket ID
   */
  get socketId(): string | undefined {
    return this.socket?.id;
  }
}

// ── 单例导出 ──────────────────────────────────────────────────────

export const wsClient = new WebSocketClient();

// ── React Hook ────────────────────────────────────────────────────

import { useEffect, useRef, useCallback, useState } from 'react';

export interface UseWebSocketOptions {
  channels?: ChannelType[];
  autoConnect?: boolean;
  onMessage?: (channel: string, data: WebSocketMessage) => void;
}

export interface UseWebSocketReturn {
  connected: boolean;
  socketId: string | undefined;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  subscribe: (channels: ChannelType | ChannelType[]) => void;
  unsubscribe: (channels: ChannelType | ChannelType[]) => void;
  getRealtime: (tsCodes: string[]) => void;
  lastMessages: Record<string, WebSocketMessage | null>;
}

/**
 * WebSocket React Hook
 * 用于在组件中使用WebSocket连接
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    channels = DEFAULT_CHANNELS,
    autoConnect = true,
    onMessage,
  } = options;

  const [connected, setConnected] = useState(false);
  const [socketId, setSocketId] = useState<string | undefined>();
  const [lastMessages, setLastMessages] = useState<Record<string, WebSocketMessage | null>>({});
  
  const handlersRef = useRef<Map<string, MessageHandler>>(new Map());
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // 连接WebSocket
  const connect = useCallback(async (): Promise<boolean> => {
    const success = await wsClient.connect();
    if (success) {
      setSocketId(wsClient.socketId);
      // 自动订阅默认频道
      wsClient.subscribe(channels);
    }
    return success;
  }, [channels]);

  // 断开连接
  const disconnect = useCallback(() => {
    wsClient.disconnect();
    setConnected(false);
    setSocketId(undefined);
  }, []);

  // 订阅频道
  const subscribe = useCallback((chs: ChannelType | ChannelType[]) => {
    wsClient.subscribe(chs);
  }, []);

  // 取消订阅
  const unsubscribe = useCallback((chs: ChannelType | ChannelType[]) => {
    wsClient.unsubscribe(chs);
  }, []);

  // 获取实时行情
  const getRealtime = useCallback((tsCodes: string[]) => {
    wsClient.getRealtime(tsCodes);
  }, []);

  // 设置状态监听
  useEffect(() => {
    wsClient.setStateChangeListener((isConnected) => {
      setConnected(isConnected);
      if (isConnected) {
        setSocketId(wsClient.socketId);
      }
    });
  }, []);

  // 注册消息处理器
  useEffect(() => {
    const allChannels = [...channels, 'system', 'realtime_response'];
    
    allChannels.forEach((channel) => {
      const handler = (data: WebSocketMessage) => {
        setLastMessages((prev) => ({
          ...prev,
          [channel]: data,
        }));
        
        // 调用外部回调
        if (optionsRef.current.onMessage) {
          optionsRef.current.onMessage(channel, data);
        }
      };
      
      handlersRef.current.set(channel, handler);
      wsClient.on(channel as any, handler);
    });

    // 清理
    return () => {
      allChannels.forEach((channel) => {
        const handler = handlersRef.current.get(channel);
        if (handler) {
          wsClient.off(channel, handler);
        }
      });
    };
  }, [channels]);

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      if (autoConnect) {
        // 组件卸载时不断开，保持连接
        // wsClient.disconnect();
      }
    };
  }, [autoConnect, connect]);

  return {
    connected,
    socketId,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    getRealtime,
    lastMessages,
  };
}

// ── 工具函数 ──────────────────────────────────────────────────────

/**
 * 获取WebSocket统计信息
 */
export async function getWebSocketStats(): Promise<WebSocketStats | null> {
  try {
    const response = await fetch(`${WS_URL}/api/ws/stats`);
    const result = await response.json();
    return result.data;
  } catch (error) {
    console.error('[WS] 获取统计信息失败:', error);
    return null;
  }
}

/**
 * 手动广播消息（需要权限）
 */
export async function broadcastMessage(
  event: string,
  message: string,
  room?: string
): Promise<boolean> {
  try {
    const response = await fetch(`${WS_URL}/api/ws/broadcast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, message, room }),
    });
    const result = await response.json();
    return result.code === 0;
  } catch (error) {
    console.error('[WS] 广播消息失败:', error);
    return false;
  }
}

export default wsClient;