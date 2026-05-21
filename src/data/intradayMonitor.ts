// ═══════════════════════════════════════════════════════════════
// 盘中监控模块 — 核心数据层
// 模块1: 大盘&板块情绪全局监控
// 模块2: 主线题材+龙头梯队识别
// 模块3: 主升浪个股实时筛选+盘中预警
// 模块4: 持仓股实时盯盘系统
// 模块5: 复盘&回测系统
// ═══════════════════════════════════════════════════════════════


// ═══════════════════════════════════════════════════════════════
// 模块1: 大盘&板块情绪全局监控
// ═══════════════════════════════════════════════════════════════

// ── 情绪周期阶段 ──
export type SentimentPhase = '启动期' | '发酵期' | '主升期' | '退潮期';

export const SENTIMENT_PHASE_CONFIG: Record<SentimentPhase, {
  color: string;
  bgColor: string;
  description: string;
  positionAdvice: string;
  maxPosition: number; // 最大仓位建议(%)
  tactics: string[]; // 适合战法
  forbidden: string[]; // 禁止战法
}> = {
  '启动期': {
    color: '#3b82f6',
    bgColor: 'rgba(59,130,246,0.1)',
    description: '新题材初现，资金试探性介入',
    positionAdvice: '轻仓试错，聚焦首板',
    maxPosition: 20,
    tactics: ['首板打板', '题材挖掘', '低位潜伏'],
    forbidden: ['连板接力', '高位追涨'],
  },
  '发酵期': {
    color: '#22c55e',
    bgColor: 'rgba(34,197,94,0.1)',
    description: '题材扩散，板块效应显现',
    positionAdvice: '加仓主线，关注二板',
    maxPosition: 50,
    tactics: ['二板确认', '板块跟风', 'N字反包'],
    forbidden: ['低位潜伏(错过时机)'],
  },
  '主升期': {
    color: '#ef4444',
    bgColor: 'rgba(239,68,68,0.1)',
    description: '主线明确，龙头加速，赚钱效应最强',
    positionAdvice: '重仓主线龙头，持股待涨',
    maxPosition: 80,
    tactics: ['连板接力', '龙头首阴', '主升加速'],
    forbidden: ['空仓观望(错过主升)'],
  },
  '退潮期': {
    color: '#6b7280',
    bgColor: 'rgba(107,114,128,0.1)',
    description: '高位补跌，炸板率上升，资金出逃',
    positionAdvice: '空仓或极轻仓观望',
    maxPosition: 10,
    tactics: ['空仓观望'],
    forbidden: ['连板接力', '高位追涨', '主升加速'],
  },
};

// ── 大盘监控指标 ──
export interface MarketMonitor {
  // 涨跌统计
  limitUpCount: number;       // 涨停家数
  limitDownCount: number;     // 跌停家数
  brokenBoardCount: number;   // 炸板家数
  boardSealRate: number;      // 封板率(%)
  maxConsecutiveBoards: number; // 连板高度
  
  // 赚钱效应
  yesterdayLimitUpPremium: number; // 昨日涨停溢价(%)
  consecutiveBoardPremium: number; // 连板溢价(%)
  trendStockEffect: number;        // 趋势股赚钱效应(%)
  
  // 情绪周期
  currentPhase: SentimentPhase;
  phaseConfidence: number; // 周期判定置信度(%)
  
  // 大盘指数
  indices: {
    name: string;
    code: string;
    value: number;
    change: number;
    changePercent: number;
    volume: number; // 成交额(亿)
    trend: 'up' | 'down' | 'flat';
  }[];
  
  // 全市场统计
  totalUpCount: number;   // 上涨家数
  totalDownCount: number; // 下跌家数
  totalVolume: number;    // 全市场成交额(亿)
  northFundFlow: number;  // 北向资金净流入(亿)
}

// ── 板块强度排行 ──
export interface SectorStrength {
  name: string;
  type: '主线' | '支线' | '杂毛';
  limitUpCount: number;     // 板块涨停数
  consecutiveBoardTiers: number[]; // 连板梯队 [5,3,2,1]
  totalVolume: number;      // 板块成交额(亿)
  changePercent: number;    // 板块涨跌幅(%)
  sealRate: number;         // 封板率(%)
  trendStrength: number;    // 趋势强度(0-100)
  fundFlow: number;         // 资金净流入(亿)
  isMainLine: boolean;      // 是否当日唯一主线
  status: '启动' | '发酵' | '主升' | '退潮' | '回流';
  alert?: string;           // 异动提示
}

// ── 实时情绪仪表盘输出 ──
export interface SentimentDashboard {
  phase: SentimentPhase;
  mainLine: string;         // 主线板块
  action: '可开仓' | '谨慎开仓' | '禁止开仓' | '空仓观望';
  summary: string;          // 一句话总结
  riskLevel: '低' | '中' | '高' | '极高';
}

// ═══════════════════════════════════════════════════════════════
// 模块2: 主线题材+龙头梯队识别
// ═══════════════════════════════════════════════════════════════

// ── 龙头地位类型 ──
export type LeaderType = '空间龙' | '趋势龙' | '补涨龙' | '跟风龙' | '杂毛';

// ── 龙头梯队 ──
export interface LeaderTier {
  boardCount: number;       // 连板数
  stocks: LeaderStock[];
}

export interface LeaderStock {
  code: string;
  name: string;
  price: number;
  change: number;
  leaderType: LeaderType;
  boardCount: number;       // 连板数
  sector: string;           // 所属板块
  sealAmount: string;       // 封单金额
  limitUpTime: string;      // 涨停时间
  volumeRatio: number;      // 量比
  turnoverRate: number;     // 换手率(%)
  
  // 龙头地位评分(0-100)
  score: LeaderScore;
  
  // 是否属于主线
  isMainLine: boolean;
}

export interface LeaderScore {
  total: number;            // 总分
  recognition: number;      // 辨识度(0-20)
  sectorDrive: number;      // 板块带动性(0-20)
  fundCluster: number;      // 资金抱团(0-20)
  trendStrength: number;    // 趋势强度(0-20)
  chipStability: number;    // 筹码稳定性(0-20)
}

// ── 主线一致性校验 ──
export interface MainLineConsistency {
  mainLineSectors: string[]; // 主线题材列表
  filteredStocks: LeaderStock[]; // 过滤后的主线龙头
  blockedStocks: { stock: LeaderStock; reason: string }[]; // 被屏蔽的非主线
}

// ═══════════════════════════════════════════════════════════════
// 模块3: 主升浪个股实时筛选+盘中预警
// ═══════════════════════════════════════════════════════════════

// ── 买点类型 ──
export type BuyPointType = '主升加速' | '弱转强' | '龙头首阴' | '二波启动';

export const BUY_POINT_CONFIG: Record<BuyPointType, {
  color: string;
  icon: string;
  description: string;
  riskLevel: '低' | '中' | '高';
  stopLossPercent: number; // 止损位(%)
  tactics: string;         // 对应战法
}> = {
  '主升加速': {
    color: '#ef4444',
    icon: 'TrendingUp',
    description: '主线龙头站稳5/10日线，放量突破',
    riskLevel: '中',
    stopLossPercent: -5,
    tactics: '主升浪战法',
  },
  '弱转强': {
    color: '#22c55e',
    icon: 'RefreshCw',
    description: '主线龙头分歧转一致，板块回流',
    riskLevel: '中',
    stopLossPercent: -4,
    tactics: '分歧转一致战法',
  },
  '龙头首阴': {
    color: '#c9a84c',
    icon: 'AlertCircle',
    description: '空间龙缩量回踩关键均线',
    riskLevel: '高',
    stopLossPercent: -6,
    tactics: '龙头首阴战法',
  },
  '二波启动': {
    color: '#8b5cf6',
    icon: 'Zap',
    description: '龙头横盘企稳，放量启动',
    riskLevel: '低',
    stopLossPercent: -4,
    tactics: '二波启动战法',
  },
};

// ── 预警信号 ──
export interface AlertSignal {
  id: string;
  time: string;
  code: string;
  name: string;
  price: number;
  change: number;
  buyPointType: BuyPointType;
  logic: string;          // 买点逻辑
  tactics: string;        // 对应战法
  riskLevel: '低' | '中' | '高';
  stopLoss: number;       // 止损位
  stopLossPrice: number;  // 止损价格
  sector: string;         // 所属板块
  isMainLine: boolean;    // 是否主线
  confidence: number;     // 信号置信度(%)
}

// ── 过滤条件 ──
export interface FilterCondition {
  excludeNonMainLine: boolean;    // 排除非主线
  excludeRetreatPhase: boolean;   // 退潮期关闭预警
  excludeST: boolean;             // 排除ST
  excludeDelisting: boolean;      // 排除退市
  excludeLossMaking: boolean;     // 排除亏损严重
  excludeLowLiquidity: boolean;   // 排除流动性差
  excludeZhuangGu: boolean;       // 排除庄股
  excludeHighRisk: boolean;       // 排除高位风险
}

export const DEFAULT_FILTER: FilterCondition = {
  excludeNonMainLine: true,
  excludeRetreatPhase: true,
  excludeST: true,
  excludeDelisting: true,
  excludeLossMaking: true,
  excludeLowLiquidity: true,
  excludeZhuangGu: true,
  excludeHighRisk: true,
};

// ═══════════════════════════════════════════════════════════════
// 模块4: 持仓股实时盯盘系统
// ═══════════════════════════════════════════════════════════════

// ── 持仓股 ──
export interface HoldingStock {
  code: string;
  name: string;
  costPrice: number;      // 成本价
  currentPrice: number;   // 当前价
  quantity: number;       // 持仓数量
  profitLoss: number;     // 盈亏(%)
  profitLossAmount: number; // 盈亏金额
  
  // 趋势监控
  ma5: number;            // 5日线
  ma10: number;           // 10日线
  ma20: number;           // 20日线
  trendStatus: '多头' | '支撑' | '破位' | '空头';
  
  // 量能监控
  volumeStatus: '放量滞涨' | '放量杀跌' | '缩量企稳' | '量价齐升' | '正常';
  
  // 板块监控
  sector: string;
  sectorPhase: '启动' | '发酵' | '主升' | '退潮';
  sectorIsMainLine: boolean;
  
  // 持有逻辑
  isLeader: boolean;      // 是否龙头梯队
  isMainLine: boolean;    // 是否在主线
  holdLogicValid: boolean; // 持有逻辑是否有效
  
  // 风控
  stopLossLine: number;   // 止损线(%)
  takeProfitLine: number; // 止盈线(%)
  maxDrawdown: number;    // 最大回撤(%)
  alertTriggered: string[]; // 已触发提醒
}

// ── 持仓提醒类型 ──
export type HoldingAlertType = 
  | '趋势破位' 
  | '量能异常' 
  | '板块退潮' 
  | '止损提醒' 
  | '止盈提醒' 
  | '逻辑失效';

export interface HoldingAlert {
  type: HoldingAlertType;
  code: string;
  name: string;
  message: string;
  time: string;
  action: '止盈' | '止损' | '减仓' | '持有' | '卖出';
  urgency: '低' | '中' | '高' | '紧急';
}

// ═══════════════════════════════════════════════════════════════
// 模块5: 复盘&回测系统
// ═══════════════════════════════════════════════════════════════

// ── 回测结果 ──
export interface BacktestResult {
  period: string;         // 回测区间
  totalTrades: number;    // 总交易次数
  winRate: number;        // 胜率(%)
  avgWin: number;         // 平均盈利(%)
  avgLoss: number;        // 平均亏损(%)
  profitLossRatio: number; // 盈亏比
  maxDrawdown: number;    // 最大回撤(%)
  totalReturn: number;    // 总收益(%)
  sharpeRatio: number;    // 夏普比率
  
  // 按买点类型统计
  byBuyPoint: {
    type: BuyPointType;
    count: number;
    winRate: number;
    avgReturn: number;
  }[];
  
  // 按情绪周期统计
  byPhase: {
    phase: SentimentPhase;
    count: number;
    winRate: number;
    avgReturn: number;
  }[];
}

// ── 每日复盘 ──
export interface DailyReview {
  date: string;
  phase: SentimentPhase;
  mainLine: string;
  leaders: { code: string; name: string; boards: number }[];
  opportunities: string[];    // 操作机会
  missedOpportunities: string[]; // 错过的机会
  mistakes: string[];         // 操作失误
  summary: string;
  nextDayPlan: string;
}

// ── 操作日志 ──
export interface TradeLog {
  id: string;
  date: string;
  code: string;
  name: string;
  action: '买入' | '卖出';
  price: number;
  quantity: number;
  amount: number;
  buyPointType?: BuyPointType;
  reason: string;
  profitLoss?: number;
  holdDays?: number;
  result: '盈利' | '亏损' | '持平';
  review?: string;
}

// ── 战法参数配置 ──
export interface TacticParams {
  // 均线周期
  maShort: number;    // 短期均线(默认5)
  maMid: number;      // 中期均线(默认10)
  maLong: number;     // 长期均线(默认20)
  
