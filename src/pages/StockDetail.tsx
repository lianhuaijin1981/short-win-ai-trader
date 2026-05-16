import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import {
  TrendingUp,
  Radio,
  Crosshair,
  Anchor,
  Fingerprint,
  Target,
  AlertTriangle,
  MapPin,
  BarChart3,
  Zap,
  ShieldAlert,
  ChevronRight,
  Activity,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import ScoreRing from '@/components/ScoreRing';
import { cn } from '@/lib/utils';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */
interface StockDetailData {
  code: string;
  name: string;
  market: string;
  price: number;
  prevClose: number;
  open: number;
  high: number;
  low: number;
  changePercent: number;
  changeAmount: number;
  volume: string;
  turnover: string;
  turnoverRate: string;
  volumeRatio: number;
  score: number;
  rating: string;
  kline: KLineItem[];
  signals: SignalItem[];
  dimensions: DimensionItem[];
  fundFlow: FundFlowData;
  themes: ThemeItem[];
  tradingPlan: TradingPlanData;
  risks: string[];
  emotionPhase: string;
  emotionColor: string;
  themePosition: string;
  themeStage: string;
  anchorStatus: string;
  matchYingyou: string;
  matchPercent: number;
  matchTactics: string[];
  pe: string;
  pb: string;
  totalCap: string;
  floatCap: string;
  amplitude: string;
  weiBi: string;
  matchedYingyouList: YingyouMatchItem[];
}

interface KLineItem {
  date: string;
  open: number;
  close: number;
  low: number;
  high: number;
  volume: number;
}

interface SignalItem {
  name: string;
  icon: string;
  strength: number;
  time: string;
  desc: string;
  status: 'confirmed' | 'ongoing' | 'pending';
  color: string;
}

interface DimensionItem {
  name: string;
  score: number;
}

interface FundFlowData {
  mainNetInflow: string;
  mainTrend: string;
  dragonTigerQuality: string;
  sealStrength: string;
  breakdown: FundBreakdownItem[];
  timeline: FundTimelineItem[];
}

interface FundBreakdownItem {
  type: string;
  inflow: string;
  outflow: string;
  net: string;
}

interface FundTimelineItem {
  time: string;
  value: number;
}

interface ThemeItem {
  name: string;
  heat: number;
  change: string;
  changeUp: boolean;
  position: string;
  related: string[];
  constituents: ConstituentItem[];
}

interface ConstituentItem {
  code: string;
  name: string;
  price: number;
  changePercent: number;
}

interface TradingPlanData {
  position: string;
  entryRange: string;
  stopLoss: string;
  takeProfit: string;
  rrRatio: string;
  action: string;
  suggestion: string;
}

interface YingyouMatchItem {
  name: string;
  matchPercent: number;
  tag?: string;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */
const isUp = (n: number) => n >= 0;

function MetricBadge({ value, suffix = '%', className }: { value: number; suffix?: string; className?: string }) {
  const up = isUp(value);
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-[13px] font-mono font-medium',
        up ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]',
        className
      )}
    >
      {up ? '+' : ''}
      {value.toFixed(2)}
      {suffix}
    </span>
  );
}

function TagPill({
  children,
  variant = 'default',
  className,
}: {
  children: React.ReactNode;
  variant?: 'gold' | 'blue' | 'purple' | 'green' | 'gray' | 'red' | 'default';
  className?: string;
}) {
  const variants: Record<string, string> = {
    gold: 'bg-[#c9a84c] text-[#060b14] font-semibold',
    blue: 'bg-[#3b82f6]/20 text-[#3b82f6] border border-[#3b82f6]/30',
    purple: 'bg-[#8b5cf6]/20 text-[#8b5cf6] border border-[#8b5cf6]/30',
    green: 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30',
    gray: 'bg-[#475569]/20 text-[#94a3b8] border border-[#475569]/30',
    red: 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30',
    default: 'bg-[#141e33] text-[#94a3b8] border border-[rgba(148,163,184,0.1)]',
  };
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-[11px]', variants[variant], className)}>
      {children}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Mock Data Generator                                                */
/* ------------------------------------------------------------------ */
function generateKLine(basePrice: number, days = 30): KLineItem[] {
  const data: KLineItem[] = [];
  let price = basePrice * 0.85;
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const volatility = price * 0.035;
    const change = (Math.random() - 0.45) * volatility;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * volatility * 0.4;
    const low = Math.min(open, close) - Math.random() * volatility * 0.4;
    const volume = Math.floor(80000 + Math.random() * 250000);
    data.push({
      date: date.toISOString().slice(0, 10),
      open: +open.toFixed(2),
      close: +close.toFixed(2),
      low: +low.toFixed(2),
      high: +high.toFixed(2),
      volume,
    });
    price = close;
  }
  return data;
}

function calcMA(data: KLineItem[], period: number): (number | null)[] {
  return data.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = 0; j < period; j++) sum += data[i - j].close;
    return +(sum / period).toFixed(2);
  });
}

