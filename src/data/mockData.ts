// ── Market Index Data ───────────────────────────────────────────
export interface MarketIndex {
  name: string;
  code: string;
  value: number;
  change: number;
  changePercent: number;
}

export const marketIndices: MarketIndex[] = [
  { name: '上证指数', code: 'SH000001', value: 3247.85, change: 38.72, changePercent: 1.21 },
  { name: '深证成指', code: 'SZ399001', value: 10523.61, change: 90.56, changePercent: 0.87 },
  { name: '创业板指', code: 'SZ399006', value: 2089.32, change: 32.14, changePercent: 1.56 },
];

// ── Market Breadth ──────────────────────────────────────────────
export interface MarketBreadth {
  upCount: number;
  downCount: number;
  limitUp: number;
  limitDown: number;
  volume: number; // in 亿
}

export const marketBreadth: MarketBreadth = {
  upCount: 3248,
  downCount: 1652,
  limitUp: 68,
  limitDown: 3,
  volume: 8234.56,
};

// ── Sentiment ───────────────────────────────────────────────────
export interface SentimentData {
  phase: string;
  phaseColor: string;
  score: number;
}

export const sentimentData: SentimentData = {
  phase: '高潮期',
  phaseColor: '#c9a84c',
  score: 78,
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

export const topStocks: TopStock[] = [
  {
    rank: 1,
    code: '002837',
    name: '英维克',
    signals: ['筹码峰+', '三倍量'],
    score: 94,
    matchYingyou: '炒股养家',
    action: 'intervene',
  },
  {
    rank: 2,
    code: '600520',
    name: '文一科技',
    signals: ['N字形', '龙回头'],
    score: 91,
    matchYingyou: '92科比',
    action: 'intervene',
  },
  {
    rank: 3,
    code: '300308',
    name: '中际旭创',
    signals: ['首阴', '倍量突破'],
    score: 88,
    matchYingyou: '小鳄鱼',
    action: 'observe',
  },
  {
    rank: 4,
    code: '000938',
    name: '中芯国际',
    signals: ['平台突破'],
    score: 85,
    matchYingyou: '龙飞虎',
    action: 'observe',
  },
  {
    rank: 5,
    code: '688981',
    name: '中芯国际',
    signals: ['量价齐升'],
    score: 82,
    matchYingyou: '涅槃重生',
    action: 'hold',
  },
];

// ── Yingyou Recommendations ─────────────────────────────────────
export interface YingyouRecommend {
  name: string;
  matchPercent: number;
  stockName: string;
  stockCode: string;
  tactics: string[];
  reason: string;
}

export const yingyouRecommends: YingyouRecommend[] = [
  {
    name: '炒股养家',
    matchPercent: 92,
    stockName: '英维克',
    stockCode: '002837',
    tactics: ['筹码峰+', '首阴'],
    reason: '养家一致性+封单强度双信号',
  },
  {
    name: '92科比',
    matchPercent: 88,
    stockName: '文一科技',
    stockCode: '600520',
    tactics: ['N字形', '龙回头'],
    reason: '梯队完整性+题材发酵期',
  },
  {
    name: '小鳄鱼',
    matchPercent: 85,
    stockName: '中际旭创',
    stockCode: '300308',
    tactics: ['三倍量突破'],
    reason: '量价共振+板块龙头',
  },
];

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

export const alertMessages: AlertMessage[] = [
  { time: '14:32:05', type: '机会', content: '英维克 002837 出现三倍量突破信号，当前涨幅 +7.2%' },
  { time: '14:30:18', type: '风险', content: '创业板指30分钟内下跌 -1.5%，触发风控预警' },
  { time: '14:28:44', type: '提示', content: '市场情绪由发酵期进入高潮期，建议提高警惕' },
  { time: '14:25:12', type: '机会', content: '炒股养家模式匹配：文一科技 600520 匹配度91%' },
  { time: '14:22:38', type: '机会', content: '中际旭创 300308 N字形反包确认，建议关注' },
  { time: '14:18:55', type: '风险', content: '半导体板块资金流向转负，净流出 -12.3亿' },
  { time: '14:15:33', type: '提示', content: '尾盘30分钟，建议控制仓位在50%以内' },
  { time: '14:10:09', type: '机会', content: '首阴战法触发：中芯国际 000938 回踩5日线' },
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
  version: 'v2.4.1',
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
