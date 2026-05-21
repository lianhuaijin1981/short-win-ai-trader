import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import {
  Newspaper, Bell, TrendingUp, TrendingDown, Minus,
  Filter, Tag, AlertTriangle,
  Clock, BarChart3, Shield,
  Zap, Target, Activity,
  Globe, Building2, Users, BookOpen,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import {
  MOCK_NEWS, NEWS_SOURCES, NEWS_CATEGORIES, IMPORTANCE_LEVELS,
  IMPORTANCE_COLORS, CATEGORY_BACKTEST_STATS, NEWS_SOURCE_STATUS,
  analyzeSectorImpact,
} from '@/data/newsData';
import type {
  NewsItem, NewsSource, NewsCategory, ImportanceLevel,
} from '@/data/newsData';

/* ─── Source Icons ─── */
const getSourceIcon = (source: NewsSource) => {
  switch (source) {
    case '巨潮资讯': return Building2;
    case '上交所官网': return Building2;
    case '深交所官网': return Building2;
    case '财联社': return Newspaper;
    case '同花顺': return BarChart3;
    case '东方财富': return Globe;
    case '淘股吧': return Users;
    case '韭研公社': return BookOpen;
    case '雪球网': return Globe;
    case '开盘啦': return Zap;
    default: return Newspaper;
  }
};

/* ─── Importance Badge Color ─── */
const getImportanceBg = (importance: ImportanceLevel): string => {
  switch (importance) {
    case '重大利好': return 'bg-red-500/20 text-red-400 border-red-500/30';
    case '一般利好': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case '中性': return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    case '一般利空': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case '重大利空': return 'bg-green-500/20 text-green-400 border-green-500/30';
  }
};

/* ─── Risk Level Color ─── */
const getRiskColor = (level: string): string => {
  switch (level) {
    case '高风险': return '#ef4444';
    case '中风险': return '#f97316';
    case '低风险': return '#3b82f6';
    default: return '#6b7280';
  }
};

/* ─── Suggestion Type Color ─── */
const getSuggestionColor = (type: string): string => {
  switch (type) {
    case '积极介入': return '#ef4444';
    case '谨慎介入': return '#f97316';
    case '观望等待': return '#6b7280';
    case '逢高减仓': return '#3b82f6';
    default: return '#6b7280';
  }
};

/* ─── Page ─── */
export default function NewsPage() {
  /* ── State ── */
  const [selectedImportance, setSelectedImportance] = useState<ImportanceLevel | '全部'>('全部');
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory | '全部'>('全部');
  const [selectedSource, setSelectedSource] = useState<NewsSource | '全部'>('全部');
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'alert' | 'suggestion' | 'sector' | 'source'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showBacktest, setShowBacktest] = useState(false);

  /* ── Filtered News ─── */
  const filteredNews = useMemo(() => {
    let list = [...MOCK_NEWS].sort((a, b) => b.importanceScore - a.importanceScore);
    
    if (selectedImportance !== '全部') {
      list = list.filter(n => n.importance === selectedImportance);
    }
    if (selectedCategory !== '全部') {
      list = list.filter(n => n.category === selectedCategory);
    }
    if (selectedSource !== '全部') {
      list = list.filter(n => n.source === selectedSource);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      list = list.filter(n => 
        n.title.toLowerCase().includes(q) || 
        n.summary.toLowerCase().includes(q) ||
        n.relatedStocks.some(s => s.name.includes(q) || s.code.includes(q))
      );
    }
    
    return list;
  }, [selectedImportance, selectedCategory, selectedSource, searchQuery]);

  /* ── Alert News (重大利好 + 重大利空) ─── */
  const alertNews = useMemo(() => 
    MOCK_NEWS.filter(n => n.importance === '重大利好' || n.importance === '重大利空')
      .sort((a, b) => b.importanceScore - a.importanceScore),
    []
  );

  /* ── News with Suggestions ─── */
  const suggestionNews = useMemo(() => 
    MOCK_NEWS.filter(n => n.suggestion !== null)
      .sort((a, b) => (b.suggestion?.confidence ?? 0) - (a.suggestion?.confidence ?? 0)),
    []
  );

  /* ── Sector Impact ─── */
  const sectorImpacts = useMemo(() => analyzeSectorImpact(MOCK_NEWS), []);

  /* ── Stats ─── */
  const stats = useMemo(() => ({
    total: MOCK_NEWS.length,
    positive: MOCK_NEWS.filter(n => n.importance === '重大利好' || n.importance === '一般利好').length,
    negative: MOCK_NEWS.filter(n => n.importance === '重大利空' || n.importance === '一般利空').length,
    neutral: MOCK_NEWS.filter(n => n.importance === '中性').length,
    withSuggestion: MOCK_NEWS.filter(n => n.suggestion !== null).length,
    withRisk: MOCK_NEWS.filter(n => n.riskWarning !== null).length,
  }), []);

  /* ── Backtest Chart Option ─── */
  const backtestOption = useMemo(() => {
    const categories = NEWS_CATEGORIES;
    const winRates = categories.map(c => CATEGORY_BACKTEST_STATS[c].winRate);
    const day1Rates = categories.map(c => CATEGORY_BACKTEST_STATS[c].day1UpRate);
    
    return {
      tooltip: { 
        trigger: 'axis', 
        backgroundColor: '#1a2744', 
        borderColor: 'rgba(148,163,184,0.1)', 
        textStyle: { color: '#f1f5f9' },
        axisPointer: { type: 'shadow' }
      },
      legend: { 
        data: ['胜率', '次日上涨概率'], 
        textStyle: { color: '#94a3b8', fontSize: 11 },
        top: 0
      },
      grid: { top: 35, right: 15, bottom: 80, left: 45 },
      xAxis: { 
        type: 'category', 
        data: categories.map(c => c.replace('数据', '').replace('评级', '')),
        axisLabel: { 
          color: '#94a3b8', 
          fontSize: 10, 
          rotate: 45,
          interval: 0
        },
        axisLine: { lineStyle: { color: '#334155' } }
      },
      yAxis: { 
        type: 'value', 
        max: 100,
        axisLabel: { color: '#94a3b8', formatter: '{value}%' },
        splitLine: { lineStyle: { color: '#1e293b' } },
        axisLine: { lineStyle: { color: '#334155' } }
      },
      series: [
        {
          name: '胜率',
          type: 'bar',
          data: winRates,
          itemStyle: { color: '#c9a84c' },
          barWidth: '30%'
        },
        {
          name: '次日上涨概率',
          type: 'bar',
          data: day1Rates,
          itemStyle: { color: '#06d7d7' },
          barWidth: '30%'
        }
      ]
    };
  }, []);

  /* ── Importance Distribution Chart ─── */
  const importanceDistOption = useMemo(() => ({
    tooltip: { 
      trigger: 'item', 
      backgroundColor: '#1a2744', 
      borderColor: 'rgba(148,163,184,0.1)', 
      textStyle: { color: '#f1f5f9' } 
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      label: { show: true, color: '#94a3b8', fontSize: 11 },
      itemStyle: { borderRadius: 4, borderColor: '#0d1526', borderWidth: 2 },
      data: IMPORTANCE_LEVELS.map(level => ({
        name: level,
        value: MOCK_NEWS.filter(n => n.importance === level).length,
        itemStyle: { color: IMPORTANCE_COLORS[level] }
      }))
    }]
  }), []);

  /* ── Source Status Chart ─── */
  const sourceStatusOption = useMemo(() => ({
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: '#1a2744', 
      borderColor: 'rgba(148,163,184,0.1)', 
      textStyle: { color: '#f1f5f9' },
      axisPointer: { type: 'shadow' }
    },
    grid: { top: 15, right: 15, bottom: 15, left: 85 },
    xAxis: { 
      type: 'value', 
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#1e293b' } }
    },
    yAxis: { 
      type: 'category', 
      data: NEWS_SOURCE_STATUS.map(s => s.source).reverse(),
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      type: 'bar',
      data: NEWS_SOURCE_STATUS.map(s => s.todayCount).reverse(),
      itemStyle: { 
        color: (params: any) => {
          const colors = ['#c9a84c', '#06d7d7', '#3b82f6', '#8b5cf6', '#ef4444', '#f97316', '#22c55e', '#06d7d7', '#3b82f6', '#8b5cf6'];
          return colors[params.dataIndex % colors.length];
        }
      },
      barWidth: '60%',
      label: { show: true, position: 'right', color: '#94a3b8', fontSize: 10 }
    }]
  }), []);

  return (
      <div className="space-y-4">
        {/* ═══════ Header ═══════ */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-100 font-heading">资讯采集</h1>
              <p className="text-sm text-slate-400 mt-1">全域资讯智能采集 · 基于历史回测的重要性研判</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowBacktest(!showBacktest)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showBacktest ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'bg-slate-800/50 text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              回测数据
            </button>
          </div>
        </div>

        {/* ═══════ Stats Cards ═══════ */}
        <div className="grid grid-cols-6 gap-3">
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center">
                <Newspaper className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">今日资讯</div>
                <div className="text-xl font-bold text-slate-200">{stats.total}</div>
              </div>
            </div>
          </DataCard>
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">利好资讯</div>
                <div className="text-xl font-bold text-red-400">{stats.positive}</div>
              </div>
            </div>
          </DataCard>
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <TrendingDown className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">利空资讯</div>
                <div className="text-xl font-bold text-green-400">{stats.negative}</div>
              </div>
            </div>
          </DataCard>
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center">
                <Minus className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">中性资讯</div>
                <div className="text-xl font-bold text-slate-400">{stats.neutral}</div>
              </div>
            </div>
          </DataCard>
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#c9a84c]/10 flex items-center justify-center">
                <Target className="w-5 h-5 text-[#c9a84c]" />
              </div>
              <div>
                <div className="text-xs text-slate-500">介入建议</div>
                <div className="text-xl font-bold text-[#c9a84c]">{stats.withSuggestion}</div>
              </div>
            </div>
          </DataCard>
          <DataCard>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">风险预警</div>
                <div className="text-xl font-bold text-orange-400">{stats.withRisk}</div>
              </div>
            </div>
          </DataCard>
        </div>

        {/* ═══════ Backtest Data Panel ═══════ */}
        <AnimatePresence>
          {showBacktest && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <DataCard header={<h3 className="text-sm font-semibold text-slate-200">各消息类型历史回测统计</h3>}>
                <div className="grid grid-cols-2 gap-4">
                  <div style={{ height: 300 }}>
                    <ReactECharts option={backtestOption} style={{ height: '100%' }} />
                  </div>
                  <div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-slate-500 border-b border-slate-800">
                            <th className="py-2 px-2 text-left">消息类型</th>
                            <th className="py-2 px-2 text-right">样本数</th>
                            <th className="py-2 px-2 text-right">胜率</th>
                            <th className="py-2 px-2 text-right">次日涨%</th>
                            <th className="py-2 px-2 text-right">3日涨%</th>
                            <th className="py-2 px-2 text-right">5日涨%</th>
                            <th className="py-2 px-2 text-right">盈亏比</th>
                          </tr>
                        </thead>
                        <tbody>
                          {NEWS_CATEGORIES.map(cat => {
                            const s = CATEGORY_BACKTEST_STATS[cat];
                            return (
                              <tr key={cat} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                                <td className="py-1.5 px-2 text-slate-300">{cat}</td>
                                <td className="py-1.5 px-2 text-right text-slate-400">{s.occurrenceCount.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-right font-medium" style={{ color: s.winRate >= 60 ? '#ef4444' : s.winRate >= 50 ? '#c9a84c' : '#6b7280' }}>{s.winRate}%</td>
                                <td className="py-1.5 px-2 text-right text-slate-400">{s.day1UpRate}%</td>
                                <td className="py-1.5 px-2 text-right text-slate-400">{s.day3UpRate}%</td>
                                <td className="py-1.5 px-2 text-right text-slate-400">{s.day5UpRate}%</td>
                                <td className="py-1.5 px-2 text-right" style={{ color: s.profitLossRatio >= 1.5 ? '#ef4444' : s.profitLossRatio >= 1 ? '#c9a84c' : '#6b7280' }}>{s.profitLossRatio.toFixed(2)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </DataCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ═══════ Tabs ═══════ */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'all' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            全部资讯 ({filteredNews.length})
          </button>
          <button
            onClick={() => setActiveTab('alert')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'alert' ? 'bg-red-500/20 text-red-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            重要预警 ({alertNews.length})
          </button>
          <button
            onClick={() => setActiveTab('suggestion')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'suggestion' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            介入建议 ({suggestionNews.length})
          </button>
          <button
            onClick={() => setActiveTab('sector')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'sector' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            板块影响 ({sectorImpacts.length})
          </button>
          <button
            onClick={() => setActiveTab('source')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'source' ? 'bg-purple-500/20 text-purple-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            采集状态
          </button>
        </div>

        {/* ═══════ Filters ═══════ */}
        {activeTab === 'all' && (
          <div className="space-y-3">
            {/* Search */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="搜索资讯标题、个股代码/名称..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-[#0e1629] border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#c9a84c]/50"
              />
            </div>
            {/* Importance Filter */}
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-slate-500 py-1">重要性:</span>
              <button
                onClick={() => setSelectedImportance('全部')}
                className={`px-2.5 py-1 rounded text-xs transition-all ${
                  selectedImportance === '全部' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                全部
              </button>
              {IMPORTANCE_LEVELS.map(level => (
                <button
                  key={level}
                  onClick={() => setSelectedImportance(level)}
                  className={`px-2.5 py-1 rounded text-xs transition-all border ${
                    selectedImportance === level 
                      ? getImportanceBg(level)
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 border-transparent'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
            {/* Category Filter */}
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-slate-500 py-1">类型:</span>
              <button
                onClick={() => setSelectedCategory('全部')}
                className={`px-2.5 py-1 rounded text-xs transition-all ${
                  selectedCategory === '全部' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                全部
              </button>
              {NEWS_CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded text-xs transition-all ${
                    selectedCategory === cat ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
            {/* Source Filter */}
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-slate-500 py-1">来源:</span>
              <button
                onClick={() => setSelectedSource('全部')}
                className={`px-2.5 py-1 rounded text-xs transition-all ${
                  selectedSource === '全部' ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                全部
              </button>
              {NEWS_SOURCES.map(source => {
                const Icon = getSourceIcon(source);
                return (
                  <button
                    key={source}
                    onClick={() => setSelectedSource(source)}
                    className={`px-2.5 py-1 rounded text-xs transition-all flex items-center gap-1 ${
                      selectedSource === source ? 'bg-[#c9a84c]/20 text-[#c9a84c]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    {source}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══════ Main Content ═══════ */}
        <div className="grid grid-cols-12 gap-4">
          {/* ─── Left: News List ─── */}
          <div className={`${activeTab === 'source' ? 'col-span-12' : 'col-span-8'} space-y-3`}>
            {/* All News Tab */}
            {activeTab === 'all' && (
              <div className="space-y-2">
                {filteredNews.map((news, i) => (
                  <motion.div
                    key={news.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                  >
                    <DataCard>
                      <div 
                        className="cursor-pointer"
                        onClick={() => setSelectedNews(selectedNews?.id === news.id ? null : news)}
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              {/* Importance Badge */}
                              <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getImportanceBg(news.importance)}`}>
                                {news.importance}
                              </span>
                              {/* Source */}
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 flex items-center gap-0.5">
                                {(() => { const Icon = getSourceIcon(news.source); return <Icon className="w-2.5 h-2.5" />; })()}
                                {news.source}
                              </span>
                              {/* Category */}
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                                {news.category}
                              </span>
                              {/* Score */}
                              <span className="text-[10px] text-slate-500">
                                重要性评分: <span className="text-[#c9a84c] font-medium">{news.importanceScore}</span>
                              </span>
                            </div>
                            {/* Title */}
                            <h3 className="text-sm font-medium text-slate-200 line-clamp-1">{news.title}</h3>
                            {/* Summary */}
                            <p className="text-xs text-slate-400 mt-1 line-clamp-2">{news.summary}</p>
                          </div>
                          {/* Right Side */}
                          <div className="flex-shrink-0 text-right">
                            <div className="text-xs text-slate-500 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {news.publishTime.split(' ')[1]}
                            </div>
                            {news.suggestion && (
                              <div className="mt-1 text-[10px] px-1.5 py-0.5 rounded" style={{ 
                                backgroundColor: getSuggestionColor(news.suggestion.type) + '20',
                                color: getSuggestionColor(news.suggestion.type)
                              }}>
                                {news.suggestion.type}
                              </div>
                            )}
                            {news.riskWarning && (
                              <div className="mt-1 text-[10px] px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-400 flex items-center gap-0.5">
                                <AlertTriangle className="w-2.5 h-2.5" />
                                {news.riskWarning.level}
                              </div>
                            )}
                          </div>
                        </div>
                        {/* Related Stocks */}
                        {news.relatedStocks.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-slate-800/50">
                            <Tag className="w-3 h-3 text-slate-500 mt-0.5" />
                            {news.relatedStocks.map(stock => (
                              <span key={stock.code} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-400">
                                {stock.name}({stock.code})
                              </span>
                            ))}
                          </div>
                        )}
                        {/* Expanded Detail */}
                        <AnimatePresence>
                          {selectedNews?.id === news.id && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              className="mt-3 pt-3 border-t border-slate-800/50 space-y-3"
                            >
                              {/* Content */}
                              <div>
                                <div className="text-xs text-slate-500 mb-1">详细内容:</div>
                                <p className="text-xs text-slate-300 leading-relaxed">{news.content}</p>
                              </div>
                              {/* Backtest Stats */}
                              <div>
                                <div className="text-xs text-slate-500 mb-1.5">历史回测统计 ({news.category}):</div>
                                <div className="grid grid-cols-4 gap-2">
                                  <div className="bg-[#0e1629] rounded p-2 text-center">
                                    <div className="text-[10px] text-slate-500">样本数</div>
                                    <div className="text-sm font-bold text-slate-200">{news.backtestStats.occurrenceCount.toLocaleString()}</div>
                                  </div>
                                  <div className="bg-[#0e1629] rounded p-2 text-center">
                                    <div className="text-[10px] text-slate-500">胜率</div>
                                    <div className="text-sm font-bold" style={{ color: news.backtestStats.winRate >= 60 ? '#ef4444' : '#c9a84c' }}>{news.backtestStats.winRate}%</div>
                                  </div>
                                  <div className="bg-[#0e1629] rounded p-2 text-center">
                                    <div className="text-[10px] text-slate-500">次日上涨</div>
                                    <div className="text-sm font-bold text-slate-200">{news.backtestStats.day1UpRate}%</div>
                                  </div>
                                  <div className="bg-[#0e1629] rounded p-2 text-center">
                                    <div className="text-[10px] text-slate-500">盈亏比</div>
                                    <div className="text-sm font-bold text-slate-200">{news.backtestStats.profitLossRatio.toFixed(2)}</div>
                                  </div>
                                </div>
                              </div>
                              {/* Suggestion */}
                              {news.suggestion && (
                                <div className="bg-[#0e1629] rounded-lg p-3 border border-[#c9a84c]/20">
                                  <div className="flex items-center gap-2 mb-2">
                                    <Target className="w-4 h-4 text-[#c9a84c]" />
                                    <span className="text-sm font-semibold" style={{ color: getSuggestionColor(news.suggestion!.type) }}>
                                      {news.suggestion.type}
                                    </span>
                                    <span className="text-xs text-slate-500">置信度: {news.suggestion.confidence}%</span>
                                  </div>
                                  <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div>
                                      <span className="text-slate-500">建议仓位:</span>
                                      <span className="text-slate-200 ml-1">{news.suggestion.suggestedPosition}%</span>
                                    </div>
                                    <div>
                                      <span className="text-slate-500">持有周期:</span>
                                      <span className="text-slate-200 ml-1">{news.suggestion.holdingPeriod}</span>
                                    </div>
                                    {news.suggestion.buyRange.low > 0 && (
                                      <div>
                                        <span className="text-slate-500">买入区间:</span>
                                        <span className="text-slate-200 ml-1">{news.suggestion.buyRange.low} - {news.suggestion.buyRange.high}</span>
                                      </div>
                                    )}
                                    {news.suggestion.stopLoss > 0 && (
                                      <div>
                                        <span className="text-slate-500">止损位:</span>
                                        <span className="text-red-400 ml-1">{news.suggestion.stopLoss}</span>
                                      </div>
                                    )}
                                    {news.suggestion.takeProfit > 0 && (
                                      <div>
                                        <span className="text-slate-500">止盈位:</span>
                                        <span className="text-green-400 ml-1">{news.suggestion.takeProfit}</span>
                                      </div>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-400 mt-2">{news.suggestion.reason}</p>
                                </div>
                              )}
                              {/* Risk Warning */}
                              {news.riskWarning && (
                                <div className="bg-orange-500/5 rounded-lg p-3 border border-orange-500/20">
                                  <div className="flex items-center gap-2 mb-2">
                                    <Shield className="w-4 h-4" style={{ color: getRiskColor(news.riskWarning!.level) }} />
                                    <span className="text-sm font-semibold" style={{ color: getRiskColor(news.riskWarning!.level) }}>
                                      风险预警 - {news.riskWarning.riskType}
                                    </span>
                                  </div>
                                  <p className="text-xs text-slate-300 mb-1">{news.riskWarning.description}</p>
                                  <p className="text-xs text-orange-400">{news.riskWarning.suggestedAction}</p>
                                </div>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </DataCard>
                  </motion.div>
                ))}
                {filteredNews.length === 0 && (
                  <DataCard>
                    <div className="text-center py-12 text-slate-500">
                      <Newspaper className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>暂无匹配的资讯内容</p>
                    </div>
                  </DataCard>
                )}
              </div>
            )}

            {/* Alert Tab */}
            {activeTab === 'alert' && (
              <div className="space-y-2">
                {alertNews.map((news, i) => (
                  <motion.div
                    key={news.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <DataCard>
                      <div className="flex items-start gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          news.importance === '重大利好' ? 'bg-red-500/10' : 'bg-green-500/10'
                        }`}>
                          {news.importance === '重大利好' ? (
                            <TrendingUp className="w-5 h-5 text-red-400" />
                          ) : (
                            <TrendingDown className="w-5 h-5 text-green-400" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getImportanceBg(news.importance)}`}>
                              {news.importance}
                            </span>
                            <span className="text-xs text-slate-500">{news.publishTime}</span>
                          </div>
                          <h3 className="text-sm font-medium text-slate-200">{news.title}</h3>
                          <p className="text-xs text-slate-400 mt-1">{news.summary}</p>
                          {news.relatedStocks.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              {news.relatedStocks.map(stock => (
                                <span key={stock.code} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-400">
                                  {stock.name}({stock.code})
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </DataCard>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Suggestion Tab */}
            {activeTab === 'suggestion' && (
              <div className="space-y-2">
                {suggestionNews.map((news, i) => (
                  <motion.div
                    key={news.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <DataCard>
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-full bg-[#c9a84c]/10 flex items-center justify-center flex-shrink-0">
                          <Target className="w-5 h-5 text-[#c9a84c]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getImportanceBg(news.importance)}`}>
                              {news.importance}
                            </span>
                            {news.suggestion && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ 
                                backgroundColor: getSuggestionColor(news.suggestion.type) + '20',
                                color: getSuggestionColor(news.suggestion.type)
                              }}>
                                {news.suggestion.type}
                              </span>
                            )}
                          </div>
                          <h3 className="text-sm font-medium text-slate-200">{news.title}</h3>
                          {news.suggestion && (
                            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                              <div>
                                <span className="text-slate-500">建议仓位:</span>
                                <span className="text-slate-200 ml-1">{news.suggestion.suggestedPosition}%</span>
                              </div>
                              <div>
                                <span className="text-slate-500">持有周期:</span>
                                <span className="text-slate-200 ml-1">{news.suggestion.holdingPeriod}</span>
                              </div>
                              <div>
                                <span className="text-slate-500">置信度:</span>
                                <span className="text-[#c9a84c] ml-1">{news.suggestion.confidence}%</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </DataCard>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Sector Impact Tab */}
            {activeTab === 'sector' && (
              <div className="space-y-2">
                {sectorImpacts.map((impact, i) => (
                  <motion.div
                    key={impact.sector}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <DataCard>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            impact.direction === '利好' ? 'bg-red-500/10' : 
                            impact.direction === '利空' ? 'bg-green-500/10' : 'bg-slate-700/50'
                          }`}>
                            {impact.direction === '利好' ? (
                              <TrendingUp className="w-5 h-5 text-red-400" />
                            ) : impact.direction === '利空' ? (
                              <TrendingDown className="w-5 h-5 text-green-400" />
                            ) : (
                              <Minus className="w-5 h-5 text-slate-400" />
                            )}
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-slate-200">{impact.sector}</h3>
                            <p className="text-xs text-slate-400 mt-0.5">{impact.suggestion}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold" style={{ 
                            color: impact.direction === '利好' ? '#ef4444' : impact.direction === '利空' ? '#22c55e' : '#6b7280'
                          }}>
                            {impact.intensity}
                          </div>
                          <div className="text-[10px] text-slate-500">影响强度</div>
                          <div className="text-[10px] text-slate-500 mt-0.5">{impact.newsCount}条资讯</div>
                        </div>
                      </div>
                    </DataCard>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Source Status Tab */}
            {activeTab === 'source' && (
              <div className="grid grid-cols-2 gap-4">
                <DataCard header={<h3 className="text-sm font-semibold text-slate-200">采集源今日采集量</h3>}>
                  <div style={{ height: 300 }}>
                    <ReactECharts option={sourceStatusOption} style={{ height: '100%' }} />
                  </div>
                </DataCard>
                <DataCard header={<h3 className="text-sm font-semibold text-slate-200">采集源状态详情</h3>}>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                    {NEWS_SOURCE_STATUS.map(status => (
                      <div key={status.source} className="flex items-center justify-between p-2 bg-[#0e1629] rounded-lg">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${
                            status.status === 'connected' ? 'bg-green-500' : status.status === 'error' ? 'bg-red-500' : 'bg-slate-500'
                          }`} />
                          <span className="text-xs text-slate-300">{status.source}</span>
                        </div>
                        <div className="flex items-center gap-4 text-xs">
                          <span className="text-slate-500">
                            今日: <span className="text-[#c9a84c]">{status.todayCount}</span>
                          </span>
                          <span className="text-slate-500">
                            延迟: <span className={status.latency < 100 ? 'text-green-400' : status.latency < 150 ? 'text-yellow-400' : 'text-red-400'}>{status.latency}ms</span>
                          </span>
                          <span className="text-slate-500">{status.lastUpdate}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </DataCard>
              </div>
            )}
          </div>

          {/* ─── Right: Sidebar ─── */}
          {activeTab !== 'source' && (
            <div className="col-span-4 space-y-3">
              {/* Importance Distribution */}
              <DataCard header={<h3 className="text-[13px] font-semibold text-slate-200">重要性分布</h3>}>
                <div style={{ height: 180 }}>
                  <ReactECharts option={importanceDistOption} style={{ height: '100%' }} />
                </div>
              </DataCard>

              {/* Risk Warnings */}
              <DataCard header={<h3 className="text-[13px] font-semibold text-slate-200 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-orange-400" />风险预警</h3>}>
                <div className="space-y-2 max-h-[200px] overflow-y-auto custom-scrollbar pr-1">
                  {MOCK_NEWS.filter(n => n.riskWarning !== null).map(news => (
                    <div key={news.id} className="p-2 bg-orange-500/5 rounded-lg border border-orange-500/10">
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-400">
                          {news.riskWarning!.level}
                        </span>
                        <span className="text-[10px] text-slate-500">{news.riskWarning!.riskType}</span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-1">{news.riskWarning!.description}</p>
                      <p className="text-[10px] text-orange-400 mt-1">{news.riskWarning!.suggestedAction}</p>
                    </div>
                  ))}
                </div>
              </DataCard>

              {/* Top Suggestions */}
              <DataCard header={<h3 className="text-[13px] font-semibold text-slate-200 flex items-center gap-2"><Target className="w-4 h-4 text-[#c9a84c]" />高置信度建议</h3>}>
                <div className="space-y-2 max-h-[250px] overflow-y-auto custom-scrollbar pr-1">
                  {MOCK_NEWS
                    .filter(n => n.suggestion !== null)
                    .sort((a, b) => (b.suggestion?.confidence ?? 0) - (a.suggestion?.confidence ?? 0))
                    .slice(0, 5)
                    .map(news => (
                      <div key={news.id} className="p-2 bg-[#0e1629] rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-slate-300 line-clamp-1 flex-1">{news.title.replace(/【.*?】/g, '')}</span>
                          <span className="text-xs font-bold ml-2" style={{ color: getSuggestionColor(news.suggestion!.type) }}>
                            {news.suggestion!.confidence}%
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                          <span>{news.suggestion!.type}</span>
                          <span>·</span>
                          <span>仓位{news.suggestion!.suggestedPosition}%</span>
                          <span>·</span>
                          <span>{news.suggestion!.holdingPeriod}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </DataCard>

              {/* Related Sectors */}
              <DataCard header={<h3 className="text-[13px] font-semibold text-slate-200">热门关联板块</h3>}>
                <div className="flex flex-wrap gap-1.5">
                  {Array.from(new Set(MOCK_NEWS.flatMap(n => n.relatedSectors))).map(sector => {
                    const count = MOCK_NEWS.filter(n => n.relatedSectors.includes(sector)).length;
                    const hasPositive = MOCK_NEWS.some(n => n.relatedSectors.includes(sector) && (n.importance === '重大利好' || n.importance === '一般利好'));
                    return (
                      <span key={sector} className={`text-xs px-2 py-1 rounded ${
                        hasPositive ? 'bg-red-500/10 text-red-400' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {sector} ({count})
                      </span>
                    );
                  })}
                </div>
              </DataCard>
            </div>
          )}
        </div>
      </div>
  );
}
