/**
 * SWAT API 真实数据 Hooks
 *
 * 基于 api.ts 封装的 React Hooks，用于从后端 API 获取真实数据。
 * 支持自动刷新、错误重试、加载状态管理。
 *
 * 使用方式:
 *   const { data, loading, error, refresh } = useMarketOverview();
 */

import { useState, useEffect, useCallback, useRef } from "react";
import swatAPI, { APIError, type APIResponse } from "../services/api";

// ── Hook 通用状态类型 ───────────────────────────────────

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface AsyncActions {
  refresh: () => void;
  refreshAsync: () => Promise<void>;
}

// ── 通用数据 Hook 工厂 ──────────────────────────────────

function useAPI<T>(
  fetcher: () => Promise<APIResponse>,
  deps: any[] = [],
  autoRefresh?: number, // ms
): AsyncState<T> & AsyncActions {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetcher();
      if (response.code === 200) {
        setData(response.data as T);
      } else {
        setError(response.message || "未知错误");
      }
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(`API ${err.status}: ${err.detail || err.statusText}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("请求失败");
      }
    } finally {
      setLoading(false);
    }
  }, deps);

  // 初始加载 + 依赖变化
  useEffect(() => {
    fetchData();
  }, [fetchData, refreshKey]);

  // 自动刷新
  useEffect(() => {
    if (autoRefresh && autoRefresh > 0) {
      intervalRef.current = setInterval(() => {
        setRefreshKey((k) => k + 1);
      }, autoRefresh);
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }
  }, [autoRefresh]);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  const refreshAsync = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return { data, loading, error, refresh, refreshAsync };
}

// ── 市场数据 Hooks ──────────────────────────────────────

import type { MarketOverviewData, HeatMapSector, LimitUpStock } from "../services/api";

export function useMarketOverview(autoRefresh = 60000) {
  return useAPI<{ data: MarketOverviewData }>(
    () => swatAPI.market.overview(),
    [],
    autoRefresh,
  );
}

export function useMarketIndices(refresh = false) {
  return useAPI(
    () => swatAPI.market.indices(refresh),
    [refresh],
  );
}

export function useLimitUpStocks(params?: {
  date_str?: string;
  sort_by?: string;
  limit?: number;
}) {
  return useAPI<{ stocks: LimitUpStock[] }>(
    () => swatAPI.market.limitUp(params),
    [JSON.stringify(params)],
  );
}

export function useHeatMap(params?: {
  sort_by?: string;
  min_temperature?: number;
}) {
  return useAPI<{ sectors: HeatMapSector[] }>(
    () => swatAPI.market.heatMap(params),
    [JSON.stringify(params)],
  );
}

// ── 情绪数据 Hooks ──────────────────────────────────────

import type { EmotionDiagnosisData, ThemeData, PredictionData } from "../services/api";

export function useEmotionDiagnosis(autoRefresh = 120000) {
  return useAPI<{
    diagnosis: EmotionDiagnosisData;
    prediction: PredictionData;
  }>(() => swatAPI.sentiment.diagnosis(), [], autoRefresh);
}

export function useThemeRanking(params?: {
  min_strength?: number;
  cycle_filter?: string;
}) {
  return useAPI<{ themes: ThemeData[] }>(
    () => swatAPI.sentiment.themes(params),
    [JSON.stringify(params)],
  );
}

export function usePrediction() {
  return useAPI<{ data: PredictionData }>(() => swatAPI.sentiment.prediction());
}

export function useEmotionHistory(days = 30) {
  return useAPI(() => swatAPI.sentiment.history(days), [days]);
}

// ── 评分数据 Hooks ──────────────────────────────────────

import type { ComprehensiveScoreData, RiskRewardResult, TradePlanData } from "../services/api";

export function useScoringRank(params?: {
  limit?: number;
  min_score?: number;
  sector?: string;
}) {
  return useAPI<{ rankings: ComprehensiveScoreData[] }>(
    () => swatAPI.scoring.rank(params),
    [JSON.stringify(params)],
    120000,
  );
}

export function useStockScore(ticker: string, stock_name?: string) {
  return useAPI<{ score: ComprehensiveScoreData }>(
    () => swatAPI.scoring.calculate(ticker, stock_name),
    [ticker, stock_name],
  );
}

export function useTradePlan(ticker: string, stock_name?: string, score?: number) {
  return useAPI<{ plan: TradePlanData; score_info: any }>(
    () => swatAPI.scoring.tradePlan(ticker, stock_name, score),
    [ticker, stock_name, score],
  );
}

// ── 个股数据 Hooks ──────────────────────────────────────

import type { StockDetailData, KlineData, FundamentalsData } from "../services/api";

export function useStockDetail(ticker: string) {
  return useAPI<{ data: StockDetailData }>(
    () => swatAPI.stock.detail(ticker),
    [ticker],
    60000,
  );
}

export function useStockPrices(ticker: string, days = 60, interval = "D") {
  return useAPI<{ prices: KlineData[] }>(
    () => swatAPI.stock.prices(ticker, days, interval),
    [ticker, days, interval],
    300000,
  );
}

export function useStockFundamentals(ticker: string, refresh = false) {
  return useAPI<{ fundamentals: FundamentalsData }>(
    () => swatAPI.stock.fundamentals(ticker, refresh),
    [ticker, refresh],
  );
}

export function useStockHolders(ticker: string) {
  return useAPI(() => swatAPI.stock.holders(ticker), [ticker]);
}

export function useStockAnnouncements(
  ticker: string,
  days = 30,
  category?: string,
) {
  return useAPI(
    () => swatAPI.stock.announcements(ticker, days, category),
    [ticker, days, category],
  );
}

// ── 资讯数据 Hooks ──────────────────────────────────────

import type { NewsItem, RiskItem, PreMarketData } from "../services/api";

export function useLatestNews(params?: {
  category?: string;
  impact?: string;
  limit?: number;
  sector?: string;
}) {
  return useAPI<{ news: NewsItem[] }>(
    () => swatAPI.news.latest(params),
    [JSON.stringify(params)],
    120000,
  );
}

export function useRiskList(params?: { level?: string; risk_type?: string }) {
  return useAPI<{ risks: RiskItem[] }>(
    () => swatAPI.news.riskList(params),
    [JSON.stringify(params)],
  );
}

export function usePreMarket(autoRefresh = 300000) {
  return useAPI<{ data: PreMarketData }>(
    () => swatAPI.news.preMarket(),
    [],
    autoRefresh,
  );
}

// ── 盘中监控 Hooks ──────────────────────────────────────

export function useAnchorStocks(autoRefresh = 30000) {
  return useAPI(() => swatAPI.intraday.anchors(), [], autoRefresh);
}

export function useFundFlow(params?: { sector?: string; min_net?: number }) {
  return useAPI(
    () => swatAPI.intraday.fundFlow(params),
    [JSON.stringify(params)],
    60000,
  );
}

export function useAlerts(urgency?: string, autoRefresh = 30000) {
  return useAPI(
    () => swatAPI.intraday.alerts(urgency),
    [urgency],
    autoRefresh,
  );
}

// ── 战法 Hooks ─────────────────────────────────────────

export function useTacticsList(category?: string) {
  return useAPI(() => swatAPI.tactics.list(category), [category]);
}

export function useTacticsMatch(ticker?: string) {
  return useAPI(() => swatAPI.tactics.match(ticker), [ticker]);
}

// ── 诊断 Hooks ─────────────────────────────────────────

export function useTraderProfile(days = 90) {
  return useAPI(() => swatAPI.diagnosis.profile(days), [days]);
}

export function useAttribution(dimension = "theme", days = 90) {
  return useAPI(
    () => swatAPI.diagnosis.attribution(dimension, days),
    [dimension, days],
  );
}

export function useErrorLibrary(params?: { status?: string; error_type?: string }) {
  return useAPI(() => swatAPI.diagnosis.errors(params), [JSON.stringify(params)]);
}

// ── 辅助函数 ────────────────────────────────────────────

/**
 * 批量获取多只个股评分
 */
export async function batchGetScores(
  tickers: string[],
): Promise<Map<string, any>> {
  const results = new Map<string, any>();
  const promises = tickers.map(async (ticker) => {
    try {
      const resp = await swatAPI.scoring.calculate(ticker);
      if (resp.code === 200 && resp.data?.score) {
        results.set(ticker, resp.data.score);
      }
    } catch (err) {
      console.warn(`Failed to get score for ${ticker}:`, err);
    }
  });
  await Promise.all(promises);
  return results;
}

/**
 * 计算风险收益比 (独立方法)
 */
export async function calculateRiskReward(params: {
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  position_size?: number;
  confidence?: number;
}): Promise<RiskRewardResult | null> {
  try {
    const resp = await swatAPI.scoring.riskReward(params);
    if (resp.code === 200) {
      return resp.data.result;
    }
    return null;
  } catch (err) {
    console.error("Risk reward calculation failed:", err);
    return null;
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const resp = await swatAPI.health();
    return resp.code === 200;
  } catch {
    return false;
  }
}

// ── 导出所有 ────────────────────────────────────────────
export { swatAPI };
export { APIError };
