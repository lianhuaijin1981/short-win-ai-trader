import { useMemo, useState, useCallback } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ReactECharts from 'echarts-for-react';
import {
  X, BarChart3, Clock, Activity, ChevronUp, ChevronDown, Minus
} from 'lucide-react';
import { REAL_LIMIT_UP_STOCKS, INTRADAY_TICKS, MARKET_TOP5_GAINERS, MARKET_TOP3_BOARDS, type IntradayTick } from '@/data/realData';

/* ================================================================
   Types
   ================================================================ */

interface StockDetailModalProps {
  open: boolean;
  onClose: () => void;
  stock: {
    code: string;
    name: string;
    price: number;
    change: number;
    position?: string;
    sectorStatus?: string;
  } | null;
}

interface KlinePoint {
  date: string;
  open: number;
  close: number;
  low: number;
  high: number;
}

interface TradeRecord {
  time: string;
  price: number;
  volume: number;
  direction: 'up' | 'down' | 'neutral'; // up=买入, down=卖出, neutral=平价
}

/* ================================================================
   Color constants (同花顺深色主题)
   ================================================================ */

const BG = '#0d1526';
const BG_CARD = '#0f1929';
const BORDER = 'rgba(148,163,184,0.1)';
const TEXT_MAIN = '#f1f5f9';
const TEXT_SECOND = '#94a3b8';
const TEXT_MUTED = '#475569';
const RED = '#ef4444';   // 涨/买/阳
const GREEN = '#22c55e'; // 跌/卖/阴
const YELLOW = '#eab308'; // 均价线/MA10

/** 均线配色 */
const MA_COLORS: Record<string, string> = {
  MA5:   '#ffffff',
  MA10:  '#eab308',
  MA20:  '#a855f7',
  MA30:  '#3b82f6',
  MA60:  '#f97316',
  MA120: '#ec4899',
  MA300: '#6b7280',
};

/* ================================================================
   Helpers — Data
   ================================================================ */

function getStockKline(code: string): KlinePoint[] {
  // 优先从涨停股池中查找
  const fromLimitUp = REAL_LIMIT_UP_STOCKS.find((s) => s.code === code);
  if (fromLimitUp) return fromLimitUp.kline.map(([date, open, close, low, high]) => ({ date, open, close, low, high }));
  // 从全市场高标查找
  const fromGainers = MARKET_TOP5_GAINERS.find((s) => s.code === code);
  if (fromGainers) return fromGainers.kline.map(([date, open, close, low, high]) => ({ date, open, close, low, high }));
  // 从连板梯队查找
  const fromBoards = MARKET_TOP3_BOARDS.find((s) => s.code === code);
  if (fromBoards) return fromBoards.kline.map(([date, open, close, low, high]) => ({ date, open, close, low, high }));
  return [];
}

/** 获取真实分时数据 */
function getIntradayData(code: string): IntradayTick[] {
  return INTRADAY_TICKS[code] || [];
}

/** 生成逐笔成交数据 */
function generateTrades(ticks: IntradayTick[]): TradeRecord[] {
  const trades: TradeRecord[] = [];
  for (let i = 1; i < ticks.length; i++) {
    const prev = ticks[i - 1];
    const curr = ticks[i];
    if (curr.price > prev.price) {
      trades.push({ time: curr.time, price: curr.price, volume: Math.round(curr.volume * 0.3), direction: 'up' });
    } else if (curr.price < prev.price) {
      trades.push({ time: curr.time, price: curr.price, volume: Math.round(curr.volume * 0.3), direction: 'down' });
    } else {
      trades.push({ time: curr.time, price: curr.price, volume: Math.round(curr.volume * 0.3), direction: 'neutral' });
    }
  }
  // 只取最后80条
  return trades.slice(-80).reverse();
}

/** 生成买卖盘5档数据 */
function generateOrderBook(currentPrice: number, prevClose: number) {
  const spread = Math.max(0.01, Math.abs(currentPrice - prevClose) * 0.02);

  const sell5 = { price: currentPrice + spread * 5, volume: Math.round(Math.random() * 500 + 100) };
  const sell4 = { price: currentPrice + spread * 4, volume: Math.round(Math.random() * 800 + 200) };
  const sell3 = { price: currentPrice + spread * 3, volume: Math.round(Math.random() * 1200 + 300) };
  const sell2 = { price: currentPrice + spread * 2, volume: Math.round(Math.random() * 2000 + 500) };
  const sell1 = { price: currentPrice + spread * 1, volume: Math.round(Math.random() * 3000 + 800) };

  const buy1 = { price: currentPrice - spread * 1, volume: Math.round(Math.random() * 3000 + 800) };
  const buy2 = { price: currentPrice - spread * 2, volume: Math.round(Math.random() * 2000 + 500) };
  const buy3 = { price: currentPrice - spread * 3, volume: Math.round(Math.random() * 1200 + 300) };
  const buy4 = { price: currentPrice - spread * 4, volume: Math.round(Math.random() * 800 + 200) };
  const buy5 = { price: currentPrice - spread * 5, volume: Math.round(Math.random() * 500 + 100) };

  // 委比 = (买总量 - 卖总量) / (买总量 + 卖总量) * 100
  const totalBuy = buy1.volume + buy2.volume + buy3.volume + buy4.volume + buy5.volume;
  const totalSell = sell1.volume + sell2.volume + sell3.volume + sell4.volume + sell5.volume;
  const weiBi = ((totalBuy - totalSell) / (totalBuy + totalSell)) * 100;

  return {
    sells: [sell5, sell4, sell3, sell2, sell1],
    buys: [buy1, buy2, buy3, buy4, buy5],
    weiBi,
    totalBuy,
    totalSell,
  };
}

/* ================================================================
   Technical Indicators Calculation
   ================================================================ */

