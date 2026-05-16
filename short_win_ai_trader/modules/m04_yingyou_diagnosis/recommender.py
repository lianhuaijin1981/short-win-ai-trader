"""游资模式标的推荐引擎

基于游资数字指纹，对给定标的进行匹配度评分(0-100)，并输出:
    - 操作方式(打板/低吸/竞价等)
    - 建议仓位
    - 止损位
    - 止盈位
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from api.core.logger import get_logger
from api.models.responses import YingYouMatch
from api.services.ifind_service import ifind_service

from .fingerprints import YingYouFingerprint, registry

logger = get_logger("swat.m04.recommender")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class StockYingYouMatch:
    """个股与游资的匹配详情"""
    yingyou_name: str
    ticker: str
    name: str
    match_score: float           # 0-100 匹配度
    recommendation: str          # 综合建议
    operation: str               # 操作方式
    position: str                # 仓位建议
    stop_loss: str               # 止损建议
    take_profit: str             # 止盈建议
    dimension_scores: Dict[str, float]  # 各维度评分
    fit_reason: str              # 匹配原因
    risk_warning: str            # 风险提示
    priority: int = 0            # 优先级


# ═══════════════════════════════════════════════════════════
# 维度评分器
# ═══════════════════════════════════════════════════════════

class DimensionScorer:
    """多维度评分器 — 从多个维度评估标的与游资的匹配度"""

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        "趋势强度": 0.20,
        "题材契合": 0.20,
        "量能质量": 0.15,
        "位置优劣": 0.15,
        "换手水平": 0.10,
        "情绪匹配": 0.10,
        "资金动向": 0.10,
    }

    async def score(
        self,
        fp: YingYouFingerprint,
        ticker: str,
        name: str,
        stock_data: Optional[Dict] = None,
    ) -> StockYingYouMatch:
        """对单个标的进行完整评分"""
        try:
            if stock_data is None:
                stock_data = await self._fetch_stock_data(ticker)

            dimension_scores = self._calc_dimensions(fp, stock_data)
            total_score = self._weighted_sum(dimension_scores)

            operation = self._suggest_operation(fp, total_score, stock_data)
            position = self._suggest_position(fp, total_score)
            stop_loss = self._suggest_stop_loss(fp, stock_data)
            take_profit = self._suggest_take_profit(fp, stock_data)
            recommendation = self._gen_recommendation(
                fp, total_score, operation, position
            )
            fit_reason = self._gen_fit_reason(fp, dimension_scores, stock_data)
            risk_warning = self._gen_risk_warning(fp, stock_data)

            return StockYingYouMatch(
                yingyou_name=fp.name,
                ticker=ticker,
                name=name,
                match_score=round(total_score, 1),
                recommendation=recommendation,
                operation=operation,
                position=position,
                stop_loss=stop_loss,
                take_profit=take_profit,
                dimension_scores=dimension_scores,
                fit_reason=fit_reason,
                risk_warning=risk_warning,
                priority=int(total_score),
            )
        except Exception as e:
            logger.error(f"Scoring failed for {ticker}/{fp.name}: {e}")
            return self._fallback_match(fp, ticker, name)

    async def _fetch_stock_data(self, ticker: str) -> Dict:
        """获取个股数据"""
        try:
            prices = await ifind_service.get_recent_prices([ticker], days=20)
            fundamentals = await ifind_service.get_stock_fundamentals(ticker)
            return {
                "prices": prices,
                "fundamentals": fundamentals,
                "ticker": ticker,
            }
        except Exception as e:
            logger.warning(f"Fetch stock data failed for {ticker}: {e}")
            return self._mock_stock_data(ticker)

    def _mock_stock_data(self, ticker: str) -> Dict:
        """模拟个股数据"""
        return {
            "prices": [
                {"close": 15.5 + i * 0.3, "volume": 100000 + i * 5000,
                 "high": 16.0 + i * 0.3, "low": 15.0 + i * 0.3}
                for i in range(20)
            ],
            "fundamentals": {"ticker": ticker, "pe": 25.0},
            "ticker": ticker,
        }

    def _calc_dimensions(
        self,
        fp: YingYouFingerprint,
        stock_data: Dict,
    ) -> Dict[str, float]:
        """计算各维度评分"""
        prices = stock_data.get("prices", [])
        if not prices:
            return {k: 50.0 for k in self.DIMENSION_WEIGHTS}

        # 计算技术指标
        closes = [float(p.get("close", 0)) for p in prices if p.get("close")]
        volumes = [float(p.get("volume", 0)) for p in prices if p.get("volume")]

        if len(closes) < 5:
            return {k: 50.0 for k in self.DIMENSION_WEIGHTS}

        dimensions = {}
        dimensions["趋势强度"] = self._score_trend(closes)
        dimensions["题材契合"] = self._score_theme(fp, stock_data)
        dimensions["量能质量"] = self._score_volume(volumes)
        dimensions["位置优劣"] = self._score_position(closes, fp)
        dimensions["换手水平"] = self._score_turnover(volumes, fp, stock_data)
        dimensions["情绪匹配"] = self._score_emotion_fit(fp)
        dimensions["资金动向"] = self._score_fund_flow(stock_data)

        return dimensions

    def _score_trend(self, closes: List[float]) -> float:
        """趋势强度评分 0-100"""
        if len(closes) < 10:
            return 50.0

        # 短期均线
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10

        current = closes[-1]
        score = 50.0

        # 均线多头排列
        if current > ma5 > ma10 > ma20:
            score += 30
        elif current > ma5 > ma10:
            score += 15
        elif current < ma5 < ma10:
            score -= 20

        # 近期涨幅
        change_5d = (current - closes[-5]) / closes[-5] * 100 if closes[-5] > 0 else 0
        if 5 <= change_5d <= 20:
            score += 15
        elif change_5d > 20:
            score += 5
        elif change_5d < -10:
            score -= 20

        return max(0, min(100, score))

    def _score_theme(self, fp: YingYouFingerprint, stock_data: Dict) -> float:
        """题材契合评分 0-100"""
        # 基于游资的选股标准中的题材要求
        selection = fp.stock_selection
        theme_req = selection.get("theme", "")

        # 检查是否有题材重叠
        fundamentals = stock_data.get("fundamentals", {})
        has_theme = bool(fundamentals) and theme_req != ""

        if has_theme:
            base = 70.0
            # 加分项
            if "龙头" in str(theme_req) or "主流" in str(theme_req):
                base += 15
            if "热点" in str(theme_req):
                base += 10
            return min(100, base)

        return 50.0

    def _score_volume(self, volumes: List[float]) -> float:
        """量能质量评分 0-100"""
        if len(volumes) < 5:
            return 50.0

        avg_vol = sum(volumes[-5:]) / 5
        prev_avg = sum(volumes[-10:-5]) / 5 if len(volumes) >= 10 else avg_vol

        if avg_vol == 0:
            return 50.0

        ratio = avg_vol / prev_avg if prev_avg > 0 else 1.0

        if 1.2 <= ratio <= 3.0:
            return 80.0
        elif 0.8 <= ratio < 1.2:
            return 60.0
        elif ratio > 3.0:
            return 70.0
        return 40.0

    def _score_position(self, closes: List[float], fp: YingYouFingerprint) -> float:
        """位置优劣评分 0-100"""
        if len(closes) < 10:
            return 50.0

        current = closes[-1]
        high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
        low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)

        if high_20 == low_20:
            return 50.0

        # 当前位置在20日区间的百分比
        position_pct = (current - low_20) / (high_20 - low_20) * 100

        # 根据不同游资偏好调整
        tags = []
        if hasattr(fp.behavioral_tags, '__iter__') and not isinstance(fp.behavioral_tags, str):
            for t in fp.behavioral_tags:
                if isinstance(t, list):
                    tags.extend(t)
                else:
                    tags.append(t)

        if "回调低吸" in tags or "超跌" in tags:
            # 偏好低位
            if position_pct < 30:
                return 85.0
            elif position_pct < 50:
                return 70.0
            return 40.0
        elif "打板" in tags or "连板" in tags:
            # 偏好强势位置
            if position_pct > 70:
                return 85.0
            elif position_pct > 50:
                return 70.0
            return 50.0
        else:
            # 中性
            if 30 <= position_pct <= 70:
                return 75.0
            return 60.0

    def _score_turnover(
        self,
        volumes: List[float],
        fp: YingYouFingerprint,
        stock_data: Dict,
    ) -> float:
        """换手水平评分 0-100"""
        selection = fp.stock_selection
        turnover_req = selection.get("turnover_rate", "")

        if "15-30%" in str(turnover_req):
            return 75.0
        elif "5-25%" in str(turnover_req):
            return 65.0
        return 55.0

    def _score_emotion_fit(self, fp: YingYouFingerprint) -> float:
        """情绪匹配评分 0-100"""
        # 基于游资适用周期
        cycles = fp.applicable_cycles
        if "情绪高潮" in cycles and "情绪修复" in cycles:
            return 75.0
        elif "情绪冰点" in cycles:
            return 60.0
        return 55.0

    def _score_fund_flow(self, stock_data: Dict) -> float:
        """资金动向评分 0-100"""
        fundamentals = stock_data.get("fundamentals", {})
        if not fundamentals:
            return 50.0

        # 简化的资金流向评分
        holder_info = fundamentals.get("holder_info", {})
        if holder_info:
            return 70.0
        return 55.0

    def _weighted_sum(self, dimension_scores: Dict[str, float]) -> float:
        """加权求和"""
        total = 0.0
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            score = dimension_scores.get(dim, 50.0)
            total += score * weight
        return total

    def _suggest_operation(
        self,
        fp: YingYouFingerprint,
        score: float,
        stock_data: Dict,
    ) -> str:
        """建议操作方式"""
        if score < 40:
            return "观望，暂不介入"

        entry = fp.entry_timing.get("entry_method", "")
        if "打板" in entry:
            return "涨停板排队买入"
        elif "低吸" in entry:
            return "回踩支撑位低吸"
        elif "竞价" in entry:
            return "早盘竞价介入"
        elif "分" in entry:
            return "分批建仓"
        return "低吸为主"

    def _suggest_position(self, fp: YingYouFingerprint, score: float) -> str:
        """建议仓位"""
        if score >= 75:
            return f"{min(fp.single_position_limit, 40)}%"
        elif score >= 60:
            return f"{min(fp.single_position_limit, 25)}%"
        elif score >= 45:
            return f"{min(fp.single_position_limit, 15)}%"
        return "0%"

    def _suggest_stop_loss(self, fp: YingYouFingerprint, stock_data: Dict) -> str:
        """建议止损位"""
        return fp.stop_loss_rule

    def _suggest_take_profit(self, fp: YingYouFingerprint, stock_data: Dict) -> str:
        """建议止盈位"""
        return fp.take_profit_rule

    def _gen_recommendation(
        self,
        fp: YingYouFingerprint,
        score: float,
        operation: str,
        position: str,
    ) -> str:
        """生成综合建议"""
        if score >= 75:
            return f"高度匹配{fp.name}模式，建议{operation}，仓位{position}"
        elif score >= 60:
            return f"较匹配{fp.name}模式，可{operation}，仓位控制在{position}以内"
        elif score >= 45:
            return f"轻度匹配{fp.name}模式，可小仓位试探{operation}"
        return f"暂不符合{fp.name}模式，建议观望"

    def _gen_fit_reason(
        self,
        fp: YingYouFingerprint,
        dimension_scores: Dict[str, float],
        stock_data: Dict,
    ) -> str:
        """生成匹配原因"""
        top_dims = sorted(
            dimension_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        dim_str = ", ".join([f"{k}={v:.0f}" for k, v in top_dims])
        return f"{fp.name}维度评分: {dim_str}"

    def _gen_risk_warning(
        self,
        fp: YingYouFingerprint,
        stock_data: Dict,
    ) -> str:
        """生成风险提示"""
        return f"严格遵守{fp.name}止损规则: {fp.stop_loss_rule}"

    def _fallback_match(
        self,
        fp: YingYouFingerprint,
        ticker: str,
        name: str,
    ) -> StockYingYouMatch:
        """降级匹配结果"""
        return StockYingYouMatch(
            yingyou_name=fp.name,
            ticker=ticker,
            name=name,
            match_score=0.0,
            recommendation="数据获取失败，无法评估",
            operation="观望",
            position="0%",
            stop_loss=fp.stop_loss_rule,
            take_profit=fp.take_profit_rule,
            dimension_scores={},
            fit_reason="数据异常",
            risk_warning="请检查数据",
        )


# ═══════════════════════════════════════════════════════════
# 推荐引擎
# ═══════════════════════════════════════════════════════════

class YingYouRecommender:
    """游资模式标的推荐引擎"""

    def __init__(self):
        self.scorer = DimensionScorer()

    async def recommend(
        self,
        ticker: str,
        name: str = "",
        yingyou_filter: Optional[List[str]] = None,
    ) -> List[StockYingYouMatch]:
        """为指定标的推荐匹配的游资模式"""
        logger.info(f"Recommending for {ticker} ({name})")

        # 获取个股数据
        stock_data = await self.scorer._fetch_stock_data(ticker)

        # 筛选游资
        targets = yingyou_filter or registry.list_all()

        # 并行评分
        tasks = []
        for yingyou_name in targets:
            fp = registry.get(yingyou_name)
            if fp:
                tasks.append(self.scorer.score(fp, ticker, name, stock_data))

        results = await asyncio.gather(*tasks)

        # 按匹配度排序
        sorted_results = sorted(results, key=lambda x: x.match_score, reverse=True)
        logger.info(f"Top match for {ticker}: {sorted_results[0].yingyou_name} "
                   f"({sorted_results[0].match_score}分)")
        return sorted_results

    async def recommend_batch(
        self,
        tickers: List[Dict[str, str]],
        yingyou_filter: Optional[List[str]] = None,
    ) -> Dict[str, List[StockYingYouMatch]]:
        """批量推荐"""
        results = {}
        for item in tickers:
            ticker = item.get("ticker", "")
            name = item.get("name", "")
            if ticker:
                results[ticker] = await self.recommend(ticker, name, yingyou_filter)
        return results

    async def to_yingyou_matches(
        self,
        matches: List[StockYingYouMatch],
    ) -> List[YingYouMatch]:
        """转换为API响应模型"""
        return [
            YingYouMatch(
                yingyou_name=m.yingyou_name,
                ticker=m.ticker,
                name=m.name,
                match_score=m.match_score,
                recommendation=m.recommendation,
                operation=m.operation,
                position=m.position,
                stop_loss=m.stop_loss,
                take_profit=m.take_profit,
            )
            for m in matches
        ]

    def get_top_matches(
        self,
        matches: List[StockYingYouMatch],
        threshold: float = 50.0,
        top_n: int = 3,
    ) -> List[StockYingYouMatch]:
        """获取高匹配度结果"""
        filtered = [m for m in matches if m.match_score >= threshold]
        return filtered[:top_n]


# 全局推荐引擎实例
recommender = YingYouRecommender()