  // 放量阈值
  volumeThreshold: number; // 放量倍数(默认3)
  
  // 情绪阈值
  sentimentBullish: number;  //  bullish阈值(默认60)
  sentimentBearish: number;  //  bearish阈值(默认40)
  
  // 止损止盈
  defaultStopLoss: number;   // 默认止损(%)
  defaultTakeProfit: number; // 默认止盈(%)
}

export const DEFAULT_TACTIC_PARAMS: TacticParams = {
  maShort: 5,
  maMid: 10,
  maLong: 20,
  volumeThreshold: 3,
  sentimentBullish: 60,
  sentimentBearish: 40,
  defaultStopLoss: -5,
  defaultTakeProfit: 10,
};

// ═══════════════════════════════════════════════════════════════
// 模拟数据生成
// ═══════════════════════════════════════════════════════════════

// ── 生成大盘监控数据 ──
export function generateMarketMonitor(): MarketMonitor {
  return {
    limitUpCount: 68,
    limitDownCount: 12,
    brokenBoardCount: 15,
    boardSealRate: 81.9,
    maxConsecutiveBoards: 6,
    yesterdayLimitUpPremium: 2.3,
    consecutiveBoardPremium: 5.8,
    trendStockEffect: 65.2,
    currentPhase: '主升期',
    phaseConfidence: 78,
    indices: [
      { name: '上证指数', code: 'SH000001', value: 4135.39, change: -42.53, changePercent: -1.02, volume: 5234, trend: 'down' },
      { name: '深证成指', code: 'SZ399001', value: 15561.37, change: -184.36, changePercent: -1.17, volume: 6892, trend: 'down' },
      { name: '创业板指', code: 'SZ399006', value: 3929.06, change: -22.08, changePercent: -0.56, volume: 3456, trend: 'flat' },
      { name: '科创50', code: 'SH000688', value: 1256.78, change: 8.45, changePercent: 0.68, volume: 1234, trend: 'up' },
    ],
    totalUpCount: 3248,
    totalDownCount: 1652,
    totalVolume: 17263,
    northFundFlow: 23.5,
  };
}

// ── 生成板块强度排行 ──
export function generateSectorStrength(): SectorStrength[] {
  return [
    {
      name: '消费电子',
      type: '主线',
      limitUpCount: 12,
      consecutiveBoardTiers: [5, 3, 2, 1],
      totalVolume: 523,
      changePercent: 2.8,
      sealRate: 85.7,
      trendStrength: 92,
      fundFlow: 16.2,
      isMainLine: true,
      status: '主升',
    },
    {
      name: '化工新材料',
      type: '主线',
      limitUpCount: 8,
      consecutiveBoardTiers: [3, 2, 1],
      totalVolume: 418,
      changePercent: 1.5,
      sealRate: 80.0,
      trendStrength: 78,
      fundFlow: 6.5,
      isMainLine: false,
      status: '发酵',
    },
    {
      name: '机器人概念',
      type: '支线',
      limitUpCount: 5,
      consecutiveBoardTiers: [2, 1],
      totalVolume: 289,
      changePercent: 0.8,
      sealRate: 71.4,
      trendStrength: 65,
      fundFlow: 2.3,
      isMainLine: false,
      status: '启动',
    },
    {
      name: '绿色电力',
      type: '支线',
      limitUpCount: 4,
      consecutiveBoardTiers: [3, 1],
      totalVolume: 234,
      changePercent: 0.5,
      sealRate: 66.7,
      trendStrength: 58,
      fundFlow: 1.8,
      isMainLine: false,
      status: '回流',
    },
    {
      name: '文化传媒',
      type: '杂毛',
      limitUpCount: 2,
      consecutiveBoardTiers: [1],
      totalVolume: 198,
      changePercent: -0.5,
      sealRate: 50.0,
      trendStrength: 32,
      fundFlow: -3.5,
      isMainLine: false,
      status: '退潮',
    },
  ];
}

// ── 生成情绪仪表盘 ──
export function generateSentimentDashboard(phase: SentimentPhase, mainLine: string): SentimentDashboard {
  const config = SENTIMENT_PHASE_CONFIG[phase];
  return {
    phase,
    mainLine,
    action: phase === '主升期' ? '可开仓' : phase === '退潮期' ? '禁止开仓' : phase === '发酵期' ? '可开仓' : '谨慎开仓',
    summary: `当前市场处于【${phase}】，主线为【${mainLine}】，${config.positionAdvice}`,
    riskLevel: phase === '主升期' ? '低' : phase === '退潮期' ? '高' : '中',
  };
}

