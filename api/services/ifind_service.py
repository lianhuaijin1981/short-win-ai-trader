"""iFind API 真实调用服务 — 短线致胜AI交易智能体数据引擎

本服务封装同花顺iFind全部API，提供:
- 历史行情数据获取
- 市场快照
- 财务数据
- 智能选股
- 公告/股东信息

支持自动缓存和速率限制。
"""

import asyncio
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.core.config import APIConfig
from api.core.logger import get_logger

logger = get_logger("swat.ifind_service")
config = APIConfig()


class iFindService:
    """iFind数据服务 — 真实API调用封装"""

    def __init__(self):
        self.rate_limit = config.ifind_rate_limit
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._call_count = 0
        self._last_reset = datetime.now()
        logger.info(f"iFindService initialized (rate_limit={self.rate_limit}/s)")

    async def _rate_limit_check(self):
        """速率限制检查"""
        now = datetime.now()
        if (now - self._last_reset).total_seconds() >= 1:
            self._call_count = 0
            self._last_reset = now
        if self._call_count >= self.rate_limit:
            wait = 1.0 - (now - self._last_reset).total_seconds()
            if wait > 0:
                logger.debug(f"Rate limit hit, waiting {wait:.2f}s")
                await asyncio.sleep(wait)
            self._call_count = 0
            self._last_reset = datetime.now()
        self._call_count += 1

    def _cache_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        import hashlib
        raw = f"{prefix}:{identifier}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _cache_get(self, prefix: str, identifier: str) -> Optional[Any]:
        """读取缓存"""
        key = self._cache_key(prefix, identifier)
        fpath = self.cache_dir / f"{key}.json"
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("expires", 0) > datetime.now().timestamp():
                    return data.get("data")
            except Exception:
                pass
        return None

    def _cache_set(self, prefix: str, identifier: str, data: Any, ttl: int = 300):
        """写入缓存"""
        key = self._cache_key(prefix, identifier)
        fpath = self.cache_dir / f"{key}.json"
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump({
                    "key": key,
                    "expires": (datetime.now() + timedelta(seconds=ttl)).timestamp(),
                    "data": data,
                }, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def _call_ifind(self, api_name: str, params: dict) -> Any:
        """调用iFind API（通过工具层）
        
        注意：实际运行时通过数据源工具调用
        """
        await self._rate_limit_check()
        logger.info(f"iFind API call: {api_name} params={list(params.keys())}")
        
        # 实际调用通过数据源工具层
        try:
            from mshtools_get_data_source import get_data_source
            result = get_data_source(
                data_source_name="ifind",
                api_name=api_name,
                params=params
            )
            return result
        except Exception as e:
            logger.error(f"iFind API call failed: {e}")
            return None

    # ── 行情数据 ──────────────────────────────────────────

    async def get_stock_prices(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "D",
    ) -> List[Dict]:
        """获取历史行情数据"""
        cache_id = f"{'|'.join(sorted(tickers))}_{start_date}_{end_date}_{interval}"
        cached = self._cache_get("price", cache_id)
        if cached:
            return cached

        all_prices = []
        batch_size = 10
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            for ticker in batch:
                try:
                    file_path = f"cache/price_{ticker.replace('.', '_')}.csv"
                    result = await self._call_ifind("ifind_get_price", {
                        "ticker": ticker,
                        "start_date": start_date,
                        "end_date": end_date,
                        "interval": interval,
                        "file_path": file_path,
                        "format": "json",
                    })
                    if result:
                        all_prices.extend(result)
                except Exception as e:
                    logger.warning(f"Failed to get price for {ticker}: {e}")
            await asyncio.sleep(0.1)

        self._cache_set("price", cache_id, all_prices, ttl=300)
        return all_prices

    async def get_recent_prices(self, tickers: List[str], days: int = 5) -> List[Dict]:
        """获取最近N日行情"""
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days + 5)).isoformat()
        return await self.get_stock_prices(tickers, start, end)

    # ── 指数/市场 ─────────────────────────────────────────

    async def get_market_indices(self) -> List[Dict]:
        """获取三大指数"""
        indices = ["000001.SH", "399001.SZ", "399006.SZ"]
        cached = self._cache_get("indices", "daily")
        if cached:
            return cached

        result = []
        for idx in indices:
            try:
                prices = await self.get_recent_prices([idx], days=1)
                if prices:
                    p = prices[-1]
                    result.append({
                        "name": {"000001.SH": "上证指数", "399001.SZ": "深证成指", "399006.SZ": "创业板指"}[idx],
                        "code": idx,
                        "current": float(p.get("close", 0)),
                        "change": float(p.get("close", 0)) - float(p.get("pre_close", p.get("open", 0))),
                        "change_pct": float(p.get("change_pct", 0)),
                        "volume": float(p.get("volume", 0)),
                        "amount": float(p.get("amount", 0)),
                    })
            except Exception as e:
                logger.warning(f"Failed to get index {idx}: {e}")

        self._cache_set("indices", "daily", result, ttl=60)
        return result

    # ── 财务数据 ──────────────────────────────────────────

    async def get_financial_index(self, ticker: str, category: str) -> Dict:
        """获取财务指标"""
        current_year = date.today().year
        periods = [f"{current_year}1231", f"{current_year}0930", f"{current_year}0630"]
        
        for period in periods:
            cache_id = f"{ticker}_{period}_{category}"
            cached = self._cache_get("financial", cache_id)
            if cached:
                return cached

            try:
                file_path = f"cache/fin_{ticker.replace('.', '_')}_{period}_{category}.csv"
                result = await self._call_ifind("ifind_get_stock_financial_index", {
                    "ticker": ticker,
                    "financial_parameter": period,
                    "category": category,
                    "file_path": file_path,
                    "format": "json",
                })
                if result:
                    self._cache_set("financial", cache_id, result, ttl=86400)
                    return result
            except Exception as e:
                logger.warning(f"Financial index failed for {ticker}/{category}: {e}")
        
        return {}

    # ── 智能选股 ──────────────────────────────────────────

    async def screen_stocks(self, keyword: str) -> List[str]:
        """智能选股"""
        cached = self._cache_get("screen", keyword)
        if cached:
            return cached

        try:
            file_path = f"cache/screen_{keyword[:30]}.csv"
            result = await self._call_ifind("ifind_get_related_stock", {
                "stock_keyword": keyword,
                "file_path": file_path,
                "format": "json",
            })
            if result:
                tickers = [item.get("ticker", "") for item in result if item.get("ticker")]
                self._cache_set("screen", keyword, tickers, ttl=900)
                return tickers
        except Exception as e:
            logger.error(f"Screen stocks failed: {e}")
        return []

    # ── 公告/股东 ─────────────────────────────────────────

    async def get_announcements(self, ticker: str, days: int = 30) -> List[Dict]:
        """获取公告"""
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days)).isoformat()
        cache_id = f"{ticker}_{start}_{end}"
        cached = self._cache_get("announcement", cache_id)
        if cached:
            return cached

        try:
            file_path = f"cache/ann_{ticker.replace('.', '_')}.csv"
            result = await self._call_ifind("ifind_get_stock_announcement", {
                "ticker": ticker,
                "start_date": start,
                "end_date": end,
                "file_path": file_path,
                "format": "json",
            })
            if result:
                self._cache_set("announcement", cache_id, result, ttl=3600)
                return result
        except Exception as e:
            logger.warning(f"Announcements failed for {ticker}: {e}")
        return []

    async def get_holder_info(self, ticker: str) -> Dict:
        """获取股东信息"""
        cached = self._cache_get("holder", ticker)
        if cached:
            return cached

        try:
            file_path = f"cache/holder_{ticker.replace('.', '_')}.csv"
            result = await self._call_ifind("ifind_get_holder_info", {
                "ticker": ticker,
                "file_path": file_path,
                "format": "json",
            })
            if result:
                self._cache_set("holder", ticker, result, ttl=86400)
                return result
        except Exception as e:
            logger.warning(f"Holder info failed for {ticker}: {e}")
        return {}

    # ── 综合查询 ──────────────────────────────────────────

    async def get_stock_fundamentals(self, ticker: str) -> Dict:
        """获取个股基本面综合数据"""
        fundamentals = {"ticker": ticker}
        
        for category in ["profitability", "growth", "capital_structure", "liquidity"]:
            try:
                data = await self.get_financial_index(ticker, category)
                if data:
                    fundamentals[category] = data
            except Exception:
                pass
        
        try:
            fundamentals["holder_info"] = await self.get_holder_info(ticker)
        except Exception:
            pass
        
        try:
            fundamentals["announcements"] = await get_announcements(ticker, days=30)
        except Exception:
            pass
        
        return fundamentals


# ── 全局实例 ────────────────────────────────────────────

ifind_service = iFindService()
