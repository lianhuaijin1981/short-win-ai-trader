import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowUp, ArrowDown, TrendingUp, TrendingDown, BarChart3, Layers, Hash, DollarSign, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMemo } from 'react';

/* ─── Types ─── */
export interface DayHistoryData {
  date: string;
  score: number;
  phase: string;
  limitUp: number;
  limitDown: number;
  upCount: number;
  downCount: number;
  medianChange: number;
  northBound: number;
  volumeRatio: number;
  leadSectors: { name: string; changePct: number; stocks: number }[];
  lagSectors: { name: string; changePct: number; stocks: number }[];
  leadStocks: { code: string; name: string; changePct: number; sector: string }[];
  lagStocks: { code: string; name: string; changePct: number; sector: string }[];
}

interface Props {
  open: boolean;
  onClose: () => void;
  dayData: DayHistoryData | null;
  period: '7日' | '14日' | '30日';
}

/* ─── Phase color helper ─── */
const phaseColor = (phase: string) => {
  switch (phase) {
    case '混沌期': return '#6b7280';
    case '启动期': return '#3b82f6';
    case '发酵期': return '#06d7d7';
    case '高潮期': return '#c9a84c';
    case '分歧期': return '#f97316';
    case '退潮期': return '#ef4444';
    default: return '#6b7280';
  }
};

const scoreColor = (score: number) => {
  if (score >= 80) return '#c9a84c';
  if (score >= 60) return '#06d7d7';
  if (score >= 40) return '#3b82f6';
  if (score >= 20) return '#f97316';
  return '#ef4444';
};

/* ─── Mini stat card ─── */
function StatCard({ label, value, icon: Icon, accent }: { label: string; value: string; icon: React.ComponentType<{ size?: number; className?: string }>; accent: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.08)] px-3 py-2.5">
      <div className="flex items-center justify-center w-7 h-7 rounded-md" style={{ backgroundColor: `${accent}15` }}>
        <span style={{ color: accent }}><Icon size={14} /></span>
      </div>
      <div>
        <div className="text-[10px] text-[#475569] leading-none mb-1">{label}</div>
        <div className="text-[13px] font-semibold font-mono text-[#f1f5f9] leading-none">{value}</div>
      </div>
    </div>
  );
}

/* ─── Sort indicator ─── */
function SortBadge({ period }: { period: '7日' | '14日' | '30日' }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-[#c9a84c]/10 text-[#c9a84c] font-mono ml-2">
      按{period}排序
    </span>
  );
}

/* ─── Table Row ─── */
function TableRow({ children, index, highlight }: { children: React.ReactNode; index: number; highlight?: boolean }) {
  return (
    <div
      className={cn(
        'grid items-center gap-2 px-3 py-2 text-[12px] border-b border-[rgba(148,163,184,0.06)] transition-colors',
        index % 2 === 0 ? 'bg-[#0a0f1a]/50' : 'bg-transparent',
        highlight && 'bg-[#c9a84c]/5'
      )}
    >
      {children}
    </div>
  );
}

