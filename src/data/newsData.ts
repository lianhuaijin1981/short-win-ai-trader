/* ================================================================
   资讯采集系统数据模型与模拟数据
   基于历史回测的消息类型对个股走势重要性研判机制
   ================================================================ */

// ═══════════════════════════════════════════════════════════════
// 资讯来源定义
// ═══════════════════════════════════════════════════════════════

export type NewsSource = 
  | '巨潮资讯' 
  | '上交所官网' 
  | '深交所官网' 
  | '财联社' 
  | '同花顺' 
  | '东方财富' 
  | '淘股吧' 
  | '韭研公社' 
  | '雪球网' 
  | '开盘啦';

export const NEWS_SOURCES: NewsSource[] = [
  '巨潮资讯', '上交所官网', '深交所官网', '财联社', 
  '同花顺', '东方财富', '淘股吧', '韭研公社', '雪球网', '开盘啦'
];

// 资讯来源可靠性评级
export const SOURCE_RELIABILITY: Record<NewsSource, number> = {
  '巨潮资讯': 95,    // 官方公告，最可靠
  '上交所官网': 95,  // 官方监管信息
  '深交所官网': 95,  // 官方监管信息
  '财联社': 85,      // 专业财经媒体
  '同花顺': 80,      // 专业数据平台
  '东方财富': 80,    // 专业数据平台
  '开盘啦': 70,      // 短线资讯平台
  '韭研公社': 65,    // 社区研究平台
  '雪球网': 60,      // 投资社区
  '淘股吧': 55,      // 散户社区
};

// ═══════════════════════════════════════════════════════════════
// 资讯类型定义
// ═══════════════════════════════════════════════════════════════

export type NewsCategory = 
  | '公司公告' 
  | '监管政策' 
  | '行业动态' 
  | '宏观经济' 
  | '资金流向' 
  | '游资动向' 
  | '题材催化' 
  | '风险提示'
  | '业绩预告'
  | '股权变动'
  | '重组并购'
  | '股东增减持'
  | '龙虎榜数据'
  | '研报评级';

export const NEWS_CATEGORIES: NewsCategory[] = [
  '公司公告', '监管政策', '行业动态', '宏观经济', '资金流向', 
  '游资动向', '题材催化', '风险提示', '业绩预告', '股权变动',
  '重组并购', '股东增减持', '龙虎榜数据', '研报评级'
];

// ═══════════════════════════════════════════════════════════════
// 消息重要性研判等级
// ═══════════════════════════════════════════════════════════════

export type ImportanceLevel = '重大利好' | '一般利好' | '中性' | '一般利空' | '重大利空';

export const IMPORTANCE_LEVELS: ImportanceLevel[] = ['重大利好', '一般利好', '中性', '一般利空', '重大利空'];

export const IMPORTANCE_COLORS: Record<ImportanceLevel, string> = {
  '重大利好': '#ef4444',  // 红色
  '一般利好': '#f97316',  // 橙色
  '中性': '#6b7280',      // 灰色
  '一般利空': '#3b82f6',  // 蓝色
  '重大利空': '#22c55e',  // 绿色（A股跌用绿）
};

// ═══════════════════════════════════════════════════════════════
// 历史回测统计数据
// ═══════════════════════════════════════════════════════════════

export interface BacktestStats {
  // 该类型消息出现次数
  occurrenceCount: number;
  // 消息后1日上涨概率
  day1UpRate: number;
  // 消息后3日上涨概率
  day3UpRate: number;
  // 消息后5日上涨概率
  day5UpRate: number;
  // 平均最大涨幅(%)
  avgMaxGain: number;
  // 平均最大跌幅(%)
  avgMaxLoss: number;
  // 胜率(上涨次数/总次数)
  winRate: number;
  // 盈亏比
  profitLossRatio: number;
}

// 各消息类型的历史回测统计（基于A股2020-2026年数据模拟）
export const CATEGORY_BACKTEST_STATS: Record<NewsCategory, BacktestStats> = {
  '公司公告': {
    occurrenceCount: 12580, day1UpRate: 52, day3UpRate: 48, day5UpRate: 45,
    avgMaxGain: 3.2, avgMaxLoss: -2.8, winRate: 48, profitLossRatio: 1.14
  },
  '监管政策': {
    occurrenceCount: 856, day1UpRate: 68, day3UpRate: 72, day5UpRate: 75,
    avgMaxGain: 8.5, avgMaxLoss: -3.2, winRate: 72, profitLossRatio: 2.66
  },
  '行业动态': {
    occurrenceCount: 4520, day1UpRate: 58, day3UpRate: 55, day5UpRate: 52,
    avgMaxGain: 4.8, avgMaxLoss: -3.5, winRate: 55, profitLossRatio: 1.37
  },
  '宏观经济': {
    occurrenceCount: 1280, day1UpRate: 55, day3UpRate: 52, day5UpRate: 50,
    avgMaxGain: 3.5, avgMaxLoss: -3.0, winRate: 52, profitLossRatio: 1.17
  },
  '资金流向': {
    occurrenceCount: 8960, day1UpRate: 62, day3UpRate: 58, day5UpRate: 55,
    avgMaxGain: 5.2, avgMaxLoss: -3.8, winRate: 58, profitLossRatio: 1.37
  },
  '游资动向': {
    occurrenceCount: 3250, day1UpRate: 65, day3UpRate: 60, day5UpRate: 55,
    avgMaxGain: 7.8, avgMaxLoss: -5.2, winRate: 60, profitLossRatio: 1.50
  },
  '题材催化': {
    occurrenceCount: 5680, day1UpRate: 70, day3UpRate: 65, day5UpRate: 58,
    avgMaxGain: 9.2, avgMaxLoss: -4.5, winRate: 65, profitLossRatio: 2.04
  },
  '风险提示': {
    occurrenceCount: 2150, day1UpRate: 35, day3UpRate: 32, day5UpRate: 30,
    avgMaxGain: 2.1, avgMaxLoss: -6.8, winRate: 30, profitLossRatio: 0.31
  },
  '业绩预告': {
    occurrenceCount: 6890, day1UpRate: 72, day3UpRate: 68, day5UpRate: 62,
    avgMaxGain: 7.5, avgMaxLoss: -5.5, winRate: 68, profitLossRatio: 1.36
  },
  '股权变动': {
    occurrenceCount: 1580, day1UpRate: 58, day3UpRate: 55, day5UpRate: 52,
    avgMaxGain: 4.2, avgMaxLoss: -3.5, winRate: 55, profitLossRatio: 1.20
  },
  '重组并购': {
    occurrenceCount: 980, day1UpRate: 82, day3UpRate: 78, day5UpRate: 72,
    avgMaxGain: 15.8, avgMaxLoss: -8.5, winRate: 78, profitLossRatio: 1.86
  },
  '股东增减持': {
    occurrenceCount: 4250, day1UpRate: 45, day3UpRate: 42, day5UpRate: 40,
    avgMaxGain: 2.8, avgMaxLoss: -4.5, winRate: 42, profitLossRatio: 0.62
  },
  '龙虎榜数据': {
    occurrenceCount: 12580, day1UpRate: 58, day3UpRate: 52, day5UpRate: 48,
    avgMaxGain: 5.5, avgMaxLoss: -4.2, winRate: 52, profitLossRatio: 1.31
  },
  '研报评级': {
    occurrenceCount: 28560, day1UpRate: 55, day3UpRate: 52, day5UpRate: 50,
    avgMaxGain: 3.8, avgMaxLoss: -2.5, winRate: 52, profitLossRatio: 1.52
  },
};

// ═══════════════════════════════════════════════════════════════
// 资讯数据模型
// ═══════════════════════════════════════════════════════════════

export interface NewsItem {
  id: string;
  // 发布时间
  publishTime: string;
  // 资讯来源
  source: NewsSource;
  // 资讯类型
  category: NewsCategory;
  // 标题
  title: string;
  // 摘要
  summary: string;
  // 详细内容
  content: string;
  // 关联板块
  relatedSectors: string[];
  // 关联个股
  relatedStocks: { code: string; name: string }[];
  // 重要性等级
  importance: ImportanceLevel;
  // 重要性评分(0-100)
  importanceScore: number;
  // 历史回测统计
  backtestStats: BacktestStats;
  // 介入建议
  suggestion: NewsSuggestion | null;
  // 风险预警
  riskWarning: RiskWarning | null;
  // 是否已读
  isRead: boolean;
  // 用户标记
  userTag: '关注' | '忽略' | null;
}

// 介入建议
export interface NewsSuggestion {
  // 建议类型
  type: '积极介入' | '谨慎介入' | '观望等待' | '逢高减仓';
  // 建议仓位(%)
  suggestedPosition: number;
  // 建议买入区间
  buyRange: { low: number; high: number };
  // 建议止损位
  stopLoss: number;
  // 建议止盈位
  takeProfit: number;
  // 持有周期
  holdingPeriod: '超短(1-2日)' | '短线(3-5日)' | '中线(1-2周)';
  // 建议理由
  reason: string;
  // 置信度(%)
  confidence: number;
}

// 风险预警
export interface RiskWarning {
  // 风险等级
  level: '高风险' | '中风险' | '低风险';
  // 风险类型
  riskType: '政策风险' | '业绩风险' | '减持风险' | '退市风险' | '流动性风险' | '系统性风险';
  // 风险描述
  description: string;
  // 影响范围
  impactScope: '个股' | '板块' | '大盘';
  // 建议操作
  suggestedAction: string;
  // 预警时间
  warningTime: string;
}

// ═══════════════════════════════════════════════════════════════
// 重要性研判引擎
// ═══════════════════════════════════════════════════════════════

// 计算资讯重要性评分
export function calculateImportanceScore(
  category: NewsCategory,
  source: NewsSource,
  contentLength: number,
  hasStocks: boolean,
  hasSectors: boolean
): number {
  let score = 50; // 基础分
  
  // 消息类型权重（基于回测胜率）
  const categoryWeight = CATEGORY_BACKTEST_STATS[category].winRate - 50;
  score += categoryWeight * 0.4;
  
  // 来源可靠性权重
  score += (SOURCE_RELIABILITY[source] - 50) * 0.2;
  
  // 内容完整度
  score += Math.min(10, contentLength / 100) * 0.5;
  
  // 关联标的
  if (hasStocks) score += 5;
  if (hasSectors) score += 3;
  
  return Math.max(0, Math.min(100, Math.round(score)));
}

// 根据评分确定重要性等级
export function getImportanceLevel(score: number, category: NewsCategory): ImportanceLevel {
  const stats = CATEGORY_BACKTEST_STATS[category];
  const winRate = stats.winRate;
  
  if (score >= 80 && winRate >= 65) return '重大利好';
  if (score >= 65 && winRate >= 55) return '一般利好';
  if (score >= 45 && winRate >= 45) return '中性';
  if (score >= 35 && winRate < 45) return '一般利空';
  return '重大利空';
}

// 生成介入建议
export function generateSuggestion(
  importance: ImportanceLevel,
  stats: BacktestStats,
  stockPrice: number
): NewsSuggestion | null {
  if (importance === '重大利空' || importance === '一般利空') return null;
  
  const baseConfidence = stats.winRate;
  
  if (importance === '重大利好' && baseConfidence >= 65) {
    return {
      type: '积极介入',
      suggestedPosition: 30,
      buyRange: { 
        low: Math.round(stockPrice * 0.98 * 100) / 100, 
        high: Math.round(stockPrice * 1.02 * 100) / 100 
      },
      stopLoss: Math.round(stockPrice * 0.92 * 100) / 100,
      takeProfit: Math.round(stockPrice * 1.15 * 100) / 100,
      holdingPeriod: '短线(3-5日)',
      reason: `历史回测显示该类消息后${stats.day1UpRate}%概率上涨，平均最大涨幅${stats.avgMaxGain}%`,
      confidence: Math.min(90, baseConfidence + 10)
    };
  }
  
  if (importance === '一般利好' && baseConfidence >= 55) {
    return {
      type: '谨慎介入',
      suggestedPosition: 15,
      buyRange: { 
        low: Math.round(stockPrice * 0.97 * 100) / 100, 
        high: Math.round(stockPrice * 1.01 * 100) / 100 
      },
      stopLoss: Math.round(stockPrice * 0.95 * 100) / 100,
      takeProfit: Math.round(stockPrice * 1.08 * 100) / 100,
      holdingPeriod: '超短(1-2日)',
      reason: `历史回测胜率${stats.winRate}%，建议轻仓试水`,
      confidence: Math.min(75, baseConfidence)
    };
  }
  
  return {
    type: '观望等待',
    suggestedPosition: 0,
    buyRange: { low: 0, high: 0 },
    stopLoss: 0,
    takeProfit: 0,
    holdingPeriod: '短线(3-5日)',
    reason: '消息面中性，建议观察市场反应后再决策',
    confidence: 50
  };
}

