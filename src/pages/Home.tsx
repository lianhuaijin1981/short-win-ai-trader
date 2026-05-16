import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
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
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import ScoreRing from '@/components/ScoreRing';
import MetricBadge from '@/components/MetricBadge';
import StockRow from '@/components/StockRow';
import AlertTicker from '@/components/AlertTicker';
import DataStatusBar from '@/components/DataStatusBar';
import {
  marketIndices,
  marketBreadth,
  sentimentData,
  topStocks,
  yingyouRecommends,
  todayTactics,
  moduleCards,
  alertMessages,
  dataStatus,
  type MarketIndex,
} from '@/data/mockData';
import { cn } from '@/lib/utils';

const moduleIconMap: Record<string, React.ElementType> = {
  Activity, Eye, Fingerprint, Target, BarChart3, ClipboardCheck, Newspaper,
};

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

// ── Section 1: Market Overview ──────────────────────────────────
function MarketOverview() {
  const [indices, setIndices] = useState<MarketIndex[]>(marketIndices);

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

  const totalStocks = marketBreadth.upCount + marketBreadth.downCount;
  const upPercent = (marketBreadth.upCount / totalStocks) * 100;
  const downPercent = (marketBreadth.downCount / totalStocks) * 100;
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ x: -30, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number, number, number, number], delay: 0.1 }}
      className="col-span-12 h-[100px] bg-[#0d1526] rounded-[10px] border border-[rgba(148,163,184,0.1)] flex items-center gap-6 px-6 relative overflow-hidden hover:border-[rgba(201,168,76,0.3)] transition-colors duration-200"
    >
      {/* Gold left accent */}
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-gradient-to-b from-[#c9a84c] via-[#e0c878] to-[#c9a84c]" />

      {/* Indices */}
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

      {/* Divider */}
      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      {/* Breadth bar */}
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
          <span className="text-[#ef4444]">{marketBreadth.upCount}</span>
          <span className="text-[#22c55e]">{marketBreadth.downCount}</span>
        </div>
      </div>

      {/* Divider */}
      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      {/* Limit up/down */}
      <div className="flex flex-col gap-1 min-w-[80px]">
        <span className="text-[11px] text-[#475569]">涨停/跌停</span>
        <div className="flex items-center gap-2">
          <span className="text-[18px] font-mono font-semibold text-[#ef4444]">{marketBreadth.limitUp}</span>
          <span className="text-[#475569]">/</span>
          <span className="text-[18px] font-mono font-semibold text-[#22c55e]">{marketBreadth.limitDown}</span>
        </div>
      </div>

      {/* Divider */}
      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      {/* Sentiment */}
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

      {/* Divider */}
      <div className="w-px h-12 bg-[rgba(148,163,184,0.1)]" />

      {/* Volume */}
      <div className="flex flex-col gap-0.5 min-w-[100px]">
        <span className="text-[11px] text-[#475569]">成交额</span>
        <span className="text-[18px] font-mono font-semibold text-[#f1f5f9]">
          <AnimatedNumber value={marketBreadth.volume} decimals={0} />亿
        </span>
      </div>
    </motion.div>
  );
}

// ── Section 2: Top 5 Scoring ────────────────────────────────────
function Top5Section() {
  const navigate = useNavigate();

  return (
    <div className="col-span-12 lg:col-span-6">
      <DataCard
        delay={400}
        header={
          <div className="flex items-center justify-between w-full">
            <h2 className="text-[20px] font-semibold text-[#f1f5f9] font-orbitron tracking-wide">综合评分 Top5</h2>
            <button
              onClick={() => navigate('/scoring')}
              className="text-[12px] text-[#c9a84c] hover:underline flex items-center gap-1 transition-colors"
            >
              查看全部 <ArrowRight size={14} />
            </button>
          </div>
        }
        className="min-h-[380px]"
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
    </div>
  );
}

