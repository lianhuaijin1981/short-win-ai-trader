"""AkShare 数据服务 — A股实时数据源

使用 akshare 作为同花顺iFind的替代数据源，提供:
- 实时行情数据
- 市场指数
- 涨停板数据
- 板块资金流向
- 个股详情

AkShare 是开源的A股免费数据源，无需授权即可使用。
"""

import asyncio
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd

from api.core.config import APIConfig
from api.core.logger import get_logger

logger = get_logger("swat.akshare_service")
config = APIConfig()

# 禁用代理，避免 ProxyError
import os
os.environ["no_proxy"] = "*"
os.environ["NO_PROXY"] = "*"


class AkShareService:
    """AkShare 数据服务 — 真实A股数据获取"""

    def __init__(self):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._available = True
        # 设置 akshare 不使用代理
        try:
            import requests
            session = requests.Session()
            session.trust_env = False
            session.proxies = {}
        except Exception:
            pass
        logger.info("AkShareService initialized (proxy disabled)")

    def _cache_get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """读取缓存"""
        cache_file = self.cache_dir / f"ak_{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("expires", 0) > datetime.now().timestamp():
                    return data.get("data")
            except Exception:
                pass
        return None

    def _cache_set(self, key: str, data: Any, ttl: int = 300):
        """写入缓存"""
        cache_file = self.cache_dir / f"ak_{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "key": key,
                    "expires": (datetime.now() + timedelta(seconds=ttl)).timestamp(),
                    "data": data,
                }, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def get_market_indices(self) -> List[Dict]:
        """获取三大指数实时数据"""
        cached = self._cache_get("indices", ttl=30)
        if cached:
            return cached

        try:
            # 获取实时指数数据
            df = ak.stock_zh_index_spot_em()
            
            indices = []
            index_codes = {
                "上证指数": {"code": "000001.SH", "base": 3100},
                "深证成指": {"code": "399001.SZ", "base": 9500},
                "创业板指": {"code": "399006.SZ", "base": 1800},
            }
            
            for _, row in df.iterrows():
                name = row.get("名称", "")
                if name in index_codes:
                    info = index_codes[name]
                    current = float(row.get("最新价", info["base"]))
                    change = float(row.get("涨跌额", 0))
                    change_pct = float(row.get("涨跌幅", 0))
                    
                    indices.append({
                        "name": name,
                        "code": info["code"],
                        "current": current,
                        "change": change,
                        "change_pct": change_pct,
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                    })
            
            if indices:
                self._cache_set("indices", indices, ttl=30)
                logger.info(f"Got {len(indices)} indices from akshare")
                return indices
            
        except Exception as e:
            logger.warning(f"Failed to get indices from akshare: {e}")
        
        return []

    async def get_limit_up_stocks(self) -> List[Dict]:
        """获取涨停板股票"""
        today = date.today().strftime("%Y%m%d")
        cached = self._cache_get(f"limit_up_{today}", ttl=60)
        if cached:
            return cached

        try:
            # 获取涨停股池
            df = ak.stock_zt_pool_em(date=today)
            
            stocks = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                
                if not code or not name:
                    continue
                
                # 确定交易所后缀
                if code.startswith("6"):
                    ticker = f"{code}.SH"
                elif code.startswith("0") or code.startswith("3"):
                    ticker = f"{code}.SZ"
                else:
                    ticker = code
                
                # 连板数
                boards = int(row.get("连板数", 1))
                
                stocks.append({
                    "ticker": ticker,
                    "name": name,
                    "boards": boards,
                    "change_pct": float(row.get("涨跌幅", 10.0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)) / 10000,  # 转为亿
                    "seal_amount": float(row.get("封板资金", 0)) / 10000,
                    "first_seal_time": str(row.get("首次封板时间", "")),
                    "last_seal_time": str(row.get("最后封板时间", "")),
                    "open_times": int(row.get("炸板次数", 0)),
                    "sector": str(row.get("所属行业", "")),
                    "price": float(row.get("最新价", 0)),
                })
            
            stocks.sort(key=lambda x: x["boards"], reverse=True)
            
            if stocks:
                self._cache_set(f"limit_up_{today}", stocks, ttl=60)
                logger.info(f"Got {len(stocks)} limit-up stocks from akshare")
                return stocks
            
        except Exception as e:
            logger.warning(f"Failed to get limit-up stocks from akshare: {e}")
        
        return []

    async def get_sector_fund_flow(self) -> List[Dict]:
        """获取板块资金流向"""
        cached = self._cache_get("sector_fund_flow", ttl=60)
        if cached:
            return cached

        try:
            # 获取行业板块资金流向
            df = ak.stock_sector_fund_flow_rank(indicator="今日")
            
            sectors = []
            for _, row in df.iterrows():
                sector = str(row.get("名称", ""))
                if not sector:
                    continue
                
                inflow = float(row.get("主力净流入-净额", 0)) / 100000000  # 转为亿
                change_pct = float(row.get("涨跌幅", 0))
                
                sectors.append({
                    "sector": sector,
                    "inflow": max(0, inflow),
                    "outflow": max(0, -inflow),
                    "net": round(inflow, 2),
                    "change_pct": change_pct,
                    "limit_up_count": 0,  # 需要额外查询
                })
            
            sectors.sort(key=lambda x: x["net"], reverse=True)
            
            if sectors:
                self._cache_set("sector_fund_flow", sectors, ttl=60)
                logger.info(f"Got {len(sectors)} sectors fund flow from akshare")
                return sectors
            
        except Exception as e:
            logger.warning(f"Failed to get sector fund flow from akshare: {e}")
        
        return []

    async def get_market_overview(self) -> Dict:
        """获取市场总览数据"""
        cached = self._cache_get("market_overview", ttl=30)
        if cached:
            return cached

        try:
            # 获取涨跌统计
            df = ak.stock_market_activity_legu()
            
            stats = {}
            if not df.empty:
                row = df.iloc[0]
                stats = {
                    "total_stocks": int(row.get("总股票数", 5200)),
                    "rise_count": int(row.get("上涨数", 0)),
                    "fall_count": int(row.get("下跌数", 0)),
                    "flat_count": int(row.get("平盘数", 0)),
                    "limit_up_count": int(row.get("涨停数", 0)),
                    "limit_down_count": int(row.get("跌停数", 0)),
                }
            
            # 获取指数
            indices = await self.get_market_indices()
            
            # 计算总成交额
            total_amount = sum(idx.get("amount", 0) for idx in indices)
            total_volume = sum(idx.get("volume", 0) for idx in indices)
            
            data = {
                "date": date.today().isoformat(),
                "timestamp": datetime.now().isoformat(),
                "indices": indices,
                "stats": {
                    **stats,
                    "total_volume": total_volume,
                    "total_amount": total_amount * 100000000,  # 转为元
                },
                "source": "akshare",
            }
            
            self._cache_set("market_overview", data, ttl=30)
            return data
            
        except Exception as e:
            logger.warning(f"Failed to get market overview from akshare: {e}")
            return {
                "date": date.today().isoformat(),
                "timestamp": datetime.now().isoformat(),
                "indices": [],
                "stats": {},
                "source": "akshare_error",
            }

    async def get_stock_detail(self, ticker: str) -> Dict:
        """获取个股详情"""
        # 移除后缀获取纯代码
        code = ticker.replace(".SH", "").replace(".SZ", "")
        cached = self._cache_get(f"stock_{code}", ttl=60)
        if cached:
            return cached

        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            for _, row in df.iterrows():
                if str(row.get("代码", "")) == code:
                    data = {
                        "ticker": ticker,
                        "name": str(row.get("名称", "")),
                        "current": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌额", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "open": float(row.get("今开", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "pre_close": float(row.get("昨收", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "turnover": float(row.get("换手率", 0)),
                        "pe_ratio": float(row.get("市盈率-动态", 0)),
                        "pb_ratio": float(row.get("市净率", 0)),
                        "market_cap": float(row.get("总市值", 0)),
                    }
                    self._cache_set(f"stock_{code}", data, ttl=60)
                    return data
            
        except Exception as e:
            logger.warning(f"Failed to get stock detail for {ticker}: {e}")
        
        return {}

    async def get_stock_kline(self, ticker: str, period: str = "daily", days: int = 30) -> List[Dict]:
        """获取个股K线数据"""
        code = ticker.replace(".SH", "").replace(".SZ", "")
        cache_key = f"kline_{code}_{period}_{days}"
        cached = self._cache_get(cache_key, ttl=300)
        if cached:
            return cached

        try:
            end = date.today().strftime("%Y%m%d")
            start = (date.today() - timedelta(days=days + 10)).strftime("%Y%m%d")
            
            period_map = {
                "daily": "daily",
                "weekly": "weekly",
                "monthly": "monthly",
                "5min": "5",
                "15min": "15",
                "30min": "30",
                "60min": "60",
            }
            
            ak_period = period_map.get(period, "daily")
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=ak_period,
                start_date=start,
                end_date=end,
                adjust="qfq"
            )
            
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    "date": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                })
            
            if klines:
                self._cache_set(cache_key, klines, ttl=300)
                logger.info(f"Got {len(klines)} klines for {ticker}")
                return klines
            
        except Exception as e:
            logger.warning(f"Failed to get kline for {ticker}: {e}")
        
        return []


# 全局实例
akshare_service = AkShareService()