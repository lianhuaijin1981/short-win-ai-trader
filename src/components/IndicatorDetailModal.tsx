import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import ReactECharts from 'echarts-for-react';
import { TrendingUp, TrendingDown, Minus, Calculator, BarChart3, List } from 'lucide-react';

/* ─── Types ─── */
interface Indicator {
  name: string;
  value: string;
  status: 'good' | 'neutral' | 'warning';
  desc: string;
  sparkline: number[];
}

interface IndicatorDetailModalProps {
  open: boolean;
  onClose: () => void;
  indicator: Indicator | null;
}

/* ─── 14个指标定义 ─── */
const INDICATOR_DEFINITIONS: Record<string, { formula: string; desc: string; relatedStocks: { code: string; name: string; value: string }[] }> = {
  '涨跌停家数比': {
    formula: '涨停家数 / (涨停家数 + 跌停家数) × 100%',
    desc: '反映市场做多情绪强度，>70%为强势，<40%为弱势',
    relatedStocks: [
      { code: '001259', name: '利仁科技', value: '涨停' },
      { code: '001333', name: '光华股份', value: '涨停' },
      { code: '002031', name: '巨轮智能', value: '涨停' },
      { code: '002066', name: '瑞泰科技', value: '涨停' },
      { code: '002181', name: '粤传媒', value: '涨停' },
    ],
  },
  '连板高度': {
    formula: '当日最高连板数（自然板），盘中实时更新',
    desc: '反映市场接力意愿。6板以上为极强，4-5板为强，2-3板为中等',
    relatedStocks: [
      { code: '002918', name: '蒙娜丽莎', value: '6连板(全市场最高)' },
      { code: '001259', name: '利仁科技', value: '5连板' },
      { code: '600578', name: '京能电力', value: '3连板' },
      { code: '603779', name: '威龙股份', value: '3连板' },
    ],
  },
  '炸板率': {
    formula: '炸板数 / (涨停数 + 炸板数) × 100%',
    desc: '反映封板质量，>30%为差，<15%为优',
    relatedStocks: [
      { code: '001259', name: '利仁科技', value: '封板' },
      { code: '002196', name: '方正电机', value: '封板' },
      { code: '002348', name: '高乐股份', value: '封板' },
      { code: '002374', name: '中锐股份', value: '封板' },
    ],
  },
  '跌停家数': {
    formula: '当日跌停家数（含曾跌停）',
    desc: '反映恐慌情绪，>20家为恐慌，<5家为平稳',
    relatedStocks: [],
  },
  '涨跌中位数': {
    formula: '全部A股涨跌幅的中位数',
    desc: '反映市场整体涨跌，>+1%为强，<-1%为弱',
    relatedStocks: [],
  },
  '连板晋级率': {
    formula: '连板成功数 / 昨日连板数 × 100%，盘中实时更新',
    desc: '反映接力成功率。100%=全部晋级(极强)，>60%为优，<30%为差。昨(05-14)3只非ST连板全部晋级',
    relatedStocks: [
      { code: '002918', name: '蒙娜丽莎', value: '05-14为5连板→05-15续6板' },
      { code: '001259', name: '利仁科技', value: '05-14为4连板→05-15续5板' },
      { code: '600578', name: '京能电力', value: '05-14为2连板→05-15续3板' },
    ],
  },
  '昨涨停今表现': {
    formula: '昨日(05-14)涨停股今日(05-15)涨跌幅中位数',
    desc: '反映打板次日溢价。中位数-1.4%(33跌/18涨/7续板)，多数打板资金亏损',
    relatedStocks: [
      { code: '001259', name: '利仁科技', value: '+10.0%(续板)' },
      { code: '002918', name: '蒙娜丽莎', value: '+9.98%(续板)' },
      { code: '600578', name: '京能电力', value: '+10.05%(续板)' },
    ],
  },
  '昨连板今表现': {
    formula: '昨日(05-14)连续涨停≥2天股票今日(05-15盘中)平均涨跌幅',
    desc: '反映连板高标溢价强度。>+5%为极强(全部续板)，>0%为强，<0%为弱。基于盘中实时价格计算。昨连板=上一交易日(05-14)收盘时连续涨停≥2天的非ST股票',
    relatedStocks: [
      { code: '002918', name: '蒙娜丽莎', value: '+9.98%(05-14为5连板→05-15续6板)' },
      { code: '001259', name: '利仁科技', value: '+10.00%(05-14为4连板→05-15续5板)' },
      { code: '600578', name: '京能电力', value: '+10.05%(05-14为2连板→05-15续3板)' },
    ],
  },
  '高标溢价': {
    formula: '前日最高板今日(盘中)涨跌幅',
    desc: '反映龙头溢价。>+5%为极强(全部续板)，>+3%为优，<0%为弱。昨(05-14)最高板为蒙娜丽莎5板',
    relatedStocks: [
      { code: '002918', name: '蒙娜丽莎', value: '+9.98%(05-14为5板最高标→05-15续6板)' },
      { code: '001259', name: '利仁科技', value: '+10.00%(05-14为4板→05-15续5板)' },
      { code: '600578', name: '京能电力', value: '+10.05%(05-14为2板→05-15续3板)' },
    ],
  },
  '题材集中度': {
    formula: 'TOP3题材涨停数 / 总涨停数 × 100%',
    desc: '反映题材聚焦度，>50%为集中，<30%为分散',
    relatedStocks: [
      { code: '001259', name: '利仁科技', value: '消费电子' },
      { code: '001333', name: '光华股份', value: '化工' },
      { code: '002031', name: '巨轮智能', value: '机器人' },
    ],
  },
  '量能维持率': {
    formula: '今日成交额 / 5日均额 × 100%',
    desc: '反映资金活跃度，>80%为健康',
    relatedStocks: [],
  },
  '封单强度': {
    formula: '封单金额 / 流通市值 × 10000（单位:万分比），盘中实时',
    desc: '反映封板坚决度。3只连板全部封死为极强，>50为强，<20为弱',
    relatedStocks: [
      { code: '002918', name: '蒙娜丽莎', value: '6板封死(05-14为5板)' },
      { code: '001259', name: '利仁科技', value: '5板封死(05-14为4板)' },
      { code: '600578', name: '京能电力', value: '3板封死(05-14为2板)' },
    ],
  },
  '指数联动': {
    formula: '三大指数同向涨跌幅的加权平均',
    desc: '反映指数一致性，>80为高度一致',
    relatedStocks: [],
  },
  '北向资金': {
    formula: '当日北向资金净流入（亿元）',
    desc: '反映外资情绪，>+50亿为积极，<-30亿为消极',
    relatedStocks: [],
  },
  '恐慌指数': {
    formula: '(跌停数×3 + 跌幅>7%家数×2 + 跌幅>5%家数) / 总交易家数 × 100',
    desc: '综合恐慌指标，>40为中度恐慌，>70为极度恐慌',
    relatedStocks: [],
  },
};