function calcSMA(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) sum += values[i - j];
      result.push(parseFloat((sum / period).toFixed(2)));
    }
  }
  return result;
}

function calcEMA(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const result: number[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i === 0) result.push(values[0]);
    else {
      const ema = values[i] * k + result[i - 1] * (1 - k);
      result.push(parseFloat(ema.toFixed(4)));
    }
  }
  return result;
}

function calcStd(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      const slice = values.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
      result.push(parseFloat(Math.sqrt(variance).toFixed(4)));
    }
  }
  return result;
}

/** 计算所有MA均线 */
function calcAllMA(closes: number[]): Record<string, (number | null)[]> {
  const last5Avg = closes.slice(-5).reduce((a, b) => a + b, 0) / 5;
  const ma5 = calcSMA(closes, 5);
  const ma10 = closes.map((_, i) => i < 9 ? parseFloat((last5Avg * 0.98).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 10; j++) s += closes[i - j]; return parseFloat((s / 10).toFixed(2)); })());
  const ma20 = closes.map((_, i) => i < 19 ? parseFloat((last5Avg * 0.96).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 20; j++) s += closes[i - j]; return parseFloat((s / 20).toFixed(2)); })());
  const ma30 = closes.map((_, i) => i < 29 ? parseFloat((last5Avg * 0.94).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 30; j++) s += closes[i - j]; return parseFloat((s / 30).toFixed(2)); })());
  const ma60 = closes.map((_, i) => i < 59 ? parseFloat((last5Avg * 0.90).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 60; j++) s += closes[i - j]; return parseFloat((s / 60).toFixed(2)); })());
  const ma120 = closes.map((_, i) => i < 119 ? parseFloat((last5Avg * 0.85).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 120; j++) s += closes[i - j]; return parseFloat((s / 120).toFixed(2)); })());
  const ma300 = closes.map((_, i) => i < 299 ? parseFloat((last5Avg * 0.80).toFixed(2)) : (() => { let s = 0; for (let j = 0; j < 300; j++) s += closes[i - j]; return parseFloat((s / 300).toFixed(2)); })());
  return { MA5: ma5, MA10: ma10, MA20: ma20, MA30: ma30, MA60: ma60, MA120: ma120, MA300: ma300 };
}

/** MACD计算 */
function calcMACD(closes: number[]) {
  const ema12 = calcEMA(closes, 12);
  const ema26 = calcEMA(closes, 26);
  const dif = ema12.map((v, i) => parseFloat((v - ema26[i]).toFixed(4)));
  const dea = calcEMA(dif, 9);
  const macd = dif.map((v, i) => parseFloat(((v - dea[i]) * 2).toFixed(4)));
  return { dif, dea, macd };
}

/** KDJ计算 */
function calcKDJ(klines: KlinePoint[]) {
  const n = klines.length;
  const kValues: number[] = [];
  const dValues: number[] = [];
  const jValues: number[] = [];
  const lows = klines.map((k) => k.low);
  const highs = klines.map((k) => k.high);
  const closes = klines.map((k) => k.close);
  const period = Math.min(6, n);
  let prevK = 50, prevD = 50;
  for (let i = 0; i < n; i++) {
    const lowN = Math.min(...lows.slice(Math.max(0, i - period + 1), i + 1));
    const highN = Math.max(...highs.slice(Math.max(0, i - period + 1), i + 1));
    const rsv = highN === lowN ? 0 : ((closes[i] - lowN) / (highN - lowN)) * 100;
    const k = (2 / 3) * prevK + (1 / 3) * rsv;
    const d = (2 / 3) * prevD + (1 / 3) * k;
    const j = 3 * k - 2 * d;
    kValues.push(parseFloat(k.toFixed(2)));
    dValues.push(parseFloat(d.toFixed(2)));
    jValues.push(parseFloat(j.toFixed(2)));
    prevK = k; prevD = d;
  }
  return { k: kValues, d: dValues, j: jValues };
}

/** BOLL布林带计算 */
function calcBOLL(closes: number[]) {
  const ma5 = calcSMA(closes, 5);
  const std5 = calcStd(closes, 5);
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (ma5[i] === null || std5[i] === null) { upper.push(null); lower.push(null); }
    else {
      upper.push(parseFloat(((ma5[i] as number) + 2 * (std5[i] as number)).toFixed(2)));
      lower.push(parseFloat(((ma5[i] as number) - 2 * (std5[i] as number)).toFixed(2)));
    }
  }
  return { mid: ma5, upper, lower };
}

/** RSI计算 */
function calcRSI(closes: number[], period: number = 6): number[] {
  const rsi: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (i < period) { rsi.push(50); continue; }
    let gain = 0, loss = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const change = closes[j] - closes[j - 1];
      if (change > 0) gain += change;
      else loss += Math.abs(change);
    }
    const avgGain = gain / period;
    const avgLoss = loss / period;
    if (avgLoss === 0) rsi.push(100);
    else rsi.push(parseFloat((100 - 100 / (1 + avgGain / avgLoss)).toFixed(2)));
  }
  return rsi;
}

/** 模拟成交量 */
function generateVolumes(klines: KlinePoint[]): number[] {
  return klines.map((k, i) => {
    const isLimitUp = Math.abs(k.close - k.high) < 0.01 && i > 0 && k.close > klines[i - 1].close * 1.09;
    const base = 100000 + Math.random() * 500000;
    if (isLimitUp) return Math.round(base * (0.3 + Math.random() * 0.5));
    if (k.close > k.open) return Math.round(base * (1.2 + Math.random() * 1.5));
    return Math.round(base * (0.8 + Math.random() * 0.8));
  });
}

/* ================================================================
   ECharts Option builders — 分时图（含副图指标）
   ================================================================ */

function buildIntradayMainOption(
  times: string[],
  prices: number[],
  avgPrices: number[],
  volumes: number[],
  prevClose: number,
  limitUp: number,
  limitDown: number,
) {
  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'cross' as const, lineStyle: { color: BORDER } },
      backgroundColor: BG_CARD,
      borderColor: BORDER,
      textStyle: { color: TEXT_MAIN, fontSize: 11 },
      formatter: (params: Array<{ seriesName: string; value: number; marker: string; axisValue: string }>) => {
        if (!params || !params.length) return '';
        let html = `<div style="font-size:10px;color:${TEXT_MUTED};margin-bottom:4px;">${params[0].axisValue}</div>`;
        params.forEach((p) => {
          if (p.value !== undefined && p.value !== null) {
            const val = typeof p.value === 'number' ? p.value.toFixed(2) : p.value;
            html += `<div style="font-size:10px;">${p.marker} ${p.seriesName}: <b>${val}</b></div>`;
          }
        });
        return html;
      },
    },
    legend: { data: ['价格', '均价'], textStyle: { color: TEXT_SECOND, fontSize: 10 }, top: 4, left: 60 },
    grid: [
      { left: 60, right: 20, top: 32, height: '58%' },
      { left: 60, right: 20, top: '74%', height: '18%' },
    ],
    xAxis: [
      {
        type: 'category' as const, data: times, scale: true, boundaryGap: false,
        axisLine: { lineStyle: { color: BORDER } },
        axisLabel: { color: TEXT_MUTED, fontSize: 9, interval: 59 },
        axisTick: { show: false },
      },
      {
        type: 'category' as const, gridIndex: 1, data: times, scale: true, boundaryGap: false,
        axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true, splitNumber: 5,
        axisLine: { show: false },
        axisLabel: { color: TEXT_MUTED, fontSize: 10, fontFamily: 'JetBrains Mono', formatter: (v: number) => v.toFixed(2) },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } },
      },
      {
        scale: true, gridIndex: 1, splitNumber: 2,
        axisLine: { show: false },
        axisLabel: { color: TEXT_MUTED, fontSize: 9, formatter: (v: number) => (v >= 10000 ? (v / 10000).toFixed(0) + '万' : String(v)) },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.04)' } },
      },
    ],
    series: [
      {
        name: '价格', type: 'line', data: prices, smooth: false, showSymbol: false,
        lineStyle: { color: '#ffffff', width: 1 },
        markLine: {
          silent: true, symbol: 'none',
          data: [
            { yAxis: limitUp, lineStyle: { color: RED, type: 'dashed' as const, width: 1 }, label: { formatter: '涨停', color: RED, fontSize: 9, position: 'insideEndTop' as const } },
            { yAxis: prevClose, lineStyle: { color: TEXT_SECOND, type: 'dashed' as const, width: 0.8 }, label: { formatter: '昨收', color: TEXT_SECOND, fontSize: 9, position: 'insideStartTop' as const } },
            { yAxis: limitDown, lineStyle: { color: GREEN, type: 'dashed' as const, width: 1 }, label: { formatter: '跌停', color: GREEN, fontSize: 9, position: 'insideEndBottom' as const } },
          ],
        },
      },
      {
        name: '均价', type: 'line', data: avgPrices, smooth: false, showSymbol: false,
        lineStyle: { color: YELLOW, width: 1 },
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: volumes.map((v, i) => ({ value: v, itemStyle: { color: prices[i] >= prevClose ? RED : GREEN } })),
        barWidth: '50%',
      },
    ],
  };
}

