// ═══════════════════════════════════════════════════════════════
//  交易相关 API 服务层（预留后端接口）
// ═══════════════════════════════════════════════════════════════

import type {
  TradeRecord,
  TradeJournal,
  JournalTemplate,
  TradeDiagnosis,
  MarketEnvironment,
  SectorEnvironment,
  StockPanelData,
  CapitalFlowData,
  ComparisonData,
  NewsCatalystData,
  SpecialSceneData,
  UserProfile,
  ApiResponse,
  PaginatedResponse,
  PaginationParams,
} from '@/data/tradeData';

// ── API Base URL (可配置) ──────────────────────────────────────
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// ── Helper: Fetch with error handling ──────────────────────────
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      success: true,
      data: data as T,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    };
  }
}

// ═══════════════════════════════════════════════════════════════
//  交易日志 API
// ═══════════════════════════════════════════════════════════════

export const journalApi = {
  // 获取日志模板列表
  getTemplates: () =>
    apiFetch<JournalTemplate[]>('/journal/templates'),

  // 创建日志模板
  createTemplate: (template: Omit<JournalTemplate, 'id' | 'createdAt' | 'updatedAt'>) =>
    apiFetch<JournalTemplate>('/journal/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    }),

  // 更新日志模板
  updateTemplate: (id: string, updates: Partial<JournalTemplate>) =>
    apiFetch<JournalTemplate>(`/journal/templates/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  // 删除日志模板
  deleteTemplate: (id: string) =>
    apiFetch<void>(`/journal/templates/${id}`, {
      method: 'DELETE',
    }),

  // 获取交易日志列表
  getJournals: (params?: PaginationParams & { dateFrom?: string; dateTo?: string }) =>
    apiFetch<PaginatedResponse<TradeJournal>>(
      `/journal?${new URLSearchParams(params as any).toString()}`
    ),

  // 获取单篇日志
  getJournal: (id: string) =>
    apiFetch<TradeJournal>(`/journal/${id}`),

  // 创建交易日志
  createJournal: (journal: Omit<TradeJournal, 'id' | 'createdAt' | 'updatedAt'>) =>
    apiFetch<TradeJournal>('/journal', {
      method: 'POST',
      body: JSON.stringify(journal),
    }),

  // 更新交易日志
  updateJournal: (id: string, updates: Partial<TradeJournal>) =>
    apiFetch<TradeJournal>(`/journal/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  // 删除交易日志
  deleteJournal: (id: string) =>
    apiFetch<void>(`/journal/${id}`, {
      method: 'DELETE',
    }),
};

// ═══════════════════════════════════════════════════════════════
//  历史交易记录 API
// ═══════════════════════════════════════════════════════════════

export const tradeApi = {
  // 获取交易记录列表
  getRecords: (params?: PaginationParams & {
    dateFrom?: string;
    dateTo?: string;
    stockCode?: string;
    tradeType?: 'buy' | 'sell';
  }) =>
    apiFetch<PaginatedResponse<TradeRecord>>(
      `/trades?${new URLSearchParams(params as any).toString()}`
    ),

  // 获取单笔交易记录
  getRecord: (id: string) =>
    apiFetch<TradeRecord>(`/trades/${id}`),

  // 创建交易记录
  createRecord: (record: Omit<TradeRecord, 'id' | 'createdAt' | 'updatedAt'>) =>
    apiFetch<TradeRecord>('/trades', {
      method: 'POST',
      body: JSON.stringify(record),
    }),

  // 批量导入交易记录
  importRecords: (records: Omit<TradeRecord, 'id' | 'createdAt' | 'updatedAt'>[]) =>
    apiFetch<TradeRecord[]>('/trades/import', {
      method: 'POST',
      body: JSON.stringify({ records }),
    }),

  // 更新交易记录
  updateRecord: (id: string, updates: Partial<TradeRecord>) =>
    apiFetch<TradeRecord>(`/trades/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  // 删除交易记录
  deleteRecord: (id: string) =>
    apiFetch<void>(`/trades/${id}`, {
      method: 'DELETE',
    }),

  // 获取用户画像分析
  getUserProfile: (dateFrom?: string, dateTo?: string) =>
    apiFetch<UserProfile>(
      `/trades/profile?dateFrom=${dateFrom || ''}&dateTo=${dateTo || ''}`
    ),

  // 获取高频错误统计
  getHighFreqErrors: (dateFrom?: string, dateTo?: string) =>
    apiFetch<unknown>(
      `/trades/errors?dateFrom=${dateFrom || ''}&dateTo=${dateTo || ''}`
    ),
};

// ═══════════════════════════════════════════════════════════════
//  交易诊断 API
// ═══════════════════════════════════════════════════════════════

export const diagnosisApi = {
  // 获取交易诊断结果
  getDiagnosis: (tradeId: string) =>
    apiFetch<TradeDiagnosis>(`/diagnosis/${tradeId}`),

  // 创建/更新交易诊断
  saveDiagnosis: (diagnosis: Omit<TradeDiagnosis, 'createdAt'>) =>
    apiFetch<TradeDiagnosis>('/diagnosis', {
      method: 'POST',
      body: JSON.stringify(diagnosis),
    }),

  // 获取相似环境历史参考
  getHistoricalReference: (tradeId: string) =>
    apiFetch<unknown>('/diagnosis/historical', {
      method: 'POST',
      body: JSON.stringify({ tradeId }),
    }),
};

// ═══════════════════════════════════════════════════════════════
//  完整交易环境数据 API
// ═══════════════════════════════════════════════════════════════

export const environmentApi = {
  // 获取大盘宏观环境
  getMarketEnvironment: (timestamp: string) =>
    apiFetch<MarketEnvironment>(`/environment/market?timestamp=${timestamp}`),

  // 获取行业板块+题材联动环境
  getSectorEnvironment: (timestamp: string) =>
    apiFetch<SectorEnvironment>(`/environment/sector?timestamp=${timestamp}`),

  // 获取个股盘面图形数据
  getStockPanelData: (stockCode: string, timestamp: string) =>
    apiFetch<StockPanelData>(`/environment/stock?code=${stockCode}&timestamp=${timestamp}`),

  // 获取资金博弈与筹码异动数据
  getCapitalFlowData: (stockCode: string, timestamp: string) =>
    apiFetch<CapitalFlowData>(`/environment/capital?code=${stockCode}&timestamp=${timestamp}`),

  // 获取强弱对标对比数据
  getComparisonData: (stockCode: string, timestamp: string) =>
    apiFetch<ComparisonData>(`/environment/comparison?code=${stockCode}&timestamp=${timestamp}`),

  // 获取消息面舆情催化数据
  getNewsCatalystData: (stockCode: string, timestamp: string) =>
    apiFetch<NewsCatalystData>(`/environment/news?code=${stockCode}&timestamp=${timestamp}`),

  // 获取特殊交易场景数据
  getSpecialSceneData: (stockCode: string, timestamp: string, sceneType: string) =>
    apiFetch<SpecialSceneData>(
      `/environment/special?code=${stockCode}&timestamp=${timestamp}&scene=${sceneType}`
    ),

  // 一键获取完整交易环境（批量接口）
  getFullTradeEnvironment: (tradeId: string) =>
    apiFetch<{
      trade: TradeRecord;
      market: MarketEnvironment;
      sector: SectorEnvironment;
      stock: StockPanelData;
      capital: CapitalFlowData;
      comparison: ComparisonData;
      news: NewsCatalystData;
      special: SpecialSceneData;
      diagnosis: TradeDiagnosis;
    }>(`/environment/full/${tradeId}`),
};

// ═══════════════════════════════════════════════════════════════
//  行情数据 API（用于获取实时/历史行情）
// ═══════════════════════════════════════════════════════════════

export const marketApi = {
  // 获取指数快照
  getIndexSnapshot: (code: string, timestamp: string) =>
    apiFetch<unknown>(`/market/index?code=${code}&timestamp=${timestamp}`),

  // 获取大盘分时数据
  getIndexIntraday: (code: string, date: string) =>
    apiFetch<unknown>(`/market/index/intraday?code=${code}&date=${date}`),

  // 获取市场广度数据
  getMarketBreadth: (date: string) =>
    apiFetch<unknown>(`/market/breadth?date=${date}`),

  // 获取北向资金数据
  getNorthboundFlow: (date: string) =>
    apiFetch<unknown>(`/market/northbound?date=${date}`),

  // 获取板块行情
  getSectorSnapshot: (code: string, timestamp: string) =>
    apiFetch<unknown>(`/market/sector?code=${code}&timestamp=${timestamp}`),

  // 获取板块分时数据
  getSectorIntraday: (code: string, date: string) =>
    apiFetch<unknown>(`/market/sector/intraday?code=${code}&date=${date}`),

  // 获取题材排行
  getTopicRanking: (date: string) =>
    apiFetch<unknown>(`/market/topic-ranking?date=${date}`),

  // 获取个股分时数据
  getStockIntraday: (code: string, date: string) =>
    apiFetch<unknown>(`/market/stock/intraday?code=${code}&date=${date}`),

  // 获取个股K线数据
  getStockKline: (code: string, period: string, count: number) =>
    apiFetch<unknown>(`/market/stock/kline?code=${code}&period=${period}&count=${count}`),

  // 获取技术指标
  getTechnicalIndicators: (code: string, timestamp: string) =>
    apiFetch<unknown>(`/market/indicator?code=${code}&timestamp=${timestamp}`),

  // 获取五档盘口
  getOrderBook: (code: string, timestamp: string) =>
    apiFetch<unknown>(`/market/orderbook?code=${code}&timestamp=${timestamp}`),

  // 获取逐笔成交
  getTickData: (code: string, timestamp: string, count: number) =>
    apiFetch<unknown>(`/market/tick?code=${code}&timestamp=${timestamp}&count=${count}`),

  // 获取资金流向
  getFundFlow: (code: string, date: string) =>
    apiFetch<unknown>(`/market/fundflow?code=${code}&date=${date}`),

  // 获取筹码分布
  getChipDistribution: (code: string, date: string) =>
    apiFetch<unknown>(`/market/chip?code=${code}&date=${date}`),

  // 获取龙虎榜数据
  getDragonTigerList: (code: string, date: string) =>
    apiFetch<unknown>(`/market/dragon-tiger?code=${code}&date=${date}`),

  // 获取个股公告
  getAnnouncements: (code: string, dateFrom: string, dateTo: string) =>
    apiFetch<unknown>(`/market/announcement?code=${code}&from=${dateFrom}&to=${dateTo}`),

  // 获取个股新闻
  getStockNews: (code: string, dateFrom: string, dateTo: string) =>
    apiFetch<unknown>(`/market/news?code=${code}&from=${dateFrom}&to=${dateTo}`),

  // 获取市场舆情
  getMarketSentiment: (code: string, date: string) =>
    apiFetch<unknown>(`/market/sentiment?code=${code}&date=${date}`),
};

// ═══════════════════════════════════════════════════════════════
//  Mock Data Functions (前端开发时使用)
// ═══════════════════════════════════════════════════════════════

// 生成 mock 大盘环境数据
export function generateMockMarketEnvironment(timestamp: string): MarketEnvironment {
  return {
    timestamp,
    indices: [
      { name: '上证指数', code: '000001.SH', value: 3250.50, change: -15.30, changePercent: -0.47, volume: 2850, timestamp },
      { name: '深证成指', code: '399001.SZ', value: 10850.20, change: -85.60, changePercent: -0.78, volume: 3650, timestamp },
      { name: '创业板指', code: '399006.SZ', value: 2180.35, change: -22.15, changePercent: -1.01, volume: 1850, timestamp },
      { name: '沪深300', code: '000300.SH', value: 3850.80, change: -18.50, changePercent: -0.48, volume: 1950, timestamp },
      { name: '中证500', code: '000905.SH', value: 6250.40, change: -35.20, changePercent: -0.56, volume: 1250, timestamp },
      { name: '科创50', code: '000688.SH', value: 980.60, change: -12.80, changePercent: -1.29, volume: 680, timestamp },
    ],
    intradayTrend: {
      timePoints: generateTimePoints(),
      values: generateRandomArray(240, 3250, 3270),
      avgValues: generateRandomArray(240, 3245, 3265),
      volumes: generateRandomArray(240, 10, 50),
      trendPhase: '横盘',
    },
    marketBreadth: {
      upCount: 1850,
      downCount: 3200,
      limitUpCount: 45,
      limitDownCount: 12,
      炸板Count: 18,
      totalVolume: 8500,
      moneyEffectScore: 42,
    },
    northboundFlow: {
      netFlow: -25.8,
      shFlow: -12.5,
      szFlow: -13.3,
      trend: 'outflow',
    },
    macroTrend: {
      dailyTrend: 'sideways',
      weeklyTrend: 'down',
      monthlyTrend: 'up',
      marketPhase: '震荡市',
    },
  };
}

// 生成 mock 板块环境数据
export function generateMockSectorEnvironment(timestamp: string): SectorEnvironment {
  return {
    timestamp,
    sectorSnapshots: [
      { code: '801010', name: '农林牧渔', level: 'sw1', value: 3250.50, changePercent: 1.25, volume: 285 },
      { code: '801030', name: '基础化工', level: 'sw1', value: 4580.20, changePercent: -0.85, volume: 420 },
      { code: '801080', name: '电子', level: 'sw1', value: 5680.35, changePercent: 2.15, volume: 680 },
      { code: '801120', name: '食品饮料', level: 'sw1', value: 12850.80, changePercent: -1.20, volume: 350 },
      { code: '801180', name: '房地产', level: 'sw1', value: 2850.40, changePercent: 0.55, volume: 180 },
    ],
    sectorIntraday: {
      sectorName: '电子',
      timePoints: generateTimePoints(),
      values: generateRandomArray(240, 5650, 5720),
      volumes: generateRandomArray(240, 5, 30),
    },
    topicRanking: [
      { rank: 1, name: 'AI芯片', changePercent: 4.85, limitUpCount: 12, maxConsecutiveBoards: 5, relatedStocks: ['688981', '603893', '002371'] },
      { rank: 2, name: '机器人', changePercent: 3.25, limitUpCount: 8, maxConsecutiveBoards: 4, relatedStocks: ['002031', '300024', '688169'] },
      { rank: 3, name: '新能源车', changePercent: 2.15, limitUpCount: 5, maxConsecutiveBoards: 3, relatedStocks: ['002594', '300750', '601689'] },
      { rank: 4, name: '光伏', changePercent: -1.85, limitUpCount: 1, maxConsecutiveBoards: 1, relatedStocks: ['601012', '002129', '300274'] },
      { rank: 5, name: '医药生物', changePercent: -0.95, limitUpCount: 2, maxConsecutiveBoards: 2, relatedStocks: ['600276', '300760', '000538'] },
    ],
    leaderStocks: [
      { code: '688981', name: '中芯国际', changePercent: 12.50, isLeader: true, intradayData: generateMockIntradayTrend() },
      { code: '603893', name: '瑞芯微', changePercent: 10.02, isLeader: false, intradayData: generateMockIntradayTrend() },
      { code: '002371', name: '北方华创', changePercent: 9.98, isLeader: false, intradayData: generateMockIntradayTrend() },
    ],
  };
}

// 生成 mock 个股盘面数据
export function generateMockStockPanelData(stockCode: string, stockName: string, timestamp: string): StockPanelData {
  return {
    timestamp,
    stockCode,
    stockName,
    intradayChart: generateMockIntradayChart(),
    klineData: {
      '1m': generateMockKline(60),
      '5m': generateMockKline(48),
      '15m': generateMockKline(16),
      '30m': generateMockKline(8),
      '60m': generateMockKline(4),
      'daily': generateMockKline(30),
      'weekly': generateMockKline(12),
      'monthly': generateMockKline(6),
    },
    indicators: {
      ma: { ma5: 28.50, ma10: 27.80, ma20: 26.90, ma60: 25.50 },
      macd: { dif: 0.85, dea: 0.62, macd: 0.46 },
      kdj: { k: 72.5, d: 68.3, j: 80.9 },
      boll: { upper: 30.50, mid: 28.20, lower: 25.90 },
      rsi: { rsi6: 65.2, rsi12: 58.8, rsi24: 52.5 },
      volume: { vol5: 1.85, vol10: 1.52 },
    },
    orderBook: {
      bids: [
        { price: 28.45, volume: 1250, orders: 8 },
        { price: 28.44, volume: 850, orders: 5 },
        { price: 28.43, volume: 2100, orders: 12 },
        { price: 28.42, volume: 650, orders: 4 },
        { price: 28.41, volume: 1800, orders: 9 },
      ],
      asks: [
        { price: 28.46, volume: 950, orders: 6 },
        { price: 28.47, volume: 1500, orders: 10 },
        { price: 28.48, volume: 750, orders: 5 },
        { price: 28.49, volume: 2200, orders: 15 },
        { price: 28.50, volume: 3500, orders: 20 },
      ],
      timestamp,
    },
    tickData: generateMockTickData(20),
    intradayStats: {
      open: 27.80,
      high: 28.95,
      low: 27.50,
      close: 28.45,
      turnoverRate: 5.82,
      volumeRatio: 1.85,
      amplitude: 5.20,
      floatMarketCap: 185.5,
    },
    tradePoint: {
      time: '10:35:22',
      price: 28.45,
      type: 'buy',
    },
  };
}

// 生成 mock 资金流向数据
export function generateMockCapitalFlowData(timestamp: string): CapitalFlowData {
  return {
    timestamp,
    fundFlow: {
      superLarge: 2.85,
      large: -1.25,
      medium: 0.58,
      small: -0.95,
    },
    chipDistribution: {
      profitRatio: 62.5,
      lockedRatio: 37.5,
      concentration: 45.8,
      peakPrices: [26.50, 28.20, 30.50],
      avgCost: 27.80,
    },
    dragonTigerList: [
      { seatName: '华泰证券深圳益田路', seatType: '游资', buyAmount: 2850, sellAmount: 580, netAmount: 2270 },
      { seatName: '中信证券上海分公司', seatType: '游资', buyAmount: 1850, sellAmount: 1200, netAmount: 650 },
      { seatName: '机构专用', seatType: '机构', buyAmount: 3500, sellAmount: 800, netAmount: 2700 },
    ],
    largeOrderAnomalies: [
      { time: '09:35:15', type: '大单挂单', price: 28.50, volume: 5000 },
      { time: '10:22:38', type: '大单撤单', price: 28.40, volume: 3500 },
      { time: '14:15:42', type: '压单', price: 28.60, volume: 8000 },
    ],
  };
}

// 生成 mock 诊断结果
export function generateMockDiagnosis(tradeId: string): TradeDiagnosis {
  return {
    tradeId,
    timingAnalysis: {
      trendPosition: '上涨中途',
      isOptimalTiming: true,
      reason: '成交点位处于趋势确认后的上涨中途，均线多头排列，MACD金叉状态，属于较好的买入时机。',
    },
    riskIdentification: [
      {
        riskType: '情绪过热',
        severity: 'medium',
        description: '当日涨停家数45家，但炸板18家，市场情绪偏热',
        evidence: '炸板率28.6%，高于历史均值20%',
      },
      {
        riskType: '板块退潮',
        severity: 'low',
        description: '所属板块近3日涨幅放缓，龙头股出现分歧',
        evidence: '板块指数3日涨幅从5.2%降至1.8%',
      },
    ],
    strengthAnalysis: {
      stockState: '独立走强',
      relativeToMarket: '强于大盘',
      relativeToSector: '强于板块',
      reason: '个股当日涨幅+8.5%，同期大盘-0.47%，板块+2.15%，明显强于大盘和板块。',
    },
    deviationAnalysis: {
      userLogic: '看好AI芯片板块持续走强，龙头股突破平台买入',
      actualEnvironment: '板块确实处于强势状态，但炸板率偏高，市场情绪有退潮迹象',
      deviation: '买入逻辑基本正确，但对市场情绪风险关注不足，建议控制仓位',
      isRationalTrade: true,
    },
    historicalReference: {
      similarCount: 28,
      winRate: 68,
      avgProfit: 5.8,
      avgLoss: -3.2,
      similarConditions: ['大盘震荡市', '板块强势', '个股突破平台', '量比>1.5'],
    },
    overallScore: 78,
    summary: '该笔交易整体质量较好，买入时机选择合理，个股选择强于大盘和板块。主要风险在于市场情绪偏热，炸板率较高。建议：1）控制仓位不超过30%；2）设置止损位-3%；3）关注板块龙头走势。',
    suggestions: [
      '控制仓位在30%以内，避免情绪过热时重仓',
      '设置-3%硬止损，跌破成本价3%无条件止损',
      '关注板块龙头股走势，龙头走弱时及时减仓',
      '避免在炸板率超过25%时追高买入',
    ],
  };
}

// ── Mock Data Helper Functions ─────────────────────────────────

function generateTimePoints(): string[] {
  const points: string[] = [];
  for (let i = 0; i < 240; i++) {
    const hour = 9 + Math.floor((i + 30) / 60);
    const minute = (i + 30) % 60;
    if (hour < 15) {
      points.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
  }
  return points;
}

function generateRandomArray(length: number, min: number, max: number): number[] {
  return Array.from({ length }, () => Math.random() * (max - min) + min);
}

function generateMockIntradayTrend(): any {
  return {
    timePoints: generateTimePoints(),
    values: generateRandomArray(240, 10, 30),
    avgValues: generateRandomArray(240, 10, 28),
    volumes: generateRandomArray(240, 5, 50),
    trendPhase: '拉升',
  };
}

function generateMockIntradayChart(): any[] {
  const data: any[] = [];
  for (let i = 0; i < 240; i++) {
    const hour = 9 + Math.floor((i + 30) / 60);
    const minute = (i + 30) % 60;
    if (hour < 15) {
      data.push({
        time: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
        price: 27.5 + Math.random() * 1.5,
        avgPrice: 27.3 + Math.random() * 1.2,
        volume: Math.floor(Math.random() * 500 + 50),
      });
    }
  }
  return data;
}

function generateMockKline(count: number): any[] {
  const data: any[] = [];
  let basePrice = 25 + Math.random() * 5;
  for (let i = 0; i < count; i++) {
    const open = basePrice + (Math.random() - 0.5) * 2;
    const close = open + (Math.random() - 0.5) * 2;
    const high = Math.max(open, close) + Math.random() * 1;
    const low = Math.min(open, close) - Math.random() * 1;
    data.push({
      time: `2026-05-${String(22 - count + i + 1).padStart(2, '0')}`,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: Math.floor(Math.random() * 100000 + 10000),
      amount: Math.floor(Math.random() * 5000000 + 500000),
      turnover: parseFloat((Math.random() * 5 + 1).toFixed(2)),
    });
    basePrice = close;
  }
  return data;
}

function generateMockTickData(count: number): any[] {
  const data: any[] = [];
  let basePrice = 28.45;
  for (let i = 0; i < count; i++) {
    const direction = Math.random() > 0.5 ? 'buy' : Math.random() > 0.5 ? 'sell' : 'neutral';
    data.push({
      time: `10:35:${String(22 - i).padStart(2, '0')}`,
      price: parseFloat((basePrice + (Math.random() - 0.5) * 0.1).toFixed(2)),
      volume: Math.floor(Math.random() * 500 + 10),
      direction,
      amount: Math.floor(Math.random() * 100000 + 10000),
      isLargeOrder: Math.random() > 0.8,
    });
  }
  return data.reverse();
}