function getStockData(code: string): StockDetailData {
  const basePrice = 15 + Math.random() * 40;
  const prevClose = basePrice;
  const kline = generateKLine(basePrice, 30);
  const finalPrice = kline[kline.length - 1].close;
  const finalChangePercent = ((finalPrice - prevClose) / prevClose) * 100;

  const names = ['英维克', '文一科技', '中际旭创', '中芯国际', '某某科技', '华天科技', '浪潮信息', '某某智能'];
  const name = names[code.charCodeAt(code.length - 1) % names.length];

  return {
    code,
    name,
    market: code.startsWith('300') || code.startsWith('688') ? '创业板' : code.startsWith('002') ? '深市主板' : '沪市主板',
    price: +finalPrice.toFixed(2),
    prevClose: +prevClose.toFixed(2),
    open: +(prevClose * (1 + (Math.random() - 0.5) * 0.02)).toFixed(2),
    high: +Math.max(finalPrice, prevClose * 1.05).toFixed(2),
    low: +Math.min(finalPrice, prevClose * 0.95).toFixed(2),
    changePercent: +finalChangePercent.toFixed(2),
    changeAmount: +(finalPrice - prevClose).toFixed(2),
    volume: (0.5 + Math.random() * 50).toFixed(1) + '万手',
    turnover: (0.3 + Math.random() * 12).toFixed(1) + '亿',
    turnoverRate: (1 + Math.random() * 15).toFixed(1) + '%',
    volumeRatio: +(0.5 + Math.random() * 5).toFixed(1),
    score: Math.floor(65 + Math.random() * 30),
    rating: ['S', 'A', 'B', 'C'][Math.floor(Math.random() * 3)],
    kline,
    signals: [
      { name: '筹码峰突破', icon: 'mountain', strength: 95, time: '09:35', desc: '成交量为近期3倍，站上筹码密集区', status: 'confirmed', color: '#c9a84c' },
      { name: '三倍量突破', icon: 'zap', strength: 92, time: '09:35', desc: '量价齐升，资金大幅流入', status: 'confirmed', color: '#c9a84c' },
      { name: 'N字形反包', icon: 'trending-up', strength: 88, time: '10:15', desc: '形态确认，第二波拉升启动', status: 'ongoing', color: '#3b82f6' },
      { name: '首阴信号', icon: 'activity', strength: 75, time: '昨日', desc: '首阴后今日反包确认', status: 'confirmed', color: '#c9a84c' },
      { name: '资金流入', icon: 'dollar-sign', strength: 85, time: '持续', desc: '主力资金净流入+1.2亿', status: 'ongoing', color: '#3b82f6' },
      { name: '游资共振', icon: 'users', strength: 90, time: '09:40', desc: '炒股养家+92科比双游资介入', status: 'ongoing', color: '#8b5cf6' },
    ],
    dimensions: [
      { name: '资讯', score: Math.floor(60 + Math.random() * 35) },
      { name: '基本面', score: Math.floor(55 + Math.random() * 40) },
      { name: '技术', score: Math.floor(65 + Math.random() * 30) },
      { name: '筹码', score: Math.floor(70 + Math.random() * 25) },
      { name: '情绪', score: Math.floor(50 + Math.random() * 45) },
      { name: '资金', score: Math.floor(60 + Math.random() * 35) },
    ],
    fundFlow: {
      mainNetInflow: (Math.random() > 0.3 ? '+' : '-') + (0.1 + Math.random() * 3).toFixed(2) + '亿',
      mainTrend: '较昨日+' + Math.floor(10 + Math.random() * 50) + '%',
      dragonTigerQuality: Math.random() > 0.4 ? '优' : '中',
      sealStrength: (Math.floor(60 + Math.random() * 40)) + '%',
      breakdown: [
        { type: '超大单', inflow: '+2.1亿', outflow: '-0.8亿', net: '+1.3亿' },
        { type: '大单', inflow: '+1.5亿', outflow: '-1.2亿', net: '+0.3亿' },
        { type: '中单', inflow: '+0.8亿', outflow: '-1.0亿', net: '-0.2亿' },
        { type: '小单', inflow: '+0.5亿', outflow: '-0.6亿', net: '-0.1亿' },
      ],
      timeline: Array.from({ length: 8 }, (_, i) => ({
        time: `${9 + Math.floor(i / 2)}:${30 + (i % 2) * 30}`,
        value: +(Math.random() * 2 - 0.5).toFixed(2),
      })),
    },
    themes: [
      {
        name: '人工智能',
        heat: 92,
        change: '+3.2%',
        changeUp: true,
        position: '板块龙头',
        related: ['某某智能', '某某芯'],
        constituents: [
          { code: '000001', name: '某某智能', price: 15.8, changePercent: 5.2 },
          { code: '000002', name: '某某芯', price: 28.3, changePercent: 3.1 },
          { code: '000003', name: '某某科技', price: 12.6, changePercent: -1.2 },
        ],
      },
      {
        name: '芯片',
        heat: 78,
        change: '+1.8%',
        changeUp: true,
        position: '龙二',
        related: ['某某微', '某某半导体'],
        constituents: [
          { code: '000004', name: '某某微', price: 45.2, changePercent: 2.8 },
          { code: '000005', name: '某某半导体', price: 32.1, changePercent: 1.5 },
        ],
      },
      {
        name: '机器人',
        heat: 65,
        change: '+0.5%',
        changeUp: true,
        position: '跟风',
        related: ['某某机器人'],
        constituents: [
          { code: '000006', name: '某某机器人', price: 22.4, changePercent: 0.8 },
        ],
      },
    ],
    tradingPlan: {
      position: Math.floor(20 + Math.random() * 40) + '%',
      entryRange: (finalPrice * 0.97).toFixed(2) + '-' + (finalPrice * 1.01).toFixed(2),
      stopLoss: (finalPrice * 0.93).toFixed(2),
      takeProfit: (finalPrice * 1.12).toFixed(2),
      rrRatio: '1:' + (1.5 + Math.random() * 2).toFixed(1),
      action: Math.random() > 0.3 ? '分批建仓' : '观望等待',
      suggestion: `筹码峰+三倍量双确认，养家模式匹配。建议30%仓位，${(finalPrice * 0.98).toFixed(2)}-${(finalPrice * 1.02).toFixed(2)}区间分批介入，止损${(finalPrice * 0.93).toFixed(2)}。`,
    },
    risks: [
      '大盘情绪处于高潮期后半段，随时可能转入分歧',
      '前高附近套牢盘密集，需放量突破确认',
      '同题材后排个股已开始分化，谨防补跌',
      '游资席位出现分歧，买一独大风险',
    ],
    emotionPhase: '高潮期',
    emotionColor: '#c9a84c',
    themePosition: '人工智能 / 芯片',
    themeStage: '发酵期',
    anchorStatus: code.charCodeAt(code.length - 1) % 2 === 0 ? '龙头' : '先锋',
    matchYingyou: '炒股养家',
    matchPercent: Math.floor(75 + Math.random() * 20),
    matchTactics: ['筹码峰+', '三倍量', '首阴'],
    pe: (20 + Math.random() * 40).toFixed(1),
    pb: (2 + Math.random() * 6).toFixed(1),
    totalCap: Math.floor(30 + Math.random() * 200) + '亿',
    floatCap: Math.floor(20 + Math.random() * 120) + '亿',
    amplitude: (5 + Math.random() * 15).toFixed(1) + '%',
    weiBi: (Math.random() > 0.5 ? '+' : '-') + (10 + Math.random() * 40).toFixed(1) + '%',
    matchedYingyouList: [
      { name: '炒股养家', matchPercent: Math.floor(85 + Math.random() * 12), tag: '最匹配' },
      { name: '92科比', matchPercent: Math.floor(78 + Math.random() * 10) },
      { name: '小鳄鱼', matchPercent: Math.floor(70 + Math.random() * 12) },
    ],
  };
}

