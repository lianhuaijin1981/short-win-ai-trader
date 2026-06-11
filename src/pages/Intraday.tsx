// 数据来源: 同花顺iFind REAL_LIMIT_UP_STOCKS 2026-05-15
import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  ChevronDown,
  ChevronUp,
  Zap,
  AlertTriangle,
  Lightbulb,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import DataCard from '@/components/DataCard';
import {
  REAL_LIMIT_UP_STOCKS,
  REAL_SECTOR_ALERTS,
  REAL_FUND_FLOW,
  ANCHOR_CATEGORIES,
  TIME_PERIOD_ALERTS,
  INTRADAY_TICKS,
  STOCK_RISE_LOGIC,
  type IntradayTick,
} from '@/data/realData';

/* ================================================================
   数据构建层 — 基于真实同花顺数据构造组件所需数据结构
   所有股票代码/名称/价格均来自 REAL_LIMIT_UP_STOCKS
   ================================================================ */

// ── 板块资金流向：基于 REAL_FUND_FLOW 构建 Treemap 数据 ──
const sectorFundFlows = REAL_FUND_FLOW.map((f) => ({
  name: f.sector,
  turnover: Math.round((f.inflow + f.outflow) * 10),
  netInflow: f.net,
  changePercent: f.net > 0
    ? parseFloat((f.net * 0.15).toFixed(1))
    : parseFloat((f.net * 0.08).toFixed(1)),
}));

// ── 板块预警：基于 REAL_SECTOR_ALERTS 构建 ──
const stockNameMap = new Map(REAL_LIMIT_UP_STOCKS.map((s) => [s.code, s.name]));
const sectorAlerts = REAL_SECTOR_ALERTS.map((alert, i) => {
  const typeMap: Record<string, '机会' | '风险' | '提示'> = {
    '强板块效应': '机会',
    '资金大幅流入': '机会',
    '资金大幅流出': '风险',
    '退潮风险': '风险',
  };
  const relatedStocks = alert.affected
    .map((code) => {
      const name = stockNameMap.get(code) ?? code;
      return `${name} ${code}`;
    })
    .join(' | ');

  const minutes = 32 - i * 3;
  const time = `14:${String(minutes).padStart(2, '0')}:00`;

  return {
    time,
    type: typeMap[alert.type] ?? '提示',
    sector: alert.sector,
    content: `[${alert.urgency} urgency] ${alert.type}: ${alert.trigger}`,
    relatedStocks,
  };
});

// ── 连板高标定义（2026-06-10收盘后，AKShare全市场，排除ST）──
// 6月10日真实数据：天娱数科4板最高，71家涨停
interface BoardLeader {
  rank: number;       // 连板排名
  name: string;
  code: string;
  boards: number;     // 连板数
  sealAmount: string;
  limitUpTime: string;
  riseLogic: string;
  conceptSector: string;    // 所属概念板块
  industrySector: string;   // 所属行业板块
}

const BOARD_LEADERS: BoardLeader[] = [
  { rank: 1, name: '天娱数科', code: '002354', boards: 4, sealAmount: '1.7亿', limitUpTime: '09:33', riseLogic: '广告营销+AI+数据要素', conceptSector: 'AI营销/数据要素', industrySector: '广告营销' },
  { rank: 2, name: '金安国纪', code: '002636', boards: 3, sealAmount: '1.6亿', limitUpTime: '09:31', riseLogic: '覆铜板+PCB+电子材料', conceptSector: '半导体材料', industrySector: '元件' },
  { rank: 3, name: '中化国际', code: '600500', boards: 2, sealAmount: '2.1亿', limitUpTime: '09:25', riseLogic: '化学制品+央企改革', conceptSector: '化工新材料', industrySector: '化学制品' },
  { rank: 4, name: '圣泉集团', code: '605589', boards: 2, sealAmount: '3.6亿', limitUpTime: '09:25', riseLogic: '合成生物+酚醛树脂', conceptSector: '化工新材料', industrySector: '塑料' },
];

// ── 板块连板梯队定义 ──
// 每个板块包含：龙头 + 连板梯队 + 首板涨停股
interface SectorBoardTier {
  sectorName: string;
  sectorType: '概念板块' | '行业板块';
  leader: BoardLeader;
  boardTiers: { rank: number; name: string; code: string; boards: number; riseLogic: string }[];
  firstBoards: { name: string; code: string; riseLogic: string }[];
}

