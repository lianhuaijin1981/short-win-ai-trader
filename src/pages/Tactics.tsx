import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Target,
  Search,
  ChevronDown,
  ChevronRight,
  Zap,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  ArrowUpDown,
  BarChart3,
  Layers,
  GitBranch,
  GitCommit,
  GitMerge,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import DataCard from '@/components/DataCard';
import {
  tacticCategories,
  tacticDetails,
  screeningResults,
  resonanceItems,
  tacticAdaptation,
} from '@/data/mockData';

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] } },
};

/* ─── Score Ring SVG ─── */
function ScoreRing({ score, size = 64, stroke = 5 }: { score: number; size?: number; stroke?: number }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 90 ? '#c9a84c' : score >= 80 ? '#3b82f6' : score >= 70 ? '#06d7d7' : '#475569';

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#141e33" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number], delay: 0.3 }}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[14px] font-bold font-mono" style={{ color }}>{score}</span>
      </div>
    </div>
  );
}

/* ─── Mini Bar Chart for Win History ─── */
function MiniWinBar({ data }: { data: number[] }) {
  return (
    <div className="flex items-end gap-[2px] h-5">
      {data.map((v, i) => (
        <motion.div
          key={i}
          initial={{ height: 0 }}
          animate={{ height: `${Math.max(4, v * 16)}px` }}
          transition={{ delay: i * 0.05 + 0.2, duration: 0.3 }}
          className={cn('w-[6px] rounded-sm', v === 1 ? 'bg-[#ef4444]' : 'bg-[#22c55e]')}
        />
      ))}
    </div>
  );
}

/* ─── Filter Steps Visual ─── */
const filterSteps = [
  { label: '硬性条件', icon: Filter, desc: '流通市值>20亿', status: 'pass' as const },
  { label: '形态识别', icon: GitBranch, desc: '战法规则匹配', status: 'pass' as const },
  { label: '环境适配', icon: GitCommit, desc: '情绪周期校验', status: 'pass' as const },
  { label: '持续性判定', icon: GitMerge, desc: '量能持续性检查', status: 'checking' as const },
];

