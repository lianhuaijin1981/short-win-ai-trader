// ═══════════════════════════════════════════════════════════════
//  全域多维度战法诊股 - 诊断引擎
// ═══════════════════════════════════════════════════════════════

import type {
  DiagnosisContext,
  DiagnosisIssue,
  DiagnosisDimension,
  DimensionDiagnosis,
  FullDiagnosisReport,
  IssueSeverity,
  IssueRootCause,
} from '@/types/diagnosis';
import {
  DIMENSION_CONFIG,
  COMMON_ERRORS,
  SCORE_GRADE_CONFIG,
} from '@/types/diagnosis';
import type { TradeRecord } from '@/data/tradeData';

// ── 工具函数 ───────────────────────────────────────────────────

const generateId = () => Math.random().toString(36).substring(2, 11);

const getRandomItem = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(max, val));

// ── 诊断规则定义 ───────────────────────────────────────────────

interface RuleDef {
  id: string;
  dimension: DiagnosisDimension;
  name: string;
  check: (ctx: DiagnosisContext) => DiagnosisIssue | null;
}

const RULES: RuleDef[] = [
  // ===== 1. 资金博弈 =====
  {
    id: 'capital_1',
    dimension: 'capital',
    name: '超大单资金背离检测',
    check: (ctx) => {
      const flow = ctx.stockData?.fundFlow;
      if (!flow) return null;
      if (flow.superLarge < -500 && ctx.trade.tradeType === 'buy') {
        return createIssue('capital', 'critical', '资金背离进场',
          '超大单持续净流出状态下逆势买入',
          '超大单净流出' + Math.abs(flow.superLarge).toFixed(0) + '万',
          '等待资金回流信号确认后再进场');
      }
      return null;
    },
  },
  {
    id: 'capital_2',
    dimension: 'capital',
    name: '量价匹配检测',
    check: (ctx) => {
      const vr = ctx.stockData?.volumeRatio;
      if (!vr) return null;
      if (vr > 3 && ctx.trade.tradeType === 'buy') {
        return createIssue('capital', 'moderate', '量价失衡追入',
          '量比过高时追涨容易被套',
          '量比' + vr.toFixed(2) + '，远超正常范围',
          '量比>2时谨慎追高，等待缩量回踩');
      }
      return null;
    },
  },
  {
    id: 'capital_3',
    dimension: 'capital',
    name: '资金出逃检测',
    check: (ctx) => {
      const flow = ctx.stockData?.fundFlow;
      if (!flow) return null;
      const totalNet = flow.superLarge + flow.large + flow.medium + flow.small;
      if (totalNet < -1000 && ctx.trade.tradeType === 'buy') {
        return createIssue('capital', 'critical', '全维度资金出逃',
          '各类资金全面净流出仍执意买入',
          '全维度净流出' + Math.abs(totalNet).toFixed(0) + '万',
          '资金全面出逃时应观望，等待资金回流');
      }
      return null;
    },
  },

  // ===== 2. 筹码结构 =====
  {
    id: 'chip_1',
    dimension: 'chip',
    name: '高位筹码密集区追涨',
    check: (ctx) => {
      const profit = ctx.stockData?.chipProfit;
      if (profit !== undefined && profit > 80 && ctx.trade.tradeType === 'buy') {
        return createIssue('chip', 'critical', '高位筹码区追涨',
          '获利盘占比过高，筹码高位密集，追涨风险极大',
          '获利盘占比' + profit.toFixed(1) + '%',
          '获利盘>70%时不宜追涨，等待筹码换手');
      }
      return null;
    },
  },
  {
    id: 'chip_2',
    dimension: 'chip',
    name: '低位筹码恐慌割肉',
    check: (ctx) => {
      const profit = ctx.stockData?.chipProfit;
      if (profit !== undefined && profit < 15 && ctx.trade.tradeType === 'sell') {
        return createIssue('chip', 'moderate', '低位恐慌割肉',
          '获利盘极低时恐慌卖出，可能卖在底部区域',
          '获利盘仅' + profit.toFixed(1) + '%，处于低位',
          '低位筹码松动时不宜恐慌卖出，等待反弹');
      }
      return null;
    },
  },
  {
    id: 'chip_3',
    dimension: 'chip',
    name: '筹码集中度检测',
    check: (ctx) => {
      const conc = ctx.stockData?.chipConcentration;
      if (conc !== undefined && conc < 20) {
        return createIssue('chip', 'moderate', '筹码过度分散',
          '筹码集中度低，持仓分散，缺乏主力控盘',
          '筹码集中度仅' + conc.toFixed(1) + '%',
          '筹码集中度<30%时谨慎参与');
      }
      return null;
    },
  },

  // ===== 3. 技术形态 =====
  {
    id: 'tech_1',
    dimension: 'technical',
    name: '均线空头排列买入',
    check: (ctx) => {
      const { ma5, ma10, ma20 } = ctx.stockData || {};
      if (ma5 && ma10 && ma20 && ma5 < ma10 && ma10 < ma20 && ctx.trade.tradeType === 'buy') {
        return createIssue('technical', 'critical', '空头排列买入',
          '均线呈空头排列趋势，此时买入属于逆势操作',
          'MA5<MA10<MA20，空头排列',
          '均线空头排列时应观望，等待均线走平或金叉');
      }
      return null;
    },
  },
  {
    id: 'tech_2',
    dimension: 'technical',
    name: 'MACD死叉检测',
    check: (ctx) => {
      const macd = ctx.stockData?.macd;
      if (macd && macd.dif < macd.dea && ctx.trade.tradeType === 'buy') {
        return createIssue('technical', 'moderate', 'MACD死叉买入',
          'MACD指标死叉状态下买入，技术信号偏空',
          'DIF(' + macd.dif.toFixed(2) + ')<DEA(' + macd.dea.toFixed(2) + ')',
          'MACD死叉时应等待金叉确认后再考虑进场');
      }
      return null;
    },
  },
  {
    id: 'tech_3',
    dimension: 'technical',
    name: 'KDJ超买追涨',
    check: (ctx) => {
      const kdj = ctx.stockData?.kdj;
      if (kdj && kdj.j > 90 && ctx.trade.tradeType === 'buy') {
        return createIssue('technical', 'moderate', 'KDJ超买区追涨',
          'KDJ指标J值进入超买区仍追涨',
          'J值' + kdj.j.toFixed(1) + '，严重超买',
          'J值>90时不宜追涨，等待回调');
      }
      return null;
    },
  },
  {
    id: 'tech_4',
    dimension: 'technical',
    name: '破位不止损',
    check: (ctx) => {
      const ma20 = ctx.stockData?.ma20;
      if (ma20 && ctx.trade.tradePrice < ma20 * 0.95 && ctx.trade.tradeType === 'sell' && ctx.trade.profitLoss < -500) {
        return createIssue('technical', 'critical', '破位不止损',
          '股价已跌破重要均线支撑仍未止损',
          '成交价低于MA20约' + ((ma20 - ctx.trade.tradePrice) / ma20 * 100).toFixed(1) + '%',
          '跌破关键支撑位应果断止损，不可抱有幻想');
      }
      return null;
    },
  },

  // ===== 4. 题材风口 =====
  {
    id: 'theme_1',
    dimension: 'theme',
    name: '非主线题材交易',
    check: (ctx) => {
      if (ctx.sectorData && !ctx.sectorData.isMainTheme && ctx.trade.tradeType === 'buy') {
        return createIssue('theme', 'moderate', '非主线题材介入',
          '交易的标的所属题材非当前市场主线',
          '题材排名#' + (ctx.sectorData.themeRank || 'N/A') + '，非主线',
          '优先参与市场主线题材，非主线题材谨慎参与');
      }
      return null;
    },
  },
  {
    id: 'theme_2',
    dimension: 'theme',
    name: '板块退潮期交易',
    check: (ctx) => {
      const change = ctx.sectorData?.sectorChange;
      if (change !== undefined && change < -3 && ctx.trade.tradeType === 'buy') {
        return createIssue('theme', 'critical', '板块退潮期买入',
          '所属板块大幅下跌，处于退潮阶段',
          '板块跌幅' + Math.abs(change).toFixed(2) + '%',
          '板块退潮时应观望，不宜逆势介入');
      }
      return null;
    },
  },

  // ===== 5. 市场情绪 =====
  {
    id: 'sentiment_1',
    dimension: 'sentiment',
    name: '极端恐慌情绪割肉',
    check: (ctx) => {
      const breadth = ctx.marketData?.marketBreadth;
      if (breadth && breadth.down > breadth.up * 3 && ctx.trade.tradeType === 'sell') {
        return createIssue('sentiment', 'moderate', '极致恐慌情绪割肉',
          '市场处于极致恐慌状态，此时卖出容易卖在低点',
          '下跌' + breadth.down + '家，上涨仅' + breadth.up + '家',
          '极致恐慌时不宜恐慌割肉，等待情绪修复反弹');
      }
      return null;
    },
  },
  {
    id: 'sentiment_2',
    dimension: 'sentiment',
    name: '狂热情绪追涨',
    check: (ctx) => {
      const breadth = ctx.marketData?.marketBreadth;
      if (breadth && breadth.limitUp > 100 && ctx.trade.tradeType === 'buy') {
        return createIssue('sentiment', 'moderate', '市场狂热追涨',
          '市场涨停家数过多，情绪过热，追涨风险大',
          '涨停' + breadth.limitUp + '家，情绪狂热',
          '情绪狂热时追涨需谨慎，警惕次日分化');
      }
      return null;
    },
  },

  // ===== 6. 交易心态 =====
  {
    id: 'psychology_1',
    dimension: 'psychology',
    name: '盈利回吐检测',
    check: (ctx) => {
      if (ctx.trade.profitLoss > 0 && ctx.trade.profitLoss < ctx.trade.tradeAmount * 0.01 && ctx.trade.tradeType === 'sell') {
        return createIssue('psychology', 'moderate', '微利即走贪心回吐',
          '小幅盈利即卖出，可能错失后续更大涨幅',
          '盈利仅' + (ctx.trade.profitLoss / ctx.trade.tradeAmount * 100).toFixed(2) + '%',
          '设定合理止盈目标，不宜微利即走');
      }
      return null;
    },
  },
  {
    id: 'psychology_2',
    dimension: 'psychology',
    name: '亏损扛单检测',
    check: (ctx) => {
      if (ctx.trade.profitLoss < -ctx.trade.tradeAmount * 0.05 && ctx.trade.tradeType === 'buy') {
        return createIssue('psychology', 'critical', '深度亏损仍加仓',
          '已有较大亏损仍继续买入，存在侥幸心理',
          '当前亏损' + Math.abs(ctx.trade.profitLoss).toFixed(0) + '元',
          '亏损超5%应止损，不可侥幸扛单');
      }
      return null;
    },
  },

  // ===== 7. 操作纪律 =====
  {
    id: 'discipline_1',
    dimension: 'discipline',
    name: '无交易计划检测',
    check: (ctx) => {
      if (!ctx.trade.tradeLogic && ctx.trade.source === 'manual') {
        return createIssue('discipline', 'moderate', '无计划临时交易',
          '未记录交易逻辑，属于无计划临时操作',
          '交易思路为空',
          '每笔交易前必须制定计划，明确进出场条件');
      }
      return null;
    },
  },
  {
    id: 'discipline_2',
    dimension: 'discipline',
    name: '频繁交易检测',
    check: (ctx) => {
      const history = ctx.userHistory;
      if (history && history.totalTrades && history.totalTrades > 50) {
        return createIssue('discipline', 'moderate', '交易频率过高',
          '历史交易次数过多，存在频繁交易倾向',
          '累计交易' + history.totalTrades + '笔',
          '控制交易频率，每月交易不超过10笔');
      }
      return null;
    },
  },

  // ===== 8. 仓位管控 =====
  {
    id: 'position_1',
    dimension: 'position',
    name: '满仓重仓检测',
    check: (ctx) => {
      if (ctx.trade.positionRatio > 80) {
        return createIssue('position', 'critical', '满仓重仓操作',
          '单笔交易仓位占比过高，风险集中',
          '仓位占比' + ctx.trade.positionRatio.toFixed(1) + '%',
          '单笔交易仓位不宜超过总资金30%');
      }
      return null;
    },
  },
  {
    id: 'position_2',
    dimension: 'position',
    name: '弱势高仓位',
    check: (ctx) => {
      const indexChange = ctx.marketData?.indexChange;
      if (indexChange !== undefined && indexChange < -2 && ctx.trade.positionRatio > 50) {
        return createIssue('position', 'critical', '弱势行情高仓位',
          '大盘明显走弱仍保持高仓位',
          '大盘跌' + Math.abs(indexChange).toFixed(2) + '%，仓位' + ctx.trade.positionRatio.toFixed(1) + '%',
          '大盘跌幅>2%时应降低仓位至30%以下');
      }
      return null;
    },
  },

  // ===== 9. 周期择时 =====
  {
    id: 'cycle_1',
    dimension: 'cycle',
    name: '短线被动变长线',
    check: (ctx) => {
      const history = ctx.userHistory;
      if (history && history.avgHoldingDays && history.avgHoldingDays > 20 && ctx.trade.profitLoss < 0) {
        return createIssue('cycle', 'moderate', '短线被动变长线',
          '短线交易被套后长期持有，被动变成长线',
          '平均持仓' + history.avgHoldingDays.toFixed(0) + '天',
          '短线交易应设定明确持有期限，超期果断止损');
      }
      return null;
    },
  },
  {
    id: 'cycle_2',
    dimension: 'cycle',
    name: '趋势背离交易',
    check: (ctx) => {
      const phase = ctx.marketData?.marketPhase;
      if (phase === '熊市' && ctx.trade.tradeType === 'buy') {
        return createIssue('cycle', 'critical', '熊市周期买入',
          '大周期处于熊市阶段，此时买入胜率低',
          '市场处于' + phase + '周期',
          '熊市周期应以观望为主，不宜逆势买入');
      }
      return null;
    },
  },

  // ===== 10. 买卖点位 =====
  {
    id: 'price_1',
    dimension: 'pricePoint',
    name: '追高买入检测',
    check: (ctx) => {
      const high = ctx.stockData?.high;
      if (high && ctx.trade.tradePrice > high * 0.98 && ctx.trade.tradeType === 'buy') {
        return createIssue('pricePoint', 'moderate', '接近最高点追涨',
          '成交价格接近当日最高价，追高风险大',
          '成交价' + ctx.trade.tradePrice.toFixed(2) + '，最高价' + high.toFixed(2),
          '避免在接近最高点时追涨，等待回调');
      }
      return null;
    },
  },
  {
    id: 'price_2',
    dimension: 'pricePoint',
    name: '杀跌卖出检测',
    check: (ctx) => {
      const low = ctx.stockData?.low;
      if (low && ctx.trade.tradePrice < low * 1.02 && ctx.trade.tradeType === 'sell') {
        return createIssue('pricePoint', 'moderate', '接近最低点杀跌',
          '成交价格接近当日最低价，容易卖在低点',
          '成交价' + ctx.trade.tradePrice.toFixed(2) + '，最低价' + low.toFixed(2),
          '避免在接近最低点时恐慌卖出');
      }
      return null;
    },
  },
  {
    id: 'price_3',
    dimension: 'pricePoint',
    name: '过早抄底检测',
    check: (ctx) => {
      const low = ctx.stockData?.low;
      const open = ctx.stockData?.open;
      if (low && open && ctx.trade.tradeType === 'buy') {
        const dropFromOpen = (open - ctx.trade.tradePrice) / open * 100;
        if (dropFromOpen > 3 && ctx.trade.tradePrice > low * 1.01) {
          return createIssue('pricePoint', 'moderate', '回调中途过早抄底',
          '股价从开盘下跌较多，可能尚未企稳',
          '较开盘跌' + dropFromOpen.toFixed(1) + '%',
          '等待股价企稳信号再考虑抄底');
        }
      }
      return null;
    },
  },

  // ===== 11. 消息认知 =====
  {
    id: 'news_1',
    dimension: 'news',
    name: '利好兑现追高',
    check: (ctx) => {
      if (ctx.newsData?.hasPositiveNews && ctx.newsData.newsImpact === 'positive' && ctx.trade.tradeType === 'buy') {
        return createIssue('news', 'moderate', '利好兑现后追高',
          '利好消息已充分反映，此时追高容易被套',
          '存在利好消息',
          '利好兑现后不宜追高，警惕"买预期卖事实"');
      }
      return null;
    },
  },
  {
    id: 'news_2',
    dimension: 'news',
    name: '利空恐慌抛售',
    check: (ctx) => {
      if (ctx.newsData?.hasNegativeNews && ctx.trade.tradeType === 'sell') {
        return createIssue('news', 'moderate', '利空恐慌抛售',
          '利空消息引发恐慌性卖出',
          '存在利空消息',
          '利空落地后不宜恐慌抛售，观察市场反应');
      }
      return null;
    },
  },

  // ===== 12. 交易成本 =====
  {
    id: 'cost_1',
    dimension: 'cost',
    name: '成本侵蚀利润',
    check: (ctx) => {
      const totalCost = ctx.trade.fee + ctx.trade.stampTax + ctx.trade.transferFee;
      if (ctx.trade.profitLoss > 0 && totalCost > ctx.trade.profitLoss * 0.3) {
        return createIssue('cost', 'minor', '交易成本侵蚀利润',
          '交易成本占盈利比例过高',
          '成本' + totalCost.toFixed(2) + '元，盈利' + ctx.trade.profitLoss.toFixed(2) + '元',
          '控制交易频率，降低交易成本占比');
      }
      return null;
    },
  },
  {
    id: 'cost_2',
    dimension: 'cost',
    name: '小额交易性价比低',
    check: (ctx) => {
      const totalCost = ctx.trade.fee + ctx.trade.stampTax + ctx.trade.transferFee;
      if (ctx.trade.tradeAmount < 5000 && totalCost > ctx.trade.tradeAmount * 0.005) {
        return createIssue('cost', 'minor', '小额交易成本偏高',
          '小额交易的手续费占比过高',
          '交易金额' + ctx.trade.tradeAmount.toFixed(0) + '元，成本占比偏高',
          '小额交易需考虑成本，避免得不偿失');
      }
      return null;
    },
  },

  // ===== 13. 基本面价值 =====
  {
    id: 'fund_1',
    dimension: 'fundamental',
    name: 'ST股风险',
    check: (ctx) => {
      if (ctx.fundamentalData?.isST && ctx.trade.tradeType === 'buy') {
        return createIssue('fundamental', 'critical', '买入ST股票',
          '买入ST股票存在退市风险',
          '标的为ST股票',
          'ST股票风险极高，不建议参与');
      }
      return null;
    },
  },
  {
    id: 'fund_2',
    dimension: 'fundamental',
    name: '高估值检测',
    check: (ctx) => {
      const pe = ctx.fundamentalData?.pe;
      if (pe && pe > 100 && ctx.trade.tradeType === 'buy') {
        return createIssue('fundamental', 'moderate', '高估值买入',
          '股票市盈率过高，存在估值泡沫风险',
          'PE=' + pe.toFixed(1) + '倍',
          'PE>100时需谨慎，评估成长性能否支撑高估值');
      }
      return null;
    },
  },

  // ===== 14. 交易习惯 =====
  {
    id: 'habit_1',
    dimension: 'habit',
    name: '追涨杀跌倾向',
    check: (ctx) => {
      const errors = ctx.userHistory?.frequentErrors;
      if (errors && errors.includes('追涨杀跌')) {
        return createIssue('habit', 'moderate', '追涨杀跌陋习再现',
          '历史交易中存在追涨杀跌习惯',
          '高频错误包含"追涨杀跌"',
          '建立交易系统，克服追涨杀跌陋习');
      }
      return null;
    },
  },
  {
    id: 'habit_2',
    dimension: 'habit',
    name: '低胜率模式',
    check: (ctx) => {
      const winRate = ctx.userHistory?.winRate;
      if (winRate !== undefined && winRate < 35) {
        return createIssue('habit', 'moderate', '交易胜率偏低',
          '历史交易胜率较低，交易模式存在问题',
          '胜率仅' + winRate.toFixed(1) + '%',
          '胜率<40%需反思交易模式，调整策略');
      }
      return null;
    },
  },
];

