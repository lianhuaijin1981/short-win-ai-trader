/**
 * 实时数据监控组件
 * 展示如何使用WebSocket实时推送数据
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../services/websocket';
import type { ChannelType } from '../services/websocket';

// ── 样式 ──────────────────────────────────────────────────────────

const styles = {
  container: {
    padding: '16px',
    backgroundColor: '#1a1a2e',
    borderRadius: '8px',
    color: '#fff',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDot: (connected: boolean) => ({
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: connected ? '#00ff88' : '#ff4444',
  }),
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '12px',
  },
  card: {
    padding: '12px',
    backgroundColor: '#16213e',
    borderRadius: '6px',
    border: '1px solid #0f3460',
  },
  cardTitle: {
    fontSize: '14px',
    color: '#888',
    marginBottom: '8px',
  },
  cardValue: (positive: boolean) => ({
    fontSize: '24px',
    fontWeight: 'bold',
    color: positive ? '#00ff88' : '#ff4444',
  }),
  cardChange: (positive: boolean) => ({
    fontSize: '12px',
    color: positive ? '#00ff88' : '#ff4444',
  }),
  log: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#0f0f23',
    borderRadius: '6px',
    maxHeight: '200px',
    overflowY: 'auto' as const,
    fontSize: '12px',
    fontFamily: 'monospace',
  },
  logEntry: {
    padding: '4px 0',
    borderBottom: '1px solid #333',
  },
  button: {
    padding: '8px 16px',
    backgroundColor: '#0f3460',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  channelButtons: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap' as const,
    marginBottom: '16px',
  },
};

// ── 组件 ──────────────────────────────────────────────────────────

interface RealtimeMonitorProps {
  watchList?: string[];
  showLog?: boolean;
}

const RealtimeMonitor: React.FC<RealtimeMonitorProps> = ({
  watchList = ['000001.SZ', '600000.SH', '000002.SZ'],
  showLog = true,
}) => {
  const [logs, setLogs] = useState<Array<{ time: string; channel: string; data: any }>>([]);
  const [marketIndex, setMarketIndex] = useState<any[]>([]);
  const [realtimeData, setRealtimeData] = useState<any[]>([]);
  const [subscribedChannels, setSubscribedChannels] = useState<ChannelType[]>(['market_index']);

  // 使用WebSocket Hook
  const {
    connected,
    socketId,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    getRealtime,
    lastMessages,
  } = useWebSocket({
    channels: ['market_index'],
    autoConnect: true,
    onMessage: (channel, data) => {
      // 添加日志
      setLogs((prev) => [
        { time: new Date().toLocaleTimeString(), channel, data },
        ...prev.slice(0, 49), // 保留最近50条
      ]);

      // 处理不同频道数据
      if (channel === 'market_index' && data.data) {
        setMarketIndex(data.data);
      } else if (channel === 'stock_realtime' && data.data) {
        setRealtimeData(data.data);
      }
    },
  });

  // 订阅频道
  const handleSubscribe = useCallback((channel: ChannelType) => {
    subscribe(channel);
    setSubscribedChannels((prev) => [...prev, channel]);
  }, [subscribe]);

  // 取消订阅
  const handleUnsubscribe = useCallback((channel: ChannelType) => {
    unsubscribe(channel);
    setSubscribedChannels((prev) => prev.filter((c) => c !== channel));
  }, [unsubscribe]);

  // 获取实时行情
  const handleGetRealtime = useCallback(() => {
    getRealtime(watchList);
  }, [getRealtime, watchList]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      // 可以选择断开连接或保持连接
    };
  }, []);

  const channels: ChannelType[] = [
    'market_index',
    'stock_realtime',
    'limit_up',
    'moneyflow',
    'northbound',
  ];

  return (
    <div style={styles.container}>
      {/* 头部状态 */}
      <div style={styles.header}>
        <div style={styles.status}>
          <div style={styles.statusDot(connected)} />
          <span>{connected ? '已连接' : '未连接'}</span>
          {socketId && <span style={{ color: '#666', fontSize: '12px' }}>ID: {socketId}</span>}
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button style={styles.button} onClick={connected ? disconnect : connect}>
            {connected ? '断开' : '连接'}
          </button>
          <button style={styles.button} onClick={handleGetRealtime}>
            刷新行情
          </button>
        </div>
      </div>

      {/* 频道订阅 */}
      <div style={styles.channelButtons}>
        {channels.map((channel) => {
          const isSubscribed = subscribedChannels.includes(channel);
          return (
            <button
              key={channel}
              style={{
                ...styles.button,
                backgroundColor: isSubscribed ? '#00ff88' : '#0f3460',
                color: isSubscribed ? '#000' : '#fff',
              }}
              onClick={() => (isSubscribed ? handleUnsubscribe(channel) : handleSubscribe(channel))}
            >
              {isSubscribed ? '✓ ' : ''}{channel}
            </button>
          );
        })}
      </div>

      {/* 大盘指数 */}
      {marketIndex.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ color: '#888', fontSize: '14px', marginBottom: '8px' }}>大盘指数</h3>
          <div style={styles.grid}>
            {marketIndex.slice(0, 6).map((item, index) => {
              const isPositive = (item.pct_chg || 0) >= 0;
              return (
                <div key={index} style={styles.card}>
                  <div style={styles.cardTitle}>{item.ts_code || '指数'}</div>
                  <div style={styles.cardValue(isPositive)}>
                    {item.close?.toFixed(2) || '--'}
                  </div>
                  <div style={styles.cardChange(isPositive)}>
                    {item.pct_chg?.toFixed(2) || '0.00'}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 实时行情 */}
      {realtimeData.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ color: '#888', fontSize: '14px', marginBottom: '8px' }}>实时行情</h3>
          <div style={styles.grid}>
            {realtimeData.map((item, index) => {
              const isPositive = (item.pct_chg || 0) >= 0;
              return (
                <div key={index} style={styles.card}>
                  <div style={styles.cardTitle}>{item.name || item.ts_code}</div>
                  <div style={styles.cardValue(isPositive)}>
                    {item.price?.toFixed(2) || '--'}
                  </div>
                  <div style={styles.cardChange(isPositive)}>
                    {item.pct_chg?.toFixed(2) || '0.00'}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 消息日志 */}
      {showLog && logs.length > 0 && (
        <div>
          <h3 style={{ color: '#888', fontSize: '14px', marginBottom: '8px' }}>
            消息日志 ({logs.length})
          </h3>
          <div style={styles.log}>
            {logs.map((log, index) => (
              <div key={index} style={styles.logEntry}>
                <span style={{ color: '#666' }}>[{log.time}]</span>{' '}
                <span style={{ color: '#00ff88' }}>{log.channel}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeMonitor;