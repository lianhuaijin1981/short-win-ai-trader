// ═══════════════════════════════════════════════════════════════
//  Tushare 数据接入服务
//  文档: https://tushare.pro/document/2
// ═══════════════════════════════════════════════════════════════

import type { TradeRecord } from '@/data/tradeData';

// ── Tushare API 配置 ───────────────────────────────────────────
const TUSHARE_API_BASE = import.meta.env.VITE_TUSHARE_API_BASE || 'http://localhost:5000/api';
const TUSHARE_TOKEN = import.meta.env.VITE_TUSHARE_TOKEN || '';

// ── 类型定义 ───────────────────────────────────────────────────

export interface TushareDailyBar {
  ts_code: string;
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  pre_close: number;
  change: number;
  pct_chg: number;
  vol: number;
  amount: number;
}

export interface TushareRealTimeQuote {
  ts_code: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  pre_close: number;
  change: number;
  pct_chg: number;
  vol: number;
  amount: number;
  buy: number;
  sell: number;
}

export interface TushareIndexQuote {
  ts_code: string;
  name: string;
  close: number;
  pct_chg: number;
  vol: number;
  amount: number;
}

export interface TushareMoneyFlow {
  ts_code: string;
  trade_date: string;
  buy_lg_amount: number;
  sell_lg_amount: number;
  net_lg_amount: number;
  buy_elg_amount: number;
  sell_elg_amount: number;
  net_elg_amount: number;
  buy_m_amount: number;
  sell_m_amount: number;
  net_m_amount: number;
  buy_s_amount: number;
  sell_s_amount: number;
  net_s_amount: number;
}

export interface TushareStockBasic {
  ts_code: string;
  symbol: string;
  name: string;
  area: string;
  industry: string;
  market: string;
  list_date: string;
  is_hs: string;
}

export interface TushareDailyBasic {
  ts_code: string;
  trade_date: string;
  turnover_rate: number;
  turnover_rate_f: number;
  volume_ratio: number;
  pe: number;
  pe_ttm: number;
  pb: number;
  ps: number;
  ps_ttm: number;
  total_mv: number;
  circ_mv: number;
}

export interface TushareLimitList {
  ts_code: string;
  trade_date: string;
  name: string;
  close: number;
  pct_chg: number;
  amp: number;
  fd_amount: number;
  first_time: string;
  last_time: string;
  open_times: number;
  up_stat: string;
  limit_type: string;
}

export interface TushareConcept {
  code: string;
  name: string;
  type: string;
}

export interface TushareConceptDetail {
  id: string;
  code: string;
  name: string;
  con_count: number;
}

export interface TushareNews {
  datetime: string;
  title: string;
  content: string;
  channels: string;
}

export interface TushareTradeCalendar {
  exchange: string;
  cal_date: string;
  is_open: number;
  pretrade_date: string;
}

// ── 通用API请求函数 ────────────────────────────────────────────

interface TushareRequest {
  api_name: string;
  token: string;
  params: Record<string, any>;
  fields: string;
}

interface TushareResponse<T> {
  code: number;
  msg: string;
  data: {
    fields: string[];
    items: T[][];
  };
}