// 生成风险预警
export function generateRiskWarning(
  importance: ImportanceLevel,
  category: NewsCategory,
  title: string
): RiskWarning | null {
  if (importance !== '重大利空' && importance !== '一般利空') return null;
  
  let riskType: RiskWarning['riskType'];
  let level: RiskWarning['level'];
  let description: string;
  let action: string;
  
  switch (category) {
    case '风险提示':
      riskType = '业绩风险';
      level = importance === '重大利空' ? '高风险' : '中风险';
      description = title;
      action = '建议及时减仓或清仓，规避后续下跌风险';
      break;
    case '股东增减持':
      riskType = '减持风险';
      level = '中风险';
      description = title;
      action = '建议关注减持进度，逢高减仓';
      break;
    case '监管政策':
      riskType = '政策风险';
      level = importance === '重大利空' ? '高风险' : '中风险';
      description = title;
      action = '建议规避相关板块，等待政策明朗';
      break;
    default:
      riskType = '流动性风险';
      level = '低风险';
      description = title;
      action = '建议降低仓位，控制风险';
  }
  
  return {
    level,
    riskType,
    description,
    impactScope: '个股',
    suggestedAction: action,
    warningTime: new Date().toLocaleTimeString('zh-CN')
  };
}

// ═══════════════════════════════════════════════════════════════
// 模拟资讯数据
// ═══════════════════════════════════════════════════════════════

