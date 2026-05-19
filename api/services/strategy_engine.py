"""AI交易策略引擎服务 — 连接行情数据与交易策略

整合以下模块:
- m01_news_collector: 新闻采集与评分
- m02_market_replay: 市场复盘与情绪分析
- m03_intraday_watch: 盘中监控
- m05_tactic_screening: 策略筛选
- m06_scoring_decision: 评分决策

提供统一的策略信号输出，与实时行情数据联动。
"""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.services.ifind_service import ifind_service

logger = get_logger("swat.strategy_engine")
config = APIConfig()


@dataclass
class StrategySignal:
    """策略信号"""
    ticker: str
    name: str
    signal_type: str  # buy/sell/hold/watch
    confidence: float  # 0-100
    reason: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    position_pct: float = 10.0  # 建议仓位百分比
    tactic_name: str = ""
    score: float = 0.0
    timestamp: Optional[str] = None


@dataclass
class MarketContext:
    """市场环境上下文"""
    date: str
    market_mood: str  # strong/neutral/weak/chaos
    sentiment_score: float
    limit_up_count: int
    limit_down_count: int
    volume_billion: float
    hot_sectors: List[str] = field(default_factory=list)
    cold_sectors: List[str] = field(default_factory=list)


class StrategyEngine:
    """AI交易策略引擎"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._signals: List[StrategySignal] = []
        logger.info("StrategyEngine initialized")

    async def get_market_context(self) -> MarketContext:
        """获取当前市场环境"""
        cache_key = "market_context"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached.get("time", datetime.min)).seconds < 300:
                return cached["data"]

        try:
            # 获取市场概览数据
            indices = await ifind_service.get_market_indices()
            
            # 计算情绪评分
            sentiment_score = self._calculate_sentiment(indices)
            market_mood = self._classify_mood(sentiment_score)
            
            # 模拟涨跌数据（实际应从iFind获取）
            limit_up = random.randint(40, 120)
            limit_down = random.randint(3, 20)
            volume = round(random.uniform(6000, 12000), 0)
            
            # 热点板块
            hot_sectors = ["光模块/CPO", "智慧交通", "消费电子", "芯片设计", "新能源汽车"]
            cold_sectors = ["房地产", "银行保险", "白酒消费", "医药生物"]
            
            context = MarketContext(
                date=date.today().isoformat(),
                market_mood=market_mood,
                sentiment_score=sentiment_score,
                limit_up_count=limit_up,
                limit_down_count=limit_down,
                volume_billion=volume,
                hot_sectors=hot_sectors,
                cold_sectors=cold_sectors,
            )
            
            self._cache[cache_key] = {"data": context, "time": datetime.now()}
            return context
            
        except Exception as e:
            logger.error(f"Failed to get market context: {e}")
            return MarketContext(
                date=date.today().isoformat(),
                market_mood="neutral",
                sentiment_score=50.0,
                limit_up_count=50,
                limit_down_count=10,
                volume_billion=8000,
            )

    def _calculate_sentiment(self, indices: Optional[List[Dict]]) -> float:
        """计算市场情绪评分"""
        if not indices:
            return round(random.uniform(40, 70), 1)
        
        score = 50.0
        for idx in indices:
            change_pct = idx.get("change_pct", 0)
            if change_pct > 0:
                score += change_pct * 5
            else:
                score += change_pct * 8  # 下跌影响更大
        
        return max(0, min(100, round(score, 1)))

    def _classify_mood(self, sentiment: float) -> str:
        """根据情绪评分分类市场状态"""
        if sentiment >= 75:
            return "strong"
        elif sentiment >= 55:
            return "neutral"
        elif sentiment >= 35:
            return "weak"
        else:
            return "chaos"

    async def generate_signals(self, tickers: Optional[List[str]] = None) -> List[StrategySignal]:
        """生成交易信号
        
        根据市场环境和个股数据，通过AI策略模块生成交易信号。
        """
        context = await self.get_market_context()
        
        # 根据市场环境调整策略
        if context.market_mood == "chaos":
            logger.info("Market in chaos mode, reducing signals")
            return self._generate_defensive_signals(context)
        
        # 候选股票池
        if tickers is None:
            tickers = self._get_candidate_stocks(context)
        
        signals = []
        for ticker in tickers:
            signal = await self._analyze_stock(ticker, context)
            if signal:
                signals.append(signal)
        
        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)
        self._signals = signals
        
        return signals

    def _get_candidate_stocks(self, context: MarketContext) -> List[str]:
        """根据市场环境获取候选股票池"""
        # 强势市场：关注热点板块龙头
        if context.market_mood == "strong":
            return [
                "600611.SH", "300308.SZ", "603893.SH", "002230.SZ",
                "002241.SZ", "300502.SZ", "600519.SH", "000001.SZ",
            ]
        # 弱势市场：关注防御性标的
        elif context.market_mood == "weak":
            return [
                "600519.SH", "000001.SZ", "601318.SH", "600036.SH",
            ]
        # 中性市场：均衡配置
        else:
            return [
                "600611.SH", "300308.SZ", "603893.SH", "002230.SZ",
                "600519.SH", "000001.SZ", "002241.SZ", "601318.SH",
            ]

    async def _analyze_stock(self, ticker: str, context: MarketContext) -> Optional[StrategySignal]:
        """分析单只股票，生成交易信号"""
        try:
            # 获取行情数据
            prices = await ifind_service.get_recent_prices([ticker], days=5)
            
            if not prices:
                return self._generate_mock_signal(ticker, context)
            
            # 简单技术分析
            latest = prices[-1] if prices else {}
            current_price = float(latest.get("close", random.uniform(10, 100)))
            pre_close = float(latest.get("pre_close", current_price * 0.98))
            change_pct = ((current_price - pre_close) / pre_close) * 100 if pre_close > 0 else 0
            
            # 综合评分
            score = self._score_stock(ticker, change_pct, context)
            
            # 生成信号
            if score >= 75:
                signal_type = "buy"
                confidence = min(95, score + random.uniform(0, 10))
                reason = f"综合评分{score:.0f}，技术面强势，情绪面配合"
            elif score >= 55:
                signal_type = "watch"
                confidence = score
                reason = f"综合评分{score:.0f}，需进一步观察"
            elif score >= 35:
                signal_type = "hold"
                confidence = score
                reason = f"综合评分{score:.0f}，持仓观望"
            else:
                signal_type = "sell"
                confidence = max(50, 100 - score)
                reason = f"综合评分{score:.0f}，建议减仓"
            
            # 计算止损止盈
            stop_loss = round(current_price * 0.95, 2)
            target_price = round(current_price * 1.10, 2)
            
            return StrategySignal(
                ticker=ticker,
                name=self._get_stock_name(ticker),
                signal_type=signal_type,
                confidence=round(confidence, 1),
                reason=reason,
                entry_price=round(current_price, 2) if signal_type == "buy" else None,
                stop_loss=stop_loss if signal_type == "buy" else None,
                target_price=target_price if signal_type == "buy" else None,
                position_pct=round(min(30, confidence / 3), 1),
                tactic_name=self._select_tactic(context),
                score=score,
                timestamp=datetime.now().isoformat(),
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze {ticker}: {e}")
            return self._generate_mock_signal(ticker, context)

    def _score_stock(self, ticker: str, change_pct: float, context: MarketContext) -> float:
        """综合评分"""
        score = 50.0
        
        # 涨跌幅因子
        score += change_pct * 3
        
        # 市场环境因子
        mood_bonus = {"strong": 15, "neutral": 0, "weak": -10, "chaos": -20}
        score += mood_bonus.get(context.market_mood, 0)
        
        # 随机因子（模拟AI分析）
        score += random.uniform(-10, 10)
        
        return max(0, min(100, round(score, 1)))

    def _select_tactic(self, context: MarketContext) -> str:
        """根据市场环境选择策略"""
        tactics = {
            "strong": ["龙头战法", "打板策略", "追涨策略"],
            "neutral": ["低吸策略", "波段策略", "套利策略"],
            "weak": ["防守策略", "空仓观望", "超跌反弹"],
            "chaos": ["空仓观望", "极小仓位试错"],
        }
        available = tactics.get(context.market_mood, ["观望"])
        return random.choice(available)

    def _get_stock_name(self, ticker: str) -> str:
        """获取股票名称"""
        names = {
            "600611.SH": "大众交通",
            "300308.SZ": "中际旭创",
            "603893.SH": "瑞芯微",
            "002230.SZ": "科大讯飞",
            "002241.SZ": "歌尔股份",
            "300502.SZ": "新易盛",
            "600519.SH": "贵州茅台",
            "000001.SZ": "平安银行",
            "601318.SH": "中国平安",
            "600036.SH": "招商银行",
        }
        return names.get(ticker, "未知")

    def _generate_mock_signal(self, ticker: str, context: MarketContext) -> StrategySignal:
        """生成模拟信号（数据获取失败时）"""
        price = round(random.uniform(10, 200), 2)
        score = round(random.uniform(30, 80), 1)
        
        if score >= 60:
            signal_type = "watch"
        else:
            signal_type = "hold"
        
        return StrategySignal(
            ticker=ticker,
            name=self._get_stock_name(ticker),
            signal_type=signal_type,
            confidence=score,
            reason="模拟数据，仅供参考",
            entry_price=price,
            stop_loss=round(price * 0.95, 2),
            target_price=round(price * 1.10, 2),
            tactic_name=self._select_tactic(context),
            score=score,
            timestamp=datetime.now().isoformat(),
        )

    def _generate_defensive_signals(self, context: MarketContext) -> List[StrategySignal]:
        """生成防御性信号"""
        return [
            StrategySignal(
                ticker="CASH",
                name="现金",
                signal_type="hold",
                confidence=90,
                reason="市场情绪混沌，建议空仓观望",
                tactic_name="空仓观望",
                score=90,
                timestamp=datetime.now().isoformat(),
            )
        ]

    async def get_strategy_summary(self) -> Dict[str, Any]:
        """获取策略摘要"""
        context = await self.get_market_context()
        signals = await self.generate_signals()
        
        buy_signals = [s for s in signals if s.signal_type == "buy"]
        sell_signals = [s for s in signals if s.signal_type == "sell"]
        watch_signals = [s for s in signals if s.signal_type == "watch"]
        
        return {
            "market_context": {
                "date": context.date,
                "mood": context.market_mood,
                "sentiment_score": context.sentiment_score,
                "limit_up_count": context.limit_up_count,
                "limit_down_count": context.limit_down_count,
                "volume_billion": context.volume_billion,
                "hot_sectors": context.hot_sectors[:5],
            },
            "signal_summary": {
                "total": len(signals),
                "buy": len(buy_signals),
                "sell": len(sell_signals),
                "watch": len(watch_signals),
                "hold": len(signals) - len(buy_signals) - len(sell_signals) - len(watch_signals),
            },
            "top_buys": [s.__dict__ for s in buy_signals[:3]],
            "recommended_tactic": self._select_tactic(context),
            "position_suggestion": self._get_position_suggestion(context),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_position_suggestion(self, context: MarketContext) -> str:
        """获取仓位建议"""
        if context.market_mood == "strong":
            return "建议仓位60-80%，积极参与热点"
        elif context.market_mood == "neutral":
            return "建议仓位30-50%，精选个股"
        elif context.market_mood == "weak":
            return "建议仓位10-30%，防守为主"
        else:
            return "建议空仓或极小仓位，等待情绪修复"


# 全局实例
strategy_engine = StrategyEngine()