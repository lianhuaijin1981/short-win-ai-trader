import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactEChartsCore from 'echarts-for-react';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  BookOpen,
  AlertTriangle,
  Clock,
  Target,
  Zap,
  ChevronRight,
  CheckCircle2,
  Circle,
  Lightbulb,
  // ShieldAlert,
  // Award,
  Brain,
  // Crosshair,
  // Timer,
  // Newspaper,
  // Layers,
  // Settings,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────
interface TradeStat {
  label: string;
  value: string;
  isPositive?: boolean;
  isNegative?: boolean;
  isGold?: boolean;
}

interface StyleType {
  name: string;
  score: number;
  icon: string;
  color: string;
}

interface TopicData {
  name: string;
  profit: number;
  count: number;
  winRate: number;
}

interface PatternData {
  name: string;
  profit: number;
  count: number;
  winRate: number;
}

interface Mistake {
  date: string;
  code: string;
  name: string;
  loss: number;
  type: string;
  desc: string;
  status: 'pending' | 'analyzed' | 'improved';
  aiAnalysis: string;
}

interface Suggestion {
  title: string;
  detail: string;
  priority: 'high' | 'medium' | 'low';
  effect: string;
}

interface CalendarItem {
  day: string;
  task: string;
  status: 'done' | 'in_progress' | 'pending';
}

// ── Mock Data ─────────────────────────────────────────────────
const tradeStats: TradeStat[] = [
  { label: '总交易数', value: '156笔', isGold: true },
  { label: '胜率', value: '62.8%', isPositive: true },
  { label: '盈亏比', value: '1.78', isGold: true },
  { label: '最大回撤', value: '-8.2%', isNegative: true },
  { label: '平均盈利', value: '+¥2,450', isPositive: true },
  { label: '平均亏损', value: '-¥1,380', isNegative: true },
];

const tradeDistribution = [
  { day: '周一', value: 3200 },
  { day: '周二', value: -1200 },
  { day: '周三', value: 4500 },
  { day: '周四', value: -800 },
  { day: '周五', value: 2100 },
  { day: '周一', value: 3800 },
  { day: '周二', value: -2100 },
  { day: '周三', value: 5600 },
  { day: '周四', value: -1500 },
  { day: '周五', value: -3200 },
  { day: '周一', value: 4200 },
  { day: '周二', value: 1800 },
];

const styleTypes: StyleType[] = [
  { name: '龙头接力', score: 85, icon: 'zap', color: '#c9a84c' },
  { name: '分歧低吸', score: 72, icon: 'trending-down', color: '#3b82f6' },
  { name: '事件催化', score: 78, icon: 'zap', color: '#06d7d7' },
  { name: '趋势波段', score: 65, icon: 'trending-up', color: '#8b5cf6' },
  { name: '冰点试错', score: 58, icon: 'shield', color: '#f97316' },
  { name: '首板挖掘', score: 70, icon: 'target', color: '#22c55e' },
];

const goldenHours = [
  { time: '9:30-10:00', score: 92, label: '黄金时段', color: '#c9a84c' },
  { time: '10:00-10:30', score: 78, label: '高效时段', color: '#3b82f6' },
  { time: '10:30-11:30', score: 55, label: '一般时段', color: '#f59e0b' },
  { time: '13:00-14:00', score: 62, label: '观察时段', color: '#8b5cf6' },
  { time: '14:00-14:45', score: 70, label: '较好时段', color: '#06d7d7' },
  { time: '14:45-15:00', score: 45, label: '谨慎时段', color: '#475569' },
];

const goodTopics: TopicData[] = [
  { name: '人工智能', profit: 18500, count: 28, winRate: 75 },
  { name: '新能源车', profit: 12300, count: 18, winRate: 72 },
  { name: '半导体', profit: 8900, count: 15, winRate: 68 },
  { name: '机器人', profit: 6200, count: 10, winRate: 80 },
];

const badTopics: TopicData[] = [
  { name: '房地产', profit: -4200, count: 8, winRate: 25 },
  { name: '医药生物', profit: -3800, count: 12, winRate: 33 },
  { name: '光伏', profit: -2100, count: 6, winRate: 33 },
  { name: '银行', profit: -1500, count: 5, winRate: 20 },
];

