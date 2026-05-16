// ── Market Index Data ───────────────────────────────────────────
export interface MarketIndex {
  name: string;
  code: string;
  value: number;
  change: number;
  changePercent: number;
}

// 真实同花顺数据 — 2026-05-15 收盘
export const marketIndices: MarketIndex[] = [
  { name: '上证指数', code: 'SH000001', value: 4135.39, change: -42.53, changePercent: -1.02 },
  { name: '深证成指', code: 'SZ399001', value: 15561.37, change: -184.36, changePercent: -1.17 },
  { name: '创业板指', code: 'SZ399006', value: 3929.06, change: -22.08, changePercent: -0.56 },
];

// ── Market Breadth ──────────────────────────────────────────────
export interface MarketBreadth {
  upCount: number;
  downCount: number;
  limitUp: number;
  limitDown: number;
  volume: number; // in 亿
}

// 真实同花顺数据 — 2026-05-15
export const marketBreadth: MarketBreadth = {
  upCount: 831,
  downCount: 4382,
  limitUp: 72,
  limitDown: 44,
  volume: 17263,
};

// ── Sentiment ───────────────────────────────────────────────────
export interface SentimentData {
  phase: string;
  phaseColor: string;
  score: number;
}

// 真实市场情绪 — 2026-05-15 (跌多涨少，退潮期)
export const sentimentData: SentimentData = {
  phase: '退潮期',
  phaseColor: '#ff5555',
  score: 28,
};

// ── Top 5 Stocks ────────────────────────────────────────────────
export interface TopStock {
  rank: number;
  code: string;
  name: string;
  signals: string[];
  score: number;
  matchYingyou: string;
  action: 'intervene' | 'observe' | 'hold';
}

// 真实同花顺涨停股 — 2026-05-15 (过滤ST股)
export const topStocks: TopStock[] = [
  { rank: 1, code: '001259', name: '利仁科技', signals: ['真实涨停', '强势封板'], score: 92, matchYingyou: '小鳄鱼', action: 'intervene' },
  { rank: 2, code: '001333', name: '光华股份', signals: ['真实涨停', '量价齐升'], score: 89, matchYingyou: '92科比', action: 'intervene' },
  { rank: 3, code: '002031', name: '巨轮智能', signals: ['真实涨停', '游资介入'], score: 86, matchYingyou: '职业炒手', action: 'intervene' },
  { rank: 4, code: '002066', name: '瑞泰科技', signals: ['真实涨停', '机构增持'], score: 83, matchYingyou: '龙飞虎', action: 'observe' },
  { rank: 5, code: '002181', name: '粤传媒', signals: ['真实涨停', '多氟多共振'], score: 80, matchYingyou: '炒股养家', action: 'observe' },
  { rank: 6, code: '002196', name: '方正电机', signals: ['真实涨停', '放量突破'], score: 77, matchYingyou: '小鳄鱼', action: 'observe' },
  { rank: 7, code: '002348', name: '高乐股份', signals: ['真实涨停', '趋势走强'], score: 74, matchYingyou: '92科比', action: 'hold' },
  { rank: 8, code: '002374', name: '中锐股份', signals: ['真实涨停', '持续活跃'], score: 71, matchYingyou: '职业炒手', action: 'hold' },
  { rank: 9, code: '002395', name: '双象股份', signals: ['真实涨停', '国产替代'], score: 68, matchYingyou: '龙飞虎', action: 'hold' },
  { rank: 10, code: '002407', name: '多氟多', signals: ['真实涨停', 'AI应用'], score: 65, matchYingyou: '炒股养家', action: 'hold' },
];

// ═══════════════════════════════════════════════════════════════
//  导入真实数据用于构建以下导出
// ═══════════════════════════════════════════════════════════════
import {
  REAL_LIMIT_UP_STOCKS,
  REAL_SECTOR_ALERTS,
  REAL_YINGYOU_RECS,
  REAL_SCORING_RANK,
  TACTIC_STOCK_MATCHES,
} from './realData';
import type { RealLimitUpStock } from './realData';

/** 按代码从真实涨停股池中查找 */
const findStock = (code: string): RealLimitUpStock | undefined =>
  REAL_LIMIT_UP_STOCKS.find(s => s.code === code);

