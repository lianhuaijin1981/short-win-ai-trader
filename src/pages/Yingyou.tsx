import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactEChartsCore from 'echarts-for-react';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  AlertTriangle,
  ChevronRight,
  Zap,
  Users,
  Star,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────
interface YingyouTrader {
  id: string;
  name: string;
  alias: string;
  matchPercent: number;
  status: 'active' | 'warning' | 'inactive';
  style: string;
  market: string;
  avgHoldDays: string;
  winRate: number;
  monthlyReturn: number;
  maxDrawdown: number;
  marketCap: string;
  activeYears: string;
  philosophy: string;
  radarData: number[];
  operations: Operation[];
  recommendations: Recommendation[];
}

interface Operation {
  date: string;
  code: string;
  name: string;
  action: 'buy' | 'sell';
  price: number;
  pnl?: number;
}

interface Recommendation {
  code: string;
  name: string;
  matchPercent: number;
  tactics: string[];
  reasons: string[];
  action: 'intervene' | 'observe';
  currentPrice: number;
  changePercent: number;
}

// ── Mock Data ─────────────────────────────────────────────────
const traders: YingyouTrader[] = [
  {
    id: 'chaogu',
    name: '炒股养家',
    alias: '养家心法创始人',
    matchPercent: 92,
    status: 'active',
    style: '首板套利、一致性预期',
    market: '震荡市、弱市',
    avgHoldDays: '1-3天',
    winRate: 68.5,
    monthlyReturn: 12.3,
    maxDrawdown: -8.1,
    marketCap: '50-200亿',
    activeYears: '2010-至今',
    philosophy: '买入分歧，卖出一致。只做主流题材龙头股。',
    radarData: [85, 70, 60, 90, 95, 88, 82, 78],
    operations: [
      { date: '今日', code: '002XXX', name: '某某科技', action: 'buy', price: 18.56 },
      { date: '今日', code: '600XXX', name: '某某股份', action: 'sell', price: 25.30, pnl: 8.5 },
      { date: '昨日', code: '300XXX', name: '某某智能', action: 'buy', price: 42.18 },
      { date: '昨日', code: '000XXX', name: '某某新材', action: 'sell', price: 8.92, pnl: -2.1 },
      { date: '前日', code: '688XXX', name: '某某微', action: 'buy', price: 65.40 },
      { date: '前日', code: '002YYY', name: '某某软件', action: 'sell', price: 12.35, pnl: 12.3 },
    ],
    recommendations: [
      { code: '002837', name: '英维克', matchPercent: 94, tactics: ['筹码峰+', '首阴'], reasons: ['养家一致性评分92分', '筹码峰结构完整', '今日出现首阴信号'], action: 'intervene', currentPrice: 32.50, changePercent: 7.2 },
      { code: '600520', name: '文一科技', matchPercent: 89, tactics: ['N字形', '龙回头'], reasons: ['梯队完整性验证', '题材发酵期匹配'], action: 'intervene', currentPrice: 28.60, changePercent: 5.8 },
      { code: '300308', name: '中际旭创', matchPercent: 86, tactics: ['三倍量突破'], reasons: ['量价共振+板块龙头', '封单强度达标'], action: 'observe', currentPrice: 145.20, changePercent: 3.5 },
    ],
  },
  {
    id: 'tuixue',
    name: '退学炒股',
    alias: '超短实战派',
    matchPercent: 88,
    status: 'active',
    style: '龙头接力、情绪博弈',
    market: '强市、高潮期',
    avgHoldDays: '1-2天',
    winRate: 65.2,
    monthlyReturn: 15.8,
    maxDrawdown: -12.3,
    marketCap: '30-150亿',
    activeYears: '2015-至今',
    philosophy: '别人贪婪时我更贪婪，别人恐惧时我更恐惧。',
    radarData: [95, 55, 45, 88, 92, 90, 60, 72],
    operations: [
      { date: '今日', code: '603XXX', name: '某某电子', action: 'buy', price: 22.80 },
      { date: '昨日', code: '002ZZZ', name: '某某股份', action: 'sell', price: 15.60, pnl: 15.2 },
      { date: '昨日', code: '300YYY', name: '某某智能', action: 'buy', price: 38.90 },
      { date: '前日', code: '600AAA', name: '某某科技', action: 'sell', price: 42.30, pnl: -4.5 },
    ],
    recommendations: [
      { code: '603019', name: '中科曙光', matchPercent: 91, tactics: ['龙头接力', '情绪共振'], reasons: ['龙头地位确认', '板块情绪高涨', '封单强度92分'], action: 'intervene', currentPrice: 56.80, changePercent: 10.0 },
      { code: '002230', name: '科大讯飞', matchPercent: 84, tactics: ['分歧低吸'], reasons: ['龙头分歧转一致', '量能配合良好'], action: 'observe', currentPrice: 48.60, changePercent: 2.3 },
    ],
  },
  {
    id: 'niepan',
    name: '涅槃重生',
    alias: '情绪周期大师',
    matchPercent: 85,
    status: 'active',
    style: '冰点试错、周期切换',
    market: '情绪冰点期',
    avgHoldDays: '2-5天',
    winRate: 62.8,
    monthlyReturn: 10.5,
    maxDrawdown: -9.5,
    marketCap: '20-100亿',
    activeYears: '2012-至今',
    philosophy: '买在分歧转一致，卖在一致转分歧。',
    radarData: [70, 85, 75, 82, 78, 72, 88, 80],
    operations: [
      { date: '今日', code: '300BBB', name: '某某新材', action: 'buy', price: 12.35 },
      { date: '昨日', code: '000CCC', name: '某某能源', action: 'sell', price: 8.92, pnl: 5.6 },
      { date: '前日', code: '688DDD', name: '某某半导体', action: 'buy', price: 75.60 },
    ],
    recommendations: [
      { code: '000063', name: '中兴通讯', matchPercent: 88, tactics: ['冰点试错', '周期转折'], reasons: ['情绪冰点已现', '龙头潜质显现', '板块即将轮动'], action: 'intervene', currentPrice: 35.20, changePercent: 4.1 },
      { code: '002371', name: '北方华创', matchPercent: 82, tactics: ['低吸埋伏'], reasons: ['情绪周期底部', '半导体周期复苏'], action: 'observe', currentPrice: 285.60, changePercent: 1.8 },
    ],
  },
  {
    id: 'kebi',
    name: '92科比',
    alias: '新生代游资',
    matchPercent: 87,
    status: 'active',
    style: '龙头接力、分歧转一致',
    market: '强势市场',
    avgHoldDays: '1-2天',
    winRate: 66.7,
    monthlyReturn: 18.2,
    maxDrawdown: -14.5,
    marketCap: '50-300亿',
    activeYears: '2018-至今',
    philosophy: '只做龙头，不做杂毛。强者恒强，弱者恒弱。',
    radarData: [92, 50, 40, 95, 98, 85, 65, 75],
    operations: [
      { date: '今日', code: '600EEE', name: '某某算力', action: 'buy', price: 35.60 },
      { date: '昨日', code: '002FFF', name: '某某数据', action: 'sell', price: 28.40, pnl: 22.1 },
      { date: '前日', code: '300GGG', name: '某某云', action: 'buy', price: 42.30 },
      { date: '前日', code: '000HHH', name: '某某信息', action: 'sell', price: 18.90, pnl: 6.8 },
    ],
    recommendations: [
      { code: '603019', name: '中科曙光', matchPercent: 93, tactics: ['龙头接力', '分歧转一致'], reasons: ['算力龙头地位', '板块强度第一', '封单强度95分'], action: 'intervene', currentPrice: 56.80, changePercent: 10.0 },
      { code: '002236', name: '大华股份', matchPercent: 85, tactics: ['龙回头'], reasons: ['前期龙头回踩', '均线支撑有效'], action: 'observe', currentPrice: 22.40, changePercent: 3.2 },
    ],
  },
  {
    id: 'xiaoe',
    name: '小鳄鱼',
    alias: '首板猎手',
    matchPercent: 83,
    status: 'warning',
    style: '首板挖掘、提前埋伏',
    market: '震荡市',
    avgHoldDays: '1-3天',
    winRate: 70.2,
    monthlyReturn: 9.8,
    maxDrawdown: -7.2,
    marketCap: '30-200亿',
    activeYears: '2016-至今',
    philosophy: '首板是最安全的打板方式，盈亏比最优。',
    radarData: [78, 90, 70, 85, 72, 68, 85, 82],
    operations: [
      { date: '今日', code: '002III', name: '某某软件', action: 'buy', price: 15.80 },
      { date: '昨日', code: '300JJJ', name: '某某医疗', action: 'sell', price: 32.60, pnl: 3.2 },
    ],
    recommendations: [
      { code: '300033', name: '同花顺', matchPercent: 90, tactics: ['首板挖掘', '量能异动'], reasons: ['金融软件异动', '首板封单完整', '板块轮动预期'], action: 'intervene', currentPrice: 188.50, changePercent: 9.2 },
      { code: '002195', name: '岩山科技', matchPercent: 86, tactics: ['提前埋伏'], reasons: ['均线粘合待突破', '成交量持续放大'], action: 'observe', currentPrice: 5.60, changePercent: 2.1 },
    ],
  },
  {
    id: 'longfei',
    name: '龙飞虎',
    alias: '趋势波段王',
    matchPercent: 79,
    status: 'warning',
    style: '趋势波段、主升浪',
    market: '趋势市',
    avgHoldDays: '3-7天',
    winRate: 61.5,
    monthlyReturn: 8.6,
    maxDrawdown: -11.2,
    marketCap: '100-500亿',
    activeYears: '2010-至今',
    philosophy: '顺势而为，不与趋势为敌。抓住主升浪。',
    radarData: [60, 88, 90, 75, 70, 65, 78, 85],
    operations: [
      { date: '今日', code: '600KKK', name: '某某船舶', action: 'sell', price: 25.30, pnl: 18.5 },
      { date: '昨日', code: '000LLL', name: '某某中车', action: 'buy', price: 7.80 },
      { date: '前日', code: '300MMM', name: '某某航空', action: 'sell', price: 42.60, pnl: -3.2 },
    ],
    recommendations: [
      { code: '601766', name: '中国中车', matchPercent: 87, tactics: ['趋势波段', '主升浪'], reasons: ['趋势刚刚启动', '量能配合完美', '均线多头排列'], action: 'intervene', currentPrice: 7.80, changePercent: 5.6 },
      { code: '600893', name: '航发动力', matchPercent: 81, tactics: ['波段低吸'], reasons: ['军工趋势明确', '回调到位信号'], action: 'observe', currentPrice: 42.60, changePercent: 1.5 },
    ],
  },
  {
    id: 'zhiye',
    name: '职业炒手',
    alias: '模式交易专家',
    matchPercent: 76,
    status: 'warning',
    style: '模式内交易、严格执行',
    market: '所有市场',
    avgHoldDays: '1-3天',
    winRate: 63.8,
    monthlyReturn: 7.5,
    maxDrawdown: -6.8,
    marketCap: '50-300亿',
    activeYears: '2011-至今',
    philosophy: '模式内的交易，无论盈亏都是对的。模式外的交易，无论盈亏都是错的。',
    radarData: [75, 72, 65, 80, 76, 70, 92, 90],
    operations: [
      { date: '今日', code: '002NNN', name: '某某传媒', action: 'buy', price: 6.50 },
      { date: '昨日', code: '600OOO', name: '某某影视', action: 'sell', price: 12.80, pnl: -1.5 },
    ],
    recommendations: [
      { code: '002602', name: '世纪华通', matchPercent: 84, tactics: ['模式内交易', '严格执行'], reasons: ['符合模式定义', '止损位清晰', '盈亏比合理'], action: 'intervene', currentPrice: 6.50, changePercent: 3.8 },
      { code: '002555', name: '三七互娱', matchPercent: 80, tactics: ['模式匹配'], reasons: ['游戏板块模式触发', '执行条件完备'], action: 'observe', currentPrice: 18.20, changePercent: 1.2 },
    ],
  },
  {
    id: 'asking',
    name: 'Asking',
    alias: '超短鼻祖',
    matchPercent: 72,
    status: 'inactive',
    style: '题材挖掘、情绪引领',
    market: '题材驱动市',
    avgHoldDays: '1-2天',
    winRate: 60.5,
    monthlyReturn: 6.8,
    maxDrawdown: -15.2,
    marketCap: '20-150亿',
    activeYears: '2007-至今',
    philosophy: '炒股就是炒预期，预期来自题材，题材来自生活。',
    radarData: [82, 65, 55, 92, 80, 78, 58, 65],
    operations: [
      { date: '今日', code: '300PPP', name: '某某教育', action: 'buy', price: 8.90 },
      { date: '昨日', code: '000QQQ', name: '某某文化', action: 'sell', price: 15.40, pnl: -5.2 },
    ],
    recommendations: [
      { code: '300364', name: '中文在线', matchPercent: 83, tactics: ['题材挖掘', '情绪引领'], reasons: ['AI教育题材升温', '情绪节点契合', '前期龙头记忆'], action: 'intervene', currentPrice: 28.90, changePercent: 6.5 },
      { code: '002858', name: '科沃斯', matchPercent: 76, tactics: ['题材埋伏'], reasons: ['机器人题材轮动', '短期催化剂临近'], action: 'observe', currentPrice: 52.30, changePercent: 0.8 },
    ],
  },
];