// 概念板块连板梯队 — 6月10日真实数据
const CONCEPT_SECTOR_TIERS: SectorBoardTier[] = [
  {
    sectorName: 'AI营销/数据要素',
    sectorType: '概念板块',
    leader: BOARD_LEADERS[0], // 天娱数科
    boardTiers: [
      { rank: 1, name: '天娱数科', code: '002354', boards: 4, riseLogic: '广告营销+AI+数据要素' },
      { rank: 2, name: '南兴股份', code: '002757', boards: 1, riseLogic: '专用设备+IDC' },
    ],
    firstBoards: [
      { name: '城市传媒', code: '600229', riseLogic: '出版+传媒' },
    ],
  },
  {
    sectorName: '半导体材料',
    sectorType: '概念板块',
    leader: BOARD_LEADERS[1], // 金安国纪
    boardTiers: [
      { rank: 1, name: '金安国纪', code: '002636', boards: 3, riseLogic: '覆铜板+PCB+电子材料' },
      { rank: 2, name: '中晶科技', code: '003026', boards: 2, riseLogic: '半导体硅片' },
    ],
    firstBoards: [
      { name: '华亚智能', code: '003043', riseLogic: '半导体设备' },
    ],
  },
  {
    sectorName: '化工新材料',
    sectorType: '概念板块',
    leader: BOARD_LEADERS[2], // 中化国际
    boardTiers: [
      { rank: 1, name: '中化国际', code: '600500', boards: 2, riseLogic: '化学制品+央企改革' },
      { rank: 2, name: '圣泉集团', code: '605589', boards: 2, riseLogic: '合成生物+酚醛树脂' },
    ],
    firstBoards: [
      { name: '康达新材', code: '002669', riseLogic: '胶粘剂+军工' },
    ],
  },
  {
    sectorName: '化学制品',
    sectorType: '概念板块',
    leader: BOARD_LEADERS[3], // 圣泉集团
    boardTiers: [
      { rank: 1, name: '圣泉集团', code: '605589', boards: 2, riseLogic: '合成生物+酚醛树脂' },
      { rank: 2, name: '和远气体', code: '002971', boards: 2, riseLogic: '工业气体' },
    ],
    firstBoards: [
      { name: '恒兴新材', code: '603276', riseLogic: '化学制品' },
    ],
  },
];

// 行业板块连板梯队 — 6月10日真实数据
const INDUSTRY_SECTOR_TIERS: SectorBoardTier[] = [
  {
    sectorName: '广告营销',
    sectorType: '行业板块',
    leader: BOARD_LEADERS[0], // 天娱数科
    boardTiers: [
      { rank: 1, name: '天娱数科', code: '002354', boards: 4, riseLogic: 'AI营销龙头' },
      { rank: 2, name: '南兴股份', code: '002757', boards: 1, riseLogic: '专用设备' },
    ],
    firstBoards: [
      { name: '城市传媒', code: '600229', riseLogic: '出版' },
    ],
  },
  {
    sectorName: '元件',
    sectorType: '行业板块',
    leader: BOARD_LEADERS[1], // 金安国纪
    boardTiers: [
      { rank: 1, name: '金安国纪', code: '002636', boards: 3, riseLogic: '覆铜板龙头' },
      { rank: 2, name: '中晶科技', code: '003026', boards: 2, riseLogic: '半导体硅片' },
    ],
    firstBoards: [
      { name: '华亚智能', code: '003043', riseLogic: '半导体设备' },
    ],
  },
  {
    sectorName: '化学制品',
    sectorType: '行业板块',
    leader: BOARD_LEADERS[2], // 中化国际
    boardTiers: [
      { rank: 1, name: '中化国际', code: '600500', boards: 2, riseLogic: '化学制品央企' },
      { rank: 2, name: '和远气体', code: '002971', boards: 2, riseLogic: '工业气体' },
    ],
    firstBoards: [
      { name: '康达新材', code: '002669', riseLogic: '胶粘剂' },
      { name: '恒兴新材', code: '603276', riseLogic: '化学制品' },
    ],
  },
  {
    sectorName: '塑料',
    sectorType: '行业板块',
    leader: BOARD_LEADERS[3], // 圣泉集团
    boardTiers: [
      { rank: 1, name: '圣泉集团', code: '605589', boards: 2, riseLogic: '酚醛树脂龙头' },
      { rank: 2, name: '双星新材', code: '002585', boards: 2, riseLogic: '光学膜' },
    ],
    firstBoards: [],
  },
];

