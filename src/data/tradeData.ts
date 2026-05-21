// ═══════════════════════════════════════════════════════════════
//  交易日志 & 历史交易分析 & 完整交易环境重构 - 数据类型定义
// ═══════════════════════════════════════════════════════════════

// ── 交易日志模块 ───────────────────────────────────────────────

export interface JournalTemplate {
  id: string;
  name: string;
  sections: JournalSection[];
  createdAt: string;
  updatedAt: string;
  isDefault: boolean;
}

export interface JournalSection {
  id: string;
  title: string;
  content: string; // HTML/Markdown 富文本内容
  order: number;
  isVisible: boolean;
}

export interface TradeJournal {
  id: string;
  date: string; // YYYY-MM-DD
  templateId: string;
  sections: JournalSection[];
  tags: string[];
  mood: 'bullish' | 'bearish' | 'neutral' | 'cautious';
  createdAt: string;
  updatedAt: string;
}

// 默认日志模板
export const DEFAULT_JOURNAL_TEMPLATES: JournalTemplate[] = [
  {
    id: 'default-daily',
    name: '每日交易日志',
    sections: [
      { id: 's1', title: '大盘分析', content: '', order: 1, isVisible: true },
      { id: 's2', title: '市场风格分析', content: '', order: 2, isVisible: true },
      { id: 's3', title: '题材炒作节奏分析', content: '', order: 3, isVisible: true },
      { id: 's4', title: '锚定个股分析', content: '', order: 4, isVisible: true },
      { id: 's5', title: '交易机会风险预判', content: '', order: 5, isVisible: true },
      { id: 's6', title: '盯盘记录', content: '', order: 6, isVisible: true },
      { id: 's7', title: '日内操作逻辑', content: '', order: 7, isVisible: true },
      { id: 's8', title: '盘后分析', content: '', order: 8, isVisible: true },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isDefault: true,
  },
];

// ── 历史交易记录 ───────────────────────────────────────────────

export interface TradeRecord {
  // 一、单笔交易原生基础信息
  id: string;
  tradeTime: string; // YYYY-MM-DD HH:mm:ss
  tradeDate: string; // YYYY-MM-DD
  stockCode: string;
  stockName: string;
  market: 'SH' | 'SZ' | 'CYB' | 'KCB' | 'BSE'; // 沪/深/创业板/科创/北交所
  tradeType: 'buy' | 'sell';
  orderType: 'limit' | 'market' | 'condition'; // 限价/市价/条件单
  tradePrice: number;
  tradeVolume: number;
  tradeAmount: number;
  fee: number; // 手续费
  stampTax: number; // 印花税
  transferFee: number; // 过户费
  profitLoss: number; // 单笔盈亏
  positionRatio: number; // 占仓位比例
  accountBalance: number; // 成交瞬间账户可用资金
  dailyPnL: number; // 当日累计盈亏
  currentHolding: number; // 个股当前总持仓数量
  // 委托全链路
  orderTime: string;
  cancelRecords: CancelRecord[];
  matchStatus: 'full' | 'partial' | 'pending';
  // 来源
  source: 'manual' | 'excel' | 'ocr' | 'voice';
  screenshotUrl?: string;
  // 用户备注
  userNote: string;
  tradeLogic: string; // 当时下单思路
  createdAt: string;
  updatedAt: string;
}

export interface CancelRecord {
  time: string;
  volume: number;
  price: number;
}

// ── 用户画像分析 ───────────────────────────────────────────────

export interface UserProfile {
  totalTrades: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  maxDrawdown: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  preferredTimeSlots: TimeSlotPreference[];
  preferredSectors: SectorPreference[];
  preferredStyles: StylePreference[];
  highFreqErrors: HighFreqError[];
  tradeHabitSummary: string;
}

export interface TimeSlotPreference {
  timeSlot: string;
  tradeCount: number;
  winRate: number;
}

export interface SectorPreference {
  sector: string;
  tradeCount: number;
  winRate: number;
  avgProfit: number;
}

export interface StylePreference {
  style: string;
  tradeCount: number;
  winRate: number;
}

export interface HighFreqError {
  errorType: string;
  count: number;
  totalLoss: number;
  description: string;
}

// ── 完整交易环境重构 - 大盘宏观环境 ────────────────────────────

export interface MarketEnvironment {
  timestamp: string;
  // 主流指数快照
  indices: IndexSnapshot[];
  // 大盘日内走势定位
  intradayTrend: IntradayTrendData;
  // 市场整体情绪
  marketBreadth: MarketBreadthData;
  // 北向资金
  northboundFlow: NorthboundData;
  // 大周期环境参照
  macroTrend: MacroTrendData;
}

export interface IndexSnapshot {
  name: string;
  code: string;
  value: number;
  change: number;
  changePercent: number;
  volume: number; // 成交额
  timestamp: string;
}

export interface IntradayTrendData {
  timePoints: string[];
  values: number[];
  avgValues: number[];
  volumes: number[];
  trendPhase: '上涨' | '下跌' | '横盘' | '跳水' | '拉升';
}

export interface MarketBreadthData {
  upCount: number;
  downCount: number;
  limitUpCount: number;
  limitDownCount: number;
 炸板Count: number;
  totalVolume: number; // 两市总成交额（亿）
  moneyEffectScore: number; // 赚钱效应评分 0-100
}

export interface NorthboundData {
  netFlow: number; // 净流入/流出（亿）
  shFlow: number; // 沪股通
  szFlow: number; // 深股通
  trend: 'inflow' | 'outflow';
}

export interface MacroTrendData {
  dailyTrend: 'up' | 'down' | 'sideways';
  weeklyTrend: 'up' | 'down' | 'sideways';
  monthlyTrend: 'up' | 'down' | 'sideways';
  marketPhase: '牛市' | '熊市' | '震荡市';
}

// ── 完整交易环境重构 - 行业板块+题材联动 ───────────────────────

export interface SectorEnvironment {
  timestamp: string;
  // 多层级板块定点行情
  sectorSnapshots: SectorSnapshot[];
  // 板块分时走势
  sectorIntraday: SectorIntradayData;
  // 题材风口梯队
  topicRanking: TopicRankingItem[];
  // 对标板块龙头走势
  leaderStocks: SectorLeaderStock[];
}

export interface SectorSnapshot {
  code: string;
  name: string;
  level: 'sw1' | 'sw2' | 'concept'; // 申万一级/二级/概念
  value: number;
  changePercent: number;
  volume: number;
}

export interface SectorIntradayData {
  sectorName: string;
  timePoints: string[];
  values: number[];
  volumes: number[];
}

export interface TopicRankingItem {
  rank: number;
  name: string;
  changePercent: number;
  limitUpCount: number;
  maxConsecutiveBoards: number;
  relatedStocks: string[];
}

export interface SectorLeaderStock {
  code: string;
  name: string;
  changePercent: number;
  isLeader: boolean;
  intradayData: IntradayTrendData;
}

// ── 完整交易环境重构 - 个股盘面图形 ────────────────────────────

export interface StockPanelData {
  timestamp: string;
  stockCode: string;
  stockName: string;
  // 个股当日分时走势图
  intradayChart: IntradayChartData[];
  // 多周期K线
  klineData: {
    '1m': KlineItem[];
    '5m': KlineItem[];
    '15m': KlineItem[];
    '30m': KlineItem[];
    '60m': KlineItem[];
    'daily': KlineItem[];
    'weekly': KlineItem[];
    'monthly': KlineItem[];
  };
  // 常用技术指标
  indicators: TechnicalIndicators;
  // 五档盘口挂单快照
  orderBook: OrderBookSnapshot;
  // 前后逐笔成交回放
  tickData: TickItem[];
  // 个股日内基础数据
  intradayStats: IntradayStats;
  // 成交点位标记
  tradePoint: TradePointMarker;
}

export interface IntradayChartData {
  time: string;
  price: number;
  avgPrice: number;
  volume: number;
}

export interface KlineItem {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  turnover: number;
}

export interface TechnicalIndicators {
  ma: { ma5: number; ma10: number; ma20: number; ma60: number };
  macd: { dif: number; dea: number; macd: number };
  kdj: { k: number; d: number; j: number };
  boll: { upper: number; mid: number; lower: number };
  rsi: { rsi6: number; rsi12: number; rsi24: number };
  volume: { vol5: number; vol10: number };
}

export interface OrderBookSnapshot {
  bids: OrderBookLevel[]; // 买1-买5
  asks: OrderBookLevel[]; // 卖1-卖5
  timestamp: string;
}

export interface OrderBookLevel {
  price: number;
  volume: number;
  orders: number; // 挂单笔数
}

export interface TickItem {
  time: string;
  price: number;
  volume: number;
  direction: 'buy' | 'sell' | 'neutral';
  amount: number;
  isLargeOrder: boolean;
}

export interface IntradayStats {
  open: number;
  high: number;
  low: number;
  close: number;
  turnoverRate: number; // 换手率
  volumeRatio: number; // 量比
  amplitude: number; // 振幅
  floatMarketCap: number; // 流通市值
}

export interface TradePointMarker {
  time: string;
  price: number;
  type: 'buy' | 'sell';
}

// ── 完整交易环境重构 - 资金博弈与筹码异动 ──────────────────────

export interface CapitalFlowData {
  timestamp: string;
  // 瞬时资金流向拆分
  fundFlow: {
    superLarge: number; // 超大单净流入
    large: number; // 大单净流入
    medium: number; // 中单净流入
    small: number; // 小单净流入
  };
  // 筹码分布静态快照
  chipDistribution: ChipDistribution;
  // 龙虎榜席位回溯
  dragonTigerList: DragonTigerItem[];
  // 大额挂撤单异动记录
  largeOrderAnomalies: LargeOrderAnomaly[];
}

export interface ChipDistribution {
  profitRatio: number; // 获利盘占比
  lockedRatio: number; // 套牢盘占比
  concentration: number; // 筹码集中度
  peakPrices: number[]; // 筹码峰价格
  avgCost: number; // 平均成本
}

export interface DragonTigerItem {
  seatName: string;
  seatType: '游资' | '机构' | '沪股通' | '深股通';
  buyAmount: number;
  sellAmount: number;
  netAmount: number;
}

export interface LargeOrderAnomaly {
  time: string;
  type: '大单挂单' | '大单撤单' | '压单' | '托单';
  price: number;
  volume: number;
}

// ── 完整交易环境重构 - 强弱对标对比 ────────────────────────────

export interface ComparisonData {
  // 个股分时 + 大盘分时叠加对比
  stockVsIndex: StockVsIndexData;
  // 个股 + 同板块个股走势叠加对比
  stockVsPeers: StockVsPeersData;
  // 同期风格指数对标
  styleComparison: StyleComparisonData;
}

export interface StockVsIndexData {
  stockIntraday: IntradayChartData[];
  indexIntraday: IntradayChartData[];
  relativeStrength: number[]; // 相对强弱
}

export interface StockVsPeersData {
  targetStock: IntradayChartData[];
  peerStocks: { code: string; name: string; data: IntradayChartData[] }[];
  sectorAvg: IntradayChartData[];
}

export interface StyleComparisonData {
  smallCap: StyleIndexData;
  largeCap: StyleIndexData;
  growth: StyleIndexData;
  value: StyleIndexData;
  targetStockStyle: string;
}

export interface StyleIndexData {
  name: string;
  changePercent: number;
  trend: 'up' | 'down' | 'sideways';
}

// ── 完整交易环境重构 - 消息面舆情催化 ──────────────────────────

export interface NewsCatalystData {
  // 时间轴时序消息
  timelineNews: TimelineNewsItem[];
  // 个股当日公告汇总
  announcements: AnnouncementItem[];
  // 市场舆情热度
  sentimentHeat: SentimentHeatData;
}

export interface TimelineNewsItem {
  time: string;
  type: '公司公告' | '行业政策' | '大盘突发' | '题材催化';
  title: string;
  content: string;
  impact: 'positive' | 'negative' | 'neutral';
  source: string;
}

export interface AnnouncementItem {
  time: string;
  title: string;
  type: '业绩预告' | '减持增持' | '并购重组' | '风险警示' | '其他';
  url?: string;
}

export interface SentimentHeatData {
  discussionCount: number;
  bullishRatio: number; // 看多占比
  bearishRatio: number; // 看空占比
  hotKeywords: string[];
  sentimentTrend: 'improving' | 'deteriorating' | 'stable';
}

// ── 完整交易环境重构 - 特殊交易场景 ────────────────────────────

export interface SpecialSceneData {
  sceneType: 'callAuction' | 'tailAuction' | 'specialStock' | 'overnight';
  callAuctionData?: CallAuctionData;
  tailAuctionData?: TailAuctionData;
  specialStockData?: SpecialStockData;
  overnightData?: OvernightData;
}

export interface CallAuctionData {
  time: string; // 9:15-9:25
  matchPrice: number;
  matchVolume: number;
  unmatchVolume: number;
  bidOrders: OrderBookLevel[];
  askOrders: OrderBookLevel[];
}

export interface TailAuctionData {
  time: string; // 14:57-15:00
  matchPrice: number;
  matchVolume: number;
}

export interface SpecialStockData {
  stockType: 'KCB' | 'BSE' | 'ST' | 'convertibleBond';
  priceLimit: number; // 涨跌幅限制
  suspensionRecords: SuspensionRecord[];
}

export interface SuspensionRecord {
  time: string;
  reason: string;
  duration: number; // 停牌时长（分钟）
}

export interface OvernightData {
  orderTime: string;
  matchTime: string;
  overnightChange: number; // 隔夜涨跌幅
}

// ── 完整交易环境重构 - 智能诊断 ────────────────────────────────

export interface TradeDiagnosis {
  tradeId: string;
  // 买卖时机定位判定
  timingAnalysis: TimingAnalysis;
  // 环境风险智能识别
  riskIdentification: RiskItem[];
  // 个股强弱属性判定
  strengthAnalysis: StrengthAnalysis;
  // 决策偏差对照复盘
  deviationAnalysis: DeviationAnalysis;
  // 同环境历史胜率参考
  historicalReference: HistoricalReference;
  // 综合评分
  overallScore: number;
  // 诊断总结
  summary: string;
  // 改进建议
  suggestions: string[];
}

export interface TimingAnalysis {
  trendPosition: '趋势启动' | '上涨中途' | '顶部拐点' | '下跌中继' | '底部区间';
  isOptimalTiming: boolean;
  reason: string;
}

export interface RiskItem {
  riskType: '系统性风险' | '板块退潮' | '个股利空' | '资金出逃' | '技术破位' | '情绪过热';
  severity: 'high' | 'medium' | 'low';
  description: string;
  evidence: string;
}

export interface StrengthAnalysis {
  stockState: '独立走强' | '跟风上涨' | '弱势补跌' | '逆势抗跌';
  relativeToMarket: '强于大盘' | '同步大盘' | '弱于大盘';
  relativeToSector: '强于板块' | '同步板块' | '弱于板块';
  reason: string;
}

export interface DeviationAnalysis {
  userLogic: string; // 用户填写的下单思路
  actualEnvironment: string; // 客观盘面事实
  deviation: string; // 偏差分析
  isRationalTrade: boolean;
}

export interface HistoricalReference {
  similarCount: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  similarConditions: string[];
}

// ── API 响应类型 ───────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ── Excel 导入数据类型 ─────────────────────────────────────────

export interface ExcelTradeRecord {
  成交日期?: string;
  成交时间?: string;
  证券代码?: string;
  证券名称?: string;
  操作?: string; // 买入/卖出
  成交价格?: number;
  成交数量?: number;
  成交金额?: number;
  手续费?: number;
  印花税?: number;
  过户费?: number;
  发生金额?: number; // 实际发生金额
  成交编号?: string;
  合同编号?: string;
}

// ── OCR 识别结果 ───────────────────────────────────────────────

export interface OcrTradeResult {
  imageUrl: string;
  recognizedText: string;
  parsedTrades: Partial<TradeRecord>[];
  confidence: number;
}

// ── 语音输入结果 ───────────────────────────────────────────────

export interface VoiceInputResult {
  text: string;
  parsedTrade: Partial<TradeRecord>;
  confidence: number;
}