// Radar dimensions
const radarDimensions = [
  '打板偏好',
  '低吸能力',
  '持股周期',
  '题材敏感度',
  '龙头偏好',
  '封单强度',
  '回撤控制',
  '一致性',
];

const marketAverage = [60, 55, 50, 65, 58, 52, 45, 48];

// ── Status helpers ────────────────────────────────────────────
function getStatusColor(status: string) {
  switch (status) {
    case 'active': return 'bg-[#22c55e]';
    case 'warning': return 'bg-[#f59e0b]';
    case 'inactive': return 'bg-[#ef4444]';
    default: return 'bg-[#6b7280]';
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'active': return '活跃';
    case 'warning': return '谨慎';
    case 'inactive': return '观望';
    default: return '未知';
  }
}

// ── Components ────────────────────────────────────────────────

function ScoreRing({ percent, size = 48 }: { percent: number; size?: number }) {
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#141e33" strokeWidth={strokeWidth} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke="#c9a84c"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute text-[10px] font-mono font-semibold text-[#c9a84c]">{percent}</span>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function Yingyou() {
  const [selectedId, setSelectedId] = useState(traders[0].id);
  const [showCompare, setShowCompare] = useState(false);

  const selected = useMemo(() => traders.find((t) => t.id === selectedId)!, [selectedId]);

  // Radar chart option
  const radarOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' as const },
      radar: {
        indicator: radarDimensions.map((name) => ({ name, max: 100 })),
        center: ['50%', '50%'],
        radius: '65%',
        axisName: {
          color: '#94a3b8',
          fontSize: 11,
        },
        splitArea: { areaStyle: { color: ['transparent'] } },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: selected.radarData,
              name: selected.name,
              areaStyle: { color: 'rgba(201,168,76,0.2)' },
              lineStyle: { color: '#c9a84c', width: 2 },
              itemStyle: { color: '#c9a84c' },
            },
            ...(showCompare
              ? [
                  {
                    value: marketAverage,
                    name: '市场平均',
                    areaStyle: { color: 'rgba(59,130,246,0.1)' },
                    lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' as const },
                    itemStyle: { color: '#3b82f6' },
                  },
                ]
              : []),
          ],
          animationDuration: 1200,
          animationEasing: 'cubicOut',
        },
      ],
    }),
    [selected, showCompare]
  );

  // Multi-trader consensus analysis
  const consensusStocks = useMemo(() => {
    const stockMap: Record<string, { code: string; name: string; traders: string[]; avgMatch: number }> = {};
    traders.forEach((t) => {
      t.recommendations.forEach((r) => {
        if (!stockMap[r.code]) {
          stockMap[r.code] = { code: r.code, name: r.name, traders: [], avgMatch: 0 };
        }
        stockMap[r.code].traders.push(t.name);
        stockMap[r.code].avgMatch += r.matchPercent;
      });
    });
    return Object.values(stockMap)
      .filter((s) => s.traders.length >= 3)
      .map((s) => ({ ...s, avgMatch: Math.round(s.avgMatch / s.traders.length) }));
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-bold text-[#f1f5f9] leading-tight">游资诊断</h1>
          <p className="text-[#94a3b8] text-[14px] mt-1">8大游资数字指纹匹配与推荐系统</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0d1526] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <Users size={16} className="text-[#c9a84c]" />
          <span className="text-[12px] text-[#94a3b8]">8位游资活跃监测中</span>
        </div>
      </div>

      {/* ── Section 1: Trader Selection Bar ───────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
        className="rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-4"
      >
        <div className="flex gap-3">
          {traders.map((trader, i) => (
            <motion.button
              key={trader.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              onClick={() => setSelectedId(trader.id)}
              className={cn(
                'flex-1 relative rounded-lg border p-3 text-center transition-all duration-200',
                selectedId === trader.id
                  ? 'bg-[#141e33] border-[#c9a84c] shadow-[0_0_20px_rgba(201,168,76,0.15)]'
                  : 'bg-transparent border-[rgba(148,163,184,0.1)] hover:bg-[#141e33] hover:border-[rgba(201,168,76,0.3)]'
              )}
            >
              {/* Active indicator */}
              {selectedId === trader.id && (
                <motion.div
                  layoutId="trader-active"
                  className="absolute bottom-0 left-0 right-0 h-[3px] bg-[#c9a84c] rounded-t-full"
                />
              )}
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <span className={cn('w-2 h-2 rounded-full', getStatusColor(trader.status))} />
                <span className="text-[14px] font-medium text-[#f1f5f9]">{trader.name}</span>
              </div>
              <div className="text-[11px] font-mono text-[#94a3b8] mb-1.5">
                匹配度: <span className="text-[#c9a84c]">{trader.matchPercent}%</span>
              </div>
              {/* Match bar */}
              <div className="w-full h-1 bg-[#141e33] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${trader.matchPercent}%` }}
                  transition={{ duration: 0.8, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                  className="h-full bg-gradient-to-r from-[#8a7530] to-[#c9a84c] rounded-full"
                />
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ── Section 2: Profile + Radar ────────────────────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Trader Profile */}
        <div className="col-span-4">
          <DataCard delay={200}>
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                {/* Header */}
                <div className="mb-4">
                  <h2 className="text-[24px] font-semibold text-[#c9a84c]">{selected.name}</h2>
                  <p className="text-[12px] text-[#94a3b8] mt-0.5">{selected.alias}</p>
                </div>

                {/* Profile grid */}
                <div className="space-y-2 mb-4">
                  {[
                    { label: '操作风格', value: selected.style },
                    { label: '擅长市场', value: selected.market },
                    { label: '平均持股', value: selected.avgHoldDays, mono: true },
                    { label: '偏好市值', value: selected.marketCap },
                    { label: '活跃时间', value: selected.activeYears },
                  ].map((item, i) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06, duration: 0.3 }}
                      className="flex justify-between items-center py-1.5 border-b border-[rgba(148,163,184,0.06)]"
                    >
                      <span className="text-[12px] text-[#94a3b8]">{item.label}</span>
                      <span className={cn('text-[13px] text-[#f1f5f9]', item.mono && 'font-mono')}>
                        {item.value}
                      </span>
                    </motion.div>
                  ))}
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#ef4444]">{selected.winRate}%</div>
                      <div className="text-[10px] text-[#94a3b8]">胜率</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#ef4444]">+{selected.monthlyReturn}%</div>
                      <div className="text-[10px] text-[#94a3b8]">月收益</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#22c55e]">{selected.maxDrawdown}%</div>
                      <div className="text-[10px] text-[#94a3b8]">最大回撤</div>
                    </div>
                  </div>
                </div>

                {/* Philosophy */}
                <div className="relative bg-[#141e33] rounded-lg p-3 pl-4">
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-lg" />
                  <p className="text-[13px] text-[#f1f5f9] italic leading-relaxed">"{selected.philosophy}"</p>
                </div>

                {/* Activity sparklines */}
                <div className="mt-4">
                  <p className="text-[11px] text-[#94a3b8] mb-2">7日活跃度</p>
                  <div className="flex items-end gap-1 h-10">
                    {[0.6, 0.8, 0.4, 1.0, 0.7, 0.3, 0.9].map((h, i) => (
                      <motion.div
                        key={i}
                        initial={{ height: 0 }}
                        animate={{ height: `${h * 100}%` }}
                        transition={{ delay: i * 0.05, duration: 0.5, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                        className={cn(
                          'flex-1 rounded-t-sm',
                          h > 0.5 ? 'bg-[#c9a84c]' : 'bg-[#334155]'
                        )}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>

        {/* Radar Chart */}
        <div className="col-span-8">
          <DataCard
            delay={300}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">交易模式数字指纹</h2>
                <button
                  onClick={() => setShowCompare(!showCompare)}
                  className={cn(
                    'text-[12px] px-3 py-1 rounded-full border transition-all duration-200',
                    showCompare
                      ? 'border-[#3b82f6] text-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                      : 'border-[rgba(148,163,184,0.2)] text-[#94a3b8] hover:border-[#c9a84c]'
                  )}
                >
                  {showCompare ? '隐藏市场平均' : '对比市场平均'}
                </button>
              </>
            }
          >
            <div className="relative">
              <ReactEChartsCore option={radarOption} style={{ height: 380 }} notMerge={true} />
              {/* Center score */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <div className="text-[28px] font-mono font-bold text-[#c9a84c]">{selected.matchPercent}</div>
                <div className="text-[11px] text-[#94a3b8]">匹配度</div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Section 3: Operations + Recommendations ───────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Recent Operations */}
        <div className="col-span-6">
          <DataCard
            delay={400}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">近期操作追踪</h2>
                <span className="text-[11px] text-[#94a3b8] px-2 py-1 bg-[#141e33] rounded-md">近7日</span>
              </>
            }
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id + '-ops'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-1"
              >
                {/* Table header */}
                <div className="grid grid-cols-[60px_1fr_50px_70px_60px] gap-2 px-3 py-2 text-[11px] text-[#94a3b8] border-b border-[rgba(148,163,184,0.1)]">
                  <span>日期</span>
                  <span>股票</span>
                  <span>操作</span>
                  <span className="text-right">价格</span>
                  <span className="text-right">盈亏</span>
                </div>
                {/* Rows */}
                {selected.operations.map((op, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.07, duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                    className={cn(
                      'grid grid-cols-[60px_1fr_50px_70px_60px] gap-2 px-3 py-2.5 rounded-lg items-center transition-colors duration-200 hover:bg-[#141e33] cursor-pointer',
                      i % 2 === 0 ? 'bg-[rgba(15,25,41,0.5)]' : 'bg-transparent'
                    )}
                  >
                    {/* Left indicator */}
                    <div className={cn(
                      'absolute left-0 w-[3px] h-full rounded-r',
                      op.action === 'buy' ? 'bg-[#ef4444]' : op.pnl && op.pnl > 0 ? 'bg-[#c9a84c]' : op.pnl && op.pnl < 0 ? 'bg-[#22c55e]' : 'bg-[#c9a84c]'
                    )} style={{ position: 'relative' }}>
                      <div className={cn(
                        'absolute left-[-12px] top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r',
                        op.action === 'buy' ? 'bg-[#ef4444]' : op.pnl && op.pnl > 0 ? 'bg-[#c9a84c]' : op.pnl && op.pnl < 0 ? 'bg-[#22c55e]' : 'bg-[#c9a84c]'
                      )} />
                    </div>
                    <span className="text-[12px] text-[#94a3b8]">{op.date}</span>
                    <div>
                      <span className="text-[13px] text-[#f1f5f9] font-medium">{op.name}</span>
                      <span className="text-[11px] text-[#475569] font-mono ml-1">{op.code}</span>
                    </div>
                    <span className={cn(
                      'text-[12px] font-medium',
                      op.action === 'buy' ? 'text-[#ef4444]' : 'text-[#22c55e]'
                    )}>
                      {op.action === 'buy' ? '买入' : '卖出'}
                    </span>
                    <span className="text-[13px] font-mono text-[#f1f5f9] text-right">{op.price.toFixed(2)}</span>
                    <span className="text-[12px] font-mono text-right">
                      {op.pnl !== undefined ? (
                        <span className={op.pnl > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]'}>
                          {op.pnl > 0 ? '+' : ''}{op.pnl}%
                        </span>
                      ) : (
                        <span className="text-[#475569]">--</span>
                      )}
                    </span>
                  </motion.div>
                ))}
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>

        {/* Recommendations */}
        <div className="col-span-6">
          <DataCard
            delay={500}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">当前推荐</h2>
                <span className="text-[11px] text-[#94a3b8] flex items-center gap-1">
                  匹配度排序 <ChevronRight size={12} className="rotate-90" />
                </span>
              </>
            }
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id + '-recs'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-3"
              >
                {selected.recommendations.map((rec, i) => (
                  <motion.div
                    key={rec.code}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.12, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                    className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4 transition-all duration-200 hover:-translate-y-[3px] hover:border-[rgba(201,168,76,0.5)] hover:shadow-[0_0_20px_rgba(201,168,76,0.15)] cursor-pointer"
                  >
                    {/* Top row */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <ScoreRing percent={rec.matchPercent} size={44} />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{rec.code}</span>
                            <span className="text-[15px] font-medium text-[#f1f5f9]">{rec.name}</span>
                          </div>
                          <div className="flex gap-1.5 mt-1">
                            {rec.tactics.map((t) => (
                              <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border border-[#8b5cf6] text-[#8b5cf6] bg-[rgba(139,92,246,0.1)]">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{rec.currentPrice.toFixed(2)}</div>
                        <span className={cn(
                          'inline-flex items-center text-[11px] font-mono px-2 py-0.5 rounded-full',
                          rec.changePercent > 0
                            ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]'
                            : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]'
                        )}>
                          {rec.changePercent > 0 ? '+' : ''}{rec.changePercent}%
                        </span>
                      </div>
                    </div>
                    {/* Reasons */}
                    <div className="space-y-1 mb-2.5">
                      {rec.reasons.map((r, j) => (
                        <div key={j} className="flex items-center gap-1.5">
                          <ChevronRight size={10} className="text-[#8a7530]" />
                          <span className="text-[11px] text-[#94a3b8]">{r}</span>
                        </div>
                      ))}
                    </div>
                    {/* Action */}
                    <div className="flex gap-2">
                      <span className={cn(
                        'text-[11px] px-3 py-1 rounded-full font-medium',
                        rec.action === 'intervene' ? 'bg-[#c9a84c] text-[#060b14]' : 'bg-[rgba(249,115,22,0.2)] text-[#f97316]'
                      )}>
                        {rec.action === 'intervene' ? '关注' : '观察'}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>
      </div>

      {/* ── Section 4: Multi-Trader Consensus ─────────────── */}
      <DataCard
        delay={600}
        header={
          <>
            <div className="flex items-center gap-2">
              <Users size={18} className="text-[#c9a84c]" />
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">多游资共识分析</h2>
            </div>
            <span className="text-[11px] text-[#94a3b8] px-2 py-1 bg-[#141e33] rounded-md">{consensusStocks.length} 只共识标的</span>
          </>
        }
      >
        {consensusStocks.length > 0 ? (
          <div className="grid grid-cols-3 gap-4">
            {consensusStocks.map((stock, i) => (
              <motion.div
                key={stock.code}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                className="rounded-lg border border-[rgba(201,168,76,0.2)] bg-[rgba(201,168,76,0.03)] p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{stock.code}</span>
                    <span className="text-[14px] text-[#f1f5f9] ml-2">{stock.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star size={14} className="text-[#c9a84c]" />
                    <span className="text-[16px] font-mono font-semibold text-[#c9a84c]">{stock.avgMatch}%</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {stock.traders.map((t) => (
                    <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.1)]">
                      {t}
                    </span>
                  ))}
                </div>
                <div className="text-[11px] text-[#94a3b8]">
                  {stock.traders.length} 位游资共同看好，平均匹配度 {stock.avgMatch}%
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-[#475569] text-[13px]">
            暂无3位以上游资共识标的
          </div>
        )}

        {/* Divergence warning */}
        <div className="mt-4 rounded-lg border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.03)] p-3 flex items-center gap-3">
          <AlertTriangle size={16} className="text-[#ef4444] shrink-0" />
          <div>
            <p className="text-[13px] font-medium text-[#f1f5f9]">分歧预警</p>
            <p className="text-[11px] text-[#94a3b8]">部分游资对当前市场方向存在分歧，建议谨慎操作，控制仓位在50%以内</p>
          </div>
        </div>
      </DataCard>

      {/* ── Section 5: Strategy Recommendations ───────────── */}
      <DataCard
        delay={700}
        header={
          <div className="flex items-center gap-2">
            <Target size={18} className="text-[#c9a84c]" />
            <h2 className="text-[18px] font-semibold text-[#f1f5f9]">组合策略推荐</h2>
          </div>
        }
      >
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              level: '新手',
              icon: <Award size={20} className="text-[#22c55e]" />,
              color: '#22c55e',
              desc: '跟随单一游资，稳健起步',
              strategy: '选择匹配度最高的1位游资（炒股养家），严格跟随其推荐标的，单票仓位不超过20%',
              rules: ['只做推荐榜前2名', '止损-3%严格执行', '每日最多1笔交易', '收盘前必须清仓'],
              expectWinRate: '60%+',
              expectReturn: '5-8%/月',
            },
            {
              level: '进阶',
              icon: <Zap size={20} className="text-[#c9a84c]" />,
              color: '#c9a84c',
              desc: '多游资共振，提升胜率',
              strategy: '同时跟踪3-4位游资，选择至少2位共同推荐的标的，仓位可提升至30%',
              rules: ['关注共识标的', '允许持有隔夜', '止损-5%线', '可分批建仓'],
              expectWinRate: '65%+',
              expectReturn: '10-15%/月',
            },
            {
              level: '高手',
              icon: <TrendingUp size={20} className="text-[#ef4444]" />,
              color: '#ef4444',
              desc: '灵活运用，追逐高收益',
              strategy: '全量游资跟踪，结合情绪周期自主判断，敢于重仓龙头，灵活止损止盈',
              rules: ['全市场机会把握', '龙头可重仓50%', '浮动止损跟踪', '可融资加仓'],
              expectWinRate: '70%+',
              expectReturn: '20%+/月',
            },
          ].map((s, i) => (
            <motion.div
              key={s.level}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.1, duration: 0.4 }}
              className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4 hover:border-[rgba(201,168,76,0.3)] transition-all duration-200"
            >
              <div className="flex items-center gap-2 mb-3">
                {s.icon}
                <h3 className="text-[16px] font-semibold" style={{ color: s.color }}>{s.level}</h3>
              </div>
              <p className="text-[12px] text-[#94a3b8] mb-3">{s.desc}</p>
              <p className="text-[13px] text-[#f1f5f9] mb-3 leading-relaxed">{s.strategy}</p>
              <div className="space-y-1.5 mb-3">
                {s.rules.map((r, j) => (
                  <div key={j} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="text-[11px] text-[#94a3b8]">{r}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-3 pt-2 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#f1f5f9]">{s.expectWinRate}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期胜率</div>
                </div>
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#c9a84c]">{s.expectReturn}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期收益</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </DataCard>
    </div>
  );
}