// ── 生成龙头梯队 ──
export function generateLeaderTiers(): { tiers: LeaderTier[]; mainLineConsistency: MainLineConsistency } {
  const leaders: LeaderStock[] = [
    // 空间龙 - 6板
    {
      code: '002918', name: '蒙娜丽莎', price: 18.63, change: 10.0,
      leaderType: '空间龙', boardCount: 6, sector: '建筑材料',
      sealAmount: '3.2亿', limitUpTime: '09:30', volumeRatio: 0.8, turnoverRate: 2.1,
      score: { total: 95, recognition: 20, sectorDrive: 19, fundCluster: 18, trendStrength: 20, chipStability: 18 },
      isMainLine: true,
    },
    // 5板
    {
      code: '001259', name: '利仁科技', price: 60.5, change: 10.0,
      leaderType: '空间龙', boardCount: 5, sector: '消费电子',
      sealAmount: '2.1亿', limitUpTime: '09:25', volumeRatio: 0.6, turnoverRate: 1.8,
      score: { total: 92, recognition: 19, sectorDrive: 18, fundCluster: 19, trendStrength: 18, chipStability: 18 },
      isMainLine: true,
    },
    // 3板
    {
      code: '600578', name: '京能电力', price: 7.01, change: 10.03,
      leaderType: '趋势龙', boardCount: 3, sector: '绿色电力',
      sealAmount: '4.8亿', limitUpTime: '09:35', volumeRatio: 2.1, turnoverRate: 5.6,
      score: { total: 78, recognition: 15, sectorDrive: 16, fundCluster: 15, trendStrength: 17, chipStability: 15 },
      isMainLine: false,
    },
    // 2板 - 补涨龙
    {
      code: '001333', name: '光华股份', price: 26.05, change: 10.01,
      leaderType: '补涨龙', boardCount: 1, sector: '化工新材料',
      sealAmount: '0.6亿', limitUpTime: '09:41', volumeRatio: 3.2, turnoverRate: 8.5,
      score: { total: 72, recognition: 14, sectorDrive: 14, fundCluster: 15, trendStrength: 15, chipStability: 14 },
      isMainLine: true,
    },
    // 跟风龙
    {
      code: '002031', name: '巨轮智能', price: 8.4, change: 9.95,
      leaderType: '跟风龙', boardCount: 1, sector: '机器人',
      sealAmount: '2.1亿', limitUpTime: '09:35', volumeRatio: 2.8, turnoverRate: 12.3,
      score: { total: 58, recognition: 12, sectorDrive: 10, fundCluster: 12, trendStrength: 12, chipStability: 12 },
      isMainLine: false,
    },
    // 杂毛
    {
      code: '002374', name: '中锐股份', price: 3.55, change: 9.91,
      leaderType: '杂毛', boardCount: 1, sector: '文化传媒',
      sealAmount: '0.15亿', limitUpTime: '10:25', volumeRatio: 1.5, turnoverRate: 15.2,
      score: { total: 35, recognition: 6, sectorDrive: 5, fundCluster: 8, trendStrength: 8, chipStability: 8 },
      isMainLine: false,
    },
  ];

  const tiers: LeaderTier[] = [
    { boardCount: 6, stocks: leaders.filter(l => l.boardCount === 6) },
    { boardCount: 5, stocks: leaders.filter(l => l.boardCount === 5) },
    { boardCount: 3, stocks: leaders.filter(l => l.boardCount === 3) },
    { boardCount: 1, stocks: leaders.filter(l => l.boardCount === 1) },
  ];

  const mainLineConsistency: MainLineConsistency = {
    mainLineSectors: ['消费电子', '化工新材料'],
    filteredStocks: leaders.filter(l => l.isMainLine),
    blockedStocks: leaders.filter(l => !l.isMainLine).map(l => ({
      stock: l,
      reason: `非主线题材(${l.sector})`,
    })),
  };

  return { tiers, mainLineConsistency };
}

