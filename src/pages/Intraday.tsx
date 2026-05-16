import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import {
  Pin,
  Edit3,
  Plus,
  Bell,
  TrendingUp,
  Clock,
  ChevronRight,
  Zap,
  AlertTriangle,
  Lightbulb,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import DataCard from '@/components/DataCard';
import {
  anchoredTargets,
  sectorFundFlows,
  sectorAlerts,
  leaderTiers,
  abnormalityTracker,
} from '@/data/mockData';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] } },
};

/* ─── Mini Sparkline SVG ─── */
function MiniSparkline({ data, positive }: { data: number[]; positive: boolean }) {
  const w = 80, h = 24;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} className="opacity-80">
      <polyline
        points={points}
        fill="none"
        stroke={positive ? '#ef4444' : '#22c55e'}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ─── Signal type helper ─── */
function getSignalClasses(type: string) {
  switch (type) {
    case 'strong':
      return 'text-[#ef4444] font-semibold';
    case 'normal':
      return 'text-[#c9a84c]';
    case 'observe':
      return 'text-[#94a3b8]';
    case 'pending':
      return 'text-[#475569]';
    default:
      return 'text-[#94a3b8]';
  }
}

/* ─── Treemap Chart Option ─── */
function useTreemapOption() {
  const data = sectorFundFlows.map((s) => ({
    name: s.name,
    value: Math.abs(s.netInflow) * 10,
    netInflow: s.netInflow,
    changePercent: s.changePercent,
    turnover: s.turnover,
    itemStyle: {
      color: s.netInflow > 0
        ? `rgba(239, 68, 68, ${Math.min(0.85, 0.25 + Math.abs(s.netInflow) / 80)})`
        : `rgba(34, 197, 94, ${Math.min(0.85, 0.25 + Math.abs(s.netInflow) / 50)})`,
    },
  }));

  return {
    tooltip: {
      backgroundColor: 'rgba(13,21,38,0.95)',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
      formatter: (params: Record<string, unknown>) => {
        const d = params?.data as Record<string, unknown>;
        return `<div style="font-weight:600">${d?.name}</div>
                <div>净流入: <span style="color:${(d?.netInflow as number) > 0 ? '#ef4444' : '#22c55e'}">${(d?.netInflow as number) > 0 ? '+' : ''}${d?.netInflow}亿</span></div>
                <div>成交额: ${d?.turnover}亿</div>
                <div>涨跌幅: <span style="color:${(d?.changePercent as number) > 0 ? '#ef4444' : '#22c55e'}">${(d?.changePercent as number) > 0 ? '+' : ''}${d?.changePercent}%</span></div>`;
      },
    },
    series: [{
      type: 'treemap',
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: (params: Record<string, unknown>) => {
          const d = params?.data as Record<string, unknown>;
          return `{name|${d?.name}}\n{val|${(d?.netInflow as number) > 0 ? '+' : ''}${d?.netInflow}亿}`;
        },
        rich: {
          name: { fontSize: 13, fontWeight: 600, color: '#f1f5f9', fontFamily: 'Noto Sans SC' },
          val: { fontSize: 11, color: '#94a3b8', fontFamily: 'JetBrains Mono', padding: [4, 0, 0, 0] },
        },
      },
      itemStyle: { borderColor: 'rgba(148,163,184,0.1)', borderWidth: 1, gapWidth: 2 },
      emphasis: {
        label: { fontSize: 14, fontWeight: 700 },
        itemStyle: { borderColor: '#c9a84c', borderWidth: 2 },
      },
      data,
    }],
  };
}

/* ─── Alert Icon ─── */
function AlertIcon({ type }: { type: '机会' | '风险' | '提示' }) {
  switch (type) {
    case '机会':
      return <Lightbulb size={14} className="text-[#c9a84c] shrink-0" />;
    case '风险':
      return <AlertTriangle size={14} className="text-[#ef4444] shrink-0" />;
    case '提示':
      return <Info size={14} className="text-[#3b82f6] shrink-0" />;
  }
}

/* ─── Time Period Reminders ─── */
const timePeriods = [
  { label: '集合竞价', time: '09:15-09:25', status: 'completed', desc: '观察隔夜单情绪' },
  { label: '开盘30分', time: '09:30-10:00', status: 'completed', desc: '确认主线方向' },
  { label: '盘中震荡', time: '10:00-14:30', status: 'active', desc: '龙头分歧介入' },
  { label: '尾盘', time: '14:30-15:00', status: 'pending', desc: '先手布局' },
];

