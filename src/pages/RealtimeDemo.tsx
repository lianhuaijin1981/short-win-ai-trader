/**
 * WebSocket实时推送 & PostgreSQL 演示页面
 * 展示WebSocket实时数据接收和数据库存储功能
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from '@/services/websocket';
import type { ChannelType, WebSocketMessage } from '@/services/websocket';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wifi,
  WifiOff,
  Database,
  Activity,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Clock,
  RefreshCw,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Server,
  MessageSquare,
  Settings,
  Play,
  Square,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ── 类型定义 ──────────────────────────────────────────────────────

interface RealtimeStock {
  ts_code: string;
  name: string;
  price: number;
  change: number;
  pct_chg: number;
  vol: number;
  amount: number;
  timestamp: string;
}

interface MarketIndexData {
  ts_code: string;
  name: string;
  close: number;
  pct_chg: number;
  change: number;
}

interface MessageLog {
  id: number;
  time: string;
  channel: string;
  type: string;
  data: any;
}

interface DBStats {
  totalStocks: number;
  todayRecords: number;
  realtimeCount: number;
  lastSync: string;
}

// ── 模拟数据 ──────────────────────────────────────────────────────

const WATCH_LIST = [
  { code: '000001.SZ', name: '平安银行' },
  { code: '600000.SH', name: '浦发银行' },
  { code: '000002.SZ', name: '万科A' },
  { code: '600519.SH', name: '贵州茅台' },
  { code: '000858.SZ', name: '五粮液' },
  { code: '688981.SH', name: '中芯国际' },
];

const INDEX_LIST = [
  { code: '000001.SH', name: '上证指数' },
  { code: '399001.SZ', name: '深证成指' },
  { code: '399006.SZ', name: '创业板指' },
  { code: '000300.SH', name: '沪深300' },
];

// ── 工具函数 ──────────────────────────────────────────────────────

function formatNumber(num: number, decimals: number = 2): string {
  if (num === null || num === undefined) return '--';
  return num.toFixed(decimals);
}

function formatVolume(num: number): string {
  if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿';
  if (num >= 10000) return (num / 10000).toFixed(2) + '万';
  return num.toFixed(0);
}

// ── 子组件 ────────────────────────────────────────────────────────

// 连接状态指示器
function ConnectionStatus({ connected, socketId }: { connected: boolean; socketId?: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-[#141e33] rounded-lg">
      <div className="flex items-center gap-2">
        {connected ? (
          <Wifi className="w-4 h-4 text-green-400" />
        ) : (
          <WifiOff className="w-4 h-4 text-red-400" />
        )}
        <span className={cn(
          'text-sm font-medium',
          connected ? 'text-green-400' : 'text-red-400'
        )}>
          {connected ? '已连接' : '未连接'}
        </span>
      </div>
      {socketId && (
        <span className="text-xs text-slate-500 font-mono">ID: {socketId}</span>
      )}
    </div>
  );
}

// 频道订阅按钮
function ChannelButton({
  channel,
  subscribed,
  onClick,
}: {
  channel: ChannelType;
  subscribed: boolean;
  onClick: () => void;
}) {
  const channelLabels: Record<ChannelType, string> = {
    market_index: '大盘指数',
    stock_realtime: '实时行情',
    limit_up: '涨停板',
    limit_down: '跌停板',
    moneyflow: '资金流向',
    news: '新闻',
    northbound: '北向资金',
    system: '系统',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200',
        subscribed
          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
          : 'bg-[#141e33] text-slate-400 border border-slate-700 hover:border-slate-500'
      )}
    >
      {subscribed && <span className="mr-1">✓</span>}
      {channelLabels[channel] || channel}
    </button>
  );
}

// 股票行情卡片
function StockCard({ stock }: { stock: RealtimeStock }) {
  const isPositive = stock.pct_chg >= 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-3 bg-[#141e33] rounded-lg border border-slate-800 hover:border-slate-600 transition-colors"
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="text-sm font-medium text-slate-200">{stock.name}</div>
          <div className="text-xs text-slate-500 font-mono">{stock.ts_code}</div>
        </div>
        <div className={cn(
          'px-2 py-0.5 rounded text-xs font-medium',
          isPositive ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
        )}>
          {isPositive ? '+' : ''}{formatNumber(stock.pct_chg)}%
        </div>
      </div>
      <div className="flex justify-between items-end">
        <div className="text-lg font-bold text-slate-100">
          {formatNumber(stock.price)}
        </div>
        <div className="text-xs text-slate-500">
          量: {formatVolume(stock.vol)}
        </div>
      </div>
    </motion.div>
  );
}

// 指数行情卡片
function IndexCard({ index }: { index: MarketIndexData }) {
  const isPositive = index.pct_chg >= 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-4 bg-[#141e33] rounded-lg border border-slate-800"
    >
      <div className="flex justify-between items-start mb-3">
        <div className="text-sm font-medium text-slate-200">{index.name}</div>
        <div className={cn(
          'flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
          isPositive ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
        )}>
          {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {isPositive ? '+' : ''}{formatNumber(index.pct_chg)}%
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-100 mb-1">
        {formatNumber(index.close)}
      </div>
      <div className={cn(
        'text-sm',
        isPositive ? 'text-red-400' : 'text-green-400'
      )}>
        {isPositive ? '+' : ''}{formatNumber(index.change)}
      </div>
    </motion.div>
  );
}

// 消息日志
function MessageLogPanel({ logs }: { logs: MessageLog[] }) {
  const logRef = useRef<HTMLDivElement>(null);

  return (
    <div className="bg-[#0f0f23] rounded-lg border border-slate-800">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800">
        <MessageSquare className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-300">消息日志</span>
        <span className="ml-auto text-xs text-slate-500">{logs.length} 条</span>
      </div>
      <div ref={logRef} className="h-64 overflow-y-auto p-2 font-mono text-xs">
        <AnimatePresence>
          {logs.slice(0, 50).map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="py-1.5 px-2 border-b border-slate-800/50 last:border-0"
            >
              <span className="text-slate-500">[{log.time}]</span>{' '}
              <span className={cn(
                'px-1.5 py-0.5 rounded text-xs',
                log.channel === 'system' ? 'bg-blue-500/20 text-blue-400' :
                log.channel === 'market_index' ? 'bg-purple-500/20 text-purple-400' :
                log.channel === 'stock_realtime' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-slate-500/20 text-slate-400'
              )}>
                {log.channel}
              </span>
              {log.type && (
                <span className="text-slate-500 ml-1">/{log.type}</span>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// 数据库统计面板
function DBStatsPanel({ stats }: { stats: DBStats }) {
  const statItems = [
    { label: '股票总数', value: stats.totalStocks, icon: Database, color: 'text-blue-400' },
    { label: '今日记录', value: stats.todayRecords, icon: Clock, color: 'text-green-400' },
    { label: '实时数据', value: stats.realtimeCount, icon: Activity, color: 'text-yellow-400' },
    { label: '最后同步', value: stats.lastSync, icon: Server, color: 'text-purple-400' },
  ];

  return (
    <div className="bg-[#141e33] rounded-lg border border-slate-800 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Database className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-300">数据库统计</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {statItems.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <item.icon className={cn('w-4 h-4', item.color)} />
            <div>
              <div className="text-xs text-slate-500">{item.label}</div>
              <div className={cn('text-sm font-medium', item.color)}>{item.value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────────────

export default function RealtimeDemo() {
  const [logs, setLogs] = useState<MessageLog[]>([]);
  const [stockData, setStockData] = useState<RealtimeStock[]>([]);
  const [indexData, setIndexData] = useState<MarketIndexData[]>([]);
  const [subscribedChannels, setSubscribedChannels] = useState<ChannelType[]>(['market_index', 'system']);
  const [isSyncing, setIsSyncing] = useState(false);
  const [dbStats, setDbStats] = useState<DBStats>({
    totalStocks: 5234,
    todayRecords: 1256,
    realtimeCount: 0,
    lastSync: '--:--:--',
  });
  
  const logIdRef = useRef(0);

  // WebSocket Hook
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
    channels: ['market_index', 'system'],
    autoConnect: true,
    onMessage: (channel, data) => {
      logIdRef.current += 1;
      setLogs((prev) => [
        {
          id: logIdRef.current,
          time: new Date().toLocaleTimeString(),
          channel,
          type: data.type || '',
          data: data.data,
        },
        ...prev.slice(0, 99),
      ]);

      // 处理不同频道数据
      if (channel === 'market_index' && data.data) {
        const indices = data.data.map((item: any) => ({
          ts_code: item.ts_code || '',
          name: item.ts_code === '000001.SH' ? '上证指数' : 
                item.ts_code === '399001.SZ' ? '深证成指' :
                item.ts_code === '399006.SZ' ? '创业板指' : '沪深300',
          close: item.close || 0,
          pct_chg: item.pct_chg || 0,
          change: item.change || 0,
        }));
        if (indices.length > 0) setIndexData(indices);
      } else if (channel === 'stock_realtime' && data.data) {
        const stocks = data.data.map((item: any) => ({
          ts_code: item.ts_code || '',
          name: item.name || '',
          price: item.price || 0,
          change: item.change || 0,
          pct_chg: item.pct_chg || 0,
          vol: item.vol || 0,
          amount: item.amount || 0,
          timestamp: item.timestamp || '',
        }));
        setStockData(stocks);
        setDbStats((prev) => ({ ...prev, realtimeCount: stocks.length }));
      }
    },
  });

  // 切换订阅
  const toggleChannel = useCallback((channel: ChannelType) => {
    if (subscribedChannels.includes(channel)) {
      unsubscribe(channel);
      setSubscribedChannels((prev) => prev.filter((c) => c !== channel));
    } else {
      subscribe(channel);
      setSubscribedChannels((prev) => [...prev, channel]);
    }
  }, [subscribedChannels, subscribe, unsubscribe]);

  // 获取实时行情
  const handleGetRealtime = useCallback(() => {
    const codes = WATCH_LIST.map((w) => w.code);
    getRealtime(codes);
  }, [getRealtime]);

  // 模拟同步
  const handleSync = useCallback(() => {
    setIsSyncing(true);
    setTimeout(() => {
      setDbStats((prev) => ({
        ...prev,
        todayRecords: prev.todayRecords + Math.floor(Math.random() * 100),
        lastSync: new Date().toLocaleTimeString(),
      }));
      setIsSyncing(false);
    }, 2000);
  }, []);

  // 生成模拟数据（用于演示）
  useEffect(() => {
    if (!connected) return;

    // 模拟指数数据
    const mockIndices: MarketIndexData[] = INDEX_LIST.map((idx) => {
      const baseValues: Record<string, number> = {
        '000001.SH': 3285.42,
        '399001.SZ': 10562.18,
        '399006.SZ': 2085.67,
        '000300.SH': 3892.55,
      };
      const base = baseValues[idx.code] || 3000;
      const change = (Math.random() - 0.5) * 50;
      const pctChange = (change / base) * 100;
      return {
        ts_code: idx.code,
        name: idx.name,
        close: base + change,
        pct_chg: pctChange,
        change: change,
      };
    });
    setIndexData(mockIndices);

    // 模拟股票数据
    const mockStocks: RealtimeStock[] = WATCH_LIST.map((stock) => {
      const basePrices: Record<string, number> = {
        '000001.SZ': 11.25,
        '600000.SH': 10.85,
        '000002.SZ': 8.92,
        '600519.SH': 1685.50,
        '000858.SZ': 142.35,
        '688981.SH': 58.75,
      };
      const base = basePrices[stock.code] || 10;
      const change = (Math.random() - 0.5) * 2;
      const pctChange = (change / base) * 100;
      return {
        ts_code: stock.code,
        name: stock.name,
        price: base + change,
        change: change,
        pct_chg: pctChange,
        vol: Math.random() * 1000000,
        amount: Math.random() * 100000000,
        timestamp: new Date().toISOString(),
      };
    });
    setStockData(mockStocks);
    setDbStats((prev) => ({ ...prev, realtimeCount: mockStocks.length }));
  }, [connected]);

  const channels: ChannelType[] = [
    'market_index',
    'stock_realtime',
    'limit_up',
    'moneyflow',
    'northbound',
  ];

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">WebSocket实时推送 & PostgreSQL</h1>
          <p className="text-sm text-slate-500 mt-1">实时数据推送 · 数据库持久化 · 盘中监控</p>
        </div>
        <div className="flex items-center gap-3">
          <ConnectionStatus connected={connected} socketId={socketId} />
          <button
            onClick={connected ? disconnect : connect}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              connected
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            )}
          >
            {connected ? '断开' : '连接'}
          </button>
        </div>
      </div>

      {/* 频道订阅 */}
      <div className="bg-[#141e33] rounded-lg border border-slate-800 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium text-slate-300">频道订阅</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {channels.map((channel) => (
            <ChannelButton
              key={channel}
              channel={channel}
              subscribed={subscribedChannels.includes(channel)}
              onClick={() => toggleChannel(channel)}
            />
          ))}
        </div>
      </div>

      {/* 大盘指数 */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-medium text-slate-300">大盘指数</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {indexData.map((index) => (
            <IndexCard key={index.ts_code} index={index} />
          ))}
        </div>
      </div>

      {/* 实时行情 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-green-400" />
            <h2 className="text-sm font-medium text-slate-300">实时行情</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGetRealtime}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-md text-sm hover:bg-blue-500/30 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              刷新
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stockData.map((stock) => (
            <StockCard key={stock.ts_code} stock={stock} />
          ))}
        </div>
      </div>

      {/* 数据库统计 + 消息日志 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <DBStatsPanel stats={dbStats} />
          
          {/* 同步控制 */}
          <div className="bg-[#141e33] rounded-lg border border-slate-800 p-4">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-300">数据同步</span>
            </div>
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                isSyncing
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
              )}
            >
              {isSyncing ? (
                <>
                  <Square className="w-4 h-4" />
                  同步中...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  立即同步
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="lg:col-span-2">
          <MessageLogPanel logs={logs} />
        </div>
      </div>

      {/* 关注列表 */}
      <div className="bg-[#141e33] rounded-lg border border-slate-800 p-4">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-medium text-slate-300">关注列表</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 border-b border-slate-800">
                <th className="text-left py-2 px-3 font-medium">代码</th>
                <th className="text-left py-2 px-3 font-medium">名称</th>
                <th className="text-right py-2 px-3 font-medium">最新价</th>
                <th className="text-right py-2 px-3 font-medium">涨跌幅</th>
                <th className="text-right py-2 px-3 font-medium">成交量</th>
                <th className="text-right py-2 px-3 font-medium">成交额</th>
              </tr>
            </thead>
            <tbody>
              {stockData.map((stock) => {
                const isPositive = stock.pct_chg >= 0;
                return (
                  <tr key={stock.ts_code} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-mono text-slate-400">{stock.ts_code}</td>
                    <td className="py-2 px-3 text-slate-200">{stock.name}</td>
                    <td className={cn('py-2 px-3 text-right font-mono', isPositive ? 'text-red-400' : 'text-green-400')}>
                      {formatNumber(stock.price)}
                    </td>
                    <td className={cn('py-2 px-3 text-right font-mono', isPositive ? 'text-red-400' : 'text-green-400')}>
                      {isPositive ? '+' : ''}{formatNumber(stock.pct_chg)}%
                    </td>
                    <td className="py-2 px-3 text-right text-slate-400">{formatVolume(stock.vol)}</td>
                    <td className="py-2 px-3 text-right text-slate-400">{formatVolume(stock.amount)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}