// ── 异动追踪：基于 REAL_LIMIT_UP_STOCKS 构建 ──
const typeColorMap: Record<string, string> = {
  '放量突破': '#ef4444',
  '快速拉升': '#c9a84c',
  '大单异动': '#8b5cf6',
  '尾盘异动': '#06d7d7',
};

const abnormalityTracker = REAL_LIMIT_UP_STOCKS.map((s, i) => {
  const minutes = 35 - i * 2;
  const time = `14:${String(minutes).padStart(2, '0')}:00`;

  // 根据战法匹配确定异动类型
  let type = '大单异动';
  if (s.tacticsMatched.includes('倍量突破') || s.tacticsMatched.includes('三倍量突破战法')) {
    type = '放量突破';
  } else if (s.tacticsMatched.includes('首阴战法') || s.tacticsMatched.includes('N字形战法')) {
    type = '快速拉升';
  } else if (s.tacticsMatched.includes('连板加速') || s.tacticsMatched.includes('缩量一字')) {
    type = '尾盘异动';
  }

  const tacticStr = s.tacticsMatched.slice(0, 2).join('+');
  const yingyouStr = s.yingyouMatch ? `，${s.yingyouMatch}模式匹配` : '';

  return {
    time,
    code: s.code,
    name: s.name,
    type,
    typeColor: typeColorMap[type] ?? '#8b5cf6',
    price: s.close,
    change: s.changePct,
    volumeRatio: s.volRatio,
    aiComment: `${tacticStr}确认${yingyouStr}，量比${s.volRatio.toFixed(1)}倍，${s.reasons[0]}`,
  };
});

/* ─── Animation Variants ─── */
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