/* ------------------------------------------------------------------ */
/*  Chart Option Builders                                              */
/* ------------------------------------------------------------------ */
function buildKLineOption(kline: KLineItem[]) {
  const dates = kline.map((d) => d.date);
  const ma5 = calcMA(kline, 5);
  const ma10 = calcMA(kline, 10);
  const ma20 = calcMA(kline, 20);

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    grid: { left: 48, right: 16, top: 16, bottom: 72, height: '72%' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a2744',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: { color: '#f1f5f9', fontSize: 12, fontFamily: 'JetBrains Mono' },
      axisPointer: { type: 'cross', lineStyle: { color: 'rgba(148,163,184,0.2)' } },
      formatter: (params: any[]) => {
        if (!params?.length) return '';
        const k = params.find((p) => p.seriesName === 'K线');
        if (!k) return '';
        const maLines = params.filter((p) => p.seriesName?.startsWith('MA'));
        let html = `<div style="font-weight:700;margin-bottom:4px">${k.axisValue}</div>`;
        html += `<div style="display:grid;grid-template-columns:auto auto;gap:4px 12px">`;
        html += `<span style="color:#94a3b8">开</span><span style="color:${k.data[1] > k.data[0] ? '#ef4444' : '#22c55e'}">${k.data[1]}</span>`;
        html += `<span style="color:#94a3b8">收</span><span style="color:${k.data[2] > k.data[1] ? '#ef4444' : '#22c55e'}">${k.data[2]}</span>`;
        html += `<span style="color:#94a3b8">低</span><span>${k.data[3]}</span>`;
        html += `<span style="color:#94a3b8">高</span><span>${k.data[4]}</span>`;
        html += `</div>`;
        maLines.forEach((m) => {
          html += `<div style="margin-top:2px;font-size:11px;color:${m.color}">${m.seriesName}: ${m.data}</div>`;
        });
        return html;
      },
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, bottom: 8, height: 20, borderColor: 'transparent', backgroundColor: '#141e33', fillerColor: 'rgba(201,168,76,0.15)', textStyle: { color: '#94a3b8' }, handleStyle: { color: '#c9a84c' } }],
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
      axisLabel: { color: '#475569', fontSize: 10, fontFamily: 'JetBrains Mono' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } },
      axisLabel: { color: '#475569', fontSize: 10, fontFamily: 'JetBrains Mono' },
    },
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: kline.map((d) => [d.open, d.close, d.low, d.high]),
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e', borderWidth: 1 },
        barWidth: '55%',
      },
      { name: 'MA5', type: 'line', data: ma5, smooth: true, showSymbol: false, lineStyle: { color: '#e0e0e0', width: 1 }, },
      { name: 'MA10', type: 'line', data: ma10, smooth: true, showSymbol: false, lineStyle: { color: '#f59e0b', width: 1 }, },
      { name: 'MA20', type: 'line', data: ma20, smooth: true, showSymbol: false, lineStyle: { color: '#8b5cf6', width: 1 }, },
    ],
    legend: { data: ['MA5', 'MA10', 'MA20'], top: 0, right: 16, textStyle: { color: '#94a3b8', fontSize: 11 }, itemWidth: 16, itemHeight: 2 },
  };
}