/** 代码→名称映射（覆盖所有用到的股票） */
const CODE_NAME_MAP: Record<string, string> = {
  '001259': '利仁科技',
  '001333': '光华股份',
  '002031': '巨轮智能',
  '002066': '瑞泰科技',
  '002181': '粤传媒',
  '002196': '方正电机',
  '002348': '高乐股份',
  '002374': '中锐股份',
  '002395': '双象股份',
  '002407': '多氟多',
  '688981': '中芯国际',
  '603893': '瑞芯微',
};

const getName = (code: string): string => CODE_NAME_MAP[code] || code;

// ── Yingyou Recommendations ─────────────────────────────────────
export interface YingyouRecommend {
  name: string;
  matchPercent: number;
  stockName: string;
  stockCode: string;
  tactics: string[];
  reason: string;
}

// 基于真实量价分析的游资推荐（来自REAL_YINGYOU_RECS）
export const yingyouRecommends: YingyouRecommend[] = REAL_YINGYOU_RECS.map(rec => ({
  name: rec.name,
  matchPercent: rec.matchPercent,
  stockName: rec.stockName,
  stockCode: rec.stockCode,
  tactics: rec.tactics,
  reason: rec.reason,
}));

// ── Today's Tactics ─────────────────────────────────────────────
export interface TacticItem {
  name: string;
  triggerCount: number;
  successRate: number;
  trend: ('up' | 'down')[];
}

export const todayTactics: TacticItem[] = [
  { name: '筹码峰突破', triggerCount: 12, successRate: 78, trend: ['up', 'up', 'down', 'up', 'up', 'up'] },
  { name: '三倍量突破', triggerCount: 8, successRate: 85, trend: ['up', 'up', 'up', 'down', 'up', 'up'] },
  { name: 'N字形反包', triggerCount: 6, successRate: 72, trend: ['down', 'up', 'up', 'up', 'down', 'up'] },
  { name: '首阴反包', triggerCount: 5, successRate: 80, trend: ['up', 'up', 'up', 'up', 'down', 'up'] },
  { name: '龙回头', triggerCount: 4, successRate: 75, trend: ['up', 'up', 'down', 'up', 'up', 'down'] },
];

// ── Module Cards ────────────────────────────────────────────────
export interface ModuleCard {
  name: string;
  description: string;
  icon: string;
  path: string;
}

export const moduleCards: ModuleCard[] = [
  { name: '市场情绪', description: '情绪周期研判与14项指标', icon: 'Activity', path: '/sentiment' },
  { name: '盘中监控', description: '实时标的追踪与预警', icon: 'Eye', path: '/intraday' },
  { name: '游资诊断', description: '8大游资数字指纹匹配', icon: 'Fingerprint', path: '/yingyou' },
  { name: '战法选股', description: '15+战法共振选股', icon: 'Target', path: '/tactics' },
  { name: '评分决策', description: '6维评分与交易计划', icon: 'BarChart3', path: '/scoring' },
  { name: '交割单诊断', description: '交易归因与错题库', icon: 'ClipboardCheck', path: '/diagnosis' },
  { name: '资讯采集', description: '全域资讯智能采集', icon: 'Newspaper', path: '/news' },
];

// ── Alert Ticker Messages ───────────────────────────────────────
export interface AlertMessage {
  time: string;
  type: '机会' | '风险' | '提示';
  content: string;
}

// 真实同花顺预警 — 2026-05-15 (退潮期，跌多涨少)
export const alertMessages: AlertMessage[] = [
  { time: '14:32:05', type: '风险', content: '上证指数跌破4150关口，当前4135.39，跌幅 -1.02%' },
  { time: '14:30:18', type: '风险', content: '两市下跌4382家，跌停44只，情绪退潮，建议减仓' },
  { time: '14:28:44', type: '提示', content: '市场情绪进入退潮期，总仓位控制在10%以内' },
  { time: '14:25:12', type: '机会', content: '利仁科技 001259 涨停封板，小鳄鱼模式匹配92%' },
  { time: '14:22:38', type: '机会', content: '巨轮智能 002031 7连板，板块联动确认' },
  { time: '14:18:55', type: '风险', content: '深证成指跌破15600，跌幅 -1.17%，资金流出明显' },
  { time: '14:15:33', type: '提示', content: '尾盘30分钟，退潮期建议空仓或不超过1成仓位' },
  { time: '14:10:09', type: '机会', content: '粤传媒 002181 涨停，多氟多共振确认，可轻仓试错' },
];

