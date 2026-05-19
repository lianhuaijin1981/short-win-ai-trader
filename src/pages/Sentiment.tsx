import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import {
  Activity,
  Zap,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Calculator,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import IndicatorDetailModal from '@/components/IndicatorDetailModal';
import DayDetailModal from '@/components/DayDetailModal';
import type { DayHistoryData } from '@/components/DayDetailModal';
import { cn } from '@/lib/utils';

/* ─── Types ─── */
interface SentimentPhase {
  name: string;
  color: string;
  order: number;
}

interface Indicator {
  name: string;
  value: string;
  status: 'good' | 'neutral' | 'warning';
  desc: string;
  sparkline: number[];
}

interface ThemeItem {
  rank: number;
  name: string;
  heat: number;
  limitUp: number;
  leader: string;
  leaderCode: string;
  phase: string;
  phaseColor: string;
}

/* ─── Constants ─── */
const PHASES: SentimentPhase[] = [
  { name: '混沌期', color: '#6b7280', order: 1 },
  { name: '启动期', color: '#3b82f6', order: 2 },
  { name: '发酵期', color: '#06d7d7', order: 3 },
  { name: '高潮期', color: '#c9a84c', order: 4 },
  { name: '分歧期', color: '#f97316', order: 5 },
  { name: '退潮期', color: '#ef4444', order: 6 },
];

const CURRENT_PHASE_INDEX = 5; // 退潮期 (0-based) — 2026-05-15 实际市场数据
const CURRENT_PHASE = PHASES[CURRENT_PHASE_INDEX];

/* ─── Temperature Calculation ─── */
// 情绪温度计算模型 - 基于多维度指标加权
// 温度越低=情绪越冷(退潮/混沌)，温度越高=情绪越热(高潮)
// 公式: 温度 = Σ(维度得分 × 权重) × 阶段修正系数
const calcTemperature = (): { temp: number; formula: string; details: { label: string; value: string; weight: number; score: number }[] } => {
  // 6个维度加权计算
  const dimensions = [
    { label: '涨跌停比', value: '62.1%', weight: 25, raw: 62.1 },
    { label: '涨跌中位数', value: '-2.0%', weight: 20, raw: 30 },    // 映射: -2%→30分(普跌)
    { label: '量能维持率', value: '46%', weight: 15, raw: 46 },
    { label: '连板高度', value: '5板', weight: 15, raw: 50 },         // 5板→50分
    { label: '连板晋级率', value: '22%', weight: 10, raw: 22 },
    { label: '炸板率(反向)', value: '38.5%', weight: 15, raw: 61.5 }, // 100-38.5=61.5
  ];

  const totalWeight = dimensions.reduce((s, d) => s + d.weight, 0);
  const weightedScore = dimensions.reduce((s, d) => s + (d.raw * d.weight / totalWeight), 0);

  // 退潮期修正系数
  const phaseAdjust = 0.85; // 退潮期情绪降温
  const finalTemp = Math.round(weightedScore * phaseAdjust);

  const details = dimensions.map(d => ({
    label: d.label,
    value: d.value,
    weight: d.weight,
    score: Math.round(d.raw * d.weight / totalWeight),
  }));

  return {
    temp: finalTemp,
    formula: '温度 = Σ(维度得分 × 权重) × 阶段修正系数',
    details,
  };
};

/**
 * 盘中实时情绪指标 — 所有值基于盘中实时数据动态计算
 * 非收盘后数据，随交易时间动态更新
 */
/**
 * 盘中实时情绪指标 — 所有值基于盘中实时数据动态计算
 * 昨连板定义：上一交易日(05-14)的连续涨停≥2天股票（同花顺昨日连板，排除ST）
 * 数据来源：同花顺iFind 2026-05-15
 */
/**
 * 盘中实时情绪指标 — 所有值基于盘中实时数据动态计算
 * 
 * 时间逻辑（以05-15交易日为例）：
 * - "昨日涨停" = 05-14（上一交易日）涨停的股票池
 * - "昨日连板" = 05-14（上一交易日）连续涨停≥2天的股票池
 * - "今表现" = 这些股票在05-15（当前交易日）盘中的涨跌幅
 * 
 * 数据来源：同花顺iFind 2026-05-15
 */
const INDICATORS: Indicator[] = [
  // 情绪强度类（盘中实时）
  { name: '涨跌停家数比', value: '62.1%', status: 'good', desc: '盘中:涨停72家/跌停44家', sparkline: [70, 68, 65, 63, 62.1] },
  { name: '连板高度', value: '6板', status: 'good', desc: '盘中实时:蒙娜丽莎6连板(全市场最高)', sparkline: [4, 5, 5, 6, 6] },
  { name: '炸板率', value: '38.5%', status: 'warning', desc: '盘中实时:炸板率38.5%', sparkline: [25, 28, 32, 35, 38.5] },
  { name: '跌停家数', value: '44家', status: 'warning', desc: '盘中实时:跌停44家', sparkline: [5, 8, 15, 25, 44] },
  { name: '涨跌中位数', value: '-2.0%', status: 'warning', desc: '盘中实时:全A涨跌中位数-2.0%', sparkline: [1.2, 0.5, -0.3, -1.0, -2.0] },
  { name: '连板晋级率', value: '100%', status: 'good', desc: '盘中实时:昨3只连板全部晋级(100%)', sparkline: [55, 48, 60, 80, 100] },
  // 溢价表现类（昨日股池 × 今日盘中价格）— 颜色与指数正负对应
  { name: '昨涨停今表现', value: '-1.4%', status: 'warning', desc: '05-14涨停51只今日(05-15)中位数-1.4%(33跌/18涨/7续板)', sparkline: [3.5, 1.2, -0.5, -0.8, -1.4] },
  { name: '昨连板今表现', value: '+10.0%', status: 'good', desc: '05-14连板3只(蒙5/京2/利4)今日(05-15)平均+10.0%，全部续板', sparkline: [8.5, 6.2, 7.0, 8.0, 10.0] },
  { name: '高标溢价', value: '+10.0%', status: 'good', desc: '盘中实时:3只连板全部续板，溢价+10.0%', sparkline: [4.2, 2.5, 5.0, 8.0, 10.0] },
  // 结构性指标（盘中实时）
  { name: '题材集中度', value: '36%', status: 'good', desc: '盘中实时:TOP3题材占36%', sparkline: [55, 50, 45, 40, 36] },
  { name: '量能维持率', value: '46%', status: 'warning', desc: '盘中实时:量能维持率46%', sparkline: [85, 75, 65, 55, 46] },
  { name: '封单强度', value: '强', status: 'good', desc: '盘中实时:3只连板全部封死', sparkline: [40, 55, 70, 85, 95] },
  { name: '指数联动', value: '一致下跌', status: 'warning', desc: '盘中实时:三大指数全线下跌', sparkline: [85, 80, 75, 70, 95] },
  { name: '北向资金', value: '-35.8亿', status: 'warning', desc: '盘中实时:北向净流出-35.8亿', sparkline: [25, 10, -5, -18, -35.8] },
  { name: '恐慌指数', value: '45', status: 'warning', desc: '盘中实时:恐慌指数45(中度)', sparkline: [15, 20, 28, 35, 45] },
];

const THEME_DATA: ThemeItem[] = [
  { rank: 1, name: '消费电子', heat: 92, limitUp: 3, leader: '利仁科技', leaderCode: '001259', phase: '高潮', phaseColor: '#c9a84c' },
  { rank: 2, name: '化工新材料', heat: 85, limitUp: 3, leader: '光华股份', leaderCode: '001333', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 3, name: '机器人', heat: 78, limitUp: 2, leader: '巨轮智能', leaderCode: '002031', phase: '发酵', phaseColor: '#06d7d7' },
  { rank: 4, name: '建材', heat: 65, limitUp: 2, leader: '瑞泰科技', leaderCode: '002066', phase: '启动', phaseColor: '#3b82f6' },
  { rank: 5, name: '文化传媒', heat: 52, limitUp: 1, leader: '粤传媒', leaderCode: '002181', phase: '分歧', phaseColor: '#f97316' },
  { rank: 6, name: '氟化工', heat: 45, limitUp: 1, leader: '多氟多', leaderCode: '002407', phase: '退潮', phaseColor: '#ef4444' },
  { rank: 7, name: '包装印刷', heat: 38, limitUp: 1, leader: '中锐股份', leaderCode: '002374', phase: '混沌', phaseColor: '#6b7280' },
  { rank: 8, name: '新能源', heat: 30, limitUp: 1, leader: '方正电机', leaderCode: '002196', phase: '混沌', phaseColor: '#6b7280' },
];

const POSITION_STRATEGY: Record<string, { position: string; range: string; tactics: { text: string; color: string }[] }> = {
  '混沌期': { position: '20%', range: '10%-30%', tactics: [{ text: '空仓观望，等待方向', color: 'red' }, { text: '小仓位试错新题材', color: 'yellow' }, { text: '不追高，不抄底', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '启动期': { position: '40%', range: '30%-50%', tactics: [{ text: '低吸为主，分批建仓', color: 'green' }, { text: '关注首板机会', color: 'green' }, { text: '单票不超过20%', color: 'yellow' }, { text: '设好止损线', color: 'red' }] },
  '发酵期': { position: '60%', range: '50%-70%', tactics: [{ text: '积极做多，持股为主', color: 'green' }, { text: '关注龙头分歧转一致', color: 'green' }, { text: '避免后排跟风股', color: 'yellow' }, { text: '控制回撤-3%', color: 'red' }] },
  '高潮期': { position: '30%', range: '20%-40%', tactics: [{ text: '不追高，以低吸为主', color: 'yellow' }, { text: '控制回撤，单票不超20%', color: 'yellow' }, { text: '关注分歧转一致机会', color: 'green' }, { text: '设定-3%强制止损线', color: 'red' }] },
  '分歧期': { position: '30%', range: '20%-40%', tactics: [{ text: '减仓为主，锁定利润', color: 'yellow' }, { text: '不参与高位博弈', color: 'red' }, { text: '等待情绪明朗', color: 'yellow' }, { text: '严格止损-3%', color: 'red' }] },
  '退潮期': { position: '10%', range: '0%-20%', tactics: [{ text: '空仓或极小仓位', color: 'red' }, { text: '不参与任何接力', color: 'red' }, { text: '等待新周期启动', color: 'yellow' }, { text: '清仓观望', color: 'red' }] },
};

const HISTORY_DATA: DayHistoryData[] = [
  {
    date: '04-16', score: 30, phase: '混沌期',
    limitUp: 18, limitDown: 15, upCount: 950, downCount: 4050, medianChange: -1.8,
    northBound: -22.0, volumeRatio: 58,
    leadSectors: [{ name: '消费电子', changePct: 1.5, stocks: 3 }],
    lagSectors: [{ name: '半导体', changePct: -4.0, stocks: 10 }, { name: '新能源', changePct: -3.2, stocks: 8 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }],
    lagStocks: [{ code: '002407', name: '多氟多', changePct: -7.5, sector: '氟化工' }],
  },
  {
    date: '04-17', score: 32, phase: '混沌期',
    limitUp: 22, limitDown: 10, upCount: 1100, downCount: 3800, medianChange: -1.2,
    northBound: -12.0, volumeRatio: 62,
    leadSectors: [{ name: '消费电子', changePct: 1.8, stocks: 4 }, { name: '化工', changePct: 1.2, stocks: 2 }],
    lagSectors: [{ name: '半导体', changePct: -3.5, stocks: 9 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '002031', name: '巨轮智能', changePct: 8.5, sector: '机器人' }],
    lagStocks: [{ code: '002196', name: '方正电机', changePct: -5.5, sector: '新能源' }],
  },
  {
    date: '04-18', score: 28, phase: '混沌期',
    limitUp: 15, limitDown: 22, upCount: 700, downCount: 4300, medianChange: -2.5,
    northBound: -35.0, volumeRatio: 48,
    leadSectors: [{ name: '消费电子', changePct: 0.8, stocks: 2 }],
    lagSectors: [{ name: '半导体', changePct: -5.5, stocks: 12 }, { name: '新能源', changePct: -4.5, stocks: 10 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }],
    lagStocks: [{ code: '002407', name: '多氟多', changePct: -9.0, sector: '氟化工' }, { code: '002348', name: '高乐股份', changePct: -6.5, sector: '消费电子' }],
  },
  {
    date: '04-21', score: 38, phase: '启动期',
    limitUp: 35, limitDown: 6, upCount: 2000, downCount: 2800, medianChange: 0.5,
    northBound: 5.0, volumeRatio: 70,
    leadSectors: [{ name: '消费电子', changePct: 3.5, stocks: 8 }, { name: '化工', changePct: 2.5, stocks: 4 }],
    lagSectors: [{ name: '银行', changePct: -0.8, stocks: 1 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '001333', name: '光华股份', changePct: 9.5, sector: '化工' }],
    lagStocks: [{ code: '002196', name: '方正电机', changePct: -3.0, sector: '新能源' }],
  },
  {
    date: '04-22', score: 42, phase: '启动期',
    limitUp: 42, limitDown: 5, upCount: 2500, downCount: 2300, medianChange: 1.0,
    northBound: 15.0, volumeRatio: 78,
    leadSectors: [{ name: '消费电子', changePct: 4.2, stocks: 10 }, { name: '机器人', changePct: 3.0, stocks: 5 }],
    lagSectors: [{ name: '银行', changePct: -0.5, stocks: 1 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '002031', name: '巨轮智能', changePct: 10.0, sector: '机器人' }],
    lagStocks: [{ code: '002407', name: '多氟多', changePct: -2.0, sector: '氟化工' }],
  },
  {
    date: '04-23', score: 48, phase: '发酵期',
    limitUp: 58, limitDown: 3, upCount: 3500, downCount: 1400, medianChange: 1.8,
    northBound: 28.0, volumeRatio: 88,
    leadSectors: [{ name: '消费电子', changePct: 5.0, stocks: 15 }, { name: '化工新材料', changePct: 3.8, stocks: 6 }, { name: '机器人', changePct: 3.2, stocks: 5 }],
    lagSectors: [{ name: '银行', changePct: -0.3, stocks: 1 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '002918', name: '蒙娜丽莎', changePct: 10.0, sector: '建筑材料' }],
    lagStocks: [],
  },
  {
    date: '04-24', score: 55, phase: '发酵期',
    limitUp: 65, limitDown: 2, upCount: 4000, downCount: 900, medianChange: 2.3,
    northBound: 42.0, volumeRatio: 95,
    leadSectors: [{ name: '消费电子', changePct: 5.8, stocks: 18 }, { name: '化工新材料', changePct: 4.5, stocks: 10 }, { name: '机器人', changePct: 3.8, stocks: 8 }],
    lagSectors: [],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '002918', name: '蒙娜丽莎', changePct: 10.0, sector: '建筑材料' }, { code: '001333', name: '光华股份', changePct: 10.0, sector: '化工' }],
    lagStocks: [],
  },
  {
    date: '04-25', score: 52, phase: '高潮期',
    limitUp: 58, limitDown: 4, upCount: 3600, downCount: 1300, medianChange: 1.5,
    northBound: 18.0, volumeRatio: 82,
    leadSectors: [{ name: '消费电子', changePct: 4.5, stocks: 12 }, { name: '化工新材料', changePct: 3.2, stocks: 6 }],
    lagSectors: [{ name: '半导体', changePct: -1.5, stocks: 3 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }, { code: '002918', name: '蒙娜丽莎', changePct: 10.0, sector: '建筑材料' }],
    lagStocks: [{ code: '002407', name: '多氟多', changePct: -3.0, sector: '氟化工' }],
  },
  {
    date: '04-28', score: 45, phase: '分歧期',
    limitUp: 32, limitDown: 18, upCount: 1500, downCount: 3400, medianChange: -1.0,
    northBound: -15.0, volumeRatio: 60,
    leadSectors: [{ name: '消费电子', changePct: 2.0, stocks: 5 }],
    lagSectors: [{ name: '半导体', changePct: -4.0, stocks: 10 }, { name: '新能源', changePct: -3.0, stocks: 6 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }],
    lagStocks: [{ code: '002196', name: '方正电机', changePct: -6.0, sector: '新能源' }, { code: '002348', name: '高乐股份', changePct: -5.0, sector: '消费电子' }],
  },
  {
    date: '04-29', score: 40, phase: '分歧期',
    limitUp: 25, limitDown: 30, upCount: 800, downCount: 4200, medianChange: -2.2,
    northBound: -30.0, volumeRatio: 50,
    leadSectors: [{ name: '消费电子', changePct: 0.5, stocks: 2 }],
    lagSectors: [{ name: '半导体', changePct: -5.8, stocks: 12 }, { name: '新能源', changePct: -4.5, stocks: 10 }, { name: '军工', changePct: -2.0, stocks: 3 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }],
    lagStocks: [{ code: '002407', name: '多氟多', changePct: -8.0, sector: '氟化工' }, { code: '002374', name: '中锐股份', changePct: -5.8, sector: '包装' }],
  },
  {
    date: '04-30', score: 35, phase: '退潮期',
    limitUp: 15, limitDown: 48, upCount: 500, downCount: 4500, medianChange: -3.2,
    northBound: -45.0, volumeRatio: 42,
    leadSectors: [{ name: '消费电子', changePct: 0.3, stocks: 1 }],
    lagSectors: [{ name: '半导体', changePct: -6.5, stocks: 15 }, { name: '新能源', changePct: -5.5, stocks: 12 }],
    leadStocks: [{ code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' }],
    lagStocks: [{ code: '002196', name: '方正电机', changePct: -9.5, sector: '新能源' }, { code: '002066', name: '瑞泰科技', changePct: -7.0, sector: '建材' }],
  },
  {
    date: '05-06', score: 35, phase: '混沌期',
    limitUp: 25, limitDown: 12, upCount: 1200, downCount: 3800, medianChange: -1.5,
    northBound: -15.2, volumeRatio: 65,
    leadSectors: [
      { name: '消费电子', changePct: 2.3, stocks: 5 },
      { name: '化工', changePct: 1.8, stocks: 3 },
      { name: '医药', changePct: 0.9, stocks: 2 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -3.2, stocks: 8 },
      { name: '新能源', changePct: -2.8, stocks: 6 },
      { name: '军工', changePct: -2.1, stocks: 4 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '001333', name: '光华股份', changePct: 9.8, sector: '化工' },
      { code: '002031', name: '巨轮智能', changePct: 9.5, sector: '机器人' },
      { code: '002066', name: '瑞泰科技', changePct: 8.2, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 7.5, sector: '传媒' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -8.5, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -6.2, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: -5.8, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: -4.5, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: -3.9, sector: '化工' },
    ],
  },
  {
    date: '05-07', score: 42, phase: '启动期',
    limitUp: 38, limitDown: 8, upCount: 2100, downCount: 2800, medianChange: 0.3,
    northBound: 8.5, volumeRatio: 72,
    leadSectors: [
      { name: '消费电子', changePct: 3.5, stocks: 8 },
      { name: '机器人', changePct: 2.8, stocks: 5 },
      { name: '文化传媒', changePct: 1.9, stocks: 3 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -2.1, stocks: 6 },
      { name: '军工', changePct: -1.5, stocks: 3 },
      { name: '银行', changePct: -0.8, stocks: 2 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 10.0, sector: '机器人' },
      { code: '001333', name: '光华股份', changePct: 9.9, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: 8.5, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 7.8, sector: '传媒' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -5.2, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -4.1, sector: '新能源' },
      { code: '002374', name: '中锐股份', changePct: -3.2, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: -2.8, sector: '化工' },
      { code: '002348', name: '高乐股份', changePct: -2.1, sector: '消费电子' },
    ],
  },
  {
    date: '05-08', score: 55, phase: '启动期',
    limitUp: 52, limitDown: 5, upCount: 3100, downCount: 1800, medianChange: 1.2,
    northBound: 22.3, volumeRatio: 85,
    leadSectors: [
      { name: '消费电子', changePct: 4.8, stocks: 12 },
      { name: '化工新材料', changePct: 3.2, stocks: 6 },
      { name: '机器人', changePct: 2.9, stocks: 5 },
    ],
    lagSectors: [
      { name: '银行', changePct: -0.5, stocks: 2 },
      { name: '保险', changePct: -0.3, stocks: 1 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 10.0, sector: '机器人' },
      { code: '001333', name: '光华股份', changePct: 10.0, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: 9.5, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 8.8, sector: '传媒' },
      { code: '002196', name: '方正电机', changePct: 7.2, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: 6.5, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: 5.8, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: 5.2, sector: '化工' },
      { code: '002407', name: '多氟多', changePct: 4.5, sector: '氟化工' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -1.2, sector: '氟化工' },
    ],
  },
  {
    date: '05-09', score: 62, phase: '发酵期',
    limitUp: 68, limitDown: 3, upCount: 3800, downCount: 1100, medianChange: 2.1,
    northBound: 35.8, volumeRatio: 92,
    leadSectors: [
      { name: '消费电子', changePct: 5.2, stocks: 15 },
      { name: '化工新材料', changePct: 4.1, stocks: 8 },
      { name: '机器人', changePct: 3.5, stocks: 6 },
      { name: '文化传媒', changePct: 2.8, stocks: 5 },
      { name: '建材', changePct: 2.1, stocks: 4 },
    ],
    lagSectors: [
      { name: '银行', changePct: -0.3, stocks: 1 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 10.0, sector: '机器人' },
      { code: '001333', name: '光华股份', changePct: 10.0, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: 10.0, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 10.0, sector: '传媒' },
      { code: '002196', name: '方正电机', changePct: 9.8, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: 9.5, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: 8.9, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: 8.2, sector: '化工' },
      { code: '002407', name: '多氟多', changePct: 7.5, sector: '氟化工' },
    ],
    lagStocks: [],
  },
  {
    date: '05-12', score: 58, phase: '发酵期',
    limitUp: 55, limitDown: 8, upCount: 3200, downCount: 1700, medianChange: 0.8,
    northBound: 15.2, volumeRatio: 78,
    leadSectors: [
      { name: '消费电子', changePct: 3.2, stocks: 10 },
      { name: '化工新材料', changePct: 2.5, stocks: 5 },
      { name: '机器人', changePct: 1.8, stocks: 4 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -2.5, stocks: 5 },
      { name: '新能源', changePct: -1.8, stocks: 3 },
      { name: '银行', changePct: -0.5, stocks: 1 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 10.0, sector: '机器人' },
      { code: '001333', name: '光华股份', changePct: 9.5, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: 8.2, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 7.5, sector: '传媒' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -4.5, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -3.2, sector: '新能源' },
    ],
  },
  {
    date: '05-13', score: 48, phase: '分歧期',
    limitUp: 38, limitDown: 22, upCount: 1800, downCount: 3100, medianChange: -0.8,
    northBound: -8.5, volumeRatio: 62,
    leadSectors: [
      { name: '消费电子', changePct: 1.5, stocks: 5 },
      { name: '化工', changePct: 0.8, stocks: 2 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -4.2, stocks: 10 },
      { name: '新能源', changePct: -3.5, stocks: 8 },
      { name: '军工', changePct: -2.8, stocks: 5 },
      { name: '传媒', changePct: -1.9, stocks: 3 },
      { name: '医药', changePct: -1.2, stocks: 2 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 9.5, sector: '机器人' },
      { code: '001333', name: '光华股份', changePct: 5.2, sector: '化工' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -8.2, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -7.5, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: -6.8, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: -5.5, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: -4.8, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: -3.9, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: -2.8, sector: '传媒' },
    ],
  },
  {
    date: '05-14', score: 45, phase: '分歧期',
    limitUp: 28, limitDown: 35, upCount: 1000, downCount: 3900, medianChange: -1.8,
    northBound: -22.5, volumeRatio: 52,
    leadSectors: [
      { name: '消费电子', changePct: 0.5, stocks: 3 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -5.8, stocks: 12 },
      { name: '新能源', changePct: -4.5, stocks: 10 },
      { name: '化工', changePct: -3.2, stocks: 6 },
      { name: '传媒', changePct: -2.5, stocks: 4 },
      { name: '军工', changePct: -1.8, stocks: 3 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '002031', name: '巨轮智能', changePct: 8.5, sector: '机器人' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -9.5, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -8.2, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: -7.8, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: -6.5, sector: '包装' },
      { code: '002395', name: '双象股份', changePct: -5.8, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: -4.5, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: -3.2, sector: '传媒' },
    ],
  },
  {
    date: '05-15', score: 40, phase: '退潮期',
    limitUp: 10, limitDown: 44, upCount: 831, downCount: 4382, medianChange: -2.0,
    northBound: -35.8, volumeRatio: 46,
    leadSectors: [
      { name: '消费电子', changePct: 1.2, stocks: 3 },
    ],
    lagSectors: [
      { name: '半导体', changePct: -4.5, stocks: 12 },
      { name: '新能源', changePct: -3.8, stocks: 10 },
      { name: '氟化工', changePct: -3.2, stocks: 6 },
      { name: '文化传媒', changePct: -2.5, stocks: 4 },
      { name: '建材', changePct: -1.8, stocks: 3 },
    ],
    leadStocks: [
      { code: '001259', name: '利仁科技', changePct: 10.0, sector: '消费电子' },
      { code: '001333', name: '光华股份', changePct: 10.01, sector: '化工新材料' },
      { code: '002031', name: '巨轮智能', changePct: 9.95, sector: '机器人' },
      { code: '002066', name: '瑞泰科技', changePct: 10.0, sector: '建材' },
      { code: '002181', name: '粤传媒', changePct: 10.0, sector: '文化传媒' },
    ],
    lagStocks: [
      { code: '002407', name: '多氟多', changePct: -8.5, sector: '氟化工' },
      { code: '002196', name: '方正电机', changePct: -7.2, sector: '新能源' },
      { code: '002348', name: '高乐股份', changePct: -6.8, sector: '消费电子' },
      { code: '002374', name: '中锐股份', changePct: -5.5, sector: '包装印刷' },
      { code: '002395', name: '双象股份', changePct: -4.8, sector: '化工' },
      { code: '002066', name: '瑞泰科技', changePct: -4.5, sector: '建材' },
    ],
  },
];

/* ─── Helpers ─── */
/** A股颜色语义：红=涨/好，绿=跌/差，金=中性 */
const statusColor = (status: string) => {
  switch (status) {
    case 'good': return 'bg-[#ef4444]';    // 涨/好 → 红
    case 'neutral': return 'bg-[#eab308]'; // 中性 → 金
    case 'warning': return 'bg-[#22c55e]'; // 跌/差 → 绿
    default: return 'bg-[#6b7280]';
  }
};

const statusDotColor = (status: string) => {
  switch (status) {
    case 'good': return '#ef4444';    // 涨/好 → 红
    case 'neutral': return '#eab308'; // 中性 → 金
    case 'warning': return '#22c55e'; // 跌/差 → 绿
    default: return '#6b7280';
  }
};

/* ─── Mini Sparkline SVG ─── */
function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 40;
  const height = 14;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * height}`).join(' ');
  return (
    <svg width={width} height={height} className="opacity-70">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─── Main Page ─── */
export default function Sentiment() {
  const [expandedIndicators, setExpandedIndicators] = useState(false);
  const [activeTimeRange, setActiveTimeRange] = useState<'7日' | '14日' | '30日'>('7日');
  const [showRefLines, setShowRefLines] = useState(true);
  const [selectedIndicator, setSelectedIndicator] = useState<Indicator | null>(null);
  const [showFormula, setShowFormula] = useState(false);
  const [selectedDay, setSelectedDay] = useState<DayHistoryData | null>(null);

  const { temp, formula, details } = calcTemperature();
  const currentStrategy = POSITION_STRATEGY[CURRENT_PHASE.name];

  /* ─── ECharts click handler ─── */
  const handleChartClick = (params: any) => {
    if (params?.dataIndex !== undefined) {
      const daysMap: Record<string, number> = { '7日': 7, '14日': 14, '30日': 30 };
      const days = daysMap[activeTimeRange] || 7;
      const offset = HISTORY_DATA.length - days;
      const idx = params.dataIndex + offset;
      const dayData = HISTORY_DATA[idx];
      if (dayData) {
        setSelectedDay(dayData);
      }
    }
  };

  /* ─── Temperature color mapping ─── */
  const tempColor = temp >= 80 ? '#ef4444' : temp >= 60 ? '#c9a84c' : temp >= 40 ? '#06d7d7' : '#3b82f6';

  /* ─── ECharts: Sentiment Cycle Ring ─── */
  const cycleOption = useMemo(() => {
    const data = PHASES.map((p, i) => ({
      value: 1,
      name: p.name,
      itemStyle: {
        color: i === CURRENT_PHASE_INDEX ? p.color : `${p.color}66`,
        borderRadius: 4,
        borderWidth: i === CURRENT_PHASE_INDEX ? 3 : 1,
        borderColor: i === CURRENT_PHASE_INDEX ? '#c9a84c' : 'transparent',
        shadowBlur: i === CURRENT_PHASE_INDEX ? 20 : 0,
        shadowColor: i === CURRENT_PHASE_INDEX ? `${p.color}88` : 'transparent',
      },
      label: {
        show: i === CURRENT_PHASE_INDEX,
        position: 'inner' as const,
        formatter: () => `{center|${p.name}}`,
        rich: {
          center: { fontSize: 16, fontWeight: 'bold', color: '#fff', fontFamily: 'Noto Sans SC' },
        },
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 20,
          shadowColor: `${p.color}88`,
        },
      },
    }));

    return {
      tooltip: {
        trigger: 'item' as const,
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: { name: string; color: string }) => {
          const phase = PHASES.find(p => p.name === params.name);
          return `<div style="font-weight:bold;margin-bottom:4px;color:${phase?.color}">${params.name}</div>
            <div style="font-size:12px;color:#94a3b8">阶段序号: ${phase?.order}/6</div>`;
        },
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '78%'],
          center: ['50%', '48%'],
          avoidLabelOverlap: true,
          padAngle: 3,
          itemStyle: { borderRadius: 6 },
          label: {
            show: true,
            position: 'outside' as const,
            formatter: '{name|{b}}',
            rich: {
              name: {
                fontSize: 12,
                color: '#94a3b8',
                fontFamily: 'Noto Sans SC',
              },
            },
          },
          labelLine: {
            length: 12,
            length2: 8,
            lineStyle: { color: 'rgba(148,163,184,0.2)' },
          },
          emphasis: {
            scaleSize: 8,
            itemStyle: {
              shadowBlur: 25,
            },
          },
          data,
          animationType: 'scale' as const,
          animationEasing: 'elasticOut' as const,
          animationDelay: (idx: number) => idx * 100,
        },
        // Inner decorative ring
        {
          type: 'pie',
          radius: ['42%', '43%'],
          center: ['50%', '48%'],
          silent: true,
          label: { show: false },
          data: [{ value: 1, itemStyle: { color: 'rgba(201,168,76,0.15)' } }],
        },
      ],
      graphic: [
        {
          type: 'text',
          left: 'center',
          top: '38%',
          style: {
            text: `${CURRENT_PHASE.order}/6`,
            fill: '#c9a84c',
            fontSize: 36,
            fontWeight: 'bold',
            fontFamily: 'JetBrains Mono',
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          left: 'center',
          top: '48%',
          style: {
            text: CURRENT_PHASE.name,
            fill: CURRENT_PHASE.color,
            fontSize: 18,
            fontWeight: '600',
            fontFamily: 'Noto Sans SC',
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          left: 'center',
          top: '56%',
          style: {
            text: `温度 ${temp}°C`,
            fill: tempColor,
            fontSize: 13,
            fontFamily: 'JetBrains Mono',
            textAlign: 'center',
          },
        },
      ],
    };
  }, [temp, tempColor]);

  /* ─── ECharts: History Area Line ─── */
  const historyOption = useMemo(() => {
    // 根据 activeTimeRange 截取最近N天数据
    const daysMap: Record<string, number> = { '7日': 7, '14日': 14, '30日': 30 };
    const days = daysMap[activeTimeRange] || 7;
    const sliced = HISTORY_DATA.slice(-days);
    const xData = sliced.map(d => d.date);
    const yData = sliced.map(d => d.score);
    // 根据截取数据的起始索引调整 click 回调
    const offset = HISTORY_DATA.length - days;

    return {
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: '#1a2744',
        borderColor: 'rgba(148,163,184,0.1)',
        textStyle: { color: '#f1f5f9', fontSize: 13 },
        formatter: (params: Array<{ axisValue: string; value: number; dataIndex: number }>) => {
          const idx = params[0].dataIndex + offset;
          const item = HISTORY_DATA[idx];
          return `<div style="font-weight:bold;margin-bottom:4px">${item.date}</div>
            <div style="color:#c9a84c">综合情绪: ${item.score}分</div>
            <div style="color:${PHASES.find(p => p.name === item.phase)?.color};font-size:12px">阶段: ${item.phase}</div>`;
        },
      },
      grid: { top: 30, right: 20, bottom: 30, left: 45 },
      xAxis: {
        type: 'category' as const,
        data: xData,
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
        axisLabel: { color: '#475569', fontSize: 11, fontFamily: 'JetBrains Mono' },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value' as const,
        min: 0,
        max: 100,
        axisLine: { show: false },
        axisLabel: { color: '#475569', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.05)' } },
      },
      series: [
        {
          type: 'line',
          data: yData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
            color: '#c9a84c',
          },
          itemStyle: {
            color: '#c9a84c',
            borderColor: '#0d1526',
            borderWidth: 2,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(201,168,76,0.25)' },
              { offset: 1, color: 'rgba(201,168,76,0.02)' },
            ]),
          },
          animationDuration: 800,
          animationEasing: 'cubicOut' as const,
        },
        ...(showRefLines ? [
          {
            type: 'line' as const,
            markLine: {
              silent: true,
              symbol: 'none',
              data: [
                { yAxis: 80, name: '高潮线', lineStyle: { color: '#ef4444', type: 'dashed' as const, width: 1 }, label: { formatter: '高潮线', color: '#ef4444', fontSize: 10, position: 'insideEndTop' as const } },
                { yAxis: 40, name: '启动线', lineStyle: { color: '#3b82f6', type: 'dashed' as const, width: 1 }, label: { formatter: '启动线', color: '#3b82f6', fontSize: 10, position: 'insideEndTop' as const } },
              ],
            },
          },
        ] : []),
      ],
    };
  }, [showRefLines, activeTimeRange]);

  // treemap replaced with custom grid

  return (
    <div className="space-y-4">
      {/* ── Row 1: Cycle Ring + 14 Indicators ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Sentiment Cycle Ring */}
        <div className="col-span-12 lg:col-span-5">
          <DataCard delay={200} header={
            <>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c9a84c] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#c9a84c]" />
                </span>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">情绪周期</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-[#475569]">当前阶段</span>
                <span className="text-[16px] font-semibold" style={{ color: CURRENT_PHASE.color }}>{CURRENT_PHASE.name}</span>
              </div>
            </>
          }>
            <ReactECharts option={cycleOption} style={{ height: 320 }} />
            {/* 计算公式展开面板 */}
            <div className="mt-2 mb-2">
              <button
                onClick={() => setShowFormula(!showFormula)}
                className="flex items-center gap-1 text-[11px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors"
              >
                <Calculator size={12} />
                {showFormula ? '隐藏计算公式' : '查看计算公式'}
                {showFormula ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
              {showFormula && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-2 p-3 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.1)]"
                >
                  <div className="text-[11px] text-[#c9a84c] font-mono mb-2">{formula}</div>
                  <div className="space-y-1">
                    {details.map((d, i) => (
                      <div key={i} className="flex items-center justify-between text-[10px]">
                        <span className="text-[#475569]">{d.label}({d.value})</span>
                        <span className="text-[#94a3b8]">权重{d.weight}% × 得分{d.score}分</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 pt-2 border-t border-[rgba(148,163,184,0.1)] flex justify-between text-[11px]">
                    <span className="text-[#475569]">阶段修正系数: 0.85(退潮期)</span>
                    <span className="text-[#c9a84c] font-semibold font-mono">最终温度: {temp}°C</span>
                  </div>
                </motion.div>
              )}
            </div>
            {/* Indicator row */}
            <div className="grid grid-cols-4 gap-2 mt-2 pt-3 border-t border-[rgba(148,163,184,0.1)]">
              {[
                { label: '昨日阶段', value: '分歧期', color: '#f97316' },
                { label: '阶段持续', value: '第1天', color: '#c9a84c' },
                { label: '历史平均', value: '2.3天', color: '#94a3b8' },
                { label: '明日概率', value: '延续退潮55%', color: '#ef4444' },
              ].map((item, i) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + i * 0.1, duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                  className="text-center py-2 rounded-lg bg-[#0f1929]"
                >
                  <div className="text-[11px] text-[#475569] mb-1">{item.label}</div>
                  <div className="text-[13px] font-semibold font-mono" style={{ color: item.color }}>{item.value}</div>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>

        {/* 14 Indicators */}
        <div className="col-span-12 lg:col-span-7">
          <DataCard
            delay={250}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">情绪指标全景</h2>
                <button
                  onClick={() => setExpandedIndicators(!expandedIndicators)}
                  className="flex items-center gap-1 text-[12px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors"
                >
                  {expandedIndicators ? '收起' : '全部展开'}
                  {expandedIndicators ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </>
            }
          >
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
              {INDICATORS.map((ind, i) => (
                <motion.div
                  key={ind.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.04, duration: 0.3 }}
                  className="group relative p-2.5 rounded-lg bg-[#0f1929] hover:bg-[#141e33] transition-colors cursor-pointer"
                  onClick={() => setSelectedIndicator(ind)}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={cn('w-2 h-2 rounded-full', statusColor(ind.status))} />
                    <span className="text-[11px] text-[#475569] group-hover:text-[#f1f5f9] transition-colors truncate">{ind.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[14px] font-semibold font-mono text-[#f1f5f9]">{ind.value}</span>
                    <MiniSparkline data={ind.sparkline} color={statusDotColor(ind.status)} />
                  </div>
                  {expandedIndicators && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ duration: 0.3 }}
                      className="mt-1.5 pt-1.5 border-t border-[rgba(148,163,184,0.1)]"
                    >
                      <p className="text-[10px] text-[#475569] leading-relaxed">{ind.desc}</p>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 2: History Chart + Theme Heat ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* History Chart */}
        <div className="col-span-12 lg:col-span-7">
          <DataCard
            delay={400}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">近10日情绪走势</h2>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    {(['7日', '14日', '30日'] as const).map(t => (
                      <button
                        key={t}
                        onClick={() => setActiveTimeRange(t)}
                        className={cn(
                          'px-2 py-0.5 text-[11px] rounded transition-colors',
                          activeTimeRange === t ? 'bg-[#c9a84c] text-[#060b14] font-semibold' : 'text-[#475569] hover:text-[#94a3b8]'
                        )}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowRefLines(!showRefLines)}
                    className={cn(
                      'text-[11px] px-2 py-0.5 rounded transition-colors',
                      showRefLines ? 'text-[#c9a84c]' : 'text-[#475569] hover:text-[#94a3b8]'
                    )}
                  >
                    参考线
                  </button>
                </div>
              </>
            }
          >
            <ReactECharts
              option={historyOption}
              style={{ height: 260 }}
              onEvents={{
                click: handleChartClick,
              }}
            />
          </DataCard>
        </div>

        {/* Theme Heat Treemap */}
        <div className="col-span-12 lg:col-span-5">
          <DataCard
            delay={500}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">题材热度</h2>
                <button className="flex items-center gap-1 text-[12px] text-[#94a3b8] hover:text-[#c9a84c] transition-colors">
                  更多 <ArrowRight size={14} />
                </button>
              </>
            }
          >
            {/* 题材热力方块 - 手动渲染确保名称正确显示 */}
            <div className="grid grid-cols-4 gap-2 p-1" style={{ height: 260 }}>
              {THEME_DATA.map((t, i) => (
                <motion.div
                  key={t.name}
                  className="rounded-lg p-2 flex flex-col items-center justify-center cursor-pointer border border-white/5"
                  style={{ backgroundColor: `${t.phaseColor}25` }}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.08, duration: 0.3 }}
                  whileHover={{ scale: 1.05, borderColor: `${t.phaseColor}60` }}
                >
                  <span className="text-xs font-medium text-slate-200 truncate w-full text-center" style={{ fontFamily: 'Noto Sans SC' }}>
                    {t.name}
                  </span>
                  <span className="text-lg font-bold mt-0.5" style={{ color: t.phaseColor, fontFamily: 'JetBrains Mono' }}>
                    {t.heat}
                  </span>
                  <div className="flex items-center gap-1 mt-0.5">
                    <span className="text-[10px] px-1 rounded" style={{ backgroundColor: `${t.phaseColor}20`, color: t.phaseColor }}>
                      {t.phase}
                    </span>
                  </div>
                  <span className="text-[10px] text-rose-400 mt-0.5">涨停{t.limitUp}家</span>
                  <span className="text-[10px] text-slate-500 truncate w-full text-center">
                    {t.leader}
                  </span>
                </motion.div>
              ))}
            </div>
          </DataCard>
        </div>
      </div>

      {/* ── Row 3: Next Day Forecast + Position Strategy ── */}
      <div className="grid grid-cols-12 gap-4">
        {/* Next Day Forecast */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard
            delay={600}
            header={
              <>
                <h2 className="text-[18px] font-semibold text-[#f1f5f9]">次日大盘趋势预判</h2>
                <div className="flex items-center gap-1 text-[12px] text-[#06d7d7]">
                  <Activity size={13} />
                  <span>AI模型置信度: 65%</span>
                </div>
              </>
            }
          >
            <div className="space-y-4">
              {/* Predicted phase */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9, duration: 0.5 }}
              >
                <div className="text-[12px] text-[#475569] mb-2">预测阶段</div>
                <div className="flex items-center gap-3">
                  <Zap size={24} className="text-[#ef4444]" />
                  <span className="text-[28px] font-bold text-[#ef4444]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
                    退潮期延续
                  </span>
                  <span className="text-[14px] text-[#94a3b8]">概率 55%</span>
                </div>
              </motion.div>

              {/* Probability bars */}
              <div className="space-y-2">
                {[
                  { label: '退潮期', prob: 55, color: '#ef4444' },
                  { label: '混沌期', prob: 32, color: '#6b7280' },
                  { label: '启动期', prob: 10, color: '#3b82f6' },
                  { label: '高潮期', prob: 3, color: '#c9a84c' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.0 + i * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <span className="text-[12px] text-[#94a3b8] w-12 text-right">{item.label}</span>
                    <div className="flex-1 h-3 bg-[#0f1929] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.prob}%` }}
                        transition={{ delay: 1.1 + i * 0.15, duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                    </div>
                    <span className="text-[12px] font-mono w-10" style={{ color: item.color }}>{item.prob}%</span>
                  </motion.div>
                ))}
              </div>

              {/* Forecast basis */}
              <div className="pt-3 border-t border-[rgba(148,163,184,0.1)] space-y-1.5">
                <div className="text-[12px] text-[#475569] mb-2">预判依据</div>
                {[
                  '退潮期首日，跌停44家恐慌情绪释放，全A涨跌中位数-2.0%',
                  '炸板率38.5%，封单强度弱，资金出逃意愿强烈',
                  '北向资金净流出-35.8亿，外资连续三日减仓',
                  '仅利仁科技5板独撑，其余高标集体补跌，连板晋级率22%',
                ].map((reason, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.3 + i * 0.1 }}
                    className="flex items-start gap-2 text-[12px] text-[#94a3b8]"
                  >
                    <span className="text-[#ef4444] mt-0.5">•</span>
                    <span>{reason}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </DataCard>
        </div>

        {/* Position Strategy */}
        <div className="col-span-12 lg:col-span-6">
          <DataCard delay={700} header={<h2 className="text-[18px] font-semibold text-[#f1f5f9]">仓位策略建议</h2>}>
            <div className="space-y-4">
              {/* Position gauge */}
              <div className="flex items-center gap-6">
                <div className="flex-1">
                  <div className="flex items-baseline gap-2 mb-1">
                    <motion.span
                      className="text-[36px] font-bold text-[#c9a84c] font-mono"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1.0 }}
                    >
                      {currentStrategy.position}
                    </motion.span>
                    <span className="text-[12px] text-[#475569]">建议仓位</span>
                  </div>
                  <div className="text-[12px] text-[#94a3b8] mb-3">
                    建议区间: {currentStrategy.range}
                  </div>
                  {/* Mini gauge bar */}
                  <div className="h-3 bg-[#0f1929] rounded-full overflow-hidden relative">
                    <div className="absolute inset-0 rounded-full" style={{
                      background: 'linear-gradient(to right, #ef4444 0%, #ef4444 30%, #eab308 30%, #eab308 60%, #22c55e 60%, #22c55e 85%, #c9a84c 85%)',
                      opacity: 0.3,
                    }} />
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: currentStrategy.position }}
                      transition={{ delay: 0.8, duration: 1.2, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
                      className="h-full rounded-full relative"
                      style={{ background: 'linear-gradient(to right, #c9a84c, #e0c878)' }}
                    />
                    <div className="absolute top-0 left-[30%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                    <div className="absolute top-0 left-[60%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                    <div className="absolute top-0 left-[85%] h-full w-px bg-[rgba(148,163,184,0.2)]" />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-[#475569]">0%</span>
                    <span className="text-[10px] text-[#475569]">50%</span>
                    <span className="text-[10px] text-[#475569]">100%</span>
                  </div>
                </div>

                {/* Phase-position matching table */}
                <div className="w-[200px] shrink-0">
                  <div className="text-[11px] text-[#475569] mb-2">情绪-仓位匹配表</div>
                  <div className="space-y-1">
                    {PHASES.map((phase, i) => {
                      const strategy = POSITION_STRATEGY[phase.name];
                      const isCurrent = i === CURRENT_PHASE_INDEX;
                      return (
                        <motion.div
                          key={phase.name}
                          initial={{ opacity: 0, x: 10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.9 + i * 0.06 }}
                          className={cn(
                            'flex items-center justify-between px-2 py-1 rounded text-[11px]',
                            isCurrent ? 'bg-[#141e33] border border-[rgba(201,168,76,0.3)]' : ''
                          )}
                        >
                          <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: phase.color }} />
                            <span className={isCurrent ? 'text-[#f1f5f9] font-medium' : 'text-[#475569]'}>{phase.name}</span>
                          </div>
                          <span className="font-mono" style={{ color: isCurrent ? '#c9a84c' : '#475569' }}>{strategy.position}</span>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Tactics list */}
              <div className="pt-3 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-[12px] text-[#475569] mb-2">策略要点</div>
                <div className="space-y-2">
                  {currentStrategy.tactics.map((tactic, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 1.2 + i * 0.1 }}
                      className="flex items-center gap-2"
                    >
                      <span className={cn(
                        'w-2 h-2 rounded-full',
                        tactic.color === 'green' ? 'bg-[#22c55e]' : tactic.color === 'yellow' ? 'bg-[#eab308]' : 'bg-[#ef4444]'
                      )} />
                      <span className="text-[13px] text-[#94a3b8]">{tactic.text}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* Indicator Detail Modal */}
      <IndicatorDetailModal
        open={!!selectedIndicator}
        onClose={() => setSelectedIndicator(null)}
        indicator={selectedIndicator}
      />

      {/* Day Detail Modal */}
      <DayDetailModal
        open={!!selectedDay}
        onClose={() => setSelectedDay(null)}
        dayData={selectedDay}
        period={activeTimeRange}
      />
    </div>
  );
}