function buildRadarOption(dimensions: DimensionItem[]) {
  return {
    backgroundColor: 'transparent',
    radar: {
      indicator: dimensions.map((d) => ({ name: d.name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#94a3b8', fontSize: 11, fontFamily: 'Noto Sans SC' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
      splitArea: { show: true, areaStyle: { color: ['transparent', 'rgba(201,168,76,0.02)', 'transparent', 'rgba(201,168,76,0.03)'] } },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: dimensions.map((d) => d.score),
        name: '评分',
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#c9a84c', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(201,168,76,0.35)' }, { offset: 1, color: 'rgba(201,168,76,0.05)' }]) },
        itemStyle: { color: '#c9a84c', borderColor: '#e0c878', borderWidth: 1 },
      }],
    }],
  };
}

function buildFundAreaOption(timeline: FundTimelineItem[]) {
  const times = timeline.map((t) => t.time);
  const values = timeline.map((t) => t.value);
  return {
    backgroundColor: 'transparent',
    grid: { left: 40, right: 8, top: 8, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a2744',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: { color: '#f1f5f9', fontSize: 11 },
      formatter: (p: any) => `${p[0].axisValue}<br/>净流入: <span style="color:${p[0].data >= 0 ? '#ef4444' : '#22c55e'}">${p[0].data}亿</span>`,
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
      axisLabel: { color: '#475569', fontSize: 9 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } },
      axisLabel: { color: '#475569', fontSize: 9, formatter: '{value}亿' },
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: '#ef4444' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(239,68,68,0.3)' }, { offset: 1, color: 'rgba(239,68,68,0.02)' }]) },
    }],
  };
}