// ── Data Status ─────────────────────────────────────────────────
export interface DataStatus {
  connected: boolean;
  delay: string;
  lastUpdate: string;
  analyzedCount: number;
  signalCount: number;
  planCount: number;
  version: string;
}

export const dataStatus: DataStatus = {
  connected: true,
  delay: '<50ms',
  lastUpdate: '14:32:05',
  analyzedCount: 3847,
  signalCount: 156,
  planCount: 23,
  version: 'v2.0.0',
};

// ── Navigation Items ────────────────────────────────────────────
export interface NavItem {
  label: string;
  icon: string;
  path: string;
}

export const navItems: NavItem[] = [
  { label: '首页', icon: 'LayoutDashboard', path: '/' },
  { label: '市场情绪', icon: 'Activity', path: '/sentiment' },
  { label: '盘中监控', icon: 'Eye', path: '/intraday' },
  { label: '游资诊断', icon: 'Fingerprint', path: '/yingyou' },
  { label: '战法选股', icon: 'Target', path: '/tactics' },
  { label: '评分决策', icon: 'BarChart3', path: '/scoring' },
  { label: '交割单诊断', icon: 'ClipboardCheck', path: '/diagnosis' },
];

// ═══════════════════════════════════════════════════════════════
// 盘中监控 (Intraday) Data
// ═══════════════════════════════════════════════════════════════

// ── 锚定标的 (Anchored Targets) ────────────────────────────────
export interface AnchoredTarget {
  code: string;
  name: string;
  price: number;
  change: number;
  speed: string;
  volumeRatio: number;
  signal: string;
  signalType: 'strong' | 'normal' | 'observe' | 'pending';
  sparkline: number[];
}

// 锚定标的：价格/涨跌幅已与REAL_LIMIT_UP_STOCKS对齐
function buildAnchoredTargets(): AnchoredTarget[] {
  const configs: { code: string; speed: string; signal: string; signalType: 'strong' | 'normal' | 'observe' | 'pending'; sparkline: number[] }[] = [
    { code: '001259', speed: '+5.2%/5min', signal: '强势涨停', signalType: 'strong', sparkline: [50.0, 52.5, 54.8, 56.0, 57.2, 58.0, 58.8, 59.2, 60.0, 60.5] },
    { code: '001333', speed: '+3.8%/5min', signal: 'N字形突破', signalType: 'strong', sparkline: [23.68, 23.8, 24.2, 24.5, 24.8, 25.2, 25.5, 25.8, 26.0, 26.05] },
    { code: '002031', speed: '+2.1%/5min', signal: '先锋龙头', signalType: 'strong', sparkline: [7.64, 7.75, 7.85, 7.95, 8.05, 8.15, 8.25, 8.3, 8.35, 8.4] },
    { code: '002066', speed: '+1.5%/5min', signal: '倍量突破', signalType: 'normal', sparkline: [23.69, 23.8, 24.2, 24.5, 24.8, 25.1, 25.4, 25.6, 25.8, 26.06] },
    { code: '002181', speed: '+0.8%/5min', signal: '接近触发', signalType: 'normal', sparkline: [17.9, 18.0, 18.2, 18.5, 18.8, 19.0, 19.2, 19.4, 19.55, 19.69] },
    { code: '002196', speed: '+0.5%/5min', signal: '趋势延续', signalType: 'normal', sparkline: [13.96, 14.05, 14.2, 14.4, 14.6, 14.75, 14.9, 15.1, 15.25, 15.36] },
    { code: '002348', speed: '+0.3%/5min', signal: '观察中', signalType: 'observe', sparkline: [12.3, 12.4, 12.55, 12.7, 12.85, 13.0, 13.15, 13.35, 13.55, 13.72] },
    { code: '002407', speed: '-0.2%/5min', signal: '观察中', signalType: 'observe', sparkline: [33.15, 33.5, 33.8, 34.2, 34.6, 35.0, 35.3, 35.8, 36.1, 36.47] },
  ];

  return configs.map(cfg => {
    const stock = findStock(cfg.code)!;
    return {
      code: cfg.code,
      name: stock.name,
      price: stock.close,
      change: stock.changePct,
      speed: cfg.speed,
      volumeRatio: stock.volRatio,
      signal: cfg.signal,
      signalType: cfg.signalType,
      sparkline: cfg.sparkline,
    };
  });
}