// ── Section 3: Yingyou Recommendations ──────────────────────────
function YingyouSection() {
  return (
    <div className="col-span-12 lg:col-span-3">
      <DataCard
        delay={600}
        header={
          <div className="flex items-center justify-between w-full">
            <h2 className="text-[20px] font-semibold text-[#f1f5f9]">游资推荐</h2>
            <button className="p-1 rounded hover:bg-[#141e33] transition-colors group/refresh">
              <RefreshCw size={16} className="text-[#475569] group-hover/refresh:text-[#c9a84c] transition-all duration-300 group-hover/refresh:rotate-180" />
            </button>
          </div>
        }
      >
        <div className="flex flex-col gap-3">
          {yingyouRecommends.map((rec, i) => (
            <motion.div
              key={rec.name}
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{
                duration: 0.5,
                delay: (1100 + i * 150) / 1000,
                ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
              }}
              className={cn(
                'p-3 rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929]',
                'hover:border-[rgba(201,168,76,0.5)] hover:shadow-glow-gold hover:-translate-y-0.5',
                'transition-all duration-200 cursor-pointer'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[14px] font-medium text-[#c9a84c]">{rec.name}</span>
                <span className="text-[12px] font-mono text-[#94a3b8]">{rec.matchPercent}%</span>
              </div>

              {/* Match bar */}
              <div className="h-1.5 bg-[#141e33] rounded-full overflow-hidden mb-2">
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

              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[13px] text-[#f1f5f9]">{rec.stockName}</span>
                <span className="text-[11px] font-mono text-[#475569]">{rec.stockCode}</span>
              </div>

              <div className="flex flex-wrap gap-1 mb-1.5">
                {rec.tactics.map((t) => (
                  <span key={t} className="px-1.5 py-0.5 rounded-full text-[10px] border border-[#8b5cf6]/40 text-[#8b5cf6] bg-[#8b5cf6]/10">
                    {t}
                  </span>
                ))}
              </div>

              <p className="text-[11px] text-[#475569] leading-snug">{rec.reason}</p>
            </motion.div>
          ))}
        </div>
      </DataCard>
    </div>
  );
}

// ── Section 4: Today's Tactics ──────────────────────────────────
function TacticsSection() {
  return (
    <div className="col-span-12 lg:col-span-3">
      <DataCard
        delay={700}
        header={
          <div className="flex items-center justify-between w-full">
            <h2 className="text-[20px] font-semibold text-[#f1f5f9]">今日战法</h2>
            <div className="flex items-center gap-1.5 text-[#475569]">
              <Calendar size={14} />
              <span className="text-[11px] font-mono">
                {new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })}
              </span>
            </div>
          </div>
        }
      >
        <div className="flex flex-col gap-3">
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
              className="p-2.5 rounded-lg hover:bg-[#141e33] transition-colors duration-200 cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[14px] font-medium text-[#8b5cf6] group-hover:text-[#a78bfa] transition-colors">
                  {tactic.name}
                </span>
                <span className="text-[12px] font-mono text-[#94a3b8]">触发: {tactic.triggerCount}次</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[11px] text-[#475569]">近5日成功率: {tactic.successRate}%</span>
                {/* Mini bar chart */}
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
    </div>
  );
}

// ── Section 5: Module Quick Access ──────────────────────────────
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
                'flex flex-col items-center justify-center gap-2 py-5 px-3',
                'bg-[#0d1526] rounded-[10px] border border-[rgba(148,163,184,0.1)]',
                'hover:border-[rgba(201,168,76,0.5)] hover:shadow-glow-gold',
                'transition-all duration-200 group'
              )}
            >
              <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-[#141e33] group-hover:bg-[#c9a84c]/10 transition-colors duration-200">
                <Icon
                  size={24}
                  className="text-[#c9a84c] group-hover:scale-110 transition-transform duration-200"
                />
              </div>
              <span className="text-[13px] text-[#f1f5f9] font-medium">{mod.name}</span>
              <span className="text-[10px] text-[#475569] text-center leading-tight line-clamp-1">{mod.description}</span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

// ── Main Home Page ──────────────────────────────────────────────
export default function Home() {
  return (
    <div className="space-y-4">
      {/* Grid layout */}
      <div className="grid grid-cols-12 gap-4">
        {/* Row 1: Market Overview */}
        <MarketOverview />

        {/* Row 2: Top5 + Yingyou + Tactics */}
        <Top5Section />
        <YingyouSection />
        <TacticsSection />

        {/* Row 3: Module Cards */}
        <ModuleCards />
      </div>

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