// ── 创建诊断疑点 ───────────────────────────────────────────────

function createIssue(
  dimension: DiagnosisDimension,
  severity: IssueSeverity,
  title: string,
  description: string,
  evidence: string,
  suggestion: string,
  rootCause?: IssueRootCause,
  standardOperation?: string,
): DiagnosisIssue {
  const commonError = getRandomItem(COMMON_ERRORS[dimension]);
  const cause = rootCause || getDefaultRootCause(dimension, severity);
  return {
    id: generateId(),
    dimension,
    dimensionLabel: DIMENSION_CONFIG[dimension].label,
    severity,
    rootCause: cause,
    title,
    description,
    commonError,
    evidence,
    suggestion,
    standardOperation: standardOperation || suggestion,
  };
}

function getDefaultRootCause(dimension: DiagnosisDimension, _severity: IssueSeverity): IssueRootCause {
  const map: Record<string, IssueRootCause> = {
    psychology: 'psychology_bias',
    discipline: 'discipline_failure',
    habit: 'cognitive_gap',
    position: 'planning_missing',
    cycle: 'cognitive_gap',
    pricePoint: 'cognitive_gap',
    news: 'cognitive_gap',
    cost: 'planning_missing',
    fundamental: 'cognitive_gap',
    capital: 'objective_market',
    chip: 'objective_market',
    technical: 'objective_market',
    theme: 'objective_market',
    sentiment: 'objective_market',
  };
  return map[dimension] || 'cognitive_gap';
}

