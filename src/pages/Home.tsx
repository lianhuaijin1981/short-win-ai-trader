// 融合首页 - 市场概览 + 情绪分析 + 核心数据
import { useEffect, useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import {
  Activity,
  Eye,
  Fingerprint,
  Target,
  BarChart3,
  ClipboardCheck,
  Newspaper,
  ArrowRight,
  RefreshCw,
  Calendar,
  ChevronDown,
  ChevronUp,
  Calculator,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import ScoreRing from '@/components/ScoreRing';
import MetricBadge from '@/components/MetricBadge';
import StockRow from '@/components/StockRow';
import AlertTicker from '@/components/AlertTicker';
import DataStatusBar from '@/components/DataStatusBar';
import IndicatorDetailModal from '@/components/IndicatorDetailModal';
import DayDetailModal from '@/components/DayDetailModal';
import type { DayHistoryData } from '@/components/DayDetailModal';
import {
  REAL_INDICES,
  REAL_BREADTH,
  REAL_SENTIMENT,
  REAL_LIMIT_UP_STOCKS,
  REAL_YINGYOU_RECS,
  TACTIC_RULES,
  REAL_SECTOR_ALERTS,
  REAL_PREDICTION,
} from '@/data/realData';
import {
  moduleCards,
  dataStatus,
} from '@/data/mockData';
import { cn } from '@/lib/utils';
import swatAPI from '@/services/api';

const moduleIconMap: Record<string, React.ElementType> = {
  Activity, Eye, Fingerprint, Target, BarChart3, ClipboardCheck, Newspaper,
};

/* ================================================================
   类型定义
   ================================================================ */
interface MarketIndex {
  name: string;
  code: string;
  value: number;
  change: number;
  changePercent: number;
}

/* ─── 基于真实数据构建组件所需数据结构 ─── */

// 市场指数
const marketIndices: MarketIndex[] = REAL_INDICES.map((idx) => ({
  name: idx.name,
  code: idx.code,
  value: idx.value,
  change: idx.change,
  changePercent: idx.changePercent,
}));

// 市场情绪
const sentimentData = {
  phase: REAL_SENTIMENT.phase,
  phaseColor: REAL_SENTIMENT.phaseColor,
  score: REAL_SENTIMENT.score,
};

// Top5 股票
interface TopStock {
  rank: number;
  code: string;
  name: string;
  signals: string[];
  score: number;
  matchYingyou: string;
  action: 'intervene' | 'observe' | 'hold';
}

const topStocks: TopStock[] = REAL_LIMIT_UP_STOCKS.slice(0, 5).map((s) => {
  const signals = [
    s.reasons[0] ?? '真实涨停',
    s.tacticsMatched[0] ?? '强势封板',
  ].filter(Boolean);
  const score = Math.min(
    98,
    Math.round(
      60 +
        s.consecutiveBoards * 8 +
        s.volTo20d * 5 +
        s.tacticsMatched.length * 6 +
        (s.changePct >= 10 ? 5 : 0)
    )
  );
  const action: TopStock['action'] =
    s.consecutiveBoards >= 4 ? 'intervene' : s.consecutiveBoards >= 1 ? 'observe' : 'hold';
  return {
    rank: s.rank,
    code: s.code,
    name: s.name,
    signals,
    score,
    matchYingyou: s.yingyouMatch || '—',
    action,
  };
});

// 游资推荐
const yingyouRecommends = REAL_YINGYOU_RECS.slice(0, 5);

// 今日战法
interface TacticItem {
  name: string;
  triggerCount: number;
  successRate: number;
  trend: ('up' | 'down')[];
}

function generateTrend(triggerCount: number, successRate: number): ('up' | 'down')[] {
  const baseUp = Math.min(6, Math.max(0, Math.round((successRate / 100) * 4 + triggerCount * 0.2)));
  const trend: ('up' | 'down')[] = [];
  for (let i = 0; i < 6; i++) {
    trend.push(i < baseUp ? 'up' : 'down');
  }
  return trend.sort(() => (Math.random() > 0.5 ? 1 : -1));
}

const todayTactics: TacticItem[] = TACTIC_RULES.filter((t) => t.triggerCount > 0)
  .slice(0, 5)
  .map((t) => ({
    name: t.name,
    triggerCount: t.triggerCount,
    successRate: t.successRate,
    trend: generateTrend(t.triggerCount, t.successRate),
  }));

// 预警消息
interface AlertMessage {
  time: string;
  type: '机会' | '风险' | '提示';
  content: string;
}

const alertMessages: AlertMessage[] = [
  {
    time: '14:32:05',
    type: '风险',
    content: `上证指数跌破4150关口，当前${REAL_INDICES[0].value}，跌幅 ${REAL_INDICES[0].changePercent}%`,
  },
  {
    time: '14:30:18',
    type: '风险',
    content: `两市下跌${REAL_BREADTH.downCount}家，跌停${REAL_BREADTH.limitDown}只，情绪退潮，建议减仓`,
  },
  {
    time: '14:28:44',
    type: '提示',
    content: `市场情绪进入${REAL_SENTIMENT.phase}，总仓位控制在${REAL_SENTIMENT.positionLimit}%以内`,
  },
  ...REAL_SECTOR_ALERTS.slice(0, 3).map((alert, i) => {
    const minutes = 25 - i * 3;
    const stockMap = new Map(REAL_LIMIT_UP_STOCKS.map((s) => [s.code, s.name]));
    const affectedStr = alert.affected
      .slice(0, 2)
      .map((code) => `${stockMap.get(code) ?? ''} ${code}`)
      .join(' | ');
    return {
      time: `14:${String(minutes).padStart(2, '0')}:00`,
      type: (alert.urgency === '高' && alert.type.includes('流出') ? '风险' : alert.type.includes('流入') || alert.type.includes('强') ? '机会' : '提示') as '机会' | '风险' | '提示',
      content: `${alert.sector}: ${alert.trigger}${affectedStr ? ` (${affectedStr})` : ''}`,
    };
  }),
  {
    time: '14:22:38',
    type: '机会',
    content: `利仁科技 001259 5连板涨停封板，${REAL_LIMIT_UP_STOCKS[0].yingyouMatch}模式匹配98%`,
  },
  {
    time: '14:15:33',
    type: '提示',
    content: REAL_PREDICTION.advice,
  },
];

/* ─── 情绪周期相关 ─── */
interface SentimentPhase {
  name: string;
  color: string;
  order: number;
}

interface Indicator {
  name: string;
  value: string;
  status: 'good' | 'neutral' | 'warning';
  desc: string;
  sparkline: number[];
}

interface ThemeItem {
  rank: number;
  name: string;
  heat: number;
  limitUp: number;
  leader: string;
  leaderCode: string;
  phase: string;
  phaseColor: string;
}

const PHASES: SentimentPhase[] = [
  { name: '混沌期', color: '#6b7280', order: 1 },
  { name: '启动期', color: '#3b82f6', order: 2 },
  { name: '发酵期', color: '#06d7d7', order: 3 },
  { name: '高潮期', color: '#c9a84c', order: 4 },
  { name: '分歧期', color: '#f97316', order: 5 },
  { name: '退潮期', color: '#ef4444', order: 6 },
];

const CURRENT_PHASE_INDEX = 5;
const CURRENT_PHASE = PHASES[CURRENT_PHASE_INDEX];

// 情绪温度计算
const calcTemperature = (): { temp: number; formula: string; details: { label: string; value: string; weight: number; score: number }[] } => {
  const dimensions = [
    { label: '涨跌停比', value: '62.1%', weight: 25, raw: 62.1 },
    { label: '涨跌中位数', value: '-2.0%', weight: 20, raw: 30 },
    { label: '量能维持率', value: '46%', weight: 15, raw: 46 },
    { label: '连板高度', value: '5板', weight: 15, raw: 50 },
    { label: '连板晋级率', value: '22%', weight: 10, raw: 22 },
    { label: '炸板率(反向)', value: '38.5%', weight: 15, raw: 61.5 },
  ];

  const totalWeight = dimensions.reduce((s, d) => s + d.weight, 0);
  const weightedScore = dimensions.reduce((s, d) => s + (d.raw * d.weight / totalWeight), 0);
  const phaseAdjust = 0.85;
  const finalTemp = Math.round(weightedScore * phaseAdjust);

  const details = dimensions.map(d => ({
    label: d.label,
    value: d.value,
    weight: d.weight,
    score: Math.round(d.raw * d.weight / totalWeight),
  }));

  return { temp: finalTemp, formula: '温度 = Σ(维度得分 × 权重) × 阶段修正系数', details };
};

const INDICATORS: Indicator[] = [
  { name: '涨跌停家数比', value: '62.1%', status: 'good', desc: '盘中:涨停72家/跌停44家', sparkline: [70, 68, 65, 63, 62.1] },
  { name: '连板高度', value: '6板', status: 'good', desc: '盘中实时:蒙娜丽莎6连板', sparkline: [4, 5, 5, 6, 6] },
  { name: '炸板率', value: '38.5%', status: 'warning', desc: '盘中实时:炸板率38.5%', sparkline: [25, 28, 32, 35, 38.5] },
  { name: '跌停家数', value: '44家', status: 'warning', desc: '盘中实时:跌停44家', sparkline: [5, 8, 15, 25, 44] },
  { name: '涨跌中位数', value: '-2.0%', status: 'warning', desc: '盘中实时:全A涨跌中位数-2.0%', sparkline: [1.2, 0.5, -0.3, -1.0, -2.0] },
  { name: '连板晋级率', value: '100%', status: 'good', desc: '盘中实时:昨3只连板全部晋级', sparkline: [55, 48, 60, 80, 100] },
  { name: '昨涨停今表现', value: '-1.4%', status: 'warning', desc: '05-14涨停51只今日中位数-1.4%', sparkline: [3.5, 1.2, -0.5, -0.8, -1.4] },
  { name: '昨连板今表现', value: '+10.0%', status: 'good', desc: '05-14连板3只今日平均+10.0%', sparkline: [8.5, 6.2, 7.0, 8.0, 10.0] },
  { name: '题材集中度', value: '36%', status: 'good', desc: '盘中实时:TOP3题材占36%', sparkline: [55, 50, 45, 40, 36] },
  { name: '量能维持率', value: '46%', status: 'warning', desc: '盘中实时:量能维持率46%', sparkline: [85, 75, 65, 55, 46] },
  { name: '北向资金', value: '-35.8亿', status: 'warning', desc: '盘中实时:北向净流出-35.8亿', sparkline: [25, 10, -5, -18, -35.8] },
  { name: '恐慌指数', value: '45', status: 'warning', desc: '盘中实时:恐慌指数45(中度)', sparkline: [15, 20, 28, 35, 45] },
];

const THEME_DATA: ThemeItem[] = [
  { rank: 1, name: '消费电子', heat: 92, limitUp: 3, leader: '利仁科技', leaderCode: '001259', phase: '高潮', phaseColor: '#c9a84c' },
  { rank: 2, name: '化工新材料', heat: 85, limitUp: 3, leader: '光华股份', leaderCode: '001333', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 3, name: '机器人', heat: 78, limitUp: 2, leader: '巨轮智能', leaderCode: '002031', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 4, name: '建材', heat: 65, limitUp: 2, leader: '瑞泰科技', leaderCode: '002066', phase: '启动', phaseColor: '#3b82f6' },
  { rank: 5, name: '文化传媒', heat: 52, limitUp: 1, leader: '粤传媒', leaderCode: '002181', phase: '分歧', phaseColor: '#f97316' },
  { rank: 6, name: '氟化工', heat: 45, limitUp: 1, leader: '多氟多', leaderCode: '002407', phase: '退潮', phaseColor: '#ef4444' },
];

const POSITION_STRATEGY: Record<string, { position: string; range: string; tactics: { text: string; color: string }[] }> = {
  '混沌期': { position: '20%', range: '10%-30%', tactics: [{ text: '空仓观望，等待方向', color: 'red' }, { text: '小仓位试错新题材', color: 'yellow' }, { text: '不追高，不抄底', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '启动期': { position: '40%', range: '30%-50%', tactics: [{ text: '低吸为主，分批建仓', color: 'green' }, { text: '关注首板机会', color: 'green' }, { text: '单票不超过20%', color: 'yellow' }, { text: '设好止损线', color: 'red' }] },
  '发酵期': { position: '60%', range: '50%-70%', tactics: [{ text: '积极做多，持股为主', color: 'green' }, { text: '关注龙头分歧转一致', color: 'green' }, { text: '避免后排跟风股', color: 'yellow' }, { text: '控制回撤-3%', color: 'red' }] },
  '高潮期': { position: '30%', range: '20%-40%', tactics: [{ text: '不追高，以低吸为主', color: 'yellow' }, { text: '控制回撤，单票不超20%', color: 'yellow' }, { text: '关注分歧转一致机会', color: 'green' }, { text: '设定-3%强制止损线', color: 'red' }] },
  '分歧期': { position: '30%', range: '20%-40%', tactics: [{ text: '减仓为主，锁定利润', color: 'yellow' }, { text: '不参与高位博弈', color: 'red' }, { text: '等待情绪明朗', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '退潮期': { position: '10%', range: '0%-20%', tactics: [{ text: '空仓或极小仓位', color: 'red' }, { text: '不参与任何接力', color: 'red' }, { text: '等待新周期启动', color: 'yellow' }, { text: '清仓观望', color: 'red' }] },
};

const HISTORY_DATA: DayHistoryData[] = [
  { date: '05-06', score: 35, phase: '混沌期', limitUp: 25, limitDown: 12, upCount: 1200, downCount: 3800, medianChange: -1.5, northBound: -15.2, volumeRatio: 65, leadSectors: [{ name: '消费电子', changePct: 2.3, stocks: 5 }], lagSectors: [{ name: '半导体', changePct: -3.2, stocks: 8 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -8.5, sector: '氟化工' }] },
  { date: '05-07', score: 42, phase: '启动期', limitUp: 38, limitDown: 8, upCount: 2100, downCount: 2800, medianChange: 0.3, northBound: 8.5, volumeRatio: 72, leadSectors: [{ name: '消费电子', changePct: 3.5, stocks: 8 }], lagSectors: [{ name: '半导体', changePct: -2.1, stocks: 6 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -5.2, sector: '氟化工' }] },
  { date: '05-08', score: 55, phase: '启动期', limitUp: 52, limitDown: 5, upCount: 3100, downCount: 1800, medianChange: 1.2, northBound: 22.3, volumeRatio: 85, leadSectors: [{ name: '消费电子', changePct: 4.8, stocks: 12 }], lagSectors: [{ name: '银行', changePct: -0.5, stocks: 2 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -1.2, sector: '氟化工' }] },
  { date: '05-09', score: 62, phase: '发酵期', limitUp: 68, limitDown: 3, upCount: 3800, downCount: 1100, medianChange: 2.1, northBound: 35.8, volumeRatio: 92, leadSectors: [{ name: '消费电子', changePct: 5.2, stocks: 15 }], lagSectors: [{ name: '银行', changePct: -0.3, stocks: 1 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [] },
  { date: '05-12', score: 58, phase: '发酵期', limitUp: 55, limitDown: 8, upCount: 3200, downCount: 1700, medianChange: 0.8, northBound: 15.2, volumeRatio: 78, leadSectors: [{ name: '消费电子', changePct: 3.2, stocks: 10 }], lagSectors: [{ name: '半导体', changePct: -2.5, stocks: 5 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -4.5, sector: '氟化工' }] },
  { date: '05-13', score: 48, phase: '分歧期', limitUp: 38, limitDown: 22, upCount: 1800, downCount: 3100, medianChange: -0.8, northBound: -8.5, volumeRatio: 62, leadSectors: [{ name: '消费电子', changePct: 1.5, stocks: 5 }], lagSectors: [{ name: '半导体', changePct: -4.2, stocks: 10 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -8.2, sector: '氟化工' }] },
  { date: '05-14', score: 45, phase: '分歧期', limitUp: 28, limitDown: 35, upCount: 1000, downCount: 3900, medianChange: -1.8, northBound: -22.5, volumeRatio: 52, leadSectors: [{ name: '消费电子', changePct: 0.5, stocks: 3 }], lagSectors: [{ name: '半导体', changePct: -5.8, stocks: 12 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -9.5, sector: '氟化工' }] },
  { date: '05-15', score: 40, phase: '退潮期', limitUp: 10, limitDown: 44, upCount: 831, downCount: 4382, medianChange: -2.0, northBound: -35.8, volumeRatio: 46, leadSectors: [{ name: '消费电子', changePct: 1.2, stocks: 3 }], lagSectors: [{ name: '半导体', changePct: -4.5, stocks: 12 }], leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }], lagStocks: [{ code: '002407', name: '多氟多', changePct: -8.5, sector: '氟化工' }] },
];

/* ─── Animated Number Component ─── */
function AnimatedNumber({ value, decimals = 2 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 1200;
    const start = performance.now();
    const animate = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(value * eased);
      if (t < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [value]);

  return <span>{display.toFixed(decimals)}</span>;
}

/* ─── Mini Sparkline SVG ─── */
function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 40;
  const height = 14;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * height}`).join(' ');
  return (
    <svg width={width} height={height} className="opacity-70">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─── Helpers ─── */
const statusColor = (status: string) => {
  switch (status) {
    case 'good': return 'bg-[#ef4444]';
    case 'neutral': return 'bg-[#eab308]';
    case 'warning': return 'bg-[#22c55e]';
    default: return 'bg-[#6b7280]';
  }
};

const statusDotColor = (status: string) => {
  switch (status) {
    case 'good': return '#ef4444';
    case 'neutral': return '#eab308';
    case 'warning': return '#22c55e';
    default: return '#6b7280';
  }
};

/* ─── Market Overview ─── */
interface ApiDataType {
  indices: any[];
  stats: any;
  limitUpStocks: any[];
  date: string;
}

function MarketOverview({ apiData }: { apiData: ApiDataType | null }) {
  const [indices, setIndices] = useState<MarketIndex[]>(marketIndices);
  const [breadth, setBreadth] = useState({
    upCount: REAL_BREADTH.upCount,
    downCount: REAL_BREADTH.downCount,
    limitUp: REAL_BREADTH.limitUp,
    limitDown: REAL_BREADTH.limitDown,
    volume: REAL_BREADTH.volume,
    prevVolume: REAL_BREADTH.prevVolume,
    volumeChange: REAL_BREADTH.volumeChange,
    totalStocks: REAL_BREADTH.totalStocks,
  });

  // 使用API数据更新指数
  useEffect(() => {
    if (apiData?.indices?.length) {
      const apiIndices: MarketIndex[] = apiData.indices.map((idx: any) => ({
        name: idx.name,
        code: idx.code,
        value: idx.current,
        change: idx.change,
        changePercent: idx.change_pct,
      }));
      setIndices(apiIndices);
    }
  }, [apiData?.indices]);

  // 使用API数据更新市场宽度
  useEffect(() => {
    if (apiData?.stats) {
      setBreadth({
        upCount: apiData.stats.rise_count || REAL_BREADTH.upCount,
        downCount: apiData.stats.fall_count || REAL_BREADTH.downCount,
        limitUp: apiData.stats.limit_up_count || REAL_BREADTH.limitUp,
        limitDown: apiData.stats.limit_down_count || REAL_BREADTH.limitDown,
        volume: Math.round((apiData.stats.total_volume || 0) / 100000000),
        prevVolume: REAL_BREADTH.prevVolume,
        volumeChange: REAL_BREADTH.volumeChange,
        totalStocks: apiData.stats.total_stocks || REAL_BREADTH.totalStocks,
      });
    }
  }, [apiData?.stats]);

  // 模拟实时波动
  useEffect(() => {
    const interval = setInterval(() => {
      setIndices((prev) =>
        prev.map((idx) => {
          const delta = (Math.random() - 0.48) * 2;
          const newValue = idx.value + delta;
          const newChange = idx.change + delta * 0.1;
          return {
            ...idx,
            value: newValue,
            change: newChange,
            changePercent: (newChange / (newValue - newChange)) * 100,
          };
        })
      );
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const totalStocks = breadth.upCount + breadth.downCount;
  const upPercent = totalStocks > 0 ? (breadth.upCount / totalStocks) * 100 : 50;
  const downPercent = totalStocks > 0 ? (breadth.downCount / totalStocks) * 100 : 50;
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ x: -30, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number, number, number, number], delay: 0.1 }}
      className="col-span-12 h-[100px] bg-[#0d1526] rounded-[10px] border border-[rgba(148,163,184,0.1)] flex items-center gap-6 px-6 relative overflow-hidden hover:border-[rgba(201,168,76,0.3)] transition-colors duration-200"
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-gradient-to-b from-[#c9a84c] via-[#e0c878] to-[#c9a84c]" />

      {indices.map((idx) => (
        <div key={idx.code} className="flex flex-col gap-0.5 min-w-[130px]">
          <span className="text-[11px] text-[#475569]">{idx.name}</span>
          <div className="flex items-center gap-2">
            <span className="text-[24px] font-mono font-bold text-[#f1f5f9] leading-none">
              <AnimatedNumber value={idx.value} />
            </span>
            <MetricBadge value={idx.changePercent} />
          </div>
        </div>
      ))}

      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      <div className="flex flex-col gap-1 min-w-[160px]">
        <span className="text-[11px] text-[#475569]">涨跌分布</span>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-3 bg-[#141e33] rounded-full overflow-hidden flex">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${upPercent}%` }}
              transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              className="h-full bg-[#ef4444] rounded-l-full"
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${downPercent}%` }}
              transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              className="h-full bg-[#22c55e] rounded-r-full"
            />
          </div>
        </div>
        <div className="flex justify-between text-[10px] font-mono">
          <span className="text-[#ef4444]">{breadth.upCount}</span>
          <span className="text-[#22c55e]">{breadth.downCount}</span>
        </div>
      </div>

      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      <div className="flex flex-col gap-1 min-w-[80px]">
        <span className="text-[11px] text-[#475569]">涨停/跌停</span>
        <div className="flex items-center gap-2">
          <span className="text-[18px] font-mono font-semibold text-[#ef4444]">{breadth.limitUp}</span>
          <span className="text-[#475569]">/</span>
          <span className="text-[18px] font-mono font-semibold text-[#22c55e]">{breadth.limitDown}</span>
        </div>
      </div>

      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      <div
        className="flex items-center gap-3 cursor-pointer group"
        onClick={() => navigate('/sentiment')}
      >
        <div className="flex flex-col gap-0.5">
          <span className="text-[11px] text-[#475569]">市场情绪</span>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#c9a84c]/20 text-[#c9a84c] border border-[#c9a84c]/30 w-fit">
            {sentimentData.phase}
          </span>
        </div>
        <ScoreRing score={sentimentData.score} size="sm" />
      </div>

      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      <div className="flex flex-col gap-0.5 min-w-[100px]">
        <span className="text-[11px] text-[#475569]">成交额</span>
        <span className="text-[18px] font-mono font-semibold text-[#f1f5f9]">
          <AnimatedNumber value={breadth.volume} decimals={0} />亿
        </span>
      </div>
    </motion.div>
  );
}

/* ─── Sentiment Cycle Ring ─── */
function SentimentCycleCard() {
  const { temp, formula, details } = calcTemperature();
  const [showFormula, setShowFormula] = useState(false);
  const navigate = useNavigate();

  const tempColor = temp >= 80 ? '#ef4444' : temp >= 60 ? '#c9a84c' : temp >= 40 ? '#06d7d7' : '#3b82f6';

  const cycleOption = useMemo(() => {
    const data = PHASES.map((p, i) => ({
      value: 1,
      name: p.name,
      itemStyle: {
        color: i === CURRENT_PHASE_INDEX ? p.color : `${p.color}66`,
        borderRadius: 4,
        borderWidth: i === CURRENT_PHASE_INDEX ? 3 : 1,
        borderColor: i === CURRENT_PHASE_INDEX ? '#c9a84c' : 'transparent',
        shadowBlur: i === CURRENT_PHASE_INDEX ? 20 : 0,
        shadowColor: i === CURRENT_PHASE_INDEX ? `${p.color}88` : 'transparent',
      },
      label: {
        show: i === CURRENT_PHASE_INDEX,
        position: 'inner' as const,
        formatter: () => `{center|${p.name}}`,
        rich: {
          center: { fontSize: 16, fontWeight: 'bold', color: '#fff', fontFamily: 'Noto Sans SC' },
        },
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 20,
          shadowColor: `${p.color}88`,
        },
      },
    }));

    return {
      tooltip: {
        trigger: 'item' as const,
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: { name: string; color: string }) => {
          const phase = PHASES.find(p => p.name === params.name);
          return `<div style="font-weight:bold;margin-bottom:4px;color:${phase?.color}">${params.name}</div>
            <div style="font-size:12px;color:#94a3b8">阶段序号: ${phase?.order}/6</div>`;
        },
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '78%'],
          center: ['50%', '48%'],
          avoidLabelOverlap: true,
          padAngle: 3,
          itemStyle: { borderRadius: 6 },
          label: {
            show: true,
            position: 'outside' as const,
            formatter: '{name|{b}}',
            rich: {
              name: { fontSize: 12, color: '#94a3b8', fontFamily: 'Noto Sans SC' },
            },
          },
          labelLine: {
            length: 12,
            length2: 8,
            lineStyle: { color: 'rgba(148,163,184,0.2)' },
          },
          emphasis: { scaleSize: 8, itemStyle: { shadowBlur: 25 } },
          data,
          animationType: 'scale' as const,
          animationEasing: 'elasticOut' as const,
          animationDelay: (idx: number) => idx * 100,
        },
        {
          type: 'pie',
          radius: ['42%', '43%'],
          center: ['50%', '48%'],
          silent: true,
          label: { show: false },
          data: [{ value: 1, itemStyle: { color: 'rgba(201,168,76,0.15)' } }],
        },
      ],
      graphic: [
        {
          type: 'text',
          left: 'center',
          top: '38%',
          style: { text: `${CURRENT_PHASE.order}/6`, fill: '#c9a84c', fontSize: 36, fontWeight: 'bold', fontFamily: 'JetBrains Mono', textAlign: 'center' },
        },
        {
          type: 'text',
          left: 'center',
          top: '48%',
          style: { text: CURRENT_PHASE.name, fill: CURRENT_PHASE.color, fontSize: 18, fontWeight: '600', fontFamily: 'Noto Sans SC', textAlign: 'center' },
        },
        {
          type: 'text',
          left: 'center',
          top: '56%',
          style: { text: `温度 ${temp}°C`, fill: tempColor, fontSize: 13, fontFamily: 'JetBrains Mono', textAlign: 'center' },
        },
      ],
    };
  }, [temp, tempColor]);

  return (
    <DataCard delay={200} header={
      <>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c9a84c] opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#c9a84c]" />
          </span>
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">情绪周期</h2>
        </div>
        <button
          onClick={() => navigate('/sentiment')}
          className="text-[12px] text-[#c9a84c] hover:underline flex items-center gap-1 transition-colors"
        >
          详情 <ArrowRight size={14} />
        </button>
      </>
    }>
      <ReactECharts option={cycleOption} style={{ height: 240 }} />
      <div className="mt-2">
        <button
          onClick={() => setShowFormula(!showFormula)}
          className="flex items-center gap-1 text-[11px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors"
        >
          <Calculator size={12} />
          {showFormula ? '隐藏计算公式' : '查看计算公式'}
          {showFormula ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
        {showFormula && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-2 p-3 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.1)]"
          >
            <div className="text-[11px] text-[#c9a84c] font-mono mb-2">{formula}</div>
            <div className="space-y-1">
              {details.map((d, i) => (
                <div key={i} className="flex items-center justify-between text-[10px]">
                  <span className="text-[#475569]">{d.label}({d.value})</span>
                  <span className="text-[#94a3b8]">权重{d.weight}% × 得分{d.score}分</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
      <div className="grid grid-cols-4 gap-2 mt-2 pt-3 border-t border-[rgba(148,163,184,0.1)]">
        {[
          { label: '昨日阶段', value: '分歧期', color: '#f97316' },
          { label: '阶段持续', value: '第1天', color: '#c9a84c' },
          { label: '历史平均', value: '2.3天', color: '#94a3b8' },
          { label: '明日概率', value: '延续退潮55%', color: '#ef4444' },
        ].map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 + i * 0.1, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
            className="text-center py-2 rounded-lg bg-[#0f1929]"
          >
            <div className="text-[11px] text-[#475569] mb-1">{item.label}</div>
            <div className="text-[13px] font-semibold font-mono" style={{ color: item.color }}>{item.value}</div>
          </motion.div>
        ))}
      </div>
    </DataCard>
  );
}

/* ─── Indicators Grid ─── */
function IndicatorsGrid() {
  const [selectedIndicator, setSelectedIndicator] = useState<Indicator | null>(null);
  const [expandedIndicators, setExpandedIndicators] = useState(false);

  return (
    <DataCard
      delay={250}
      header={
        <>
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">情绪指标</h2>
          <button
            onClick={() => setExpandedIndicators(!expandedIndicators)}
            className="flex items-center gap-1 text-[12px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors"
          >
            {expandedIndicators ? '收起' : '全部展开'}
            {expandedIndicators ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </>
      }
    >
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
        {INDICATORS.map((ind, i) => (
          <motion.div
            key={ind.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.04, duration: 0.3 }}
            className="group relative p-2 rounded-lg bg-[#0f1929] hover:bg-[#141e33] transition-colors cursor-pointer"
            onClick={() => setSelectedIndicator(ind)}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className={cn('w-2 h-2 rounded-full', statusColor(ind.status))} />
              <span className="text-[10px] text-[#475569] group-hover:text-[#f1f5f9] transition-colors truncate">{ind.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-semibold font-mono text-[#f1f5f9]">{ind.value}</span>
              <MiniSparkline data={ind.sparkline} color={statusDotColor(ind.status)} />
            </div>
            {expandedIndicators && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.3 }}
                className="mt-1.5 pt-1.5 border-t border-[rgba(148,163,184,0.1)]"
              >
                <p className="text-[10px] text-[#475569] leading-relaxed">{ind.desc}</p>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
      <IndicatorDetailModal
        open={!!selectedIndicator}
        onClose={() => setSelectedIndicator(null)}
        indicator={selectedIndicator}
      />
    </DataCard>
  );
}

/* ─── Theme Heat ─── */
function ThemeHeatCard() {
  return (
    <DataCard
      delay={500}
      header={
        <>
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">题材热度</h2>
          <button className="flex items-center gap-1 text-[12px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors">
            更多 <ArrowRight size={14} />
          </button>
        </>
      }
    >
      <div className="grid grid-cols-3 gap-2 p-1">
        {THEME_DATA.map((t, i) => (
          <motion.div
            key={t.name}
            className="rounded-lg p-2 flex flex-col items-center justify-center cursor-pointer border border-white/5"
            style={{ backgroundColor: `${t.phaseColor}25` }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            whileHover={{ scale: 1.05, borderColor: `${t.phaseColor}60` }}
          >
            <span className="text-[11px] font-medium text-slate-200 truncate w-full text-center" style={{ fontFamily: 'Noto Sans SC' }}>
              {t.name}
            </span>
            <span className="text-base font-bold mt-0.5" style={{ color: t.phaseColor, fontFamily: 'JetBrains Mono' }}>
              {t.heat}
            </span>
            <span className="text-[9px] px-1 rounded" style={{ backgroundColor: `${t.phaseColor}20`, color: t.phaseColor }}>
              {t.phase}
            </span>
            <span className="text-[9px] text-rose-400 mt-0.5">涨停{t.limitUp}家</span>
            <span className="text-[9px] text-slate-500 truncate w-full text-center">
              {t.leader}
            </span>
          </motion.div>
        ))}
      </div>
    </DataCard>
  );
}

/* ─── History Chart ─── */
function HistoryChartCard() {
  const [activeTimeRange, setActiveTimeRange] = useState<'7日' | '14日' | '30日'>('7日');
  const [showRefLines, setShowRefLines] = useState(true);
  const [selectedDay, setSelectedDay] = useState<DayHistoryData | null>(null);

  const historyOption = useMemo(() => {
    const daysMap: Record<string, number> = { '7日': 7, '14日': 14, '30日': 30 };
    const days = daysMap[activeTimeRange] || 7;
    const sliced = HISTORY_DATA.slice(-days);
    const xData = sliced.map(d => d.date);
    const yData = sliced.map(d => d.score);
    const offset = HISTORY_DATA.length - days;

    return {
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: Array<{ axisValue: string; value: number; dataIndex: number }>) => {
          const idx = params[0].dataIndex + offset;
          const item = HISTORY_DATA[idx];
          return `<div style="font-weight:bold;margin-bottom:4px">${item.date}</div>
            <div style="color:#c9a84c">综合情绪: ${item.score}分</div>
            <div style="color:${PHASES.find(p => p.name === item.phase)?.color};font-size:12px">阶段: ${item.phase}</div>`;
        },
      },
      grid: { top: 20, right: 15, bottom: 25, left: 40 },
      xAxis: {
        type: 'category' as const,
        data: xData,
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
        axisLabel: { color: '#475569', fontSize: 11, fontFamily: 'JetBrains Mono' },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value' as const,
        min: 0,
        max: 100,
        axisLine: { show: false },
        axisLabel: { color: '#475569', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.05)' } },
      },
      series: [
        {
          type: 'line',
          data: yData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#c9a84c' },
          itemStyle: { color: '#c9a84c', borderColor: '#0d1526', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(201,168,76,0.25)' },
              { offset: 1, color: 'rgba(201,168,76,0.02)' },
            ]),
          },
          animationDuration: 800,
          animationEasing: 'cubicOut' as const,
        },
        ...(showRefLines ? [
          {
            type: 'line' as const,
            markLine: {
              silent: true,
              symbol: 'none',
              data: [
                { yAxis: 80, name: '高潮线', lineStyle: { color: '#ef4444', type: 'dashed' as const, width: 1 }, label: { formatter: '高潮线', color: '#ef4444', fontSize: 10, position: 'insideEndTop' as const } },
                { yAxis: 40, name: '启动线', lineStyle: { color: '#3b82f6', type: 'dashed' as const, width: 1 }, label: { formatter: '启动线', color: '#3b82f6', fontSize: 10, position: 'insideEndTop' as const } },
              ],
            },
          },
        ] : []),
      ],
    };
  }, [showRefLines, activeTimeRange]);

  const handleChartClick = (params: any) => {
    if (params?.dataIndex !== undefined) {
      const daysMap: Record<string, number> = { '7日': 7, '14日': 14, '30日': 30 };
      const days = daysMap[activeTimeRange] || 7;
      const offset = HISTORY_DATA.length - days;
      const idx = params.dataIndex + offset;
      const dayData = HISTORY_DATA[idx];
      if (dayData) setSelectedDay(dayData);
    }
  };

  return (
    <DataCard
      delay={400}
      header={
        <>
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">情绪走势</h2>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              {(['7日', '14日', '30日'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setActiveTimeRange(t)}
                  className={cn(
                    'px-2 py-0.5 text-[11px] rounded transition-colors',
                    activeTimeRange === t ? 'bg-[#c9a84c] text-[#060b14] font-semibold' : 'text-[#475569] hover:text-[#94a3b8]'
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowRefLines(!showRefLines)}
              className={cn(
                'text-[11px] px-2 py-0.5 rounded transition-colors',
                showRefLines ? 'text-[#c9a84c]' : 'text-[#475569] hover:text-[#94a3b8]'
              )}
            >
              参考线
            </button>
          </div>
        </>
      }
    >
      <ReactECharts
        option={historyOption}
        style={{ height: 200 }}
        onEvents={{ click: handleChartClick }}
      />
      <DayDetailModal
        open={!!selectedDay}
        onClose={() => setSelectedDay(null)}
        dayData={selectedDay}
        period={activeTimeRange}
      />
    </DataCard>
  );
}

/* ─── Position Strategy ─── */
function PositionStrategyCard() {
  const currentStrategy = POSITION_STRATEGY[CURRENT_PHASE.name];

  return (
    <DataCard delay={700} header={<h2 className="text-[16px] font-semibold text-[#f1f5f9]">仓位策略</h2>}>
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex items-baseline gap-2 mb-1">
              <motion.span
                className="text-[28px] font-bold text-[#c9a84c] font-mono"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.0 }}
              >
                {currentStrategy.position}
              </motion.span>
              <span className="text-[12px] text-[#475569]">建议仓位</span>
            </div>
            <div className="text-[11px] text-[#94a3b8] mb-2">
              建议区间: {currentStrategy.range}
            </div>
            <div className="h-2.5 bg-[#0f1929] rounded-full overflow-hidden relative">
              <div className="absolute inset-0 rounded-full" style={{
                background: 'linear-gradient(to right, #ef4444 0%, #ef4444 30%, #eab308 30%, #eab308 60%, #22c55e 60%, #22c55e 85%, #c9a84c 85%)',
                opacity: 0.3,
              }} />
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: currentStrategy.position }}
                transition={{ delay: 0.8, duration: 1.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                className="h-full rounded-full relative"
                style={{ background: 'linear-gradient(to right, #c9a84c, #e0c878)' }}
              />
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-[rgba(148,163,184,0.1)]">
          <div className="text-[11px] text-[#475569] mb-2">策略要点</div>
          <div className="space-y-1.5">
            {currentStrategy.tactics.map((tactic, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.2 + i * 0.1 }}
                className="flex items-center gap-2"
              >
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  tactic.color === 'green' ? 'bg-[#22c55e]' : tactic.color === 'yellow' ? 'bg-[#eab308]' : 'bg-[#ef4444]'
                )} />
                <span className="text-[12px] text-[#94a3b8]">{tactic.text}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </DataCard>
  );
}

/* ─── Top5 Section ─── */
function Top5Section() {
  const navigate = useNavigate();

  return (
    <DataCard
      delay={400}
      header={
        <div className="flex items-center justify-between w-full">
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">综合评分 Top5</h2>
          <button
            onClick={() => navigate('/scoring')}
            className="text-[12px] text-[#c9a84c] hover:underline flex items-center gap-1 transition-colors"
          >
            查看全部 <ArrowRight size={14} />
          </button>
        </div>
      }
      className="min-h-[300px]"
    >
      <div className="flex flex-col gap-1">
        {topStocks.map((stock, i) => (
          <StockRow
            key={stock.code}
            stock={stock}
            delay={900 + i * 100}
            onClick={(code) => navigate(`/stock/${code}`)}
          />
        ))}
      </div>
    </DataCard>
  );
}

/* ─── Yingyou Section ─── */
function YingyouSection() {
  return (
    <DataCard
      delay={600}
      header={
        <div className="flex items-center justify-between w-full">
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">游资推荐</h2>
          <button className="p-1 rounded hover:bg-[#141e33] transition-colors group/refresh">
            <RefreshCw size={16} className="text-[#475569] group-hover/refresh:text-[#c9a84c] transition-all duration-300 group-hover/refresh:rotate-180" />
          </button>
        </div>
      }
    >
      <div className="flex flex-col gap-2">
        {yingyouRecommends.map((rec, i) => (
          <motion.div
            key={`${rec.name}-${rec.stockCode}`}
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{
              duration: 0.5,
              delay: (1100 + i * 150) / 1000,
              ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
            }}
            className={cn(
              'p-2.5 rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929]',
              'hover:border-[rgba(201,168,76,0.5)] hover:shadow-glow-gold hover:-translate-y-0.5',
              'transition-all duration-200 cursor-pointer'
            )}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[13px] font-medium text-[#c9a84c]">{rec.name}</span>
              <span className="text-[11px] font-mono text-[#94a3b8]">{rec.matchPercent}%</span>
            </div>
            <div className="h-1.5 bg-[#141e33] rounded-full overflow-hidden mb-1.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${rec.matchPercent}%` }}
                transition={{
                  duration: 1,
                  delay: (1300 + i * 200) / 1000,
                  ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
                }}
                className="h-full bg-gradient-to-r from-[#8a7530] to-[#c9a84c] rounded-full"
              />
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[12px] text-[#f1f5f9]">{rec.stockName}</span>
              <span className="text-[10px] font-mono text-[#475569]">{rec.stockCode}</span>
            </div>
            <div className="flex flex-wrap gap-1 mb-1">
              {rec.tactics.map((t) => (
                <span key={t} className="px-1.5 py-0.5 rounded-full text-[9px] border border-[#8b5cf6]/40 text-[#8b5cf6] bg-[#8b5cf6]/10">
                  {t}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-[#475569] leading-snug">{rec.reason}</p>
          </motion.div>
        ))}
      </div>
    </DataCard>
  );
}

/* ─── Tactics Section ─── */
function TacticsSection() {
  return (
    <DataCard
      delay={700}
      header={
        <div className="flex items-center justify-between w-full">
          <h2 className="text-[16px] font-semibold text-[#f1f5f9]">今日战法</h2>
          <div className="flex items-center gap-1.5 text-[#475569]">
            <Calendar size={14} />
            <span className="text-[11px] font-mono">
              {new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })}
            </span>
          </div>
        </div>
      }
    >
      <div className="flex flex-col gap-2">
        {todayTactics.map((tactic, i) => (
          <motion.div
            key={tactic.name}
            initial={{ y: 15, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{
              duration: 0.4,
              delay: (1200 + i * 100) / 1000,
              ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
            }}
            className="p-2 rounded-lg hover:bg-[#141e33] transition-colors duration-200 cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[13px] font-medium text-[#8b5cf6] group-hover:text-[#a78bfa] transition-colors">
                {tactic.name}
              </span>
              <span className="text-[11px] font-mono text-[#94a3b8]">触发: {tactic.triggerCount}次</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#475569]">近5日成功率: {tactic.successRate}%</span>
              <div className="flex items-end gap-[3px] h-4">
                {tactic.trend.map((t, j) => (
                  <motion.div
                    key={j}
                    initial={{ height: 0 }}
                    animate={{ height: t === 'up' ? 14 : 6 }}
                    transition={{
                      duration: 0.6,
                      delay: (1400 + i * 50 + j * 50) / 1000,
                      ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
                    }}
                    className={cn(
                      'w-[5px] rounded-sm',
                      t === 'up' ? 'bg-[#ef4444]' : 'bg-[#22c55e]'
                    )}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </DataCard>
  );
}

/* ─── Module Cards ─── */
function ModuleCards() {
  const navigate = useNavigate();

  return (
    <div className="col-span-12">
      <div className="grid grid-cols-7 gap-3">
        {moduleCards.map((mod, i) => {
          const Icon = moduleIconMap[mod.icon] || Activity;
          return (
            <motion.button
              key={mod.name}
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{
                duration: 0.5,
                delay: (1400 + i * 80) / 1000,
                ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
              }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate(mod.path)}
              className={cn(
                'flex flex-col items-center justify-center gap-2 py-4 px-3',
                'bg-[#0d1526] rounded-[10px] border border-[rgba(148,163,184,0.1)]',
                'hover:border-[rgba(201,168,76,0.5)] hover:shadow-glow-gold',
                'transition-all duration-200 group'
              )}
            >
              <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-[#141e33] group-hover:bg-[#c9a84c]/10 transition-colors duration-200">
                <Icon
                  size={20}
                  className="text-[#c9a84c] group-hover:scale-110 transition-transform duration-200"
                />
              </div>
              <span className="text-[12px] text-[#f1f5f9] font-medium">{mod.name}</span>
              <span className="text-[9px] text-[#475569] text-center leading-tight line-clamp-1">{mod.description}</span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Main Home Page ─── */
export default function Home() {
  const [apiData, setApiData] = useState<{
    indices: any[];
    stats: any;
    limitUpStocks: any[];
    date: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  // 从API获取实时数据
  const fetchRealtimeData = useCallback(async () => {
    try {
      setLoading(true);
      const [marketRes, limitUpRes] = await Promise.all([
        swatAPI.market.overview(false),
        swatAPI.market.limitUp({ limit: 10 }),
      ]);
      
      console.log('=== API Response Debug ===');
      console.log('Market Response:', JSON.stringify(marketRes, null, 2));
      console.log('Market Response data:', marketRes.data);
      console.log('Market Response indices:', marketRes.data?.indices);
      console.log('LimitUp Response:', JSON.stringify(limitUpRes, null, 2));
      console.log('LimitUp Response data:', limitUpRes.data);
      
      // API返回格式: {code: 200, data: {date, indices, stats, source}, source: "cache", timestamp: "..."}
      // marketRes 是 {code: 200, data: {date, indices, stats, source}, source: "cache", timestamp: "..."}
      // marketRes.data 是 {date, indices, stats, source}
      const marketData = marketRes.data;
      const limitUpData = limitUpRes.data;
      
      console.log('Processed marketData:', marketData);
      console.log('Processed limitUpData:', limitUpData);
      
      setApiData({
        indices: marketData?.indices || [],
        stats: marketData?.stats || {},
        limitUpStocks: limitUpData?.stocks || [],
        date: marketData?.date || '',
      });
    } catch (error) {
      console.error('Failed to fetch realtime data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRealtimeData();
    // 每30秒刷新一次数据
    const interval = setInterval(fetchRealtimeData, 30000);
    return () => clearInterval(interval);
  }, [fetchRealtimeData]);

  return (
    <div className="space-y-4">
      {/* Row 1: Market Overview */}
      <div className="grid grid-cols-12 gap-4">
        <MarketOverview apiData={apiData} />
      </div>

      {/* Row 2: Sentiment Cycle + Indicators */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4">
          <SentimentCycleCard />
        </div>
        <div className="col-span-12 lg:col-span-8">
          <IndicatorsGrid />
        </div>
      </div>

      {/* Row 3: History Chart + Theme Heat + Position Strategy */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5">
          <HistoryChartCard />
        </div>
        <div className="col-span-12 lg:col-span-4">
          <ThemeHeatCard />
        </div>
        <div className="col-span-12 lg:col-span-3">
          <PositionStrategyCard />
        </div>
      </div>

      {/* Row 4: Top5 + Yingyou + Tactics */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5">
          <Top5Section />
        </div>
        <div className="col-span-12 lg:col-span-4">
          <YingyouSection />
        </div>
        <div className="col-span-12 lg:col-span-3">
          <TacticsSection />
        </div>
      </div>

      {/* Row 5: Module Cards */}
      <ModuleCards />

      {/* Alert Ticker */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.7 }}
      >
        <AlertTicker messages={alertMessages} />
      </motion.div>

      {/* Data Status Bar */}
      <DataStatusBar status={dataStatus} />
    </div>
  );
}