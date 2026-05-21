// ═══════════════════════════════════════════════════════════════
// 盘中监控模块 — 主页面
// 整合5大核心模块：
// 1. 大盘&板块情绪全局监控
// 2. 主线题材+龙头梯队识别
// 3. 主升浪个股实时筛选+盘中预警
// 4. 持仓股实时盯盘系统
// 5. 复盘&回测系统
// ══════════════════════════════════════════════════════════════

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import {
  TrendingUp, TrendingDown, Activity, Zap, AlertTriangle, Bell,
  BarChart3, Play, Pause, RotateCcw, Eye,
  CheckCircle, XCircle, AlertCircle, ArrowUpRight, ArrowDownRight,
  Minus, Award, RefreshCw, AlertCircle as AlertCircleIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import DataCard from '@/components/DataCard';
import {
  SENTIMENT_PHASE_CONFIG,
  generateMarketMonitor, generateSectorStrength, generateSentimentDashboard,
  generateLeaderTiers,
  BUY_POINT_CONFIG,
  DEFAULT_FILTER,
  generateAlertSignals,
  generateHoldingStocks, generateHoldingAlerts,
  DEFAULT_TACTIC_PARAMS,
  generateBacktestResult, generateDailyReview, generateTradeLogs,
} from '@/data/intradayMonitor';
import type {
  SentimentPhase, MarketMonitor, SectorStrength, SentimentDashboard,
  LeaderTier, AlertSignal, FilterCondition,
  HoldingStock, HoldingAlert, HoldingAlertType,
  BacktestResult, DailyReview, TradeLog, TacticParams,
} from '@/data/intradayMonitor';

/* ─── Animation Variants ─── */
const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] } },
};

/* ─── 图标映射 ─── */
const phaseIconMap: Record<SentimentPhase, React.ElementType> = {
  '启动期': Play,
  '发酵期': RefreshCw,
  '主升期': TrendingUp,
  '退潮期': TrendingDown,
};

const alertTypeIconMap: Record<HoldingAlertType, React.ElementType> = {
  '趋势破位': ArrowDownRight,
  '量能异常': AlertTriangle,
  '板块退潮': TrendingDown,
  '止损提醒': AlertTriangle,
  '止盈提醒': CheckCircle,
  '逻辑失效': XCircle,
};

const urgencyColorMap: Record<string, string> = {
  '低': '#22c55e',
  '中': '#eab308',
  '高': '#ef4444',
  '紧急': '#dc2626',
};

/* ─── 情绪仪表盘 ─── */
function SentimentGauge({ phase, confidence }: { phase: SentimentPhase; confidence: number }) {
  const config = SENTIMENT_PHASE_CONFIG[phase];
  const Icon = phaseIconMap[phase];
  
  return (
    <div className="flex items-center gap-4">
      <div className="relative">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center border-2"
          style={{ borderColor: config.color, backgroundColor: config.bgColor }}
        >
          <Icon size={24} style={{ color: config.color }} />
        </div>
        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[#0d1526] flex items-center justify-center text-[10px] font-bold" style={{ color: config.color }}>
          {confidence}%
        </div>
      </div>
      <div>
        <div className="text-[18px] font-bold" style={{ color: config.color }}>{phase}</div>
        <div className="text-[12px] text-[#94a3b8]">{config.description}</div>
      </div>
    </div>
  );
}

/* ─── 大盘指标卡片 ─── */
function MarketMetricCard({ label, value, unit, trend, color }: {
  label: string; value: string | number; unit?: string; trend?: 'up' | 'down' | 'flat'; color: string;
}) {
  const TrendIcon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Minus;
  return (
    <div className="bg-[#141e33] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
      <div className="text-[11px] text-[#475569] mb-1">{label}</div>
      <div className="flex items-baseline gap-1">
        <span className="text-[20px] font-bold font-mono" style={{ color }}>{value}</span>
        {unit && <span className="text-[11px] text-[#475569]">{unit}</span>}
        {trend && <TrendIcon size={12} style={{ color: trend === 'up' ? '#ef4444' : trend === 'down' ? '#22c55e' : '#475569' }} />}
      </div>
    </div>
  );
}

/* ─── 板块强度条 ─── */
function SectorStrengthBar({ sector }: { sector: SectorStrength }) {
  const typeColor = sector.type === '主线' ? '#ef4444' : sector.type === '支线' ? '#eab308' : '#6b7280';
  const statusColor = sector.status === '主升' ? '#ef4444' : sector.status === '发酵' ? '#22c55e' : sector.status === '启动' ? '#3b82f6' : sector.status === '回流' ? '#8b5cf6' : '#6b7280';
  
  return (
    <motion.div
      variants={itemVariants}
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all duration-200',
        sector.isMainLine ? 'bg-[rgba(239,68,68,0.06)] border-[rgba(239,68,68,0.2)]' : 'bg-[#141e33] border-[rgba(148,163,184,0.06)]'
      )}
    >
      <div className="w-[100px] shrink-0">
        <div className="flex items-center gap-2">
          {sector.isMainLine && <span className="text-[10px] px-1 py-0.5 bg-[#ef4444] text-white rounded font-medium">主线</span>}
          <span className="text-[13px] font-medium text-[#f1f5f9] truncate">{sector.name}</span>
        </div>
      </div>
      
      <div className="w-[50px] text-center">
        <div className="text-[14px] font-bold text-[#ef4444] font-mono">{sector.limitUpCount}</div>
        <div className="text-[9px] text-[#475569]">涨停</div>
      </div>
      
      <div className="w-[80px]">
        <div className="flex gap-0.5">
          {sector.consecutiveBoardTiers.map((b, i) => (
            <span key={i} className="text-[9px] px-1 py-0.5 rounded bg-[rgba(239,68,68,0.15)] text-[#ef4444]">{b}板</span>
          ))}
        </div>
      </div>
      
      <div className="flex-1">
        <div className="h-2 bg-[#0f1929] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${sector.trendStrength}%` }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
            className="h-full rounded-full"
            style={{ backgroundColor: typeColor }}
          />
        </div>
        <div className="text-[9px] text-[#475569] text-right mt-0.5">{sector.trendStrength}</div>
      </div>
      
      <div className="w-[50px] text-center">
        <div className="text-[12px] font-mono" style={{ color: sector.sealRate > 70 ? '#22c55e' : '#eab308' }}>{sector.sealRate}%</div>
        <div className="text-[9px] text-[#475569]">封板</div>
      </div>
      
      <div className="w-[50px] text-center">
        <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: `${statusColor}20`, color: statusColor }}>
          {sector.status}
        </span>
      </div>
      
      <div className="w-[60px] text-right">
        <div className={cn('text-[12px] font-mono', sector.fundFlow > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
          {sector.fundFlow > 0 ? '+' : ''}{sector.fundFlow}亿
        </div>
      </div>
    </motion.div>
  );
}

