"""游资共识分析引擎

功能:
    1. 多游资共识标的挖掘 — 当≥3位游资同时看好某标的时，产生共识信号
    2. 分歧预警 — 当游资之间对某标的看法分歧较大时发出预警
    3. 共识强度分级 — A/B/C/D 四级共识

共识逻辑:
    - 强共识(≥4位游资): 标的有极高确定性
    - 中共识(3位游资): 标的具备较好机会
    - 弱共识(2位游资): 可适当关注
    - 无共识: 观望为主
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set

from api.core.logger import get_logger

from .fingerprints import registry
from .recommender import StockYingYouMatch, YingYouRecommender

logger = get_logger("swat.m04.consensus")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class ConsensusSignal:
    """共识信号"""
    ticker: str
    name: str
    consensus_level: str       # A/B/C/D
    yingyou_names: List[str]   # 共识游资列表
    avg_score: float           # 平均匹配度
    max_score: float           # 最高匹配度
    agreement_score: float     # 一致性评分 0-100
    summary: str               # 共识总结
    risk_note: str             # 风险注释
    priority: int = 0          # 优先级


@dataclass
class DivergenceAlert:
    """分歧预警"""
    ticker: str
    name: str
    divergence_score: float    # 分歧度 0-100
    bull_yingyou: List[str]    # 看好游资
    bear_yingyou: List[str]    # 看空游资
    reason: str                # 分歧原因
    alert_level: str           # 预警级别
    suggestion: str            # 建议


@dataclass
class ConsensusReport:
    """共识分析报告"""
    timestamp: str
    strong_consensus: List[ConsensusSignal]   # 强共识(≥4位)
    medium_consensus: List[ConsensusSignal]   # 中共识(3位)
    weak_consensus: List[ConsensusSignal]     # 弱共识(2位)
    divergence_alerts: List[DivergenceAlert]  # 分歧预警
    summary: str                              # 总结


# ═══════════════════════════════════════════════════════════
# 共识分析器
# ═══════════════════════════════════════════════════════════

class ConsensusAnalyzer:
    """游资共识分析器"""

    # 共识阈值
    CONSENSUS_STRONG = 4    # 强共识: ≥4位游资
    CONSENSUS_MEDIUM = 3    # 中共识: 3位游资
    CONSENSUS_WEAK = 2      # 弱共识: 2位游资

    # 匹配度阈值
    SCORE_THRESHOLD = 50.0  # 最低匹配度

    def __init__(self):
        self.recommender = YingYouRecommender()

    async def analyze(
        self,
        tickers: List[Dict[str, str]],
        score_threshold: float = 50.0,
    ) -> ConsensusReport:
        """分析多个标的的游资共识"""
        logger.info(f"Analyzing consensus for {len(tickers)} tickers")

        # 获取所有标的的匹配结果
        all_matches = await self.recommender.recommend_batch(tickers)

        # 分析共识
        consensus_signals = self._find_consensus(all_matches, score_threshold)
        divergence_alerts = self._find_divergence(all_matches)

        # 分级
        strong = [s for s in consensus_signals if s.consensus_level == "A"]
        medium = [s for s in consensus_signals if s.consensus_level == "B"]
        weak = [s for s in consensus_signals if s.consensus_level == "C"]

        # 按优先级排序
        strong.sort(key=lambda x: x.priority, reverse=True)
        medium.sort(key=lambda x: x.priority, reverse=True)
        weak.sort(key=lambda x: x.priority, reverse=True)

        summary = self._gen_summary(strong, medium, weak, divergence_alerts)

        return ConsensusReport(
            timestamp=datetime.now().isoformat(),
            strong_consensus=strong,
            medium_consensus=medium,
            weak_consensus=weak,
            divergence_alerts=divergence_alerts,
            summary=summary,
        )

    async def analyze_single(
        self,
        ticker: str,
        name: str = "",
        score_threshold: float = 50.0,
    ) -> Optional[ConsensusSignal]:
        """分析单个标的的游资共识"""
        matches = await self.recommender.recommend(ticker, name)
        relevant = [m for m in matches if m.match_score >= score_threshold]

        if len(relevant) < self.CONSENSUS_WEAK:
            return None

        return self._create_consensus_signal(ticker, name, relevant)

    def _find_consensus(
        self,
        all_matches: Dict[str, List[StockYingYouMatch]],
        threshold: float,
    ) -> List[ConsensusSignal]:
        """从所有匹配结果中找出共识标的"""
        signals = []

        for ticker, matches in all_matches.items():
            relevant = [m for m in matches if m.match_score >= threshold]

            if len(relevant) >= self.CONSENSUS_WEAK:
                name = relevant[0].name if relevant else ""
                signal = self._create_consensus_signal(ticker, name, relevant)
                signals.append(signal)

        return signals

    def _create_consensus_signal(
        self,
        ticker: str,
        name: str,
        matches: List[StockYingYouMatch],
    ) -> ConsensusSignal:
        """创建共识信号"""
        names = [m.yingyou_name for m in matches]
        scores = [m.match_score for m in matches]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0

        # 一致性评分
        if len(scores) >= 2:
            std = (sum((s - avg_score) ** 2 for s in scores) / len(scores)) ** 0.5
            agreement = max(0, 100 - std * 2)
        else:
            agreement = 100.0

        # 共识级别
        count = len(names)
        if count >= self.CONSENSUS_STRONG:
            level = "A"
        elif count >= self.CONSENSUS_MEDIUM:
            level = "B"
        elif count >= self.CONSENSUS_WEAK:
            level = "C"
        else:
            level = "D"

        # 共识总结
        summary = self._gen_consensus_summary(names, avg_score, level)
        risk_note = self._gen_risk_note(level, agreement)
        priority = int(avg_score * count)

        return ConsensusSignal(
            ticker=ticker,
            name=name,
            consensus_level=level,
            yingyou_names=names,
            avg_score=round(avg_score, 1),
            max_score=round(max_score, 1),
            agreement_score=round(agreement, 1),
            summary=summary,
            risk_note=risk_note,
            priority=priority,
        )

    def _find_divergence(
        self,
        all_matches: Dict[str, List[StockYingYouMatch]],
    ) -> List[DivergenceAlert]:
        """找出分歧标的"""
        alerts = []

        for ticker, matches in all_matches.items():
            if len(matches) < 4:
                continue

            # 分组: 看好(>60) / 中性(40-60) / 看空(<40)
            bull = [m for m in matches if m.match_score > 60]
            neutral = [m for m in matches if 40 <= m.match_score <= 60]
            bear = [m for m in matches if m.match_score < 40]

            # 分歧条件: 既有看好的也有看空的
            if bull and bear:
                divergence_score = self._calc_divergence(matches)
                if divergence_score > 40:
                    name = matches[0].name if matches else ""
                    alert = DivergenceAlert(
                        ticker=ticker,
                        name=name,
                        divergence_score=round(divergence_score, 1),
                        bull_yingyou=[m.yingyou_name for m in bull],
                        bear_yingyou=[m.yingyou_name for m in bear],
                        reason=f"{len(bull)}位游资看好 vs {len(bear)}位游资看空",
                        alert_level="高" if divergence_score > 60 else "中",
                        suggestion="分歧较大，谨慎参与，等待方向明确",
                    )
                    alerts.append(alert)

        # 按分歧度排序
        alerts.sort(key=lambda x: x.divergence_score, reverse=True)
        return alerts

    def _calc_divergence(self, matches: List[StockYingYouMatch]) -> float:
        """计算分歧度 0-100"""
        if len(matches) < 2:
            return 0.0

        scores = [m.match_score for m in matches]
        avg = sum(scores) / len(scores)

        # 计算标准差
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5

        # 标准差映射到 0-100
        return min(100, std * 2)

    def _gen_consensus_summary(
        self,
        names: List[str],
        avg_score: float,
        level: str,
    ) -> str:
        """生成共识总结"""
        level_desc = {
            "A": "强共识",
            "B": "中共识",
            "C": "弱共识",
            "D": "无共识",
        }

        names_str = "、".join(names)
        return (
            f"{level_desc.get(level, '')}: {names_str}共{len(names)}位游资看好，"
            f"平均匹配度{avg_score:.0f}分"
        )

    def _gen_risk_note(self, level: str, agreement: float) -> str:
        """生成风险注释"""
        if level == "A":
            return "多游资共识，确定性较高，但仍需控制仓位"
        elif level == "B":
            return "有游资共识，可适当参与"
        elif agreement < 50:
            return "游资间分歧较大，谨慎参与"
        return "共识较弱，观望为主"

    def _gen_summary(
        self,
        strong: List[ConsensusSignal],
        medium: List[ConsensusSignal],
        weak: List[ConsensusSignal],
        alerts: List[DivergenceAlert],
    ) -> str:
        """生成总结"""
        parts = []
        if strong:
            names = "、".join([s.ticker for s in strong[:3]])
            parts.append(f"强共识标的({len(strong)}只): {names}")
        if medium:
            names = "、".join([s.ticker for s in medium[:3]])
            parts.append(f"中共识标的({len(medium)}只): {names}")
        if alerts:
            parts.append(f"分歧预警({len(alerts)}只): 游资间看法分化")

        if not parts:
            return "当前暂无游资共识标的，市场分歧较大或机会不明确"

        return "; ".join(parts)


# ═══════════════════════════════════════════════════════════
# 共识标的池
# ═══════════════════════════════════════════════════════════

class ConsensusPool:
    """共识标的池 — 持续追踪游资共识标的"""

    def __init__(self):
        self.analyzer = ConsensusAnalyzer()
        self._pool: Dict[str, ConsensusSignal] = {}
        self._last_update: Optional[str] = None

    async def refresh(self, tickers: List[Dict[str, str]]) -> ConsensusReport:
        """刷新共识池"""
        report = await self.analyzer.analyze(tickers)

        # 更新池
        self._pool = {}
        for signal in (report.strong_consensus + report.medium_consensus):
            self._pool[signal.ticker] = signal

        self._last_update = datetime.now().isoformat()
        logger.info(f"Consensus pool refreshed: {len(self._pool)} tickers")
        return report

    def get_pool(self) -> Dict[str, ConsensusSignal]:
        """获取当前共识池"""
        return self._pool.copy()

    def get_by_level(self, level: str) -> List[ConsensusSignal]:
        """按级别获取共识标的"""
        return [s for s in self._pool.values() if s.consensus_level == level]

    def has_consensus(self, ticker: str, min_level: str = "B") -> bool:
        """检查标的是否有共识"""
        signal = self._pool.get(ticker)
        if not signal:
            return False
        level_order = {"A": 3, "B": 2, "C": 1, "D": 0}
        return level_order.get(signal.consensus_level, 0) >= level_order.get(min_level, 0)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        levels = [s.consensus_level for s in self._pool.values()]
        return {
            "total": len(self._pool),
            "strong": levels.count("A"),
            "medium": levels.count("B"),
            "weak": levels.count("C"),
            "last_update": self._last_update,
        }


# 全局实例
consensus_analyzer = ConsensusAnalyzer()
consensus_pool = ConsensusPool()