/** 分时副图 MACD */
function buildIntradayMACDOption(times: string[], dif: number[], dea: number[], macd: number[]) {
  return {
    backgroundColor: 'transparent', animation: false,
    tooltip: { trigger: 'axis' as const, backgroundColor: BG_CARD, borderColor: BORDER, textStyle: { color: TEXT_MAIN, fontSize: 10 } },
    legend: { data: ['DIF', 'DEA', 'MACD'], textStyle: { color: TEXT_SECOND, fontSize: 9 }, top: 0, itemWidth: 14, itemHeight: 2 },
    grid: { left: 60, right: 20, top: 22, bottom: 20, height: '68%' },
    xAxis: { type: 'category' as const, data: times, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
    series: [
      { name: 'DIF', type: 'line', data: dif, smooth: true, showSymbol: false, lineStyle: { color: '#fff', width: 1 } },
      { name: 'DEA', type: 'line', data: dea, smooth: true, showSymbol: false, lineStyle: { color: YELLOW, width: 1 } },
      { name: 'MACD', type: 'bar', data: macd, barWidth: '50%', itemStyle: { color: (p: { value: number }) => p.value >= 0 ? RED : GREEN } },
    ],
  };
}

/** 分时副图 KDJ */
function buildIntradayKDJOption(times: string[], k: number[], d: number[], j: number[]) {
  return {
    backgroundColor: 'transparent', animation: false,
    tooltip: { trigger: 'axis' as const, backgroundColor: BG_CARD, borderColor: BORDER, textStyle: { color: TEXT_MAIN, fontSize: 10 } },
    legend: { data: ['K', 'D', 'J'], textStyle: { color: TEXT_SECOND, fontSize: 9 }, top: 0, itemWidth: 14, itemHeight: 2 },
    grid: { left: 60, right: 20, top: 22, bottom: 20, height: '68%' },
    xAxis: { type: 'category' as const, data: times, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value' as const, min: 0, max: 100, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
    series: [
      { name: 'K', type: 'line', data: k, smooth: true, showSymbol: false, lineStyle: { color: '#fff', width: 1.2 } },
      { name: 'D', type: 'line', data: d, smooth: true, showSymbol: false, lineStyle: { color: YELLOW, width: 1 } },
      { name: 'J', type: 'line', data: j, smooth: true, showSymbol: false, lineStyle: { color: '#a855f7', width: 1 } },
    ],
  };
}

/** 分时副图 RSI */
function buildIntradayRSIOption(times: string[], rsi: number[]) {
  return {
    backgroundColor: 'transparent', animation: false,
    tooltip: { trigger: 'axis' as const, backgroundColor: BG_CARD, borderColor: BORDER, textStyle: { color: TEXT_MAIN, fontSize: 10 } },
    legend: { data: ['RSI'], textStyle: { color: TEXT_SECOND, fontSize: 9 }, top: 0, itemWidth: 14, itemHeight: 2 },
    grid: { left: 60, right: 20, top: 22, bottom: 20, height: '68%' },
    xAxis: { type: 'category' as const, data: times, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value' as const, min: 0, max: 100, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
    series: [
      { name: 'RSI', type: 'line', data: rsi, smooth: true, showSymbol: false, lineStyle: { color: '#fff', width: 1.2 },
        markLine: { silent: true, symbol: 'none', data: [
          { yAxis: 80, lineStyle: { color: RED, type: 'dashed' as const, width: 0.5 }, label: { show: false } },
          { yAxis: 50, lineStyle: { color: TEXT_MUTED, type: 'dashed' as const, width: 0.5 }, label: { show: false } },
          { yAxis: 20, lineStyle: { color: GREEN, type: 'dashed' as const, width: 0.5 }, label: { show: false } },
        ]},
      },
    ],
  };
}

/** 分时副图 BOLL */
function buildIntradayBOLLOption(times: string[], mid: (number | null)[], upper: (number | null)[], lower: (number | null)[]) {
  return {
    backgroundColor: 'transparent', animation: false,
    tooltip: { trigger: 'axis' as const, backgroundColor: BG_CARD, borderColor: BORDER, textStyle: { color: TEXT_MAIN, fontSize: 10 } },
    legend: { data: ['上轨', '中轨', '下轨'], textStyle: { color: TEXT_SECOND, fontSize: 9 }, top: 0, itemWidth: 14, itemHeight: 2 },
    grid: { left: 60, right: 20, top: 22, bottom: 20, height: '68%' },
    xAxis: { type: 'category' as const, data: times, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
    series: [
      { name: '上轨', type: 'line', data: upper, smooth: true, showSymbol: false, lineStyle: { color: RED, width: 1 } },
      { name: '中轨', type: 'line', data: mid, smooth: true, showSymbol: false, lineStyle: { color: '#fff', width: 1.2 } },
      { name: '下轨', type: 'line', data: lower, smooth: true, showSymbol: false, lineStyle: { color: GREEN, width: 1 } },
    ],
  };
}

/* ================================================================
   ECharts Option builders — 日K线（含成交量+MACD）
   ================================================================ */

function buildDailyKlineOption(
  klines: KlinePoint[],
  volumes: number[],
  mas: Record<string, (number | null)[]>,
  macdData: { dif: number[]; dea: number[]; macd: number[] },
) {
  const dates = klines.map((k) => k.date);
  const candleData = klines.map((k) => [k.open, k.close, k.low, k.high]);

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'cross' as const, lineStyle: { color: BORDER, type: 'dashed' as const } },
      backgroundColor: BG_CARD,
      borderColor: BORDER,
      textStyle: { color: TEXT_MAIN, fontSize: 11, fontFamily: 'JetBrains Mono' },
      formatter: (params: unknown) => {
        const ps = params as Array<{ seriesName: string; value: unknown; dataIndex: number; marker: string }>;
        if (!ps || !ps.length) return '';
        const idx = ps[0].dataIndex;
        const k = klines[idx];
        if (!k) return '';
        let html = `<div style="font-size:11px;color:${TEXT_MUTED};margin-bottom:4px;">${k.date}</div>`;
        html += `<div style="display:flex;gap:8px;margin-bottom:4px;">`;
        html += `<span style="color:${TEXT_SECOND}">开 ${k.open.toFixed(2)}</span>`;
        html += `<span style="color:${k.close >= k.open ? RED : GREEN}">收 ${k.close.toFixed(2)}</span>`;
        html += `<span style="color:${TEXT_SECOND}">高 ${k.high.toFixed(2)}</span>`;
        html += `<span style="color:${TEXT_SECOND}">低 ${k.low.toFixed(2)}</span>`;
        html += `</div>`;
        ps.forEach((p) => {
          if (p.seriesName === 'K线' || p.seriesName === '成交量' || p.seriesName === 'MACD' || p.seriesName === 'DIF' || p.seriesName === 'DEA') return;
          const v = typeof p.value === 'number' ? p.value.toFixed(2) : String(p.value);
          html += `<div style="font-size:10px;">${p.marker} ${p.seriesName}: <b>${v}</b></div>`;
        });
        return html;
      },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: 60, right: 20, top: 32, height: '48%' },
      { left: 60, right: 20, top: '64%', height: '10%' },
      { left: 60, right: 20, top: '80%', height: '12%' },
    ],
    xAxis: [
      { type: 'category' as const, data: dates, scale: true, boundaryGap: true, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { color: TEXT_MUTED, fontSize: 10 }, axisTick: { show: false }, splitLine: { show: false }, gridIndex: 0 },
      { type: 'category' as const, data: dates, gridIndex: 1, scale: true, boundaryGap: true, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false }, splitLine: { show: false } },
      { type: 'category' as const, data: dates, gridIndex: 2, scale: true, boundaryGap: true, axisLine: { lineStyle: { color: BORDER } }, axisLabel: { show: false }, axisTick: { show: false }, splitLine: { show: false } },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 10, fontFamily: 'JetBrains Mono' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)' } } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.04)' } } },
      { scale: true, gridIndex: 2, splitNumber: 2, axisLine: { show: false }, axisLabel: { color: TEXT_MUTED, fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.04)' } } },
    ],
    series: [
      { name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: candleData,
        itemStyle: { color: RED, color0: GREEN, borderColor: RED, borderColor0: GREEN, borderWidth: 1 },
        barWidth: '50%',
      },
      { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA5, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA5, width: 1.2 } },
      { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA10, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA10, width: 1 } },
      { name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA20, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA20, width: 1 } },
      { name: 'MA30', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA30, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA30, width: 1 } },
      { name: 'MA60', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA60, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA60, width: 1 } },
      { name: 'MA120', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA120, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA120, width: 1 } },
      { name: 'MA300', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: mas.MA300, smooth: true, showSymbol: false, lineStyle: { color: MA_COLORS.MA300, width: 1 } },
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: volumes.map((v, i) => ({ value: v, itemStyle: { color: klines[i].close >= klines[i].open ? RED : GREEN } })),
        barWidth: '50%',
      },
      { name: 'DIF', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.dif, smooth: true, showSymbol: false, lineStyle: { color: '#fff', width: 1 } },
      { name: 'DEA', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.dea, smooth: true, showSymbol: false, lineStyle: { color: YELLOW, width: 1 } },
      { name: 'MACD', type: 'bar', xAxisIndex: 2, yAxisIndex: 2,
        data: macdData.macd, barWidth: '50%',
        itemStyle: { color: (p: { value: number }) => p.value >= 0 ? RED : GREEN },
      },
    ],
  };
}