// ── 维度评分 ───────────────────────────────────────────────────

function calculateDimensionScore(
  dimension: DiagnosisDimension,
  issues: DiagnosisIssue[],
  context: DiagnosisContext,
): number {
  let score = 100;
  
  for (const issue of issues) {
    switch (issue.severity) {
      case 'critical': score -= 25; break;
      case 'moderate': score -= 15; break;
      case 'minor': score -= 8; break;
    }
  }
  
  // 根据维度特性调整
  if (dimension === 'position' && context.trade.positionRatio > 50) {
    score -= 10;
  }
  
  return clamp(score, 0, 100);
}

// ── 综合评分 ───────────────────────────────────────────────────

function calculateOverallScore(dimensions: DimensionDiagnosis[]): number {
  let totalWeight = 0;
  let weightedScore = 0;
  
  for (const dim of dimensions) {
    const weight = DIMENSION_CONFIG[dim.dimension].weight;
    totalWeight += weight;
    weightedScore += dim.score * weight;
  }
  
  return totalWeight > 0 ? Math.round(weightedScore / totalWeight) : 0;
}

function getScoreGrade(score: number): 'excellent' | 'compliant' | 'flawed' | 'failed' {
  if (score >= SCORE_GRADE_CONFIG.excellent.min) return 'excellent';
  if (score >= SCORE_GRADE_CONFIG.compliant.min) return 'compliant';
  if (score >= SCORE_GRADE_CONFIG.flawed.min) return 'flawed';
  return 'failed';
}

