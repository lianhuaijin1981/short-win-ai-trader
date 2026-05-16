"""iFind API 客户端封装 — 对接同花顺数据平台"""

import asyncio
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..core.config import AppConfig
from ..core.exceptions import iFindAPIError
from ..core.logger import get_logger
from .cache_manager import CacheManager
from .data_models import (
    DragonBond, LimitUpStock, MarketSnapshot, StockPrice, ThemeData,
)

logger = get_logger("swat.ifind")


class iFindClient:
    """同花顺iFind数据客户端
    
    封装iFind所有API接口，提供:
    - 历史行情数据获取
    - 实时行情快照
    - 财务数据查询
    - 龙虎榜数据
    - 公告信息
    - 智能选股
    - 股东信息
    """

    def __init__(self, config: AppConfig):
        self.config = config.data.ifind
        self.cache = CacheManager(
            cache_dir=self.config.cache_dir,
            default_ttl=self.config.cache_ttl,
        )
        logger.info(f"iFind客户端初始化: rate_limit={self.config.rate_limit}/s")

    # ==================== 行情数据 ====================

    async def get_stock_price(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        interval: str = "D",
        adjust: str = "backward",
    ) -> List[StockPrice]:
        """获取历史行情数据
        
        Args:
            tickers: 股票代码列表, e.g. ['600519.SH', '000001.SZ']
            start_date: 开始日期
            end_date: 结束日期
            interval: D=日 W=周 M=月
            adjust: backward=后复权 forward=前复权 none=不复权
        """
        cache_key = f"{'|'.join(sorted(tickers))}_{start_date}_{end_date}_{interval}_{adjust}"
        cached = self.cache.get("price", cache_key)
        if cached:
            return cached

        try:
            # 使用iFind API获取数据
            all_prices = []
            # iFind限制每请求最多10个ticker
            batch_size = self.config.max_tickers_per_query
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                logger.debug(f"获取行情: {batch} [{start_date} ~ {end_date}]")
                prices = await self._fetch_price_batch(batch, start_date, end_date, interval, adjust)
                all_prices.extend(prices)
                await asyncio.sleep(1.0 / self.config.rate_limit)

            self.cache.set("price", cache_key, all_prices, ttl=self.config.cache_ttl)
            return all_prices

        except Exception as e:
            logger.error(f"获取行情数据失败: {e}")
            raise iFindAPIError(f"获取行情失败: {e}")

    async def _fetch_price_batch(
        self, tickers: List[str], start_date: date, end_date: date,
        interval: str, adjust: str,
    ) -> List[StockPrice]:
        """批量获取行情（内部方法）"""
        from ..core.data_manager import get_data_source
        
        results = []
        for ticker in tickers:
            try:
                file_path = f"cache/price_{ticker.replace('.', '_')}_{start_date}_{end_date}.csv"
                data = get_data_source(
                    data_source_name="ifind",
                    api_name="ifind_get_price",
                    params={
                        "ticker": ticker,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "file_path": file_path,
                        "interval": interval,
                        "adjust": adjust,
                        "format": "json",
                    }
                )
                if data:
                    for item in data:
                        results.append(StockPrice(
                            ticker=ticker,
                            trade_date=date.fromisoformat(item.get("trade_date", str(date.today()))),
                            open=float(item.get("open", 0)),
                            high=float(item.get("high", 0)),
                            low=float(item.get("low", 0)),
                            close=float(item.get("close", 0)),
                            volume=int(item.get("volume", 0)),
                            amount=float(item.get("amount", 0)),
                            change_pct=float(item.get("change_pct", 0)),
                        ))
            except Exception as e:
                logger.warning(f"获取{ticker}行情失败: {e}")
        return results

    async def get_recent_prices(self, tickers: List[str], days: int = 5) -> List[StockPrice]:
        """获取最近N日行情（便捷方法）"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 5)  # 多取几天避免节假日
        return await self.get_stock_price(tickers, start_date, end_date)

    async def get_market_snapshot(self, trade_date: Optional[date] = None) -> MarketSnapshot:
        """获取市场快照"""
        trade_date = trade_date or date.today()
        cached = self.cache.get("market_snapshot", str(trade_date))
        if cached:
            return cached

        # 获取指数数据作为市场快照基础
        try:
            indices = ["000001.SH", "399001.SZ", "399006.SZ"]  # 上证/深证/创业板
            snapshot = MarketSnapshot(
                trade_date=trade_date,
                sh_index=await self._get_index_close("000001.SH", trade_date),
                sz_index=await self._get_index_close("399001.SZ", trade_date),
                cy_index=await self._get_index_close("399006.SZ", trade_date),
            )
            self.cache.set("market_snapshot", str(trade_date), snapshot, ttl=300)
            return snapshot
        except Exception as e:
            logger.error(f"获取市场快照失败: {e}")
            return MarketSnapshot(trade_date=trade_date)

    async def _get_index_close(self, ticker: str, trade_date: date) -> float:
        """获取指数收盘价"""
        try:
            prices = await self.get_stock_price([ticker], trade_date - timedelta(days=5), trade_date)
            if prices:
                return prices[-1].close
        except Exception:
            pass
        return 0.0

    # ==================== 涨停/连板数据 ====================

    async def get_limit_up_stocks(self, trade_date: Optional[date] = None) -> List[LimitUpStock]:
        """获取涨停股列表（使用智能选股接口）"""
        trade_date = trade_date or date.today()
        cached = self.cache.get("limit_up", str(trade_date))
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/limit_up_{trade_date}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_related_stock",
                params={
                    "stock_keyword": f"{trade_date.strftime('%Y年%m月%d日')} 涨停",
                    "file_path": file_path,
                    "format": "json",
                }
            )
            stocks = []
            if data:
                for item in data:
                    stocks.append(LimitUpStock(
                        ticker=item.get("ticker", ""),
                        name=item.get("name", ""),
                        consecutive_boards=int(item.get("consecutive_boards", 0)),
                        theme=item.get("theme", ""),
                        change_pct=float(item.get("change_pct", 9.9)),
                    ))
            self.cache.set("limit_up", str(trade_date), stocks, ttl=300)
            return stocks
        except Exception as e:
            logger.error(f"获取涨停股失败: {e}")
            return []

    # ==================== 龙虎榜数据 ====================

    async def get_dragon_bonds(self, trade_date: Optional[date] = None) -> List[DragonBond]:
        """获取龙虎榜数据"""
        trade_date = trade_date or date.today()
        cached = self.cache.get("dragon_bond", str(trade_date))
        if cached:
            return cached

        try:
            # 通过智能选股接口获取
            from ..core.data_manager import get_data_source
            file_path = f"cache/dragon_bond_{trade_date}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_related_stock",
                params={
                    "stock_keyword": f"{trade_date.strftime('%Y年%m月%d日')} 龙虎榜",
                    "file_path": file_path,
                    "format": "json",
                }
            )
            bonds = []
            if data:
                for item in data:
                    bonds.append(DragonBond(
                        ticker=item.get("ticker", ""),
                        trade_date=trade_date,
                        seat_name=item.get("seat_name", ""),
                        buy_amount=float(item.get("buy_amount", 0)),
                        sell_amount=float(item.get("sell_amount", 0)),
                        net_amount=float(item.get("net_amount", 0)),
                        seat_type=item.get("seat_type", "未知"),
                    ))
            self.cache.set("dragon_bond", str(trade_date), bonds, ttl=300)
            return bonds
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return []

    # ==================== 题材数据 ====================

    async def get_theme_data(self, theme_name: str, trade_date: Optional[date] = None) -> ThemeData:
        """获取题材数据"""
        trade_date = trade_date or date.today()
        cached = self.cache.get("theme", f"{theme_name}_{trade_date}")
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/theme_{theme_name}_{trade_date}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_related_stock",
                params={
                    "stock_keyword": f"{trade_date.strftime('%Y年%m月%d日')} {theme_name}",
                    "file_path": file_path,
                    "format": "json",
                }
            )
            stocks = []
            if data:
                for item in data:
                    stocks.append(item.get("ticker", ""))

            theme = ThemeData(
                theme_name=theme_name,
                stocks=stocks,
            )
            self.cache.set("theme", f"{theme_name}_{trade_date}", theme, ttl=300)
            return theme
        except Exception as e:
            logger.error(f"获取题材数据失败: {e}")
            return ThemeData(theme_name=theme_name)

    # ==================== 财务数据 ====================

    async def get_financial_data(self, ticker: str, report_period: str) -> Dict:
        """获取财务数据
        
        Args:
            ticker: 股票代码
            report_period: 报告期, e.g. '20241231'
        """
        cache_key = f"{ticker}_{report_period}"
        cached = self.cache.get("financial", cache_key)
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/financial_{ticker.replace('.', '_')}_{report_period}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_financial_statements",
                params={
                    "ticker": ticker,
                    "statement": "all",
                    "financial_parameter": report_period,
                    "file_path": file_path,
                    "format": "json",
                }
            )
            result = data if data else {}
            self.cache.set("financial", cache_key, result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return {}

    # ==================== 智能选股 ====================

    async def screen_stocks(self, keyword: str, market: str = "stock") -> List[str]:
        """智能选股
        
        Args:
            keyword: 选股条件, e.g. '人工智能 股价大于50 PE小于25'
            market: stock=股票 US_stock=美股 HK_stock=港股
        """
        cache_key = f"{keyword}_{market}"
        cached = self.cache.get("screen", cache_key)
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/screen_{hash(keyword) & 0xFFFFFFFF}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_related_stock",
                params={
                    "stock_keyword": keyword,
                    "file_path": file_path,
                    "market": market,
                    "format": "json",
                }
            )
            tickers = []
            if data:
                for item in data:
                    tickers.append(item.get("ticker", ""))
            self.cache.set("screen", cache_key, tickers, ttl=900)
            return tickers
        except Exception as e:
            logger.error(f"智能选股失败: {e}")
            return []

    # ==================== 公告数据 ====================

    async def get_announcements(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict]:
        """获取个股公告"""
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=30))
        cache_key = f"{ticker}_{start_date}_{end_date}"
        cached = self.cache.get("announcement", cache_key)
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/announcement_{ticker.replace('.', '_')}_{start_date}_{end_date}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_stock_announcement",
                params={
                    "ticker": ticker,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "file_path": file_path,
                    "format": "json",
                }
            )
            announcements = data if data else []
            self.cache.set("announcement", cache_key, announcements, ttl=3600)
            return announcements
        except Exception as e:
            logger.error(f"获取公告失败: {e}")
            return []

    # ==================== 股东信息 ====================

    async def get_holder_info(self, ticker: str) -> Dict:
        """获取股东信息"""
        cached = self.cache.get("holder", ticker)
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/holder_{ticker.replace('.', '_')}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_holder_info",
                params={
                    "ticker": ticker,
                    "file_path": file_path,
                    "format": "json",
                }
            )
            result = data if data else {}
            self.cache.set("holder", ticker, result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"获取股东信息失败: {e}")
            return {}

    # ==================== 财务指标 ====================

    async def get_financial_index(
        self, ticker: str, report_period: str, category: str
    ) -> Dict:
        """获取财务指标
        
        Args:
            category: capital_structure/liquidity/efficiency/profitability/growth/cash_coverage
        """
        cache_key = f"{ticker}_{report_period}_{category}"
        cached = self.cache.get("financial_index", cache_key)
        if cached:
            return cached

        try:
            from ..core.data_manager import get_data_source
            file_path = f"cache/fin_idx_{ticker.replace('.', '_')}_{report_period}_{category}.csv"
            data = get_data_source(
                data_source_name="ifind",
                api_name="ifind_get_stock_financial_index",
                params={
                    "ticker": ticker,
                    "financial_parameter": report_period,
                    "category": category,
                    "file_path": file_path,
                    "format": "json",
                }
            )
            result = data if data else {}
            self.cache.set("financial_index", cache_key, result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"获取财务指标失败: {e}")
            return {}