// ── 生成预警信号 ──
export function generateAlertSignals(): AlertSignal[] {
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
  
  return [
    {
      id: 'alert-001',
      time: timeStr,
      code: '001259', name: '利仁科技', price: 60.5, change: 10.0,
      buyPointType: '主升加速',
      logic: '5连板龙头，站稳5日线，放量突破前高',
      tactics: '主升浪战法',
      riskLevel: '中',
      stopLoss: -5,
      stopLossPrice: 57.48,
      sector: '消费电子',
      isMainLine: true,
      confidence: 88,
    },
    {
      id: 'alert-002',
      time: timeStr,
      code: '001333', name: '光华股份', price: 26.05, change: 10.01,
      buyPointType: '弱转强',
      logic: '昨日炸板今日反包，板块回流确认',
      tactics: '分歧转一致战法',
      riskLevel: '中',
      stopLoss: -4,
      stopLossPrice: 25.01,
      sector: '化工新材料',
      isMainLine: true,
      confidence: 75,
    },
    {
      id: 'alert-003',
      time: timeStr,
      code: '002918', name: '蒙娜丽莎', price: 18.63, change: 10.0,
      buyPointType: '龙头首阴',
      logic: '6板空间龙，缩量回踩5日线，筹码锁定',
      tactics: '龙头首阴战法',
      riskLevel: '高',
      stopLoss: -6,
      stopLossPrice: 17.51,
      sector: '建筑材料',
      isMainLine: true,
      confidence: 68,
    },
  ];
}

// ── 生成持仓股数据 ──
export function generateHoldingStocks(): HoldingStock[] {
  return [
    {
      code: '001259', name: '利仁科技',
      costPrice: 55.0, currentPrice: 60.5, quantity: 1000,
      profitLoss: 10.0, profitLossAmount: 5500,
      ma5: 52.3, ma10: 45.8, ma20: 38.5,
      trendStatus: '多头',
      volumeStatus: '量价齐升',
      sector: '消费电子', sectorPhase: '主升', sectorIsMainLine: true,
      isLeader: true, isMainLine: true, holdLogicValid: true,
      stopLossLine: -5, takeProfitLine: 20, maxDrawdown: -2.1,
      alertTriggered: [],
    },
    {
      code: '002031', name: '巨轮智能',
      costPrice: 7.8, currentPrice: 8.4, quantity: 5000,
      profitLoss: 7.69, profitLossAmount: 3000,
      ma5: 7.5, ma10: 7.2, ma20: 6.8,
      trendStatus: '支撑',
      volumeStatus: '放量滞涨',
      sector: '机器人', sectorPhase: '启动', sectorIsMainLine: false,
      isLeader: false, isMainLine: false, holdLogicValid: false,
      stopLossLine: -5, takeProfitLine: 15, maxDrawdown: -3.5,
      alertTriggered: ['量能异常', '逻辑失效'],
    },
  ];
}

// ── 生成持仓提醒 ──
export function generateHoldingAlerts(holdings: HoldingStock[]): HoldingAlert[] {
  const alerts: HoldingAlert[] = [];
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  holdings.forEach(h => {
    // 趋势破位检查
    if (h.currentPrice < h.ma10 && h.trendStatus === '破位') {
      alerts.push({
        type: '趋势破位',
        code: h.code, name: h.name,
        message: `${h.name} 跌破10日线(${h.ma10.toFixed(2)})，当前价${h.currentPrice.toFixed(2)}`,
        time: timeStr,
        action: '减仓',
        urgency: '高',
      });
    }
    
    // 量能异常检查
    if (h.volumeStatus === '放量滞涨' || h.volumeStatus === '放量杀跌') {
      alerts.push({
        type: '量能异常',
        code: h.code, name: h.name,
        message: `${h.name} ${h.volumeStatus}，注意风险`,
        time: timeStr,
        action: '减仓',
        urgency: '中',
      });
    }
    
    // 板块退潮检查
    if (h.sectorPhase === '退潮' && h.sectorIsMainLine === false) {
      alerts.push({
        type: '板块退潮',
        code: h.code, name: h.name,
        message: `${h.name} 所属板块【${h.sector}】进入退潮期`,
        time: timeStr,
        action: '卖出',
        urgency: '高',
      });
    }
    
    // 逻辑失效检查
    if (!h.holdLogicValid) {
      alerts.push({
        type: '逻辑失效',
        code: h.code, name: h.name,
        message: `${h.name} 持有逻辑失效：非主线题材，非龙头梯队`,
        time: timeStr,
        action: '卖出',
        urgency: '紧急',
      });
    }
    
    // 止损检查
    if (h.profitLoss <= h.stopLossLine) {
      alerts.push({
        type: '止损提醒',
        code: h.code, name: h.name,
        message: `${h.name} 触及止损线(${h.stopLossLine}%)，当前亏损${h.profitLoss.toFixed(2)}%`,
        time: timeStr,
        action: '止损',
        urgency: '紧急',
      });
    }
    
    // 止盈检查
    if (h.profitLoss >= h.takeProfitLine) {
      alerts.push({
        type: '止盈提醒',
        code: h.code, name: h.name,
        message: `${h.name} 达到止盈目标(${h.takeProfitLine}%)，当前盈利${h.profitLoss.toFixed(2)}%`,
        time: timeStr,
        action: '止盈',
        urgency: '中',
      });
    }
  });
  
  return alerts;
}