const goodPatterns: PatternData[] = [
  { name: '筹码峰突破', profit: 15200, count: 22, winRate: 82 },
  { name: 'N字形反包', profit: 9800, count: 16, winRate: 75 },
  { name: '龙回头', profit: 7600, count: 12, winRate: 78 },
  { name: '首阴反包', profit: 5400, count: 10, winRate: 70 },
];

const badPatterns: PatternData[] = [
  { name: '三倍量突破', profit: -5200, count: 14, winRate: 36 },
  { name: '平台突破', profit: -3800, count: 10, winRate: 30 },
  { name: '尾盘偷袭', profit: -2900, count: 8, winRate: 25 },
  { name: '跟风追涨', profit: -4100, count: 12, winRate: 17 },
];

const highFreqErrors = [
  { name: '止损不坚决', count: 18, loss: 18500, trend: 'up' as const },
  { name: '追高被套', count: 14, loss: 15200, trend: 'up' as const },
  { name: '逆势操作', count: 11, loss: 12300, trend: 'down' as const },
  { name: '仓位过重', count: 9, loss: 9800, trend: 'up' as const },
  { name: '模式外交易', count: 7, loss: 6500, trend: 'down' as const },
];

const profitAttribution = [
  { name: '行情把握', value: 35, color: '#c9a84c' },
  { name: '资讯优势', value: 20, color: '#3b82f6' },
  { name: '技术分析', value: 25, color: '#06d7d7' },
  { name: '模式执行', value: 15, color: '#8b5cf6' },
  { name: '操作纪律', value: 5, color: '#22c55e' },
];

const lossTracing = [
  { name: '宏观环境', value: 15, color: '#ef4444' },
  { name: '题材退潮', value: 25, color: '#f97316' },
  { name: '标的选择', value: 20, color: '#f59e0b' },
  { name: '模式失效', value: 18, color: '#8b5cf6' },
  { name: '节奏踏错', value: 12, color: '#06d7d7' },
  { name: '风控不足', value: 22, color: '#ef4444' },
  { name: '信息滞后', value: 8, color: '#475569' },
];

const mistakes: Mistake[] = [
  {
    date: '01/15',
    code: '002XXX',
    name: '某某科技',
    loss: 2100,
    type: '止损不坚决',
    desc: '跌破5日线未及时止损，心存侥幸导致亏损扩大',
    status: 'pending',
    aiAnalysis: '止损纪律执行不到位，建议设置-3%硬止损线。同类错误本月已发生3次。',
  },
  {
    date: '01/13',
    code: '600XXX',
    name: '某某股份',
    loss: 1500,
    type: '追高被套',
    desc: '已涨7%后追涨买入，买入后即回落',
    status: 'analyzed',
    aiAnalysis: '追涨时机过晚，应等回调或早盘第一时间介入。',
  },
  {
    date: '01/10',
    code: '300XXX',
    name: '某某智能',
    loss: 1800,
    type: '逆势操作',
    desc: '大盘下跌中强行买入，被系统性风险拖累',
    status: 'improved',
    aiAnalysis: '未考虑大盘环境，建议加入大盘趋势判断条件。',
  },
  {
    date: '01/08',
    code: '000XXX',
    name: '某某新材',
    loss: 3200,
    type: '仓位过重',
    desc: '单票仓位达70%，波动剧烈时无法承受',
    status: 'pending',
    aiAnalysis: '单票仓位不应超过30%，当前仓位管理存在严重问题。',
  },
  {
    date: '01/05',
    code: '688XXX',
    name: '某某微',
    loss: 900,
    type: '模式外交易',
    desc: '不符合任何战法规则，凭感觉买入',
    status: 'analyzed',
    aiAnalysis: '严格按模式交易，不符合条件坚决不做。',
  },
];

const suggestions: Suggestion[] = [
  { title: '严格执行止损', detail: '设定-3%硬止损线，触发后无条件执行，不抱侥幸心理', priority: 'high', effect: '预计提升胜率5%' },
  { title: '控制单票仓位', detail: '单票仓位不超过30%，分2-3批建仓', priority: 'high', effect: '预计降低回撤40%' },
  { title: '只做模式内交易', detail: '严格按15+战法筛选，不符合条件坚决不做', priority: 'medium', effect: '预计提升胜率3%' },
  { title: '加强早盘操作', detail: '数据显示你早盘胜率70%，聚焦早盘机会', priority: 'medium', effect: '预计提升收益8%' },
  { title: '复盘每笔交易', detail: '建立交易日志，每日收盘后15分钟强制复盘', priority: 'low', effect: '预计提升纪律性10%' },
];