export const MOCK_NEWS: NewsItem[] = [
  // 重大利好 - 监管政策
  {
    id: 'news-001',
    publishTime: '2026-06-10 21:30:00',
    source: '财联社',
    category: '监管政策',
    title: '【政策利好】国务院：加快培育数据要素市场，推进数据资产入表试点',
    summary: '国务院印发《关于加快数据要素市场化配置改革的指导意见》，提出加快培育数据要素市场，推进数据资产入表试点，数据要素概念股有望受益。',
    content: '国务院今日印发《关于加快数据要素市场化配置改革的指导意见》，明确提出加快培育数据要素市场，推进数据资产入表试点工作，支持符合条件的数据服务企业上市融资。文件还提出建立数据产权制度，推动数据跨境流动。',
    relatedSectors: ['数据要素', 'AI营销', '数字经济'],
    relatedStocks: [
      { code: '002354', name: '天娱数科' },
      { code: '300496', name: '中科创达' },
      { code: '603881', name: '数据港' }
    ],
    importance: '重大利好',
    importanceScore: 88,
    backtestStats: CATEGORY_BACKTEST_STATS['监管政策'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 10,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '中线(1-2周)',
      reason: '监管政策类消息历史回测胜率72%，但当前处于退潮期，涨停71家/跌停44家，建议轻仓试水',
      confidence: 65
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利好 - 题材催化
  {
    id: 'news-002',
    publishTime: '2026-06-10 20:15:00',
    source: '同花顺',
    category: '题材催化',
    title: '【AI营销催化】天娱数科4连板成最高标，AI营销+数据要素双轮驱动',
    summary: '天娱数科今日缩量涨停走出4连板，成为当前市场最高连板标的，AI营销+数据要素概念受资金追捧。',
    content: '天娱数科(002354)今日缩量涨停，走出4连板行情，成为当前市场最高连板标的。公司主营AI营销业务，同时布局数据要素赛道。从龙虎榜来看，知名游资小鳄鱼现身买方。但当前市场处于退潮期，涨停71家/跌停44家，追高需谨慎。',
    relatedSectors: ['AI营销', '数据要素', '数字经济'],
    relatedStocks: [
      { code: '002354', name: '天娱数科' },
      { code: '002636', name: '金安国纪' },
      { code: '600500', name: '中化国际' }
    ],
    importance: '一般利好',
    importanceScore: 72,
    backtestStats: CATEGORY_BACKTEST_STATS['题材催化'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '题材催化类消息历史回测胜率65%，但4连板高位+退潮期，追高风险极大',
      confidence: 45
    },
    riskWarning: {
      level: '高风险',
      riskType: '流动性风险',
      description: '4连板高位股，退潮期追高风险极大，可能面临连续跌停',
      impactScope: '个股',
      suggestedAction: '退潮期严禁追高，等待回调或新周期确认',
      warningTime: '20:15:00'
    },
    isRead: false,
    userTag: null
  },
  // 一般利好 - 龙虎榜数据
  {
    id: 'news-003',
    publishTime: '2026-06-10 18:30:00',
    source: '同花顺',
    category: '龙虎榜数据',
    title: '【龙虎榜】金安国纪获游资炒股养家买入，3连板覆铜板龙头',
    summary: '金安国纪今日登上龙虎榜，知名游资炒股养家现身买方，该股今日走出3连板行情。',
    content: '金安国纪(002636)今日因连续3个交易日涨幅偏离值累计达20%登上龙虎榜。买方席位中，炒股养家所在营业部买入约3200万元。该股为覆铜板龙头，受益于PCB材料需求增长。',
    relatedSectors: ['覆铜板', 'PCB材料', '电子元件'],
    relatedStocks: [
      { code: '002636', name: '金安国纪' },
      { code: '600500', name: '中化国际' }
    ],
    importance: '一般利好',
    importanceScore: 65,
    backtestStats: CATEGORY_BACKTEST_STATS['龙虎榜数据'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '龙虎榜显示游资买入，但3连板高位+退潮期，建议观望',
      confidence: 50
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 行业动态
  {
    id: 'news-004',
    publishTime: '2026-06-10 17:00:00',
    source: '东方财富',
    category: '行业动态',
    title: '【行业动态】6月10日涨停71家/跌停44家，市场处于退潮期',
    summary: '今日A股涨停71家，跌停44家，连板高度压缩至4板，市场情绪处于退潮阶段。',
    content: '据同花顺数据，6月10日A股涨停71家，跌停44家，涨停/跌停比1.61，连板高度仅4板（天娱数科）。从情绪周期来看，当前处于退潮期，建议总仓位控制在1成以内。历史数据显示，退潮期涨停股次日溢价率仅35%左右。',
    relatedSectors: ['大盘'],
    relatedStocks: [],
    importance: '中性',
    importanceScore: 55,
    backtestStats: CATEGORY_BACKTEST_STATS['行业动态'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '退潮期涨停71家/跌停44家，建议总仓位控制在1成以内，等待新周期确认',
      confidence: 70
    },
    riskWarning: {
      level: '中风险',
      riskType: '系统性风险',
      description: '市场处于退潮期，涨停71家/跌停44家，情绪极度恶化',
      impactScope: '大盘',
      suggestedAction: '退潮期总仓位控制在1成以内，严禁追高',
      warningTime: '17:00:00'
    },
    isRead: false,
    userTag: null
  },
  // 一般利好 - 资金流向
  {
    id: 'news-005',
    publishTime: '2026-06-10 15:30:00',
    source: '东方财富',
    category: '资金流向',
    title: '【资金动向】今日主力资金净流入AI营销板块，天娱数科获净买入1.2亿',
    summary: '今日主力资金净流入AI营销板块2.8亿元，天娱数科获净买入1.2亿元居首。',
    content: '今日主力资金流向显示，AI营销板块获净流入2.8亿元，其中天娱数科获净买入1.2亿元居首，金安国纪获净买入8500万元。但整体市场资金呈净流出状态，主力资金全天净流出约180亿元。',
    relatedSectors: ['AI营销', '数据要素'],
    relatedStocks: [
      { code: '002354', name: '天娱数科' },
      { code: '002636', name: '金安国纪' }
    ],
    importance: '一般利好',
    importanceScore: 62,
    backtestStats: CATEGORY_BACKTEST_STATS['资金流向'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 5,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '资金流向类消息历史回测胜率58%，但退潮期资金持续性存疑',
      confidence: 48
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利空 - 股东减持
  {
    id: 'news-006',
    publishTime: '2026-06-10 17:45:00',
    source: '巨潮资讯',
    category: '股东增减持',
    title: '【减持公告】中化国际股东拟减持不超过2%股份',
    summary: '中化国际公告，持股5%以上股东计划在未来3个月内通过集中竞价方式减持不超过公司总股本2%的股份。',
    content: '中化国际(600500)今日公告，公司股东因自身资金需求，计划自本公告披露之日起3个交易日后的3个月内，通过集中竞价交易方式减持公司股份不超过2800万股，即不超过公司总股本的2%。',
    relatedSectors: ['化学制品', '国企改革'],
    relatedStocks: [
      { code: '600500', name: '中化国际' }
    ],
    importance: '一般利空',
    importanceScore: 38,
    backtestStats: CATEGORY_BACKTEST_STATS['股东增减持'],
    suggestion: null,
    riskWarning: {
      level: '中风险',
      riskType: '减持风险',
      description: '大股东拟减持不超过2%股份，可能对股价形成压制',
      impactScope: '个股',
      suggestedAction: '建议关注减持进展，若股价跌破支撑位建议减仓',
      warningTime: '17:45:00'
    },
    isRead: false,
    userTag: null
  },
  // 重大利空 - 风险提示
  {
    id: 'news-007',
    publishTime: '2026-06-10 16:30:00',
    source: '巨潮资讯',
    category: '风险提示',
    title: '【退市风险】*STXX公司股票可能被终止上市的风险提示',
    summary: '*STXX公司股票已被实施退市风险警示，若2025年度经审计的净利润为负且营业收入低于1亿元，公司股票将被终止上市。',
    content: '*STXX公司发布风险提示公告，公司股票交易已被实施退市风险警示。根据深交所规则，若公司2025年度经审计的净利润为负值且营业收入低于1亿元，或者财务会计报告被出具无法表示意见，公司股票将被终止上市。',
    relatedSectors: [],
    relatedStocks: [
      { code: '000XXX', name: '*STXX' }
    ],
    importance: '重大利空',
    importanceScore: 15,
    backtestStats: CATEGORY_BACKTEST_STATS['风险提示'],
    suggestion: null,
    riskWarning: {
      level: '高风险',
      riskType: '退市风险',
      description: '公司面临退市风险，股价可能出现连续跌停',
      impactScope: '个股',
      suggestedAction: '强烈建议立即清仓，规避退市风险',
      warningTime: '16:30:00'
    },
    isRead: false,
    userTag: null
  },
  // 一般利好 - 游资动向
  {
    id: 'news-008',
    publishTime: '2026-06-10 14:30:00',
    source: '淘股吧',
    category: '游资动向',
    title: '【游资追踪】小鳄鱼今日介入天娱数科，4连板最高标',
    summary: '据龙虎榜数据，知名游资小鳄鱼今日买入天娱数科约4500万元，该股今日走出4连板行情。',
    content: '天娱数科(002354)今日缩量涨停走出4连板，龙虎榜显示小鳄鱼所在营业部买入4500万元。该股为AI营销+数据要素概念，当前市场最高连板标的。但退潮期高位股风险较大。',
    relatedSectors: ['AI营销', '数据要素'],
    relatedStocks: [
      { code: '002354', name: '天娱数科' }
    ],
    importance: '一般利好',
    importanceScore: 60,
    backtestStats: CATEGORY_BACKTEST_STATS['游资动向'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '游资动向类消息历史回测胜率60%，但4连板+退潮期，追高风险极大',
      confidence: 40
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 研报评级
  {
    id: 'news-009',
    publishTime: '2026-06-10 13:00:00',
    source: '雪球网',
    category: '研报评级',
    title: '【研报】中信证券：维持中化国际"买入"评级，目标价12元',
    summary: '中信证券发布研报，维持中化国际"买入"评级，认为公司化学制品业务稳健增长，目标价12元。',
    content: '中信证券发布中化国际深度研究报告，认为公司作为化学制品央企龙头，受益于国企改革深化，预计2026年净利润同比增长25%。维持"买入"评级，给予2026年15倍PE，目标价12元。',
    relatedSectors: ['化学制品', '国企改革'],
    relatedStocks: [
      { code: '600500', name: '中化国际' }
    ],
    importance: '中性',
    importanceScore: 48,
    backtestStats: CATEGORY_BACKTEST_STATS['研报评级'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '中线(1-2周)',
      reason: '研报评级类消息历史回测胜率52%，短期影响有限，建议关注基本面变化',
      confidence: 48
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利空 - 宏观经济
  {
    id: 'news-010',
    publishTime: '2026-06-10 11:30:00',
    source: '财联社',
    category: '宏观经济',
    title: '【宏观】5月CPI同比上涨0.3%，通缩压力仍存',
    summary: '国家统计局数据显示，5月CPI同比上涨0.3%，低于预期，通缩压力仍然存在。',
    content: '国家统计局今日公布5月物价数据，5月CPI同比上涨0.3%，低于市场预期的0.5%，环比下降0.2%。PPI同比下降3.5%。数据显示当前需求仍然偏弱，通缩压力依然存在。',
    relatedSectors: ['大盘'],
    relatedStocks: [],
    importance: '一般利空',
    importanceScore: 42,
    backtestStats: CATEGORY_BACKTEST_STATS['宏观经济'],
    suggestion: null,
    riskWarning: {
      level: '中风险',
      riskType: '系统性风险',
      description: 'CPI低于预期，通缩压力存在，市场情绪偏弱',
      impactScope: '大盘',
      suggestedAction: '建议降低仓位至1成以下，规避系统性风险',
      warningTime: '11:30:00'
    },
    isRead: false,
    userTag: null
  },
  // 一般利好 - 业绩预告
  {
    id: 'news-011',
    publishTime: '2026-06-10 20:00:00',
    source: '巨潮资讯',
    category: '业绩预告',
    title: '【业绩预增】圣泉集团上半年净利润预增80%-100%，合成生物业务放量',
    summary: '圣泉集团发布半年度业绩预告，预计上半年实现净利润3.5-3.9亿元，同比增长80%-100%。',
    content: '圣泉集团(605589)发布2026年半年度业绩预告，预计实现归属于上市公司股东的净利润3.5-3.9亿元，同比增长80%-100%。公司表示，受益于合成生物业务放量及酚醛树脂需求增长，上半年业绩大幅增长。',
    relatedSectors: ['合成生物', '酚醛树脂', '新材料'],
    relatedStocks: [
      { code: '605589', name: '圣泉集团' },
      { code: '003026', name: '中晶科技' }
    ],
    importance: '一般利好',
    importanceScore: 68,
    backtestStats: CATEGORY_BACKTEST_STATS['业绩预告'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 5,
      buyRange: { low: 28.5, high: 30.0 },
      stopLoss: 26.0,
      takeProfit: 35.0,
      holdingPeriod: '超短(1-2日)',
      reason: '业绩预告类消息历史回测胜率68%，但退潮期建议轻仓试水',
      confidence: 55
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 公司公告
  {
    id: 'news-012',
    publishTime: '2026-06-10 19:00:00',
    source: '巨潮资讯',
    category: '公司公告',
    title: '【公司公告】和远气体签订重大合同，金额约2.5亿元',
    summary: '和远气体公告，近日与某客户签订特种气体供应合同，预计合同金额约2.5亿元。',
    content: '和远气体(002971)今日公告，公司近日与某半导体客户签订特种气体供应合同，预计合同总金额约2.5亿元，合同履行期限3年。该合同占公司2025年度营业收入的15%。',
    relatedSectors: ['工业气体', '特种气体', '半导体材料'],
    relatedStocks: [
      { code: '002971', name: '和远气体' }
    ],
    importance: '中性',
    importanceScore: 52,
    backtestStats: CATEGORY_BACKTEST_STATS['公司公告'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '短线(3-5日)',
      reason: '公司公告类消息历史回测胜率48%，合同利好但退潮期市场反应可能有限',
      confidence: 45
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
];

// ═══════════════════════════════════════════════════════════════
// 板块影响分析
// ═══════════════════════════════════════════════════════════════

export interface SectorImpact {
  sector: string;
  // 影响方向
  direction: '利好' | '利空' | '中性';
  // 影响强度(0-100)
  intensity: number;
  // 关联资讯数量
  newsCount: number;
  // 主要资讯标题
  topNews: string[];
  // 建议操作
  suggestion: string;
}

// 分析板块影响
export function analyzeSectorImpact(newsList: NewsItem[]): SectorImpact[] {
  const sectorMap = new Map<string, {
    direction: '利好' | '利空' | '中性';
    intensity: number;
    newsCount: number;
    topNews: string[];
  }>();
  
  newsList.forEach(news => {
    news.relatedSectors.forEach(sector => {
      const existing = sectorMap.get(sector);
      const score = news.importanceScore;
      const isPositive = news.importance === '重大利好' || news.importance === '一般利好';
      const isNegative = news.importance === '重大利空' || news.importance === '一般利空';
      
      if (!existing) {
        sectorMap.set(sector, {
          direction: isPositive ? '利好' : isNegative ? '利空' : '中性',
          intensity: score,
          newsCount: 1,
          topNews: [news.title]
        });
      } else {
        existing.newsCount++;
        existing.intensity = Math.max(existing.intensity, score);
        if (existing.topNews.length < 3) {
          existing.topNews.push(news.title);
        }
        // 更新方向
        if (isPositive && existing.direction === '利空') {
          existing.direction = existing.intensity > score ? '利空' : '利好';
        } else if (isNegative && existing.direction === '利好') {
          existing.direction = existing.intensity > score ? '利好' : '利空';
        }
      }
    });
  });
  
  return Array.from(sectorMap.entries()).map(([sector, data]) => ({
    sector,
    direction: data.direction,
    intensity: data.intensity,
    newsCount: data.newsCount,
    topNews: data.topNews,
    suggestion: data.direction === '利好' 
      ? `板块受${data.newsCount}条利好资讯支撑，建议关注龙头标的`
      : data.direction === '利空'
      ? `板块受${data.newsCount}条利空资讯压制，建议规避`
      : '板块消息面中性，建议观望'
  })).sort((a, b) => b.intensity - a.intensity);
}

// ═══════════════════════════════════════════════════════════════
// 资讯采集状态
// ═══════════════════════════════════════════════════════════════

export interface NewsSourceStatus {
  source: NewsSource;
  // 连接状态
  status: 'connected' | 'disconnected' | 'error';
  // 最后更新时间
  lastUpdate: string;
  // 今日采集数量
  todayCount: number;
  // 延迟(ms)
  latency: number;
}

export const NEWS_SOURCE_STATUS: NewsSourceStatus[] = [
  { source: '巨潮资讯', status: 'connected', lastUpdate: '22:35:00', todayCount: 156, latency: 120 },
  { source: '上交所官网', status: 'connected', lastUpdate: '21:15:00', todayCount: 42, latency: 85 },
  { source: '深交所官网', status: 'connected', lastUpdate: '20:45:00', todayCount: 38, latency: 92 },
  { source: '财联社', status: 'connected', lastUpdate: '22:30:00', todayCount: 285, latency: 45 },
  { source: '同花顺', status: 'connected', lastUpdate: '22:28:00', todayCount: 320, latency: 38 },
  { source: '东方财富', status: 'connected', lastUpdate: '22:25:00', todayCount: 298, latency: 42 },
  { source: '淘股吧', status: 'connected', lastUpdate: '22:20:00', todayCount: 520, latency: 150 },
  { source: '韭研公社', status: 'connected', lastUpdate: '22:15:00', todayCount: 186, latency: 180 },
  { source: '雪球网', status: 'connected', lastUpdate: '22:10:00', todayCount: 450, latency: 95 },
  { source: '开盘啦', status: 'connected', lastUpdate: '22:05:00', todayCount: 125, latency: 200 },
];