// ── 生成优化方案 ───────────────────────────────────────────────

function generateOptimizationPlan(report: FullDiagnosisReport): FullDiagnosisReport['optimizationPlan'] {
  const immediate: string[] = [];
  const shortTerm: string[] = [];
  const longTerm: string[] = [];
  
  for (const issue of report.allIssues) {
    if (issue.severity === 'critical') {
      immediate.push(`【${issue.dimensionLabel}】${issue.title}：${issue.suggestion}`);
    } else if (issue.severity === 'moderate') {
      shortTerm.push(`【${issue.dimensionLabel}】${issue.title}：${issue.suggestion}`);
    } else {
      longTerm.push(`【${issue.dimensionLabel}】${issue.title}：${issue.suggestion}`);
    }
  }
  
  return { immediate, shortTerm, longTerm };
}

function generateBadHabits(report: FullDiagnosisReport): FullDiagnosisReport['badHabits'] {
  const habitMap = new Map<string, { count: number; issues: DiagnosisIssue[] }>();
  
  for (const issue of report.allIssues) {
    if (issue.rootCause === 'psychology_bias' || issue.rootCause === 'discipline_failure') {
      const key = issue.title;
      if (!habitMap.has(key)) {
        habitMap.set(key, { count: 0, issues: [] });
      }
      const entry = habitMap.get(key)!;
      entry.count++;
      entry.issues.push(issue);
    }
  }
  
  return Array.from(habitMap.entries()).map(([habit, data]) => ({
    habit,
    frequency: data.count,
    impact: data.issues.map(i => i.description).join('；'),
    correction: data.issues[0]?.suggestion || '需建立交易纪律，克服此陋习',
  })).sort((a, b) => b.frequency - a.frequency);
}

