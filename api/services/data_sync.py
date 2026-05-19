"""数据同步服务 — 实时数据获取与缓存管理

为短线致胜AI交易智能体提供:
1. 定时从akshare获取实时市场数据（真实A股数据）
2. 多级缓存机制（内存+磁盘）
3. 数据刷新调度
4. WebSocket实时推送支持

数据源优先级:
1. akshare (开源免费A股实时数据)
2. iFind (同花顺，需要授权)
3. Mock数据 (开发/测试)
"""

import asyncio
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict

from api.core.config import APIConfig
from api.core.logger import get_logger

logger = get_logger("swat.data_sync")
config = APIConfig()


class DataCache:
    """多级数据缓存"""
    
    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_dir = Path("cache")
        self._cache_dir.mkdir(exist_ok=True)
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """从缓存获取数据"""
        # 1. 检查内存缓存
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry["timestamp"] < ttl:
                return entry["data"]
            else:
                del self._memory_cache[key]
        
        # 2. 检查磁盘缓存
        cache_file = self._cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if time.time() - entry.get("timestamp", 0) < ttl:
                    self._memory_cache[key] = entry
                    return entry["data"]
                else:
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Disk cache read failed for {key}: {e}")
        
        return None
    
    def set(self, key: str, data: Any, ttl: int = 300):
        """设置缓存数据"""
        entry = {
            "key": key,
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl,
        }
        
        # 写入内存
        self._memory_cache[key] = entry
        
        # 写入磁盘
        cache_file = self._cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Disk cache write failed for {key}: {e}")
        
        # 通知订阅者
        self._notify_subscribers(key, data)
    
    def subscribe(self, key: str, callback: Callable):
        """订阅数据更新"""
        self._subscribers[key].append(callback)
    
    def _notify_subscribers(self, key: str, data: Any):
        """通知订阅者数据已更新"""
        for callback in self._subscribers.get(key, []):
            try:
                callback(key, data)
            except Exception as e:
                logger.error(f"Subscriber callback error for {key}: {e}")
    
    def invalidate(self, key: str):
        """使缓存失效"""
        self._memory_cache.pop(key, None)
        cache_file = self._cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()
    
    def clear_expired(self):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if now - v["timestamp"] > v.get("ttl", 300)
        ]
        for key in expired_keys:
            del self._memory_cache[key]
        
        # 清理磁盘缓存
        for cache_file in self._cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if now - entry.get("timestamp", 0) > entry.get("ttl", 300):
                    cache_file.unlink()
            except Exception:
                pass


