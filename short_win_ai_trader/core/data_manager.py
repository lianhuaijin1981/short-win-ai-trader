"""统一数据管理器 — 协调所有数据源访问"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ..data_platform.cache_manager import CacheManager
from ..data_platform.data_models import (
    DragonBond, LimitUpStock, MarketSnapshot, StockPrice, ThemeData,
)
from ..data_platform.ifind_client import iFindClient
from .config import AppConfig
from .logger import get_logger

logger = get_logger("swat.data_manager")


def get_data_source(data_source_name: str, api_name: str, params: dict) -> Any:
    """直接调用数据源API的通用方法
    
    这是一个适配器函数，用于在模块代码中直接调用数据源工具。
    """
    # 实际运行时通过工具调用
    import json
    logger.debug(f"数据源调用: {data_source_name}.{api_name}")
    # 返回模拟数据结构，实际由运行时工具填充
    return []


class DataManager:
    """统一数据管理器
    
    作为所有模块的数据访问入口，提供:
    - 统一的数据获取接口
    - 缓存管理
    - 数据格式转换
    - 批量数据获取优化
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.ifind = iFindClient(config)
        self.cache = CacheManager(
            cache_dir=config.data.ifind.cache_dir,
            default_ttl=config.data.ifind.cache_ttl,
        )
        logger.info("统一数据管理器初始化完成")

    # ==================== 便捷数据接口 ====================

    async def get_stock_prices(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
    ) -> List[StockPrice]:
        """获取个股价格数据（通用接口）"""
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days + 5)
        else:
            end_date = end_date or date.today()
            start_date = start_date or (end_date - timedelta(days=60))
        return await self.ifind.get_stock_price(tickers, start_date, end_date)

    async def get_market_overview(self, trade_date: Optional[date] = None) -> Dict:
        """获取市场概览（综合多维度数据）"""
        trade_date = trade_date or date.today()
        
        snapshot = await self.ifind.get_market_snapshot(trade_date)
        limit_ups = await self.ifind.get_limit_up_stocks(trade_date)
        dragon_bonds = await self.ifind.get_dragon_bonds(trade_date)
        
        return {
            "snapshot": snapshot,
            "limit_up_stocks": limit_ups,
            "dragon_bonds": dragon_bonds,
            "trade_date": trade_date,
        }

    async def get_stock_fundamentals(self, ticker: str) -> Dict:
        """获取个股基本面综合数据"""
        # 获取财务指标
        current_year = date.today().strftime("%Y")
        periods = [f"{current_year}1231", f"{current_year}0930", f"{int(current_year)-1}1231"]
        
        fundamentals = {
            "ticker": ticker,
            "profitability": {},
            "growth": {},
            "holder_info": {},
            "announcements": [],
        }
        
        for period in periods:
            try:
                profitability = await self.ifind.get_financial_index(
                    ticker, period, "profitability"
                )
                if profitability:
                    fundamentals["profitability"] = profitability
                    break
            except Exception:
                continue
        
        for period in periods:
            try:
                growth = await self.ifind.get_financial_index(
                    ticker, period, "growth"
                )
                if growth:
                    fundamentals["growth"] = growth
                    break
            except Exception:
                continue
        
        try:
            fundamentals["holder_info"] = await self.ifind.get_holder_info(ticker)
        except Exception:
            pass
        
        try:
            end = date.today()
            start = end - timedelta(days=30)
            fundamentals["announcements"] = await self.ifind.get_announcements(ticker, start, end)
        except Exception:
            pass
        
        return fundamentals

    async def batch_get_stock_info(self, tickers: List[str]) -> Dict[str, Dict]:
        """批量获取股票信息"""
        results = {}
        for ticker in tickers:
            try:
                info = await self.get_stock_fundamentals(ticker)
                results[ticker] = info
            except Exception as e:
                logger.warning(f"获取{ticker}信息失败: {e}")
                results[ticker] = {}
        return results

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear_all()
        logger.info("数据缓存已清空")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache.stats()