function buildFundPieOption() {
  return {
    backgroundColor: 'transparent',
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#0d1526', borderWidth: 2 },
      label: { show: true, color: '#94a3b8', fontSize: 10, formatter: '{b}\n{d}%' },
      emphasis: { label: { show: true, fontSize: 11, fontWeight: 'bold' } },
      data: [
        { value: 35, name: '超大单', itemStyle: { color: '#ef4444' } },
        { value: 25, name: '大单', itemStyle: { color: '#f97316' } },
        { value: 22, name: '中单', itemStyle: { color: '#3b82f6' } },
        { value: 18, name: '小单', itemStyle: { color: '#8b5cf6' } },
      ],
    }],
  };
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */
export default function StockDetail() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const stock = useMemo(() => getStockData(code || '000001'), [code]);
  const [activePeriod, setActivePeriod] = useState('日K');
  const periods = ['分时', '5日', '日K', '周K', '月K'];
  const priceUp = isUp(stock.changePercent);

  /* Animated counter for price */
  const [displayPrice, setDisplayPrice] = useState(stock.prevClose);
  useEffect(() => {
    const duration = 1000;
    const start = performance.now();
    const from = stock.prevClose;
    const to = stock.price;
    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayPrice(+(from + (to - from) * eased).toFixed(2));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [stock.price, stock.prevClose]);

  /* Scroll to top on code change */
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [code]);

  return (
    <div className="space-y-4">
      {/* ============================================================ */}
      {/* SECTION 1: Stock Header Bar                                  */}
      {/* ============================================================ */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
        className="rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-4 lg:p-5"
      >
        <div className="flex flex-wrap items-center gap-4 lg:gap-8">
          {/* Col 1: Code + Name */}
          <div className="flex flex-col min-w-[140px]">
            <div className="flex items-center gap-2">
              <span className="text-[24px] font-mono font-bold text-[#c9a84c] tracking-wide">{stock.code}</span>
              <TagPill variant="default">{stock.market}</TagPill>
            </div>
            <span className="text-[18px] font-semibold text-[#f1f5f9] mt-0.5">{stock.name}</span>
          </div>

          {/* Divider */}
          <div className="hidden lg:block w-px h-14 bg-[rgba(148,163,184,0.1)]" />

          {/* Col 2: Price + Change */}
          <div className="flex flex-col min-w-[120px]">
            <span className={cn('text-[36px] font-mono font-bold leading-none', priceUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
              {displayPrice.toFixed(2)}
            </span>
            <div className="flex items-center gap-2 mt-1.5">
              <MetricBadge value={stock.changePercent} />
              <span className={cn('text-[13px] font-mono', priceUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                {priceUp ? '+' : ''}{stock.changeAmount.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Divider */}
          <div className="hidden lg:block w-px h-14 bg-[rgba(148,163,184,0.1)]" />

          {/* Col 3: Today Data */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-[12px] min-w-[140px]">
            <div><span className="text-[#475569]">今开</span> <span className="font-mono text-[#f1f5f9]">{stock.open.toFixed(2)}</span></div>
            <div><span className="text-[#475569]">最高</span> <span className="font-mono text-[#ef4444]">{stock.high.toFixed(2)}</span></div>
            <div><span className="text-[#475569]">最低</span> <span className="font-mono text-[#22c55e]">{stock.low.toFixed(2)}</span></div>
            <div><span className="text-[#475569]">昨收</span> <span className="font-mono text-[#94a3b8]">{stock.prevClose.toFixed(2)}</span></div>
          </div>

          {/* Divider */}
          <div className="hidden lg:block w-px h-14 bg-[rgba(148,163,184,0.1)]" />

          {/* Col 4: Volume Data */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-[12px] min-w-[150px]">
            <div><span className="text-[#475569]">成交量</span> <span className="font-mono text-[#f1f5f9]">{stock.volume}</span></div>
            <div><span className="text-[#475569]">成交额</span> <span className="font-mono text-[#f1f5f9]">{stock.turnover}</span></div>
            <div><span className="text-[#475569]">换手率</span> <span className="font-mono text-[#f1f5f9]">{stock.turnoverRate}</span></div>
            <div><span className="text-[#475569]">量比</span> <span className={cn('font-mono', stock.volumeRatio > 2 ? 'text-[#ef4444]' : 'text-[#f1f5f9]')}>{stock.volumeRatio}</span></div>
          </div>

          {/* Divider */}
          <div className="hidden lg:block w-px h-14 bg-[rgba(148,163,184,0.1)]" />

          {/* Col 5: Score Ring + Rating */}
          <div className="flex items-center gap-3">
            <ScoreRing score={stock.score} size="md" delay={500} />
            <TagPill variant={stock.rating === 'S' ? 'gold' : stock.rating === 'A' ? 'red' : stock.rating === 'B' ? 'default' : 'gray'}>
              {stock.rating}级
            </TagPill>
          </div>

          {/* Col 6: Action Buttons */}
          <div className="flex flex-col gap-1.5 ml-auto">
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.3 }}
              className="px-4 py-1.5 bg-[#c9a84c] text-[#060b14] text-[12px] font-semibold rounded-md hover:bg-[#e0c878] transition-colors"
            >
              加入自选
            </motion.button>
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.88, duration: 0.3 }}
              className="px-4 py-1.5 border border-[#c9a84c] text-[#c9a84c] text-[12px] font-medium rounded-md hover:bg-[rgba(201,168,76,0.1)] transition-colors"
            >
              生成交易计划
            </motion.button>
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.96, duration: 0.3 }}
              className="px-4 py-1.5 border border-[rgba(148,163,184,0.2)] text-[#94a3b8] text-[12px] font-medium rounded-md hover:border-[rgba(201,168,76,0.3)] hover:text-[#f1f5f9] transition-colors"
            >
              加入锚定
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* ============================================================ */}
      {/* SECTION 2: Signal Panel (Horizontal)                         */}
      {/* ============================================================ */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-4"
      >
        <div className="flex items-center gap-2 mb-3">
          <Radio size={16} className="text-[#c9a84c]" />
          <span className="text-[16px] font-semibold text-[#f1f5f9]">全维度信号</span>
          <TagPill variant="gold">5个活跃信号</TagPill>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* Emotion Cycle */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)]">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: stock.emotionColor + '20' }}>
              <Activity size={18} style={{ color: stock.emotionColor }} />
            </div>
            <div>
              <div className="text-[11px] text-[#475569]">情绪周期</div>
              <div className="text-[13px] font-medium" style={{ color: stock.emotionColor }}>{stock.emotionPhase}</div>
            </div>
          </div>

          {/* Theme Position */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)]">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[rgba(59,130,246,0.15)]">
              <Crosshair size={18} className="text-[#3b82f6]" />
            </div>
            <div>
              <div className="text-[11px] text-[#475569]">题材定位</div>
              <div className="text-[13px] font-medium text-[#3b82f6]">{stock.themePosition}</div>
              <div className="text-[10px] text-[#475569]">{stock.themeStage}</div>
            </div>
          </div>

          {/* Anchor Status */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)]">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[rgba(6,215,215,0.15)]">
              <Anchor size={18} className="text-[#06d7d7]" />
            </div>
            <div>
              <div className="text-[11px] text-[#475569]">锚定地位</div>
              <TagPill variant={stock.anchorStatus === '龙头' ? 'gold' : 'blue'}>{stock.anchorStatus}</TagPill>
            </div>
          </div>

          {/* Yingyou Match */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)]">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[rgba(139,92,246,0.15)]">
              <Fingerprint size={18} className="text-[#8b5cf6]" />
            </div>
            <div>
              <div className="text-[11px] text-[#475569]">游资匹配</div>
              <div className="text-[13px] font-medium text-[#8b5cf6]">{stock.matchYingyou}</div>
              <div className="text-[10px] text-[#c9a84c]">匹配度{stock.matchPercent}%</div>
            </div>
          </div>

          {/* Tactics Match */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)]">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[rgba(249,115,22,0.15)]">
              <Target size={18} className="text-[#f97316]" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] text-[#475569]">战法匹配</div>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {stock.matchTactics.map((t) => (
                  <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(139,92,246,0.15)] text-[#8b5cf6] border border-[rgba(139,92,246,0.2)]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ============================================================ */}
      {/* ROW: K-Line (8 cols) + Side Info (4 cols)                    */}
      {/* ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* K-Line Chart */}
        <div className="lg:col-span-8">
          <DataCard delay={400} noPadding
            header={
              <div className="flex items-center justify-between w-full px-4 pt-4 pb-2">
                <span className="text-[16px] font-semibold text-[#f1f5f9]">日K走势</span>
                <div className="flex items-center gap-1">
                  {periods.map((p) => (
                    <button
                      key={p}
                      onClick={() => setActivePeriod(p)}
                      className={cn(
                        'px-2.5 py-1 rounded text-[11px] font-medium transition-all',
                        activePeriod === p ? 'bg-[#c9a84c] text-[#060b14]' : 'text-[#94a3b8] hover:text-[#f1f5f9]'
                      )}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            }
          >
            <div className="h-[420px] px-2 pb-2">
              <ReactECharts option={buildKLineOption(stock.kline)} style={{ height: '100%', width: '100%' }} />
            </div>
          </DataCard>
        </div>

        {/* Side Info Panel */}
        <div className="lg:col-span-4 space-y-4">
          {/* Core Metrics */}
          <DataCard delay={500}>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">市盈率</div>
                <div className="text-[14px] font-mono text-[#f1f5f9] mt-0.5">{stock.pe}</div>
              </div>
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">市净率</div>
                <div className="text-[14px] font-mono text-[#f1f5f9] mt-0.5">{stock.pb}</div>
              </div>
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">总市值</div>
                <div className="text-[14px] font-mono text-[#f1f5f9] mt-0.5">{stock.totalCap}</div>
              </div>
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">流通市值</div>
                <div className="text-[14px] font-mono text-[#f1f5f9] mt-0.5">{stock.floatCap}</div>
              </div>
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">振幅</div>
                <div className="text-[14px] font-mono text-[#c9a84c] mt-0.5">{stock.amplitude}</div>
              </div>
              <div className="text-center">
                <div className="text-[11px] text-[#475569]">委比</div>
                <div className={cn('text-[14px] font-mono mt-0.5', stock.weiBi.startsWith('+') ? 'text-[#ef4444]' : 'text-[#22c55e]')}>{stock.weiBi}</div>
              </div>
            </div>
          </DataCard>

          {/* 6D Radar */}
          <DataCard delay={600}>
            <div className="text-[13px] font-medium text-[#94a3b8] mb-2 text-center">6维评分</div>
            <div className="h-[140px]">
              <ReactECharts option={buildRadarOption(stock.dimensions)} style={{ height: '100%', width: '100%' }} />
            </div>
            <div className="text-center mt-1">
              <span className="text-[16px] font-bold text-[#c9a84c]">{stock.score}分</span>
              <span className="ml-2 text-[13px] text-[#94a3b8]">{stock.rating}级</span>
            </div>
          </DataCard>

          {/* Matched Yingyou */}
          <DataCard delay={700} className="flex-1">
            <div className="text-[13px] font-medium text-[#94a3b8] mb-3">匹配游资</div>
            <div className="space-y-3">
              {stock.matchedYingyouList.map((y) => (
                <div
                  key={y.name}
                  className="flex items-center gap-3 group cursor-pointer hover:bg-[#141e33] -mx-2 px-2 py-1.5 rounded-md transition-colors"
                  onClick={() => navigate('/yingyou')}
                >
                  <Fingerprint size={14} className="text-[#8b5cf6] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] text-[#f1f5f9] font-medium">{y.name}</span>
                      {y.tag && <TagPill variant="gold">{y.tag}</TagPill>}
                    </div>
                    <div className="w-full h-1.5 bg-[#141e33] rounded-full mt-1.5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${y.matchPercent}%` }}
                        transition={{ duration: 0.8, delay: 0.9 }}
                        className="h-full rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#c9a84c]"
                      />
                    </div>
                  </div>
                  <span className="text-[12px] font-mono text-[#c9a84c]">{y.matchPercent}%</span>
                </div>
              ))}
            </div>
          </DataCard>
        </div>
      </div>

      {/* ============================================================ */}
      {/* ROW: Signal Panel (6 cols) + Fund Flow (6 cols)                */}
      {/* ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Signal Panel */}
        <DataCard
          delay={800}
          header={
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-[#c9a84c]" />
              <span className="text-[16px] font-semibold text-[#f1f5f9]">当前信号</span>
              <TagPill variant="gold">{stock.signals.length}个活跃信号</TagPill>
            </div>
          }
        >
          <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
            {stock.signals.map((signal, idx) => (
              <motion.div
                key={signal.name}
                initial={{ x: -15, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.35, delay: 1.0 + idx * 0.08 }}
                className="flex items-start gap-3 p-2.5 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)] hover:bg-[#1a2744] transition-colors cursor-pointer group"
              >
                {/* Color bar */}
                <div className="w-[3px] self-stretch rounded-full group-hover:w-[5px] transition-all" style={{ backgroundColor: signal.color }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-medium text-[#f1f5f9]">{signal.name}</span>
                      <TagPill
                        variant={signal.status === 'confirmed' ? 'green' : signal.status === 'ongoing' ? 'gold' : 'gray'}
                      >
                        {signal.status === 'confirmed' ? '已确认' : signal.status === 'ongoing' ? '进行中' : '待验证'}
                      </TagPill>
                    </div>
                    <span className="text-[11px] font-mono text-[#475569]">{signal.time}</span>
                  </div>
                  <p className="text-[11px] text-[#94a3b8] mt-1 leading-relaxed">{signal.desc}</p>
                </div>
                <div className="shrink-0">
                  <ScoreRing score={signal.strength} size="sm" delay={1200 + idx * 100} />
                </div>
              </motion.div>
            ))}
          </div>
        </DataCard>

        {/* Fund Flow */}
        <DataCard
          delay={900}
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-[#c9a84c]" />
                <span className="text-[16px] font-semibold text-[#f1f5f9]">资金流向</span>
              </div>
              <div className="flex gap-1">
                {['实时', '5日'].map((t) => (
                  <button key={t} className="px-2 py-0.5 text-[11px] rounded text-[#94a3b8] hover:text-[#f1f5f9] bg-[#141e33] transition-colors">
                    {t}
                  </button>
                ))}
              </div>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Main inflow number */}
            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-[11px] text-[#475569] mb-1">主力净流入</div>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={cn(
                    'text-[24px] font-mono font-bold',
                    stock.fundFlow.mainNetInflow.startsWith('+') ? 'text-[#ef4444]' : 'text-[#22c55e]'
                  )}
                >
                  {stock.fundFlow.mainNetInflow}
                </motion.div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className="text-[10px] text-[#475569]">龙虎榜质量</div>
                  <div className="text-[14px] font-mono text-[#c9a84c] font-semibold">{stock.fundFlow.dragonTigerQuality}</div>
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-[#475569]">封单强度</div>
                  <div className="text-[14px] font-mono text-[#c9a84c] font-semibold">{stock.fundFlow.sealStrength}</div>
                </div>
              </div>
            </div>

            {/* Fund area chart + pie */}
            <div className="flex gap-3">
              <div className="flex-1 h-[120px]">
                <ReactECharts option={buildFundAreaOption(stock.fundFlow.timeline)} style={{ height: '100%', width: '100%' }} />
              </div>
              <div className="w-[100px] h-[120px]">
                <ReactECharts option={buildFundPieOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            </div>

            {/* Fund breakdown table */}
            <div className="grid grid-cols-4 gap-2">
              {stock.fundFlow.breakdown.map((b) => (
                <div key={b.type} className="text-center p-1.5 rounded bg-[#141e33]">
                  <div className="text-[10px] text-[#475569]">{b.type}</div>
                  <div className="text-[11px] font-mono text-[#ef4444]">{b.inflow}</div>
                  <div className="text-[11px] font-mono text-[#22c55e]">{b.outflow}</div>
                  <div className={cn('text-[11px] font-mono font-semibold', b.net.startsWith('+') ? 'text-[#ef4444]' : 'text-[#22c55e]')}>{b.net}</div>
                </div>
              ))}
            </div>
          </div>
        </DataCard>
      </div>

      {/* ============================================================ */}
      {/* ROW: Related Themes (6 cols) + Trading Plan (6 cols)           */}
      {/* ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Related Themes */}
        <DataCard
          delay={1100}
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <MapPin size={16} className="text-[#c9a84c]" />
                <span className="text-[16px] font-semibold text-[#f1f5f9]">关联题材</span>
              </div>
              <span className="text-[11px] text-[#94a3b8]">{stock.themes.length}个题材</span>
            </div>
          }
        >
          <div className="space-y-3">
            {stock.themes.map((theme, idx) => (
              <motion.div
                key={theme.name}
                initial={{ y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.4, delay: 1.3 + idx * 0.1 }}
                className="p-3 rounded-lg bg-[#141e33] border border-[rgba(148,163,184,0.06)] hover:bg-[#1a2744] transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[14px] font-medium text-[#f1f5f9]">{theme.name}</span>
                    <TagPill
                      variant={theme.position === '板块龙头' ? 'gold' : theme.position === '龙二' ? 'blue' : 'gray'}
                    >
                      {theme.position}
                    </TagPill>
                  </div>
                  <MetricBadge value={parseFloat(theme.change)} />
                </div>

                {/* Heat bar */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] text-[#475569]">热度</span>
                  <div className="flex-1 h-1.5 bg-[#0d1526] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${theme.heat}%` }}
                      transition={{ duration: 0.6, delay: 1.5 + idx * 0.15 }}
                      className="h-full rounded-full bg-gradient-to-r from-[#8a7530] to-[#c9a84c]"
                    />
                  </div>
                  <span className="text-[10px] font-mono text-[#c9a84c]">{theme.heat}</span>
                </div>

                {/* Constituents list */}
                <div className="space-y-1">
                  {theme.constituents.map((c) => (
                    <div
                      key={c.code}
                      className="flex items-center justify-between py-1 px-2 rounded hover:bg-[#0d1526] transition-colors cursor-pointer"
                      onClick={() => navigate(`/stock/${c.code}`)}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono text-[#475569]">{c.code}</span>
                        <span className="text-[12px] text-[#f1f5f9]">{c.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] font-mono text-[#f1f5f9]">{c.price.toFixed(2)}</span>
                        <span className={cn('text-[11px] font-mono', c.changePercent >= 0 ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                          {c.changePercent >= 0 ? '+' : ''}{c.changePercent.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Related tags */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {theme.related.map((r) => (
                    <span key={r} className="text-[10px] text-[#475569]">{r}</span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </DataCard>

        {/* Trading Plan */}
        <DataCard
          delay={1200}
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <TrendingUp size={16} className="text-[#c9a84c]" />
                <span className="text-[16px] font-semibold text-[#f1f5f9]">交易计划速览</span>
              </div>
              <button
                onClick={() => navigate('/scoring')}
                className="text-[11px] text-[#c9a84c] hover:text-[#e0c878] flex items-center gap-0.5 transition-colors"
              >
                查看完整计划 <ChevronRight size={12} />
              </button>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Key info grid */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: '综合评分', value: `${stock.score}分 ${stock.rating}级`, color: 'text-[#c9a84c]' },
                { label: '建议仓位', value: stock.tradingPlan.position, color: 'text-[#c9a84c]' },
                { label: '风险收益比', value: stock.tradingPlan.rrRatio, color: 'text-[#22c55e]' },
                { label: '建议操作', value: stock.tradingPlan.action, color: 'text-[#f1f5f9]' },
              ].map((item, idx) => (
                <motion.div
                  key={item.label}
                  initial={{ x: 10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 1.4 + idx * 0.08 }}
                  className="p-2.5 rounded-lg bg-[#141e33]"
                >
                  <div className="text-[11px] text-[#475569]">{item.label}</div>
                  <div className={cn('text-[16px] font-semibold mt-0.5', item.color)}>{item.value}</div>
                </motion.div>
              ))}
            </div>

            {/* Entry/Stop/Profit details */}
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 rounded-lg bg-[#141e33] border border-[rgba(59,130,246,0.2)]">
                <div className="text-[10px] text-[#3b82f6]">建议入场</div>
                <div className="text-[13px] font-mono text-[#f1f5f9] font-semibold">{stock.tradingPlan.entryRange}</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-[#141e33] border border-[rgba(239,68,68,0.2)]">
                <div className="text-[10px] text-[#ef4444]">止损</div>
                <div className="text-[13px] font-mono text-[#f1f5f9] font-semibold">{stock.tradingPlan.stopLoss}</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-[#141e33] border border-[rgba(34,197,94,0.2)]">
                <div className="text-[10px] text-[#22c55e]">止盈</div>
                <div className="text-[13px] font-mono text-[#f1f5f9] font-semibold">{stock.tradingPlan.takeProfit}</div>
              </div>
            </div>

            {/* Suggestion quote */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.6 }}
              className="relative pl-3 py-2 pr-2 bg-[#141e33] rounded-md"
            >
              <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-md" />
              <p className="text-[12px] text-[#94a3b8] leading-relaxed">{stock.tradingPlan.suggestion}</p>
            </motion.div>

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/scoring')}
                className="flex-1 py-2 bg-[#c9a84c] text-[#060b14] text-[13px] font-semibold rounded-md hover:bg-[#e0c878] transition-colors"
              >
                生成完整计划
              </button>
              <button className="flex-1 py-2 border border-[rgba(148,163,184,0.2)] text-[#94a3b8] text-[13px] font-medium rounded-md hover:border-[rgba(201,168,76,0.3)] hover:text-[#f1f5f9] transition-colors">
                加入锚定列表
              </button>
            </div>
          </div>
        </DataCard>
      </div>

      {/* ============================================================ */}
      {/* Composite Score Section (large ScoreRing + rating)             */}
      {/* ============================================================ */}
      <motion.div
        initial={{ scale: 0.97, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: 1.0 }}
        className="rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-6"
      >
        <div className="flex flex-col md:flex-row items-center justify-center gap-8">
          <ScoreRing score={stock.score} size="lg" label="综合评分" delay={1200} />
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="flex items-baseline gap-3">
              <span className="text-[48px] font-mono font-bold text-[#c9a84c] leading-none">{stock.score}</span>
              <span className="text-[24px] text-[#94a3b8]">分</span>
              <TagPill variant={stock.rating === 'S' ? 'gold' : stock.rating === 'A' ? 'red' : 'default'} className="text-[14px] px-3 py-1">
                {stock.rating}级
              </TagPill>
            </div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-x-4 gap-y-2 mt-2">
              {stock.dimensions.map((d) => (
                <div key={d.name} className="text-center">
                  <div className="text-[10px] text-[#475569]">{d.name}</div>
                  <div className={cn(
                    'text-[14px] font-mono font-semibold',
                    d.score >= 80 ? 'text-[#c9a84c]' : d.score >= 60 ? 'text-[#eab308]' : 'text-[#ef4444]'
                  )}>
                    {d.score}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* ============================================================ */}
      {/* Risk Warning Strip                                             */}
      {/* ============================================================ */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 1.4 }}
        className="rounded-[10px] border border-[rgba(239,68,68,0.3)] bg-[rgba(239,68,68,0.06)] p-4"
      >
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert size={18} className="text-[#ef4444]" />
          <span className="text-[16px] font-semibold text-[#ef4444]">风险警示</span>
          <TagPill variant="red">{stock.risks.length}项风险</TagPill>
        </div>
        <div className="space-y-2">
          {stock.risks.map((risk, idx) => (
            <motion.div
              key={idx}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 1.6 + idx * 0.1 }}
              className="flex items-start gap-2"
            >
              <AlertTriangle size={14} className="text-[#ef4444] shrink-0 mt-0.5" />
              <span className="text-[13px] text-[#f1f5f9] leading-relaxed">{risk}</span>
            </motion.div>
          ))}
        </div>
        <div className="mt-3 h-1 w-full bg-[rgba(239,68,68,0.1)] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(20, 100 - stock.score)}%` }}
            transition={{ duration: 1.5, delay: 1.8 }}
            className="h-full rounded-full bg-gradient-to-r from-[#ef4444] to-[#f97316]"
          />
        </div>
        <div className="text-center text-[11px] text-[#475569] mt-1">风险指数: {Math.max(20, 100 - stock.score)}%</div>
      </motion.div>
    </div>
  );
}