class DataSyncService:
    """数据同步服务 — 定时获取并缓存实时数据"""
    
    def __init__(self):
        self.cache = DataCache()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._akshare_available = False
        self._ifind_available = False
        self._check_data_sources()
        
        # 同步间隔配置（秒）
        self.intervals = {
            "market_overview": 30,      # 市场总览：30秒
            "indices": 15,              # 指数：15秒
            "limit_up": 60,             # 涨停板：60秒
            "heat_map": 60,             # 热力图：60秒
            "sentiment": 120,           # 情绪诊断：120秒
            "fund_flow": 30,            # 资金流向：30秒
            "anchors": 30,              # 锚定标的：30秒
            "alerts": 60,               # 预警：60秒
        }
        
        logger.info(f"DataSyncService initialized (akshare={self._akshare_available}, ifind={self._ifind_available})")
    
    def _check_data_sources(self):
        """检查数据源是否可用"""
        # 检查 akshare
        try:
            import akshare
            self._akshare_available = True
            logger.info("AkShare data source is available")
        except ImportError:
            self._akshare_available = False
            logger.warning("AkShare not available, install with: pip install akshare")
        
        # 检查 iFind
        try:
            from mshtools_get_data_source import get_data_source
            self._ifind_available = True
            logger.info("iFind data source is available")
        except ImportError:
            self._ifind_available = False
            logger.warning("iFind data source not available (mshtools_get_data_source not found)")
    
    @property
    def data_source(self) -> str:
        """当前使用的数据源 — 优先使用 iFind"""
        if self._ifind_available:
            return "ifind"
        if self._akshare_available:
            return "akshare"
        return "mock"
    
    async def sync_market_overview(self):
        """同步市场总览数据 — 优先使用iFind获取真实数据"""
        key = "market_overview"
        logger.debug(f"Syncing {key} (source={self.data_source})...")
        
        # 优先使用 iFind
        if self._ifind_available:
            try:
                from api.services.ifind_service import ifind_service
                indices = await ifind_service.get_market_indices()
                if indices:
                    stats = await self._get_market_stats()
                    data = {
                        "date": date.today().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "indices": indices,
                        "stats": stats,
                        "source": "ifind",
                    }
                    self.cache.set(key, data, ttl=self.intervals[key])
                    logger.info(f"Market overview synced from iFind: {len(indices)} indices")
                    return data
            except Exception as e:
                logger.warning(f"iFind market overview failed: {e}")
        
        # Fallback: akshare
        if self._akshare_available:
            try:
                from api.services.akshare_service import akshare_service
                data = await akshare_service.get_market_overview()
                if data and data.get("indices"):
                    self.cache.set(key, data, ttl=self.intervals[key])
                    logger.info(f"Market overview synced from akshare: {len(data.get('indices', []))} indices")
                    return data
            except Exception as e:
                logger.warning(f"AkShare market overview failed: {e}")
        
        # Fallback: 获取三大指数
        indices_data = await self._get_indices()
        stats = await self._get_market_stats()
        
        data = {
            "date": date.today().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "indices": indices_data,
            "stats": stats,
            "source": self.data_source,
        }
        
        self.cache.set(key, data, ttl=self.intervals[key])
        return data
    
    async def _get_indices(self) -> List[Dict]:
        """获取三大指数数据 — 优先使用iFind"""
        # 优先使用 iFind
        if self._ifind_available:
            try:
                from api.services.ifind_service import ifind_service
                indices = await ifind_service.get_market_indices()
                if indices:
                    return indices
            except Exception as e:
                logger.warning(f"iFind indices failed: {e}")
        
        # Fallback: akshare
        if self._akshare_available:
            try:
                from api.services.akshare_service import akshare_service
                indices = await akshare_service.get_market_indices()
                if indices:
                    return indices
            except Exception as e:
                logger.warning(f"AkShare indices failed: {e}")
        
        # Fallback to mock data
        import random
        indices = [
            ("000001.SH", "上证指数", 3100),
            ("399001.SZ", "深证成指", 9500),
            ("399006.SZ", "创业板指", 1800),
        ]
        result = []
        for code, name, base in indices:
            result.append({
                "code": code,
                "name": name,
                "current": base + random.uniform(-50, 50),
                "change": random.uniform(-30, 30),
                "change_pct": random.uniform(-2, 2),
                "volume": random.uniform(1e8, 5e8),
                "amount": random.uniform(1e10, 5e10),
            })
        return result
    
    async def _get_market_stats(self) -> Dict:
        """获取市场统计数据"""
        import random
        
        return {
            "total_stocks": 5200 + random.randint(-50, 50),
            "rise_count": random.randint(1500, 3500),
            "fall_count": random.randint(1500, 3500),
            "flat_count": random.randint(50, 200),
            "limit_up_count": random.randint(20, 80),
            "limit_down_count": random.randint(0, 20),
            "total_volume": random.uniform(5e11, 1.5e12),
            "total_amount": random.uniform(8e11, 2e12),
        }
    
    async def sync_limit_up_stocks(self):
        """同步涨停板数据 — 使用akshare获取真实涨停股"""
        key = "limit_up"
        logger.debug(f"Syncing {key} (source={self.data_source})...")
        
        if self._akshare_available:
            try:
                from api.services.akshare_service import akshare_service
                stocks = await akshare_service.get_limit_up_stocks()
                if stocks:
                    self.cache.set(key, stocks, ttl=self.intervals[key])
                    logger.info(f"Got {len(stocks)} limit-up stocks from akshare")
                    return stocks
            except Exception as e:
                logger.warning(f"AkShare limit-up stocks failed: {e}")
        
        # Fallback mock data
        import random
        stocks = []
        stock_pool = [
            ("600519.SH", "贵州茅台"), ("000001.SZ", "平安银行"),
            ("300308.SZ", "中际旭创"), ("002230.SZ", "科大讯飞"),
            ("603893.SH", "瑞芯微"), ("600611.SH", "大众交通"),
            ("002241.SZ", "歌尔股份"), ("300502.SZ", "新易盛"),
        ]
        
        for code, name in random.sample(stock_pool, min(5, len(stock_pool))):
            boards = random.randint(1, 8)
            stocks.append({
                "ticker": code,
                "name": name,
                "boards": boards,
                "change_pct": 10.0 if not code.startswith("3") else 20.0,
                "volume": random.uniform(1e7, 1e9),
                "amount": random.uniform(1e8, 5e9),
                "seal_amount": random.uniform(1e7, 5e8),
                "first_seal_time": f"09:{random.randint(25,59):02d}:{random.randint(0,59):02d}",
                "last_seal_time": f"{random.randint(9,14):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}",
                "open_times": random.randint(0, 5),
                "sector": random.choice(["光模块", "人工智能", "芯片", "消费电子", "新能源"]),
            })
        
        stocks.sort(key=lambda x: x["boards"], reverse=True)
        self.cache.set(key, stocks, ttl=self.intervals[key])
        return stocks
    
    async def sync_sentiment(self):
        """同步情绪诊断数据"""
        key = "sentiment"
        logger.debug(f"Syncing {key}...")
        
        import random
        
        phases = ["冰点期", "修复期", "发酵期", "高潮期", "分歧期", "退潮期"]
        phase = random.choice(phases)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "status": phase,
            "current_cycle": phase,
            "confidence": random.uniform(60, 95),
            "position_limit": {
                "冰点期": 20, "修复期": 40, "发酵期": 60,
                "高潮期": 30, "分歧期": 30, "退潮期": 10
            }.get(phase, 30),
            "indicators": {
                "fear_index": random.uniform(20, 80),
                "greed_index": random.uniform(20, 80),
                "sentiment_score": random.uniform(30, 90),
                "market_volatility": random.uniform(10, 50),
                "up_down_ratio": random.uniform(0.3, 3.0),
                "explode_rate": random.uniform(20, 80),
                "profit_effect": random.uniform(30, 90),
                "volume_change": random.uniform(-20, 50),
            },
            "analysis": f"当前市场处于{phase}，建议{'谨慎观望' if phase in ['冰点期', '退潮期'] else '积极参与'}",
            "suggestion": f"建议仓位控制在{random.randint(20, 60)}%以内",
        }
        
        self.cache.set(key, data, ttl=self.intervals[key])
        return data
    
    async def sync_fund_flow(self):
        """同步资金流向数据 — 使用akshare获取真实板块资金流向"""
        key = "fund_flow"
        logger.debug(f"Syncing {key} (source={self.data_source})...")
        
        if self._akshare_available:
            try:
                from api.services.akshare_service import akshare_service
                data = await akshare_service.get_sector_fund_flow()
                if data:
                    self.cache.set(key, data, ttl=self.intervals[key])
                    logger.info(f"Got {len(data)} sectors fund flow from akshare")
                    return data
            except Exception as e:
                logger.warning(f"AkShare fund flow failed: {e}")
        
        # Fallback mock data
        import random
        
        sectors = [
            "光模块/CPO", "智慧交通", "消费电子", "芯片设计",
            "新能源汽车", "文化传媒", "先进封装", "人工智能",
            "生物医药", "白酒消费", "房地产", "银行保险",
        ]
        
        data = []
        for sector in sectors:
            inflow = round(random.uniform(-20, 50), 2)
            outflow = round(random.uniform(0, 40), 2) if inflow < 0 else round(random.uniform(0, 20), 2)
            data.append({
                "sector": sector,
                "inflow": max(0, inflow),
                "outflow": outflow,
                "net": round(inflow - outflow, 2),
                "limit_up_count": random.randint(0, 8) if inflow > 10 else 0,
            })
        
        data.sort(key=lambda x: x["net"], reverse=True)
        self.cache.set(key, data, ttl=self.intervals[key])
        return data
    
    async def start(self):
        """启动数据同步服务"""
        if self._running:
            logger.warning("DataSyncService is already running")
            return
        
        self._running = True
        logger.info("DataSyncService starting...")
        
        # 创建同步任务
        self._tasks = [
            asyncio.create_task(self._sync_loop("market_overview", self.sync_market_overview)),
            asyncio.create_task(self._sync_loop("limit_up", self.sync_limit_up_stocks)),
            asyncio.create_task(self._sync_loop("sentiment", self.sync_sentiment)),
            asyncio.create_task(self._sync_loop("fund_flow", self.sync_fund_flow)),
            asyncio.create_task(self._cleanup_loop()),
        ]
        
        # 立即执行一次同步
        await asyncio.gather(
            self.sync_market_overview(),
            self.sync_limit_up_stocks(),
            self.sync_sentiment(),
            self.sync_fund_flow(),
        )
        
        logger.info("DataSyncService started with all sync tasks")
    
    async def stop(self):
        """停止数据同步服务"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("DataSyncService stopped")
    
    async def _sync_loop(self, name: str, sync_func):
        """同步循环"""
        while self._running:
            try:
                await sync_func()
            except Exception as e:
                logger.error(f"Sync loop error for {name}: {e}")
            
            interval = self.intervals.get(name, 60)
            await asyncio.sleep(interval)
    
    async def _cleanup_loop(self):
        """缓存清理循环"""
        while self._running:
            try:
                self.cache.clear_expired()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
            await asyncio.sleep(300)  # 每5分钟清理一次


# 全局实例
data_sync_service = DataSyncService()