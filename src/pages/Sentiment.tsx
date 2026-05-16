import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import {
  Activity,
  Zap,
  ChevronDown,
  ChevronUp,
  ArrowRight,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import { cn } from '@/lib/utils';

/* ─── Types ─── */
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

/* ─── Constants ─── */
const PHASES: SentimentPhase[] = [
  { name: '混沌期', color: '#6b7280', order: 1 },
  { name: '启动期', color: '#3b82f6', order: 2 },
  { name: '发酵期', color: '#06d7d7', order: 3 },
  { name: '高潮期', color: '#c9a84c', order: 4 },
  { name: '分歧期', color: '#f97316', order: 5 },
  { name: '退潮期', color: '#ef4444', order: 6 },
];

const CURRENT_PHASE_INDEX = 2; // 发酵期 (0-based)
const CURRENT_PHASE = PHASES[CURRENT_PHASE_INDEX];
const TEMPERATURE = 72;

const INDICATORS: Indicator[] = [
  { name: '涨停家数比', value: '12.3%', status: 'good', desc: '涨停数/总交易数', sparkline: [10, 12, 11, 13, 12.3] },
  { name: '连板高度', value: '6板', status: 'good', desc: '最高连板数', sparkline: [4, 5, 5, 6, 6] },
  { name: '炸板率', value: '18.5%', status: 'neutral', desc: '涨停后开板比例', sparkline: [22, 20, 19, 18, 18.5] },
  { name: '跌停家数', value: '3家', status: 'good', desc: '跌停数量', sparkline: [5, 4, 3, 3, 3] },
  { name: '涨跌中位数', value: '+1.2%', status: 'good', desc: '涨跌幅中位数', sparkline: [0.8, 1.0, 0.9, 1.1, 1.2] },
  { name: '连板晋级率', value: '62%', status: 'neutral', desc: '首板晋级二板比例', sparkline: [55, 58, 60, 61, 62] },
  { name: '昨涨停今表现', value: '+3.8%', status: 'good', desc: '昨日涨停股今日平均涨跌', sparkline: [2, 2.5, 3, 3.5, 3.8] },
  { name: '高标溢价', value: '+2.1%', status: 'good', desc: '高位股溢价情况', sparkline: [1, 1.5, 1.8, 2, 2.1] },
  { name: '题材集中度', value: '78%', status: 'neutral', desc: '资金流向TOP3题材占比', sparkline: [70, 72, 74, 76, 78] },
  { name: '量能维持率', value: '95%', status: 'good', desc: '今日成交额/5日均额', sparkline: [88, 90, 92, 93, 95] },
  { name: '封单强度', value: '强', status: 'good', desc: '涨停封单综合评估', sparkline: [60, 70, 75, 80, 85] },
  { name: '指数联动', value: '一致', status: 'good', desc: '三大指数走势一致性', sparkline: [70, 75, 80, 85, 90] },
  { name: '北向资金', value: '+23.5亿', status: 'good', desc: '北向资金流向', sparkline: [15, 18, 20, 22, 23.5] },
  { name: '恐慌指数', value: '12', status: 'good', desc: 'VIX风格恐慌指标', sparkline: [20, 18, 15, 14, 12] },
];

const THEME_DATA: ThemeItem[] = [
  { rank: 1, name: 'AI算力', heat: 92, limitUp: 12, leader: '英维克', leaderCode: '002837', phase: '高潮', phaseColor: '#c9a84c' },
  { rank: 2, name: 'CPO光模块', heat: 85, limitUp: 8, leader: '中际旭创', leaderCode: '300308', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 3, name: '机器人', heat: 78, limitUp: 6, leader: '埃斯顿', leaderCode: '002747', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 4, name: '半导体', heat: 65, limitUp: 5, leader: '中芯国际', leaderCode: '688981', phase: '启动', phaseColor: '#3b82f6' },
  { rank: 5, name: '新能源车', heat: 52, limitUp: 3, leader: '比亚迪', leaderCode: '002594', phase: '分歧', phaseColor: '#f97316' },
  { rank: 6, name: '光伏储能', heat: 45, limitUp: 2, leader: '阳光电源', leaderCode: '300274', phase: '退潮', phaseColor: '#ef4444' },
  { rank: 7, name: '创新药', heat: 38, limitUp: 2, leader: '恒瑞医药', leaderCode: '600276', phase: '混沌', phaseColor: '#6b7280' },
  { rank: 8, name: '军工', heat: 30, limitUp: 1, leader: '中航沈飞', leaderCode: '600760', phase: '混沌', phaseColor: '#6b7280' },
];

const POSITION_STRATEGY: Record<string, { position: string; range: string; tactics: { text: string; color: string }[] }> = {
  '混沌期': { position: '20%', range: '10%-30%', tactics: [{ text: '空仓观望，等待方向', color: 'red' }, { text: '小仓位试错新题材', color: 'yellow' }, { text: '不追高，不抄底', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '启动期': { position: '40%', range: '30%-50%', tactics: [{ text: '低吸为主，分批建仓', color: 'green' }, { text: '关注首板机会', color: 'green' }, { text: '单票不超过20%', color: 'yellow' }, { text: '设好止损线', color: 'red' }] },
  '发酵期': { position: '60%', range: '50%-70%', tactics: [{ text: '积极做多，持股为主', color: 'green' }, { text: '关注龙头分歧转一致', color: 'green' }, { text: '避免后排跟风股', color: 'yellow' }, { text: '控制回撤-3%', color: 'red' }] },
  '高潮期': { position: '30%', range: '20%-40%', tactics: [{ text: '不追高，以低吸为主', color: 'yellow' }, { text: '控制回撤，单票不超20%', color: 'yellow' }, { text: '关注分歧转一致机会', color: 'green' }, { text: '设定-3%强制止损线', color: 'red' }] },
  '分歧期': { position: '30%', range: '20%-40%', tactics: [{ text: '减仓为主，锁定利润', color: 'yellow' }, { text: '不参与高位博弈', color: 'red' }, { text: '等待情绪明朗', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '退潮期': { position: '10%', range: '0%-20%', tactics: [{ text: '空仓或极小仓位', color: 'red' }, { text: '不参与任何接力', color: 'red' }, { text: '等待新周期启动', color: 'yellow' }, { text: '清仓观望', color: 'red' }] },
};

const HISTORY_DATA = [
  { date: '01-06', score: 35, phase: '混沌期' },
  { date: '01-07', score: 42, phase: '启动期' },
  { date: '01-08', score: 55, phase: '启动期' },
  { date: '01-09', score: 62, phase: '发酵期' },
  { date: '01-10', score: 58, phase: '发酵期' },
  { date: '01-13', score: 48, phase: '分歧期' },
  { date: '01-14', score: 40, phase: '混沌期' },
  { date: '01-15', score: 52, phase: '启动期' },
  { date: '01-16', score: 65, phase: '发酵期' },
  { date: '01-17', score: 72, phase: '发酵期' },
];

/* ─── Helpers ─── */
const statusColor = (status: string) => {
  switch (status) {
    case 'good': return 'bg-[#22c55e]';
    case 'neutral': return 'bg-[#eab308]';
    case 'warning': return 'bg-[#ef4444]';
    default: return 'bg-[#6b7280]';
  }
};

const statusDotColor = (status: string) => {
  switch (status) {
    case 'good': return '#22c55e';
    case 'neutral': return '#eab308';
    case 'warning': return '#ef4444';
    default: return '#6b7280';
  }
};

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

/* ─── Main Page ─── */
export default function Sentiment() {
  const [expandedIndicators, setExpandedIndicators] = useState(false);
  const [activeTimeRange, setActiveTimeRange] = useState<'7日' | '14日' | '30日'>('7日');
  const [showRefLines, setShowRefLines] = useState(true);

  const currentStrategy = POSITION_STRATEGY[CURRENT_PHASE.name];

  /* ─── ECharts: Sentiment Cycle Ring ─── */
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
              name: {
                fontSize: 12,
                color: '#94a3b8',
                fontFamily: 'Noto Sans SC',
              },
            },
          },
          labelLine: {
            length: 12,
            length2: 8,
            lineStyle: { color: 'rgba(148,163,184,0.2)' },
          },
          emphasis: {
            scaleSize: 8,
            itemStyle: {
              shadowBlur: 25,
            },
          },
          data,
          animationType: 'scale' as const,
          animationEasing: 'elasticOut' as const,
          animationDelay: (idx: number) => idx * 100,
        },
        // Inner decorative ring
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
          style: {
            text: `${CURRENT_PHASE.order}/6`,
            fill: '#c9a84c',
            fontSize: 36,
            fontWeight: 'bold',
            fontFamily: 'JetBrains Mono',
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          left: 'center',
          top: '48%',
          style: {
            text: CURRENT_PHASE.name,
            fill: CURRENT_PHASE.color,
            fontSize: 18,
            fontWeight: '600',
            fontFamily: 'Noto Sans SC',
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          left: 'center',
          top: '56%',
          style: {
            text: `温度 ${TEMPERATURE}°C`,
            fill: TEMPERATURE > 80 ? '#ef4444' : TEMPERATURE > 60 ? '#c9a84c' : '#06d7d7',
            fontSize: 13,
            fontFamily: 'JetBrains Mono',
            textAlign: 'center',
          },
        },
      ],
    };
  }, []);

  /* ─── ECharts: History Area Line ─── */
  const historyOption = useMemo(() => {
    const xData = HISTORY_DATA.map(d => d.date);
    const yData = HISTORY_DATA.map(d => d.score);

    return {
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: Array<{ axisValue: string; value: number; dataIndex: number }>) => {
          const idx = params[0].dataIndex;
          const item = HISTORY_DATA[idx];
          return `<div style="font-weight:bold;margin-bottom:4px">${item.date}</div>
            <div style="color:#c9a84c">综合情绪: ${item.score}分</div>
            <div style="color:${PHASES.find(p => p.name === item.phase)?.color};font-size:12px">阶段: ${item.phase}</div>`;
        },
      },
      grid: { top: 30, right: 20, bottom: 30, left: 45 },
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
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(201,168,76,0.25)' },
              { offset: 1, color: 'rgba(201,168,76,0.02)' },
            ]),
          },
          animationDuration: 1500,
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
  }, [showRefLines]);

  /* ─── ECharts: Theme Treemap ─── */
  const treemapOption = useMemo(() => {
    return {
      tooltip: {
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: { name: string; value: number; data: { limitUp?: number; leader?: string; leaderCode?: string; phase?: string } }) => {
          const d = params.data as { limitUp?: number; leader?: string; leaderCode?: string; phase?: string };
          return `<div style="font-weight:bold;margin-bottom:4px">${params.name}</div>
            <div style="color:#c9a84c">热度: ${params.value}</div>
            <div style="color:#ef4444;font-size:12px">涨停: ${d.limitUp || 0}家</div>
            <div style="color:#94a3b8;font-size:12px">龙头: ${d.leader || '-'} (${d.leaderCode || ''})</div>`;
        },
      },
      series: [
        {
          type: 'treemap',
          width: '100%',
          height: '90%',
          top: '5%',
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: {
            show: true,
            formatter: '{name|{name}}\n{val|{c}}',
            rich: {
              name: { fontSize: 13, fontWeight: 'bold', color: '#f1f5f9', fontFamily: 'Noto Sans SC', lineHeight: 20 },
              val: { fontSize: 16, fontWeight: 'bold', color: '#c9a84c', fontFamily: 'JetBrains Mono', lineHeight: 22 },
            },
          },
          itemStyle: {
            borderColor: '#0d1526',
            borderWidth: 3,
            gapWidth: 3,
            borderRadius: 6,
          },
          levels: [
            {
              itemStyle: {
                borderColor: '#0d1526',
                borderWidth: 3,
                gapWidth: 3,
              },
            },
          ],
          data: THEME_DATA.map(t => ({
            name: t.name,
            value: t.heat,
            limitUp: t.limitUp,
            leader: t.leader,
            leaderCode: t.leaderCode,
            phase: t.phase,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                { offset: 0, color: `${t.phaseColor}44` },
                { offset: 1, color: `${t.phaseColor}22` },
              ]),
            },
          })),
          animationDuration: 800,
          animationEasing: 'cubicOut' as const,
          animationDelay: (idx: number) => idx * 80,
        },
      ],
    };
  }, []);

  return (
    <div className="space-y-4">
      {/* ── Row 1: Cycle Ring + 14 Indicators ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Sentiment Cycle Ring */}
        <div className="col-span-12 lg:col-span-5">
          <DataCard delay={200} header={
            <>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c9a84c] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#c9a84c]" />
                </span>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">情绪周期</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-[#475569]">当前阶段</span>
                <span className="text-[16px] font-semibold" style={{ color: CURRENT_PHASE.color }}>{CURRENT_PHASE.name}</span>
              </div>
            </>
          }>
            <ReactECharts option={cycleOption} style={{ height: 320 }} />
            {/* Indicator row */}
            <div className="grid grid-cols-4 gap-2 mt-2 pt-3 border-t border-[rgba(148,163,184,0.1)]">
              {[
                { label: '昨日阶段', value: '启动期', color: '#3b82f6' },
                { label: '阶段持续', value: '第2天', color: '#c9a84c' },
                { label: '历史平均', value: '2.1天', color: '#94a3b8' },
                { label: '明日概率', value: '高潮65%', color: '#c9a84c' },
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
        </div>

        {/* 14 Indicators */}
        <div className="col-span-12 lg:col-span-7">
          <DataCard
            delay={250}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">情绪指标全景</h2>
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
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
              {INDICATORS.map((ind, i) => (
                <motion.div
                  key={ind.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.04, duration: 0.3 }}
                  className="group relative p-2.5 rounded-lg bg-[#0f1929] hover:bg-[#141e33] transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={cn('w-2 h-2 rounded-full', statusColor(ind.status))} />
                    <span className="text-[11px] text-[#475569] group-hover:text-[#f1f5f9] transition-colors truncate">{ind.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[14px] font-semibold font-mono text-[#f1f5f9]">{ind.value}</span>
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
          </DataCard>
        </div>
      </div>

      {/* ── Row 2: History Chart + Theme Heat ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* History Chart */}
        <div className="col-span-12 lg:col-span-7">
          <DataCard
            delay={400}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">近10日情绪走势</h2>
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
            <ReactECharts option={historyOption} style={{ height: 260 }} />
          </DataCard>
        </div>

        {/* Theme Heat Treemap */}
        <div className="col-span-12 lg:col-span-5">
          <DataCard
            delay={500}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">题材热度</h2>
                <button className="flex items-center gap-1 text-[12px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors">
                  更多 <ArrowRight size={14} />
                </button>
              </>
            }
          >
            <ReactECharts option={treemapOption} style={{ height: 260 }} />
          </DataCard>
        </div>
      </div>

      {/* ── Row 3: Next Day Forecast + Position Strategy ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Next Day Forecast */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard
            delay={600}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">次日大盘趋势预判</h2>
                <div className="flex items-center gap-1 text-[12px] text-[#06d7d7]">
                  <Activity size={13} />
                  <span>AI模型置信度: 78%</span>
                </div>
              </>
            }
          >
            <div className="space-y-4">
              {/* Predicted phase */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9, duration: 0.5 }}
              >
                <div className="text-[12px] text-[#475569] mb-2">预测阶段</div>
                <div className="flex items-center gap-3">
                  <Zap size={24} className="text-[#c9a84c]" />
                  <span className="text-[28px] font-bold text-[#c9a84c]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
                    高潮期
                  </span>
                  <span className="text-[14px] text-[#94a3b8]">概率 65%</span>
                </div>
              </motion.div>

              {/* Probability bars */}
              <div className="space-y-2">
                {[
                  { label: '高潮期', prob: 65, color: '#c9a84c' },
                  { label: '分歧期', prob: 25, color: '#f97316' },
                  { label: '退潮期', prob: 10, color: '#ef4444' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.0 + i * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <span className="text-[12px] text-[#94a3b8] w-12 text-right">{item.label}</span>
                    <div className="flex-1 h-3 bg-[#0f1929] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.prob}%` }}
                        transition={{ delay: 1.1 + i * 0.15, duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                    </div>
                    <span className="text-[12px] font-mono w-10" style={{ color: item.color }}>{item.prob}%</span>
                  </motion.div>
                ))}
              </div>

              {/* Forecast basis */}
              <div className="pt-3 border-t border-[rgba(148,163,184,0.1)] space-y-1.5">
                <div className="text-[12px] text-[#475569] mb-2">预判依据</div>
                {[
                  '发酵期已持续2天，历史平均2.1天，明日或进入高潮',
                  '今日炸板率18.5%，处于可控范围',
                  '北向资金净流入+23.5亿，增量资金入场',
                  'AI算力题材热度持续升温，龙头英维克强势',
                ].map((reason, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.3 + i * 0.1 }}
                    className="flex items-start gap-2 text-[12px] text-[#94a3b8]"
                  >
                    <span className="text-[#c9a84c] mt-0.5">•</span>
                    <span>{reason}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </DataCard>
        </div>

        {/* Position Strategy */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard delay={700} header={<h2 className="text-[18px] font-semibold text-[#f1f5f9]">仓位策略建议</h2>}>
            <div className="space-y-4">
              {/* Position gauge */}
              <div className="flex items-center gap-6">
                <div className="flex-1">
                  <div className="flex items-baseline gap-2 mb-1">
                    <motion.span
                      className="text-[36px] font-bold text-[#c9a84c] font-mono"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1.0 }}
                    >
                      {currentStrategy.position}
                    </motion.span>
                    <span className="text-[12px] text-[#475569]">建议仓位</span>
                  </div>
                  <div className="text-[12px] text-[#94a3b8] mb-3">
                    建议区间: {currentStrategy.range}
                  </div>
                  {/* Mini gauge bar */}
                  <div className="h-3 bg-[#0f1929] rounded-full overflow-hidden relative">
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
                    <div className="absolute top-0 left-[30%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                    <div className="absolute top-0 left-[60%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                    <div className="absolute top-0 left-[85%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-[#475569]">0%</span>
                    <span className="text-[10px] text-[#475569]">50%</span>
                    <span className="text-[10px] text-[#475569]">100%</span>
                  </div>
                </div>

                {/* Phase-position matching table */}
                <div className="w-[200px] shrink-0">
                  <div className="text-[11px] text-[#475569] mb-2">情绪-仓位匹配表</div>
                  <div className="space-y-1">
                    {PHASES.map((phase, i) => {
                      const strategy = POSITION_STRATEGY[phase.name];
                      const isCurrent = i === CURRENT_PHASE_INDEX;
                      return (
                        <motion.div
                          key={phase.name}
                          initial={{ opacity: 0, x: 10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.9 + i * 0.06 }}
                          className={cn(
                            'flex items-center justify-between px-2 py-1 rounded text-[11px]',
                            isCurrent ? 'bg-[#141e33] border border-[rgba(201,168,76,0.3)]' : ''
                          )}
                        >
                          <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: phase.color }} />
                            <span className={isCurrent ? 'text-[#f1f5f9] font-medium' : 'text-[#475569]'}>{phase.name}</span>
                          </div>
                          <span className="font-mono" style={{ color: isCurrent ? '#c9a84c' : '#475569' }}>{strategy.position}</span>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Tactics list */}
              <div className="pt-3 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-[12px] text-[#475569] mb-2">策略要点</div>
                <div className="space-y-2">
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
                      <span className="text-[13px] text-[#94a3b8]">{tactic.text}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>
    </div>
  );
}
