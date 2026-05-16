/**
 * SWAT API 服务层 — 封装所有后端 API 调用
 *
 * 特性:
 * - 统一错误处理与重试
 * - 响应数据缓存 (TTL)
 * - TypeScript 类型定义
 * - 请求/响应拦截器
 */

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const DEFAULT_TIMEOUT = 15000;
const MAX_RETRIES = 2;

// ── 缓存系统 ────────────────────────────────────────────

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

const cache = new Map<string, CacheEntry<any>>();

function getCacheKey(url: string, params?: Record<string, any>): string {
  if (!params) return url;
  const qs = new URLSearchParams(params).toString();
  return `${url}?${qs}`;
}

function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (!entry) return null;
  const now = Date.now();
  if (now - entry.timestamp > entry.ttl * 1000) {
    cache.delete(key);
    return null;
  }
  return entry.data as T;
}

function setCache<T>(key: string, data: T, ttl: number = 60): void {
  cache.set(key, { data, timestamp: Date.now(), ttl });
}

function clearCache(): void {
  cache.clear();
}

// ── 错误类 ──────────────────────────────────────────────

export class APIError extends Error {
  status: number;
  statusText: string;
  detail?: string;
  constructor(
    status: number,
    statusText: string,
    detail?: string,
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "APIError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
  }
}

export class NetworkError extends Error {
  constructor(message = "Network error") {
    super(message);
    this.name = "NetworkError";
  }
}

// ── 核心请求函数 ────────────────────────────────────────

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  cacheTtl?: number;
  useCache?: boolean;
  timeout?: number;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    params,
    headers = {},
    cacheTtl = 60,
    useCache = method === "GET",
    timeout = DEFAULT_TIMEOUT,
  } = options;

  const url = `${API_BASE_URL}${endpoint}`;
  const cacheKey = getCacheKey(url, params);

  // 检查缓存
  if (useCache && method === "GET") {
    const cached = getCached<T>(cacheKey);
    if (cached) return cached;
  }

  // 构建 URL (含查询参数)
  const urlObj = new URL(url, typeof window !== "undefined" ? window.location.origin : undefined);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) urlObj.searchParams.set(k, String(v));
    });
  }

  // 请求配置
  const fetchOptions: RequestInit = {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...headers,
    },
  };
  if (body) fetchOptions.body = JSON.stringify(body);

  // 重试逻辑
  let lastError: Error | null = null;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(urlObj.toString(), {
        ...fetchOptions,
        signal: controller.signal,
      });
      clearTimeout(timer);

      // 处理非 2xx 响应
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new APIError(
          response.status,
          response.statusText,
          errorBody.detail || errorBody.message || `${response.status} ${response.statusText}`,
        );
      }

      const result = await response.json();

      // 写入缓存
      if (useCache && method === "GET") {
        setCache(cacheKey, result, cacheTtl);
      }

      return result as T;
    } catch (err: any) {
      lastError = err;
      if (err.name === "AbortError") {
        lastError = new NetworkError("Request timeout");
      }
      if (err instanceof APIError && err.status < 500) break;
      if (attempt < MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
      }
    }
  }

  throw lastError || new NetworkError("Request failed after retries");
}

// ── 响应类型定义 ────────────────────────────────────────

export interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

// ── 市场数据 ────────────────────────────────────────────

export interface MarketOverviewData {
  date: string;
  indices: IndexData[];
  limit_up_count: number;
  limit_down_count: number;
  total_stocks: number;
  up_count: number;
  down_count: number;
  volume: number;
}

export interface IndexData {
  name: string;
  code: string;
  current: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
}

export interface LimitUpStock {
  ticker: string;
  name: string;
  boards: number;
  sector: string;
  price: number;
  change_pct: number;
  volume: number;
  first_board_time: string;
}

export interface HeatMapSector {
  sector: string;
  temperature: number;
  change_pct: number;
  limit_up_count: number;
  leading_stock: string;
  net_inflow: number;
}

// ── 情绪数据 ────────────────────────────────────────────

export interface EmotionDiagnosisData {
  current_cycle: string;
  confidence: number;
  position_limit: number;
  adapted_mode: string;
  core_principle: string;
  next_day_prediction: string;
  indicators: EmotionIndicators;
}

export interface EmotionIndicators {
  up_down_ratio: number;
  explode_rate: number;
  profit_effect: number;
  volume_change: number;
  max_consecutive_boards: number;
  promotion_rate: number;
  break_rate: number;
  dragon_premium: number;
  main_inflow_ratio: number;
  yingyou_activity: number;
  northbound_flow: number;
  theme_strength: number;
  sector_linkage: number;
}

export interface ThemeData {
  rank: number;
  theme: string;
  cycle: string;
  strength: number;
  limit_up_count: number;
  leading: string;
  followers: string[];
  capital: number;
  trend: string;
  temperature: number;
}