/* ─── Main Component ─── */
export default function Intraday() {
  const [activeTheme, setActiveTheme] = useState(0);
  const [trackerFilter, setTrackerFilter] = useState('全部');
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragState = useRef({ startX: 0, scrollLeft: 0 });

  const treemapOption = useTreemapOption();
  const currentTier = leaderTiers[activeTheme];

  const trackerFilters = ['全部', '放量突破', '快速拉升', '大单异动', '尾盘异动'];
  const filteredTracker = trackerFilter === '全部'
    ? abnormalityTracker
    : abnormalityTracker.filter((a) => a.type === trackerFilter);

  /* Drag scroll handlers */
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    dragState.current = { startX: e.pageX - (scrollRef.current?.offsetLeft || 0), scrollLeft: scrollRef.current?.scrollLeft || 0 };
  }, []);
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !scrollRef.current) return;
    e.preventDefault();
    const x = e.pageX - (scrollRef.current.offsetLeft || 0);
    const walk = (x - dragState.current.startX) * 1.5;
    scrollRef.current.scrollLeft = dragState.current.scrollLeft - walk;
  }, [isDragging]);
  const handleMouseUp = useCallback(() => setIsDragging(false), []);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-4"
    >
      {/* ═══ Row 1: 锚定标的 + 资金流向 ═══ */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* ── 锚定标的 ── */}
        <DataCard
          delay={0}
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <Pin size={18} className="text-[#c9a84c]" />
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">锚定标的</h2>
                <span className="text-[11px] text-[#475569] ml-1 font-mono">{anchoredTargets.length}只</span>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1 px-2.5 py-1 text-[12px] text-[#94a3b8] hover:text-[#f1f5f9] bg-[#141e33] hover:bg-[#1a2744] rounded-md transition-colors">
                  <Edit3 size={12} /> 编辑列表
                </button>
                <button className="flex items-center gap-1 px-2.5 py-1 text-[12px] text-[#060b14] bg-[#c9a84c] hover:bg-[#e0c878] rounded-md transition-colors">
                  <Plus size={12} /> 添加
                </button>
              </div>
            </div>
          }
          className="min-h-[420px]"
        >
          {/* Table Header */}
          <div className="grid grid-cols-[80px_80px_70px_60px_90px_50px_110px_80px] gap-1 px-2 pb-2 text-[11px] text-[#475569] font-medium border-b border-[rgba(148,163,184,0.1)]">
            <span>代码</span>
            <span>名称</span>
            <span className="text-right">现价</span>
            <span className="text-right">涨跌</span>
            <span className="text-right">涨速</span>
            <span className="text-right">量比</span>
            <span>信号</span>
            <span className="text-right">走势</span>
          </div>
          {/* Table Rows */}
          <div className="space-y-0.5 mt-1">
            {anchoredTargets.map((stock, i) => {
              const isUp = stock.change > 0;
              const isLimitUp = stock.change >= 9.5;
              const isLimitDown = stock.change <= -9.5;
              return (
                <motion.div
                  key={stock.code}
                  variants={itemVariants}
                  custom={i}
                  className={cn(
                    'grid grid-cols-[80px_80px_70px_60px_90px_50px_110px_80px] gap-1 px-2 py-1.5 rounded-md cursor-pointer transition-all duration-200 group',
                    isLimitUp && 'bg-[rgba(239,68,68,0.08)]',
                    isLimitDown && 'bg-[rgba(34,197,94,0.08)]',
                    !isLimitUp && !isLimitDown && 'hover:bg-[#141e33]'
                  )}
                >
                  <span className="text-[13px] font-mono text-[#f1f5f9]">{stock.code}</span>
                  <span className="text-[13px] text-[#f1f5f9] truncate">{stock.name}</span>
                  <span className="text-[13px] font-mono text-right text-[#f1f5f9]">{stock.price.toFixed(2)}</span>
                  <span className={cn('text-[13px] font-mono text-right', isUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                    {isUp ? '+' : ''}{stock.change}%
                  </span>
                  <span className={cn('text-[12px] font-mono text-right', isUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                    {stock.speed}
                  </span>
                  <span className="text-[12px] font-mono text-right text-[#94a3b8]">{stock.volumeRatio.toFixed(1)}</span>
                  <span className={cn('text-[12px]', getSignalClasses(stock.signalType))}>
                    {stock.signal}
                  </span>
                  <div className="flex justify-end">
                    <MiniSparkline data={stock.sparkline} positive={isUp} />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </DataCard>

        {/* ── 资金流向 Treemap ── */}
        <DataCard
          delay={100}
          header={
            <div className="flex items-center justify-between w-full">
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">板块资金流向</h2>
              <div className="flex items-center gap-3 text-[11px]">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[rgba(239,68,68,0.5)]" />流入</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[rgba(34,197,94,0.5)]" />流出</span>
              </div>
            </div>
          }
          className="min-h-[420px]"
        >
          <div className="w-full h-[340px]">
            <ReactECharts option={treemapOption} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} />
          </div>
        </DataCard>
      </div>

      {/* ═══ Row 2: 板块预警 + 龙头梯队 ═══ */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* ── 板块异动预警 ── */}
        <DataCard
          delay={200}
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">板块异动预警</h2>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ef4444] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#ef4444]" />
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Bell size={16} className="text-[#ef4444]" />
                <span className="text-[12px] px-2 py-0.5 bg-[rgba(239,68,68,0.15)] text-[#ef4444] rounded-full">{sectorAlerts.length}条新预警</span>
              </div>
            </div>
          }
          className="min-h-[340px]"
        >
          <div className="space-y-0">
            {sectorAlerts.map((alert, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                className="flex gap-3 px-2 py-3 border-b border-[rgba(148,163,184,0.08)] hover:bg-[#141e33] rounded-md transition-colors cursor-pointer group"
              >
                <div className="flex flex-col items-center gap-1 pt-0.5">
                  <AlertIcon type={alert.type} />
                  <span className="text-[11px] text-[#475569] font-mono">{alert.time}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={cn(
                      'text-[12px] px-1.5 py-0.5 rounded font-medium',
                      alert.type === '机会' && 'bg-[rgba(201,168,76,0.15)] text-[#c9a84c]',
                      alert.type === '风险' && 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]',
                      alert.type === '提示' && 'bg-[rgba(59,130,246,0.15)] text-[#3b82f6]',
                    )}>
                      {alert.type}
                    </span>
                    <span className="text-[13px] font-medium text-[#f1f5f9]">{alert.sector}</span>
                  </div>
                  <p className="text-[12px] text-[#94a3b8] leading-relaxed">{alert.content}</p>
                  <p className="text-[11px] text-[#475569] font-mono mt-0.5">{alert.relatedStocks}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </DataCard>

        {/* ── 龙头梯队 ── */}
        <DataCard
          delay={300}
          header={
            <div className="flex items-center justify-between w-full">
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">龙头梯队</h2>
              <select
                value={activeTheme}
                onChange={(e) => setActiveTheme(Number(e.target.value))}
                className="text-[12px] bg-[#141e33] text-[#f1f5f9] border border-[rgba(148,163,184,0.15)] rounded-md px-2 py-1 outline-none focus:border-[#c9a84c]"
              >
                {leaderTiers.map((t, i) => (
                  <option key={i} value={i}>{t.theme}</option>
                ))}
              </select>
            </div>
          }
          className="min-h-[340px]"
        >
          <motion.div
            key={activeTheme}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-2"
          >
            {/* 总龙头 */}
            <div className="relative bg-[rgba(201,168,76,0.08)] border border-[rgba(201,168,76,0.3)] rounded-lg p-3">
              <div className="absolute -top-px left-4 right-4 h-[2px] bg-gradient-to-r from-transparent via-[#c9a84c] to-transparent" />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap size={16} className="text-[#c9a84c]" />
                  <span className="text-[16px] font-bold text-[#c9a84c]">{currentTier.topLeader.name}</span>
                  <span className="text-[11px] text-[#475569] font-mono">{currentTier.topLeader.code}</span>
                </div>
                <span className="text-[20px] font-bold text-[#ef4444] font-mono">{currentTier.topLeader.boards}连板</span>
              </div>
              <div className="flex items-center gap-4 mt-2 text-[11px] text-[#94a3b8]">
                <span>封单: <span className="text-[#f1f5f9] font-mono">{currentTier.topLeader.sealAmount}</span></span>
                <span>涨停: <span className="text-[#f1f5f9] font-mono">{currentTier.topLeader.limitUpTime}</span></span>
              </div>
            </div>

            {/* 连接线 */}
            <div className="flex justify-center">
              <div className="w-px h-4 border-l-2 border-dashed border-[rgba(148,163,184,0.2)]" />
            </div>

            {/* 龙二/龙三 */}
            <div className="grid grid-cols-2 gap-2">
              {currentTier.secondTier.map((s, i) => (
                <div key={i} className="bg-[rgba(59,130,246,0.06)] border border-[rgba(59,130,246,0.2)] rounded-lg p-2.5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-[10px] text-[#3b82f6] font-mono">#{i + 2}</span>
                    <span className="text-[13px] font-medium text-[#f1f5f9]">{s.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-[#475569] font-mono">{s.code}</span>
                    <span className="text-[14px] font-semibold text-[#ef4444] font-mono">{s.boards}连板</span>
                  </div>
                  <div className="text-[10px] text-[#475569] mt-1">封单: <span className="font-mono">{s.sealAmount}</span></div>
                </div>
              ))}
            </div>

            {/* 连接线 */}
            <div className="flex justify-center">
              <div className="w-px h-4 border-l-2 border-dashed border-[rgba(148,163,184,0.2)]" />
            </div>

            {/* 中位股 */}
            <div className="grid grid-cols-3 gap-2">
              {currentTier.midTier.map((s, i) => (
                <div key={i} className="bg-[#141e33] rounded-lg p-2 text-center">
                  <span className="text-[12px] text-[#94a3b8]">{s.name}</span>
                  <div className="text-[12px] text-[#ef4444] font-mono mt-0.5">{s.boards}连板</div>
                </div>
              ))}
            </div>

            {/* 连接线 */}
            <div className="flex justify-center">
              <div className="w-px h-4 border-l-2 border-dashed border-[rgba(148,163,184,0.2)]" />
            </div>

            {/* 首板 */}
            <div className="flex flex-wrap gap-1.5 items-center">
              {currentTier.firstBoard.map((s, i) => (
                <span key={i} className="text-[11px] px-2 py-0.5 bg-[#0f1929] text-[#475569] rounded-full border border-[rgba(148,163,184,0.08)]">
                  {s.name}
                </span>
              ))}
              <span className="text-[11px] text-[#c9a84c] font-mono">+{currentTier.firstBoardCount}首板</span>
            </div>
          </motion.div>
        </DataCard>
      </div>

      {/* ═══ Row 3: 分时段提醒 + 资金30分钟总结 ═══ */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* 分时段提醒 */}
        <DataCard
          delay={350}
          header={
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-[#06d7d7]" />
              <h2 className="text-[16px] font-semibold text-[#f1f5f9]">分时段提醒</h2>
            </div>
          }
          className="xl:col-span-1"
        >
          <div className="space-y-2">
            {timePeriods.map((p, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.08 }}
                className={cn(
                  'flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-200',
                  p.status === 'active' && 'bg-[rgba(201,168,76,0.06)] border-[rgba(201,168,76,0.25)]',
                  p.status === 'completed' && 'bg-transparent border-[rgba(148,163,184,0.06)] opacity-60',
                  p.status === 'pending' && 'bg-transparent border-[rgba(148,163,184,0.08)]',
                )}
              >
                <div className={cn(
                  'w-2 h-2 rounded-full shrink-0',
                  p.status === 'completed' && 'bg-[#22c55e]',
                  p.status === 'active' && 'bg-[#c9a84c] animate-pulse',
                  p.status === 'pending' && 'bg-[#475569]',
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className={cn('text-[13px] font-medium', p.status === 'active' ? 'text-[#c9a84c]' : 'text-[#94a3b8]')}>
                      {p.label}
                    </span>
                    <span className="text-[11px] text-[#475569] font-mono">{p.time}</span>
                  </div>
                  <p className="text-[11px] text-[#475569] mt-0.5">{p.desc}</p>
                </div>
                {p.status === 'completed' && <ChevronRight size={14} className="text-[#22c55e]" />}
                {p.status === 'active' && <div className="w-1.5 h-1.5 rounded-full bg-[#c9a84c] animate-pulse" />}
              </motion.div>
            ))}
          </div>
        </DataCard>

        {/* 资金30分钟总结 */}
        <DataCard
          delay={400}
          header={
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-[#c9a84c]" />
              <h2 className="text-[16px] font-semibold text-[#f1f5f9]">资金30分钟总结</h2>
              <span className="text-[11px] text-[#475569] font-mono">14:00-14:30</span>
            </div>
          }
          className="xl:col-span-2"
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: '主线流入', value: '+87.3亿', color: '#ef4444', icon: TrendingUp },
              { label: '北向资金', value: '+23.5亿', color: '#c9a84c', icon: TrendingUp },
              { label: '游资活跃', value: '156笔', color: '#8b5cf6', icon: Zap },
              { label: '板块轮动', value: 'AI→新能源', color: '#06d7d7', icon: TrendingUp },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.45 + i * 0.06 }}
                className="bg-[#141e33] rounded-lg p-3 text-center border border-[rgba(148,163,184,0.06)]"
              >
                <div className="flex items-center justify-center gap-1 mb-1.5">
                  <item.icon size={12} style={{ color: item.color }} />
                  <span className="text-[11px] text-[#475569]">{item.label}</span>
                </div>
                <span className="text-[16px] font-bold font-mono" style={{ color: item.color }}>{item.value}</span>
              </motion.div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div className="bg-[rgba(239,68,68,0.06)] rounded-md p-2">
              <div className="text-[11px] text-[#475569]">上涨家数</div>
              <div className="text-[18px] font-bold text-[#ef4444] font-mono mt-1">3,248</div>
            </div>
            <div className="bg-[rgba(34,197,94,0.06)] rounded-md p-2">
              <div className="text-[11px] text-[#475569]">下跌家数</div>
              <div className="text-[18px] font-bold text-[#22c55e] font-mono mt-1">1,652</div>
            </div>
            <div className="bg-[rgba(201,168,76,0.06)] rounded-md p-2">
              <div className="text-[11px] text-[#475569]">涨停</div>
              <div className="text-[18px] font-bold text-[#c9a84c] font-mono mt-1">68</div>
            </div>
          </div>
        </DataCard>
      </div>

      {/* ═══ Row 4: 异动追踪清单 (Full Width) ═══ */}
      <DataCard
        delay={500}
        header={
          <div className="flex items-center justify-between w-full flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-[#c9a84c]" />
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">实时异动追踪</h2>
            </div>
            <div className="flex items-center gap-1 bg-[#141e33] rounded-lg p-0.5">
              {trackerFilters.map((f) => (
                <button
                  key={f}
                  onClick={() => setTrackerFilter(f)}
                  className={cn(
                    'px-2.5 py-1 text-[11px] rounded-md transition-all duration-200',
                    trackerFilter === f
                      ? 'bg-[#c9a84c] text-[#060b14] font-medium'
                      : 'text-[#94a3b8] hover:text-[#f1f5f9]'
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        }
        className="min-h-[200px]"
      >
        <div
          ref={scrollRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={cn('flex gap-3 overflow-x-auto pb-2', isDragging && 'cursor-grabbing')}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {filteredTracker.map((item, i) => (
            <motion.div
              key={`${item.code}-${i}`}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.06, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              className="shrink-0 w-[240px] bg-[#141e33] rounded-lg p-3 border border-[rgba(148,163,184,0.08)] hover:border-[rgba(201,168,76,0.3)] hover:-translate-y-1 hover:shadow-elevated transition-all duration-200 cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] text-[#06d7d7] font-mono">{item.time}</span>
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded-full text-white font-medium"
                  style={{ backgroundColor: item.typeColor }}
                >
                  {item.type}
                </span>
              </div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[13px] font-mono text-[#f1f5f9]">{item.code}</span>
                <span className="text-[13px] text-[#f1f5f9]">{item.name}</span>
              </div>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-[15px] font-bold text-[#f1f5f9] font-mono">{item.price.toFixed(2)}</span>
                <span className={cn(
                  'text-[12px] font-mono px-1.5 py-0.5 rounded',
                  item.change > 0 ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]'
                )}>
                  {item.change > 0 ? '+' : ''}{item.change}%
                </span>
              </div>
              <div className="text-[11px] text-[#475569] font-mono mb-1.5">量比: {item.volumeRatio}x</div>
              <p className="text-[11px] text-[#475569] leading-relaxed border-t border-[rgba(148,163,184,0.06)] pt-1.5">
                {item.aiComment}
              </p>
            </motion.div>
          ))}
        </div>
      </DataCard>
    </motion.div>
  );
}