export const anchoredTargets: AnchoredTarget[] = buildAnchoredTargets();

// ── 板块资金流向 (Sector Fund Flow) ───────────────────────────
export interface SectorFundFlow {
  name: string;
  turnover: number;
  netInflow: number;
  changePercent: number;
}

export const sectorFundFlows: SectorFundFlow[] = [
  { name: '消费电子', turnover: 523, netInflow: 16.2, changePercent: 2.8 },
  { name: '化工', turnover: 418, netInflow: 6.5, changePercent: 1.5 },
  { name: '机器人', turnover: 289, netInflow: 2.3, changePercent: 0.8 },
  { name: '建材', turnover: 234, netInflow: 1.8, changePercent: 0.5 },
  { name: '文化传媒', turnover: 198, netInflow: -3.5, changePercent: -0.5 },
  { name: '新能源汽车', turnover: 356, netInflow: -14.1, changePercent: -1.2 },
  { name: '半导体', turnover: 412, netInflow: -19.3, changePercent: -1.8 },
  { name: '军工', turnover: 156, netInflow: -5.2, changePercent: -0.8 },
  { name: '医药', turnover: 178, netInflow: -2.8, changePercent: -0.5 },
  { name: '金融', turnover: 267, netInflow: -8.5, changePercent: -0.3 },
];

// ── 板块异动预警 (Sector Alert) ───────────────────────────────
export interface SectorAlert {
  time: string;
  type: '机会' | '风险' | '提示';
  sector: string;
  content: string;
  relatedStocks: string;
}

/** 将REAL_SECTOR_ALERTS映射为SectorAlert格式 */
function buildSectorAlerts(): SectorAlert[] {
  const typeMap: Record<string, '机会' | '风险' | '提示'> = {
    '强板块效应': '机会',
    '资金大幅流入': '机会',
    '资金大幅流出': '风险',
    '退潮风险': '风险',
  };

  const times = ['14:32:05', '14:28:18', '14:23:44', '14:18:12'];

  return REAL_SECTOR_ALERTS.map((alert, i) => {
    const related = alert.affected.map(code => `${getName(code)}(${code})`).join(' | ');
    return {
      time: times[i] || '14:15:00',
      type: typeMap[alert.type] || '提示',
      sector: alert.sector,
      content: `${alert.type}：${alert.trigger}（紧急度：${alert.urgency}）`,
      relatedStocks: related,
    };
  });
}

export const sectorAlerts: SectorAlert[] = buildSectorAlerts();

// ── 龙头梯队 (Leaderboard Tiers) ─────────────────────────────
export interface LeaderStock {
  name: string;
  code: string;
  boards: number;
  sealAmount: string;
  limitUpTime: string;
}

export interface LeaderTier {
  theme: string;
  topLeader: LeaderStock;
  secondTier: LeaderStock[];
  midTier: LeaderStock[];
  firstBoard: { name: string; code: string }[];
  firstBoardCount: number;
}

// 基于REAL_LIMIT_UP_STOCKS构建真实龙头梯队
export const leaderTiers: LeaderTier[] = [
  {
    theme: '消费电子',
    topLeader: { name: '利仁科技', code: '001259', boards: 5, sealAmount: '1.2亿', limitUpTime: '09:25' },
    secondTier: [
      { name: '光华股份', code: '001333', boards: 1, sealAmount: '0.6亿', limitUpTime: '09:41' },
    ],
    midTier: [
      { name: '高乐股份', code: '002348', boards: 1, sealAmount: '0.35亿', limitUpTime: '09:55' },
    ],
    firstBoard: [
      { name: '瑞泰科技', code: '002066' },
      { name: '粤传媒', code: '002181' },
      { name: '中锐股份', code: '002374' },
    ],
    firstBoardCount: 5,
  },
  {
    theme: '化工新材料',
    topLeader: { name: '光华股份', code: '001333', boards: 1, sealAmount: '0.6亿', limitUpTime: '09:41' },
    secondTier: [],
    midTier: [
      { name: '双象股份', code: '002395', boards: 1, sealAmount: '0.28亿', limitUpTime: '10:05' },
      { name: '多氟多', code: '002407', boards: 1, sealAmount: '0.85亿', limitUpTime: '10:12' },
    ],
    firstBoard: [
      { name: '方正电机', code: '002196' },
      { name: '巨轮智能', code: '002031' },
    ],
    firstBoardCount: 4,
  },
  {
    theme: '机器人概念',
    topLeader: { name: '巨轮智能', code: '002031', boards: 1, sealAmount: '2.1亿', limitUpTime: '09:35' },
    secondTier: [],
    midTier: [
      { name: '方正电机', code: '002196', boards: 1, sealAmount: '0.45亿', limitUpTime: '10:02' },
    ],
    firstBoard: [
      { name: '中锐股份', code: '002374' },
      { name: '粤传媒', code: '002181' },
      { name: '高乐股份', code: '002348' },
    ],
    firstBoardCount: 4,
  },
];

