import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  DollarSign,
  MessageSquare,
  AlertTriangle,
  Clock,
  Target,
  Zap,
  Eye,
  Layers,
  Download,
  Camera,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TradeRecord } from '@/data/tradeData';
import { useTradeRecords } from '@/hooks/useTradeStorage';
import type { FullDiagnosisReport, DiagnosisContext } from '@/types/diagnosis';
import { runFullDiagnosis } from '@/services/diagnosisEngine';
import DiagnosisReport from '@/components/DiagnosisReport';

// ── 工具函数 ───────────────────────────────────────────────────
const formatNumber = (n: number) => n.toLocaleString('zh-CN');
const formatPercent = (n: number) => `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;

// ── 模拟数据生成器 ─────────────────────────────────────────────
const generateMockEnvironment = (trade: TradeRecord) => {
  const tradeDate = trade.tradeDate;
  const tradeTime = trade.tradeTime;

  return {
    // 一、单笔交易基础信息
    tradeInfo: {
      ...trade,
      timeSlot: getTimeSlot(trade.tradeTime),
      orderChain: {
        orderTime: trade.tradeTime,
        matchTime: trade.tradeTime,
        cancelRecords: trade.cancelRecords || [],
        matchStatus: trade.matchStatus,
      },
    },
    // 二、大盘宏观环境
    marketEnv: {
      indices: [
        { name: '上证指数', code: 'SH000001', value: 3285.67, change: -15.23, changePercent: -0.46, volume: 2856 },
        { name: '深证成指', code: 'SZ399001', value: 10532.45, change: -85.67, changePercent: -0.81, volume: 3567 },
        { name: '创业板指', code: 'SZ399006', value: 2156.89, change: -12.34, changePercent: -0.57, volume: 1234 },
        { name: '沪深300', code: 'SH000300', value: 3856.23, change: -18.45, changePercent: -0.48, volume: 1567 },
        { name: '中证500', code: 'SH000905', value: 5678.90, change: -25.67, changePercent: -0.45, volume: 987 },
        { name: '科创50', code: 'SH000688', value: 987.65, change: -5.43, changePercent: -0.55, volume: 456 },
      ],
      marketBreadth: {
        upCount: 1856,
        downCount: 3245,
        limitUp: 45,
        limitDown: 12,
       炸板: 8,
        totalVolume: 8567,
        moneyEffect: 35,
      },
      northFlow: {
        netInflow: -25.67,
        trend: '流出',
        shFlow: -15.23,
        szFlow: -10.44,
      },
      trendContext: {
        daily: '震荡',
        weekly: '下行',
        monthly: '震荡上行',
        marketPhase: '震荡市',
      },
    },
    // 三、板块题材环境
    sectorEnv: {
      industry: {
        name: getSectorForStock(trade.stockCode),
        value: 2567.89,
        changePercent: -0.35,
        volume: 456,
      },
      concept: {
        name: getConceptForStock(trade.stockCode),
        value: 1234.56,
        changePercent: 1.25,
        volume: 234,
      },
      hotThemes: [
        { name: 'AI应用', changePercent: 3.56, leader: 'XXX科技', height: 5 },
        { name: '半导体', changePercent: 2.34, leader: 'YYY微', height: 3 },
        { name: '新能源', changePercent: -1.23, leader: 'ZZZ能源', height: 2 },
        { name: '医药', changePercent: 0.89, leader: 'AAA制药', height: 2 },
        { name: '消费', changePercent: -0.56, leader: 'BBB食品', height: 1 },
      ],
      sectorLeader: {
        name: '板块龙头',
        code: '000001',
        changePercent: 9.98,
        isLimitUp: true,
      },
    },
    // 四、个股盘面
    stockPanel: {
      basic: {
        open: trade.tradePrice * 0.98,
        high: trade.tradePrice * 1.05,
        low: trade.tradePrice * 0.95,
        turnover: 5.67,
        volumeRatio: 2.34,
        amplitude: 8.56,
        floatMarketCap: 156.78,
      },
      indicators: {
        ma5: trade.tradePrice * 0.97,
        ma10: trade.tradePrice * 0.95,
        ma20: trade.tradePrice * 0.92,
        macd: { dif: 0.23, dea: 0.18, macd: 0.10 },
        kdj: { k: 65.4, d: 58.2, j: 79.8 },
        boll: { upper: trade.tradePrice * 1.08, mid: trade.tradePrice, lower: trade.tradePrice * 0.92 },
      },
      orderBook: {
        bids: [
          { price: trade.tradePrice - 0.01, volume: 156 },
          { price: trade.tradePrice - 0.02, volume: 234 },
          { price: trade.tradePrice - 0.03, volume: 345 },
          { price: trade.tradePrice - 0.04, volume: 123 },
          { price: trade.tradePrice - 0.05, volume: 567 },
        ],
        asks: [
          { price: trade.tradePrice + 0.01, volume: 234 },
          { price: trade.tradePrice + 0.02, volume: 345 },
          { price: trade.tradePrice + 0.03, volume: 123 },
          { price: trade.tradePrice + 0.04, volume: 456 },
          { price: trade.tradePrice + 0.05, volume: 234 },
        ],
      },
    },
    // 五、资金博弈
    fundFlow: {
      superLarge: { inflow: 1234, outflow: 2345, net: -1111 },
      large: { inflow: 2345, outflow: 1234, net: 1111 },
      medium: { inflow: 3456, outflow: 2345, net: 1111 },
      small: { inflow: 4567, outflow: 3456, net: 1111 },
      chipDistribution: {
        profitRatio: 35.6,
        lossRatio: 64.4,
        concentration: 45.6,
        peakPrice: trade.tradePrice * 0.95,
      },
    },
    // 六、消息面
    newsEnv: {
      companyNews: [
        { time: tradeDate, title: `${trade.stockName}发布最新公告`, type: '公告' },
        { time: tradeDate, title: '行业政策利好', type: '利好' },
      ],
      marketSentiment: {
        heat: 75,
        bullishRatio: 45,
        bearishRatio: 55,
      },
    },
    // 七、智能诊断
    diagnosis: {
      timing: '上涨中途',
      riskLevel: '中',
      risks: ['大盘震荡', '板块分化'],
      stockStatus: '跟风上涨',
      score: 65,
      suggestions: [
        '当前处于大盘震荡期，个股跟风上涨',
        '建议控制仓位，设置止损位',
        '关注板块龙头走势，判断是否独立行情',
      ],
    },
  };
};

const getTimeSlot = (time: string): string => {
  const hour = new Date(time).getHours();
  if (hour < 9.5) return '集合竞价';
  if (hour < 11.5) return '早盘';
  if (hour < 13) return '午间休息';
  if (hour < 14.5) return '午盘';
  return '尾盘';
};

const getSectorForStock = (_code: string): string => {
  const sectors = ['消费电子', '半导体', '新能源', '医药生物', '计算机', '通信'];
  return sectors[Math.floor(Math.random() * sectors.length)];
};

const getConceptForStock = (_code: string): string => {
  const concepts = ['AI应用', '国产替代', '碳中和', '数字经济', '智能制造'];
  return concepts[Math.floor(Math.random() * concepts.length)];
};

// ── 主组件 ─────────────────────────────────────────────────────
export default function TradeEnvironment() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getRecord } = useTradeRecords();
  const [trade, setTrade] = useState<TradeRecord | null>(null);
  const [env, setEnv] = useState<ReturnType<typeof generateMockEnvironment> | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [viewMode, setViewMode] = useState<'normal' | 'indicator' | 'fund' | 'compare'>('normal');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [diagnosisReport, setDiagnosisReport] = useState<FullDiagnosisReport | null>(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);

  // 执行诊断
  const handleDiagnosis = useCallback(() => {
    if (!trade || !env) return;
    setIsDiagnosing(true);
    
    // 模拟异步加载
    setTimeout(() => {
      const context: DiagnosisContext = {
        trade,
        marketData: {
          indexChange: env.marketEnv.indices[0]?.changePercent,
          marketBreadth: {
            up: env.marketEnv.marketBreadth.upCount,
            down: env.marketEnv.marketBreadth.downCount,
            limitUp: env.marketEnv.marketBreadth.limitUp,
            limitDown: env.marketEnv.marketBreadth.limitDown,
          },
          northFlow: env.marketEnv.northFlow.netInflow,
          totalVolume: env.marketEnv.marketBreadth.totalVolume,
          marketPhase: env.marketEnv.trendContext.marketPhase,
        },
        sectorData: {
          sectorChange: env.sectorEnv.industry.changePercent,
          themeRank: 3,
          isMainTheme: env.sectorEnv.hotThemes.some(t => t.changePercent > 2),
          leaderChange: env.sectorEnv.sectorLeader.changePercent,
        },
        stockData: {
          open: env.stockPanel.basic.open,
          high: env.stockPanel.basic.high,
          low: env.stockPanel.basic.low,
          close: trade.tradePrice,
          turnover: env.stockPanel.basic.turnover,
          volumeRatio: env.stockPanel.basic.volumeRatio,
          amplitude: env.stockPanel.basic.amplitude,
          ma5: env.stockPanel.indicators.ma5,
          ma10: env.stockPanel.indicators.ma10,
          ma20: env.stockPanel.indicators.ma20,
          macd: env.stockPanel.indicators.macd,
          kdj: env.stockPanel.indicators.kdj,
          chipProfit: env.fundFlow.chipDistribution.profitRatio,
          chipConcentration: env.fundFlow.chipDistribution.concentration,
          fundFlow: {
            superLarge: env.fundFlow.superLarge.net,
            large: env.fundFlow.large.net,
            medium: env.fundFlow.medium.net,
            small: env.fundFlow.small.net,
          },
        },
        newsData: {
          hasPositiveNews: env.newsEnv.companyNews.some(n => n.type === '利好'),
          hasNegativeNews: env.newsEnv.companyNews.some(n => n.type === '利空'),
          newsImpact: 'neutral',
        },
        userHistory: {
          totalTrades: 25,
          winRate: 45,
          avgHoldingDays: 8,
          frequentErrors: [],
          tradingStyle: '短线',
        },
      };
      
      const report = runFullDiagnosis(trade, context);
      setDiagnosisReport(report);
      setIsDiagnosing(false);
    }, 500);
  }, [trade, env]);

  useEffect(() => {
    if (id) {
      const record = getRecord(id);
      if (record) {
        setTrade(record);
        setEnv(generateMockEnvironment(record));
      }
    }
  }, [id, getRecord]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      if (trade) {
        setEnv(generateMockEnvironment(trade));
      }
      setIsRefreshing(false);
    }, 1000);
  };

  if (!trade || !env) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0d1526] text-[#94a3b8]">
        <div className="text-center">
          <Activity size={48} className="mx-auto mb-4 text-[#64748b]" />
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: '总览', icon: <Eye size={16} /> },
    { id: 'market', label: '大盘环境', icon: <BarChart3 size={16} /> },
    { id: 'sector', label: '板块题材', icon: <Layers size={16} /> },
    { id: 'stock', label: '个股盘面', icon: <Activity size={16} /> },
    { id: 'fund', label: '资金博弈', icon: <DollarSign size={16} /> },
    { id: 'news', label: '消息面', icon: <MessageSquare size={16} /> },
    { id: 'diagnosis', label: '智能诊断', icon: <Target size={16} /> },
  ];

  return (
    <div className="h-full flex flex-col bg-[#0d1526] text-[#e2e8f0]">
      {/* 顶部导航 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)] bg-[#111827]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/trade-history')}
            className="flex items-center gap-2 text-[#94a3b8] hover:text-[#c9a84c] transition-colors"
          >
            <ArrowLeft size={18} />
            返回
          </button>
          <div>
            <h1 className="text-lg font-bold text-[#c9a84c]">
              {trade.stockName}({trade.stockCode}) - 交易环境重构
            </h1>
            <p className="text-xs text-[#64748b]">
              {trade.tradeTime} | {trade.tradeType === 'buy' ? '买入' : '卖出'} | 价格: {trade.tradePrice.toFixed(2)} | 数量: {trade.tradeVolume}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className={cn(
              'p-2 rounded transition-colors',
              isRefreshing ? 'animate-spin' : 'hover:bg-[#1e293b]'
            )}
          >
            <RefreshCw size={16} className="text-[#94a3b8]" />
          </button>
          <button className="p-2 hover:bg-[#1e293b] rounded transition-colors" title="截图">
            <Camera size={16} className="text-[#94a3b8]" />
          </button>
          <button className="p-2 hover:bg-[#1e293b] rounded transition-colors" title="导出">
            <Download size={16} className="text-[#94a3b8]" />
          </button>
          <div className="flex items-center gap-1 ml-2">
            {(['normal', 'indicator', 'fund', 'compare'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  'px-2 py-1 rounded text-xs transition-colors',
                  viewMode === mode ? 'bg-[#c9a84c] text-[#0d1526]' : 'bg-[#1e293b] text-[#94a3b8] hover:bg-[#334155]'
                )}
              >
                {mode === 'normal' ? '裸盘' : mode === 'indicator' ? '指标' : mode === 'fund' ? '资金' : '对比'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab 导航 */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[rgba(148,163,184,0.1)] bg-[#0f172a] overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded text-sm whitespace-nowrap transition-colors',
              activeTab === tab.id
                ? 'bg-[#1e293b] text-[#c9a84c]'
                : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {activeTab === 'overview' && <OverviewTab env={env} trade={trade} />}
            {activeTab === 'market' && <MarketTab marketEnv={env.marketEnv} />}
            {activeTab === 'sector' && <SectorTab sectorEnv={env.sectorEnv} />}
            {activeTab === 'stock' && <StockTab stockPanel={env.stockPanel} trade={trade} />}
            {activeTab === 'fund' && <FundTab fundFlow={env.fundFlow} />}
            {activeTab === 'news' && <NewsTab newsEnv={env.newsEnv} />}
            {activeTab === 'diagnosis' && (
              <DiagnosisTab 
                diagnosis={env.diagnosis} 
                trade={trade} 
                onRunDiagnosis={handleDiagnosis}
                isDiagnosing={isDiagnosing}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* 诊断报告弹窗 */}
      {diagnosisReport && (
        <DiagnosisReport
          report={diagnosisReport}
          onClose={() => setDiagnosisReport(null)}
        />
      )}
    </div>
  );
}

// ── 总览 Tab ───────────────────────────────────────────────────
function OverviewTab({ env, trade }: { env: ReturnType<typeof generateMockEnvironment>; trade: TradeRecord }) {
  return (
    <div className="space-y-4">
      {/* 交易快照 */}
      <div className="grid grid-cols-4 gap-3">
        <InfoCard title="交易时间" value={trade.tradeTime} icon={<Clock size={16} />} />
        <InfoCard title="交易方向" value={trade.tradeType === 'buy' ? '买入' : '卖出'} icon={<Zap size={16} />} />
        <InfoCard title="成交价格" value={trade.tradePrice.toFixed(2)} icon={<DollarSign size={16} />} />
        <InfoCard title="成交金额" value={`¥${formatNumber(trade.tradeAmount)}`} icon={<BarChart3 size={16} />} />
      </div>

      {/* 大盘概览 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <BarChart3 size={16} />
          大盘快照
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {env.marketEnv.indices.slice(0, 3).map(idx => (
            <div key={idx.code} className="p-2 bg-[#1e293b] rounded">
              <div className="text-xs text-[#64748b]">{idx.name}</div>
              <div className="text-sm font-mono text-[#e2e8f0]">{idx.value.toFixed(2)}</div>
              <div className={cn(
                'text-xs font-mono',
                idx.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
              )}>
                {formatPercent(idx.changePercent)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 市场情绪 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <Activity size={16} />
          市场情绪
        </h3>
        <div className="grid grid-cols-4 gap-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#22c55e]">{env.marketEnv.marketBreadth.upCount}</div>
            <div className="text-xs text-[#64748b]">上涨</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[#ef4444]">{env.marketEnv.marketBreadth.downCount}</div>
            <div className="text-xs text-[#64748b]">下跌</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[#22c55e]">{env.marketEnv.marketBreadth.limitUp}</div>
            <div className="text-xs text-[#64748b]">涨停</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[#ef4444]">{env.marketEnv.marketBreadth.limitDown}</div>
            <div className="text-xs text-[#64748b]">跌停</div>
          </div>
        </div>
      </div>

      {/* 诊断摘要 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <Target size={16} />
          智能诊断摘要
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-2 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">买卖时机</div>
            <div className="text-sm text-[#e2e8f0]">{env.diagnosis.timing}</div>
          </div>
          <div className="p-2 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">风险等级</div>
            <div className="text-sm text-[#ef4444]">{env.diagnosis.riskLevel}</div>
          </div>
          <div className="p-2 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">个股状态</div>
            <div className="text-sm text-[#e2e8f0]">{env.diagnosis.stockStatus}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 大盘环境 Tab ───────────────────────────────────────────────
function MarketTab({ marketEnv }: { marketEnv: ReturnType<typeof generateMockEnvironment>['marketEnv'] }) {
  return (
    <div className="space-y-4">
      {/* 指数快照 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">主流指数快照</h3>
        <div className="grid grid-cols-3 gap-3">
          {marketEnv.indices.map(idx => (
            <div key={idx.code} className="p-3 bg-[#1e293b] rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[#e2e8f0]">{idx.name}</span>
                <span className={cn(
                  'flex items-center gap-1 text-xs',
                  idx.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
                )}>
                  {idx.changePercent >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {formatPercent(idx.changePercent)}
                </span>
              </div>
              <div className="text-lg font-mono text-[#e2e8f0]">{idx.value.toFixed(2)}</div>
              <div className="text-xs text-[#64748b]">成交额: {formatNumber(idx.volume)}亿</div>
            </div>
          ))}
        </div>
      </div>

      {/* 市场宽度 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">市场宽度</h3>
        <div className="grid grid-cols-4 gap-3">
          <StatBox label="上涨家数" value={marketEnv.marketBreadth.upCount} color="text-[#22c55e]" />
          <StatBox label="下跌家数" value={marketEnv.marketBreadth.downCount} color="text-[#ef4444]" />
          <StatBox label="涨停" value={marketEnv.marketBreadth.limitUp} color="text-[#22c55e]" />
          <StatBox label="跌停" value={marketEnv.marketBreadth.limitDown} color="text-[#ef4444]" />
          <StatBox label="炸板" value={marketEnv.marketBreadth.炸板} color="text-[#f59e0b]" />
          <StatBox label="两市成交" value={`${formatNumber(marketEnv.marketBreadth.totalVolume)}亿`} color="text-[#e2e8f0]" />
          <StatBox label="赚钱效应" value={`${marketEnv.marketBreadth.moneyEffect}分`} color="text-[#f59e0b]" />
          <StatBox label="大环境" value={marketEnv.trendContext.marketPhase} color="text-[#e2e8f0]" />
        </div>
      </div>

      {/* 北向资金 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">北向资金</h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">净流入/出</div>
            <div className={cn(
              'text-lg font-mono',
              marketEnv.northFlow.netInflow >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
            )}>
              {marketEnv.northFlow.netInflow >= 0 ? '+' : ''}{marketEnv.northFlow.netInflow}亿
            </div>
          </div>
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">沪股通</div>
            <div className="text-lg font-mono text-[#e2e8f0]">{marketEnv.northFlow.shFlow}亿</div>
          </div>
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b]">深股通</div>
            <div className="text-lg font-mono text-[#e2e8f0]">{marketEnv.northFlow.szFlow}亿</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 板块题材 Tab ───────────────────────────────────────────────
function SectorTab({ sectorEnv }: { sectorEnv: ReturnType<typeof generateMockEnvironment>['sectorEnv'] }) {
  return (
    <div className="space-y-4">
      {/* 所属板块 */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#c9a84c] mb-2">所属行业</h3>
          <div className="text-lg text-[#e2e8f0]">{sectorEnv.industry.name}</div>
          <div className={cn(
            'text-sm',
            sectorEnv.industry.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
          )}>
            {formatPercent(sectorEnv.industry.changePercent)}
          </div>
        </div>
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#c9a84c] mb-2">所属概念</h3>
          <div className="text-lg text-[#e2e8f0]">{sectorEnv.concept.name}</div>
          <div className={cn(
            'text-sm',
            sectorEnv.concept.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
          )}>
            {formatPercent(sectorEnv.concept.changePercent)}
          </div>
        </div>
      </div>

      {/* 热门题材 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">热门题材排行</h3>
        <div className="space-y-2">
          {sectorEnv.hotThemes.map((theme, i) => (
            <div key={i} className="flex items-center justify-between p-2 bg-[#1e293b] rounded">
              <div className="flex items-center gap-3">
                <span className="text-xs text-[#64748b] w-6">{i + 1}</span>
                <span className="text-sm text-[#e2e8f0]">{theme.name}</span>
                <span className="text-xs text-[#64748b]">龙头: {theme.leader}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-[#64748b]">{theme.height}连板</span>
                <span className={cn(
                  'text-sm font-mono',
                  theme.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
                )}>
                  {formatPercent(theme.changePercent)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 板块龙头 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">板块龙头</h3>
        <div className="flex items-center justify-between p-3 bg-[#1e293b] rounded">
          <div>
            <div className="text-sm text-[#e2e8f0]">{sectorEnv.sectorLeader.name}</div>
            <div className="text-xs text-[#64748b]">{sectorEnv.sectorLeader.code}</div>
          </div>
          <div className={cn(
            'text-lg font-mono',
            sectorEnv.sectorLeader.changePercent >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
          )}>
            {formatPercent(sectorEnv.sectorLeader.changePercent)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 个股盘面 Tab ───────────────────────────────────────────────
function StockTab({ stockPanel, trade }: { stockPanel: ReturnType<typeof generateMockEnvironment>['stockPanel']; trade: TradeRecord }) {
  return (
    <div className="space-y-4">
      {/* 基础数据 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">日内基础数据</h3>
        <div className="grid grid-cols-4 gap-3">
          <StatBox label="开盘价" value={stockPanel.basic.open.toFixed(2)} />
          <StatBox label="最高价" value={stockPanel.basic.high.toFixed(2)} />
          <StatBox label="最低价" value={stockPanel.basic.low.toFixed(2)} />
          <StatBox label="换手率" value={`${stockPanel.basic.turnover}%`} />
          <StatBox label="量比" value={stockPanel.basic.volumeRatio.toFixed(2)} />
          <StatBox label="振幅" value={`${stockPanel.basic.amplitude}%`} />
          <StatBox label="流通市值" value={`${stockPanel.basic.floatMarketCap}亿`} />
          <StatBox label="成交价" value={trade.tradePrice.toFixed(2)} highlight />
        </div>
      </div>

      {/* 技术指标 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">技术指标</h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b] mb-2">均线</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-[#64748b]">MA5</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.ma5.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">MA10</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.ma10.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">MA20</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.ma20.toFixed(2)}</span></div>
            </div>
          </div>
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b] mb-2">MACD</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-[#64748b]">DIF</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.macd.dif.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">DEA</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.macd.dea.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">MACD</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.macd.macd.toFixed(2)}</span></div>
            </div>
          </div>
          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b] mb-2">KDJ</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-[#64748b]">K</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.kdj.k.toFixed(1)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">D</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.kdj.d.toFixed(1)}</span></div>
              <div className="flex justify-between"><span className="text-[#64748b]">J</span><span className="text-[#e2e8f0] font-mono">{stockPanel.indicators.kdj.j.toFixed(1)}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* 五档盘口 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">五档盘口</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-[#ef4444] mb-2">卖盘</div>
            <div className="space-y-1">
              {[...stockPanel.orderBook.asks].reverse().map((ask, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-[#ef4444] font-mono">卖{5 - i}</span>
                  <span className="text-[#ef4444] font-mono">{ask.price.toFixed(2)}</span>
                  <span className="text-[#64748b] font-mono">{ask.volume}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="text-xs text-[#22c55e] mb-2">买盘</div>
            <div className="space-y-1">
              {stockPanel.orderBook.bids.map((bid, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-[#22c55e] font-mono">买{i + 1}</span>
                  <span className="text-[#22c55e] font-mono">{bid.price.toFixed(2)}</span>
                  <span className="text-[#64748b] font-mono">{bid.volume}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 资金博弈 Tab ───────────────────────────────────────────────
function FundTab({ fundFlow }: { fundFlow: ReturnType<typeof generateMockEnvironment>['fundFlow'] }) {
  return (
    <div className="space-y-4">
      {/* 资金流向 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">资金流向</h3>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: '超大单', data: fundFlow.superLarge },
            { label: '大单', data: fundFlow.large },
            { label: '中单', data: fundFlow.medium },
            { label: '小单', data: fundFlow.small },
          ].map(item => (
            <div key={item.label} className="p-3 bg-[#1e293b] rounded">
              <div className="text-xs text-[#64748b] mb-2">{item.label}</div>
              <div className="text-xs text-[#22c55e]">流入: {formatNumber(item.data.inflow)}万</div>
              <div className="text-xs text-[#ef4444]">流出: {formatNumber(item.data.outflow)}万</div>
              <div className={cn(
                'text-sm font-mono mt-1',
                item.data.net >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
              )}>
                净额: {item.data.net >= 0 ? '+' : ''}{formatNumber(item.data.net)}万
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 筹码分布 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">筹码分布</h3>
        <div className="grid grid-cols-3 gap-3">
          <StatBox label="获利盘" value={`${fundFlow.chipDistribution.profitRatio}%`} color="text-[#22c55e]" />
          <StatBox label="套牢盘" value={`${fundFlow.chipDistribution.lossRatio}%`} color="text-[#ef4444]" />
          <StatBox label="筹码集中度" value={`${fundFlow.chipDistribution.concentration}%`} />
        </div>
      </div>
    </div>
  );
}

// ── 消息面 Tab ─────────────────────────────────────────────────
function NewsTab({ newsEnv }: { newsEnv: ReturnType<typeof generateMockEnvironment>['newsEnv'] }) {
  return (
    <div className="space-y-4">
      {/* 公司公告 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">公司公告</h3>
        <div className="space-y-2">
          {newsEnv.companyNews.map((news, i) => (
            <div key={i} className="flex items-start gap-3 p-2 bg-[#1e293b] rounded">
              <span className="px-2 py-0.5 bg-[#c9a84c]/20 text-[#c9a84c] text-xs rounded">{news.type}</span>
              <div>
                <div className="text-sm text-[#e2e8f0]">{news.title}</div>
                <div className="text-xs text-[#64748b]">{news.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 市场舆情 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">市场舆情</h3>
        <div className="grid grid-cols-3 gap-3">
          <StatBox label="讨论热度" value={`${newsEnv.marketSentiment.heat}分`} />
          <StatBox label="看多比例" value={`${newsEnv.marketSentiment.bullishRatio}%`} color="text-[#22c55e]" />
          <StatBox label="看空比例" value={`${newsEnv.marketSentiment.bearishRatio}%`} color="text-[#ef4444]" />
        </div>
      </div>
    </div>
  );
}

// ── 智能诊断 Tab ───────────────────────────────────────────────
function DiagnosisTab({ 
  diagnosis, 
  trade, 
  onRunDiagnosis, 
  isDiagnosing 
}: { 
  diagnosis: ReturnType<typeof generateMockEnvironment>['diagnosis']; 
  trade: TradeRecord;
  onRunDiagnosis: () => void;
  isDiagnosing: boolean;
}) {
  return (
    <div className="space-y-4">
      {/* 12维度诊断按钮 */}
      <div className="p-4 bg-gradient-to-r from-[#c9a84c]/10 to-[#c9a84c]/5 rounded-lg border border-[#c9a84c]/30">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#c9a84c] flex items-center gap-2">
              <Target size={16} />
              全域多维度战法诊股
            </h3>
            <p className="text-xs text-[#64748b] mt-1">
              12维度全方位诊断：资金、筹码、技术、题材、情绪、心态、纪律、仓位、周期、点位、消息、成本、基本面、习惯
            </p>
          </div>
          <button
            onClick={onRunDiagnosis}
            disabled={isDiagnosing}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              isDiagnosing
                ? 'bg-[#64748b]/50 text-[#94a3b8] cursor-not-allowed'
                : 'bg-[#c9a84c] text-[#0d1526] hover:bg-[#b8974a]'
            )}
          >
            {isDiagnosing ? (
              <span className="flex items-center gap-2">
                <RefreshCw size={14} className="animate-spin" />
                诊断中...
              </span>
            ) : (
              '开始12维度诊断'
            )}
          </button>
        </div>
      </div>

      {/* 诊断结果 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <h3 className="text-xs text-[#64748b] mb-2">买卖时机判定</h3>
          <div className="text-lg text-[#c9a84c]">{diagnosis.timing}</div>
        </div>
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <h3 className="text-xs text-[#64748b] mb-2">风险等级</h3>
          <div className={cn(
            'text-lg',
            diagnosis.riskLevel === '高' ? 'text-[#ef4444]' :
            diagnosis.riskLevel === '中' ? 'text-[#f59e0b]' : 'text-[#22c55e]'
          )}>
            {diagnosis.riskLevel}
          </div>
        </div>
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
          <h3 className="text-xs text-[#64748b] mb-2">个股状态</h3>
          <div className="text-lg text-[#e2e8f0]">{diagnosis.stockStatus}</div>
        </div>
      </div>

      {/* 风险提示 */}
      {diagnosis.risks.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(239,68,68,0.2)]">
          <h3 className="text-sm font-medium text-[#ef4444] mb-3 flex items-center gap-2">
            <AlertTriangle size={16} />
            风险提示
          </h3>
          <div className="space-y-2">
            {diagnosis.risks.map((risk, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-[#ef4444]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#ef4444]" />
                {risk}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 操作建议 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <Target size={16} />
          操作建议
        </h3>
        <div className="space-y-2">
          {diagnosis.suggestions.map((suggestion, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-[#e2e8f0]">
              <span className="w-5 h-5 rounded-full bg-[#c9a84c]/20 text-[#c9a84c] flex items-center justify-center text-xs shrink-0">
                {i + 1}
              </span>
              {suggestion}
            </div>
          ))}
        </div>
      </div>

      {/* 决策偏差复盘 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3">决策偏差复盘</h3>
        <div className="p-3 bg-[#1e293b] rounded">
          <div className="text-xs text-[#64748b] mb-2">您的下单思路</div>
          <div className="text-sm text-[#e2e8f0] mb-3">{trade.tradeLogic || '未记录'}</div>
          <div className="text-xs text-[#64748b] mb-2">客观盘面事实</div>
          <div className="text-sm text-[#e2e8f0]">
            成交时大盘{diagnosis.timing}，个股{diagnosis.stockStatus}，
            存在{diagnosis.risks.join('、')}等风险因素。
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 通用组件 ───────────────────────────────────────────────────
function InfoCard({ title, value, icon }: { title: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div className="p-3 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[#64748b]">{title}</span>
        <span className="text-[#c9a84c]">{icon}</span>
      </div>
      <div className="text-sm text-[#e2e8f0] font-mono">{value}</div>
    </div>
  );
}

function StatBox({ label, value, color = 'text-[#e2e8f0]', highlight = false }: { label: string; value: string | number; color?: string; highlight?: boolean }) {
  return (
    <div className={cn(
      'p-3 rounded',
      highlight ? 'bg-[#c9a84c]/10 border border-[#c9a84c]/30' : 'bg-[#1e293b]'
    )}>
      <div className="text-xs text-[#64748b]">{label}</div>
      <div className={cn('text-sm font-mono', color)}>{value}</div>
    </div>
  );
}