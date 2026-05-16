import { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import {
  Search, Zap, BarChart3, Layers,
  CheckCircle2, XCircle, Swords, Activity,
  Sparkles, Plus, X,
  Cpu, Box,
} from 'lucide-react';
import Layout from '@/components/Layout';
import DataCard from '@/components/DataCard';
import {
  TACTIC_RULES, TACTIC_STOCK_MATCHES, REAL_LIMIT_UP_STOCKS, MULTI_PERIOD_KLINES,
} from '@/data/realData';
import type { TacticRule, TacticStockMatch } from '@/data/realData';

/* ─── Types ─── */
interface MatchWithStock extends TacticStockMatch {
  stock?: (typeof REAL_LIMIT_UP_STOCKS)[number];
}

/* ─── Success Rate Data (3d/5d/10d) ─── */
const TACTIC_SUCCESS_RATES: Record<string, { d3: number; d5: number; d10: number }> = {
  '首阴战法': { d3: 68, d5: 65, d10: 62 },
  'N字形战法': { d3: 72, d5: 70, d10: 68 },
  '倍量突破': { d3: 65, d5: 63, d10: 60 },
  '三倍量突破战法': { d3: 58, d5: 55, d10: 52 },
  '连板加速': { d3: 75, d5: 72, d10: 70 },
  '龙头情绪战法': { d3: 80, d5: 78, d10: 75 },
  '缩量突破战法': { d3: 60, d5: 58, d10: 55 },
  '反核战法': { d3: 55, d5: 52, d10: 50 },
  '低位首板战法': { d3: 62, d5: 60, d10: 58 },
  '筹码峰战法': { d3: 58, d5: 55, d10: 52 },
  '平台突破战法': { d3: 65, d5: 63, d10: 60 },
  '一进二战法': { d3: 55, d5: 52, d10: 50 },
  '布林带战法': { d3: 58, d5: 55, d10: 52 },
  '分时承接战法': { d3: 60, d5: 58, d10: 55 },
  '缩量尾盘先手战法': { d3: 50, d5: 48, d10: 45 },
  // 新增战法
  '龙头低吸战法': { d3: 58, d5: 56, d10: 54 },
  '欧奈尔CANSLIM模型': { d3: 70, d5: 72, d10: 75 },
  '利弗莫尔关键点位': { d3: 65, d5: 68, d10: 66 },
  '达瓦斯箱体理论': { d3: 62, d5: 65, d10: 63 },
  '威科夫量价分析': { d3: 60, d5: 63, d10: 61 },
  '米内尔维尼趋势模板': { d3: 68, d5: 70, d10: 72 },
};

/* ─── Category Filter Tabs ─── */
const CATEGORY_TABS = ['全部', '情绪', '量能', '形态', '筹码', '技术分析'] as const;
type CategoryTab = (typeof CATEGORY_TABS)[number];

const getCategoryGroup = (cat: string): CategoryTab => {
  if (cat.includes('情绪')) return '情绪';
  if (cat.includes('量能')) return '量能';
  if (cat.includes('形态')) return '形态';
  if (cat.includes('筹码')) return '筹码';
  if (cat.includes('技术分析')) return '技术分析';
  return '技术分析'; // default group for others
};

/* ─── Category Icon Map ─── */
const getCategoryIcon = (name: string) => {
  switch (name) {
    case '量能战法': return BarChart3;
    case '形态战法': return Layers;
    case '情绪战法': return Activity;
    case '筹码战法': return Box;
    case '技术分析战法': return Cpu;
    default: return Swords;
  }
};

/* ─── Success Rate Color (按成功率分档着色) ─── */
const getSuccessRateColor = (rate: number): string => {
  if (rate >= 80) return '#ef4444';   // 红 ≥80%
  if (rate >= 70) return '#f97316';   // 橙 70-80%
  if (rate >= 60) return '#3b82f6';   // 蓝 60-70%
  if (rate >= 50) return '#06d7d7';   // 青 50-60%
  return '#6b7280';                    // 灰 <50%
};

/* ─── Match Score Color ─── */
const getScoreColor = (score: number) => {
  if (score >= 90) return '#c9a84c';
  if (score >= 80) return '#06d7d7';
  if (score >= 70) return '#3b82f6';
  if (score >= 60) return '#f97316';
  return '#ef4444';
};

const getSuccessRate = (tacticName: string, period: 'd3' | 'd5' | 'd10'): number => {
  return TACTIC_SUCCESS_RATES[tacticName]?.[period] ?? 50;
};

/* ─── Page ─── */
export default function TacticsPage() {
  /* ── State ── */
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTactic, setSelectedTactic] = useState<string>('首阴战法');
  const [activeTab, setActiveTab] = useState<'all' | 'resonance'>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [customTactics, setCustomTactics] = useState<TacticRule[]>([]);
  const [successPeriod, setSuccessPeriod] = useState<'d3' | 'd5' | 'd10'>('d5');
  const [hoveredStock, setHoveredStock] = useState<MatchWithStock | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<CategoryTab>('全部');

  /* ── Add Form State ── */
  const [formName, setFormName] = useState('');
  const [formCategory, setFormCategory] = useState('情绪战法');
  const [formConditions, setFormConditions] = useState('');
  const [formBestEnv, setFormBestEnv] = useState('');

  const allTactics = useMemo(() => [...TACTIC_RULES, ...customTactics], [customTactics]);

  /* ── Filtered tactics by category tab ── */
  const categoryFilteredTactics = useMemo(() => {
    let list = allTactics;
    if (categoryFilter !== '全部') {
      list = list.filter(t => getCategoryGroup(t.category) === categoryFilter);
    }
    if (searchQuery.trim()) {
      list = list.filter(t => t.name.includes(searchQuery.trim()));
    }
    return list;
  }, [allTactics, categoryFilter, searchQuery]);

  /* ── Actual matched stocks using TACTIC_STOCK_MATCHES ── */
  const matchedStocks = useMemo<MatchWithStock[]>(() => {
    if (!selectedTactic) return [];
    const matches = TACTIC_STOCK_MATCHES.filter(m => m.tactic === selectedTactic);
    return matches.map(m => {
      const stock = REAL_LIMIT_UP_STOCKS.find(s => s.code === m.code);
      return { ...m, stock };
    }).filter(m => m.stock);
  }, [selectedTactic]);

  const actualCount = matchedStocks.length;

  /* ── Current tactic rule ── */
  const currentTactic = allTactics.find(t => t.name === selectedTactic);

  /* ── Multi-tactic resonance ── */
  const resonanceStocks = useMemo(() => {
    const codeMap: Record<string, { code: string; name: string; tactics: string[] }> = {};
    REAL_LIMIT_UP_STOCKS.forEach(s => {
      if (s.tacticsMatched.length >= 2) {
        codeMap[s.code] = { code: s.code, name: s.name, tactics: s.tacticsMatched };
      }
    });
    return Object.values(codeMap);
  }, []);

  /* ── Global stats ── */
  const globalStats = useMemo(() => {
    const uniqueTactics = new Set(TACTIC_STOCK_MATCHES.map(m => m.tactic));
    const totalMatches = TACTIC_STOCK_MATCHES.length;
    let totalRate = 0;
    let count = 0;
    uniqueTactics.forEach(t => {
      totalRate += getSuccessRate(t, successPeriod);
      count++;
    });
    const avgRate = count > 0 ? Math.round(totalRate / count) : 0;
    return { tacticCount: uniqueTactics.size, totalMatches, avgRate };
  }, [successPeriod]);

  /* ── Mini K-line option generator (with fallback to REAL_LIMIT_UP_STOCKS) ── */
  const getMiniKlineOption = useCallback((stockCode: string) => {
    // 优先从MULTI_PERIOD_KLINES获取
    const klines = MULTI_PERIOD_KLINES[stockCode];
    if (klines && klines.daily && klines.daily.length > 0) {
      const data = klines.daily.slice(-15);
      return {
        grid: { top: 5, right: 5, bottom: 5, left: 5 },
        xAxis: { type: 'category', show: false, data: data.map((_, i) => String(i)) },
        yAxis: { type: 'value', scale: true, show: false },
        series: [{
          type: 'candlestick',
          data: data.map(k => [k[1], k[2], k[3], k[4]]),
          itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' },
        }],
      };
    }
    // Fallback: 从REAL_LIMIT_UP_STOCKS获取kline数据
    const stock = REAL_LIMIT_UP_STOCKS.find(s => s.code === stockCode);
    if (stock && stock.kline && stock.kline.length > 0) {
      const data = stock.kline;
      return {
        grid: { top: 5, right: 5, bottom: 5, left: 5 },
        xAxis: { type: 'category', show: false, data: data.map((_, i) => String(i)) },
        yAxis: { type: 'value', scale: true, show: false },
        series: [{
          type: 'candlestick',
          data: data.map(k => [k[1], k[2], k[3], k[4]]),
          itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' },
        }],
      };
    }
    // 空数据兜底
    return {
      grid: { top: 5, right: 5, bottom: 5, left: 5 },
      xAxis: { type: 'category', show: false },
      yAxis: { type: 'value', scale: true, show: false },
      series: [{
        type: 'candlestick',
        data: [] as number[][],
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' },
      }],
    };
  }, []);

  /* ── Trigger distribution chart ── */
  const triggerDistOption = useMemo(() => ({
    tooltip: { trigger: 'item', backgroundColor: '#1a2744', borderColor: 'rgba(148,163,184,0.1)', textStyle: { color: '#f1f5f9' } },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'],
      avoidLabelOverlap: true,
      label: { show: true, color: '#94a3b8', fontSize: 11, fontFamily: 'Noto Sans SC' },
      itemStyle: { borderRadius: 4, borderColor: '#0d1526', borderWidth: 2 },
      data: allTactics.filter((t): t is TacticRule & { triggerCount: number } => {
        const cnt = TACTIC_STOCK_MATCHES.filter(m => m.tactic === t.name).length;
        return cnt > 0;
      }).map(t => {
        const cnt = TACTIC_STOCK_MATCHES.filter(m => m.tactic === t.name).length;
        return {
          name: t.name, value: cnt,
          itemStyle: { color: getScoreColor(60 + cnt * 8) },
        };
      }),
    }],
  }), [allTactics]);

  /* ── Add tactic handler ── */
  const handleAddTactic = () => {
    if (!formName.trim()) return;
    const newTactic: TacticRule = {
      name: formName.trim(),
      category: formCategory,
      conditions: formConditions.split('；').map(s => s.trim()).filter(Boolean),
      bestEnv: formBestEnv.trim() || '震荡市',
      triggerCount: 0,
      successRate: 50,
    };
    setCustomTactics(prev => [...prev, newTactic]);
    setFormName('');
    setFormCategory('情绪战法');
    setFormConditions('');
    setFormBestEnv('');
    setShowAddForm(false);
  };

  /* ── Actual trigger count for a tactic ── */
  const getActualTriggerCount = (tacticName: string) =>
    TACTIC_STOCK_MATCHES.filter(m => m.tactic === tacticName).length;

  /* ── Success rate period label ── */
  const periodLabel = { d3: '3日', d5: '5日', d10: '10日' } as const;

  return (
    <Layout>
      <div className="p-6 space-y-4">
        {/* ═══════ Header ═══════ */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-100 font-heading">战法选股</h1>
              <p className="text-sm text-slate-400 mt-1">基于真实量价数据的战法匹配与筛选</p>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#c9a84c]/20 text-[#c9a84c] text-sm font-medium hover:bg-[#c9a84c]/30 transition-colors"
            >
              <Plus className="w-4 h-4" />
              添加战法
            </button>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs text-slate-500">战法触发</div>
              <div className="text-sm font-bold text-slate-200">
                <span className="text-[#c9a84c]">{globalStats.tacticCount}</span>战法 /
                <span className="text-[#c9a84c]">{globalStats.totalMatches}</span>只
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">平均成功率({periodLabel[successPeriod]})</div>
              <div className="text-sm font-bold" style={{ color: getSuccessRateColor(globalStats.avgRate) }}>
                {globalStats.avgRate}%
              </div>
            </div>
          </div>
        </div>

        {/* ═══════ Add Form Modal ═══════ */}
        <AnimatePresence>
          {showAddForm && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-[#0e1629] border border-[rgba(148,163,184,0.15)] rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-200">添加自定义战法</h3>
                <button onClick={() => setShowAddForm(false)} className="text-slate-500 hover:text-slate-300">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">战法名称</label>
                  <input
                    type="text" value={formName} onChange={e => setFormName(e.target.value)}
                    placeholder="如: 龙回头战法"
                    className="w-full px-3 py-1.5 bg-[#0d1526] border border-slate-700/50 rounded text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-[#c9a84c]/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">分类</label>
                  <select
                    value={formCategory} onChange={e => setFormCategory(e.target.value)}
                    className="w-full px-3 py-1.5 bg-[#0d1526] border border-slate-700/50 rounded text-sm text-slate-200 focus:outline-none focus:border-[#c9a84c]/50"
                  >
                    <option value="情绪战法">情绪战法</option>
                    <option value="量能战法">量能战法</option>
                    <option value="形态战法">形态战法</option>
                    <option value="筹码战法">筹码战法</option>
                    <option value="技术分析战法">技术分析战法</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">触发条件（分号分隔）</label>
                  <input
                    type="text" value={formConditions} onChange={e => setFormConditions(e.target.value)}
                    placeholder="条件1；条件2；条件3"
                    className="w-full px-3 py-1.5 bg-[#0d1526] border border-slate-700/50 rounded text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-[#c9a84c]/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">最佳环境</label>
                  <input
                    type="text" value={formBestEnv} onChange={e => setFormBestEnv(e.target.value)}
                    placeholder="如: 震荡市"
                    className="w-full px-3 py-1.5 bg-[#0d1526] border border-slate-700/50 rounded text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-[#c9a84c]/50"
                  />
                </div>
              </div>
              <div className="mt-3 flex justify-end">
                <button
                  onClick={handleAddTactic}
                  disabled={!formName.trim()}
                  className="px-4 py-1.5 rounded-lg bg-[#c9a84c] text-[#0d1526] text-sm font-semibold hover:bg-[#d4b45a] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  确认添加
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ═══════ Main Grid ═══════ */}
        <div className="grid grid-cols-12 gap-4">
          {/* ─── Left: Tactic Library (narrow) ─── */}
          <div className="col-span-4 lg:col-span-3 space-y-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text" placeholder="搜索战法..."
                value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-[#0e1629] border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#c9a84c]/50"
              />
            </div>

            {/* Category Filter Tabs */}
            <div className="flex flex-wrap gap-1">
              {CATEGORY_TABS.map(tab => (
                <button
                  key={tab}
                  onClick={() => setCategoryFilter(tab)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                    categoryFilter === tab
                      ? 'bg-[#c9a84c]/20 text-[#c9a84c]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Success Rate Period Toggle */}
            <div className="flex items-center gap-1 bg-[#0e1629] rounded-lg p-1">
              {(['d3', 'd5', 'd10'] as const).map(p => (
                <button
                  key={p}
                  onClick={() => setSuccessPeriod(p)}
                  className={`flex-1 py-1 rounded text-xs font-medium transition-all ${
                    successPeriod === p
                      ? 'bg-[#c9a84c]/20 text-[#c9a84c]'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {periodLabel[p]}
                </button>
              ))}
            </div>

            {/* Tactic Cards List */}
            <DataCard>
              <div className="space-y-1 max-h-[calc(100vh-420px)] overflow-y-auto custom-scrollbar pr-1">
                {categoryFilteredTactics.map(tactic => {
                  const tCount = getActualTriggerCount(tactic.name);
                  const sRate = getSuccessRate(tactic.name, successPeriod);
                  const isSelected = selectedTactic === tactic.name;
                  const Icon = getCategoryIcon(tactic.category);
                  // 使用新的成功率颜色分档
                  const rateColor = getSuccessRateColor(sRate);
                  return (
                    <button
                      key={tactic.name}
                      onClick={() => { setSelectedTactic(tactic.name); setActiveTab('all'); }}
                      className={`w-full text-left rounded-lg p-2.5 transition-all ${
                        isSelected
                          ? 'bg-[#c9a84c]/10 border border-[#c9a84c]/30'
                          : 'hover:bg-slate-800/30 border border-transparent'
                      }`}
                    >
                      {/* Name + Category badge */}
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <Icon className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                          <span
                            className="text-sm font-medium truncate"
                            style={{ color: isSelected ? '#c9a84c' : rateColor }}
                          >
                            {tactic.name}
                          </span>
                        </div>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 flex-shrink-0">
                          {tactic.category.replace('战法', '')}
                        </span>
                      </div>
                      {/* Trigger count + Success rate */}
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">
                          实际触发<span className={tCount > 0 ? 'text-emerald-400 font-medium' : 'text-slate-500'}> {tCount}</span>只
                        </span>
                        <span className="text-slate-500">
                          成功率: <span style={{ color: rateColor }} className="font-medium">{sRate}%</span>
                        </span>
                      </div>
                    </button>
                  );
                })}
                {categoryFilteredTactics.length === 0 && (
                  <div className="text-center py-6 text-slate-500 text-sm">未找到匹配战法</div>
                )}
              </div>
            </DataCard>

            {/* Trigger Distribution Chart */}
            <DataCard header={<h3 className="text-[13px] font-semibold text-[#f1f5f9]">战法触发分布</h3>}>
              <div style={{ height: 160 }}>
                <ReactECharts option={triggerDistOption} style={{ height: '100%' }} />
              </div>
            </DataCard>
          </div>

          {/* ─── Right: Results (wide) ─── */}
          <div className="col-span-8 lg:col-span-9 space-y-3">
            {/* Tactic Detail Header */}
            {currentTactic && (
              <DataCard>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <h2
                        className="text-lg font-bold"
                        style={{ color: getSuccessRateColor(getSuccessRate(currentTactic.name, successPeriod)) }}
                      >
                        {currentTactic.name}
                      </h2>
                      <span className="text-xs px-2 py-0.5 rounded bg-[#c9a84c]/20 text-[#c9a84c]">{currentTactic.category}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                        实际触发: {actualCount}只
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-400 flex-wrap">
                      <span>
                        成功率:
                        <strong className="ml-1" style={{ color: getSuccessRateColor(getSuccessRate(currentTactic.name, successPeriod)) }}>
                          {getSuccessRate(currentTactic.name, successPeriod)}%
                        </strong>
                        <span className="text-xs text-slate-600 ml-1">({periodLabel[successPeriod]})</span>
                      </span>
                      <span>最佳环境: {currentTactic.bestEnv}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xs text-slate-500 mb-1.5">触发条件:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {currentTactic.conditions.map((c, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-md bg-[#0e1629] border border-slate-700/50 text-slate-300">
                        {i + 1}. {c}
                      </span>
                    ))}
                  </div>
                </div>
              </DataCard>
            )}

            {/* Tabs + Stats Row */}
            <div className="flex items-center gap-3">
              <div className="flex gap-2 flex-1">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'all' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  选股结果 ({actualCount}只)
                </button>
                <button
                  onClick={() => setActiveTab('resonance')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'resonance' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  多战法共振 ({resonanceStocks.length}组)
                </button>
              </div>
              {/* Compact trigger stats inline */}
              {activeTab === 'all' && currentTactic && (
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-500">
                    触发<span className="text-[#c9a84c] font-medium">{getActualTriggerCount(currentTactic.name)}</span>只
                  </span>
                  <span className="text-slate-500">
                    成功率<span style={{ color: getSuccessRateColor(getSuccessRate(currentTactic.name, successPeriod)) }} className="font-medium">{getSuccessRate(currentTactic.name, successPeriod)}%</span>
                  </span>
                </div>
              )}
            </div>

            {/* ─── Stock Results (2-col grid) ─── */}
            {activeTab === 'all' ? (
              <div>
                {actualCount === 0 ? (
                  <DataCard>
                    <div className="text-center py-12 text-slate-500">
                      <Zap className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>该战法今日未触发匹配标的</p>
                      <p className="text-sm mt-1">当前退潮期，多数战法触发率低</p>
                    </div>
                  </DataCard>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {matchedStocks.map((m, i) => (
                      <motion.div
                        key={`${m.code}-${i}`}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.06 }}
                        className="relative"
                        onMouseEnter={() => setHoveredStock(m)}
                        onMouseLeave={() => setHoveredStock(null)}
                      >
                        <DataCard>
                          <div className="flex items-start gap-3">
                            {/* Rank */}
                            <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-[#0e1629] flex items-center justify-center text-xs font-bold" style={{ color: getScoreColor(m.matchScore) }}>
                              {i + 1}
                            </div>
                            {/* Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs text-slate-500 font-mono">{m.code}</span>
                                <span className="text-sm font-bold text-slate-100">{m.name}</span>
                                {m.stock && (
                                  <>
                                    <span className="text-sm font-bold text-rose-400 font-mono">+{m.stock.changePct}%</span>
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                                      {m.stock.consecutiveBoards > 1 ? `${m.stock.consecutiveBoards}连板` : '首板'}
                                    </span>
                                  </>
                                )}
                              </div>
                              <p className="text-xs text-[#c9a84c] mt-1 truncate">{m.matchReason}</p>
                              {/* Condition pills */}
                              <div className="flex flex-wrap gap-1 mt-1.5">
                                {m.details.map((d, j) => (
                                  <span key={j} className={`text-[10px] px-1.5 py-0.5 rounded flex items-center gap-0.5 ${d.met ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800/50 text-slate-500'}`}>
                                    {d.met ? <CheckCircle2 className="w-2.5 h-2.5" /> : <XCircle className="w-2.5 h-2.5" />}
                                    {d.condition}
                                  </span>
                                ))}
                              </div>
                            </div>
                            {/* Score */}
                            <div className="flex-shrink-0 text-right">
                              <div className="text-xl font-bold font-mono" style={{ color: getScoreColor(m.matchScore) }}>{m.matchScore}</div>
                              <div className="text-[10px] text-slate-500">匹配度</div>
                            </div>
                          </div>
                        </DataCard>

                        {/* ═══════ Hover Tooltip with Mini K-line ═══════ */}
                        {hoveredStock?.code === m.code && hoveredStock?.tactic === m.tactic && (
                          <div
                            className="absolute z-50 bg-[#0d1526] border border-[rgba(148,163,184,0.15)] rounded-lg p-2.5 shadow-xl"
                            style={{ width: 320, top: -8, left: 'calc(100% + 8px)' }}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[11px] text-[#f1f5f9] font-medium">{m.name} <span className="text-slate-500 font-mono">{m.code}</span></span>
                              <span className="text-[10px] text-[#c9a84c]">{m.matchReason}</span>
                            </div>
                            {/* Mini K-line Chart */}
                            <div style={{ height: 120 }}>
                              <ReactECharts
                                option={getMiniKlineOption(m.code)}
                                style={{ height: '100%' }}
                                opts={{ renderer: 'canvas' }}
                              />
                            </div>
                            {/* Condition details */}
                            <div className="mt-1.5 space-y-0.5">
                              {m.details.map((d, idx) => (
                                <div key={idx} className="flex items-center justify-between text-[9px]">
                                  <span className={d.met ? 'text-[#22c55e]' : 'text-[#ef4444]'}>{d.condition}</span>
                                  <span className="text-[#94a3b8] font-mono">{d.value}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                )}

                {/* ═══════ Bottom: Triggered Tactics Summary (compact inline) ═══════ */}
                {actualCount > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800">
                    <div className="flex items-center gap-4 flex-wrap">
                      <span className="text-xs text-slate-500">该战法今日触发 <strong className="text-[#c9a84c]">{actualCount}</strong> 只标的</span>
                      <span className="text-xs text-slate-500">
                        成功率
                        <strong className="ml-1" style={{ color: getSuccessRateColor(getSuccessRate(selectedTactic, successPeriod)) }}>
                          {getSuccessRate(selectedTactic, successPeriod)}%
                        </strong>
                      </span>
                      <span className="text-xs text-slate-500">
                        最高匹配度 <strong className="text-[#c9a84c]">{Math.max(...matchedStocks.map(m => m.matchScore))}</strong>分
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* ─── Resonance Tab ─── */
              <div className="grid grid-cols-2 gap-3">
                {resonanceStocks.map((s, i) => (
                  <motion.div key={s.code} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.08 }}>
                    <DataCard>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-[#c9a84c]/10 flex items-center justify-center">
                          <Sparkles className="w-5 h-5 text-[#c9a84c]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-100">{s.name}</span>
                            <span className="text-xs text-slate-500 font-mono">{s.code}</span>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {s.tactics.map(t => (
                              <span key={t} className="text-xs px-1.5 py-0.5 rounded bg-[#c9a84c]/10 text-[#c9a84c]">{t}</span>
                            ))}
                          </div>
                        </div>
                        <div className="text-center flex-shrink-0">
                          <div className="text-lg font-bold text-[#c9a84c]">{s.tactics.length}</div>
                          <div className="text-[10px] text-slate-500">战法共振</div>
                        </div>
                      </div>
                    </DataCard>
                  </motion.div>
                ))}
              </div>
            )}

            {/* ═══════ All Tactics Trigger Overview (moved from bottom to compact card) ═══════ */}
            <DataCard header={<h3 className="text-[13px] font-semibold text-[#f1f5f9]">全部战法触发统计</h3>}>
              <div className="flex flex-wrap gap-2">
                {allTactics
                  .filter(t => getActualTriggerCount(t.name) > 0)
                  .map(t => {
                    const cnt = getActualTriggerCount(t.name);
                    const rate = getSuccessRate(t.name, successPeriod);
                    return (
                      <div key={t.name} className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#0e1629]">
                        <span className="text-xs font-medium" style={{ color: getSuccessRateColor(rate) }}>{t.name}</span>
                        <span className="text-xs font-bold text-[#c9a84c]">{cnt}只</span>
                        <span className="text-[10px] text-slate-500">{rate}%</span>
                      </div>
                    );
                  })}
                {allTactics.filter(t => getActualTriggerCount(t.name) === 0).length > 0 && (
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#0e1629] opacity-50">
                    <span className="text-xs text-slate-500">
                      未触发: {allTactics.filter(t => getActualTriggerCount(t.name) === 0).length}个
                    </span>
                  </div>
                )}
              </div>
            </DataCard>
          </div>
        </div>
      </div>
    </Layout>
  );
}