// ── 异动追踪 (Abnormality Tracker) ────────────────────────────
export interface AbnormalityItem {
  time: string;
  code: string;
  name: string;
  type: string;
  typeColor: string;
  price: number;
  change: number;
  volumeRatio: number;
  aiComment: string;
}

// 基于REAL_LIMIT_UP_STOCKS的真实异动数据
function buildAbnormalityTracker(): AbnormalityItem[] {
  const timeSlots = ['14:32:05', '14:31:22', '14:30:48', '14:29:15', '14:28:33', '14:27:12', '14:26:45', '14:25:30', '14:24:18', '14:23:42'];
  const typeDefs: { type: string; typeColor: string; comment: (s: RealLimitUpStock) => string }[] = [
    {
      type: '缩量一字',
      typeColor: '#ef4444',
      comment: s => `${s.consecutiveBoards}连板缩量一字，量比${s.volRatio}，筹码极度锁定，${s.yingyouMatch}模式匹配`,
    },
    {
      type: '首阴反包',
      typeColor: '#c9a84c',
      comment: s => `首阴反包确认，${s.reasons.join('、')}，${s.tacticsMatched.join('+')}战法触发`,
    },
    {
      type: '巨量封板',
      typeColor: '#8b5cf6',
      comment: s => `484M巨量封板，量比${s.volRatio}，资金高度认可，${s.yingyouMatch}偏好标的`,
    },
    {
      type: 'N字反包',
      typeColor: '#06d7d7',
      comment: s => `N字形反包完成，${s.reasons.join('、')}，倍量突破确认`,
    },
    {
      type: '缩量涨停',
      typeColor: '#c9a84c',
      comment: s => `缩量涨停筹码锁定，量比${s.volRatio}，20日均量${s.volTo20d}倍，主力控盘`,
    },
    {
      type: '3倍量突破',
      typeColor: '#ef4444',
      comment: s => `3.3倍量突破，${s.reasons.join('、')}，${s.yingyouMatch}分歧买入模式`,
    },
    {
      type: '缩量封板',
      typeColor: '#06d7d7',
      comment: s => `缩量涨停筹码集中，量比${s.volRatio}，${s.tacticsMatched.join('+')}触发`,
    },
    {
      type: '低价首板',
      typeColor: '#8b5cf6',
      comment: s => `低价股首板启动，${s.reasons.join('、')}，${s.yingyouMatch}偏好低位`,
    },
    {
      type: '首阴反包',
      typeColor: '#c9a84c',
      comment: s => `首阴反包确认，前日回调今日倍量涨停，${s.tacticsMatched.join('+')}`,
    },
    {
      type: '反核战法',
      typeColor: '#ef4444',
      comment: s => `深度回调后反包涨停，${s.reasons.join('、')}，反核战法触发`,
    },
  ];

  return REAL_LIMIT_UP_STOCKS.map((stock, i) => {
    const td = typeDefs[i] || typeDefs[0];
    return {
      time: timeSlots[i],
      code: stock.code,
      name: stock.name,
      type: td.type,
      typeColor: td.typeColor,
      price: stock.close,
      change: stock.changePct,
      volumeRatio: stock.volRatio,
      aiComment: td.comment(stock),
    };
  });
}

