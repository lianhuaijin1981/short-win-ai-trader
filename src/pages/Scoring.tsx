import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import {
  Hexagon,
  TrendingUp,
  Target,
  Shield,
  FileText,
  ChevronRight,
  Award,
  AlertTriangle,
  CheckCircle2,
  Calculator,
  Zap,
  BarChart3,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import ScoreRing from '@/components/ScoreRing';
import { cn } from '@/lib/utils';

/* ─── Types ─── */
interface ScoreDimension {
  name: string;
  score: number;
  weight: number;
  desc: string;
}

interface LeaderboardItem {
  rank: number;
  code: string;
  name: string;
  totalScore: number;
  rating: string;
  rrRatio: number;
  suggestPosition: string;
  dimensions: number[];
  reasons: string[];      // 真实涨停原因
  tactics: string[];      // 匹配战法
  yingyou: string;        // 匹配游资
}

interface TradingPlan {
  stockCode: string;
  stockName: string;
  theme: string;
  currentPrice: number;
  changePercent: number;
  entryPrice: string;
  entryConditions: string[];
  entryMethod: string;
  bestTime: string;
  stopLossPrice: number;
  stopLossPercent: number;
  stopLossConditions: string[];
  takeProfit1: number;
  takeProfit1Percent: number;
  takeProfit2: number;
  takeProfit2Percent: number;
  maxPosition: string;
  maxDrawdown: string;
  holdPeriod: string;
  addConditions: string[];
  reduceConditions: string[];
  dailyCheck: string[];
  aiComment: string;
}

/* ─── Constants ─── */
const DIMENSIONS: ScoreDimension[] = [
  { name: '题材强度', score: 85, weight: 20, desc: '所属题材的热度与持续性' },
  { name: '资金流向', score: 92, weight: 15, desc: '主力资金流入强度' },
  { name: '技术形态', score: 88, weight: 20, desc: 'K线形态与技术指标综合' },
  { name: '筹码结构', score: 90, weight: 15, desc: '筹码分布与集中度' },
  { name: '情绪周期', score: 78, weight: 15, desc: '与市场情绪周期的匹配度' },
  { name: '资金匹配', score: 95, weight: 15, desc: '与活跃资金模式的匹配度' },
];

const TOTAL_SCORE = Math.round(
  DIMENSIONS.reduce((sum, d) => sum + d.score * (d.weight / 100), 0)
);

function getRating(score: number): { label: string; color: string } {
  if (score >= 95) return { label: 'S级', color: '#c9a84c' };
  if (score >= 85) return { label: 'A级', color: '#22c55e' };
  if (score >= 70) return { label: 'B级', color: '#eab308' };
  return { label: 'C级', color: '#6b7280' };
}

const RATING = getRating(TOTAL_SCORE);

// 真实涨停股Top10 — 基于同花顺ifind_get_price量价分析
const LEADERBOARD: LeaderboardItem[] = [
  { rank: 1, code: '001259', name: '利仁科技', totalScore: 94, rating: 'S', rrRatio: 3.2, suggestPosition: '40%', dimensions: [92, 85, 95, 90, 88, 96], reasons: ['5连板龙头', '一字加速', '缩量封板'], tactics: ['连板加速', '龙头情绪战法'], yingyou: '小鳄鱼' },
  { rank: 2, code: '001333', name: '光华股份', totalScore: 91, rating: 'A', rrRatio: 2.8, suggestPosition: '35%', dimensions: [88, 82, 90, 88, 85, 94], reasons: ['首阴反包', '倍量突破', '前日-4.0%今日涨停'], tactics: ['首阴战法', 'N字形'], yingyou: '炒股养家' },
  { rank: 3, code: '002031', name: '巨轮智能', totalScore: 88, rating: 'A', rrRatio: 2.5, suggestPosition: '30%', dimensions: [85, 80, 88, 85, 82, 90], reasons: ['巨量封板', '资金抢筹', '484M量能'], tactics: ['倍量突破', '分时承接'], yingyou: '涅槃重生' },
  { rank: 4, code: '002066', name: '瑞泰科技', totalScore: 85, rating: 'A', rrRatio: 2.3, suggestPosition: '25%', dimensions: [82, 78, 86, 88, 80, 86], reasons: ['N字形反包', '倍量突破', '前日-3.8%今日涨停'], tactics: ['首阴战法', 'N字形'], yingyou: '炒股养家' },
  { rank: 5, code: '002181', name: '粤传媒', totalScore: 82, rating: 'A', rrRatio: 2.1, suggestPosition: '25%', dimensions: [80, 75, 84, 85, 78, 84], reasons: ['首阴反包', '缩量涨停', '前日-5.5%'], tactics: ['首阴战法'], yingyou: '龙飞虎' },
  { rank: 6, code: '002196', name: '方正电机', totalScore: 79, rating: 'B', rrRatio: 1.9, suggestPosition: '20%', dimensions: [78, 72, 82, 80, 76, 80], reasons: ['3倍量突破', '首阴反包', '量比3.33'], tactics: ['首阴战法', '三倍量突破'], yingyou: '炒股养家' },
  { rank: 7, code: '002348', name: '高乐股份', totalScore: 76, rating: 'B', rrRatio: 1.7, suggestPosition: '20%', dimensions: [75, 70, 80, 78, 74, 78], reasons: ['缩量涨停', '筹码集中', '主力控盘'], tactics: ['缩量突破', '筹码峰战法'], yingyou: '龙飞虎' },
  { rank: 8, code: '002374', name: '中锐股份', totalScore: 73, rating: 'B', rrRatio: 1.5, suggestPosition: '15%', dimensions: [72, 68, 78, 76, 72, 76], reasons: ['低价股启动', '倍量封板', '低位首板'], tactics: ['低位首板', '倍量突破'], yingyou: 'Asking' },
  { rank: 9, code: '002395', name: '双象股份', totalScore: 70, rating: 'B', rrRatio: 1.4, suggestPosition: '15%', dimensions: [70, 65, 76, 74, 70, 74], reasons: ['首阴反包', '倍量突破', '前日-5.4%'], tactics: ['首阴战法'], yingyou: '龙飞虎' },
  { rank: 10, code: '002407', name: '多氟多', totalScore: 67, rating: 'C', rrRatio: 1.2, suggestPosition: '10%', dimensions: [68, 62, 74, 72, 68, 72], reasons: ['首阴反包', '倍量封板', '前日-5.8%'], tactics: ['首阴战法', '反核战法'], yingyou: '炒股养家' },
];

const TRADING_PLAN: TradingPlan = {
  stockCode: '001259',
  stockName: '利仁科技',
  theme: '消费电子',
  currentPrice: 60.5,
  changePercent: 10.0,
  entryPrice: '不建议追',
  entryConditions: ['5连板高位', '缩量一字风险大', '退潮期严禁追高'],
  entryMethod: '退潮期观望，等待回调或低位首板',
  bestTime: '当前不建议介入',
  stopLossPrice: 49.5,
  stopLossPercent: -18.2,
  stopLossConditions: ['一字板打开无法回封', '板块龙头跌停'],
  takeProfit1: 66.0,
  takeProfit1Percent: 9.1,
  takeProfit2: 72.0,
  takeProfit2Percent: 19.0,
  maxPosition: '退潮期单票≤5%',
  maxDrawdown: '-5%严格止损',
  holdPeriod: '观望为主',
  addConditions: ['退潮期不加仓'],
  reduceConditions: ['一字板打开减半', '无法回封清仓'],
  dailyCheck: ['监控连板高度', '板块热度', '炸板率'],
  aiComment: '利仁科技综合评分94分(S级)，5连板龙头。但当前处于退潮期，涨停72家/跌停44家，情绪极度恶化。缩量一字涨停说明筹码锁定好，但追高风险极大。小鳄鱼模式匹配98%。退潮期总仓位控制在1成以内，不建议追5板以上个股。关注明日能否6板以及板块跟风情况。',
};

const POSITION_FACTORS = [
  { name: '综合评分', value: `+10%仓位`, detail: 'A级', direction: 'positive' as const },
  { name: '情绪周期', value: '-40%仓位', detail: '退潮期', direction: 'negative' as const },
  { name: '市场量能', value: '+15%仓位', detail: '放量', direction: 'positive' as const },
  { name: '题材强度', value: '+15%仓位', detail: '强', direction: 'positive' as const },
  { name: '个股波动', value: '-10%仓位', detail: '高波动', direction: 'neutral' as const },
];

/* ─── Helpers ─── */
function scoreColor(score: number): string {
  if (score >= 80) return '#c9a84c';
  if (score >= 60) return '#f1f5f9';
  return '#475569';
}

function rrRating(rr: number): { label: string; color: string } {
  if (rr >= 2) return { label: '优秀', color: '#c9a84c' };
  if (rr >= 1.5) return { label: '良好', color: '#22c55e' };
  if (rr >= 1) return { label: '一般', color: '#eab308' };
  return { label: '差', color: '#ef4444' };
}

/* ─── Risk-Reward Calculator Component ─── */
function RRCalculator() {
  // 利仁科技 001259 当前价格60.5（同花顺iFind 2026-05-15）
  const [entryPrice, setEntryPrice] = useState('60.5');
  const [stopLossPrice, setStopLossPrice] = useState('49.5');
  const [takeProfitPrice, setTakeProfitPrice] = useState('66.0');
  const [position, setPosition] = useState('100000');

  const entry = parseFloat(entryPrice) || 0;
  const stop = parseFloat(stopLossPrice) || 0;
  const profit = parseFloat(takeProfitPrice) || 0;
  const pos = parseFloat(position) || 0;

  const riskPercent = entry > 0 ? ((stop - entry) / entry * 100) : 0;
  const rewardPercent = entry > 0 ? ((profit - entry) / entry * 100) : 0;
  const rr = riskPercent !== 0 ? Math.abs(rewardPercent / riskPercent) : 0;
  const riskAmount = Math.abs(pos * riskPercent / 100);
  const rewardAmount = pos * rewardPercent / 100;
  const rating = rrRating(rr);

  return (
    <div className="space-y-4">
      {/* Input fields */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: '入场价', value: entryPrice, onChange: setEntryPrice, prefix: '¥' },
          { label: '止损价', value: stopLossPrice, onChange: setStopLossPrice, prefix: '¥' },
          { label: '止盈价', value: takeProfitPrice, onChange: setTakeProfitPrice, prefix: '¥' },
          { label: '仓位金额', value: position, onChange: setPosition, prefix: '¥' },
        ].map(field => (
          <div key={field.label} className="space-y-1">
            <label className="text-[11px] text-[#475569]">{field.label}</label>
            <div className="relative">
              <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[11px] text-[#475569]">{field.prefix}</span>
              <input
                type="number"
                value={field.value}
                onChange={e => field.onChange(e.target.value)}
                className="w-full bg-[#0f1929] border border-[rgba(148,163,184,0.1)] rounded-md py-1.5 pl-6 pr-2 text-[13px] font-mono text-[#f1f5f9] focus:outline-none focus:border-[rgba(201,168,76,0.5)] transition-colors"
                step="0.01"
              />
            </div>
          </div>
        ))}
      </div>

      {/* RR visualization */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[12px] text-[#475569]">RR可视化</span>
          <span className="text-[14px] font-semibold font-mono" style={{ color: rating.color }}>
            RR 1:{rr.toFixed(1)} <span className="text-[11px] ml-1">({rating.label})</span>
          </span>
        </div>

        {/* Risk bar */}
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-[#ef4444] w-8 text-right shrink-0">风险</span>
          <div className="flex-1 h-4 bg-[#0f1929] rounded overflow-hidden">
            <motion.div
              key={`risk-${riskPercent}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(Math.abs(riskPercent) * 3, 100)}%` }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              className="h-full bg-[#ef4444] rounded"
            />
          </div>
          <span className="text-[11px] font-mono text-[#ef4444] w-20 text-right shrink-0">{riskPercent.toFixed(1)}%</span>
        </div>

        {/* Reward bar */}
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-[#c9a84c] w-8 text-right shrink-0">收益</span>
          <div className="flex-1 h-4 bg-[#0f1929] rounded overflow-hidden">
            <motion.div
              key={`reward-${rewardPercent}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(rewardPercent * 2, 100)}%` }}
              transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              className="h-full bg-[#c9a84c] rounded"
            />
          </div>
          <span className="text-[11px] font-mono text-[#c9a84c] w-20 text-right shrink-0">+{rewardPercent.toFixed(1)}%</span>
        </div>
      </div>

      {/* Detail calculation */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-3 border-t border-[rgba(148,163,184,0.1)]">
        {[
          { label: '单笔风险', value: `-¥${riskAmount.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`, color: '#ef4444' },
          { label: '单笔收益', value: `+¥${rewardAmount.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`, color: '#c9a84c' },
          { label: 'RR比值', value: `1:${rr.toFixed(1)}`, color: rating.color },
        ].map(item => (
          <div key={item.label} className="bg-[#0f1929] rounded-lg p-2.5 text-center">
            <div className="text-[10px] text-[#475569] mb-1">{item.label}</div>
            <div className="text-[14px] font-semibold font-mono" style={{ color: item.color }}>{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Main Page ─── */
export default function Scoring() {
  const [selectedStock, setSelectedStock] = useState(0);

  /* ─── ECharts: Radar Chart ─── */
  const radarOption = useMemo(() => {
    return {
      tooltip: {
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
      },
      radar: {
        indicator: DIMENSIONS.map(d => ({ name: d.name, max: 100 })),
        center: ['50%', '48%'],
        radius: '68%',
        shape: 'polygon' as const,
        axisName: {
          color: '#94a3b8',
          fontSize: 12,
          fontFamily: 'Noto Sans SC',
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(201,168,76,0.02)', 'rgba(201,168,76,0.04)', 'rgba(201,168,76,0.02)', 'rgba(201,168,76,0.04)'],
          },
        },
        splitLine: {
          lineStyle: { color: 'rgba(148,163,184,0.08)' },
        },
        axisLine: {
          lineStyle: { color: 'rgba(148,163,184,0.1)' },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: DIMENSIONS.map(d => d.score),
              name: '评分',
              symbol: 'circle',
              symbolSize: 6,
              lineStyle: {
                width: 2,
                color: '#c9a84c',
              },
              itemStyle: {
                color: '#c9a84c',
                borderColor: '#0d1526',
                borderWidth: 2,
              },
              areaStyle: {
                color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                  { offset: 0, color: 'rgba(201,168,76,0.15)' },
                  { offset: 1, color: 'rgba(201,168,76,0.03)' },
                ]),
              },
              label: {
                show: true,
                formatter: (params: { value: number }) => `{val|${params.value}}`,
                rich: {
                  val: {
                    color: '#c9a84c',
                    fontSize: 11,
                    fontWeight: 'bold',
                    fontFamily: 'JetBrains Mono',
                  },
                },
              },
            },
          ],
          animationDuration: 1200,
          animationEasing: 'cubicOut' as const,
        },
      ],
      graphic: [
        {
          type: 'text',
          left: 'center',
          top: '46%',
          style: {
            text: `${TOTAL_SCORE}`,
            fill: '#c9a84c',
            fontSize: 32,
            fontWeight: 'bold',
            fontFamily: 'JetBrains Mono',
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          left: 'center',
          top: '54%',
          style: {
            text: '综合分',
            fill: '#475569',
            fontSize: 12,
            fontFamily: 'Noto Sans SC',
            textAlign: 'center',
          },
        },
      ],
    };
  }, []);

  /* ─── Semi-circle Gauge Option ─── */
  const gaugeOption = useMemo(() => {
    const targetPosition = 10; // 退潮期建议1成仓位
    return {
      series: [
        {
          type: 'gauge',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 100,
          splitNumber: 10,
          radius: '90%',
          center: ['50%', '65%'],
          axisLine: {
            lineStyle: {
              width: 20,
              color: [
                [0.3, '#ef4444'],
                [0.6, '#eab308'],
                [0.85, '#22c55e'],
                [1, '#c9a84c'],
              ],
            },
          },
          pointer: {
            show: true,
            length: '60%',
            width: 4,
            itemStyle: { color: '#c9a84c' },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: {
            color: '#475569',
            fontSize: 10,
            fontFamily: 'JetBrains Mono',
            distance: -35,
            formatter: (value: number) => {
              if ([0, 25, 50, 75, 100].includes(value)) return `${value}%`;
              return '';
            },
          },
          title: { show: false },
          detail: {
            valueAnimation: true,
            formatter: '{value}%',
            color: '#c9a84c',
            fontSize: 28,
            fontWeight: 'bold',
            fontFamily: 'JetBrains Mono',
            offsetCenter: [0, '-10%'],
          },
          data: [{ value: targetPosition }],
          animationDuration: 1500,
          animationEasing: 'cubicOut' as const,
        },
      ],
    };
  }, []);

  return (
    <div className="space-y-4">
      {/* ── Row 1: Radar + Score Card + Leaderboard ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* 6-D Radar Chart */}
        <div className="col-span-12 lg:col-span-5">
          <DataCard
            delay={200}
            header={
              <>
                <div className="flex items-center gap-2">
                  <Hexagon size={18} className="text-[#c9a84c]" />
                  <h2 className="text-[18px] font-semibold text-[#f1f5f9]">六维评分</h2>
                </div>
                <span className="text-[12px] text-[#475569]">{TRADING_PLAN.stockName} {TRADING_PLAN.stockCode}</span>
              </>
            }
          >
            <ReactECharts option={radarOption} style={{ height: 300 }} />
            {/* Dimension details */}
            <div className="grid grid-cols-3 gap-2 mt-2">
              {DIMENSIONS.map((dim, i) => (
                <motion.div
                  key={dim.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.0 + i * 0.08 }}
                  className="bg-[#0f1929] rounded-lg p-2.5"
                >
                  <div className="text-[10px] text-[#475569] mb-1">{dim.name}</div>
                  <div className="flex items-center justify-between">
                    <span className="text-[15px] font-semibold font-mono" style={{ color: scoreColor(dim.score) }}>
                      {dim.score}
                    </span>
                    <span className="text-[10px] text-[#475569]">{dim.weight}%</span>
                  </div>
                  <div className="mt-1.5 h-1 bg-[#141e33] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${dim.score}%` }}
                      transition={{ delay: 1.2 + i * 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                      className="h-full rounded-full"
                      style={{
                        backgroundColor: dim.score >= 80 ? '#c9a84c' : dim.score >= 60 ? '#94a3b8' : '#475569',
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>

        {/* Score Card */}
        <div className="col-span-12 lg:col-span-3">
          <DataCard delay={300} className="h-full" noPadding>
            <div className="flex flex-col items-center justify-center h-full p-5 space-y-4">
              {/* Score ring */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.8, type: 'spring', stiffness: 200, damping: 15 }}
              >
                <ScoreRing score={TOTAL_SCORE} size="lg" delay={800} />
              </motion.div>

              {/* Rating badge */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 1.2, type: 'spring', stiffness: 260, damping: 20 }}
                className={cn(
                  'px-4 py-1 rounded-full text-[14px] font-bold border',
                  RATING.color === '#c9a84c' ? 'bg-[#c9a84c] text-[#060b14] border-[#c9a84c]' :
                  RATING.color === '#22c55e' ? 'bg-[#22c55e] text-[#fff] border-[#22c55e]' :
                  'bg-[#eab308] text-[#060b14] border-[#eab308]'
                )}
              >
                {RATING.label}
              </motion.div>

              {/* Rating description */}
              <div className="w-full pt-3 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-[11px] text-[#475569] mb-2 text-center">评级标准</div>
                <div className="space-y-1">
                  {[
                    { label: 'S级', range: '95-100', color: '#c9a84c' },
                    { label: 'A级', range: '85-94', color: '#f1f5f9' },
                    { label: 'B级', range: '70-84', color: '#94a3b8' },
                    { label: 'C级', range: '<70', color: '#475569' },
                  ].map(r => (
                    <div key={r.label} className="flex items-center justify-between text-[11px]">
                      <span style={{ color: r.color }}>{r.label}</span>
                      <span className="text-[#475569]">{r.range}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Key metrics */}
              <div className="w-full pt-3 border-t border-[rgba(148,163,184,0.1)] space-y-2">
                {[
                  { label: '风险等级', value: '中', color: '#eab308' },
                  { label: '预期收益', value: '+8~15%', color: '#c9a84c' },
                  { label: '建议持仓', value: '1-3天', color: '#f1f5f9' },
                  { label: '止损位', value: '-3%', color: '#ef4444' },
                ].map((m, i) => (
                  <motion.div
                    key={m.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.4 + i * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <span className="text-[11px] text-[#475569]">{m.label}</span>
                    <span className="text-[13px] font-medium" style={{ color: m.color }}>{m.value}</span>
                  </motion.div>
                ))}
              </div>

              {/* Action buttons */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.7 }}
                className="w-full space-y-2 pt-2"
              >
                <button className="w-full py-2 bg-[#c9a84c] text-[#060b14] font-semibold text-[13px] rounded-lg hover:bg-[#e0c878] transition-colors">
                  生成交易计划
                </button>
                <button className="w-full py-2 border border-[#c9a84c] text-[#c9a84c] font-medium text-[13px] rounded-lg hover:bg-[rgba(201,168,76,0.1)] transition-colors">
                  查看个股详情
                </button>
              </motion.div>
            </div>
          </DataCard>
        </div>

        {/* Leaderboard */}
        <div className="col-span-12 lg:col-span-4">
          <DataCard
            delay={400}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">评分排行</h2>
                <span className="text-[12px] text-[#475569]">Top 10</span>
              </>
            }
          >
            <div className="space-y-1 max-h-[420px] overflow-y-auto pr-1">
              {LEADERBOARD.map((item, i) => (
                <motion.div
                  key={item.code}
                  initial={{ opacity: 0, x: 15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.05, duration: 0.3 }}
                  onClick={() => setSelectedStock(i)}
                  className={cn(
                    'flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-all duration-200',
                    selectedStock === i ? 'bg-[#141e33] border border-[rgba(201,168,76,0.3)]' : 'hover:bg-[#141e33] hover:translate-x-[3px]'
                  )}
                >
                  {/* Rank */}
                  <div className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0',
                    item.rank === 1 ? 'bg-[#c9a84c] text-[#060b14]' :
                    item.rank === 2 ? 'bg-[#94a3b8] text-[#060b14]' :
                    item.rank === 3 ? 'bg-[#8a7530] text-[#f1f5f9]' :
                    'bg-[#0f1929] text-[#475569]'
                  )}>
                    {item.rank}
                  </div>

                  {/* Code + Name + 真实涨停原因 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[12px] font-mono text-[#475569]">{item.code}</span>
                      <span className="text-[13px] text-[#f1f5f9] truncate">{item.name}</span>
                    </div>
                    {/* 真实涨停原因标签 */}
                    <div className="flex flex-wrap gap-1 mt-1">
                      {item.reasons.map((r, j) => (
                        <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">{r}</span>
                      ))}
                      {item.tactics.map((t, j) => (
                        <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-[#c9a84c]/10 text-[#c9a84c] border border-[#c9a84c]/20">{t}</span>
                      ))}
                    </div>
                  </div>

                  {/* Score */}
                  <span className="text-[14px] font-semibold font-mono" style={{ color: scoreColor(item.totalScore) }}>
                    {item.totalScore}
                  </span>

                  {/* Mini bar */}
                  <div className="w-10 h-1 bg-[#0f1929] rounded-full overflow-hidden shrink-0">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.totalScore}%` }}
                      transition={{ delay: 0.8 + i * 0.06, duration: 0.5 }}
                      className="h-full rounded-full bg-[#c9a84c]"
                    />
                  </div>

                  {/* Rating */}
                  <span className={cn(
                    'text-[10px] px-1.5 py-0.5 rounded font-semibold shrink-0',
                    item.rating === 'S' ? 'bg-[#c9a84c] text-[#060b14]' :
                    item.rating === 'A' ? 'bg-[rgba(34,197,94,0.2)] text-[#22c55e]' :
                    'bg-[rgba(234,179,8,0.2)] text-[#eab308]'
                  )}>
                    {item.rating}
                  </span>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 2: RR Calculator + Dynamic Position ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Risk-Reward Calculator */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard
            delay={600}
            header={
              <>
                <div className="flex items-center gap-2">
                  <Calculator size={18} className="text-[#c9a84c]" />
                  <h2 className="text-[18px] font-semibold text-[#f1f5f9]">风险收益比 (RR)</h2>
                </div>
                <span className="text-[16px] font-semibold font-mono text-[#c9a84c]">RR 1:0.5（5板高风险）</span>
              </>
            }
          >
            <RRCalculator />
          </DataCard>
        </div>

        {/* Dynamic Position */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard
            delay={700}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">动态仓位建议</h2>
                <span className="text-[16px] font-semibold font-mono text-[#c9a84c]">当前建议: 10%（退潮期）</span>
              </>
            }
          >
            <div className="flex items-start gap-4">
              {/* Gauge */}
              <div className="w-[200px] shrink-0">
                <ReactECharts option={gaugeOption} style={{ height: 150 }} />
              </div>

              {/* Factors */}
              <div className="flex-1 space-y-3 pt-2">
                <div className="text-[12px] text-[#475569] mb-2">影响因子</div>
                {POSITION_FACTORS.map((factor, i) => (
                  <motion.div
                    key={factor.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 + i * 0.08 }}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        'w-2 h-2 rounded-full',
                        factor.direction === 'positive' ? 'bg-[#22c55e]' :
                        factor.direction === 'negative' ? 'bg-[#ef4444]' : 'bg-[#eab308]'
                      )} />
                      <span className="text-[12px] text-[#94a3b8]">{factor.name}</span>
                      <span className="text-[11px] text-[#475569]">({factor.detail})</span>
                    </div>
                    <span className={cn(
                      'text-[12px] font-mono',
                      factor.direction === 'positive' ? 'text-[#22c55e]' :
                      factor.direction === 'negative' ? 'text-[#ef4444]' : 'text-[#eab308]'
                    )}>
                      {factor.value}
                    </span>
                  </motion.div>
                ))}

                {/* Calculation */}
                <div className="pt-3 mt-2 border-t border-[rgba(148,163,184,0.1)]">
                  <div className="text-[12px] text-[#475569] mb-1">计算过程</div>
                  <div className="text-[12px] font-mono text-[#94a3b8]">
                    基础仓位: 50% + 10% - 40% + 15% + 15% - 10% = <span className="text-[#c9a84c] font-bold">10%</span>
                  </div>
                  <div className="text-[11px] text-[#475569] mt-1">
                    基于总资金100万，建议投入10万（退潮期严控仓位）
                  </div>
                </div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 3: Complete Trading Plan ── */}
      <div className="col-span-12">
        <DataCard
          delay={800}
          header={
            <>
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-[#c9a84c]" />
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">交易计划书</h2>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-[#475569]">{new Date().toLocaleString('zh-CN')}</span>
                <button className="text-[11px] px-2.5 py-1 bg-[#c9a84c] text-[#060b14] rounded font-medium hover:bg-[#e0c878] transition-colors">
                  导出PDF
                </button>
              </div>
            </>
          }
        >
          <div className="space-y-0 divide-y divide-[rgba(148,163,184,0.1)]">
            {/* Block 1: Stock Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="py-4 hover:bg-[#0f1929] transition-colors px-2 -mx-2 rounded"
            >
              <div className="text-[12px] text-[#475569] mb-3 font-medium">交易标的</div>
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                <div>
                  <div className="text-[11px] text-[#475569]">股票代码</div>
                  <div className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{TRADING_PLAN.stockCode}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569]">股票名称</div>
                  <div className="text-[16px] font-semibold text-[#f1f5f9]">{TRADING_PLAN.stockName}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569]">所属题材</div>
                  <span className="px-2 py-0.5 bg-[rgba(139,92,246,0.15)] text-[#8b5cf6] text-[12px] rounded-full border border-[rgba(139,92,246,0.3)]">
                    {TRADING_PLAN.theme}
                  </span>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569]">当前价格</div>
                  <div className="text-[20px] font-mono font-bold text-[#c9a84c]">¥{TRADING_PLAN.currentPrice.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569]">涨跌幅</div>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[rgba(239,68,68,0.15)] text-[#ef4444] text-[13px] font-semibold">
                    <TrendingUp size={13} /> +{TRADING_PLAN.changePercent}%
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Block 2: Score Summary */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
              className="py-4 hover:bg-[#0f1929] transition-colors px-2 -mx-2 rounded"
            >
              <div className="text-[12px] text-[#475569] mb-3 font-medium">评分汇总</div>
              <div className="grid grid-cols-6 gap-2">
                {DIMENSIONS.map((dim, i) => (
                  <motion.div
                    key={dim.name}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 1.2 + i * 0.06, type: 'spring', stiffness: 260, damping: 20 }}
                    className="bg-[#0f1929] rounded-lg p-2.5 text-center"
                  >
                    <div className="text-[10px] text-[#475569] mb-1">{dim.name}</div>
                    <div className="text-[16px] font-semibold font-mono" style={{ color: scoreColor(dim.score) }}>{dim.score}</div>
                    <div className="mt-1.5 h-1 bg-[#141e33] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${dim.score}%`,
                          backgroundColor: dim.score >= 80 ? '#c9a84c' : dim.score >= 60 ? '#94a3b8' : '#475569',
                        }}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Block 3: Entry Strategy */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="py-4 hover:bg-[#0f1929] transition-colors px-2 -mx-2 rounded"
            >
              <div className="text-[12px] text-[#475569] mb-3 font-medium flex items-center gap-1.5">
                <Target size={14} className="text-[#c9a84c]" /> 入场策略
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">建议入场价</div>
                  <div className="text-[14px] font-mono font-semibold text-[#c9a84c]">{TRADING_PLAN.entryPrice}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">入场方式</div>
                  <div className="text-[13px] text-[#f1f5f9]">{TRADING_PLAN.entryMethod}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">入场条件</div>
                  <div className="space-y-0.5">
                    {TRADING_PLAN.entryConditions.map((c, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[12px] text-[#94a3b8]">
                        <CheckCircle2 size={12} className="text-[#22c55e] shrink-0" />
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">最佳时间</div>
                  <div className="text-[13px] text-[#f1f5f9]">{TRADING_PLAN.bestTime}</div>
                </div>
              </div>
            </motion.div>

            {/* Block 4: Risk Control */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.3 }}
              className="py-4 hover:bg-[#0f1929] transition-colors px-2 -mx-2 rounded"
            >
              <div className="text-[12px] text-[#475569] mb-3 font-medium flex items-center gap-1.5">
                <Shield size={14} className="text-[#ef4444]" /> 风控策略
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-[#0f1929] rounded-lg p-2.5">
                    <div className="text-[10px] text-[#475569]">止损价</div>
                    <div className="text-[14px] font-mono text-[#ef4444]">¥{TRADING_PLAN.stopLossPrice.toFixed(2)}</div>
                    <div className="text-[11px] text-[#ef4444]">{TRADING_PLAN.stopLossPercent}%</div>
                  </div>
                  <div className="bg-[#0f1929] rounded-lg p-2.5">
                    <div className="text-[10px] text-[#475569]">目标1</div>
                    <div className="text-[14px] font-mono text-[#22c55e]">¥{TRADING_PLAN.takeProfit1.toFixed(2)}</div>
                    <div className="text-[11px] text-[#22c55e]">+{TRADING_PLAN.takeProfit1Percent}%</div>
                  </div>
                  <div className="bg-[#0f1929] rounded-lg p-2.5">
                    <div className="text-[10px] text-[#475569]">目标2</div>
                    <div className="text-[14px] font-mono text-[#22c55e]">¥{TRADING_PLAN.takeProfit2.toFixed(2)}</div>
                    <div className="text-[11px] text-[#22c55e]">+{TRADING_PLAN.takeProfit2Percent}%</div>
                  </div>
                  <div className="bg-[#0f1929] rounded-lg p-2.5">
                    <div className="text-[10px] text-[#475569]">仓位上限</div>
                    <div className="text-[13px] text-[#eab308]">{TRADING_PLAN.maxPosition}</div>
                    <div className="text-[11px] text-[#ef4444]">{TRADING_PLAN.maxDrawdown}</div>
                  </div>
                </div>

                {/* Price scale visualization */}
                <div className="relative h-8 bg-[#0f1929] rounded-lg overflow-hidden flex">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(TRADING_PLAN.stopLossPrice / TRADING_PLAN.takeProfit2) * 100}%` }}
                    transition={{ delay: 1.4, duration: 0.6 }}
                    className="h-full bg-[rgba(239,68,68,0.3)] flex items-center justify-center"
                  >
                    <span className="text-[10px] text-[#ef4444] font-mono">止损</span>
                  </motion.div>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${((TRADING_PLAN.currentPrice - TRADING_PLAN.stopLossPrice) / TRADING_PLAN.takeProfit2) * 100}%` }}
                    transition={{ delay: 1.5, duration: 0.6 }}
                    className="h-full bg-[rgba(201,168,76,0.3)] flex items-center justify-center"
                  >
                    <span className="text-[10px] text-[#c9a84c] font-mono">入场区</span>
                  </motion.div>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${((TRADING_PLAN.takeProfit1 - TRADING_PLAN.currentPrice) / TRADING_PLAN.takeProfit2) * 100}%` }}
                    transition={{ delay: 1.6, duration: 0.6 }}
                    className="h-full bg-[rgba(34,197,94,0.3)] flex items-center justify-center"
                  >
                    <span className="text-[10px] text-[#22c55e] font-mono">目标1</span>
                  </motion.div>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${((TRADING_PLAN.takeProfit2 - TRADING_PLAN.takeProfit1) / TRADING_PLAN.takeProfit2) * 100}%` }}
                    transition={{ delay: 1.7, duration: 0.6 }}
                    className="h-full bg-[rgba(34,197,94,0.2)] flex items-center justify-center"
                  >
                    <span className="text-[10px] text-[#22c55e] font-mono">目标2</span>
                  </motion.div>
                </div>

                <div>
                  <div className="text-[11px] text-[#475569] mb-1">止损条件</div>
                  <div className="space-y-0.5">
                    {TRADING_PLAN.stopLossConditions.map((c, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[12px] text-[#94a3b8]">
                        <AlertTriangle size={12} className="text-[#ef4444] shrink-0" />
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Block 5: Position Management */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.4 }}
              className="py-4 hover:bg-[#0f1929] transition-colors px-2 -mx-2 rounded"
            >
              <div className="text-[12px] text-[#475569] mb-3 font-medium flex items-center gap-1.5">
                <BarChart3 size={14} className="text-[#06d7d7]" /> 持仓管理
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">建议持仓周期</div>
                  <div className="text-[14px] text-[#f1f5f9] font-medium">{TRADING_PLAN.holdPeriod}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">加仓条件</div>
                  <div className="text-[13px] text-[#22c55e]">{TRADING_PLAN.addConditions[0]}</div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">减仓条件</div>
                  <div className="space-y-0.5">
                    {TRADING_PLAN.reduceConditions.map((c, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[12px] text-[#94a3b8]">
                        <ChevronRight size={12} className="text-[#eab308] shrink-0" />
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-[#475569] mb-0.5">每日检查</div>
                  <div className="space-y-0.5">
                    {TRADING_PLAN.dailyCheck.map((c, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[12px] text-[#94a3b8]">
                        <CheckCircle2 size={12} className="text-[#06d7d7] shrink-0" />
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Block 6: AI Comment */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.5 }}
              className="py-4 px-2 -mx-2 rounded bg-[#0f1929] border-l-4 border-[#c9a84c]"
            >
              <div className="text-[14px] font-semibold text-[#c9a84c] mb-2 flex items-center gap-1.5">
                <Zap size={16} /> AI综合研判
              </div>
              <p className="text-[13px] text-[#94a3b8] leading-relaxed">
                {TRADING_PLAN.aiComment}
              </p>
              <div className="mt-3 pt-2 border-t border-dashed border-[rgba(148,163,184,0.1)] flex items-center gap-2">
                <Award size={14} className="text-[#c9a84c]" />
                <span className="text-[11px] text-[#475569]">AI交易智能体 v2.4.1 · {new Date().toLocaleString('zh-CN')}</span>
              </div>
            </motion.div>
          </div>
        </DataCard>
      </div>
    </div>
  );
}