/* ─── 龙头梯队卡片 ─── */
function LeaderTierCard({ tier }: { tier: LeaderTier }) {
  return (
    <div className="bg-[#141e33] rounded-lg border border-[rgba(148,163,184,0.06)] overflow-hidden">
      <div className="px-3 py-2 bg-[rgba(239,68,68,0.06)] border-b border-[rgba(148,163,184,0.06)]">
        <span className="text-[14px] font-bold text-[#ef4444]">{tier.boardCount}连板</span>
        <span className="text-[11px] text-[#475569] ml-2">({tier.stocks.length}只)</span>
      </div>
      <div className="p-2 space-y-1.5">
        {tier.stocks.map(stock => (
          <motion.div
            key={stock.code}
            whileHover={{ scale: 1.01 }}
            className="flex items-center gap-2 p-2 rounded hover:bg-[#1a2744] cursor-pointer transition-all"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-medium text-[#f1f5f9]">{stock.name}</span>
                <span className="text-[10px] text-[#475569] font-mono">{stock.code}</span>
                <span
                  className="text-[9px] px-1 py-0.5 rounded"
                  style={{
                    backgroundColor: stock.leaderType === '空间龙' ? 'rgba(239,68,68,0.15)' : stock.leaderType === '趋势龙' ? 'rgba(59,130,246,0.15)' : stock.leaderType === '补涨龙' ? 'rgba(234,179,8,0.15)' : 'rgba(107,114,128,0.15)',
                    color: stock.leaderType === '空间龙' ? '#ef4444' : stock.leaderType === '趋势龙' ? '#3b82f6' : stock.leaderType === '补涨龙' ? '#eab308' : '#6b7280',
                  }}
                >
                  {stock.leaderType}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-[10px] text-[#475569]">
                <span>{stock.sector}</span>
                <span>涨停:{stock.limitUpTime}</span>
                <span>量比:{stock.volumeRatio}x</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[15px] font-bold text-[#f1f5f9] font-mono">{stock.price.toFixed(2)}</div>
              <div className={cn('text-[11px] font-mono', stock.change > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                {stock.change > 0 ? '+' : ''}{stock.change}%
              </div>
            </div>
            <div className="relative w-10 h-10">
              <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1a2744" strokeWidth="2" />
                <circle
                  cx="18" cy="18" r="15.9" fill="none"
                  stroke={stock.score.total >= 80 ? '#ef4444' : stock.score.total >= 60 ? '#eab308' : '#6b7280'}
                  strokeWidth="2"
                  strokeDasharray={`${stock.score.total * 1.0} 100`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-[10px] font-bold font-mono" style={{ color: stock.score.total >= 80 ? '#ef4444' : stock.score.total >= 60 ? '#eab308' : '#6b7280' }}>
                  {stock.score.total}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/* ─── 预警信号卡片 ─── */
function AlertSignalCard({ signal }: { signal: AlertSignal }) {
  const config = BUY_POINT_CONFIG[signal.buyPointType];
  const Icon = config.icon === 'TrendingUp' ? TrendingUp : config.icon === 'RefreshCw' ? RefreshCw : config.icon === 'AlertCircle' ? AlertCircleIcon : Zap;
  
  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ y: -2, boxShadow: '0 8px 25px rgba(0,0,0,0.3)' }}
      className="w-[280px] shrink-0 bg-[#141e33] rounded-lg border border-[rgba(148,163,184,0.08)] overflow-hidden cursor-pointer"
    >
      <div className="flex items-center justify-between px-3 py-2" style={{ backgroundColor: `${config.color}10` }}>
        <div className="flex items-center gap-2">
          <Icon size={14} style={{ color: config.color }} />
          <span className="text-[12px] font-medium" style={{ color: config.color }}>{signal.buyPointType}</span>
        </div>
        <span className="text-[10px] text-[#475569] font-mono">{signal.time}</span>
      </div>
      
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[14px] font-medium text-[#f1f5f9]">{signal.name}</span>
            <span className="text-[10px] text-[#475569] ml-2 font-mono">{signal.code}</span>
          </div>
          <div className="text-right">
            <div className="text-[16px] font-bold text-[#f1f5f9] font-mono">{signal.price.toFixed(2)}</div>
            <div className={cn('text-[11px] font-mono', signal.change > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
              {signal.change > 0 ? '+' : ''}{signal.change}%
            </div>
          </div>
        </div>
        
        <div className="text-[11px] text-[#94a3b8] bg-[#0f1929] rounded p-2 leading-relaxed">
          {signal.logic}
        </div>
        
        <div className="flex items-center justify-between text-[10px]">
          <span className="px-1.5 py-0.5 bg-[rgba(201,168,76,0.15)] text-[#c9a84c] rounded">{signal.tactics}</span>
          <div className="flex items-center gap-2">
            <span className="text-[#475569]">止损: <span className="text-[#ef4444] font-mono">{signal.stopLossPrice.toFixed(2)}</span></span>
            <span className="text-[#475569]">置信度: <span className="text-[#22c55e] font-mono">{signal.confidence}%</span></span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ─── 持仓股监控卡片 ─── */
function HoldingStockCard({ stock, alerts }: { stock: HoldingStock; alerts: HoldingAlert[] }) {
  const stockAlerts = alerts.filter(a => a.code === stock.code);
  const isProfit = stock.profitLoss > 0;
  
  return (
    <div className={cn(
      'bg-[#141e33] rounded-lg border overflow-hidden transition-all duration-200',
      stockAlerts.some(a => a.urgency === '紧急') ? 'border-[rgba(220,38,38,0.3)]' : 'border-[rgba(148,163,184,0.06)]'
    )}>
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-[rgba(148,163,184,0.06)]">
        <div className="flex items-center gap-2">
          <span className="text-[14px] font-medium text-[#f1f5f9]">{stock.name}</span>
          <span className="text-[10px] text-[#475569] font-mono">{stock.code}</span>
          {stock.isLeader && <span className="text-[9px] px-1 py-0.5 bg-[rgba(239,68,68,0.15)] text-[#ef4444] rounded">龙头</span>}
          {stock.isMainLine && <span className="text-[9px] px-1 py-0.5 bg-[rgba(34,197,94,0.15)] text-[#22c55e] rounded">主线</span>}
        </div>
        <div className="text-right">
          <div className="text-[16px] font-bold text-[#f1f5f9] font-mono">{stock.currentPrice.toFixed(2)}</div>
          <div className={cn('text-[11px] font-mono', isProfit ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
            {isProfit ? '+' : ''}{stock.profitLoss.toFixed(2)}%
          </div>
        </div>
      </div>
      
      <div className="px-3 py-2 grid grid-cols-2 gap-2">
        <div>
          <div className="text-[9px] text-[#475569] mb-1">趋势状态</div>
          <div className={cn(
            'text-[11px] px-1.5 py-0.5 rounded inline-block',
            stock.trendStatus === '多头' ? 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]' :
            stock.trendStatus === '支撑' ? 'bg-[rgba(234,179,8,0.15)] text-[#eab308]' :
            stock.trendStatus === '破位' ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' :
            'bg-[rgba(107,114,128,0.15)] text-[#6b7280]'
          )}>
            {stock.trendStatus}
          </div>
        </div>
        <div>
          <div className="text-[9px] text-[#475569] mb-1">量能状态</div>
          <div className={cn(
            'text-[11px] px-1.5 py-0.5 rounded inline-block',
            stock.volumeStatus === '量价齐升' ? 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]' :
            stock.volumeStatus === '放量滞涨' || stock.volumeStatus === '放量杀跌' ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' :
            'bg-[rgba(107,114,128,0.15)] text-[#6b7280]'
          )}>
            {stock.volumeStatus}
          </div>
        </div>
      </div>
      
      <div className="px-3 py-1.5 flex items-center gap-3 text-[10px] text-[#475569]">
        <span>MA5: <span className="font-mono text-[#f1f5f9]">{stock.ma5.toFixed(2)}</span></span>
        <span>MA10: <span className="font-mono text-[#f1f5f9]">{stock.ma10.toFixed(2)}</span></span>
        <span>MA20: <span className="font-mono text-[#f1f5f9]">{stock.ma20.toFixed(2)}</span></span>
      </div>
      
      <div className="px-3 py-1.5 flex items-center gap-3 text-[10px]">
        <span className="text-[#475569]">板块: <span className="text-[#94a3b8]">{stock.sector}</span></span>
        <span className="text-[#475569]">阶段: <span className={cn(
          stock.sectorPhase === '主升' ? 'text-[#ef4444]' :
          stock.sectorPhase === '发酵' ? 'text-[#22c55e]' :
          stock.sectorPhase === '启动' ? 'text-[#3b82f6]' : 'text-[#6b7280]'
        )}>{stock.sectorPhase}</span></span>
        {!stock.holdLogicValid && (
          <span className="text-[#ef4444] flex items-center gap-0.5">
            <XCircle size={10} /> 逻辑失效
          </span>
        )}
      </div>
      
      {stockAlerts.length > 0 && (
        <div className="px-3 py-2 border-t border-[rgba(148,163,184,0.06)] space-y-1">
          {stockAlerts.map((alert, i) => {
            const AlertIcon = alertTypeIconMap[alert.type];
            return (
              <div key={i} className="flex items-center gap-2 text-[10px]">
                <AlertIcon size={10} style={{ color: urgencyColorMap[alert.urgency] }} />
                <span style={{ color: urgencyColorMap[alert.urgency] }} className="font-medium">[{alert.urgency}]</span>
                <span className="text-[#94a3b8]">{alert.message}</span>
                <span className="ml-auto px-1 py-0.5 rounded" style={{ backgroundColor: `${urgencyColorMap[alert.urgency]}20`, color: urgencyColorMap[alert.urgency] }}>
                  {alert.action}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── 回测结果图表 ─── */
function BacktestChart({ result }: { result: BacktestResult }) {
  const option = {
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: 'rgba(13,21,38,0.95)',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
    },
    legend: {
      data: ['胜率', '平均收益'],
      textStyle: { color: '#94a3b8', fontSize: 11 },
      top: 0,
    },
    grid: { left: 40, right: 20, top: 30, bottom: 20 },
    xAxis: {
      type: 'category' as const,
      data: result.byBuyPoint.map(b => b.type),
      axisLabel: { color: '#475569', fontSize: 10, rotate: 15 },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
    },
    yAxis: [
      { type: 'value' as const, name: '胜率(%)', max: 100, axisLabel: { color: '#475569', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
      { type: 'value' as const, name: '收益(%)', axisLabel: { color: '#475569', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      {
        name: '胜率', type: 'bar' as const,
        data: result.byBuyPoint.map(b => ({ value: b.winRate, itemStyle: { color: b.winRate > 65 ? '#22c55e' : '#eab308' } })),
        barWidth: 20,
      },
      {
        name: '平均收益', type: 'line' as const, yAxisIndex: 1,
        data: result.byBuyPoint.map(b => b.avgReturn),
        itemStyle: { color: '#c9a84c' },
        smooth: true,
      },
    ],
  };
  
  return <ReactECharts option={option} style={{ height: '220px' }} opts={{ renderer: 'canvas' }} />;
}

/* ─── 主页面组件 ─── */
export default function IntradayMonitor() {
  const [activeModule, setActiveModule] = useState<'overview' | 'leaders' | 'alerts' | 'holdings' | 'review'>('overview');
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [refreshInterval] = useState(10);
  
  const [marketData, setMarketData] = useState<MarketMonitor>(generateMarketMonitor());
  const [sectors] = useState<SectorStrength[]>(generateSectorStrength());
  const [dashboard] = useState<SentimentDashboard>(generateSentimentDashboard('主升期', '消费电子'));
  const [leaderData] = useState(generateLeaderTiers());
  const [alertSignals, setAlertSignals] = useState<AlertSignal[]>(generateAlertSignals());
  const [holdings, setHoldings] = useState<HoldingStock[]>(generateHoldingStocks());
  const [holdingAlerts, setHoldingAlerts] = useState<HoldingAlert[]>([]);
  const [backtestResult] = useState<BacktestResult>(generateBacktestResult());
  const [dailyReview] = useState<DailyReview>(generateDailyReview());
  const [tradeLogs] = useState<TradeLog[]>(generateTradeLogs());
  const [filterConfig, setFilterConfig] = useState<FilterCondition>(DEFAULT_FILTER);
  const [_tacticParams] = useState<TacticParams>(DEFAULT_TACTIC_PARAMS);
  
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  useEffect(() => {
    if (isLive) {
      timerRef.current = setInterval(() => {
        setLastUpdate(new Date());
        setMarketData(generateMarketMonitor());
        setAlertSignals(generateAlertSignals());
        setHoldings(generateHoldingStocks());
      }, refreshInterval * 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isLive, refreshInterval]);
  
  useEffect(() => {
    setHoldingAlerts(generateHoldingAlerts(holdings));
  }, [holdings]);
  
  const modules = [
    { id: 'overview' as const, label: '全局监控', icon: Activity },
    { id: 'leaders' as const, label: '龙头梯队', icon: Award },
    { id: 'alerts' as const, label: '盘中预警', icon: Bell },
    { id: 'holdings' as const, label: '持仓盯盘', icon: Eye },
    { id: 'review' as const, label: '复盘回测', icon: BarChart3 },
  ];
  
  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-4">
      {/* ═══ 顶部控制栏 ═══ */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 bg-[#141e33] rounded-lg p-0.5">
          {modules.map(m => (
            <button
              key={m.id}
              onClick={() => setActiveModule(m.id)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded-md transition-all',
                activeModule === m.id ? 'bg-[#c9a84c] text-[#060b14] font-medium' : 'text-[#94a3b8] hover:text-[#f1f5f9]'
              )}
            >
              <m.icon size={14} />
              {m.label}
            </button>
          ))}
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[11px] text-[#475569]">
            <span className={cn('relative flex h-2 w-2', isLive && 'animate-pulse')}>
              <span className={cn('absolute inline-flex h-full w-full rounded-full', isLive ? 'bg-[#22c55e] opacity-75' : 'bg-[#6b7280]')} />
              <span className={cn('relative inline-flex rounded-full h-2 w-2', isLive ? 'bg-[#22c55e]' : 'bg-[#6b7280]')} />
            </span>
            <span>{isLive ? '实时刷新中' : '已暂停'}</span>
            <span className="font-mono">{lastUpdate.toLocaleTimeString()}</span>
          </div>
          <button onClick={() => setIsLive(!isLive)} className="p-1.5 rounded hover:bg-[#141e33] text-[#94a3b8]">
            {isLive ? <Pause size={14} /> : <Play size={14} />}
          </button>
          <button onClick={() => setLastUpdate(new Date())} className="p-1.5 rounded hover:bg-[#141e33] text-[#94a3b8]">
            <RotateCcw size={14} />
          </button>
        </div>
      </div>
      
      {/* ══ 模块1: 全局监控 ═══ */}
      {activeModule === 'overview' && (
        <div className="space-y-4">
          {/* 情绪仪表盘 + 大盘指标 */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-12 lg:col-span-4">
              <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">情绪周期仪表盘</h2>}>
                <div className="flex flex-col items-center gap-4">
                  <SentimentGauge phase={marketData.currentPhase} confidence={marketData.phaseConfidence} />
                  <div className="text-center">
                    <div className="text-[24px] font-bold" style={{ color: SENTIMENT_PHASE_CONFIG[marketData.currentPhase].color }}>
                      {dashboard.action}
                    </div>
                    <div className="text-[12px] text-[#94a3b8] mt-1">{dashboard.summary}</div>
                    <div className="text-[11px] text-[#475569] mt-2">
                      风险等级: <span className={cn(
                        dashboard.riskLevel === '低' ? 'text-[#22c55e]' :
                        dashboard.riskLevel === '中' ? 'text-[#eab308]' :
                        dashboard.riskLevel === '高' ? 'text-[#ef4444]' : 'text-[#dc2626]'
                      )}>{dashboard.riskLevel}</span>
                    </div>
                  </div>
                </div>
              </DataCard>
            </div>
            
            <div className="col-span-12 lg:col-span-8">
              <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">大盘监控指标</h2>}>
                <div className="grid grid-cols-4 gap-2">
                  <MarketMetricCard label="涨停家数" value={marketData.limitUpCount} color="#ef4444" trend="up" />
                  <MarketMetricCard label="跌停家数" value={marketData.limitDownCount} color="#22c55e" trend="down" />
                  <MarketMetricCard label="封板率" value={marketData.boardSealRate} unit="%" color="#22c55e" />
                  <MarketMetricCard label="连板高度" value={marketData.maxConsecutiveBoards} unit="板" color="#c9a84c" />
                  <MarketMetricCard label="昨日溢价" value={marketData.yesterdayLimitUpPremium} unit="%" color="#22c55e" />
                  <MarketMetricCard label="连板溢价" value={marketData.consecutiveBoardPremium} unit="%" color="#22c55e" />
                  <MarketMetricCard label="上涨家数" value={marketData.totalUpCount} color="#ef4444" trend="up" />
                  <MarketMetricCard label="下跌家数" value={marketData.totalDownCount} color="#22c55e" trend="down" />
                </div>
              </DataCard>
            </div>
          </div>
          
          {/* 大盘指数 */}
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">大盘指数监控</h2>}>
            <div className="grid grid-cols-4 gap-3">
              {marketData.indices.map(idx => (
                <div key={idx.code} className="bg-[#141e33] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[12px] text-[#94a3b8] mb-1">{idx.name}</div>
                  <div className="text-[18px] font-bold text-[#f1f5f9] font-mono">{idx.value.toFixed(2)}</div>
                  <div className={cn('text-[12px] font-mono', idx.changePercent > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                    {idx.changePercent > 0 ? '+' : ''}{idx.changePercent}%
                  </div>
                  <div className="text-[10px] text-[#475569] mt-1">成交额: {idx.volume}亿</div>
                </div>
              ))}
            </div>
          </DataCard>
          
          {/* 板块强度排行 */}
          <DataCard header={
            <div className="flex items-center justify-between w-full">
              <h2 className="text-[16px] font-semibold text-[#f1f5f9]">板块强度排行榜</h2>
              <div className="flex items-center gap-2 text-[11px]">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#ef4444]" />主线</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#eab308]" />支线</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#6b7280]" />杂毛</span>
              </div>
            </div>
          }>
            <div className="space-y-2">
              <div className="grid grid-cols-[100px_50px_80px_1fr_50px_50px_60px] gap-3 px-3 py-1.5 text-[10px] text-[#475569] font-medium">
                <span>板块名称</span><span className="text-center">涨停</span><span>连板梯队</span><span>趋势强度</span><span className="text-center">封板率</span><span className="text-center">状态</span><span className="text-right">资金流向</span>
              </div>
              {sectors.map((sector, i) => (
                <SectorStrengthBar key={i} sector={sector} />
              ))}
            </div>
          </DataCard>
        </div>
      )}
      
      {/* ═══ 模块2: 龙头梯队 ═══ */}
      {activeModule === 'leaders' && (
        <div className="space-y-4">
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">主线一致性校验</h2>}>
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-4">
                <div className="text-[12px] text-[#475569] mb-2">主线题材</div>
                <div className="space-y-1">
                  {leaderData.mainLineConsistency.mainLineSectors.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 bg-[rgba(34,197,94,0.06)] rounded-lg border border-[rgba(34,197,94,0.15)]">
                      <CheckCircle size={14} className="text-[#22c55e]" />
                      <span className="text-[13px] text-[#f1f5f9]">{s}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="col-span-4">
                <div className="text-[12px] text-[#475569] mb-2">主线龙头 ({leaderData.mainLineConsistency.filteredStocks.length}只)</div>
                <div className="space-y-1">
                  {leaderData.mainLineConsistency.filteredStocks.map(s => (
                    <div key={s.code} className="flex items-center justify-between px-3 py-1.5 bg-[#141e33] rounded">
                      <span className="text-[12px] text-[#f1f5f9]">{s.name}</span>
                      <span className="text-[11px] text-[#22c55e]">评分:{s.score.total}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="col-span-4">
                <div className="text-[12px] text-[#475569] mb-2">已屏蔽非主线 ({leaderData.mainLineConsistency.blockedStocks.length}只)</div>
                <div className="space-y-1">
                  {leaderData.mainLineConsistency.blockedStocks.map((b, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-1.5 bg-[rgba(239,68,68,0.06)] rounded border border-[rgba(239,68,68,0.1)]">
                      <span className="text-[12px] text-[#94a3b8]">{b.stock.name}</span>
                      <span className="text-[10px] text-[#ef4444]">{b.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </DataCard>
          
          <div className="grid grid-cols-2 gap-4">
            {leaderData.tiers.map((tier, i) => (
              <LeaderTierCard key={i} tier={tier} />
            ))}
          </div>
        </div>
      )}
      
      {/* ═══ 模块3: 盘中预警 ══ */}
      {activeModule === 'alerts' && (
        <div className="space-y-4">
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">预警设置</h2>}>
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-6">
                <div className="text-[12px] text-[#475569] mb-2">过滤条件</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(filterConfig).map(([key, value]) => (
                    <label key={key} className="flex items-center gap-2 text-[11px] text-[#94a3b8]">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={() => setFilterConfig(prev => ({ ...prev, [key]: !value }))}
                        className="w-3.5 h-3.5 rounded border-[rgba(148,163,184,0.2)] bg-[#0f1929] text-[#c9a84c] focus:ring-[#c9a84c]"
                      />
                      {key === 'excludeNonMainLine' ? '排除非主线' :
                       key === 'excludeRetreatPhase' ? '退潮期关闭预警' :
                       key === 'excludeST' ? '排除ST' :
                       key === 'excludeDelisting' ? '排除退市' :
                       key === 'excludeLossMaking' ? '排除亏损' :
                       key === 'excludeLowLiquidity' ? '排除低流动性' :
                       key === 'excludeZhuangGu' ? '排除庄股' : '排除高位风险'}
                    </label>
                  ))}
                </div>
              </div>
              <div className="col-span-6">
                <div className="text-[12px] text-[#475569] mb-2">买点类型</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(BUY_POINT_CONFIG).map(([type, config]) => (
                    <div key={type} className="flex items-center gap-2 px-2 py-1.5 bg-[#141e33] rounded">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: config.color }} />
                      <span className="text-[11px] text-[#f1f5f9]">{type}</span>
                      <span className="text-[10px] text-[#475569] ml-auto">止损{config.stopLossPercent}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </DataCard>
          
          <DataCard header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <Bell size={16} className="text-[#c9a84c]" />
                <h2 className="text-[16px] font-semibold text-[#f1f5f9]">实时预警信号</h2>
                <span className="text-[11px] px-2 py-0.5 bg-[rgba(201,168,76,0.15)] text-[#c9a84c] rounded-full">{alertSignals.length}条</span>
              </div>
            </div>
          }>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {alertSignals.map((signal, i) => (
                <AlertSignalCard key={i} signal={signal} />
              ))}
            </div>
          </DataCard>
        </div>
      )}
      
      {/* ══ 模块4: 持仓盯盘 ═══ */}
      {activeModule === 'holdings' && (
        <div className="space-y-4">
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">持仓总览</h2>}>
            <div className="grid grid-cols-4 gap-3">
              <MarketMetricCard label="持仓数量" value={holdings.length} color="#c9a84c" />
              <MarketMetricCard label="总盈亏" value={holdings.reduce((sum, h) => sum + h.profitLossAmount, 0).toFixed(0)} unit="元" color={holdings.reduce((sum, h) => sum + h.profitLossAmount, 0) > 0 ? '#ef4444' : '#22c55e'} />
              <MarketMetricCard label="逻辑有效" value={holdings.filter(h => h.holdLogicValid).length} color="#22c55e" />
              <MarketMetricCard label="待处理提醒" value={holdingAlerts.length} color="#ef4444" />
            </div>
          </DataCard>
          
          {holdingAlerts.length > 0 && (
            <DataCard header={
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-[#ef4444]" />
                <h2 className="text-[16px] font-semibold text-[#f1f5f9]">持仓提醒</h2>
                <span className="text-[11px] px-2 py-0.5 bg-[rgba(239,68,68,0.15)] text-[#ef4444] rounded-full">{holdingAlerts.length}条</span>
              </div>
            }>
              <div className="space-y-2">
                {holdingAlerts.map((alert, i) => {
                  const AlertIcon = alertTypeIconMap[alert.type];
                  return (
                    <motion.div
                      key={i}
                      variants={itemVariants}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg border',
                        alert.urgency === '紧急' ? 'bg-[rgba(220,38,38,0.06)] border-[rgba(220,38,38,0.2)]' :
                        alert.urgency === '高' ? 'bg-[rgba(239,68,68,0.06)] border-[rgba(239,68,68,0.15)]' :
                        'bg-[#141e33] border-[rgba(148,163,184,0.06)]'
                      )}
                    >
                      <AlertIcon size={16} style={{ color: urgencyColorMap[alert.urgency] }} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[12px] font-medium text-[#f1f5f9]">{alert.name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: `${urgencyColorMap[alert.urgency]}20`, color: urgencyColorMap[alert.urgency] }}>
                            {alert.urgency}
                          </span>
                          <span className="text-[10px] text-[#475569]">{alert.time}</span>
                        </div>
                        <div className="text-[11px] text-[#94a3b8] mt-0.5">{alert.message}</div>
                      </div>
                      <span className="px-2 py-1 rounded text-[11px] font-medium" style={{ backgroundColor: `${urgencyColorMap[alert.urgency]}20`, color: urgencyColorMap[alert.urgency] }}>
                        {alert.action}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </DataCard>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            {holdings.map((stock, i) => (
              <HoldingStockCard key={i} stock={stock} alerts={holdingAlerts} />
            ))}
          </div>
        </div>
      )}
      
      {/* ═══ 模块5: 复盘回测 ═══ */}
      {activeModule === 'review' && (
        <div className="space-y-4">
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">历史回测结果</h2>}>
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-4">
                <div className="grid grid-cols-2 gap-2">
                  <MarketMetricCard label="总交易" value={backtestResult.totalTrades} color="#c9a84c" />
                  <MarketMetricCard label="胜率" value={backtestResult.winRate} unit="%" color="#22c55e" />
                  <MarketMetricCard label="盈亏比" value={backtestResult.profitLossRatio.toFixed(2)} color="#22c55e" />
                  <MarketMetricCard label="总收益" value={backtestResult.totalReturn} unit="%" color="#ef4444" />
                  <MarketMetricCard label="最大回撤" value={backtestResult.maxDrawdown} unit="%" color="#ef4444" />
                  <MarketMetricCard label="夏普比率" value={backtestResult.sharpeRatio.toFixed(2)} color="#22c55e" />
                </div>
              </div>
              <div className="col-span-8">
                <BacktestChart result={backtestResult} />
              </div>
            </div>
          </DataCard>
          
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">每日复盘</h2>}>
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-4 space-y-3">
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">日期</div>
                  <div className="text-[14px] text-[#f1f5f9]">{dailyReview.date}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">情绪周期</div>
                  <span className="text-[12px] px-2 py-0.5 rounded" style={{ backgroundColor: SENTIMENT_PHASE_CONFIG[dailyReview.phase].bgColor, color: SENTIMENT_PHASE_CONFIG[dailyReview.phase].color }}>
                    {dailyReview.phase}
                  </span>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">主线板块</div>
                  <div className="text-[13px] text-[#f1f5f9]">{dailyReview.mainLine}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">龙头股</div>
                  <div className="space-y-1">
                    {dailyReview.leaders.map((l, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px]">
                        <span className="text-[#f1f5f9]">{l.name}</span>
                        <span className="text-[#ef4444]">{l.boards}板</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="col-span-4 space-y-3">
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">操作机会</div>
                  <div className="space-y-1">
                    {dailyReview.opportunities.map((o, i) => (
                      <div key={i} className="text-[11px] text-[#22c55e] flex items-start gap-1">
                        <CheckCircle size={12} className="mt-0.5 shrink-0" />
                        <span>{o}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">错过机会</div>
                  <div className="space-y-1">
                    {dailyReview.missedOpportunities.map((o, i) => (
                      <div key={i} className="text-[11px] text-[#eab308] flex items-start gap-1">
                        <AlertCircle size={12} className="mt-0.5 shrink-0" />
                        <span>{o}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="col-span-4 space-y-3">
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">操作失误</div>
                  <div className="space-y-1">
                    {dailyReview.mistakes.map((m, i) => (
                      <div key={i} className="text-[11px] text-[#ef4444] flex items-start gap-1">
                        <XCircle size={12} className="mt-0.5 shrink-0" />
                        <span>{m}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-1">次日计划</div>
                  <div className="text-[11px] text-[#94a3b8] bg-[#0f1929] rounded p-2 leading-relaxed">
                    {dailyReview.nextDayPlan}
                  </div>
                </div>
              </div>
            </div>
          </DataCard>
          
          <DataCard header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">操作日志</h2>}>
            <div className="space-y-2">
              <div className="grid grid-cols-[80px_80px_60px_50px_60px_60px_80px_60px_60px_60px] gap-2 px-3 py-1.5 text-[10px] text-[#475569] font-medium border-b border-[rgba(148,163,184,0.06)]">
                <span>日期</span><span>名称</span><span>操作</span><span>价格</span><span>数量</span><span>金额</span><span>买点</span><span>盈亏</span><span>持仓</span><span>结果</span>
              </div>
              {tradeLogs.map((log, i) => (
                <motion.div
                  key={i}
                  variants={itemVariants}
                  className="grid grid-cols-[80px_80px_60px_50px_60px_60px_80px_60px_60px_60px] gap-2 px-3 py-2 text-[11px] hover:bg-[#141e33] rounded transition-colors"
                >
                  <span className="text-[#475569] font-mono">{log.date}</span>
                  <span className="text-[#f1f5f9]">{log.name}</span>
                  <span className={log.action === '买入' ? 'text-[#22c55e]' : 'text-[#ef4444]'}>{log.action}</span>
                  <span className="text-[#f1f5f9] font-mono">{log.price.toFixed(2)}</span>
                  <span className="text-[#94a3b8]">{log.quantity}</span>
                  <span className="text-[#94a3b8] font-mono">{log.amount.toLocaleString()}</span>
                  <span className="text-[#c9a84c] truncate">{log.buyPointType || '--'}</span>
                  <span className={cn('font-mono', (log.profitLoss ?? 0) > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                    {log.profitLoss != null ? `${log.profitLoss > 0 ? '+' : ''}${log.profitLoss}%` : '--'}
                  </span>
                  <span className="text-[#475569]">{log.holdDays != null ? `${log.holdDays}天` : '--'}</span>
                  <span className={cn(
                    'px-1 py-0.5 rounded text-center',
                    log.result === '盈利' ? 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]' :
                    log.result === '亏损' ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' :
                    'bg-[rgba(107,114,128,0.15)] text-[#6b7280]'
                  )}>{log.result}</span>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>
      )}
    </motion.div>
  );
}