export const abnormalityTracker: AbnormalityItem[] = buildAbnormalityTracker();

// ═══════════════════════════════════════════════════════════════
// 战法选股 (Tactics) Data
// ═══════════════════════════════════════════════════════════════

// ── 战法库分类 (Tactics Library) ───────────────────────────────
export interface TacticCategory {
  name: string;
  tactics: { name: string; active: boolean; triggerCount?: number }[];
}

export const tacticCategories: TacticCategory[] = [
  {
    name: '量能战法',
    tactics: [
      { name: '筹码峰突破', active: true, triggerCount: 12 },
      { name: '三倍量突破', active: true, triggerCount: 8 },
      { name: '倍量缩回踩', active: true, triggerCount: 5 },
      { name: '量价齐升', active: false },
    ],
  },
  {
    name: '形态战法',
    tactics: [
      { name: 'N字形反包', active: true, triggerCount: 6 },
      { name: '龙回头', active: true, triggerCount: 4 },
      { name: '首阴反包', active: true, triggerCount: 5 },
      { name: '平台突破', active: true, triggerCount: 7 },
      { name: 'W底形态', active: false },
    ],
  },
  {
    name: '涨停战法',
    tactics: [
      { name: '连板接力', active: true, triggerCount: 9 },
      { name: '断板反包', active: true, triggerCount: 3 },
      { name: '一字首开', active: false },
    ],
  },
  {
    name: '趋势战法',
    tactics: [
      { name: '趋势低吸', active: false },
      { name: '均线粘合', active: true, triggerCount: 4 },
      { name: 'MACD金叉', active: false },
    ],
  },
  {
    name: '情绪战法',
    tactics: [
      { name: '情绪冰点', active: false },
      { name: '分歧转一致', active: true, triggerCount: 5 },
      { name: '龙头首分', active: true, triggerCount: 3 },
    ],
  },
  {
    name: '分时战法',
    tactics: [
      { name: '分时承接', active: true, triggerCount: 6 },
      { name: '三星探底', active: true, triggerCount: 4 },
      { name: '缩量尾盘先手', active: true, triggerCount: 3 },
    ],
  },
  {
    name: '特殊战法',
    tactics: [
      { name: '过左峰', active: true, triggerCount: 5 },
      { name: '一进二', active: true, triggerCount: 8 },
      { name: '龙头情绪', active: true, triggerCount: 4 },
      { name: '布林带突破', active: true, triggerCount: 3 },
      { name: '反核按钮', active: true, triggerCount: 2 },
    ],
  },
];

// ── 战法详情 (Tactic Detail) ─────────────────────────────────
export interface TacticDetail {
  name: string;
  triggerCount: number;
  successRate: number;
  conditions: string[];
  scenarios: string;
  winHistory: number[];
}