/* ─── Helpers ─── */
const statusDotColor = (status: string): string => {
  switch (status) {
    case 'good': return '#22c55e';
    case 'neutral': return '#eab308';
    case 'warning': return '#ef4444';
    default: return '#6b7280';
  }
};

const statusTextColor = (status: string): string => {
  switch (status) {
    case 'good': return '#22c55e';
    case 'neutral': return '#eab308';
    case 'warning': return '#ef4444';
    default: return '#6b7280';
  }
};

const statusLabel = (status: string): string => {
  switch (status) {
    case 'good': return '积极';
    case 'neutral': return '中性';
    case 'warning': return '警示';
    default: return '未知';
  }
};

const TrendIcon = ({ status }: { status: string }) => {
  if (status === 'good') return <TrendingUp size={16} className="text-[#22c55e]" />;
  if (status === 'warning') return <TrendingDown size={16} className="text-[#ef4444]" />;
  return <Minus size={16} className="text-[#eab308]" />;
};

/* ─── Component ─── */
export default function IndicatorDetailModal({ open, onClose, indicator }: IndicatorDetailModalProps) {
  if (!indicator) return null;

  const def = INDICATOR_DEFINITIONS[indicator.name];
  const color = statusDotColor(indicator.status);
  const sColor = statusTextColor(indicator.status);

  /* 5日走势图配置 */
  const sparklineOption = {
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: '#1a2744',
      borderColor: 'rgba(148,163,184,0.1)',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
      formatter: (params: Array<{ axisValue: string; value: number; dataIndex: number }>) => {
        const idx = params[0].dataIndex;
        const dayLabels = ['T-4', 'T-3', 'T-2', 'T-1', '今日'];
        return `<div style="font-size:11px;color:#94a3b8">${dayLabels[idx]}</div>
                <div style="color:${color};font-weight:bold">${params[0].value}</div>`;
      },
    },
    grid: { top: 20, right: 15, bottom: 25, left: 15 },
    xAxis: {
      type: 'category' as const,
      data: ['T-4', 'T-3', 'T-2', 'T-1', '今日'],
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
      axisLabel: { color: '#475569', fontSize: 10, fontFamily: 'JetBrains Mono' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value' as const,
      axisLine: { show: false },
      axisLabel: { show: false },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.05)' } },
    },
    series: [
      {
        type: 'line',
        data: indicator.sparkline,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 2.5,
          color: color,
        },
        itemStyle: {
          color: color,
          borderColor: '#0d1526',
          borderWidth: 2,
        },
        areaStyle: {
          color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: color + '30' },
              { offset: 1, color: color + '05' },
            ],
          },
        },
        animationDuration: 800,
        animationEasing: 'cubicOut' as const,
      },
    ],
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="bg-[#0d1526] border-[rgba(148,163,184,0.1)] max-w-2xl max-h-[80vh] overflow-y-auto p-0 gap-0">
        {/* Header */}
        <DialogHeader className="p-5 pb-0">
          <DialogTitle className="text-[#f1f5f9] flex items-center gap-3 text-[18px]">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}60` }}
            />
            {indicator.name}
            <span
              className="text-[11px] px-2 py-0.5 rounded-full ml-auto"
              style={{
                backgroundColor: sColor + '20',
                color: sColor,
                border: `1px solid ${sColor}30`,
              }}
            >
              {statusLabel(indicator.status)}
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="p-5 space-y-4">
          {/* 当前值 */}
          <div className="text-center py-3 rounded-xl bg-[#0f1929] border border-[rgba(148,163,184,0.06)]">
            <div className="flex items-center justify-center gap-2 mb-1">
              <TrendIcon status={indicator.status} />
              <span className="text-[11px] text-[#475569] tracking-wide">当前值</span>
            </div>
            <span
              className="text-[36px] font-bold font-mono tracking-tight"
              style={{ color: sColor, textShadow: `0 0 20px ${sColor}30` }}
            >
              {indicator.value}
            </span>
            <div className="text-[11px] text-[#475569] mt-1">{indicator.desc}</div>
          </div>

          {/* 计算公式 */}
          {def && (
            <div className="rounded-xl bg-[#0f1929] border border-[rgba(148,163,184,0.06)] overflow-hidden">
              <div className="flex items-center gap-2 px-4 pt-3 pb-2">
                <Calculator size={13} className="text-[#c9a84c]" />
                <span className="text-[12px] text-[#475569] font-medium">计算公式</span>
              </div>
              <div className="px-4 pb-2">
                <code className="text-[13px] text-[#c9a84c] font-mono bg-[#0d1526] px-3 py-2 rounded-lg block border border-[rgba(201,168,76,0.1)]">
                  {def.formula}
                </code>
              </div>
              <div className="px-4 pb-3">
                <p className="text-[11px] text-[#94a3b8] leading-relaxed">
                  <span className="text-[#475569]">解读：</span>
                  {def.desc}
                </p>
              </div>
            </div>
          )}

          {/* 5日走势图 */}
          <div className="rounded-xl bg-[#0f1929] border border-[rgba(148,163,184,0.06)] overflow-hidden">
            <div className="flex items-center gap-2 px-4 pt-3 pb-1">
              <BarChart3 size={13} className="text-[#c9a84c]" />
              <span className="text-[12px] text-[#475569] font-medium">5日走势</span>
            </div>
            <ReactECharts option={sparklineOption} style={{ height: 180 }} />
          </div>

          {/* 相关个股 */}
          {def && def.relatedStocks.length > 0 && (
            <div className="rounded-xl bg-[#0f1929] border border-[rgba(148,163,184,0.06)] overflow-hidden">
              <div className="flex items-center gap-2 px-4 pt-3 pb-2">
                <List size={13} className="text-[#c9a84c]" />
                <span className="text-[12px] text-[#475569] font-medium">相关个股</span>
              </div>
              <div className="px-4 pb-3">
                <table className="w-full">
                  <thead>
                    <tr className="text-[11px] text-[#475569] border-b border-[rgba(148,163,184,0.08)]">
                      <th className="text-left py-2 font-medium w-[80px]">代码</th>
                      <th className="text-left py-2 font-medium">名称</th>
                      <th className="text-right py-2 font-medium">指标值</th>
                    </tr>
                  </thead>
                  <tbody>
                    {def.relatedStocks.map((stock) => (
                      <tr
                        key={stock.code}
                        className="border-b border-[rgba(148,163,184,0.04)] last:border-b-0 hover:bg-[rgba(148,163,184,0.03)] transition-colors cursor-pointer"
                      >
                        <td className="py-2.5 text-[12px] text-[#94a3b8] font-mono">{stock.code}</td>
                        <td className="py-2.5 text-[13px] text-[#f1f5f9]">{stock.name}</td>
                        <td className="py-2.5 text-right">
                          <span
                            className="text-[12px] font-medium px-2 py-0.5 rounded"
                            style={{
                              backgroundColor: indicator.status === 'good' ? 'rgba(34,197,94,0.12)' : indicator.status === 'warning' ? 'rgba(239,68,68,0.12)' : 'rgba(234,179,8,0.12)',
                              color: indicator.status === 'good' ? '#22c55e' : indicator.status === 'warning' ? '#ef4444' : '#eab308',
                            }}
                          >
                            {stock.value}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