export interface PredictionData {
  market_trend: string;
  recommended_operation: string;
  key_observation_points: string[];
  success_rate_estimate: string;
  risk_reminders: string[];
  opportunity_directions: string[];
}

// ── 评分数据 ────────────────────────────────────────────

export interface DimensionScore {
  dimension: string;
  weight: number;
  score: number;
  details?: Record<string, any>;
}

export interface ComprehensiveScoreData {
  ticker: string;
  name: string;
  total_score: number;
  rating: string;
  risk_reward_ratio: number;
  risk_level: string;
  priority: number;
  position_pct: number;
  decision: string;
  dimension_scores: DimensionScore[];
}

export interface TradePlanData {
  ticker: string;
  name: string;
  entry_price: number;
  entry_type: string;
  stop_loss: number;
  take_profit: number;
  position_pct: number;
  risk_reward: string;
  hold_conditions: string[];
  sell_conditions: string[];
}

export interface RiskRewardResult {
  risk_reward_ratio: number;
  risk_reward_display: string;
  decision: string;
  level: string;
  recommended_position: string;
  breakeven_win_rate: string;
}

// ── 个股数据 ────────────────────────────────────────────

export interface StockDetailData {
  ticker: string;
  name: string;
  current_price: number;
  change_pct: number;
  emotion_cycle: string;
  theme_position: string;
  anchor_position: string;
  comprehensive_score: number;
  rating: string;
  yingyou_matches: any[];
  tactic_matches: any[];
  trade_plan: TradePlanData;
  risk_points: string[];
  success_logic: string[];
  kline: any[];
}

export interface KlineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  change_pct: number;
  ma5: number;
  ma10: number;
  ma20: number;
}

export interface FundamentalsData {
  profitability: Record<string, number>;
  growth: Record<string, number>;
  capital_structure: Record<string, number>;
  liquidity: Record<string, number>;
  valuation: Record<string, number>;
}

// ── 资讯数据 ────────────────────────────────────────────

export interface NewsItem {
  id: string;
  title: string;
  category: string;
  impact: string;
  related_sectors: string[];
  source: string;
  publish_time: string;
  is_important: boolean;
}

export interface RiskItem {
  ticker: string;
  name: string;
  risk_type: string;
  level: string;
  description: string;
  action: string;
}

export interface PreMarketData {
  date: string;
  overseas_markets: Record<string, { close: number; change_pct: number }>;
  key_news: any[];
  today_focus: any[];
  sector_outlook: any[];
  sentiment_indicator: string;
  trading_strategy: string;
}

// ── API 方法 ────────────────────────────────────────────