const calendar: CalendarItem[] = [
  { day: '周一', task: '制定本周交易计划', status: 'done' },
  { day: '周二', task: '严格执行止损规则', status: 'in_progress' },
  { day: '周三', task: '控制仓位在30%内', status: 'pending' },
  { day: '周四', task: '只做模式内交易', status: 'pending' },
  { day: '周五', task: '周末全面复盘', status: 'pending' },
  { day: '周六', task: '错题库复盘+改进', status: 'pending' },
  { day: '周日', task: '更新交易日志', status: 'pending' },
];

// Style radar dimensions (5维)
const styleDimensions = [
  { name: '进攻性', max: 100 },
  { name: '防守性', max: 100 },
  { name: '纪律性', max: 100 },
  { name: '适应力', max: 100 },
  { name: '复盘力', max: 100 },
];

const userStyleData = [72, 58, 65, 70, 55];
const topTraderStyleData = [85, 80, 90, 82, 88];

// ── Helper Components ────────────────────────────────────────

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    high: 'bg-[#ef4444] text-white',
    medium: 'bg-[#f59e0b] text-[#060b14]',
    low: 'bg-[#c9a84c] text-[#060b14]',
  };
  const labels: Record<string, string> = { high: '高', medium: '中', low: '低' };
  return (
    <span className={cn('text-[10px] px-2 py-0.5 rounded-full font-medium', colors[priority] || colors.low)}>
      {labels[priority] || '低'}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]',
    analyzed: 'bg-[rgba(201,168,76,0.15)] text-[#c9a84c]',
    improved: 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]',
  };
  const labels: Record<string, string> = { pending: '待复盘', analyzed: '已分析', improved: '已改进' };
  return (
    <span className={cn('text-[10px] px-2 py-0.5 rounded-full font-medium', styles[status])}>
      {labels[status]}
    </span>
  );
}

function CalendarIcon({ status }: { status: string }) {
  if (status === 'done') return <CheckCircle2 size={14} className="text-[#22c55e]" />;
  if (status === 'in_progress') return <Circle size={14} className="text-[#c9a84c]" />;
  return <Circle size={14} className="text-[#475569]" />;
}

