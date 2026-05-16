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

export const anchoredTargets: AnchoredTarget[] = [
  { code: '002837', name: '英维克', price: 18.56, change: 9.8, speed: '+2.3%/5min', volumeRatio: 3.2, signal: '三倍量突破', signalType: 'strong', sparkline: [16.8, 17.0, 17.2, 17.1, 17.5, 17.8, 18.0, 18.2, 18.4, 18.56] },
  { code: '600520', name: '文一科技', price: 25.30, change: 6.2, speed: '+1.1%/5min', volumeRatio: 2.1, signal: '筹码峰异动', signalType: 'normal', sparkline: [23.5, 23.8, 24.0, 24.2, 24.1, 24.5, 24.8, 25.0, 25.1, 25.30] },
  { code: '300308', name: '中际旭创', price: 42.18, change: -1.5, speed: '-0.8%/5min', volumeRatio: 0.9, signal: '观察中', signalType: 'observe', sparkline: [43.0, 42.8, 42.6, 42.5, 42.4, 42.3, 42.2, 42.0, 42.1, 42.18] },
  { code: '000938', name: '中芯国际', price: 8.92, change: 4.1, speed: '+0.5%/5min', volumeRatio: 1.5, signal: '接近触发', signalType: 'normal', sparkline: [8.5, 8.55, 8.6, 8.58, 8.62, 8.65, 8.7, 8.75, 8.8, 8.92] },
  { code: '688981', name: '中芯微', price: 65.40, change: 7.3, speed: '+1.8%/5min', volumeRatio: 2.8, signal: 'N字形', signalType: 'strong', sparkline: [60.5, 61.0, 61.5, 62.0, 62.5, 63.0, 63.8, 64.2, 64.8, 65.40] },
  { code: '002230', name: '科大讯飞', price: 12.35, change: 0.2, speed: '+0.1%/5min', volumeRatio: 1.0, signal: '等待', signalType: 'pending', sparkline: [12.2, 12.25, 12.28, 12.3, 12.32, 12.31, 12.33, 12.34, 12.35, 12.35] },
  { code: '600111', name: '北方稀土', price: 21.68, change: 5.6, speed: '+1.5%/5min', volumeRatio: 2.4, signal: '倍量突破', signalType: 'strong', sparkline: [20.2, 20.4, 20.6, 20.5, 20.8, 21.0, 21.2, 21.4, 21.5, 21.68] },
  { code: '300750', name: '宁德时代', price: 185.30, change: -0.8, speed: '-0.2%/5min', volumeRatio: 0.7, signal: '观察中', signalType: 'observe', sparkline: [187.0, 186.5, 186.0, 186.2, 185.8, 185.5, 185.4, 185.2, 185.0, 185.30] },
];

// ── 板块资金流向 (Sector Fund Flow) ───────────────────────────
export interface SectorFundFlow {
  name: string;
  turnover: number;
  netInflow: number;
  changePercent: number;
}

export const sectorFundFlows: SectorFundFlow[] = [
  { name: '人工智能', turnover: 523, netInflow: 45.2, changePercent: 3.2 },
  { name: '新能源车', turnover: 418, netInflow: 32.1, changePercent: 2.1 },
  { name: '半导体', turnover: 356, netInflow: -12.5, changePercent: -0.8 },
  { name: '机器人', turnover: 289, netInflow: 18.3, changePercent: 1.5 },
  { name: '光伏', turnover: 234, netInflow: -8.2, changePercent: -0.5 },
  { name: '医药', turnover: 198, netInflow: 5.1, changePercent: 0.3 },
  { name: '军工', turnover: 156, netInflow: -3.8, changePercent: -0.2 },
  { name: '金融', turnover: 412, netInflow: 22.7, changePercent: 1.8 },
  { name: '地产', turnover: 178, netInflow: -6.4, changePercent: -0.7 },
  { name: '消费', turnover: 267, netInflow: 8.9, changePercent: 0.8 },
];

// ── 板块异动预警 (Sector Alert) ───────────────────────────────
export interface SectorAlert {
  time: string;
  type: '机会' | '风险' | '提示';
  sector: string;
  content: string;
  relatedStocks: string;
}

export const sectorAlerts: SectorAlert[] = [
  { time: '14:32:05', type: '机会', sector: '人工智能', content: '多股集体拉升，资金快速流入', relatedStocks: '英维克 +9.8% | 中际旭创 +7.2%' },
  { time: '14:28:18', type: '风险', sector: '半导体', content: '龙头股跳水，板块跟跌', relatedStocks: '中芯微 -3.5% | 北方华创 -2.1%' },
  { time: '14:25:44', type: '机会', sector: '新能源车', content: '政策利好催化，板块异动', relatedStocks: '宁德时代 +5.2% | 比亚迪 +4.8%' },
  { time: '14:20:12', type: '提示', sector: '光伏', content: '资金持续流出，注意风险', relatedStocks: '隆基绿能 -1.8% | 通威股份 -1.2%' },
  { time: '14:15:33', type: '机会', sector: '机器人', content: '涨停潮启动，情绪高涨', relatedStocks: '埃斯顿涨停 | 机器人 +8.1%' },
];

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