// ── 主诊断函数 ─────────────────────────────────────────────────

export function runFullDiagnosis(
  trade: TradeRecord,
  context: Partial<DiagnosisContext> = {},
): FullDiagnosisReport {
  const fullContext: DiagnosisContext = {
    trade,
    marketData: context.marketData,
    sectorData: context.sectorData,
    stockData: context.stockData,
    newsData: context.newsData,
    fundamentalData: context.fundamentalData,
    userHistory: context.userHistory,
  };
  
  // 执行所有规则
  const allIssues: DiagnosisIssue[] = [];
  const dimensionIssues = new Map<DiagnosisDimension, DiagnosisIssue[]>();
  
  for (const rule of RULES) {
    try {
      const issue = rule.check(fullContext);
      if (issue) {
        allIssues.push(issue);
        if (!dimensionIssues.has(rule.dimension)) {
          dimensionIssues.set(rule.dimension, []);
        }
        dimensionIssues.get(rule.dimension)!.push(issue);
      }
    } catch (e) {
      console.warn(`Rule ${rule.id} failed:`, e);
    }
  }
  
  // 生成各维度诊断结果
  const dimensions: DimensionDiagnosis[] = (Object.keys(DIMENSION_CONFIG) as DiagnosisDimension[]).map(dim => {
    const issues = dimensionIssues.get(dim) || [];
    const score = calculateDimensionScore(dim, issues, fullContext);
    const config = DIMENSION_CONFIG[dim];
    
    return {
      dimension: dim,
      dimensionLabel: config.label,
      score,
      issues,
      highlights: score >= 80 ? [`${config.label}表现良好，无明显问题`] : [],
      summary: issues.length === 0 
        ? `${config.label}维度未发现明显问题`
        : `${config.label}维度发现${issues.length}个问题，其中严重${issues.filter(i => i.severity === 'critical').length}个`,
    };
  });
  
  // 综合评分
  const overallScore = calculateOverallScore(dimensions);
  const scoreGrade = getScoreGrade(overallScore);
  
  // 统计
  const criticalCount = allIssues.filter(i => i.severity === 'critical').length;
  const moderateCount = allIssues.filter(i => i.severity === 'moderate').length;
  const minorCount = allIssues.filter(i => i.severity === 'minor').length;
  
  // 亮点汇总
  const allHighlights = dimensions.flatMap(d => d.highlights);
  
  // 生成报告
  const report: FullDiagnosisReport = {
    tradeId: trade.id,
    tradeInfo: trade,
    generatedAt: new Date().toISOString(),
    dimensions,
    overallScore,
    scoreGrade,
    allIssues,
    criticalCount,
    moderateCount,
    minorCount,
    allHighlights,
    summary: generateSummary(overallScore, scoreGrade, allIssues),
    optimizationPlan: { immediate: [], shortTerm: [], longTerm: [] },
    badHabits: [],
  };
  
  // 填充优化方案和陋习
  report.optimizationPlan = generateOptimizationPlan(report);
  report.badHabits = generateBadHabits(report);
  
  return report;
}

function generateSummary(
  score: number,
  grade: string,
  issues: DiagnosisIssue[],
): string {
  const gradeLabel = SCORE_GRADE_CONFIG[grade as keyof typeof SCORE_GRADE_CONFIG]?.label || '未知';
  const criticalIssues = issues.filter(i => i.severity === 'critical');
  
  let summary = `本次交易综合评分${score}分，属于"${gradeLabel}"等级。`;
  
  if (criticalIssues.length > 0) {
    summary += `存在${criticalIssues.length}个严重问题：${criticalIssues.map(i => i.title).join('、')}。`;
  }
  
  if (issues.length === 0) {
    summary += '交易操作规范，无明显问题，继续保持。';
  }
  
  return summary;
}

// ── 导出供外部使用 ─────────────────────────────────────────────

export { DIMENSION_CONFIG, COMMON_ERRORS, SCORE_GRADE_CONFIG };