export const swatAPI = {
  // ── 系统 ─────────────────────────────────────────
  health: () =>
    request<APIResponse>("/health", { cacheTtl: 10, useCache: false }),

  // ── 市场 ─────────────────────────────────────────
  market: {
    overview: (useCache = true) =>
      request<APIResponse<{ data: MarketOverviewData }>>("/market/overview", {
        cacheTtl: 60,
        useCache,
      }),
    indices: (refresh = false) =>
      request<APIResponse>("/market/indices", {
        params: refresh ? { refresh: "true" } : undefined,
        cacheTtl: 60,
      }),
    limitUp: (params?: {
      date_str?: string;
      sort_by?: string;
      limit?: number;
    }) =>
      request<APIResponse<{ data: { stocks: LimitUpStock[]; total_limit_up: number } }>>(
        "/market/limit-up",
        { params, cacheTtl: 120 },
      ),
    heatMap: (params?: {
      sort_by?: string;
      min_temperature?: number;
    }) =>
      request<APIResponse<{ data: { sectors: HeatMapSector[] } }>>(
        "/market/heat-map",
        { params, cacheTtl: 120 },
      ),
  },

  // ── 情绪 ─────────────────────────────────────────
  sentiment: {
    diagnosis: () =>
      request<APIResponse<{ data: { diagnosis: EmotionDiagnosisData; prediction: PredictionData } }>>(
        "/sentiment/diagnosis",
        { cacheTtl: 120 },
      ),
    themes: (params?: { min_strength?: number; cycle_filter?: string }) =>
      request<APIResponse<{ data: { themes: ThemeData[] } }>>("/sentiment/themes", {
        params,
        cacheTtl: 180,
      }),
    prediction: () =>
      request<APIResponse<{ data: PredictionData }>>("/sentiment/prediction", {
        cacheTtl: 120,
      }),
    history: (days = 30) =>
      request<APIResponse>("/sentiment/history", { params: { days }, cacheTtl: 300 }),
  },

  // ── 评分 ─────────────────────────────────────────
  scoring: {
    rank: (params?: { limit?: number; min_score?: number; sector?: string }) =>
      request<APIResponse<{ data: { rankings: ComprehensiveScoreData[] } }>>(
        "/scoring/rank",
        { params, cacheTtl: 120 },
      ),
    calculate: (ticker: string, stock_name?: string) =>
      request<APIResponse<{ data: { score: ComprehensiveScoreData } }>>(
        "/scoring/calculate",
        { params: { ticker, stock_name }, cacheTtl: 60 },
      ),
    riskReward: (data: {
      entry_price: number;
      stop_loss: number;
      take_profit: number;
      position_size?: number;
      confidence?: number;
    }) =>
      request<APIResponse<{ data: { result: RiskRewardResult } }>>("/scoring/risk-reward", {
        method: "POST",
        body: data,
        useCache: false,
      }),
    tradePlan: (ticker: string, stock_name?: string, score?: number) =>
      request<APIResponse<{ data: { plan: TradePlanData; score_info: any } }>>(
        "/scoring/trade-plan",
        { params: { ticker, stock_name, score }, cacheTtl: 60 },
      ),
  },

  // ── 个股 ─────────────────────────────────────────
  stock: {
    detail: (ticker: string) =>
      request<APIResponse<{ data: StockDetailData }>>(`/stock/${ticker}`, {
        cacheTtl: 60,
      }),
    prices: (ticker: string, days = 60, interval = "D") =>
      request<APIResponse<{ data: { prices: KlineData[] } }>>(
        `/stock/${ticker}/prices`,
        { params: { days, interval }, cacheTtl: 300 },
      ),
    fundamentals: (ticker: string, refresh = false) =>
      request<APIResponse<{ data: { fundamentals: FundamentalsData } }>>(
        `/stock/${ticker}/fundamentals`,
        { params: refresh ? { refresh: "true" } : undefined, cacheTtl: 3600 },
      ),
    holders: (ticker: string) =>
      request<APIResponse>(`/stock/${ticker}/holders`, { cacheTtl: 3600 }),
    announcements: (ticker: string, days = 30, category?: string) =>
      request<APIResponse>(`/stock/${ticker}/announcements`, {
        params: { days, category },
        cacheTtl: 1800,
      }),
  },

  // ── 资讯 ─────────────────────────────────────────
  news: {
    latest: (params?: {
      category?: string;
      impact?: string;
      limit?: number;
      sector?: string;
    }) =>
      request<APIResponse<{ data: { news: NewsItem[] } }>>("/news/latest", {
        params,
        cacheTtl: 120,
      }),
    riskList: (params?: { level?: string; risk_type?: string }) =>
      request<APIResponse<{ data: { risks: RiskItem[] } }>>("/news/risk-list", {
        params,
        cacheTtl: 600,
      }),
    preMarket: () =>
      request<APIResponse<{ data: PreMarketData }>>("/news/pre-market", {
        cacheTtl: 600,
      }),
  },

  // ── 盘中 ─────────────────────────────────────────
  intraday: {
    anchors: () =>
      request<APIResponse>("/intraday/anchors", { cacheTtl: 30 }),
    fundFlow: (params?: { sector?: string; min_net?: number }) =>
      request<APIResponse>("/intraday/fund-flow", { params, cacheTtl: 60 }),
    alerts: (urgency?: string) =>
      request<APIResponse>("/intraday/alerts", {
        params: urgency ? { urgency } : undefined,
        cacheTtl: 30,
      }),
  },

  // ── 战法 ─────────────────────────────────────────
  tactics: {
    list: (category?: string) =>
      request<APIResponse>("/tactics/list", {
        params: category ? { category } : undefined,
        cacheTtl: 3600,
      }),
    match: (ticker?: string) =>
      request<APIResponse>("/tactics/match", {
        params: ticker ? { ticker } : undefined,
        cacheTtl: 120,
      }),
    backtest: (tactic_name: string, days = 30) =>
      request<APIResponse>("/tactics/backtest", {
        params: { tactic_name, days },
        cacheTtl: 600,
      }),
  },

  // ── 诊断 ─────────────────────────────────────────
  diagnosis: {
    import: (records: any[]) =>
      request<APIResponse>("/diagnosis/import", {
        method: "POST",
        body: { records },
        useCache: false,
      }),
    profile: (days = 90) =>
      request<APIResponse>("/diagnosis/profile", {
        params: { days },
        cacheTtl: 300,
      }),
    attribution: (dimension = "theme", days = 90) =>
      request<APIResponse>("/diagnosis/attribution", {
        params: { dimension, days },
        cacheTtl: 300,
      }),
    errors: (params?: { status?: string; error_type?: string }) =>
      request<APIResponse>("/diagnosis/errors", {
        params,
        cacheTtl: 300,
      }),
  },

  // ── 游资 ─────────────────────────────────────────
  yingyou: {
    matches: (ticker: string) =>
      request<APIResponse>(`/yingyou/match/${ticker}`, { cacheTtl: 300 }),
  },

  // ── 缓存管理 ─────────────────────────────────────
  cache: {
    clear: clearCache,
    size: () => cache.size,
    invalidate: (pattern: string) => {
      const regex = new RegExp(pattern);
      for (const key of cache.keys()) {
        if (regex.test(key)) cache.delete(key);
      }
    },
  },
};

export default swatAPI;
