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
  // 重大利好 - 重组并购
  {
    id: 'news-001',
    publishTime: '2026-05-20 22:35:00',
    source: '巨潮资讯',
    category: '重组并购',
    title: '【重大资产重组】中芯国际拟收购华虹半导体部分产线，整合国内晶圆代工产能',
    summary: '中芯国际公告称拟以现金+股份方式收购华虹半导体上海及无锡产线，交易对价约280亿元。此次收购将大幅提升公司12英寸晶圆产能，巩固国内晶圆代工龙头地位。',
    content: '中芯国际(688981)晚间公告，公司拟通过发行股份及支付现金方式，收购华虹半导体旗下上海华虹宏力及无锡华虹半导体全部资产。交易完成后，公司将新增月产能约8万片12英寸晶圆，成为全球第三大纯晶圆代工厂。',
    relatedSectors: ['半导体', '芯片概念', '国产替代'],
    relatedStocks: [
      { code: '688981', name: '中芯国际' },
      { code: '603893', name: '瑞芯微' },
      { code: '002049', name: '紫光国微' }
    ],
    importance: '重大利好',
    importanceScore: 92,
    backtestStats: CATEGORY_BACKTEST_STATS['重组并购'],
    suggestion: {
      type: '积极介入',
      suggestedPosition: 30,
      buyRange: { low: 88.5, high: 92.0 },
      stopLoss: 82.0,
      takeProfit: 105.0,
      holdingPeriod: '短线(3-5日)',
      reason: '重组并购类消息历史回测胜率78%，平均最大涨幅15.8%，半导体国产替代逻辑强化',
      confidence: 85
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 重大利好 - 监管政策
  {
    id: 'news-002',
    publishTime: '2026-05-20 21:15:00',
    source: '上交所官网',
    category: '监管政策',
    title: '【政策利好】证监会发布《关于深化科创板改革 服务科技创新的若干意见》',
    summary: '证监会发布科创板改革新政，包括优化上市条件、放宽涨跌幅限制、引入做市商制度等12项措施，旨在提升科创板服务科技创新能力。',
    content: '为深入贯彻创新驱动发展战略，证监会今日发布《关于深化科创板改革 服务科技创新的若干意见》，提出优化科创板上市条件、研究适当放宽涨跌幅限制、引入做市商制度、完善退市机制等12项改革措施。',
    relatedSectors: ['科创板', '半导体', '生物医药', '新能源'],
    relatedStocks: [
      { code: '688981', name: '中芯国际' },
      { code: '688008', name: '澜起科技' },
      { code: '688111', name: '金山办公' }
    ],
    importance: '重大利好',
    importanceScore: 88,
    backtestStats: CATEGORY_BACKTEST_STATS['监管政策'],
    suggestion: {
      type: '积极介入',
      suggestedPosition: 25,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '中线(1-2周)',
      reason: '监管政策类消息历史回测胜率72%，科创板改革利好科技股估值提升',
      confidence: 80
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利好 - 业绩预告
  {
    id: 'news-003',
    publishTime: '2026-05-20 20:45:00',
    source: '巨潮资讯',
    category: '业绩预告',
    title: '【业绩超预期】利仁科技上半年净利润预增180%-200%，消费电子需求旺盛',
    summary: '利仁科技发布半年度业绩预告，预计上半年实现净利润2.8-3.0亿元，同比增长180%-200%，主要受益于消费电子市场需求持续旺盛。',
    content: '利仁科技(001259)发布2026年半年度业绩预告，预计实现归属于上市公司股东的净利润2.8-3.0亿元，同比增长180%-200%。公司表示，受益于智能家居产品需求增长及新品放量，上半年订单量同比大幅增长。',
    relatedSectors: ['消费电子', '智能家居', '小家电'],
    relatedStocks: [
      { code: '001259', name: '利仁科技' },
      { code: '002032', name: '苏泊尔' },
      { code: '002242', name: '九阳股份' }
    ],
    importance: '一般利好',
    importanceScore: 72,
    backtestStats: CATEGORY_BACKTEST_STATS['业绩预告'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 15,
      buyRange: { low: 58.5, high: 61.0 },
      stopLoss: 55.0,
      takeProfit: 68.0,
      holdingPeriod: '超短(1-2日)',
      reason: '业绩预告类消息历史回测胜率68%，但股价已处高位，注意追高风险',
      confidence: 65
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利好 - 题材催化
  {
    id: 'news-004',
    publishTime: '2026-05-20 19:30:00',
    source: '财联社',
    category: '题材催化',
    title: '【AI应用催化】华为发布盘古大模型5.0，AI应用产业链有望受益',
    summary: '华为在开发者大会上正式发布盘古大模型5.0，性能较上一代提升10倍，支持多模态交互。AI应用产业链相关公司有望受益。',
    content: '华为今日在HDC 2026开发者大会上正式发布盘古大模型5.0，该模型在语言理解、图像识别、代码生成等方面性能较4.0版本提升10倍。同时宣布将向合作伙伴开放API接口，推动AI应用在多行业落地。',
    relatedSectors: ['AI应用', '华为概念', '大模型', '算力'],
    relatedStocks: [
      { code: '002407', name: '多氟多' },
      { code: '300496', name: '中科创达' },
      { code: '002230', name: '科大讯飞' }
    ],
    importance: '一般利好',
    importanceScore: 68,
    backtestStats: CATEGORY_BACKTEST_STATS['题材催化'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 15,
      buyRange: { low: 35.0, high: 37.0 },
      stopLoss: 33.0,
      takeProfit: 42.0,
      holdingPeriod: '短线(3-5日)',
      reason: '题材催化类消息历史回测胜率65%，AI产业链热度持续，但需关注持续性',
      confidence: 62
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 行业动态
  {
    id: 'news-005',
    publishTime: '2026-05-20 18:20:00',
    source: '同花顺',
    category: '行业动态',
    title: '【行业动态】5月新能源汽车销量同比增长25%，渗透率达38%',
    summary: '乘联会数据显示，5月新能源汽车零售销量85万辆，同比增长25%，环比增长8%，市场渗透率达到38%，行业维持高景气度。',
    content: '据乘联会最新数据，5月份国内新能源汽车零售销量达到85万辆，同比增长25%，环比增长8%。其中纯电动车销量58万辆，插电混动车型27万辆。新能源汽车市场渗透率进一步提升至38%。',
    relatedSectors: ['新能源汽车', '锂电池', '充电桩'],
    relatedStocks: [
      { code: '002196', name: '方正电机' },
      { code: '300750', name: '宁德时代' },
      { code: '002594', name: '比亚迪' }
    ],
    importance: '中性',
    importanceScore: 52,
    backtestStats: CATEGORY_BACKTEST_STATS['行业动态'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '短线(3-5日)',
      reason: '行业动态消息历史回测胜率55%，数据符合预期，暂无超预期表现',
      confidence: 50
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利空 - 股东减持
  {
    id: 'news-006',
    publishTime: '2026-05-20 17:45:00',
    source: '巨潮资讯',
    category: '股东增减持',
    title: '【减持公告】巨轮智能股东拟减持不超过3%股份',
    summary: '巨轮智能公告，持股5%以上股东XX计划在未来3个月内通过集中竞价方式减持不超过公司总股本3%的股份。',
    content: '巨轮智能(002031)今日公告，公司股东广州XX投资有限公司因自身资金需求，计划自本公告披露之日起3个交易日后的3个月内，通过集中竞价交易方式减持公司股份不超过2100万股，即不超过公司总股本的3%。',
    relatedSectors: ['机器人', '智能制造'],
    relatedStocks: [
      { code: '002031', name: '巨轮智能' }
    ],
    importance: '一般利空',
    importanceScore: 38,
    backtestStats: CATEGORY_BACKTEST_STATS['股东增减持'],
    suggestion: null,
    riskWarning: {
      level: '中风险',
      riskType: '减持风险',
      description: '大股东拟减持不超过3%股份，可能对股价形成压制',
      impactScope: '个股',
      suggestedAction: '建议关注减持进展，若股价跌破7.5元支撑位建议减仓',
      warningTime: '17:45:00'
    },
    isRead: false,
    userTag: null
  },
  // 重大利空 - 风险提示
  {
    id: 'news-007',
    publishTime: '2026-05-20 16:30:00',
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
  // 一般利好 - 资金流向
  {
    id: 'news-008',
    publishTime: '2026-05-20 15:30:00',
    source: '东方财富',
    category: '资金流向',
    title: '【资金动向】北向资金今日净买入85亿元，重点加仓半导体和消费电子',
    summary: '北向资金今日净买入85.2亿元，连续3日净流入。重点加仓方向为半导体、消费电子、新能源板块。',
    content: '今日北向资金呈现大幅净流入态势，全天净买入85.2亿元，其中沪股通净买入52.3亿元，深股通净买入32.9亿元。从十大活跃个股来看，北向资金重点买入了中芯国际、立讯精密、宁德时代等个股。',
    relatedSectors: ['半导体', '消费电子', '新能源'],
    relatedStocks: [
      { code: '688981', name: '中芯国际' },
      { code: '002475', name: '立讯精密' },
      { code: '300750', name: '宁德时代' }
    ],
    importance: '一般利好',
    importanceScore: 65,
    backtestStats: CATEGORY_BACKTEST_STATS['资金流向'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 15,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '北向资金连续净流入，市场情绪偏暖，但需关注持续性',
      confidence: 58
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 龙虎榜数据
  {
    id: 'news-009',
    publishTime: '2026-05-20 15:00:00',
    source: '同花顺',
    category: '龙虎榜数据',
    title: '【龙虎榜】利仁科技获3家机构买入，游资小鳄鱼现身买方',
    summary: '利仁科技今日登上龙虎榜，买方席位出现3家机构专用席位，知名游资小鳄鱼也现身买方前五。',
    content: '利仁科技(001259)今日因连续3个交易日涨幅偏离值累计达20%登上龙虎榜。买方席位中，3家机构专用席位合计买入约1.8亿元，知名游资小鳄鱼所在营业部买入约3500万元。卖方席位以散户为主。',
    relatedSectors: ['消费电子', '智能家居'],
    relatedStocks: [
      { code: '001259', name: '利仁科技' }
    ],
    importance: '中性',
    importanceScore: 55,
    backtestStats: CATEGORY_BACKTEST_STATS['龙虎榜数据'],
    suggestion: {
      type: '观望等待',
      suggestedPosition: 0,
      buyRange: { low: 0, high: 0 },
      stopLoss: 0,
      takeProfit: 0,
      holdingPeriod: '超短(1-2日)',
      reason: '龙虎榜显示机构和游资共同买入，但股价已处高位，追高风险较大',
      confidence: 52
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 一般利好 - 游资动向
  {
    id: 'news-010',
    publishTime: '2026-05-20 14:30:00',
    source: '淘股吧',
    category: '游资动向',
    title: '【游资追踪】炒股养家今日介入光华股份，N字形反包战法',
    summary: '据龙虎榜数据，知名游资炒股养家今日买入光华股份约2800万元，该股今日走出N字形反包形态。',
    content: '光华股份(001333)今日涨停，龙虎榜显示炒股养家所在营业部买入2800万元。该股此前经历3日回调，今日倍量涨停反包，走出典型N字形形态。从历史数据看，炒股养家介入的标的次日溢价率约65%。',
    relatedSectors: ['化工新材料'],
    relatedStocks: [
      { code: '001333', name: '光华股份' }
    ],
    importance: '一般利好',
    importanceScore: 62,
    backtestStats: CATEGORY_BACKTEST_STATS['游资动向'],
    suggestion: {
      type: '谨慎介入',
      suggestedPosition: 10,
      buyRange: { low: 25.5, high: 26.5 },
      stopLoss: 24.0,
      takeProfit: 29.0,
      holdingPeriod: '超短(1-2日)',
      reason: '游资动向类消息历史回测胜率60%，炒股养家介入标的次日溢价率约65%',
      confidence: 58
    },
    riskWarning: null,
    isRead: false,
    userTag: null
  },
  // 中性 - 研报评级
  {
    id: 'news-011',
    publishTime: '2026-05-20 13:00:00',
    source: '雪球网',
    category: '研报评级',
    title: '【研报】中信证券：维持宁德时代"买入"评级，目标价280元',
    summary: '中信证券发布研报，维持宁德时代"买入"评级，认为公司全球市占率持续提升，目标价280元。',
    content: '中信证券发布宁德时代深度研究报告，认为公司作为全球动力电池龙头，受益于新能源汽车渗透率持续提升，预计2026年净利润同比增长35%。维持"买入"评级，给予2026年40倍PE，目标价280元。',
    relatedSectors: ['锂电池', '新能源汽车'],
    relatedStocks: [
      { code: '300750', name: '宁德时代' }
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
    id: 'news-012',
    publishTime: '2026-05-20 11:30:00',
    source: '财联社',
    category: '宏观经济',
    title: '【宏观】美联储会议纪要显示可能再次加息，全球市场承压',
    summary: '美联储最新会议纪要显示，多数官员认为通胀仍具粘性，可能需要再次加息。消息公布后，全球股市普跌。',
    content: '美联储公布5月货币政策会议纪要，显示多数官员认为当前通胀水平仍高于目标，可能需要进一步加息。纪要公布后，美股期货下跌，亚太市场午后跳水，A股三大指数跌幅扩大。',
    relatedSectors: ['大盘'],
    relatedStocks: [],
    importance: '一般利空',
    importanceScore: 42,
    backtestStats: CATEGORY_BACKTEST_STATS['宏观经济'],
    suggestion: null,
    riskWarning: {
      level: '中风险',
      riskType: '系统性风险',
      description: '美联储可能再次加息，全球风险资产承压',
      impactScope: '大盘',
      suggestedAction: '建议降低总仓位至3成以下，规避系统性风险',
      warningTime: '11:30:00'
    },
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