// ── 生成回测结果 ──
export function generateBacktestResult(): BacktestResult {
  return {
    period: '2025-01-01 ~ 2026-05-15',
    totalTrades: 156,
    winRate: 68.5,
    avgWin: 12.3,
    avgLoss: -5.8,
    profitLossRatio: 2.12,
    maxDrawdown: -15.6,
    totalReturn: 128.5,
    sharpeRatio: 1.85,
    byBuyPoint: [
      { type: '主升加速', count: 45, winRate: 72.2, avgReturn: 15.6 },
      { type: '弱转强', count: 38, winRate: 65.8, avgReturn: 10.2 },
      { type: '龙头首阴', count: 28, winRate: 57.1, avgReturn: 8.5 },
      { type: '二波启动', count: 45, winRate: 75.6, avgReturn: 18.3 },
    ],
    byPhase: [
      { phase: '启动期', count: 25, winRate: 56.0, avgReturn: 6.8 },
      { phase: '发酵期', count: 42, winRate: 66.7, avgReturn: 10.5 },
      { phase: '主升期', count: 68, winRate: 76.5, avgReturn: 16.2 },
      { phase: '退潮期', count: 21, winRate: 38.1, avgReturn: -3.2 },
    ],
  };
}

// ── 生成每日复盘 ──
export function generateDailyReview(): DailyReview {
  return {
    date: '2026-05-15',
    phase: '主升期',
    mainLine: '消费电子',
    leaders: [
      { code: '002918', name: '蒙娜丽莎', boards: 6 },
      { code: '001259', name: '利仁科技', boards: 5 },
      { code: '600578', name: '京能电力', boards: 3 },
    ],
    opportunities: [
      '利仁科技5板主升加速买点',
      '光华股份弱转强买点',
      '蒙娜丽莎龙头首阴买点',
    ],
    missedOpportunities: [
      '巨轮智能早盘弱转强未及时介入',
    ],
    mistakes: [
      '巨轮智能非主线题材持仓过久',
    ],
    summary: '市场处于主升期，消费电子为主线，蒙娜丽莎6板空间龙，利仁科技5板跟风。赚钱效应良好，连板溢价显著。',
    nextDayPlan: '重点关注消费电子板块持续性，蒙娜丽莎6板能否继续拓展空间，利仁科技5板晋级情况。',
  };
}

// ── 生成操作日志 ──
export function generateTradeLogs(): TradeLog[] {
  return [
    {
      id: 'T001', date: '2026-05-12', code: '001259', name: '利仁科技',
      action: '买入', price: 45.45, quantity: 1000, amount: 45450,
      buyPointType: '主升加速', reason: '3板晋级4板，主升加速买点',
      result: '盈利', profitLoss: 33.1, holdDays: 3,
      review: '买点精准，持股待涨',
    },
    {
      id: 'T002', date: '2026-05-13', code: '002031', name: '巨轮智能',
      action: '买入', price: 7.29, quantity: 5000, amount: 36450,
      buyPointType: '弱转强', reason: '机器人板块回流，弱转强买点',
      result: '盈利', profitLoss: 15.2, holdDays: 2,
      review: '非主线题材，应及时止盈',
    },
    {
      id: 'T003', date: '2026-05-14', code: '001333', name: '光华股份',
      action: '买入', price: 23.68, quantity: 2000, amount: 47360,
      buyPointType: '弱转强', reason: '首阴反包，分歧转一致',
      result: '盈利', profitLoss: 10.0, holdDays: 1,
      review: '买点确认，继续持有',
    },
  ];
}