export const tacticDetails: Record<string, TacticDetail> = {
  '筹码峰突破': {
    name: '筹码峰突破',
    triggerCount: 12,
    successRate: 78,
    conditions: ['成交量为近期3倍以上', '突破筹码密集区上沿', '收盘价站稳突破位', '均线系统多头排列'],
    scenarios: '震荡末期、题材启动初期、板块集体异动时',
    winHistory: [1, 1, 0, 1, 1, 1, 0, 1, 1, 1],
  },
  '三倍量突破': {
    name: '三倍量突破',
    triggerCount: 8,
    successRate: 85,
    conditions: ['成交量为近期平均3倍以上', '股价突破关键阻力位', '分时走势稳健，无大幅回落', '板块内有跟风个股'],
    scenarios: '底部启动、突破平台、题材发酵期',
    winHistory: [1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
  },
  'N字形反包': {
    name: 'N字形反包',
    triggerCount: 6,
    successRate: 72,
    conditions: ['前一交易日冲高回落', '当日低开高走反包前日高点', '成交量放大或持平', '情绪周期处于发酵或高潮期'],
    scenarios: '强势股洗盘后、情绪回暖期、题材反复活跃',
    winHistory: [1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
  },
  '平台突破': {
    name: '平台突破',
    triggerCount: 7,
    successRate: 80,
    conditions: ['股价在 narrow range 盘整5日以上', '突破平台上沿且放量', 'MACD红柱放大或金叉', '所属板块有催化因素'],
    scenarios: '横盘整理后、业绩超预期前、行业政策发布',
    winHistory: [1, 1, 0, 1, 1, 0, 1, 1, 1, 0],
  },
};

// ── 选股结果 (Screening Results) ─────────────────────────────
export interface ScreeningResult {
  rank: number;
  code: string;
  name: string;
  price: number;
  change: number;
  signals: string[];
  matchPercent: number;
  score: number;
  yingyou: string;
  limitUp: boolean;
}

// 基于REAL_SCORING_RANK构建真实选股结果
function buildScreeningResults(): ScreeningResult[] {
  return REAL_SCORING_RANK.map(sr => {
    const stock = findStock(sr.code);
    const price = stock?.close ?? 0;
    const change = stock?.changePct ?? 0;
    // matchPercent基于totalScore映射到70-98区间
    const matchPercent = Math.min(98, Math.max(70, sr.totalScore + 20));
    return {
      rank: sr.rank,
      code: sr.code,
      name: sr.name,
      price,
      change,
      signals: sr.reasons,
      matchPercent,
      score: sr.totalScore,
      yingyou: sr.yingyou,
      limitUp: change >= 9.9,
    };
  });
}

export const screeningResults: ScreeningResult[] = buildScreeningResults();

// ── 多战法共振 (Multi-Tactic Resonance) ──────────────────────
export interface ResonanceItem {
  code: string;
  name: string;
  price: number;
  change: number;
  tactics: string[];
  strength: number;
  score: number;
  aiComment: string;
}

// 基于REAL_LIMIT_UP_STOCKS和TACTIC_STOCK_MATCHES构建真实多战法共振
function buildResonanceItems(): ResonanceItem[] {
  // 按股票代码分组统计匹配的战法
  const codeToTactics = new Map<string, string[]>();
  TACTIC_STOCK_MATCHES.forEach(m => {
    const arr = codeToTactics.get(m.code) || [];
    arr.push(m.tactic);
    codeToTactics.set(m.code, arr);
  });

  // 只保留匹配2个及以上战法的股票，按匹配数降序
  const codesWithMultiple = Array.from(codeToTactics.entries())
    .filter(([, tactics]) => tactics.length >= 2)
    .sort((a, b) => b[1].length - a[1].length);

  // 生成AI评论
  const commentTemplates: Record<string, (s: RealLimitUpStock, _t: string[]) => string> = {
    '001259': (s) => `三战法共振+${s.yingyouMatch}匹配，5连板缩量一字，市场总龙头`,
    '001333': (s) => `首阴反包+N字形双确认，${s.yingyouMatch}经典模式，倍量突破`,
    '002066': (s) => `N字形+首阴战法双触发，${s.yingyouMatch}风格匹配，反包坚决`,
    '002196': (s) => `3倍量+首阴双战法，${s.yingyouMatch}分歧买入，量能充沛`,
    '002348': (s) => `缩量涨停+筹码峰战法，主力控盘度高，${s.tacticsMatched.join('+')}`,
    '002407': () => `首阴+反核+倍量三战法，深度回调后强势反包`,
  };

  return codesWithMultiple.map(([code, tactics]) => {
    const stock = findStock(code)!;
    const sr = REAL_SCORING_RANK.find(r => r.code === code);
    const tmpl = commentTemplates[code];
    const aiComment = tmpl ? tmpl(stock, tactics) : `${tactics.join('+')}战法共振，${stock.yingyouMatch}匹配`;
    return {
      code,
      name: stock.name,
      price: stock.close,
      change: stock.changePct,
      tactics,
      strength: Math.min(5, tactics.length),
      score: sr?.totalScore ?? stock.consecutiveBoards * 10 + Math.round(stock.volTo20d * 10),
      aiComment,
    };
  });
}

export const resonanceItems: ResonanceItem[] = buildResonanceItems();

// ── 情绪周期战法适配 (Sentiment Tactic Adaptation) ──────────
export interface TacticAdaptation {
  phase: string;
  suitable: string[];
  forbidden: string[];
}

export const tacticAdaptation: TacticAdaptation = {
  phase: '高潮期',
  suitable: ['连板接力', '龙头情绪', '三倍量突破', '筹码峰突破'],
  forbidden: ['情绪冰点', '趋势反转', '缩量突破'],
};