/* ================================================================
   Sub-Components
   ================================================================ */

/** 5档买卖盘 */
function OrderBookPanel({ currentPrice, prevClose, orderBook }: { currentPrice: number; prevClose: number; orderBook: ReturnType<typeof generateOrderBook> }) {
  const isUp = currentPrice >= prevClose;
  return (
    <div className="flex flex-col h-full text-[12px] select-none">
      {/* 卖5-卖1 */}
      <div className="flex-1 flex flex-col justify-end">
        {orderBook.sells.map((s, i) => (
          <div key={`sell${5 - i}`} className="flex items-center justify-between py-[3px] px-2 hover:bg-[rgba(255,255,255,0.03)]">
            <span className="text-[#94a3b8] w-8">卖{5 - i}</span>
            <span className="font-mono text-[#ef4444] flex-1 text-right pr-3">{s.price.toFixed(2)}</span>
            <span className="font-mono text-[#94a3b8] w-12 text-right">{s.volume}</span>
          </div>
        ))}
      </div>

      {/* 分隔线 + 最新价 */}
      <div className="border-y border-[rgba(148,163,184,0.12)] py-2 px-2 my-1">
        <div className="flex items-center justify-between">
          <span className="text-[#94a3b8]">最新</span>
          <span className="font-mono font-bold text-[16px]" style={{ color: isUp ? RED : GREEN }}>{currentPrice.toFixed(2)}</span>
        </div>
      </div>

      {/* 买1-买5 */}
      <div className="flex-1 flex flex-col justify-start">
        {orderBook.buys.map((b, i) => (
          <div key={`buy${i + 1}`} className="flex items-center justify-between py-[3px] px-2 hover:bg-[rgba(255,255,255,0.03)]">
            <span className="text-[#94a3b8] w-8">买{i + 1}</span>
            <span className="font-mono text-[#22c55e] flex-1 text-right pr-3">{b.price.toFixed(2)}</span>
            <span className="font-mono text-[#94a3b8] w-12 text-right">{b.volume}</span>
          </div>
        ))}
      </div>

      {/* 统计信息 */}
      <div className="mt-2 pt-2 border-t border-[rgba(148,163,184,0.08)] space-y-1 px-1">
        <div className="flex justify-between">
          <span className="text-[#475569]">委比</span>
          <span className="font-mono" style={{ color: orderBook.weiBi >= 0 ? RED : GREEN }}>{orderBook.weiBi >= 0 ? '+' : ''}{orderBook.weiBi.toFixed(2)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#475569]">总量</span>
          <span className="font-mono text-[#94a3b8]">{(orderBook.totalBuy + orderBook.totalSell).toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#475569]">外盘</span>
          <span className="font-mono text-[#ef4444]">{orderBook.totalBuy.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#475569]">内盘</span>
          <span className="font-mono text-[#22c55e]">{orderBook.totalSell.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}

/** 逐笔成交 */
function TradeList({ trades }: { trades: TradeRecord[] }) {
  return (
    <div className="flex flex-col h-full">
      {/* 表头 */}
      <div className="flex items-center justify-between py-1 px-2 border-b border-[rgba(148,163,184,0.08)] text-[10px] text-[#475569]">
        <span className="w-12">时间</span>
        <span className="flex-1 text-center">价格</span>
        <span className="w-10 text-right">手数</span>
        <span className="w-6 text-right">方向</span>
      </div>
      {/* 列表 */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {trades.map((t, i) => (
          <div key={i} className="flex items-center justify-between py-[2px] px-2 hover:bg-[rgba(255,255,255,0.02)] text-[11px] font-mono">
            <span className="w-12 text-[#475569]">{t.time}</span>
            <span className="flex-1 text-center" style={{ color: t.direction === 'up' ? RED : t.direction === 'down' ? GREEN : TEXT_SECOND }}>{t.price.toFixed(2)}</span>
            <span className="w-10 text-right text-[#94a3b8]">{t.volume}</span>
            <span className="w-6 text-right">
              {t.direction === 'up' ? <ChevronUp size={12} className="text-[#ef4444] inline" /> :
               t.direction === 'down' ? <ChevronDown size={12} className="text-[#22c55e] inline" /> :
               <Minus size={12} className="text-[#475569] inline" />}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** MA数值显示条 */
function MABar({ mas, lastIdx }: { mas: Record<string, (number | null)[]>; lastIdx: number }) {
  return (
    <div className="flex items-center gap-3 px-2 py-1 flex-wrap">
      {Object.entries(MA_COLORS).map(([name, color]) => {
        const val = mas[name]?.[lastIdx];
        return (
          <span key={name} className="flex items-center gap-1 text-[10px]">
            <span className="w-2 h-[2px] inline-block rounded-full" style={{ backgroundColor: color }} />
            <span style={{ color }}>{name}</span>
            <span className="font-mono text-[#94a3b8]">{val !== null ? val.toFixed(2) : '-'}</span>
          </span>
        );
      })}
    </div>
  );
}

/* ================================================================
   Main Component
   ================================================================ */

export default function StockDetailModal({ open, onClose, stock }: StockDetailModalProps) {
  const [mainTab, setMainTab] = useState<'intraday' | 'daily'>('intraday');
  const [subIndicator, setSubIndicator] = useState<'MACD' | 'KDJ' | 'RSI' | 'BOLL'>('MACD');

  const [calcError, setCalcError] = useState<string | null>(null);

  const stockData = useMemo(() => {
    if (!stock) return null;
    setCalcError(null);
    try {
      const klines = getStockKline(stock.code);
      if (klines.length === 0) return null;

      const closes = klines.map((k) => k.close);
      const dates = klines.map((k) => k.date);
      const mas = calcAllMA(closes);
      const macd = calcMACD(closes);
      const kdj = calcKDJ(klines);
      const boll = calcBOLL(closes);
      const rsi = calcRSI(closes);
      const volumes = generateVolumes(klines);

      // 昨收、涨停价、跌停价
      const prevClose = klines.length > 1 ? klines[klines.length - 2].close : closes[0];
      const limitUp = parseFloat((prevClose * 1.1).toFixed(2));
      const limitDown = parseFloat((prevClose * 0.9).toFixed(2));

      // 真实分时数据
      const intradayTicks = getIntradayData(stock.code);
      const hasIntraday = intradayTicks.length > 0;
      const intradayTimes = hasIntraday ? intradayTicks.map((t) => t.time) : [];
      const intradayPrices = hasIntraday ? intradayTicks.map((t) => t.price) : [];
      const intradayAvgPrices = hasIntraday ? intradayTicks.map((t) => t.avgPrice) : [];
      const intradayVolumes = hasIntraday ? intradayTicks.map((t) => t.volume) : [];

      // 逐笔成交
      const trades = hasIntraday ? generateTrades(intradayTicks) : [];

      // 买卖盘
      const orderBook = generateOrderBook(stock.price, prevClose);

      const rawStock = REAL_LIMIT_UP_STOCKS.find((s) => s.code === stock.code)
        || MARKET_TOP5_GAINERS.find((s) => s.code === stock.code)
        || MARKET_TOP3_BOARDS.find((s) => s.code === stock.code);

      return {
        klines, closes, dates, mas, macd, kdj, boll, rsi, volumes,
        prevClose, limitUp, limitDown,
        intradayTicks, intradayTimes, intradayPrices, intradayAvgPrices, intradayVolumes,
        trades, orderBook, rawStock,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCalcError(msg);
      return null;
    }
  }, [stock]);

  // ── 数据异常兜底 ──
  if (!open) return null;
  if (!stock || !stockData) {
    return (
      <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
        <DialogContent
          showCloseButton={false}
          className="border-0 p-0 m-0 rounded-none overflow-hidden flex flex-col !max-w-none !w-screen !h-screen !max-h-screen !inset-0 !top-0 !left-0 !translate-x-0 !translate-y-0"
          style={{ backgroundColor: BG }}
        >
          <div className="flex items-center justify-between px-4 py-2 border-b border-[rgba(148,163,184,0.1)] shrink-0" style={{ backgroundColor: BG_CARD }}>
            <span className="text-[16px] font-bold text-[#f1f5f9]">个股详情</span>
            <button onClick={onClose} className="p-1 rounded hover:bg-[rgba(255,255,255,0.08)] transition-colors">
              <X size={18} className="text-[#94a3b8]" />
            </button>
          </div>
          <div className="flex-1 flex items-center justify-center flex-col gap-3">
            <BarChart3 size={48} className="text-[#475569] opacity-50" />
            <span className="text-[14px] text-[#94a3b8]">{!stock ? '未选择个股' : `暂无 ${stock.code} ${stock.name} 的数据`}</span>
            {calcError && (
              <div className="max-w-[600px] mx-4 p-3 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] rounded text-[12px] text-[#ef4444] font-mono">
                计算错误: {calcError}
              </div>
            )}
            <button onClick={onClose} className="px-4 py-2 bg-[#c9a84c] text-[#060b14] rounded-md text-[13px] font-medium hover:bg-[#e0c878] transition-colors">关闭</button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const {
    klines, dates, mas, macd, volumes,
    prevClose, limitUp, limitDown,
    intradayTimes, intradayPrices, intradayAvgPrices, intradayVolumes,
    trades, orderBook, rawStock,
  } = stockData;

  const isUp = stock.change >= 0;
  const priceColor = isUp ? RED : GREEN;
  const lastIdx = dates.length - 1;

  // 标签
  const positionTag = stock.position || (rawStock?.consecutiveBoards && rawStock.consecutiveBoards >= 3 ? '总龙头' : rawStock?.consecutiveBoards && rawStock.consecutiveBoards >= 2 ? '分支龙头' : '首板');
  const sectorTag = stock.sectorStatus || '主线';

  // 换手率/振幅等模拟
  const huanShou = rawStock ? (rawStock.volTo20d * 10).toFixed(2) : '0.00';
  const liangBi = rawStock ? rawStock.volRatio.toFixed(2) : '0.00';
  const zhenFu = rawStock ? ((rawStock.changePct * 1.2)).toFixed(2) : '0.00';

  // ── 图表配置 ──
  const intradayMainOpt = buildIntradayMainOption(intradayTimes, intradayPrices, intradayAvgPrices, intradayVolumes, prevClose, limitUp, limitDown);

  // 分时副图配置
  const getSubIndicatorOption = useCallback(() => {
    switch (subIndicator) {
      case 'MACD': {
        const ema12 = calcEMA(intradayPrices, 12);
        const ema26 = calcEMA(intradayPrices, 26);
        const dif = ema12.map((v, i) => parseFloat((v - ema26[i]).toFixed(4)));
        const dea = calcEMA(dif, 9);
        const macdVal = dif.map((v, i) => parseFloat(((v - dea[i]) * 2).toFixed(4)));
        return buildIntradayMACDOption(intradayTimes, dif, dea, macdVal);
      }
      case 'KDJ': {
        const kdjV = calcKDJ(intradayPrices.map((p, i) => ({ date: intradayTimes[i], open: p, close: p, low: p * 0.998, high: p * 1.002 })));
        return buildIntradayKDJOption(intradayTimes, kdjV.k, kdjV.d, kdjV.j);
      }
      case 'RSI': {
        const rsiV = calcRSI(intradayPrices);
        return buildIntradayRSIOption(intradayTimes, rsiV);
      }
      case 'BOLL': {
        const bollV = calcBOLL(intradayPrices);
        return buildIntradayBOLLOption(intradayTimes, bollV.mid, bollV.upper, bollV.lower);
      }
    }
  }, [subIndicator, intradayTimes, intradayPrices]);

  const dailyKlineOpt = buildDailyKlineOption(klines, volumes, mas, macd);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent
        showCloseButton={false}
        className="border-0 p-0 m-0 rounded-none overflow-hidden flex flex-col !max-w-none !w-screen !h-screen !max-h-screen !inset-0 !top-0 !left-0 !translate-x-0 !translate-y-0"
        style={{
          backgroundColor: BG,
        }}
      >
        {/* ═══════════════ Header ═══════════════ */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[rgba(148,163,184,0.1)] shrink-0" style={{ backgroundColor: BG_CARD }}>
          <div className="flex items-center gap-3">
            {/* 股票名称代码 */}
            <div className="flex items-center gap-2">
              <span className="text-[16px] font-bold text-[#f1f5f9]">{stock.name}</span>
              <span className="text-[12px] text-[#94a3b8] font-mono">{stock.code}</span>
            </div>
            {/* 标签 */}
            <span className="text-[10px] px-2 py-[2px] rounded bg-[rgba(201,168,76,0.15)] text-[#c9a84c] border border-[rgba(201,168,76,0.2)]">{positionTag}</span>
            <span className="text-[10px] px-2 py-[2px] rounded bg-[rgba(6,215,215,0.12)] text-[#06d7d7] border border-[rgba(6,215,215,0.2)]">{sectorTag}</span>
            {rawStock?.consecutiveBoards && rawStock.consecutiveBoards >= 1 && (
              <span className="text-[10px] px-2 py-[2px] rounded bg-[rgba(239,68,68,0.15)] text-[#ef4444] border border-[rgba(239,68,68,0.2)]">{rawStock.consecutiveBoards}连板</span>
            )}
            {/* 价格信息 */}
            <div className="flex items-center gap-3 ml-4">
              <span className="text-[22px] font-bold font-mono" style={{ color: priceColor }}>{stock.price.toFixed(2)}</span>
              <span className="text-[12px] font-mono" style={{ color: priceColor }}>{isUp ? '+' : ''}{stock.change.toFixed(2)}%</span>
              {stock.change >= 9.9 && <span className="text-[10px] px-2 py-[2px] rounded bg-[rgba(239,68,68,0.2)] text-[#ef4444] font-bold">涨停</span>}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* 游资 */}
            {rawStock?.yingyouMatch && (
              <span className="text-[10px] px-2 py-[2px] rounded bg-[rgba(168,85,247,0.12)] text-[#a855f7] border border-[rgba(168,85,247,0.2)]">{rawStock.yingyouMatch}</span>
            )}
            {/* 关闭按钮 */}
            <button onClick={onClose} className="p-1 rounded hover:bg-[rgba(255,255,255,0.08)] transition-colors">
              <X size={18} className="text-[#94a3b8]" />
            </button>
          </div>
        </div>

        {/* ═══════════════ 主内容区 (3栏布局) ═══════════════ */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* ─── 左栏：盘口数据 ─── */}
          <div className="w-[160px] shrink-0 border-r border-[rgba(148,163,184,0.08)] flex flex-col" style={{ backgroundColor: BG_CARD }}>
            {/* 涨跌幅摘要 */}
            <div className="px-3 py-2 border-b border-[rgba(148,163,184,0.06)]">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#475569]">涨跌</span>
                <span className="text-[12px] font-mono" style={{ color: priceColor }}>{isUp ? '+' : ''}{stock.change.toFixed(2)}%</span>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#475569]">振幅</span>
                <span className="text-[12px] font-mono text-[#94a3b8]">{zhenFu}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#475569]">换手</span>
                <span className="text-[12px] font-mono text-[#94a3b8]">{huanShou}%</span>
              </div>
            </div>
            {/* 买卖盘 */}
            <div className="flex-1 overflow-y-auto px-2 py-1">
              <OrderBookPanel currentPrice={stock.price} prevClose={prevClose} orderBook={orderBook} />
            </div>
            {/* 底部统计 */}
            <div className="px-3 py-2 border-t border-[rgba(148,163,184,0.06)] space-y-1">
              <div className="flex justify-between">
                <span className="text-[10px] text-[#475569]">量比</span>
                <span className="text-[11px] font-mono text-[#94a3b8]">{liangBi}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] text-[#475569]">涨停</span>
                <span className="text-[11px] font-mono text-[#ef4444]">{limitUp.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] text-[#475569]">跌停</span>
                <span className="text-[11px] font-mono text-[#22c55e]">{limitDown.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] text-[#475569]">昨收</span>
                <span className="text-[11px] font-mono text-[#94a3b8]">{prevClose.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* ─── 中栏：图表主区域 ─── */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* 顶部Tab切换 */}
            <div className="flex items-center justify-between px-3 py-1 border-b border-[rgba(148,163,184,0.06)] shrink-0">
              <Tabs value={mainTab} onValueChange={(v) => setMainTab(v as 'intraday' | 'daily')}>
                <TabsList className="bg-[#0f1929] border border-[rgba(148,163,184,0.08)] h-7">
                  <TabsTrigger value="intraday" className="text-[11px] data-[state=active]:bg-[#1a2744] data-[state=active]:text-[#f1f5f9] text-[#475569] px-3 py-0.5 h-6">
                    <Clock size={12} className="mr-1" />分时
                  </TabsTrigger>
                  <TabsTrigger value="daily" className="text-[11px] data-[state=active]:bg-[#1a2744] data-[state=active]:text-[#f1f5f9] text-[#475569] px-3 py-0.5 h-6">
                    <BarChart3 size={12} className="mr-1" />日线
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              {/* 日线MA数值显示 */}
              {mainTab === 'daily' && <MABar mas={mas} lastIdx={lastIdx} />}
            </div>

            {/* 图表区域 */}
            <div className="flex-1 flex flex-col min-h-0">
              {mainTab === 'intraday' ? (
                <>
                  {/* 分时主图 */}
                  <div className="flex-[3] min-h-0">
                    {intradayTimes.length > 0 ? (
                      <ReactECharts option={intradayMainOpt} style={{ height: '100%', width: '100%' }} notMerge={true} />
                    ) : (
                      <div className="flex items-center justify-center h-full text-[#475569] text-[13px]">暂无分时数据</div>
                    )}
                  </div>
                  {/* 分时副图指标 */}
                  <div className="flex-1 min-h-[100px] border-t border-[rgba(148,163,184,0.06)]">
                    {intradayTimes.length > 0 ? (
                      <ReactECharts option={getSubIndicatorOption()} style={{ height: '100%', width: '100%' }} notMerge={true} />
                    ) : (
                      <div className="flex items-center justify-center h-full text-[#475569] text-[13px]">--</div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  {/* 日K主图 (K线+MA+成交量+MACD 四合一) */}
                  <div className="flex-1 min-h-0">
                    {klines.length > 0 ? (
                      <ReactECharts option={dailyKlineOpt} style={{ height: '100%', width: '100%' }} notMerge={true} />
                    ) : (
                      <div className="flex items-center justify-center h-full text-[#475569] text-[13px]">暂无日线数据</div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ─── 右栏：逐笔成交 ─── */}
          <div className="w-[150px] shrink-0 border-l border-[rgba(148,163,184,0.08)] flex flex-col" style={{ backgroundColor: BG_CARD }}>
            <div className="px-3 py-2 border-b border-[rgba(148,163,184,0.06)] flex items-center gap-1.5">
              <Activity size={11} className="text-[#c9a84c]" />
              <span className="text-[11px] text-[#475569] font-medium">逐笔成交</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <TradeList trades={trades} />
            </div>
          </div>
        </div>

        {/* ═══════════════ 底部工具栏 ═══════════════ */}
        <div className="shrink-0 border-t border-[rgba(148,163,184,0.1)] px-4 py-1.5 flex items-center gap-4" style={{ backgroundColor: BG_CARD }}>
          {mainTab === 'intraday' && (
            <>
              {/* 分时副图指标切换 */}
              <div className="flex items-center gap-1">
                {(['MACD', 'KDJ', 'RSI', 'BOLL'] as const).map((ind) => (
                  <button
                    key={ind}
                    onClick={() => setSubIndicator(ind)}
                    className="text-[10px] px-2 py-[2px] rounded transition-colors"
                    style={{
                      backgroundColor: subIndicator === ind ? 'rgba(26,39,68,0.8)' : 'transparent',
                      color: subIndicator === ind ? TEXT_MAIN : TEXT_MUTED,
                      border: subIndicator === ind ? '1px solid rgba(148,163,184,0.15)' : '1px solid transparent',
                    }}
                  >
                    {ind}
                  </button>
                ))}
              </div>
              <div className="w-px h-4 bg-[rgba(148,163,184,0.1)]" />
            </>
          )}
          {mainTab === 'daily' && (
            <>
              <span className="text-[10px] text-[#475569]">日线指标</span>
              <div className="w-px h-4 bg-[rgba(148,163,184,0.1)]" />
            </>
          )}
          {/* 底部数据摘要 */}
          <div className="flex items-center gap-4 text-[10px]">
            <span className="text-[#475569]">涨停: <span className="font-mono text-[#ef4444]">{limitUp.toFixed(2)}</span></span>
            <span className="text-[#475569]">跌停: <span className="font-mono text-[#22c55e]">{limitDown.toFixed(2)}</span></span>
            <span className="text-[#475569]">昨收: <span className="font-mono text-[#94a3b8]">{prevClose.toFixed(2)}</span></span>
            <span className="text-[#475569]">最新: <span className="font-mono" style={{ color: priceColor }}>{stock.price.toFixed(2)}</span></span>
            <span className="text-[#475569]">涨幅: <span className="font-mono" style={{ color: priceColor }}>{isUp ? '+' : ''}{stock.change.toFixed(2)}%</span></span>
            <span className="text-[#475569]">换手: <span className="font-mono text-[#94a3b8]">{huanShou}%</span></span>
            <span className="text-[#475569]">量比: <span className="font-mono text-[#94a3b8]">{liangBi}</span></span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
