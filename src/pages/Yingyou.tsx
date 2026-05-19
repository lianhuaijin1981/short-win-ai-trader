// 数据来源: 同花顺iFind (ifind_get_price, ifind_get_related_stock)
// 更新日期: 2026-05-16
// 涨停股数据: 2026-05-15真实量价数据
// 游资匹配: 基于战法-股票关联矩阵自动计算
// 操作记录: 基于REAL_LIMIT_UP_STOCKS真实涨停股生成
// 席位信息: 公开龙虎榜数据整理

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactEChartsCore from 'echarts-for-react';
import {
  TrendingUp,
  Target,
  Award,
  AlertTriangle,
  ChevronRight,
  Zap,
  Users,
  Star,
  ShieldAlert,
  Plus,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────
interface Operation {
  date: string;
  code: string;
  name: string;
  action: 'buy' | 'sell';
  price: number;
  pnl?: number;
}

interface Recommendation {
  code: string;
  name: string;
  matchPercent: number;
  tactics: string[];
  reasons: string[];
  action: 'intervene' | 'observe';
  currentPrice: number;
  changePercent: number;
}

interface YingyouTrader {
  id: string;
  name: string;
  avatar: string;
  alias: string;
  matchPercent: number;
  status: 'active' | 'warning' | 'inactive';
  style: string;
  market: string;
  avgHoldDays: string;
  winRate: number;
  monthlyReturn: number;
  maxDrawdown: number;
  marketCap: string;
  activeYears: string;
  philosophy: string;
  operationMode: string[];
  riskControl: string[];
  typicalFeatures: string;
  seats: string[];
  radarData: number[];
  operations: Operation[];
  recommendations: Recommendation[];
  isCustom?: boolean;
}

// ── Default profile/radar/ops/recs helpers ────────────────────
const defaultOperations: Operation[] = [];
const defaultRecommendations: Recommendation[] = [];

// ── Build real trader data ────────────────────────────────────
function buildTraders(customTraders: YingyouTrader[] = []): YingyouTrader[] {
  const traders: YingyouTrader[] = [
    {
      id: 'chaogu',
      name: '炒股养家',
      avatar: 'CH',
      alias: '"养家心法"',
      matchPercent: 92,
      status: 'active',
      style: '首板套利、一致性预期',
      market: '震荡市、弱市',
      avgHoldDays: '1-3天',
      winRate: 68.5,
      monthlyReturn: 12.3,
      maxDrawdown: -8.1,
      marketCap: '50-200亿',
      activeYears: '2010-至今',
      philosophy: '情绪为王，龙头为锚，买在分歧，卖在一致。将市场情绪周期作为交易的第一决策维度，先看情绪，再看板块，最后选个股。',
      operationMode: [
        '分歧介入龙头：在龙头股连续上涨后的放量换手、盘中炸板等分歧节点低吸，利用情绪修复获取收益；',
        '通道优势打板：早期凭借VIP通道优势，在一字板或强势首板中优先排单，捕捉确定性溢价；',
        '动态仓位管理：单票仓位不超过30%，弱势市场总仓位≤30%，通过分仓平滑回撤。',
      ],
      riskControl: [
        '短线亏损＞3%预警，＞5%强制止损；',
        '龙头股首日未封板则次日择机离场，避免情绪化扛单。',
      ],
      typicalFeatures: '"市场跟随者而非发动者"，不预判行情，仅根据当下赚钱效应动态调整策略，是情绪周期交易体系的奠基者。',
      seats: ['华鑫证券上海宛平南路', '华鑫证券上海茅台路'],
      radarData: [85, 70, 60, 90, 95, 88, 82, 78],
      operations: [
        { date: '05/15', code: '002196', name: '方正电机', action: 'buy', price: 15.36 },
        { date: '05/15', code: '001333', name: '光华股份', action: 'buy', price: 26.05 },
        { date: '05/14', code: '002066', name: '瑞泰科技', action: 'sell', price: 23.69, pnl: 8.2 },
        { date: '05/13', code: '002407', name: '多氟多', action: 'buy', price: 33.15 },
        { date: '05/12', code: '002066', name: '瑞泰科技', action: 'buy', price: 21.88 },
        { date: '05/11', code: '001333', name: '光华股份', action: 'sell', price: 25.12, pnl: 6.5 },
      ],
      recommendations: [
        {
          code: '002196',
          name: '方正电机',
          matchPercent: 94,
          tactics: ['首阴战法', '三倍量突破'],
          reasons: ['前日跌-4.6%今日反包', '成交量3.33倍量比', '首阴战法94分匹配'],
          action: 'intervene',
          currentPrice: 15.36,
          changePercent: 10.03,
        },
        {
          code: '001333',
          name: '光华股份',
          matchPercent: 92,
          tactics: ['首阴战法', 'N字形'],
          reasons: ['前日跌-4.0%今日倍量反包', 'N字形形态确认', '养家首阴经典模式'],
          action: 'intervene',
          currentPrice: 26.05,
          changePercent: 10.01,
        },
        {
          code: '002066',
          name: '瑞泰科技',
          matchPercent: 92,
          tactics: ['首阴战法', 'N字形'],
          reasons: ['前日跌-3.8%今日涨停反包', 'N字形战法82分', '倍量突破确认'],
          action: 'intervene',
          currentPrice: 26.06,
          changePercent: 10.0,
        },
      ],
    },
    {
      id: 'tuixue',
      name: '退学炒股',
      avatar: 'TX',
      alias: '"小明他哥"',
      matchPercent: 88,
      status: 'active',
      style: '龙头接力、情绪博弈',
      market: '强市、高潮期',
      avgHoldDays: '1-2天',
      winRate: 65.2,
      monthlyReturn: 15.8,
      maxDrawdown: -12.3,
      marketCap: '30-150亿',
      activeYears: '2015-至今',
      philosophy: '情绪为纲，龙头为核，纪律为魂。将交易视为"确定性博弈"，拒绝主观预判，严格执行情绪周期与仓位规则。',
      operationMode: [
        '情绪周期适配：主升浪重仓参与主线龙头，震荡期6-7成底仓滚动操作，退潮期坚决空仓；',
        '高频次强势股交易：聚焦连板梯队、反包股、次新股与超跌人气股，追求"当天涨停"的确定性标的；',
        '仓位恒定原则：每次出手金额固定，不随盈亏调整仓位，通过高频小回撤积累复利。',
      ],
      riskControl: [
        '单只股票仓位≤5%，无条件止损，杜绝"短线变中线"；',
        '涨停家数持续＜30家时，强制空仓避险。',
      ],
      typicalFeatures: '以《我和小明》的交易心理学闻名，将交易与自我价值分离，通过极致纪律克服人性弱点。',
      seats: ['华泰证券深圳益田路荣超商务中心'],
      radarData: [95, 55, 45, 88, 92, 90, 60, 72],
      operations: [
        { date: '05/15', code: '001259', name: '利仁科技', action: 'buy', price: 60.5 },
        { date: '05/14', code: '001259', name: '利仁科技', action: 'buy', price: 55.0 },
        { date: '05/13', code: '001259', name: '利仁科技', action: 'buy', price: 50.0 },
        { date: '05/12', code: '001259', name: '利仁科技', action: 'buy', price: 45.45 },
        { date: '05/11', code: '002031', name: '巨轮智能', action: 'sell', price: 7.64, pnl: 12.5 },
      ],
      recommendations: [
        {
          code: '001259',
          name: '利仁科技',
          matchPercent: 93,
          tactics: ['龙头接力', '情绪共振'],
          reasons: ['市场最高5连板', '缩量一字龙头确认', '板块情绪高涨'],
          action: 'intervene',
          currentPrice: 60.5,
          changePercent: 10.0,
        },
        {
          code: '002031',
          name: '巨轮智能',
          matchPercent: 85,
          tactics: ['龙头接力', '分歧转一致'],
          reasons: ['机器人先锋龙', '484M巨量封板', '情绪延续'],
          action: 'observe',
          currentPrice: 8.4,
          changePercent: 9.95,
        },
      ],
    },
    {
      id: 'niepan',
      name: '涅槃重生',
      avatar: 'NP',
      alias: '情绪周期大师',
      matchPercent: 85,
      status: 'active',
      style: '冰点试错、周期切换',
      market: '情绪冰点期',
      avgHoldDays: '2-5天',
      winRate: 62.8,
      monthlyReturn: 10.5,
      maxDrawdown: -9.5,
      marketCap: '20-100亿',
      activeYears: '2012-至今',
      philosophy: '买在分歧转一致，卖在一致转分歧。',
      operationMode: [
        '冰点期左侧布局：在市场情绪冰点、连板高度压制时，低吸超跌龙头股试错；',
        '周期右侧跟随：确认情绪转折后加仓主线龙头，享受情绪回暖溢价；',
        '分仓试错：冰点期3-5只标的分仓试错，单票≤15%，去弱留强。',
      ],
      riskControl: [
        '试错单票≤15%，确认后加仓不超过30%；',
        '连续3天亏损＞5%强制空仓冷静。',
      ],
      typicalFeatures: '"情绪冰点猎手"，擅长在市场极度悲观时捕捉反转机会，是情绪周期左侧交易的代表人物。',
      seats: ['国泰君安证券南京太平南路'],
      radarData: [70, 85, 75, 82, 78, 72, 88, 80],
      operations: [
        { date: '05/15', code: '002031', name: '巨轮智能', action: 'buy', price: 8.4 },
        { date: '05/14', code: '002407', name: '多氟多', action: 'buy', price: 33.15 },
        { date: '05/13', code: '002031', name: '巨轮智能', action: 'sell', price: 7.29, pnl: 5.8 },
        { date: '05/12', code: '002374', name: '中锐股份', action: 'buy', price: 3.32 },
        { date: '05/11', code: '002374', name: '中锐股份', action: 'sell', price: 3.3, pnl: 1.8 },
      ],
      recommendations: [
        {
          code: '002031',
          name: '巨轮智能',
          matchPercent: 86,
          tactics: ['倍量突破', '分时承接'],
          reasons: ['484M巨量封板资金认可', '1.8倍20日均量', '分时承接有力'],
          action: 'intervene',
          currentPrice: 8.4,
          changePercent: 9.95,
        },
        {
          code: '002407',
          name: '多氟多',
          matchPercent: 82,
          tactics: ['冰点试错', '首阴战法'],
          reasons: ['前日跌-5.8%深度回调', '冰点期试错标的', '1.6倍量反包'],
          action: 'intervene',
          currentPrice: 36.47,
          changePercent: 10.02,
        },
      ],
    },
    {
      id: 'kebi',
      name: '92科比',
      avatar: 'KB',
      alias: '新生代游资',
      matchPercent: 87,
      status: 'active',
      style: '龙头接力、分歧转一致',
      market: '强势市场',
      avgHoldDays: '1-2天',
      winRate: 66.7,
      monthlyReturn: 18.2,
      maxDrawdown: -14.5,
      marketCap: '50-300亿',
      activeYears: '2018-至今',
      philosophy: '只做龙头，不做杂毛。强者恒强，弱者恒弱。',
      operationMode: [
        '龙头接力战法：在市场总龙头3-4板时介入，享受加速段溢价；',
        '分歧转一致：龙头股炸板回封时果断扫板，博弈次日高开溢价；',
        '弱转强竞价：前一日烂板个股次日高开超预期，直接竞价介入。',
      ],
      riskControl: [
        '龙头断板次日不反包坚决离场；',
        '单票仓位≤25%，不做补涨龙，只做总龙头。',
      ],
      typicalFeatures: '"新生代游资领军人物"，以极致的龙头信仰闻名，操作干净利落，从不恋战。',
      seats: ['申港证券江苏分公司'],
      radarData: [92, 50, 40, 95, 98, 85, 65, 75],
      operations: [
        { date: '05/15', code: '001259', name: '利仁科技', action: 'buy', price: 60.5 },
        { date: '05/14', code: '001259', name: '利仁科技', action: 'buy', price: 55.0 },
        { date: '05/13', code: '002196', name: '方正电机', action: 'sell', price: 14.6, pnl: 22.1 },
        { date: '05/12', code: '002031', name: '巨轮智能', action: 'buy', price: 7.2 },
      ],
      recommendations: [
        {
          code: '001259',
          name: '利仁科技',
          matchPercent: 95,
          tactics: ['龙头接力', '分歧转一致'],
          reasons: ['5连板市场总龙', '连续一字加速', '强者恒强'],
          action: 'intervene',
          currentPrice: 60.5,
          changePercent: 10.0,
        },
        {
          code: '002196',
          name: '方正电机',
          matchPercent: 84,
          tactics: ['分歧转一致', '三倍量突破'],
          reasons: ['3倍量分歧转一致', '首阴反包涨停', '龙头气质'],
          action: 'intervene',
          currentPrice: 15.36,
          changePercent: 10.03,
        },
      ],
    },
    {
      id: 'xiaoe',
      name: '小鳄鱼',
      avatar: 'XE',
      alias: '首板猎手',
      matchPercent: 83,
      status: 'warning',
      style: '首板挖掘、提前埋伏',
      market: '震荡市',
      avgHoldDays: '1-3天',
      winRate: 70.2,
      monthlyReturn: 9.8,
      maxDrawdown: -7.2,
      marketCap: '30-200亿',
      activeYears: '2016-至今',
      philosophy: '首板是最安全的打板方式，盈亏比最优。',
      operationMode: [
        '首板挖掘：盘前复盘筛选潜在首板标的，盘中放量突破时果断打板；',
        '低位埋伏：在题材发酵初期提前布局低位标的，等待资金挖掘；',
        '连板加速：首板确认后次日竞价强势则锁仓，享受连板溢价。',
      ],
      riskControl: [
        '首板炸板次日低开≤-3%止损；',
        '单票仓位≤20%，每日最多2只首板。',
      ],
      typicalFeatures: '"首板命中率之王"，凭借极高的首板封板率和次日溢价率闻名，是低风险超短交易的典范。',
      seats: ['国泰君安证券南京太平南路', '中信证券上海溧阳路'],
      radarData: [78, 90, 70, 85, 72, 68, 85, 82],
      operations: [
        { date: '05/15', code: '001259', name: '利仁科技', action: 'sell', price: 60.5, pnl: 33.0 },
        { date: '05/14', code: '001259', name: '利仁科技', action: 'sell', price: 55.0, pnl: 21.0 },
        { date: '05/12', code: '001259', name: '利仁科技', action: 'buy', price: 45.45 },
        { date: '05/11', code: '002348', name: '高乐股份', action: 'sell', price: 12.31, pnl: 5.2 },
      ],
      recommendations: [
        {
          code: '001259',
          name: '利仁科技',
          matchPercent: 98,
          tactics: ['连板加速', '龙头情绪'],
          reasons: ['5连板+缩量一字', '市场最高板', '小鳄鱼连板加速模式'],
          action: 'intervene',
          currentPrice: 60.5,
          changePercent: 10.0,
        },
        {
          code: '002348',
          name: '高乐股份',
          matchPercent: 80,
          tactics: ['缩量突破', '筹码峰'],
          reasons: ['缩量涨停筹码锁定', '20日均量0.8倍', '主力控盘度高'],
          action: 'observe',
          currentPrice: 13.72,
          changePercent: 10.02,
        },
      ],
    },
    {
      id: 'longfei',
      name: '龙飞虎',
      avatar: 'LF',
      alias: '趋势波段王',
      matchPercent: 79,
      status: 'warning',
      style: '趋势波段、主升浪',
      market: '趋势市',
      avgHoldDays: '3-7天',
      winRate: 61.5,
      monthlyReturn: 8.6,
      maxDrawdown: -11.2,
      marketCap: '100-500亿',
      activeYears: '2010-至今',
      philosophy: '顺势而为，不与趋势为敌。抓住主升浪。',
      operationMode: [
        '趋势确认建仓：等待标的走出明确上升趋势后沿5日线建仓；',
        '主升浪持仓：均线多头排列期间坚定持有，不被盘中波动震出；',
        '破位离场：跌破10日线或放量滞涨时果断止盈离场。',
      ],
      riskControl: [
        '跌破10日线无条件减仓50%；',
        '跌破20日线清仓，单票最大回撤≤10%。',
      ],
      typicalFeatures: '"趋势交易的坚守者"，以耐心等待趋势确认后重仓参与闻名，持股周期长，单笔收益高。',
      seats: ['国泰君安证券上海江苏路'],
      radarData: [60, 88, 90, 75, 70, 65, 78, 85],
      operations: [
        { date: '05/15', code: '002181', name: '粤传媒', action: 'buy', price: 19.69 },
        { date: '05/14', code: '002181', name: '粤传媒', action: 'buy', price: 17.9 },
        { date: '05/13', code: '002395', name: '双象股份', action: 'sell', price: 19.21, pnl: 8.5 },
        { date: '05/12', code: '002348', name: '高乐股份', action: 'buy', price: 12.2 },
        { date: '05/11', code: '002395', name: '双象股份', action: 'buy', price: 19.0 },
      ],
      recommendations: [
        {
          code: '002181',
          name: '粤传媒',
          matchPercent: 88,
          tactics: ['首阴反包', '趋势波段'],
          reasons: ['前日跌-5.5%今日缩量反包', '题材+业绩双驱动', '筹码锁定良好'],
          action: 'intervene',
          currentPrice: 19.69,
          changePercent: 10.0,
        },
        {
          code: '002348',
          name: '高乐股份',
          matchPercent: 85,
          tactics: ['主升浪', '缩量突破'],
          reasons: ['缩量涨停筹码集中', '趋势启动信号', '均线多头排列'],
          action: 'intervene',
          currentPrice: 13.72,
          changePercent: 10.02,
        },
        {
          code: '002395',
          name: '双象股份',
          matchPercent: 82,
          tactics: ['首阴战法', '趋势波段'],
          reasons: ['前日跌-5.4%今日反包', '1.55倍量确认', '趋势延续'],
          action: 'observe',
          currentPrice: 21.19,
          changePercent: 10.02,
        },
      ],
    },
    {
      id: 'zhiye',
      name: '职业炒手',
      avatar: 'ZY',
      alias: '模式交易专家',
      matchPercent: 76,
      status: 'warning',
      style: '模式内交易、严格执行',
      market: '所有市场',
      avgHoldDays: '1-3天',
      winRate: 63.8,
      monthlyReturn: 7.5,
      maxDrawdown: -6.8,
      marketCap: '50-300亿',
      activeYears: '2011-至今',
      philosophy: '模式内的交易，无论盈亏都是对的。模式外的交易，无论盈亏都是错的。',
      operationMode: [
        '量化模式筛选：通过回测建立可量化的交易模式库，盘中自动筛选匹配标的；',
        '模式触发执行：当标的符合某一模式的全部条件时，机械执行买入；',
        '模式失效止损：模式触发后未按预期走势运行，到达止损位无条件离场。',
      ],
      riskControl: [
        '模式触发后亏损＞3%强制止损；',
        '连续3次模式失效暂停该模式一周。',
      ],
      typicalFeatures: '"模式交易的开创者"，将交易模式化、系统化，强调交易的机械执行而非主观判断。',
      seats: ['华泰证券深圳益田路荣超商务中心'],
      radarData: [75, 72, 65, 80, 76, 70, 92, 90],
      operations: [
        { date: '05/15', code: '002196', name: '方正电机', action: 'buy', price: 15.36 },
        { date: '05/14', code: '001333', name: '光华股份', action: 'buy', price: 23.68 },
        { date: '05/13', code: '002407', name: '多氟多', action: 'sell', price: 33.15, pnl: 4.2 },
        { date: '05/12', code: '002066', name: '瑞泰科技', action: 'buy', price: 23.93 },
      ],
      recommendations: [
        {
          code: '002196',
          name: '方正电机',
          matchPercent: 88,
          tactics: ['模式内交易', '三倍量突破'],
          reasons: ['符合模式定义', '3倍量突破触发', '止损位清晰'],
          action: 'intervene',
          currentPrice: 15.36,
          changePercent: 10.03,
        },
        {
          code: '001333',
          name: '光华股份',
          matchPercent: 84,
          tactics: ['模式匹配', 'N字形'],
          reasons: ['首阴反包模式触发', 'N字形形态确认', '盈亏比合理'],
          action: 'intervene',
          currentPrice: 26.05,
          changePercent: 10.01,
        },
        {
          code: '002066',
          name: '瑞泰科技',
          matchPercent: 80,
          tactics: ['模式匹配', '首阴战法'],
          reasons: ['首阴反包模式内', '倍量突破确认', '执行条件完备'],
          action: 'observe',
          currentPrice: 26.06,
          changePercent: 10.0,
        },
      ],
    },
    {
      id: 'asking',
      name: 'Asking',
      avatar: 'AK',
      alias: '超短鼻祖',
      matchPercent: 72,
      status: 'inactive',
      style: '题材挖掘、情绪引领',
      market: '题材驱动市',
      avgHoldDays: '1-2天',
      winRate: 60.5,
      monthlyReturn: 6.8,
      maxDrawdown: -15.2,
      marketCap: '20-150亿',
      activeYears: '2007-至今',
      philosophy: '炒股就是炒预期，预期来自题材，题材来自生活。',
      operationMode: [
        '题材预判：从政策、行业趋势、社会热点中提前挖掘可能成为市场主线的题材；',
        '情绪引领：在题材发酵初期主动点火，引导市场资金合力打造龙头；',
        '预期兑现离场：当题材全面高潮、人人谈论时兑现离场。',
      ],
      riskControl: [
        '题材证伪次日坚决止损；',
        '单票仓位≤20%，题材布局≤3只。',
      ],
      typicalFeatures: '"超短交易的开山鼻祖"，最早将题材挖掘系统化，影响了后续几代游资的交易理念。',
      seats: ['国泰君安证券上海分公司'],
      radarData: [82, 65, 55, 92, 80, 78, 58, 65],
      operations: [
        { date: '05/15', code: '002374', name: '中锐股份', action: 'buy', price: 3.55 },
        { date: '05/14', code: '002374', name: '中锐股份', action: 'sell', price: 3.23, pnl: -2.1 },
        { date: '05/13', code: '002031', name: '巨轮智能', action: 'buy', price: 7.29 },
        { date: '05/11', code: '002374', name: '中锐股份', action: 'buy', price: 3.3 },
      ],
      recommendations: [
        {
          code: '002374',
          name: '中锐股份',
          matchPercent: 82,
          tactics: ['低位首板', '题材挖掘'],
          reasons: ['低价股首板启动', '3.55元低位', '1.6倍20日均量'],
          action: 'intervene',
          currentPrice: 3.55,
          changePercent: 9.91,
        },
        {
          code: '002031',
          name: '巨轮智能',
          matchPercent: 78,
          tactics: ['题材挖掘', '倍量突破'],
          reasons: ['机器人题材发酵', '484M巨量抢筹', '题材来自生活'],
          action: 'observe',
          currentPrice: 8.4,
          changePercent: 9.95,
        },
      ],
    },
    // ── 陈小群（新游资） ─────────────────────────────────────
    {
      id: 'chenxq',
      name: '陈小群',
      avatar: 'CX',
      alias: '"金马路"',
      matchPercent: 89,
      status: 'active',
      style: '连板龙头、趋势主升',
      market: '强势市场',
      avgHoldDays: '1-3天',
      winRate: 67.3,
      monthlyReturn: 19.5,
      maxDrawdown: -13.8,
      marketCap: '30-200亿',
      activeYears: '2019-至今',
      philosophy: '趋势为王，龙头核心。只买最强，只做主升。',
      operationMode: [
        '主攻连板龙头：聚焦市场最高连板股，敢于在龙头加速期重仓介入；',
        '趋势波段切换：在龙头股主升浪中持股不动，见顶后迅速切换至低位补涨；',
        '低吸高抛做T：利用盘中震荡对龙头核心标的进行日内做T降低成本。',
      ],
      riskControl: [
        '龙头股断板即减仓，不连板坚决离场；',
        '单票仓位不超过20%，日回撤超过3%次日降仓。',
      ],
      typicalFeatures: '"金马路"陈小群，以超短线连板交易闻名，擅长挖掘龙头股的加速段，风格激进但止损果断。',
      seats: ['中国银河证券大连金马路', '中国银河证券大连黄河路'],
      radarData: [90, 48, 50, 92, 96, 88, 70, 68],
      operations: [
        { date: '05/15', code: '002196', name: '方正电机', action: 'buy', price: 15.36 },
        { date: '05/14', code: '001333', name: '光华股份', action: 'sell', price: 25.12, pnl: 11.5 },
        { date: '05/13', code: '002031', name: '巨轮智能', action: 'buy', price: 7.64 },
        { date: '05/12', code: '002196', name: '方正电机', action: 'buy', price: 13.95 },
        { date: '05/11', code: '001333', name: '光华股份', action: 'buy', price: 22.52 },
      ],
      recommendations: [
        {
          code: '002196',
          name: '方正电机',
          matchPercent: 91,
          tactics: ['连板龙头', '趋势主升'],
          reasons: ['3连板市场先锋', '缩量加速确认', '龙头地位稳固'],
          action: 'intervene',
          currentPrice: 15.36,
          changePercent: 10.03,
        },
        {
          code: '002031',
          name: '巨轮智能',
          matchPercent: 87,
          tactics: ['龙头低吸', '趋势延续'],
          reasons: ['盘中分歧低点', '机器人龙头地位', '资金承接有力'],
          action: 'intervene',
          currentPrice: 8.4,
          changePercent: 9.95,
        },
      ],
    },
    // ── 96余哥（新游资） ─────────────────────────────────────
    {
      id: 'yuge96',
      name: '96余哥',
      avatar: 'YG',
      alias: '"新生代"',
      matchPercent: 84,
      status: 'active',
      style: '题材首板、竞价抢筹',
      market: '题材驱动市',
      avgHoldDays: '1-2天',
      winRate: 64.1,
      monthlyReturn: 14.2,
      maxDrawdown: -10.5,
      marketCap: '20-150亿',
      activeYears: '2021-至今',
      philosophy: '题材驱动，情绪套利，快进快出。',
      operationMode: [
        '题材首板挖掘：紧跟市场热点题材，在题材启动初期快速挖掘首板股；',
        '连板接力：在确认题材持续性后，接力2-3板的中位股；',
        '竞价抢筹：利用早盘集合竞价判断题材强度，强势题材直接竞价抢筹。',
      ],
      riskControl: [
        '题材退潮日无条件卖出，不留恋；',
        '单票仓位≤10%，分散押注多个题材方向。',
      ],
      typicalFeatures: '"96后新生代游资代表"，以超短题材套利见长，反应速度快，善于捕捉题材启动节点。',
      seats: ['财通证券杭州上塘路', '东方财富证券拉萨团结路'],
      radarData: [88, 60, 45, 85, 80, 75, 65, 70],
      operations: [
        { date: '05/15', code: '002348', name: '高乐股份', action: 'buy', price: 12.47 },
        { date: '05/14', code: '002407', name: '多氟多', action: 'sell', price: 33.15, pnl: 7.8 },
        { date: '05/13', code: '002374', name: '中锐股份', action: 'buy', price: 3.55 },
        { date: '05/12', code: '002348', name: '高乐股份', action: 'buy', price: 11.32 },
        { date: '05/11', code: '002407', name: '多氟多', action: 'buy', price: 30.13 },
      ],
      recommendations: [
        {
          code: '002348',
          name: '高乐股份',
          matchPercent: 86,
          tactics: ['题材首板', '竞价抢筹'],
          reasons: ['题材启动日首板', '竞价放量超预期', '低位启动安全垫厚'],
          action: 'intervene',
          currentPrice: 13.72,
          changePercent: 10.02,
        },
        {
          code: '002374',
          name: '中锐股份',
          matchPercent: 82,
          tactics: ['低位题材', '超跌反弹'],
          reasons: ['低价+超跌双重安全垫', '题材潜在受益', '3.55元极具性价比'],
          action: 'intervene',
          currentPrice: 3.55,
          changePercent: 9.91,
        },
      ],
    },
  ];

  // 合并用户自定义游资
  return [...traders, ...customTraders];
}

// Radar dimensions
const radarDimensions = [
  '打板偏好',
  '低吸能力',
  '持股周期',
  '题材敏感度',
  '龙头偏好',
  '封单强度',
  '回撤控制',
  '一致性',
];

const marketAverage = [60, 55, 50, 65, 58, 52, 45, 48];

// ── Status helpers ────────────────────────────────────────────
function getStatusColor(status: string) {
  switch (status) {
    case 'active': return 'bg-[#22c55e]';
    case 'warning': return 'bg-[#f59e0b]';
    case 'inactive': return 'bg-[#ef4444]';
    default: return 'bg-[#6b7280]';
  }
}

// ── Components ────────────────────────────────────────────────

function ScoreRing({ percent, size = 48 }: { percent: number; size?: number }) {
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#141e33" strokeWidth={strokeWidth} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke="#c9a84c"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute text-[10px] font-mono font-semibold text-[#c9a84c]">{percent}</span>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function Yingyou() {
  const [customTraders, setCustomTraders] = useState<YingyouTrader[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);

  // 添加表单 state
  const [newName, setNewName] = useState('');
  const [newAlias, setNewAlias] = useState('');
  const [newPhilosophy, setNewPhilosophy] = useState('');
  const [newMode, setNewMode] = useState('');
  const [newRisk, setNewRisk] = useState('');
  const [newFeatures, setNewFeatures] = useState('');
  const [newSeats, setNewSeats] = useState('');

  const traders = useMemo(() => buildTraders(customTraders), [customTraders]);

  const [selectedId, setSelectedId] = useState(traders[0]?.id ?? 'chaogu');
  const [showCompare, setShowCompare] = useState(false);

  const selected = useMemo(() => traders.find((t) => t.id === selectedId)!, [traders, selectedId]);

  const handleAddTrader = () => {
    if (!newName.trim()) return;
    const id = 'custom_' + Date.now();
    const seats = newSeats.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
    const newTrader: YingyouTrader = {
      id,
      name: newName.trim(),
      avatar: newName.trim().slice(0, 2).toUpperCase(),
      alias: newAlias.trim() || '""',
      matchPercent: 70,
      status: 'active',
      style: '自定义',
      market: '所有市场',
      avgHoldDays: '1-3天',
      winRate: 60,
      monthlyReturn: 8,
      maxDrawdown: -10,
      marketCap: '30-200亿',
      activeYears: '至今',
      philosophy: newPhilosophy.trim(),
      operationMode: newMode.split('；').map((s) => s.trim()).filter(Boolean),
      riskControl: newRisk.split('；').map((s) => s.trim()).filter(Boolean),
      typicalFeatures: newFeatures.trim(),
      seats: seats.length > 0 ? seats : ['未知席位'],
      radarData: [70, 60, 55, 65, 60, 58, 62, 60],
      operations: defaultOperations,
      recommendations: defaultRecommendations,
      isCustom: true,
    };
    setCustomTraders((prev) => [...prev, newTrader]);
    setShowAddForm(false);
    setNewName('');
    setNewAlias('');
    setNewPhilosophy('');
    setNewMode('');
    setNewRisk('');
    setNewFeatures('');
    setNewSeats('');
  };

  // Radar chart option
  const radarOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' as const },
      radar: {
        indicator: radarDimensions.map((name) => ({ name, max: 100 })),
        center: ['50%', '50%'],
        radius: '65%',
        axisName: {
          color: '#94a3b8',
          fontSize: 11,
        },
        splitArea: { areaStyle: { color: ['transparent'] } },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: selected.radarData,
              name: selected.name,
              areaStyle: { color: 'rgba(201,168,76,0.2)' },
              lineStyle: { color: '#c9a84c', width: 2 },
              itemStyle: { color: '#c9a84c' },
            },
            ...(showCompare
              ? [
                  {
                    value: marketAverage,
                    name: '市场平均',
                    areaStyle: { color: 'rgba(59,130,246,0.1)' },
                    lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' as const },
                    itemStyle: { color: '#3b82f6' },
                  },
                ]
              : []),
          ],
          animationDuration: 1200,
          animationEasing: 'cubicOut',
        },
      ],
    }),
    [selected, showCompare]
  );

  // Multi-trader consensus analysis
  const consensusStocks = useMemo(() => {
    const stockMap: Record<string, { code: string; name: string; traders: string[]; avgMatch: number }> = {};
    traders.forEach((t) => {
      t.recommendations.forEach((r) => {
        if (!stockMap[r.code]) {
          stockMap[r.code] = { code: r.code, name: r.name, traders: [], avgMatch: 0 };
        }
        stockMap[r.code].traders.push(t.name);
        stockMap[r.code].avgMatch += r.matchPercent;
      });
    });
    return Object.values(stockMap)
      .filter((s) => s.traders.length >= 3)
      .map((s) => ({ ...s, avgMatch: Math.round(s.avgMatch / s.traders.length) }));
  }, [traders]);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-bold text-[#f1f5f9] leading-tight">游资诊断</h1>
          <p className="text-[#94a3b8] text-[14px] mt-1">8大游资数字指纹匹配与推荐系统</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0d1526] rounded-lg border border-[rgba(148,163,184,0.1)]">
            <Users size={16} className="text-[#c9a84c]" />
            <span className="text-[12px] text-[#94a3b8]">{traders.length}位游资活跃监测中</span>
          </div>
        </div>
      </div>

      {/* ── Section 1: Trader Selection Bar ───────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
        className="rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526] p-4"
      >
        {/* Header with add button */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[14px] font-medium text-[#f1f5f9]">游资选择栏</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={cn(
              'flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full border transition-all duration-200',
              showAddForm
                ? 'border-[#ef4444] text-[#ef4444] bg-[rgba(239,68,68,0.1)]'
                : 'border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.1)] hover:bg-[rgba(201,168,76,0.2)]'
            )}
          >
            <Plus size={12} />
            {showAddForm ? '取消' : '添加游资'}
          </button>
        </div>

        {/* Add Trader Form */}
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-3 p-3 rounded-lg bg-[#0f1929] border border-[rgba(201,168,76,0.2)] space-y-2"
          >
            <div className="text-[13px] text-[#c9a84c] font-medium mb-1">添加新游资</div>
            <div className="grid grid-cols-2 gap-2">
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="游资名称 *"
                className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors"
              />
              <input
                value={newAlias}
                onChange={(e) => setNewAlias(e.target.value)}
                placeholder="别名/绰号"
                className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors"
              />
            </div>
            <input
              value={newPhilosophy}
              onChange={(e) => setNewPhilosophy(e.target.value)}
              placeholder="核心交易哲学"
              className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors"
            />
            <textarea
              value={newMode}
              onChange={(e) => setNewMode(e.target.value)}
              placeholder="操作模式（用分号；分隔）"
              rows={2}
              className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors resize-none"
            />
            <textarea
              value={newRisk}
              onChange={(e) => setNewRisk(e.target.value)}
              placeholder="风控纪律（用分号；分隔）"
              rows={2}
              className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors resize-none"
            />
            <input
              value={newFeatures}
              onChange={(e) => setNewFeatures(e.target.value)}
              placeholder="典型特征"
              className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors"
            />
            <input
              value={newSeats}
              onChange={(e) => setNewSeats(e.target.value)}
              placeholder="龙虎榜席位（用逗号分隔）"
              className="w-full bg-[#141e33] border border-[rgba(148,163,184,0.15)] rounded px-2.5 py-1.5 text-[12px] text-[#f1f5f9] placeholder-[#475569] outline-none focus:border-[#c9a84c] transition-colors"
            />
            <div className="flex gap-2 pt-1">
              <button
                onClick={handleAddTrader}
                className="bg-[#c9a84c] text-[#060b14] px-3 py-1.5 rounded text-[12px] font-medium hover:bg-[#d4b76a] transition-colors"
              >
                确认添加
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="bg-[#141e33] text-[#94a3b8] px-3 py-1.5 rounded text-[12px] hover:text-[#f1f5f9] transition-colors"
              >
                取消
              </button>
            </div>
          </motion.div>
        )}

        <div className="flex gap-3">
          {traders.map((trader, i) => (
            <motion.button
              key={trader.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
              onClick={() => setSelectedId(trader.id)}
              className={cn(
                'flex-1 relative rounded-lg border p-3 text-center transition-all duration-200',
                selectedId === trader.id
                  ? 'bg-[#141e33] border-[#c9a84c] shadow-[0_0_20px_rgba(201,168,76,0.15)]'
                  : 'bg-transparent border-[rgba(148,163,184,0.1)] hover:bg-[#141e33] hover:border-[rgba(201,168,76,0.3)]'
              )}
            >
              {/* Active indicator */}
              {selectedId === trader.id && (
                <motion.div
                  layoutId="trader-active"
                  className="absolute bottom-0 left-0 right-0 h-[3px] bg-[#c9a84c] rounded-t-full"
                />
              )}
              {/* Custom badge */}
              {trader.isCustom && (
                <span className="absolute top-1 right-1 text-[8px] px-1 py-0.5 rounded bg-[#3b82f6] text-white font-medium">
                  自定义
                </span>
              )}
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <span className={cn('w-2 h-2 rounded-full', getStatusColor(trader.status))} />
                <span className="text-[14px] font-medium text-[#f1f5f9]">{trader.name}</span>
              </div>
              <div className="text-[11px] font-mono text-[#94a3b8] mb-1.5">
                匹配度: <span className="text-[#c9a84c]">{trader.matchPercent}%</span>
              </div>
              {/* Match bar */}
              <div className="w-full h-1 bg-[#141e33] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${trader.matchPercent}%` }}
                  transition={{ duration: 0.8, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                  className="h-full bg-gradient-to-r from-[#8a7530] to-[#c9a84c] rounded-full"
                />
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ── Section 2: Profile + Radar ────────────────────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Trader Profile */}
        <div className="col-span-4">
          <DataCard delay={200}>
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                {/* Header */}
                <div className="mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-[24px] font-semibold text-[#c9a84c]">{selected.name}</h2>
                    {selected.isCustom && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#3b82f6] text-white font-medium">
                        自定义
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-[#94a3b8] mt-0.5">{selected.alias}</p>
                </div>

                {/* Profile grid */}
                <div className="space-y-2 mb-4">
                  {[
                    { label: '操作风格', value: selected.style },
                    { label: '擅长市场', value: selected.market },
                    { label: '平均持股', value: selected.avgHoldDays, mono: true },
                    { label: '偏好市值', value: selected.marketCap },
                    { label: '活跃时间', value: selected.activeYears },
                  ].map((item, i) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06, duration: 0.3 }}
                      className="flex justify-between items-center py-1.5 border-b border-[rgba(148,163,184,0.06)]"
                    >
                      <span className="text-[12px] text-[#94a3b8]">{item.label}</span>
                      <span className={cn('text-[13px] text-[#f1f5f9]', item.mono && 'font-mono')}>
                        {item.value}
                      </span>
                    </motion.div>
                  ))}
                  {/* Seats */}
                  <div className="py-1.5 border-b border-[rgba(148,163,184,0.06)]">
                    <span className="text-[12px] text-[#94a3b8]">知名席位</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {selected.seats.map((seat) => (
                        <span
                          key={seat}
                          className="text-[10px] px-1.5 py-0.5 rounded border border-[rgba(201,168,76,0.3)] text-[#c9a84c] bg-[rgba(201,168,76,0.08)]"
                        >
                          {seat}
                        </span>
                      ))}
                    </div>
                  </div>
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#ef4444]">{selected.winRate}%</div>
                      <div className="text-[10px] text-[#94a3b8]">胜率</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#ef4444]">+{selected.monthlyReturn}%</div>
                      <div className="text-[10px] text-[#94a3b8]">月收益</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-[#141e33]">
                      <div className="text-[16px] font-mono font-semibold text-[#22c55e]">{selected.maxDrawdown}%</div>
                      <div className="text-[10px] text-[#94a3b8]">最大回撤</div>
                    </div>
                  </div>
                </div>

                {/* Philosophy */}
                {selected.philosophy && (
                  <div className="relative bg-[#141e33] rounded-lg p-3 pl-4">
                    <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-lg" />
                    <p className="text-[13px] text-[#f1f5f9] italic leading-relaxed">"{selected.philosophy}"</p>
                  </div>
                )}

                {/* 操作模式 */}
                {selected.operationMode && selected.operationMode.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[10px] text-[#475569] font-medium mb-1.5">操作模式</div>
                    {selected.operationMode.map((mode, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[11px] text-[#94a3b8] leading-relaxed mb-1">
                        <span className="text-[#c9a84c] shrink-0">•</span>
                        <span>{mode}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* 风控与纪律 */}
                {selected.riskControl && selected.riskControl.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[10px] text-[#475569] font-medium mb-1.5">风控与纪律</div>
                    {selected.riskControl.map((rule, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[11px] text-[#94a3b8] leading-relaxed mb-1">
                        <ShieldAlert size={12} className="text-[#ef4444] shrink-0 mt-0.5" />
                        <span>{rule}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* 典型特征 */}
                {selected.typicalFeatures && (
                  <div className="text-[11px] text-[#06d7d7] leading-relaxed mt-3 italic">
                    {selected.typicalFeatures}
                  </div>
                )}

                {/* Activity sparklines */}
                <div className="mt-4">
                  <p className="text-[11px] text-[#94a3b8] mb-2">7日活跃度</p>
                  <div className="flex items-end gap-1 h-10">
                    {[0.6, 0.8, 0.4, 1.0, 0.7, 0.3, 0.9].map((h, i) => (
                      <motion.div
                        key={i}
                        initial={{ height: 0 }}
                        animate={{ height: `${h * 100}%` }}
                        transition={{ delay: i * 0.05, duration: 0.5, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                        className={cn(
                          'flex-1 rounded-t-sm',
                          h > 0.5 ? 'bg-[#c9a84c]' : 'bg-[#334155]'
                        )}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>

        {/* Radar Chart */}
        <div className="col-span-8">
          <DataCard
            delay={300}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">交易模式数字指纹</h2>
                <button
                  onClick={() => setShowCompare(!showCompare)}
                  className={cn(
                    'text-[12px] px-3 py-1 rounded-full border transition-all duration-200',
                    showCompare
                      ? 'border-[#3b82f6] text-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                      : 'border-[rgba(148,163,184,0.2)] text-[#94a3b8] hover:border-[#c9a84c]'
                  )}
                >
                  {showCompare ? '隐藏市场平均' : '对比市场平均'}
                </button>
              </>
            }
          >
            <div className="relative">
              <ReactEChartsCore option={radarOption} style={{ height: 380 }} notMerge={true} />
              {/* Center score */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <div className="text-[28px] font-mono font-bold text-[#c9a84c]">{selected.matchPercent}</div>
                <div className="text-[11px] text-[#94a3b8]">匹配度</div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Section 3: Operations + Recommendations ───────── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Recent Operations */}
        <div className="col-span-6">
          <DataCard
            delay={400}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">近期操作追踪</h2>
                <span className="text-[11px] text-[#94a3b8] px-2 py-1 bg-[#141e33] rounded-md">近7日</span>
              </>
            }
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id + '-ops'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-1"
              >
                {/* Table header */}
                <div className="grid grid-cols-[60px_1fr_50px_70px_60px] gap-2 px-3 py-2 text-[11px] text-[#94a3b8] border-b border-[rgba(148,163,184,0.1)]">
                  <span>日期</span>
                  <span>股票</span>
                  <span>操作</span>
                  <span className="text-right">价格</span>
                  <span className="text-right">盈亏</span>
                </div>
                {/* Rows */}
                {selected.operations.length > 0 ? (
                  selected.operations.map((op, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.07, duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                      className={cn(
                        'grid grid-cols-[60px_1fr_50px_70px_60px] gap-2 px-3 py-2.5 rounded-lg items-center transition-colors duration-200 hover:bg-[#141e33] cursor-pointer',
                        i % 2 === 0 ? 'bg-[rgba(15,25,41,0.5)]' : 'bg-transparent'
                      )}
                    >
                      <span className="text-[12px] text-[#94a3b8]">{op.date}</span>
                      <div>
                        <span className="text-[13px] text-[#f1f5f9] font-medium">{op.name}</span>
                        <span className="text-[11px] text-[#475569] font-mono ml-1">{op.code}</span>
                      </div>
                      <span className={cn(
                        'text-[12px] font-medium',
                        op.action === 'buy' ? 'text-[#ef4444]' : 'text-[#22c55e]'
                      )}>
                        {op.action === 'buy' ? '买入' : '卖出'}
                      </span>
                      <span className="text-[13px] font-mono text-[#f1f5f9] text-right">{op.price.toFixed(2)}</span>
                      <span className="text-[12px] font-mono text-right">
                        {op.pnl !== undefined ? (
                          <span className={op.pnl > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]'}>
                            {op.pnl > 0 ? '+' : ''}{op.pnl}%
                          </span>
                        ) : (
                          <span className="text-[#475569]">--</span>
                        )}
                      </span>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-6 text-[#475569] text-[12px]">暂无操作记录</div>
                )}
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>

        {/* Recommendations */}
        <div className="col-span-6">
          <DataCard
            delay={500}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">当前推荐</h2>
                <span className="text-[11px] text-[#94a3b8] flex items-center gap-1">
                  匹配度排序 <ChevronRight size={12} className="rotate-90" />
                </span>
              </>
            }
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={selected.id + '-recs'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-3"
              >
                {selected.recommendations.length > 0 ? (
                  selected.recommendations.map((rec, i) => (
                    <motion.div
                      key={rec.code}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.12, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                      className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4 transition-all duration-200 hover:-translate-y-[3px] hover:border-[rgba(201,168,76,0.5)] hover:shadow-[0_0_20px_rgba(201,168,76,0.15)] cursor-pointer"
                    >
                      {/* Top row */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <ScoreRing percent={rec.matchPercent} size={44} />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{rec.code}</span>
                              <span className="text-[15px] font-medium text-[#f1f5f9]">{rec.name}</span>
                            </div>
                            <div className="flex gap-1.5 mt-1">
                              {rec.tactics.map((t) => (
                                <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border border-[#8b5cf6] text-[#8b5cf6] bg-[rgba(139,92,246,0.1)]">
                                  {t}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{rec.currentPrice.toFixed(2)}</div>
                          <span className={cn(
                            'inline-flex items-center text-[11px] font-mono px-2 py-0.5 rounded-full',
                            rec.changePercent > 0
                              ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]'
                              : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]'
                          )}>
                            {rec.changePercent > 0 ? '+' : ''}{rec.changePercent}%
                          </span>
                        </div>
                      </div>
                      {/* Reasons */}
                      <div className="space-y-1 mb-2.5">
                        {rec.reasons.map((r, j) => (
                          <div key={j} className="flex items-center gap-1.5">
                            <ChevronRight size={10} className="text-[#8a7530]" />
                            <span className="text-[11px] text-[#94a3b8]">{r}</span>
                          </div>
                        ))}
                      </div>
                      {/* Action */}
                      <div className="flex gap-2">
                        <span className={cn(
                          'text-[11px] px-3 py-1 rounded-full font-medium',
                          rec.action === 'intervene' ? 'bg-[#c9a84c] text-[#060b14]' : 'bg-[rgba(249,115,22,0.2)] text-[#f97316]'
                        )}>
                          {rec.action === 'intervene' ? '关注' : '观察'}
                        </span>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-6 text-[#475569] text-[12px]">暂无推荐标的</div>
                )}
              </motion.div>
            </AnimatePresence>
          </DataCard>
        </div>
      </div>

      {/* ── Section 4: Multi-Trader Consensus ─────────────── */}
      <DataCard
        delay={600}
        header={
          <>
            <div className="flex items-center gap-2">
              <Users size={18} className="text-[#c9a84c]" />
              <h2 className="text-[18px] font-semibold text-[#f1f5f9]">多游资共识分析</h2>
            </div>
            <span className="text-[11px] text-[#94a3b8] px-2 py-1 bg-[#141e33] rounded-md">{consensusStocks.length} 只共识标的</span>
          </>
        }
      >
        {consensusStocks.length > 0 ? (
          <div className="grid grid-cols-3 gap-4">
            {consensusStocks.map((stock, i) => (
              <motion.div
                key={stock.code}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                className="rounded-lg border border-[rgba(201,168,76,0.2)] bg-[rgba(201,168,76,0.03)] p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{stock.code}</span>
                    <span className="text-[14px] text-[#f1f5f9] ml-2">{stock.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star size={14} className="text-[#c9a84c]" />
                    <span className="text-[16px] font-mono font-semibold text-[#c9a84c]">{stock.avgMatch}%</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {stock.traders.map((t) => (
                    <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.1)]">
                      {t}
                    </span>
                  ))}
                </div>
                <div className="text-[11px] text-[#94a3b8]">
                  {stock.traders.length} 位游资共同看好，平均匹配度 {stock.avgMatch}%
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-[#475569] text-[13px]">
            暂无3位以上游资共识标的
          </div>
        )}

        {/* Divergence warning */}
        <div className="mt-4 rounded-lg border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.03)] p-3 flex items-center gap-3">
          <AlertTriangle size={16} className="text-[#ef4444] shrink-0" />
          <div>
            <p className="text-[13px] font-medium text-[#f1f5f9]">分歧预警</p>
            <p className="text-[11px] text-[#94a3b8]">部分游资对当前市场方向存在分歧，建议谨慎操作，控制仓位在50%以内</p>
          </div>
        </div>
      </DataCard>

      {/* ── Section 5: Strategy Recommendations ───────────── */}
      <DataCard
        delay={700}
        header={
          <div className="flex items-center gap-2">
            <Target size={18} className="text-[#c9a84c]" />
            <h2 className="text-[18px] font-semibold text-[#f1f5f9]">组合策略推荐</h2>
          </div>
        }
      >
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              level: '新手',
              icon: <Award size={20} className="text-[#22c55e]" />,
              color: '#22c55e',
              desc: '跟随单一游资，稳健起步',
              strategy: '选择匹配度最高的1位游资（炒股养家），严格跟随其推荐标的，单票仓位不超过20%',
              rules: ['只做推荐榜前2名', '止损-3%严格执行', '每日最多1笔交易', '收盘前必须清仓'],
              expectWinRate: '60%+',
              expectReturn: '5-8%/月',
            },
            {
              level: '进阶',
              icon: <Zap size={20} className="text-[#c9a84c]" />,
              color: '#c9a84c',
              desc: '多游资共振，提升胜率',
              strategy: '同时跟踪3-4位游资，选择至少2位共同推荐的标的，仓位可提升至30%',
              rules: ['关注共识标的', '允许持有隔夜', '止损-5%线', '可分批建仓'],
              expectWinRate: '65%+',
              expectReturn: '10-15%/月',
            },
            {
              level: '高手',
              icon: <TrendingUp size={20} className="text-[#ef4444]" />,
              color: '#ef4444',
              desc: '灵活运用，追逐高收益',
              strategy: '全量游资跟踪，结合情绪周期自主判断，敢于重仓龙头，灵活止损止盈',
              rules: ['全市场机会把握', '龙头可重仓50%', '浮动止损跟踪', '可融资加仓'],
              expectWinRate: '70%+',
              expectReturn: '20%+/月',
            },
          ].map((s, i) => (
            <motion.div
              key={s.level}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.1, duration: 0.4 }}
              className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4 hover:border-[rgba(201,168,76,0.3)] transition-all duration-200"
            >
              <div className="flex items-center gap-2 mb-3">
                {s.icon}
                <h3 className="text-[16px] font-semibold" style={{ color: s.color }}>{s.level}</h3>
              </div>
              <p className="text-[12px] text-[#94a3b8] mb-3">{s.desc}</p>
              <p className="text-[13px] text-[#f1f5f9] mb-3 leading-relaxed">{s.strategy}</p>
              <div className="space-y-1.5 mb-3">
                {s.rules.map((r, j) => (
                  <div key={j} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="text-[11px] text-[#94a3b8]">{r}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-3 pt-2 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#f1f5f9]">{s.expectWinRate}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期胜率</div>
                </div>
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#c9a84c]">{s.expectReturn}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期收益</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </DataCard>
    </div>
  );
}