export const leaderTiers: LeaderTier[] = [
  {
    theme: '人工智能',
    topLeader: { name: '英维克', code: '002837', boards: 6, sealAmount: '2.3亿', limitUpTime: '09:35' },
    secondTier: [
      { name: '中际旭创', code: '300308', boards: 4, sealAmount: '1.2亿', limitUpTime: '09:42' },
      { name: '科大讯飞', code: '002230', boards: 3, sealAmount: '0.8亿', limitUpTime: '10:05' },
    ],
    midTier: [
      { name: '昆仑万维', code: '300418', boards: 2, sealAmount: '0.5亿', limitUpTime: '10:28' },
      { name: '拓尔思', code: '300229', boards: 2, sealAmount: '0.3亿', limitUpTime: '10:45' },
      { name: '汉王科技', code: '002362', boards: 2, sealAmount: '0.4亿', limitUpTime: '11:02' },
    ],
    firstBoard: [
      { name: '云从科技', code: '688327' },
      { name: '商汤科技', code: '600728' },
      { name: '寒武纪', code: '688256' },
      { name: '海康威视', code: '002415' },
    ],
    firstBoardCount: 8,
  },
  {
    theme: '新能源车',
    topLeader: { name: '比亚迪', code: '002594', boards: 5, sealAmount: '3.1亿', limitUpTime: '09:38' },
    secondTier: [
      { name: '宁德时代', code: '300750', boards: 3, sealAmount: '1.5亿', limitUpTime: '09:55' },
      { name: '天赐材料', code: '002709', boards: 3, sealAmount: '0.9亿', limitUpTime: '10:12' },
    ],
    midTier: [
      { name: '恩捷股份', code: '002812', boards: 2, sealAmount: '0.6亿', limitUpTime: '10:35' },
      { name: '璞泰来', code: '603659', boards: 2, sealAmount: '0.4亿', limitUpTime: '10:48' },
      { name: '新宙邦', code: '300037', boards: 2, sealAmount: '0.3亿', limitUpTime: '11:05' },
    ],
    firstBoard: [
      { name: '亿纬锂能', code: '300014' },
      { name: '国轩高科', code: '002074' },
      { name: '欣旺达', code: '300207' },
    ],
    firstBoardCount: 6,
  },
  {
    theme: '半导体',
    topLeader: { name: '中芯国际', code: '688981', boards: 4, sealAmount: '1.8亿', limitUpTime: '09:45' },
    secondTier: [
      { name: '北方华创', code: '002371', boards: 3, sealAmount: '1.0亿', limitUpTime: '10:02' },
      { name: '韦尔股份', code: '603501', boards: 2, sealAmount: '0.7亿', limitUpTime: '10:25' },
    ],
    midTier: [
      { name: '兆易创新', code: '603986', boards: 2, sealAmount: '0.5亿', limitUpTime: '10:40' },
      { name: '紫光国微', code: '002049', boards: 2, sealAmount: '0.4亿', limitUpTime: '10:55' },
      { name: '圣邦股份', code: '300661', boards: 1, sealAmount: '-', limitUpTime: '-' },
    ],
    firstBoard: [
      { name: '卓胜微', code: '300782' },
      { name: '澜起科技', code: '688008' },
      { name: '沪硅产业', code: '688126' },
    ],
    firstBoardCount: 5,
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

export const abnormalityTracker: AbnormalityItem[] = [
  { time: '14:32:05', code: '002837', name: '英维克', type: '放量突破', typeColor: '#ef4444', price: 18.56, change: 9.8, volumeRatio: 3.2, aiComment: '三倍量突破筹码峰，游资模式匹配91%' },
  { time: '14:31:22', code: '600520', name: '文一科技', type: '快速拉升', typeColor: '#c9a84c', price: 25.30, change: 6.2, volumeRatio: 2.1, aiComment: '5分钟拉升4%，疑似游资介入' },
  { time: '14:30:48', code: '300308', name: '中际旭创', type: '大单买入', typeColor: '#8b5cf6', price: 42.18, change: 3.5, volumeRatio: 1.8, aiComment: '万手大单连续买入，关注封板' },
  { time: '14:29:15', code: '000938', name: '中芯国际', type: '放量突破', typeColor: '#ef4444', price: 8.92, change: 4.1, volumeRatio: 1.5, aiComment: '突破近期平台，量能放大' },
  { time: '14:28:33', code: '688981', name: '中芯微', type: '尾盘异动', typeColor: '#06d7d7', price: 65.40, change: 7.3, volumeRatio: 2.8, aiComment: 'N字形形态确认，资金持续流入' },
  { time: '14:27:12', code: '002230', name: '科大讯飞', type: '快速拉升', typeColor: '#c9a84c', price: 12.35, change: 2.8, volumeRatio: 1.9, aiComment: 'AI概念催化，资金关注度提升' },
  { time: '14:26:45', code: '600111', name: '北方稀土', type: '大单买入', typeColor: '#8b5cf6', price: 21.68, change: 5.6, volumeRatio: 2.4, aiComment: '稀土永磁概念，机构+游资合力' },
  { time: '14:25:30', code: '300750', name: '宁德时代', type: '放量突破', typeColor: '#ef4444', price: 185.30, change: -0.8, volumeRatio: 0.7, aiComment: '新能源龙头，调整后有望反弹' },
];

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

export const screeningResults: ScreeningResult[] = [
  { rank: 1, code: '002837', name: '英维克', price: 18.56, change: 9.8, signals: ['筹码峰+', '三倍量'], matchPercent: 98, score: 94, yingyou: '炒股养家', limitUp: true },
  { rank: 2, code: '600520', name: '文一科技', price: 25.30, change: 6.2, signals: ['筹码峰', 'N字形'], matchPercent: 95, score: 91, yingyou: '92科比', limitUp: false },
  { rank: 3, code: '300308', name: '中际旭创', price: 42.18, change: 3.5, signals: ['三倍量突破'], matchPercent: 92, score: 88, yingyou: '小鳄鱼', limitUp: false },
  { rank: 4, code: '000938', name: '中芯国际', price: 8.92, change: 4.1, signals: ['筹码峰异动'], matchPercent: 88, score: 85, yingyou: '龙飞虎', limitUp: false },
  { rank: 5, code: '688981', name: '中芯微', price: 65.40, change: 7.3, signals: ['N字形确认'], matchPercent: 85, score: 82, yingyou: '涅槃重生', limitUp: false },
  { rank: 6, code: '002230', name: '科大讯飞', price: 12.35, change: 2.1, signals: ['倍量突破'], matchPercent: 82, score: 79, yingyou: '退学炒股', limitUp: false },
  { rank: 7, code: '600111', name: '北方稀土', price: 21.68, change: 1.8, signals: ['筹码峰弱信号'], matchPercent: 78, score: 75, yingyou: '职业炒手', limitUp: false },
  { rank: 8, code: '300750', name: '宁德时代', price: 185.30, change: 0.5, signals: ['三倍量(待确认)'], matchPercent: 75, score: 72, yingyou: 'Asking', limitUp: false },
  { rank: 9, code: '002812', name: '恩捷股份', price: 45.60, change: 5.2, signals: ['平台突破', '倍量'], matchPercent: 90, score: 87, yingyou: '作手新一', limitUp: false },
  { rank: 10, code: '603659', name: '璞泰来', price: 32.18, change: 3.8, signals: ['N字形', '龙回头'], matchPercent: 87, score: 83, yingyou: '赵老哥', limitUp: false },
];

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

export const resonanceItems: ResonanceItem[] = [
  { code: '002837', name: '英维克', price: 18.56, change: 9.8, tactics: ['筹码峰+', '三倍量', 'N字形'], strength: 5, score: 94, aiComment: '三战法共振+养家匹配，今日最强信号' },
  { code: '600520', name: '文一科技', price: 25.30, change: 6.2, tactics: ['筹码峰', 'N字形', '龙回头'], strength: 4, score: 91, aiComment: '形态+量能双确认，92科比模式匹配' },
  { code: '300308', name: '中际旭创', price: 42.18, change: 3.5, tactics: ['三倍量', '首阴', '平台突破'], strength: 4, score: 88, aiComment: '量价+形态共振，封板概率高' },
  { code: '000938', name: '中芯国际', price: 8.92, change: 4.1, tactics: ['筹码峰', '倍量缩回踩'], strength: 3, score: 85, aiComment: '量能战法双触发，观察持续性' },
  { code: '688981', name: '中芯微', price: 65.40, change: 7.3, tactics: ['N字形', '三倍量', '连板接力', '龙头情绪'], strength: 5, score: 93, aiComment: '四战法共振，龙头气质尽显' },
  { code: '002230', name: '科大讯飞', price: 12.35, change: 2.8, tactics: ['平台突破', '分时承接'], strength: 2, score: 79, aiComment: '分时+形态共振，适合低吸' },
];

// ── 情绪周期战法适配 (Sentiment Tactic Adaptation) ──────────
export interface TacticAdaptation {
  phase: string;
  suitable: string[];
  forbidden: string[];
}

export const tacticAdaptation: TacticAdaptation = {
  phase: '高潮期',
  suitable: ['连板接力', '龙头情绪', '三倍量突破', '筹码峰突破'],
  forbidden: ['情绪冰点', '趋势低吸', '缩量尾盘先手'],
};