export default function Tactics() {
  const [selectedTactic, setSelectedTactic] = useState('筹码峰突破');
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['量能战法', '形态战法']);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'匹配度' | '涨跌幅' | '成交额' | '连板数'>('匹配度');
  const [showLimitUpOnly, setShowLimitUpOnly] = useState(false);
  const [resonanceFilter, setResonanceFilter] = useState<'全部' | '2战法' | '3战法+'>('全部');

  const toggleCategory = (name: string) => {
    setExpandedCategories((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const detail = tacticDetails[selectedTactic] || tacticDetails['筹码峰突破'];

  /* Filtered tactics for search */
  const filteredCategories = useMemo(() => {
    if (!searchQuery) return tacticCategories;
    const q = searchQuery.toLowerCase();
    return tacticCategories
      .map((cat) => ({
        ...cat,
        tactics: cat.tactics.filter((t) => t.name.toLowerCase().includes(q)),
      }))
      .filter((cat) => cat.tactics.length > 0);
  }, [searchQuery]);

  /* Sorted + filtered screening results */
  const sortedResults = useMemo(() => {
    let results = [...screeningResults];
    if (showLimitUpOnly) results = results.filter((r) => r.limitUp);
    switch (sortBy) {
      case '匹配度':
        results.sort((a, b) => b.matchPercent - a.matchPercent);
        break;
      case '涨跌幅':
        results.sort((a, b) => b.change - a.change);
        break;
      case '连板数':
        results.sort((a, b) => b.change - a.change);
        break;
      default:
        break;
    }
    return results;
  }, [sortBy, showLimitUpOnly]);

  /* Filtered resonance items */
  const filteredResonance = useMemo(() => {
    if (resonanceFilter === '全部') return resonanceItems;
    if (resonanceFilter === '2战法') return resonanceItems.filter((r) => r.tactics.length === 2);
    return resonanceItems.filter((r) => r.tactics.length >= 3);
  }, [resonanceFilter]);

  /* All active tactic names */
  const allActiveTactics = tacticCategories.flatMap((cat) => cat.tactics.filter((t) => t.active).map((t) => t.name));

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-4">
      {/* ═══ Row 1: 战法库导航 + 选股结果 ═══ */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* ── 战法库导航 (3 cols) ── */}
        <motion.div
          variants={itemVariants}
          className="xl:col-span-3 bg-[#0d1526] rounded-[10px] border border-[rgba(148,163,184,0.1)] overflow-hidden"
        >
          <div className="p-4 border-b border-[rgba(148,163,184,0.08)]">
            <h3 className="text-[16px] font-semibold text-[#f1f5f9] mb-3">战法库</h3>
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#475569]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索战法..."
                className="w-full bg-[#0f1929] text-[#f1f5f9] text-[13px] pl-8 pr-3 py-2 rounded-md border border-[rgba(148,163,184,0.1)] outline-none focus:border-[#c9a84c] placeholder:text-[#475569] transition-colors"
              />
            </div>
          </div>
          <div className="p-3 space-y-1 max-h-[calc(100vh-280px)] overflow-y-auto">
            <AnimatePresence>
              {filteredCategories.map((cat) => (
                <div key={cat.name}>
                  <button
                    onClick={() => toggleCategory(cat.name)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 text-[13px] font-medium text-[#94a3b8] hover:text-[#f1f5f9] rounded-md hover:bg-[#141e33] transition-colors"
                  >
                    {expandedCategories.includes(cat.name) ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                    <span>{cat.name}</span>
                    <span className="text-[11px] text-[#475569] font-mono ml-auto">
                      {cat.tactics.filter((t) => t.active).length}/{cat.tactics.length}
                    </span>
                  </button>
                  <AnimatePresence>
                    {expandedCategories.includes(cat.name) && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                      >
                        {cat.tactics.map((tactic) => (
                          <motion.button
                            key={tactic.name}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            onClick={() => setSelectedTactic(tactic.name)}
                            className={cn(
                              'w-full flex items-center gap-2 px-3 py-1.5 text-[12px] rounded-md transition-all duration-150 relative',
                              selectedTactic === tactic.name
                                ? 'bg-[#141e33] text-[#f1f5f9]'
                                : tactic.active
                                  ? 'text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#141e33]'
                                  : 'text-[#475569] hover:text-[#94a3b8]',
                              selectedTactic === tactic.name && 'before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-[3px] before:h-4 before:bg-[#c9a84c] before:rounded-r-full',
                            )}
                          >
                            <span
                              className={cn(
                                'w-1.5 h-1.5 rounded-full shrink-0',
                                tactic.active ? 'bg-[#c9a84c]' : 'bg-[#334155]',
                              )}
                            />
                            <span className="truncate">{tactic.name}</span>
                            {tactic.active && tactic.triggerCount && (
                              <span className="text-[10px] text-[#475569] font-mono ml-auto">({tactic.triggerCount})</span>
                            )}
                          </motion.button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* ── 战法详情 + 选股结果 (9 cols) ── */}
        <div className="xl:col-span-9 space-y-4">
          {/* 战法详情面板 */}
          <DataCard delay={100}>
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedTactic}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h1 className="text-[22px] font-bold text-[#8b5cf6]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
                      {detail.name}
                    </h1>
                    <span className="text-[11px] px-2 py-0.5 bg-[rgba(139,92,246,0.15)] text-[#8b5cf6] rounded-full">
                      今日触发: {detail.triggerCount}次
                    </span>
                  </div>
                  <span className="flex items-center gap-1 text-[12px] px-2 py-1 bg-[rgba(34,197,94,0.1)] text-[#22c55e] rounded-md font-mono">
                    <TrendingUp size={12} /> 近30日成功率: {detail.successRate}%
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <h4 className="text-[11px] text-[#475569] mb-2 flex items-center gap-1">
                      <Target size={11} /> 触发条件
                    </h4>
                    <ul className="space-y-1">
                      {detail.conditions.map((c, i) => (
                        <li key={i} className="text-[12px] text-[#94a3b8] flex items-start gap-1.5">
                          <span className="text-[#c9a84c] font-mono text-[10px] mt-0.5">{i + 1}.</span>
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-[11px] text-[#475569] mb-2 flex items-center gap-1">
                      <Layers size={11} /> 适用场景
                    </h4>
                    <p className="text-[12px] text-[#94a3b8] leading-relaxed">{detail.scenarios}</p>
                  </div>
                  <div>
                    <h4 className="text-[11px] text-[#475569] mb-2 flex items-center gap-1">
                      <BarChart3 size={11} /> 胜率统计
                    </h4>
                    <div className="flex items-center gap-3">
                      <MiniWinBar data={detail.winHistory} />
                      <span className="text-[13px] font-mono text-[#22c55e]">{detail.successRate}%</span>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-[#475569]">
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[#ef4444]" />盈</span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[#22c55e]" />亏</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </DataCard>

          {/* 选股结果表格 */}
          <DataCard
            delay={200}
            header={
              <div className="flex items-center justify-between w-full flex-wrap gap-2">
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">选股结果</h2>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    <ArrowUpDown size={12} className="text-[#475569]" />
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                      className="text-[11px] bg-[#141e33] text-[#94a3b8] border border-[rgba(148,163,184,0.1)] rounded-md px-2 py-1 outline-none"
                    >
                      <option>匹配度</option>
                      <option>涨跌幅</option>
                      <option>成交额</option>
                      <option>连板数</option>
                    </select>
                  </div>
                  <button
                    onClick={() => setShowLimitUpOnly(!showLimitUpOnly)}
                    className={cn(
                      'text-[11px] px-2 py-1 rounded-md border transition-colors',
                      showLimitUpOnly
                        ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444] border-[rgba(239,68,68,0.3)]'
                        : 'bg-[#141e33] text-[#94a3b8] border-[rgba(148,163,184,0.1)]'
                    )}
                  >
                    仅看涨停
                  </button>
                  <span className="text-[11px] text-[#475569] font-mono">{sortedResults.length}只</span>
                </div>
              </div>
            }
            className="min-h-[400px]"
          >
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-[11px] text-[#475569] border-b border-[rgba(148,163,184,0.1)]">
                    <th className="text-left py-2 px-2 font-medium">排名</th>
                    <th className="text-left py-2 px-2 font-medium">代码</th>
                    <th className="text-left py-2 px-2 font-medium">名称</th>
                    <th className="text-right py-2 px-2 font-medium">现价</th>
                    <th className="text-right py-2 px-2 font-medium">涨跌</th>
                    <th className="text-left py-2 px-2 font-medium">触发信号</th>
                    <th className="text-right py-2 px-2 font-medium">匹配度</th>
                    <th className="text-right py-2 px-2 font-medium">综合分</th>
                    <th className="text-left py-2 px-2 font-medium">游资匹配</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence>
                    {sortedResults.map((row, i) => {
                      const isUp = row.change > 0;
                      return (
                        <motion.tr
                          key={row.code}
                          layout
                          initial={{ opacity: 0, y: 15 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ delay: i * 0.04, duration: 0.3 }}
                          className={cn(
                            'text-[13px] border-b border-[rgba(148,163,184,0.05)] cursor-pointer transition-all duration-150 group',
                            row.limitUp && 'bg-[rgba(239,68,68,0.06)]',
                            !row.limitUp && 'hover:bg-[#141e33]',
                            row.matchPercent >= 90 && 'border-l-2 border-l-[#c9a84c]',
                          )}
                        >
                          <td className="py-2.5 px-2">
                            <span className={cn(
                              'text-[12px] font-mono font-bold',
                              i === 0 ? 'text-[#c9a84c]' : i === 1 ? 'text-[#94a3b8]' : i === 2 ? 'text-[#8a7530]' : 'text-[#475569]',
                            )}>
                              {row.rank}
                            </span>
                          </td>
                          <td className="py-2.5 px-2 text-[13px] font-mono text-[#f1f5f9]">{row.code}</td>
                          <td className="py-2.5 px-2 text-[13px] text-[#f1f5f9]">{row.name}</td>
                          <td className="py-2.5 px-2 text-[13px] font-mono text-right text-[#f1f5f9]">{row.price.toFixed(2)}</td>
                          <td className={cn('py-2.5 px-2 text-[13px] font-mono text-right', isUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                            {isUp ? '+' : ''}{row.change}%
                          </td>
                          <td className="py-2.5 px-2">
                            <div className="flex flex-wrap gap-1">
                              {row.signals.map((s, j) => (
                                <span key={j} className="text-[10px] px-1.5 py-0.5 bg-[rgba(139,92,246,0.1)] text-[#8b5cf6] rounded-full border border-[rgba(139,92,246,0.15)]">
                                  {s}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="py-2.5 px-2 text-right">
                            <motion.span
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className={cn(
                                'text-[13px] font-mono font-semibold',
                                row.matchPercent >= 90 ? 'text-[#c9a84c]' : row.matchPercent >= 80 ? 'text-[#3b82f6]' : 'text-[#94a3b8]',
                              )}
                            >
                              {row.matchPercent}%
                            </motion.span>
                          </td>
                          <td className="py-2.5 px-2 text-right">
                            <span className={cn(
                              'text-[13px] font-mono font-bold',
                              row.score >= 90 ? 'text-[#c9a84c]' : row.score >= 80 ? 'text-[#ef4444]' : 'text-[#94a3b8]',
                            )}>
                              {row.score}
                            </span>
                          </td>
                          <td className="py-2.5 px-2 text-[12px] text-[#c9a84c]">{row.yingyou}</td>
                        </motion.tr>
                      );
                    })}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ═══ Row 2: 多战法共振 ═══ */}
      <DataCard
        delay={400}
        header={
          <div className="flex items-center justify-between w-full flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-[#c9a84c]" />
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">多战法共振</h2>
              <span className="text-[11px] text-[#475569]">同时触发多个战法的标的，信号强度更高</span>
            </div>
            <div className="flex items-center gap-1 bg-[#141e33] rounded-lg p-0.5">
              {(['全部', '2战法', '3战法+'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setResonanceFilter(f)}
                  className={cn(
                    'px-2.5 py-1 text-[11px] rounded-md transition-all duration-200',
                    resonanceFilter === f
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
        className="min-h-[240px]"
      >
        <div className="flex gap-4 overflow-x-auto pb-2" style={{ cursor: 'grab' }}>
          <AnimatePresence>
            {filteredResonance.map((item, i) => {
              const topColor = item.tactics.length >= 4 ? '#c9a84c' : item.tactics.length >= 3 ? '#06d7d7' : '#3b82f6';
              return (
                <motion.div
                  key={item.code}
                  layout
                  initial={{ opacity: 0, y: 25, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: i * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                  className="shrink-0 w-[280px] bg-[#141e33] rounded-lg border border-[rgba(148,163,184,0.08)] hover:border-[rgba(201,168,76,0.25)] hover:-translate-y-1 hover:shadow-elevated transition-all duration-200 cursor-pointer overflow-hidden group"
                >
                  {/* Top color bar */}
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ delay: 0.2 + i * 0.08, duration: 0.4 }}
                    className="h-[2px] group-hover:h-[4px] transition-all duration-200"
                    style={{ background: `linear-gradient(to right, ${topColor}, ${topColor}88)` }}
                  />
                  <div className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-[11px] text-[#475569] font-mono">{item.code}</span>
                        <h3 className="text-[15px] font-semibold text-[#f1f5f9]">{item.name}</h3>
                      </div>
                      <ScoreRing score={item.score} size={56} stroke={4} />
                    </div>
                    <div className="flex items-center gap-2 mb-2.5">
                      <span className="text-[14px] font-mono text-[#f1f5f9]">{item.price.toFixed(2)}</span>
                      <span className={cn(
                        'text-[11px] font-mono px-1.5 py-0.5 rounded',
                        item.change > 0 ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]' : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]'
                      )}>
                        {item.change > 0 ? '+' : ''}{item.change}%
                      </span>
                    </div>
                    {/* Tactics tags */}
                    <div className="flex flex-wrap gap-1 mb-2.5">
                      {item.tactics.map((t, j) => (
                        <motion.span
                          key={t}
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: 0.3 + i * 0.08 + j * 0.04, type: 'spring', stiffness: 400, damping: 15 }}
                          className={cn(
                            'text-[10px] px-1.5 py-0.5 rounded-full border',
                            item.tactics.length >= 3
                              ? 'bg-[rgba(139,92,246,0.12)] text-[#8b5cf6] border-[rgba(139,92,246,0.25)]'
                              : 'bg-[rgba(139,92,246,0.08)] text-[#8b5cf6] border-[rgba(139,92,246,0.15)]',
                          )}
                        >
                          {t}
                        </motion.span>
                      ))}
                    </div>
                    {/* Strength indicator */}
                    <div className="flex items-center gap-1 mb-2">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <motion.div
                          key={j}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.4 + i * 0.08 + j * 0.06 }}
                          className={cn(
                            'w-2 h-2 rounded-full',
                            j < item.strength ? 'bg-[#c9a84c]' : 'bg-[#334155]',
                          )}
                        />
                      ))}
                      <span className="text-[10px] text-[#475569] font-mono ml-1">{item.tactics.length}战法共振</span>
                    </div>
                    {/* AI Comment */}
                    <p className="text-[11px] text-[#475569] leading-relaxed border-t border-[rgba(148,163,184,0.06)] pt-1.5">
                      {item.aiComment}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </DataCard>

      {/* ═══ Row 3: 情绪周期战法适配 + 筛选流程可视化 ═══ */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* 战法场景适配提示 */}
        <DataCard
          delay={500}
          header={
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-[#f97316]" />
              <h2 className="text-[16px] font-semibold text-[#f1f5f9]">战法场景适配</h2>
              <span className="text-[11px] px-2 py-0.5 bg-[rgba(201,168,76,0.1)] text-[#c9a84c] rounded-full">
                当前: {tacticAdaptation.phase}
              </span>
            </div>
          }
        >
          <div className="space-y-3">
            <div>
              <h4 className="text-[11px] text-[#22c55e] mb-2 flex items-center gap-1">
                <CheckCircle2 size={12} /> 当前适宜战法
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {tacticAdaptation.suitable.map((t) => (
                  <span key={t} className="text-[11px] px-2 py-1 bg-[rgba(34,197,94,0.08)] text-[#22c55e] rounded-md border border-[rgba(34,197,94,0.15)]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="border-t border-[rgba(148,163,184,0.06)] pt-3">
              <h4 className="text-[11px] text-[#ef4444] mb-2 flex items-center gap-1">
                <XCircle size={12} /> 当前禁忌战法
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {tacticAdaptation.forbidden.map((t) => (
                  <span key={t} className="text-[11px] px-2 py-1 bg-[rgba(239,68,68,0.08)] text-[#ef4444] rounded-md border border-[rgba(239,68,68,0.15)]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </DataCard>

        {/* 筛选流程可视化 */}
        <DataCard
          delay={550}
          header={
            <div className="flex items-center gap-2">
              <GitBranch size={16} className="text-[#06d7d7]" />
              <h2 className="text-[16px] font-semibold text-[#f1f5f9]">筛选流程</h2>
            </div>
          }
        >
          <div className="flex items-center gap-2">
            {filterSteps.map((step, i) => (
              <div key={i} className="flex items-center gap-2 flex-1">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + i * 0.1 }}
                  className={cn(
                    'flex-1 rounded-lg p-2.5 border transition-all duration-200',
                    step.status === 'pass' && 'bg-[rgba(34,197,94,0.05)] border-[rgba(34,197,94,0.2)]',
                    step.status === 'checking' && 'bg-[rgba(201,168,76,0.05)] border-[rgba(201,168,76,0.2)]',
                  )}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <step.icon size={12} className={cn(
                      step.status === 'pass' && 'text-[#22c55e]',
                      step.status === 'checking' && 'text-[#c9a84c]',
                    )} />
                    <span className={cn(
                      'text-[11px] font-medium',
                      step.status === 'pass' && 'text-[#22c55e]',
                      step.status === 'checking' && 'text-[#c9a84c]',
                    )}>
                      {step.label}
                    </span>
                  </div>
                  <p className="text-[10px] text-[#475569]">{step.desc}</p>
                  {step.status === 'pass' && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.8 + i * 0.1, type: 'spring' }}
                      className="mt-1"
                    >
                      <CheckCircle2 size={12} className="text-[#22c55e]" />
                    </motion.div>
                  )}
                  {step.status === 'checking' && (
                    <div className="mt-1 w-3 h-3 border-2 border-[#c9a84c] border-t-transparent rounded-full animate-spin" />
                  )}
                </motion.div>
                {i < filterSteps.length - 1 && (
                  <ArrowRight size={14} className="text-[#475569] shrink-0" />
                )}
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-[#475569]">
            <span>全市场 {allActiveTactics.length} 个战法同时扫描</span>
            <span className="font-mono">共筛选出 {screeningResults.length} 只标的</span>
          </div>
        </DataCard>
      </div>
    </motion.div>
  );
}