// ── Main Page ─────────────────────────────────────────────────
export default function Diagnosis() {
  const [period, setPeriod] = useState<'7d' | '30d' | 'year'>('30d');
  const [attrTab, setAttrTab] = useState<'topic' | 'pattern'>('topic');
  const [showCompare, setShowCompare] = useState(false);
  const [expandedMistake, setExpandedMistake] = useState<number | null>(null);
  const [mistakeFilter, setMistakeFilter] = useState<'all' | 'pending' | 'improved'>('all');

  const periods: { key: typeof period; label: string }[] = [
    { key: '7d', label: '近7日' },
    { key: '30d', label: '近30日' },
    { key: 'year', label: '本年' },
  ];

  // Style radar option
  const styleRadarOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      radar: {
        indicator: styleDimensions,
        center: ['50%', '52%'],
        radius: '60%',
        axisName: { color: '#94a3b8', fontSize: 11 },
        splitArea: { areaStyle: { color: ['transparent'] } },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: userStyleData,
              name: '我的风格',
              areaStyle: { color: 'rgba(201,168,76,0.2)' },
              lineStyle: { color: '#c9a84c', width: 2 },
              itemStyle: { color: '#c9a84c' },
            },
            ...(showCompare
              ? [
                  {
                    value: topTraderStyleData,
                    name: '顶级游资',
                    areaStyle: { color: 'rgba(59,130,246,0.08)' },
                    lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' as const },
                    itemStyle: { color: '#3b82f6' },
                  },
                ]
              : []),
          ],
          animationDuration: 1000,
        },
      ],
    }),
    [showCompare]
  );

  // PnL distribution bar chart option
  const pnlBarOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      grid: { left: 10, right: 10, top: 5, bottom: 20 },
      xAxis: {
        type: 'category' as const,
        data: tradeDistribution.map((_, i) => `${i + 1}`),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#475569', fontSize: 10 },
      },
      yAxis: {
        type: 'value' as const,
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
        axisLabel: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: tradeDistribution.map((d) => ({
            value: d.value,
            itemStyle: {
              color: d.value >= 0 ? 'rgba(239,68,68,0.6)' : 'rgba(34,197,94,0.6)',
              borderRadius: d.value >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3],
            },
          })),
          barWidth: '60%',
          animationDuration: 600,
          animationDelay: (idx: number) => idx * 40,
        },
      ],
    }),
    []
  );

  // Attribution bar chart
  const attrBarOption = useMemo(() => {
    const data = attrTab === 'topic' ? [...goodTopics, ...badTopics.map((t) => ({ ...t, profit: -t.profit }))] : [...goodPatterns, ...badPatterns.map((p) => ({ ...p, profit: -p.profit }))];
    const colors = data.map((d) => (d.profit >= 0 ? '#ef4444' : '#22c55e'));
    return {
      backgroundColor: 'transparent',
      grid: { left: 100, right: 80, top: 10, bottom: 10 },
      xAxis: {
        type: 'value' as const,
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
        axisLabel: { color: '#475569', fontSize: 10, formatter: (v: number) => `¥${Math.abs(v).toLocaleString()}` },
      },
      yAxis: {
        type: 'category' as const,
        data: data.map((d) => d.name).reverse(),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
      },
      series: [
        {
          type: 'bar',
          data: data.map((d, i) => ({
            value: d.profit,
            itemStyle: { color: colors[i], borderRadius: d.profit >= 0 ? [0, 3, 3, 0] : [3, 0, 0, 3] },
          })).reverse(),
          barWidth: 16,
          label: {
            show: true,
            position: 'right' as const,
            color: '#94a3b8',
            fontSize: 10,
            formatter: (p: { value: number; dataIndex: number }) => {
              const idx = data.length - 1 - p.dataIndex;
              return `${data[idx].winRate}%胜率 ${data[idx].count}笔`;
            },
          },
          animationDuration: 600,
          animationDelay: (idx: number) => idx * 80,
        },
      ],
    };
  }, [attrTab]);

  // Profit attribution pie
  const profitPieOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 4, borderColor: '#0d1526', borderWidth: 2 },
          label: { show: true, color: '#94a3b8', fontSize: 10, formatter: '{b}\n{d}%' },
          data: profitAttribution.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
          animationDuration: 1000,
        },
      ],
    }),
    []
  );

  // Loss tracing pie
  const lossPieOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 4, borderColor: '#0d1526', borderWidth: 2 },
          label: { show: true, color: '#94a3b8', fontSize: 10, formatter: '{b}\n{d}%' },
          data: lossTracing.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
          animationDuration: 1000,
        },
      ],
    }),
    []
  );

  const filteredMistakes = useMemo(() => {
    if (mistakeFilter === 'all') return mistakes;
    return mistakes.filter((m) => m.status === mistakeFilter);
  }, [mistakeFilter]);

  const calendarProgress = useMemo(() => {
    const done = calendar.filter((c) => c.status === 'done').length;
    return { done, total: calendar.length, percent: Math.round((done / calendar.length) * 100) };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-bold text-[#f1f5f9] leading-tight">交割单诊断</h1>
          <p className="text-[#94a3b8] text-[14px] mt-1">交易归因分析与错题库系统</p>
        </div>
      </div>

      {/* ── Row 1: Trading Profile + Attribution ──────────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Trading Profile */}
        <div className="col-span-4">
          <DataCard
            delay={200}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">交易画像</h2>
                <div className="flex gap-1">
                  {periods.map((p) => (
                    <button
                      key={p.key}
                      onClick={() => setPeriod(p.key)}
                      className={cn(
                        'text-[11px] px-2 py-1 rounded-md transition-all duration-200',
                        period === p.key
                          ? 'bg-[#141e33] text-[#c9a84c]'
                          : 'text-[#94a3b8] hover:text-[#f1f5f9]'
                      )}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </>
            }
          >
            {/* Core stats */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              {tradeStats.slice(0, 3).map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1, duration: 0.5 }}
                  className="text-center p-2.5 rounded-lg bg-[#141e33]"
                >
                  <div
                    className={cn(
                      'text-[18px] font-mono font-bold',
                      stat.isPositive ? 'text-[#ef4444]' : stat.isNegative ? 'text-[#22c55e]' : stat.isGold ? 'text-[#c9a84c]' : 'text-[#f1f5f9]'
                    )}
                  >
                    {stat.value}
                  </div>
                  <div className="text-[10px] text-[#94a3b8]">{stat.label}</div>
                </motion.div>
              ))}
            </div>

            {/* PnL Distribution Chart */}
            <div className="mb-4">
              <p className="text-[11px] text-[#94a3b8] mb-2">盈亏分布</p>
              <ReactEChartsCore option={pnlBarOption} style={{ height: 120 }} />
              {/* Zero line indicator */}
              <div className="relative h-[1px] bg-[rgba(148,163,184,0.1)] mt-1">
                <div className="absolute left-1/2 top-0 w-[1px] h-2 bg-[#94a3b8] -translate-y-1/2" />
              </div>
            </div>

            {/* Detailed stats grid */}
            <div className="grid grid-cols-2 gap-2">
              {tradeStats.slice(3).map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + i * 0.06, duration: 0.3 }}
                  className="flex justify-between items-center py-1.5 px-2 rounded-md bg-[#0f1929]"
                >
                  <span className="text-[11px] text-[#94a3b8]">{stat.label}</span>
                  <span
                    className={cn(
                      'text-[13px] font-mono font-semibold',
                      stat.isPositive ? 'text-[#ef4444]' : stat.isNegative ? 'text-[#22c55e]' : 'text-[#f1f5f9]'
                    )}
                  >
                    {stat.value}
                  </span>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>

        {/* Attribution Analysis */}
        <div className="col-span-8">
          <DataCard
            delay={300}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">交易归因分析</h2>
                <div className="flex gap-1">
                  {[
                    { key: 'topic' as const, label: '题材' },
                    { key: 'pattern' as const, label: '模式' },
                  ].map((t) => (
                    <button
                      key={t.key}
                      onClick={() => setAttrTab(t.key)}
                      className={cn(
                        'text-[11px] px-2 py-1 rounded-md transition-all duration-200',
                        attrTab === t.key
                          ? 'bg-[#141e33] text-[#c9a84c]'
                          : 'text-[#94a3b8] hover:text-[#f1f5f9]'
                      )}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </>
            }
          >
            <div className="grid grid-cols-2 gap-4">
              {/* Attribution bar chart */}
              <ReactEChartsCore option={attrBarOption} style={{ height: 260 }} notMerge={true} />

              {/* AI Summary */}
              <div className="space-y-3">
                <div className="relative bg-[#141e33] rounded-lg p-3 pl-4">
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-lg" />
                  <p className="text-[12px] text-[#94a3b8] leading-relaxed">
                    你最赚钱的{attrTab === 'topic' ? '题材' : '模式'}是
                    <span className="text-[#ef4444] font-semibold"> {attrTab === 'topic' ? '人工智能' : '筹码峰突破'} </span>
                    (+¥{attrTab === 'topic' ? '18,500' : '15,200'}，
                    {attrTab === 'topic' ? '75' : '82'}%胜率)。
                    {attrTab === 'topic'
                      ? '半导体板块表现较弱，建议减少相关操作。'
                      : '三倍量突破模式近期失效较多，建议暂时回避。'}
                  </p>
                </div>

                {/* High frequency errors */}
                <div>
                  <p className="text-[11px] text-[#94a3b8] mb-2 flex items-center gap-1">
                    <AlertTriangle size={12} className="text-[#ef4444]" />
                    高频错误 TOP5
                  </p>
                  <div className="space-y-1.5">
                    {highFreqErrors.map((err, i) => (
                      <motion.div
                        key={err.name}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + i * 0.08, duration: 0.3 }}
                        className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-[rgba(239,68,68,0.05)] border border-[rgba(239,68,68,0.1)]"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-medium text-[#f1f5f9]">{err.name}</span>
                          <span className="text-[10px] text-[#475569]">{err.count}次</span>
                        </div>
                        <span className="text-[11px] font-mono text-[#22c55e]">-¥{err.loss.toLocaleString()}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 2: Style Profile + Mistake Library ────────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Style Profile */}
        <div className="col-span-6">
          <DataCard
            delay={400}
            header={
              <>
                <div className="flex items-center gap-2">
                  <Brain size={16} className="text-[#c9a84c]" />
                  <h2 className="text-[18px] font-semibold text-[#f1f5f9]">风格画像</h2>
                </div>
                <button
                  onClick={() => setShowCompare(!showCompare)}
                  className={cn(
                    'text-[11px] px-2 py-1 rounded-full border transition-all',
                    showCompare
                      ? 'border-[#3b82f6] text-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                      : 'border-[rgba(148,163,184,0.2)] text-[#94a3b8]'
                  )}
                >
                  vs 顶级游资
                </button>
              </>
            }
          >
            <div className="flex gap-4">
              {/* Radar */}
              <div className="relative flex-shrink-0" style={{ width: 260 }}>
                <ReactEChartsCore option={styleRadarOption} style={{ height: 240 }} notMerge={true} />
                {/* Center grade */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 1, duration: 0.5, type: 'spring' }}
                    className="text-[22px] font-bold text-[#c9a84c]"
                  >
                    B+
                  </motion.div>
                  <div className="text-[9px] text-[#94a3b8]">成长中</div>
                </div>
              </div>

              {/* Style types + Tags */}
              <div className="flex-1 space-y-3">
                {/* Style type scores */}
                <div className="space-y-2">
                  <p className="text-[11px] text-[#94a3b8] mb-1">风格定型</p>
                  {styleTypes.map((s, i) => (
                    <motion.div
                      key={s.name}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.06, duration: 0.3 }}
                      className="flex items-center gap-2"
                    >
                      <span className="text-[11px] text-[#94a3b8] w-16 shrink-0">{s.name}</span>
                      <div className="flex-1 h-2 bg-[#141e33] rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${s.score}%` }}
                          transition={{ delay: 0.7 + i * 0.06, duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: s.color }}
                        />
                      </div>
                      <span className="text-[11px] font-mono text-[#f1f5f9] w-8 text-right">{s.score}</span>
                    </motion.div>
                  ))}
                </div>

                {/* Style tags */}
                <div className="pt-2 border-t border-[rgba(148,163,184,0.1)]">
                  <p className="text-[11px] text-[#94a3b8] mb-2">风格标签</p>
                  <div className="flex flex-wrap gap-1.5">
                    {['趋势跟随者', '短线选手', '题材驱动', '偏好多头', '执行力待提高'].map((tag, i) => (
                      <motion.span
                        key={tag}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 1 + i * 0.06, type: 'spring' }}
                        className={cn(
                          'text-[10px] px-2.5 py-1 rounded-full border',
                          i < 2
                            ? 'border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.08)]'
                            : i === 2
                              ? 'border-[#8b5cf6] text-[#8b5cf6] bg-[rgba(139,92,246,0.08)]'
                              : i === 3
                                ? 'border-[#ef4444] text-[#ef4444] bg-[rgba(239,68,68,0.08)]'
                                : 'border-[#f59e0b] text-[#f59e0b] bg-[rgba(249,115,22,0.08)]'
                        )}
                      >
                        {tag}
                      </motion.span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </DataCard>
        </div>

        {/* Mistake Library */}
        <div className="col-span-6">
          <DataCard
            delay={500}
            header={
              <>
                <div className="flex items-center gap-2">
                  <BookOpen size={16} className="text-[#ef4444]" />
                  <h2 className="text-[18px] font-semibold text-[#f1f5f9]">错题库</h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[rgba(239,68,68,0.15)] text-[#ef4444] font-medium">
                    {mistakes.length}笔待复盘
                  </span>
                  <div className="flex gap-1">
                    {[
                      { key: 'all' as const, label: '全部' },
                      { key: 'pending' as const, label: '未复盘' },
                      { key: 'improved' as const, label: '已改进' },
                    ].map((f) => (
                      <button
                        key={f.key}
                        onClick={() => setMistakeFilter(f.key)}
                        className={cn(
                          'text-[10px] px-2 py-0.5 rounded-md transition-all',
                          mistakeFilter === f.key
                            ? 'bg-[#141e33] text-[#c9a84c]'
                            : 'text-[#475569] hover:text-[#94a3b8]'
                        )}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            }
          >
            <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
              <AnimatePresence mode="wait">
                {filteredMistakes.map((m, i) => (
                  <motion.div
                    key={m.date + m.code}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: i * 0.1, duration: 0.4 }}
                    className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] overflow-hidden transition-all duration-200 hover:bg-[#141e33]"
                  >
                    <div
                      className="p-3 cursor-pointer"
                      onClick={() => setExpandedMistake(expandedMistake === i ? null : i)}
                    >
                      {/* Top row */}
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono text-[#475569]">{m.date}</span>
                          <span className="text-[13px] text-[#f1f5f9]">{m.name}</span>
                          <span className="text-[11px] text-[#475569] font-mono">{m.code}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-mono text-[#22c55e]">-¥{m.loss.toLocaleString()}</span>
                          <StatusBadge status={m.status} />
                        </div>
                      </div>
                      {/* Error type */}
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] px-2 py-0.5 rounded-full border border-[#ef4444] text-[#ef4444] bg-[rgba(239,68,68,0.08)]">
                          {m.type}
                        </span>
                        <ChevronRight
                          size={14}
                          className={cn(
                            'text-[#475569] transition-transform duration-200',
                            expandedMistake === i && 'rotate-90'
                          )}
                        />
                      </div>
                      {/* Description */}
                      <p className="text-[11px] text-[#94a3b8] mt-1.5 leading-relaxed">{m.desc}</p>
                    </div>

                    {/* Expanded AI Analysis */}
                    <AnimatePresence>
                      {expandedMistake === i && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden"
                        >
                          <div className="px-3 pb-3">
                            <div className="bg-[#141e33] rounded-lg p-3 relative pl-4">
                              <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-lg" />
                              <p className="text-[11px] text-[#94a3b8] leading-relaxed mb-2">{m.aiAnalysis}</p>
                              <button className="text-[10px] px-3 py-1 bg-[#c9a84c] text-[#060b14] rounded-full font-medium hover:bg-[#e0c878] transition-colors">
                                标记已改进
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 3: Golden Hour + Attribution Details ──────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Golden Trading Hours */}
        <div className="col-span-4">
          <DataCard
            delay={500}
            header={
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-[#c9a84c]" />
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">黄金出手时段</h2>
              </div>
            }
          >
            <div className="space-y-3">
              {goldenHours.map((h, i) => (
                <motion.div
                  key={h.time}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.08, duration: 0.3 }}
                  className="flex items-center gap-3"
                >
                  <span className="text-[11px] text-[#94a3b8] w-24 shrink-0 font-mono">{h.time}</span>
                  <div className="flex-1 h-3 bg-[#141e33] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${h.score}%` }}
                      transition={{ delay: 0.7 + i * 0.08, duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: h.color }}
                    />
                  </div>
                  <span className="text-[11px] font-mono font-semibold w-10 text-right" style={{ color: h.color }}>
                    {h.score}
                  </span>
                </motion.div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-[rgba(148,163,184,0.1)]">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[rgba(201,168,76,0.05)] border border-[rgba(201,168,76,0.15)]">
                <Zap size={14} className="text-[#c9a84c]" />
                <span className="text-[11px] text-[#94a3b8]">
                  建议集中在 <span className="text-[#c9a84c] font-semibold">9:30-10:00</span> 出手，胜率最高
                </span>
              </div>
            </div>
          </DataCard>
        </div>

        {/* Good vs Bad Topic/Pattern Comparison */}
        <div className="col-span-4">
          <DataCard
            delay={550}
            header={
              <>
                <div className="flex items-center gap-2">
                  <BarChart3 size={16} className="text-[#22c55e]" />
                  <h2 className="text-[18px] font-semibold text-[#f1f5f9]">
                    {attrTab === 'topic' ? '擅长/亏损题材' : '擅长/亏损模式'}
                  </h2>
                </div>
              </>
            }
          >
            <div className="space-y-4">
              {/* Good at */}
              <div>
                <p className="text-[11px] text-[#22c55e] mb-2 flex items-center gap-1">
                  <TrendingUp size={12} />
                  擅长{attrTab === 'topic' ? '题材' : '模式'}
                </p>
                <div className="space-y-1.5">
                  {(attrTab === 'topic' ? goodTopics : goodPatterns).map((item, i) => (
                    <motion.div
                      key={item.name}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.06, duration: 0.3 }}
                      className="flex items-center justify-between py-1 px-2 rounded-md bg-[rgba(239,68,68,0.03)]"
                    >
                      <span className="text-[12px] text-[#f1f5f9]">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono text-[#ef4444]">+¥{item.profit.toLocaleString()}</span>
                        <span className="text-[10px] text-[#22c55e]">{item.winRate}%胜</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Bad at */}
              <div className="pt-2 border-t border-[rgba(148,163,184,0.1)]">
                <p className="text-[11px] text-[#22c55e] mb-2 flex items-center gap-1">
                  <TrendingDown size={12} />
                  亏损{attrTab === 'topic' ? '题材' : '模式'}
                </p>
                <div className="space-y-1.5">
                  {(attrTab === 'topic' ? badTopics : badPatterns).map((item, i) => (
                    <motion.div
                      key={item.name}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + i * 0.06, duration: 0.3 }}
                      className="flex items-center justify-between py-1 px-2 rounded-md bg-[rgba(34,197,94,0.03)]"
                    >
                      <span className="text-[12px] text-[#f1f5f9]">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono text-[#22c55e]">-¥{Math.abs(item.profit).toLocaleString()}</span>
                        <span className="text-[10px] text-[#ef4444]">{item.winRate}%胜</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </DataCard>
        </div>

        {/* Profit Attribution + Loss Tracing */}
        <div className="col-span-4">
          <DataCard
            delay={600}
            header={
              <div className="flex items-center gap-2">
                <Target size={16} className="text-[#c9a84c]" />
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">盈利归因 / 亏损溯源</h2>
              </div>
            }
          >
            <div className="grid grid-cols-2 gap-3">
              {/* Profit Attribution Pie */}
              <div>
                <p className="text-[11px] text-[#c9a84c] mb-1 text-center">盈利归因 (5维)</p>
                <ReactEChartsCore option={profitPieOption} style={{ height: 180 }} />
              </div>
              {/* Loss Tracing Pie */}
              <div>
                <p className="text-[11px] text-[#ef4444] mb-1 text-center">亏损溯源 (7类)</p>
                <ReactEChartsCore option={lossPieOption} style={{ height: 180 }} />
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 4: Improvement Plan (full width) ──────────── */}
      <DataCard
        delay={700}
        header={
          <div className="flex items-center gap-2">
            <Lightbulb size={18} className="text-[#c9a84c]" />
            <h2 className="text-[18px] font-semibold text-[#f1f5f9]">改进建议与行动计划</h2>
          </div>
        }
      >
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Suggestions */}
          <div className="col-span-7 space-y-3">
            {suggestions.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + i * 0.08, duration: 0.35 }}
                className="flex items-start gap-3 p-3 rounded-lg border border-[rgba(148,163,184,0.08)] bg-[#0f1929] hover:border-[rgba(201,168,76,0.2)] transition-all"
              >
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#c9a84c] flex items-center justify-center text-[#060b14] text-[12px] font-bold">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[14px] font-medium text-[#f1f5f9]">{s.title}</span>
                    <PriorityBadge priority={s.priority} />
                  </div>
                  <p className="text-[12px] text-[#94a3b8] leading-relaxed">{s.detail}</p>
                  <p className="text-[10px] text-[#c9a84c] mt-1">{s.effect}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Right: Calendar */}
          <div className="col-span-5">
            <div className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4">
              <p className="text-[13px] font-medium text-[#f1f5f9] mb-3">本周行动计划</p>
              <div className="space-y-2">
                {calendar.map((item, i) => (
                  <motion.div
                    key={item.day}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 + i * 0.05, duration: 0.3 }}
                    className="flex items-center gap-3 py-2 px-2 rounded-md hover:bg-[#141e33] transition-colors"
                  >
                    <CalendarIcon status={item.status} />
                    <span className={cn(
                      'text-[12px] w-10',
                      item.status === 'done' ? 'text-[#475569] line-through' : 'text-[#94a3b8]'
                    )}>
                      {item.day}
                    </span>
                    <span className={cn(
                      'text-[12px] flex-1',
                      item.status === 'done' ? 'text-[#475569] line-through' : 'text-[#f1f5f9]'
                    )}>
                      {item.task}
                    </span>
                    {item.status === 'done' && <CheckCircle2 size={14} className="text-[#22c55e]" />}
                    {item.status === 'in_progress' && <span className="text-[9px] text-[#c9a84c]">进行中</span>}
                  </motion.div>
                ))}
              </div>

              {/* Progress */}
              <div className="mt-4 pt-3 border-t border-[rgba(148,163,184,0.1)]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] text-[#94a3b8]">本周完成度</span>
                  <span className="text-[11px] font-mono text-[#c9a84c]">{calendarProgress.done}/{calendarProgress.total}</span>
                </div>
                <div className="h-2 bg-[#141e33] rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${calendarProgress.percent}%` }}
                    transition={{ delay: 1.5, duration: 1, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                    className="h-full bg-gradient-to-r from-[#8a7530] to-[#c9a84c] rounded-full"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </DataCard>
    </div>
  );
}