async function tushareRequest<T>(
  apiName: string,
  params: Record<string, any> = {},
  fields: string = ''
): Promise<T[]> {
  const requestBody: TushareRequest = {
    api_name: apiName,
    token: TUSHARE_TOKEN,
    params,
    fields,
  };

  try {
    const response = await fetch(`${TUSHARE_API_BASE}/tushare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: TushareResponse<T> = await response.json();

    if (result.code !== 0) {
      throw new Error(`Tushare Error: ${result.msg}`);
    }

    // 将数组格式转换为对象格式
    const fieldNames = result.data.fields;
    return result.data.items.map((item) => {
      const obj: Record<string, any> = {};
      fieldNames.forEach((field, index) => {
        obj[field] = item[index];
      });
      return obj as unknown as T;
    });
  } catch (error) {
    console.error(`Tushare API [${apiName}] 请求失败:`, error);
    return [];
  }
}

// ═══════════════════════════════════════════════════════════════
//  行情数据接口
// ═══════════════════════════════════════════════════════════════

export const tushareMarketApi = {
  // 获取A股日线行情
  getDailyBars: async (
    tsCode: string,
    startDate?: string,
    endDate?: string
  ): Promise<TushareDailyBar[]> => {
    const params: Record<string, any> = { ts_code: tsCode };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return tushareRequest<TushareDailyBar>('daily', params,
      'ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount');
  },

  // 获取实时行情
  getRealTimeQuotes: async (tsCodes: string[]): Promise<TushareRealTimeQuote[]> => {
    return tushareRequest<TushareRealTimeQuote>('stk_mins',
      { ts_code: tsCodes.join(','), freq: '1min' },
      'ts_code,name,price,open,high,low,pre_close,change,pct_chg,vol,amount,buy,sell');
  },

  // 获取大盘指数行情
  getIndexQuotes: async (): Promise<TushareIndexQuote[]> => {
    const indexCodes = [
      '000001.SH', // 上证指数
      '399001.SZ', // 深证成指
      '399006.SZ', // 创业板指
      '000300.SH', // 沪深300
      '000905.SH', // 中证500
      '000688.SH', // 科创50
    ];
    return tushareRequest<TushareIndexQuote>('index_daily',
      { ts_code: indexCodes.join(',') },
      'ts_code,name,close,pct_chg,vol,amount');
  },

  // 获取大盘分时数据
  getIndexIntraday: async (tsCode: string, tradeDate: string): Promise<any[]> => {
    return tushareRequest('stk_mins',
      { ts_code: tsCode, freq: '1min', trade_date: tradeDate },
      'ts_code,time,open,high,low,close,vol,amount');
  },

  // 获取市场广度（涨跌家数）
  getMarketBreadth: async (tradeDate: string): Promise<any[]> => {
    return tushareRequest('index_daily',
      { ts_code: '000001.SH', start_date: tradeDate, end_date: tradeDate },
      'ts_code,trade_date,close,pct_chg');
  },

  // 获取个股K线
  getStockKline: async (
    tsCode: string,
    period: string = 'daily',
    count: number = 100
  ): Promise<TushareDailyBar[]> => {
    const freqMap: Record<string, string> = {
      '1m': '1min',
      '5m': '5min',
      '15m': '15min',
      '30m': '30min',
      '60m': '60min',
      'daily': 'D',
      'weekly': 'W',
      'monthly': 'M',
    };
    return tushareRequest<TushareDailyBar>('stk_mins',
      { ts_code: tsCode, freq: freqMap[period] || 'D', count },
      'ts_code,time,open,high,low,close,vol,amount');
  },

  // 获取技术指标
  getTechnicalIndicators: async (
    tsCode: string,
    indicator: string = 'MACD',
    period: string = 'daily'
  ): Promise<any[]> => {
    return tushareRequest('stk_factor',
      { ts_code: tsCode },
      'ts_code,trade_date,macd_dif,macd_dea,macd,k,d,j,rsi');
  },
};

// ═══════════════════════════════════════════════════════════════
//  资金流向接口
// ═══════════════════════════════════════════════════════════════

export const tushareFundApi = {
  // 获取个股资金流向
  getStockMoneyFlow: async (
    tsCode: string,
    startDate?: string,
    endDate?: string
  ): Promise<TushareMoneyFlow[]> => {
    const params: Record<string, any> = { ts_code: tsCode };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return tushareRequest<TushareMoneyFlow>('moneyflow', params,
      'ts_code,trade_date,buy_lg_amount,sell_lg_amount,net_lg_amount,buy_elg_amount,sell_elg_amount,net_elg_amount,buy_m_amount,sell_m_amount,net_m_amount,buy_s_amount,sell_s_amount,net_s_amount');
  },

  // 获取大盘资金流向
  getIndexMoneyFlow: async (tradeDate: string): Promise<any[]> => {
    return tushareRequest('moneyflow_mkt_dc',
      { trade_date: tradeDate },
      'trade_date,net_amount,close');
  },

  // 获取北向资金流向
  getNorthboundFlow: async (startDate: string, endDate: string): Promise<any[]> => {
    return tushareRequest('moneyflow_hsgt',
      { start_date: startDate, end_date: endDate },
      'trade_date,ggt_ss,ggt_sz,hgt,sgt,north_money');
  },

  // 获取板块资金流向
  getSectorMoneyFlow: async (
    type: string = 'industry',
    tradeDate: string
  ): Promise<any[]> => {
    return tushareRequest('moneyflow_ind_ths',
      { type, trade_date: tradeDate },
      'ts_code,trade_date,name,change,net_amount,net_amount_rate');
  },

  // 获取龙虎榜数据
  getDragonTigerList: async (
    tradeDate: string,
    tsCode?: string
  ): Promise<any[]> => {
    const params: Record<string, any> = { trade_date: tradeDate };
    if (tsCode) params.ts_code = tsCode;
    return tushareRequest('top_list', params,
      'ts_code,trade_date,name,close,pct_change,turnover_rate,amount,l_sell,l_buy,net_amount');
  },
};

// ═══════════════════════════════════════════════════════════════
//  筹码分布接口
// ═══════════════════════════════════════════════════════════════

export const tushareChipApi = {
  // 获取筹码分布（需要通过其他数据计算）
  getChipDistribution: async (
    tsCode: string,
    tradeDate: string
  ): Promise<any> => {
    // Tushare不直接提供筹码分布，需要通过换手率和成交量计算
    const dailyData = await tushareRequest('daily_basic',
      { ts_code: tsCode, trade_date: tradeDate },
      'ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio');
    return dailyData[0] || null;
  },
};

// ═══════════════════════════════════════════════════════════════
//  板块题材接口
// ═══════════════════════════════════════════════════════════════

export const tushareSectorApi = {
  // 获取行业板块列表
  getIndustryList: async (): Promise<any[]> => {
    return tushareRequest('ths_index',
      { type: 'N' },
      'ts_code,name,count');
  },

  // 获取概念板块列表
  getConceptList: async (): Promise<TushareConceptDetail[]> => {
    return tushareRequest<TushareConceptDetail>('concept', {}, 'code,name,type');
  },

  // 获取板块行情
  getSectorQuotes: async (tradeDate: string): Promise<any[]> => {
    return tushareRequest('ths_daily',
      { trade_date: tradeDate },
      'ts_code,trade_date,close,pct_chg,vol,amount');
  },

  // 获取题材龙头股
  getConceptLeaders: async (conceptCode: string): Promise<any[]> => {
    return tushareRequest('concept_detail',
      { id: conceptCode },
      'id,code,name');
  },

  // 获取涨停板列表
  getLimitUpList: async (tradeDate: string): Promise<TushareLimitList[]> => {
    return tushareRequest<TushareLimitList>('limit_list_d',
      { trade_date: tradeDate, limit_type: 'U' },
      'ts_code,trade_date,name,close,pct_chg,amp,fd_amount,first_time,last_time,open_times,up_stat,limit_type');
  },

  // 获取跌停板列表
  getLimitDownList: async (tradeDate: string): Promise<TushareLimitList[]> => {
    return tushareRequest<TushareLimitList>('limit_list_d',
      { trade_date: tradeDate, limit_type: 'D' },
      'ts_code,trade_date,name,close,pct_chg,amp,fd_amount,first_time,last_time,open_times,up_stat,limit_type');
  },
};

// ═══════════════════════════════════════════════════════════════
//  基本面数据接口
// ═══════════════════════════════════════════════════════════════

export const tushareFundamentalApi = {
  // 获取股票基本信息
  getStockBasic: async (tsCode?: string): Promise<TushareStockBasic[]> => {
    const params = tsCode ? { ts_code: tsCode } : {};
    return tushareRequest<TushareStockBasic>('stock_basic', params,
      'ts_code,symbol,name,area,industry,market,list_date,is_hs');
  },

  // 获取每日指标
  getDailyBasic: async (
    tsCode: string,
    startDate?: string,
    endDate?: string
  ): Promise<TushareDailyBasic[]> => {
    const params: Record<string, any> = { ts_code: tsCode };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return tushareRequest<TushareDailyBasic>('daily_basic', params,
      'ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,total_mv,circ_mv');
  },

  // 获取财务数据
  getFinanceData: async (tsCode: string): Promise<any[]> => {
    return tushareRequest('fina_indicator',
      { ts_code: tsCode },
      'ts_code,ann_date,roe,roa,grossprofit_margin,netprofit_margin');
  },

  // 获取业绩预告
  getForecast: async (tsCode: string): Promise<any[]> => {
    return tushareRequest('forecast',
      { ts_code: tsCode },
      'ts_code,ann_date,net_profit,yoy_net_profit');
  },
};

// ═══════════════════════════════════════════════════════════════
//  消息面接口
// ═══════════════════════════════════════════════════════════════

export const tushareNewsApi = {
  // 获取新闻快讯
  getNewsList: async (startDate: string, endDate: string): Promise<TushareNews[]> => {
    return tushareRequest<TushareNews>('news',
      { start_date: startDate, end_date: endDate },
      'datetime,title,content,channels');
  },

  // 获取个股新闻
  getStockNews: async (
    tsCode: string,
    startDate: string,
    endDate: string
  ): Promise<any[]> => {
    return tushareRequest('major_news',
      { ts_code: tsCode, start_date: startDate, end_date: endDate },
      'ts_code,datetime,title,content');
  },

  // 获取公司公告
  getAnnouncements: async (
    tsCode: string,
    startDate: string,
    endDate: string
  ): Promise<any[]> => {
    return tushareRequest('anns',
      { ts_code: tsCode, start_date: startDate, end_date: endDate },
      'ts_code,ann_date,title,content');
  },
};

// ═══════════════════════════════════════════════════════════════
//  交易日历
// ═══════════════════════════════════════════════════════════════

export const tushareCalendarApi = {
  // 获取交易日历
  getTradeCalendar: async (
    exchange: string = 'SSE',
    startDate: string,
    endDate: string
  ): Promise<TushareTradeCalendar[]> => {
    return tushareRequest<TushareTradeCalendar>('trade_cal',
      { exchange, start_date: startDate, end_date: endDate },
      'exchange,cal_date,is_open,pretrade_date');
  },

  // 判断是否为交易日
  isTradeDay: async (date: string): Promise<boolean> => {
    const result = await tushareRequest<TushareTradeCalendar>('trade_cal',
      { exchange: 'SSE', start_date: date, end_date: date },
      'cal_date,is_open');
    return result.length > 0 && result[0].is_open === 1;
  },
};

// ═══════════════════════════════════════════════════════════════
//  代码转换工具
// ═══════════════════════════════════════════════════════════════

export const codeConverter = {
  // 将股票代码转换为Tushare格式
  toTushareCode: (code: string, market?: string): string => {
    if (code.includes('.')) return code;
    if (code.startsWith('6')) return `${code}.SH`;
    if (code.startsWith('0') || code.startsWith('3')) return `${code}.SZ`;
    if (code.startsWith('8') || code.startsWith('4')) return `${code}.BJ`;
    return `${code}.SZ`;
  },

  // 将Tushare格式转换为普通代码
  fromTushareCode: (tsCode: string): string => {
    return tsCode.split('.')[0];
  },

  // 获取市场标识
  getMarket: (code: string): string => {
    if (code.startsWith('6')) return 'SH';
    if (code.startsWith('0') || code.startsWith('3')) return 'SZ';
    if (code.startsWith('8') || code.startsWith('4')) return 'BJ';
    return 'SZ';
  },
};

// ═══════════════════════════════════════════════════════════════
//  综合数据服务（用于诊断引擎）
// ═══════════════════════════════════════════════════════════════

export interface StockDiagnosisData {
  dailyBars: TushareDailyBar[];
  moneyFlow: TushareMoneyFlow[];
  dailyBasic: TushareDailyBasic[];
  stockBasic: TushareStockBasic | null;
  realTimeQuote: TushareRealTimeQuote | null;
}

export const tushareDiagnosisService = {
  // 获取诊断所需的完整数据
  getStockDiagnosisData: async (
    tsCode: string,
    tradeDate: string
  ): Promise<StockDiagnosisData> => {
    const [dailyBars, moneyFlow, dailyBasic, stockBasicList, realTimeQuotes] = await Promise.allSettled([
      tushareMarketApi.getDailyBars(tsCode, tradeDate.slice(0, 4) + '0101', tradeDate),
      tushareFundApi.getStockMoneyFlow(tsCode, tradeDate.slice(0, 4) + '0101', tradeDate),
      tushareFundamentalApi.getDailyBasic(tsCode, tradeDate, tradeDate),
      tushareFundamentalApi.getStockBasic(tsCode),
      tushareMarketApi.getRealTimeQuotes([tsCode]),
    ]);

    return {
      dailyBars: dailyBars.status === 'fulfilled' ? dailyBars.value : [],
      moneyFlow: moneyFlow.status === 'fulfilled' ? moneyFlow.value : [],
      dailyBasic: dailyBasic.status === 'fulfilled' ? dailyBasic.value : [],
      stockBasic: stockBasicList.status === 'fulfilled' ? stockBasicList.value[0] || null : null,
      realTimeQuote: realTimeQuotes.status === 'fulfilled' ? realTimeQuotes.value[0] || null : null,
    };
  },

  // 获取市场环境数据
  getMarketEnvironment: async (tradeDate: string) => {
    const [indexQuotes, limitUpList, limitDownList] = await Promise.allSettled([
      tushareMarketApi.getIndexQuotes(),
      tushareSectorApi.getLimitUpList(tradeDate),
      tushareSectorApi.getLimitDownList(tradeDate),
    ]);

    return {
      indices: indexQuotes.status === 'fulfilled' ? indexQuotes.value : [],
      limitUpCount: limitUpList.status === 'fulfilled' ? limitUpList.value.length : 0,
      limitDownCount: limitDownList.status === 'fulfilled' ? limitDownList.value.length : 0,
    };
  },
};

// ── 导出默认对象 ───────────────────────────────────────────────
export default {
  market: tushareMarketApi,
  fund: tushareFundApi,
  chip: tushareChipApi,
  sector: tushareSectorApi,
  fundamental: tushareFundamentalApi,
  news: tushareNewsApi,
  calendar: tushareCalendarApi,
  diagnosis: tushareDiagnosisService,
  codeConverter,
};