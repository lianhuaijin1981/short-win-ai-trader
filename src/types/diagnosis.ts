// ═══════════════════════════════════════════════════════════════
//  全域多维度战法诊股 - 12维度诊断类型定义
// ═══════════════════════════════════════════════════════════════

import type { TradeRecord } from '@/data/tradeData';

// ── 诊断维度枚举 ───────────────────────────────────────────────

export type DiagnosisDimension =
  | 'capital'        // 1. 资金博弈
  | 'chip'           // 2. 筹码结构
  | 'technical'      // 3. 技术形态
  | 'theme'          // 4. 题材风口
  | 'sentiment'      // 5. 市场情绪
  | 'psychology'     // 6. 交易心态
  | 'discipline'     // 7. 操作纪律
  | 'position'       // 8. 仓位管控
  | 'cycle'          // 9. 周期择时
  | 'pricePoint'     // 10. 买卖点位
  | 'news'           // 11. 消息认知
  | 'cost'           // 12. 交易成本
  | 'fundamental'    // 13. 基本面价值
  | 'habit';         // 14. 交易习惯

// ── 问题等级 ───────────────────────────────────────────────────

export type IssueSeverity = 'critical' | 'moderate' | 'minor';

// ── 问题根源类别 ───────────────────────────────────────────────

export type IssueRootCause = 
  | 'objective_market'    // 客观行情限制
  | 'psychology_bias'     // 个人心态偏差
  | 'discipline_failure'  // 执行纪律问题
  | 'cognitive_gap'       // 认知判断不足
  | 'planning_missing';   // 规划缺失

// ── 诊断疑点 ───────────────────────────────────────────────────

export interface DiagnosisIssue {
  id: string;
  dimension: DiagnosisDimension;
  dimensionLabel: string;
  severity: IssueSeverity;
  rootCause: IssueRootCause;
  title: string;           // 问题标题
  description: string;     // 详细描述
  commonError: string;     // 散户高频错误
  evidence: string;        // 证据/依据
  suggestion: string;      // 改进建议
  standardOperation: string; // 标准操作方式
  timestamp?: string;      // 关联时间点
  price?: number;          // 关联价格点
}

// ── 维度诊断结果 ───────────────────────────────────────────────

export interface DimensionDiagnosis {
  dimension: DiagnosisDimension;
  dimensionLabel: string;
  score: number;           // 该维度得分 0-100
  issues: DiagnosisIssue[];
  highlights: string[];    // 该维度亮点
  summary: string;         // 维度总结
}

// ── 完整诊断报告 ───────────────────────────────────────────────

export interface FullDiagnosisReport {
  tradeId: string;
  tradeInfo: TradeRecord;
  generatedAt: string;
  
  // 各维度诊断结果
  dimensions: DimensionDiagnosis[];
  
  // 综合评分
  overallScore: number;
  scoreGrade: 'excellent' | 'compliant' | 'flawed' | 'failed';
  
  // 问题汇总
  allIssues: DiagnosisIssue[];
  criticalCount: number;
  moderateCount: number;
  minorCount: number;
  
  // 亮点汇总
  allHighlights: string[];
  
  // 综合总结
  summary: string;
  
  // 定制化优化方案
  optimizationPlan: {
    immediate: string[];    // 立即修正
    shortTerm: string[];    // 短期改进
    longTerm: string[];     // 长期养成
  };
  
  // 陋习规避提示
  badHabits: {
    habit: string;
    frequency: number;
    impact: string;
    correction: string;
  }[];
}

// ── 诊断上下文数据 ─────────────────────────────────────────────

export interface DiagnosisContext {
  trade: TradeRecord;
  // 市场环境数据
  marketData?: {
    indexChange?: number;
    marketBreadth?: { up: number; down: number; limitUp: number; limitDown: number };
    northFlow?: number;
    totalVolume?: number;
    marketPhase?: string;
  };
  // 板块数据
  sectorData?: {
    sectorChange?: number;
    themeRank?: number;
    isMainTheme?: boolean;
    leaderChange?: number;
  };
  // 个股数据
  stockData?: {
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    turnover?: number;
    volumeRatio?: number;
    amplitude?: number;
    ma5?: number;
    ma10?: number;
    ma20?: number;
    macd?: { dif: number; dea: number; macd: number };
    kdj?: { k: number; d: number; j: number };
    rsi?: number;
    chipProfit?: number;
    chipConcentration?: number;
    fundFlow?: { superLarge: number; large: number; medium: number; small: number };
  };
  // 消息面
  newsData?: {
    hasPositiveNews?: boolean;
    hasNegativeNews?: boolean;
    newsImpact?: 'positive' | 'negative' | 'neutral';
  };
  // 基本面
  fundamentalData?: {
    pe?: number;
    pb?: number;
    roe?: number;
    profitGrowth?: number;
    revenueGrowth?: number;
    isST?: boolean;
  };
  // 用户历史数据
  userHistory?: {
    totalTrades?: number;
    winRate?: number;
    avgHoldingDays?: number;
    frequentErrors?: string[];
    tradingStyle?: string;
  };
}

// ── 诊断规则 ───────────────────────────────────────────────────

export interface DiagnosisRule {
  id: string;
  dimension: DiagnosisDimension;
  name: string;
  description: string;
  check: (context: DiagnosisContext) => DiagnosisIssue | null;
}

// ── 维度配置 ───────────────────────────────────────────────────

export const DIMENSION_CONFIG: Record<DiagnosisDimension, {
  label: string;
  icon: string;
  color: string;
  weight: number;  // 权重
}> = {
  capital: { label: '资金博弈', icon: '💰', color: '#3b82f6', weight: 8 },
  chip: { label: '筹码结构', icon: '📊', color: '#8b5cf6', weight: 7 },
  technical: { label: '技术形态', icon: '📈', color: '#06b6d4', weight: 8 },
  theme: { label: '题材风口', icon: '🔥', color: '#f59e0b', weight: 7 },
  sentiment: { label: '市场情绪', icon: '😤', color: '#ec4899', weight: 6 },
  psychology: { label: '交易心态', icon: '🧠', color: '#f97316', weight: 9 },
  discipline: { label: '操作纪律', icon: '📋', color: '#a855f7', weight: 9 },
  position: { label: '仓位管控', icon: '⚖️', color: '#22c55e', weight: 8 },
  cycle: { label: '周期择时', icon: '🔄', color: '#14b8a6', weight: 7 },
  pricePoint: { label: '买卖点位', icon: '🎯', color: '#ef4444', weight: 8 },
  news: { label: '消息认知', icon: '📰', color: '#6366f1', weight: 6 },
  cost: { label: '交易成本', icon: '💸', color: '#84cc16', weight: 5 },
  fundamental: { label: '基本面价值', icon: '🏢', color: '#0ea5e9', weight: 7 },
  habit: { label: '交易习惯', icon: '🔁', color: '#d946ef', weight: 8 },
};

// ── 评分等级 ───────────────────────────────────────────────────

export const SCORE_GRADE_CONFIG = {
  excellent: { min: 85, label: '优秀操作', color: '#22c55e' },
  compliant: { min: 70, label: '合规操作', color: '#3b82f6' },
  flawed: { min: 50, label: '瑕疵操作', color: '#f59e0b' },
  failed: { min: 0, label: '失误操作', color: '#ef4444' },
};

// ── 散户高频错误库 ─────────────────────────────────────────────

export const COMMON_ERRORS: Record<DiagnosisDimension, string[]> = {
  capital: [
    '仅凭单笔大单盲目跟风入场',
    '无视持续资金出逃执意持仓',
    '放量缩量信号误判',
    '忽略外部资金压制逆势交易',
  ],
  chip: [
    '高位密集筹码区追涨',
    '低位筹码未企稳恐慌割肉',
    '忽视压力筹码区盲目加仓',
  ],
  technical: [
    '假突破误判进场',
    '破位后抱有幻想不止损',
    '超买超卖区间逆势操作',
    '单一指标片面决策',
  ],
  theme: [
    '题材末期退潮跟风接盘',
    '冷门小题材重仓博弈',
    '板块分化选错个股',
    '脱离主线盲目交易',
  ],
  sentiment: [
    '市场狂热高位追涨',
    '极致恐慌低位割肉',
    '分歧阶段贸然重仓博弈',
  ],
  psychology: [
    '盈利不舍止盈贪心回吐',
    '亏损恐惧盲目止损套牢筹码',
    '心存侥幸无视风险扛单',
    '踏空后急躁乱选股入场',
    '小幅波动心态慌乱频繁改决策',
  ],
  discipline: [
    '提前制定的止盈止损线形同虚设',
    '盘中临时随意加仓减仓',
    '擅自更改进场离场条件',
    '无计划临时突发交易',
    '既定规则反复打破',
  ],
  position: [
    '单次满仓重仓赌行情',
    '弱势行情依旧高仓位持仓',
    '盈利小幅加仓亏损大幅补仓',
    '持仓过于集中单一标的',
    '逆势行情盲目摊薄成本',
  ],
  cycle: [
    '短线交易被套后被动变长线',
    '长线持仓频繁做短线波段',
    '大小周期趋势背离依旧进场',
    '错把反弹反转',
    '错把回调见顶',
  ],
  pricePoint: [
    '最高点追涨买入',
    '最低点杀跌卖出',
    '回调中途过早抄底',
    '上涨中途提前止盈踏空利润',
  ],
  news: [
    '轻信网传小道消息盲目买卖',
    '利好兑现后追高',
    '利空落地恐慌抛售',
    '过度解读短期细碎消息放大行情预期',
  ],
  cost: [
    '频繁小额交易累积高额手续费',
    '小差价频繁买卖得不偿失',
    '忽略成本导致实际收益缩水',
  ],
  fundamental: [
    '纯凭盘面涨跌无视基本面暴雷风险',
    '高估题材个股实际价值',
    '低位忽视优质基本面盲目割肉',
  ],
  habit: [
    '习惯性追涨杀跌',
    '偏爱冷门弱势股',
    '频繁切换标的交易',
    '单一模式不变通应对多变行情',
  ],
};