/* ─── Main Component ─── */
export default function DayDetailModal({ open, onClose, dayData, period }: Props) {
  if (!dayData) return null;

  const { date, score, phase, limitUp, limitDown, upCount, downCount, medianChange, northBound, volumeRatio, leadSectors, lagSectors, leadStocks, lagStocks } = dayData;

  /* Sort stocks by changePct for display (simulating period-based sort) */
  const sortedLeadStocks = useMemo(() => {
    return [...leadStocks].sort((a, b) => b.changePct - a.changePct);
  }, [leadStocks]);

  const sortedLagStocks = useMemo(() => {
    return [...lagStocks].sort((a, b) => a.changePct - b.changePct);
  }, [lagStocks]);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-0" showCloseButton={false}>
        {/* Custom close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 w-7 h-7 rounded-md bg-[#0f1929] border border-[rgba(148,163,184,0.1)] flex items-center justify-center text-[#475569] hover:text-[#f1f5f9] hover:border-[rgba(201,168,76,0.3)] transition-all"
        >
          <span className="sr-only">Close</span>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
        </button>

        {/* ── Header ─── */}
        <DialogHeader className="px-5 pt-5 pb-4 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-4">
            {/* Date & Score */}
            <div className="flex items-center gap-3">
              <div>
                <DialogTitle className="text-[20px] font-bold text-[#f1f5f9] font-mono">{date}</DialogTitle>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="text-[12px] px-1.5 py-0.5 rounded font-medium" style={{ backgroundColor: `${phaseColor(phase)}20`, color: phaseColor(phase) }}>
                    {phase}
                  </span>
                  <span className="text-[11px] text-[#475569]">情绪综合得分</span>
                </div>
              </div>
            </div>

            {/* Score ring */}
            <div className="flex items-center gap-2 ml-auto">
              <div className="relative w-[52px] h-[52px] flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="22" fill="none" stroke="#0f1929" strokeWidth="4" />
                  <circle
                    cx="26" cy="26" r="22" fill="none"
                    stroke={scoreColor(score)}
                    strokeWidth="4"
                    strokeDasharray={`${(score / 100) * 138.23} 138.23`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="text-[16px] font-bold font-mono" style={{ color: scoreColor(score) }}>{score}</span>
              </div>
            </div>
          </div>

          {/* ── Stat Grid ─── */}
          <div className="grid grid-cols-4 gap-2 mt-4">
            <StatCard label="涨停" value={`${limitUp}家`} icon={TrendingUp} accent="#ef4444" />
            <StatCard label="跌停" value={`${limitDown}家`} icon={TrendingDown} accent="#22c55e" />
            <StatCard label="涨跌中位" value={`${medianChange > 0 ? '+' : ''}${medianChange}%`} icon={BarChart3} accent={medianChange >= 0 ? '#ef4444' : '#22c55e'} />
            <StatCard label="北向资金" value={`${northBound > 0 ? '+' : ''}${northBound}亿`} icon={DollarSign} accent={northBound >= 0 ? '#ef4444' : '#22c55e'} />
          </div>
          <div className="grid grid-cols-4 gap-2 mt-2">
            <StatCard label="上涨家数" value={`${upCount.toLocaleString()}`} icon={ArrowUp} accent="#ef4444" />
            <StatCard label="下跌家数" value={`${downCount.toLocaleString()}`} icon={ArrowDown} accent="#22c55e" />
            <StatCard label="量能维持" value={`${volumeRatio}%`} icon={Activity} accent="#c9a84c" />
            <StatCard label="涨跌比" value={`${upCount > 0 && downCount > 0 ? (upCount / downCount).toFixed(2) : '—'}`} icon={Hash} accent="#3b82f6" />
          </div>
        </DialogHeader>

        {/* ── Tabs ─── */}
        <div className="px-5 pt-4 pb-5">
          <Tabs defaultValue="leadSectors" className="w-full">
            <TabsList className="w-full grid grid-cols-4 bg-[#0f1929] border border-[rgba(148,163,184,0.08)] h-9">
              <TabsTrigger value="leadSectors" className="text-[11px] data-[state=active]:bg-[#c9a84c] data-[state=active]:text-[#060b14] data-[state=active]:font-semibold text-[#475569]">
                <ArrowUp size={12} className="mr-1" />领涨板块
              </TabsTrigger>
              <TabsTrigger value="lagSectors" className="text-[11px] data-[state=active]:bg-[#c9a84c] data-[state=active]:text-[#060b14] data-[state=active]:font-semibold text-[#475569]">
                <ArrowDown size={12} className="mr-1" />领跌板块
              </TabsTrigger>
              <TabsTrigger value="leadStocks" className="text-[11px] data-[state=active]:bg-[#c9a84c] data-[state=active]:text-[#060b14] data-[state=active]:font-semibold text-[#475569]">
                <TrendingUp size={12} className="mr-1" />领涨个股
              </TabsTrigger>
              <TabsTrigger value="lagStocks" className="text-[11px] data-[state=active]:bg-[#c9a84c] data-[state=active]:text-[#060b14] data-[state=active]:font-semibold text-[#475569]">
                <TrendingDown size={12} className="mr-1" />领跌个股
              </TabsTrigger>
            </TabsList>

            {/* ── Lead Sectors Tab ─── */}
            <TabsContent value="leadSectors" className="mt-3">
              <div className="rounded-lg border border-[rgba(148,163,184,0.08)] overflow-hidden">
                {/* Header */}
                <div className="grid grid-cols-[50px_1fr_80px_80px] gap-2 px-3 py-2 bg-[#0f1929] text-[11px] font-medium text-[#475569] border-b border-[rgba(148,163,184,0.1)]">
                  <span>排名</span>
                  <span>板块名称</span>
                  <span className="text-right">涨跌幅</span>
                  <span className="text-right">涨停家数</span>
                </div>
                {leadSectors.length === 0 ? (
                  <div className="px-3 py-8 text-center text-[12px] text-[#475569]">当日无领涨板块数据</div>
                ) : (
                  leadSectors.map((s, i) => (
                    <TableRow key={s.name} index={i} highlight={i < 3}>
                      <span className="text-[12px] font-mono w-[50px]" style={{ color: i === 0 ? '#c9a84c' : i === 1 ? '#94a3b8' : i === 2 ? '#b45309' : '#475569' }}>
                        {i + 1}
                      </span>
                      <span className="text-[12px] text-[#f1f5f9] font-medium">{s.name}</span>
                      <span className="text-[12px] font-mono text-right text-[#ef4444]">+{s.changePct.toFixed(1)}%</span>
                      <span className="text-[12px] font-mono text-right text-[#ef4444]">{s.stocks}家</span>
                    </TableRow>
                  ))
                )}
              </div>
            </TabsContent>

            {/* ── Lag Sectors Tab ─── */}
            <TabsContent value="lagSectors" className="mt-3">
              <div className="rounded-lg border border-[rgba(148,163,184,0.08)] overflow-hidden">
                <div className="grid grid-cols-[50px_1fr_80px_80px] gap-2 px-3 py-2 bg-[#0f1929] text-[11px] font-medium text-[#475569] border-b border-[rgba(148,163,184,0.1)]">
                  <span>排名</span>
                  <span>板块名称</span>
                  <span className="text-right">涨跌幅</span>
                  <span className="text-right">下跌家数</span>
                </div>
                {lagSectors.length === 0 ? (
                  <div className="px-3 py-8 text-center text-[12px] text-[#475569]">当日无领跌板块数据</div>
                ) : (
                  lagSectors.map((s, i) => (
                    <TableRow key={s.name} index={i} highlight={i < 3}>
                      <span className="text-[12px] font-mono w-[50px]" style={{ color: i === 0 ? '#c9a84c' : i === 1 ? '#94a3b8' : i === 2 ? '#b45309' : '#475569' }}>
                        {i + 1}
                      </span>
                      <span className="text-[12px] text-[#f1f5f9] font-medium">{s.name}</span>
                      <span className="text-[12px] font-mono text-right text-[#22c55e]">{s.changePct.toFixed(1)}%</span>
                      <span className="text-[12px] font-mono text-right text-[#22c55e]">{s.stocks}家</span>
                    </TableRow>
                  ))
                )}
              </div>
            </TabsContent>

            {/* ── Lead Stocks Tab ─── */}
            <TabsContent value="leadStocks" className="mt-3">
              <div className="rounded-lg border border-[rgba(148,163,184,0.08)] overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2 bg-[#0f1929] border-b border-[rgba(148,163,184,0.1)]">
                  <div className="grid grid-cols-[50px_1fr_90px_80px_80px] gap-2 text-[11px] font-medium text-[#475569] flex-1">
                    <span>排名</span>
                    <span>个股</span>
                    <span>所属板块</span>
                    <span className="text-right">涨幅</span>
                    <span className="text-right">代码</span>
                  </div>
                </div>
                <div className="px-3 py-1.5 bg-[#c9a84c]/5 border-b border-[rgba(148,163,184,0.06)]">
                  <SortBadge period={period} />
                </div>
                {sortedLeadStocks.length === 0 ? (
                  <div className="px-3 py-8 text-center text-[12px] text-[#475569]">当日无领涨个股数据</div>
                ) : (
                  sortedLeadStocks.map((s, i) => (
                    <TableRow key={s.code} index={i} highlight={i < 3}>
                      <span className="text-[12px] font-mono w-[50px]" style={{ color: i === 0 ? '#c9a84c' : i === 1 ? '#94a3b8' : i === 2 ? '#b45309' : '#475569' }}>
                        {i + 1}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <Layers size={12} className="text-[#475569] shrink-0" />
                        <span className="text-[12px] text-[#f1f5f9] font-medium">{s.name}</span>
                      </div>
                      <span className="text-[11px] text-[#475569]">{s.sector}</span>
                      <span className="text-[12px] font-mono text-right text-[#ef4444]">+{s.changePct.toFixed(1)}%</span>
                      <span className="text-[11px] font-mono text-right text-[#475569]">{s.code}</span>
                    </TableRow>
                  ))
                )}
              </div>
            </TabsContent>

            {/* ── Lag Stocks Tab ─── */}
            <TabsContent value="lagStocks" className="mt-3">
              <div className="rounded-lg border border-[rgba(148,163,184,0.08)] overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2 bg-[#0f1929] border-b border-[rgba(148,163,184,0.1)]">
                  <div className="grid grid-cols-[50px_1fr_90px_80px_80px] gap-2 text-[11px] font-medium text-[#475569] flex-1">
                    <span>排名</span>
                    <span>个股</span>
                    <span>所属板块</span>
                    <span className="text-right">跌幅</span>
                    <span className="text-right">代码</span>
                  </div>
                </div>
                <div className="px-3 py-1.5 bg-[#c9a84c]/5 border-b border-[rgba(148,163,184,0.06)]">
                  <SortBadge period={period} />
                </div>
                {sortedLagStocks.length === 0 ? (
                  <div className="px-3 py-8 text-center text-[12px] text-[#475569]">当日无领跌个股数据</div>
                ) : (
                  sortedLagStocks.map((s, i) => (
                    <TableRow key={s.code} index={i} highlight={i < 3}>
                      <span className="text-[12px] font-mono w-[50px]" style={{ color: i === 0 ? '#c9a84c' : i === 1 ? '#94a3b8' : i === 2 ? '#b45309' : '#475569' }}>
                        {i + 1}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <Layers size={12} className="text-[#475569] shrink-0" />
                        <span className="text-[12px] text-[#f1f5f9] font-medium">{s.name}</span>
                      </div>
                      <span className="text-[11px] text-[#475569]">{s.sector}</span>
                      <span className="text-[12px] font-mono text-right text-[#22c55e]">{s.changePct.toFixed(1)}%</span>
                      <span className="text-[11px] font-mono text-right text-[#475569]">{s.code}</span>
                    </TableRow>
                  ))
                )}
              </div>
            </TabsContent>
          </Tabs>

          {/* ── Click hint ─── */}
          <div className="mt-4 pt-3 border-t border-[rgba(148,163,184,0.06)] text-center">
            <span className="text-[10px] text-[#475569]">点击图表其他日期查看不同日期的详细数据</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