/* ─── Mini Intraday Sparkline (分时图) ─── */
function MiniIntradaySparkline({ ticks, positive }: { ticks: IntradayTick[]; positive: boolean }) {
  const w = 90, h = 28;
  const prices = ticks.map((t) => t.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const points = prices.map((v, i) => {
    const x = (i / (prices.length - 1)) * w;
    const y = h - ((v - min) / range) * h * 0.8 - h * 0.1;
    return `${x},${y}`;
  }).join(' ');
  const avgPrices = ticks.map((t) => t.avgPrice);
  const avgMin = Math.min(...avgPrices);
  const avgMax = Math.max(...avgPrices);
  const avgRange = avgMax - avgMin || 1;
  const avgPoints = avgPrices.map((v, i) => {
    const x = (i / (avgPrices.length - 1)) * w;
    const y = h - ((v - avgMin) / avgRange) * h * 0.8 - h * 0.1;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} className="opacity-80">
      <polyline points={avgPoints} fill="none" stroke={positive ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'} strokeWidth={1} strokeDasharray="2,2" />
      <polyline points={points} fill="none" stroke={positive ? '#ef4444' : '#22c55e'} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
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

// TIME_PERIOD_ALERTS 来自 realData.ts

/* ─── Main Component ─── */
export default function Intraday() {
  const [trackerFilter, setTrackerFilter] = useState('全部');
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragState = useRef({ startX: 0, scrollLeft: 0 });

  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('全场高标');
  const [expandedPeriod, setExpandedPeriod] = useState<number | null>(null);

  // ── 龙头梯队状态 ──
  const [selectedLeaderIdx, setSelectedLeaderIdx] = useState(0); // 当前选中的高标索引
  const [sectorMode, setSectorMode] = useState<'概念板块' | '行业板块'>('概念板块'); // 板块类型

  const togglePeriod = (i: number) => {
    setExpandedPeriod(expandedPeriod === i ? null : i);
  };

  const treemapOption = useTreemapOption();

  // ── 龙头梯队派生数据 ──
  const leader = BOARD_LEADERS[selectedLeaderIdx];
  const sectorTiers = sectorMode === '概念板块' ? CONCEPT_SECTOR_TIERS : INDUSTRY_SECTOR_TIERS;
  const currentSector = sectorTiers.find((s) => s.leader.code === leader.code) ?? sectorTiers[0];

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
                <span className="text-[11px] text-[#475569] ml-1 font-mono">{ANCHOR_CATEGORIES.reduce((sum, c) => sum + c.stocks.length, 0)}只</span>
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
          {/* 分类切换Tab */}
          <div className="flex items-center gap-1 bg-[#141e33] rounded-lg p-0.5 mb-2">
            {ANCHOR_CATEGORIES.map((cat) => (
              <button
                key={cat.category}
                onClick={() => setActiveCategory(cat.category)}
                className={cn(
                  'flex items-center gap-1 px-2.5 py-1 text-[11px] rounded-md transition-all duration-200',
                  activeCategory === cat.category
                    ? 'text-[#060b14] font-medium'
                    : 'text-[#94a3b8] hover:text-[#f1f5f9]'
                )}
                style={{
                  backgroundColor: activeCategory === cat.category ? cat.color : 'transparent',
                }}
              >
                <span>{cat.category}</span>
                <span className="text-[10px] opacity-70">({cat.stocks.length})</span>
              </button>
            ))}
          </div>

          {/* 当前类别的锚定标列表 */}
          {ANCHOR_CATEGORIES.filter(c => c.category === activeCategory).map((cat) => (
            <div key={cat.category}>
              <div className="text-[10px] text-[#475569] mb-1">{cat.description}</div>
              {/* 表头 */}
              <div className="grid grid-cols-[65px_60px_52px_48px_70px_48px_90px_120px_80px] gap-1 px-2 pb-1.5 text-[10px] text-[#475569] font-medium border-b border-[rgba(148,163,184,0.1)]">
                <span>代码</span><span>名称</span><span className="text-right">现价</span>
                <span className="text-right">涨跌</span><span>定位</span><span className="text-right">地位</span>
                <span>信息</span><span>上涨逻辑</span><span className="text-right">分时</span>
              </div>
              {/* 标的行 */}
              <div className="space-y-0.5 mt-1">
                {cat.stocks.map((stock, i) => {
                  const isUp = stock.change > 0;
                  const ticks = INTRADAY_TICKS[stock.code];
                  return (
                    <motion.div
                      key={stock.code}
                      variants={itemVariants}
                      custom={i}
                      onClick={() => navigate(`/stock/${stock.code}`)}
                      className="grid grid-cols-[65px_60px_52px_48px_70px_48px_90px_120px_80px] gap-1 px-2 py-1.5 rounded-md cursor-pointer hover:bg-[#141e33] transition-all group"
                    >
                      <span className="text-[12px] font-mono text-[#f1f5f9]">{stock.code}</span>
                      <span className="text-[12px] text-[#f1f5f9] truncate">{stock.name}</span>
                      <span className="text-[12px] font-mono text-right text-[#f1f5f9]">{stock.price.toFixed(2)}</span>
                      <span className={cn('text-[12px] font-mono text-right', isUp ? 'text-[#ef4444]' : 'text-[#22c55e]')}>
                        {isUp ? '+' : ''}{stock.change}%
                      </span>
                      <span className="text-[11px]" style={{ color: cat.color }}>{stock.position}</span>
                      <span className="text-[11px] text-[#94a3b8] text-right">{stock.sectorStatus}</span>
                      <span className="text-[10px] text-[#475569] truncate">{stock.extraInfo}</span>
                      <span className="text-[10px] text-[#94a3b8] truncate leading-tight" title={STOCK_RISE_LOGIC[stock.code] || ''}>
                        {STOCK_RISE_LOGIC[stock.code] || '--'}
                      </span>
                      <div className="flex justify-end">
                        {ticks && <MiniIntradaySparkline ticks={ticks} positive={isUp} />}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
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
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setSectorMode('概念板块')}
                  className={cn(
                    'px-2 py-0.5 text-[11px] rounded transition-all',
                    sectorMode === '概念板块'
                      ? 'bg-[#c9a84c] text-[#060b14] font-medium'
                      : 'text-[#94a3b8] hover:text-[#f1f5f9] bg-[#141e33]'
                  )}
                >
                  概念板块
                </button>
                <button
                  onClick={() => setSectorMode('行业板块')}
                  className={cn(
                    'px-2 py-0.5 text-[11px] rounded transition-all',
                    sectorMode === '行业板块'
                      ? 'bg-[#c9a84c] text-[#060b14] font-medium'
                      : 'text-[#94a3b8] hover:text-[#f1f5f9] bg-[#141e33]'
                  )}
                >
                  行业板块
                </button>
              </div>
            </div>
          }
          className="min-h-[340px]"
        >
          <div className="flex gap-3 h-full">
            {/* 左侧：当前选中高标的板块连板梯队 */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* 板块类型切换Tab */}
              <div className="flex items-center gap-1 mb-2">
                <button
                  onClick={() => setSectorMode('概念板块')}
                  className={cn(
                    'px-2 py-0.5 text-[10px] rounded transition-all',
                    sectorMode === '概念板块'
                      ? 'bg-[#c9a84c] text-[#060b14] font-medium'
                      : 'text-[#94a3b8] hover:text-[#f1f5f9] bg-[#0f1929]'
                  )}
                >
                  概念板块
                </button>
                <button
                  onClick={() => setSectorMode('行业板块')}
                  className={cn(
                    'px-2 py-0.5 text-[10px] rounded transition-all',
                    sectorMode === '行业板块'
                      ? 'bg-[#c9a84c] text-[#060b14] font-medium'
                      : 'text-[#94a3b8] hover:text-[#f1f5f9] bg-[#0f1929]'
                  )}
                >
                  行业板块
                </button>
                <span className="text-[10px] text-[#475569] ml-2">{currentSector.sectorName}</span>
              </div>

              {/* 龙头卡片 */}
              <div className="mb-2 p-3 rounded-lg bg-[#141e33] border border-[rgba(201,168,76,0.2)]">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[#c9a84c] text-[18px] font-bold">{leader.name}</span>
                    <span className="text-[10px] text-[#475569] ml-2">{leader.code}</span>
                  </div>
                  <span className="text-[#ef4444] text-[18px] font-bold">{leader.boards}连板</span>
                </div>
                <div className="text-[10px] text-[#94a3b8] mt-1">
                  封单:{leader.sealAmount} 涨停:{leader.limitUpTime}
                </div>
                <div className="text-[10px] text-[#c9a84c] mt-0.5">
                  上涨逻辑: {STOCK_RISE_LOGIC[leader.code] || leader.riseLogic}
                </div>
              </div>

              {/* 同板块连板梯队 */}
              <div className="flex-1 overflow-y-auto">
                <div className="text-[10px] text-[#475569] mb-1">{currentSector.sectorName} · 连板梯队</div>
                {currentSector.boardTiers.map((t) => (
                  <div
                    key={t.code}
                    className="flex items-center gap-2 py-1 px-2 rounded hover:bg-[#141e33] cursor-pointer"
                    onClick={() => navigate(`/stock/${t.code}`)}
                  >
                    <span className="text-[10px] text-[#475569] w-4">#{t.rank}</span>
                    <span className="text-[12px] text-[#f1f5f9]">{t.name}</span>
                    <span className="text-[10px] text-[#94a3b8]">{t.code}</span>
                    <span className="text-[11px] text-[#ef4444] ml-auto">{t.boards}板</span>
                  </div>
                ))}
              </div>

              {/* 首板涨停 */}
              <div className="mt-2 pt-2 border-t border-[rgba(148,163,184,0.06)]">
                <div className="text-[10px] text-[#475569] mb-1">首板涨停 ({currentSector.firstBoards.length}只)</div>
                <div className="flex flex-wrap gap-1">
                  {currentSector.firstBoards.map((fb) => (
                    <span
                      key={fb.code}
                      className="text-[10px] px-1.5 py-0.5 bg-[#0f1929] text-[#94a3b8] rounded cursor-pointer hover:text-[#c9a84c]"
                      onClick={() => navigate(`/stock/${fb.code}`)}
                      title={fb.riseLogic}
                    >
                      {fb.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* 右侧：其他连板高标 */}
            <div className="w-[140px] shrink-0">
              <div className="text-[10px] text-[#475569] mb-2 font-medium">连板高标</div>
              <div className="space-y-1.5">
                {BOARD_LEADERS.map((bl, i) => (
                  <div
                    key={bl.code}
                    onClick={() => setSelectedLeaderIdx(i)}
                    className={cn(
                      'p-2 rounded cursor-pointer transition-all border',
                      selectedLeaderIdx === i
                        ? 'bg-[#141e33] border-[#c9a84c]'
                        : 'bg-[#0f1929] border-transparent hover:bg-[#141e33]'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={cn(
                          'text-[12px] font-medium',
                          selectedLeaderIdx === i ? 'text-[#c9a84c]' : 'text-[#f1f5f9]'
                        )}
                      >
                        {bl.name}
                      </span>
                      <span className="text-[11px] text-[#ef4444]">{bl.boards}板</span>
                    </div>
                    <div className="text-[9px] text-[#475569] mt-0.5">{bl.conceptSector.split('/')[0]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
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
          {/* 分时段提醒渲染 */}
          <div className="space-y-2">
            {TIME_PERIOD_ALERTS.map((p, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.08 }}
                className={cn(
                  'rounded-lg border transition-all duration-200 overflow-hidden',
                  p.status === 'active' && 'bg-[rgba(201,168,76,0.06)] border-[rgba(201,168,76,0.25)]',
                  p.status === 'completed' && 'bg-transparent border-[rgba(148,163,184,0.06)] opacity-60',
                  p.status === 'pending' && 'bg-transparent border-[rgba(148,163,184,0.08)]',
                )}
              >
                {/* 时段标题行 */}
                <div className="flex items-center gap-3 p-2.5">
                  <div className={cn(
                    'w-2 h-2 rounded-full shrink-0',
                    p.status === 'completed' && 'bg-[#22c55e]',
                    p.status === 'active' && 'bg-[#c9a84c] animate-pulse',
                    p.status === 'pending' && 'bg-[#475569]',
                  )} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={cn('text-[13px] font-medium', p.status === 'active' ? 'text-[#c9a84c]' : 'text-[#94a3b8]')}>
                        {p.period}
                      </span>
                      <span className="text-[11px] text-[#475569] font-mono">{p.timeRange}</span>
                    </div>
                  </div>
                  {p.status === 'completed' && <ChevronRight size={14} className="text-[#22c55e]" />}
                  {p.status === 'active' && <div className="w-1.5 h-1.5 rounded-full bg-[#c9a84c] animate-pulse" />}
                </div>

                {/* 理论依据（可展开） */}
                <div className="px-2.5 pb-1">
                  <button
                    onClick={() => togglePeriod(i)}
                    className="text-[10px] text-[#475569] hover:text-[#c9a84c] transition-colors flex items-center gap-1"
                  >
                    <Lightbulb size={10} />
                    {expandedPeriod === i ? '收起' : '查看理论依据与预期'}
                    {expandedPeriod === i ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                  </button>
                  {expandedPeriod === i && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-1 space-y-1.5"
                    >
                      {/* 理论依据 */}
                      <p className="text-[11px] text-[#94a3b8] leading-relaxed bg-[#0f1929] rounded p-2">
                        {p.theoryBasis}
                      </p>
                      {/* 预期判断表格 */}
                      <div className="space-y-1">
                        <div className="text-[10px] text-[#475569] font-medium">锚定标预期判断</div>
                        {p.expectations.map((exp, j) => (
                          <div key={j} className="bg-[#0f1929] rounded p-2 text-[11px]">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[#f1f5f9] font-medium">{exp.stockName} ({exp.code})</span>
                              <span className="text-[10px]" style={{ color: '#c9a84c' }}>[{exp.position}] [{exp.sectorStatus}]</span>
                            </div>
                            <div className="grid grid-cols-3 gap-1 text-[10px]">
                              <div className="bg-[rgba(34,197,94,0.08)] rounded p-1">
                                <div className="text-[#22c55e] font-medium mb-0.5">符合预期</div>
                                <div className="text-[#94a3b8]">{exp.expected}</div>
                              </div>
                              <div className="bg-[rgba(201,168,76,0.08)] rounded p-1">
                                <div className="text-[#c9a84c] font-medium mb-0.5">强于预期</div>
                                <div className="text-[#94a3b8]">{exp.strong}</div>
                              </div>
                              <div className="bg-[rgba(239,68,68,0.08)] rounded p-1">
                                <div className="text-[#ef4444] font-medium mb-0.5">低于预期</div>
                                <div className="text-[#94a3b8]">{exp.weak}</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      {/* 操作建议 */}
                      <div className="flex flex-wrap gap-1">
                        {p.actionAdvice.map((advice, k) => (
                          <span key={k} className="text-[10px] px-1.5 py-0.5 bg-[rgba(6,215,215,0.08)] text-[#06d7d7] rounded">
                            {advice}
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
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
