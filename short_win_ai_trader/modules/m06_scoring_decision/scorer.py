"""全维度量化评分模型 — 6维度100分制"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.logger import get_logger
from ...data_platform.data_models import (
    ComprehensiveScore, DimensionScore, EmotionCycle, RiskLevel,
)

logger = get_logger("swat.scoring")


class ComprehensiveScorer:
    """综合量化评分器 — 6大维度100分制
    
    评分维度与权重:
    - 资讯催化力(20%): 等级、时效性、催化强度、市场反馈
    - 基本面安全垫(15%): 业绩增速、估值、财务健康、题材纯正度
    - 技术形态强度(20%): 均线系统、突破形态、量能、技术指标
    - 筹码结构质量(15%): 集中度、底部锁定度、套牢盘比例、峰形态
    - 市场情绪适配(15%): 情绪周期、板块效应、龙头地位、赚钱效应
    - 资金流向强度(15%): 主力净流入、龙虎榜质量、封单强度、北向
    """

    # 评分等级与决策指引
    RATING_TABLE = {
        (90, 100): ("顶级标的", "重点重仓参与，确定性极高", RiskLevel.SAFE, 1),
        (80, 89): ("优质标的", "积极参与，胜率高，适合加仓布局", RiskLevel.SAFE, 2),
        (70, 79): ("良好标的", "谨慎参与，需严格风控，快进快出", RiskLevel.CAUTIOUS, 3),
        (60, 69): ("一般标的", "轻仓试错，不恋战，见好就收", RiskLevel.HIGH_RISK, 4),
        (0, 59): ("劣质标的", "坚决规避，无操作价值，禁止介入", RiskLevel.FORBIDDEN, 5),
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self.dimensions_config = config.scoring.dimensions
        logger.info("综合评分器初始化完成")

    def calculate_score(
        self,
        ticker: str,
        stock_name: str,
        context: Dict,
    ) -> ComprehensiveScore:
        """计算综合评分
        
        Args:
            context: 整合前5模块的核心数据
                - news: 资讯评分数据
                - fundamental: 基本面数据
                - technical: 技术形态数据
                - chip: 筹码结构数据
                - emotion: 情绪周期数据
                - fund_flow: 资金流向数据
        """
        dimension_scores = []

        # 1. 资讯催化力 (20%)
        ds1 = self._score_news_catalyst(ticker, context.get("news", {}))
        dimension_scores.append(ds1)

        # 2. 基本面安全垫 (15%)
        ds2 = self._score_fundamental(ticker, context.get("fundamental", {}))
        dimension_scores.append(ds2)

        # 3. 技术形态强度 (20%)
        ds3 = self._score_technical(ticker, context.get("technical", {}))
        dimension_scores.append(ds3)

        # 4. 筹码结构质量 (15%)
        ds4 = self._score_chip_structure(ticker, context.get("chip", {}))
        dimension_scores.append(ds4)

        # 5. 市场情绪适配 (15%)
        ds5 = self._score_emotion_fit(ticker, context.get("emotion", {}))
        dimension_scores.append(ds5)

        # 6. 资金流向强度 (15%)
        ds6 = self._score_fund_flow(ticker, context.get("fund_flow", {}))
        dimension_scores.append(ds6)

        # 计算总分
        total_score = sum(ds.score * ds.weight / 100 for ds in dimension_scores)
        total_score = round(max(0, min(100, total_score)), 1)

        # 确定评级
        rating, decision, risk_level, priority = self._get_rating(total_score)

        score = ComprehensiveScore(
            ticker=ticker,
            stock_name=stock_name,
            total_score=total_score,
            rating=rating,
            dimension_scores=dimension_scores,
            risk_reward_ratio=context.get("risk_reward", 0),
            risk_level=risk_level,
            priority=priority,
            decision=decision,
        )

        logger.info(f"评分完成: {ticker} {stock_name} = {total_score}分 [{rating}]")
        return score

    def _score_news_catalyst(self, ticker: str, news_data: Dict) -> DimensionScore:
        """资讯催化力评分 (20分)"""
        config = self.dimensions_config["news_catalyst"]
        weight = config["weight"]

        # 从news_data提取数据
        level_score = news_data.get("level_score", 50)  # 0-100
        timeliness_score = news_data.get("timeliness_score", 50)
        strength_score = news_data.get("strength_score", 50)
        feedback_score = news_data.get("feedback_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            level_score * sub_weights.get("level", 0.4) +
            timeliness_score * sub_weights.get("timeliness", 0.3) +
            strength_score * sub_weights.get("strength", 0.2) +
            feedback_score * sub_weights.get("market_feedback", 0.1)
        )

        return DimensionScore(
            dimension="资讯催化力",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "资讯等级": level_score,
                "时效性": timeliness_score,
                "催化强度": strength_score,
                "市场反馈": feedback_score,
            },
        )

    def _score_fundamental(self, ticker: str, fundamental: Dict) -> DimensionScore:
        """基本面安全垫评分 (15分)"""
        config = self.dimensions_config["fundamental"]
        weight = config["weight"]

        growth = fundamental.get("growth_score", 50)
        valuation = fundamental.get("valuation_score", 50)
        health = fundamental.get("health_score", 50)
        purity = fundamental.get("theme_purity_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            growth * sub_weights.get("growth", 0.35) +
            valuation * sub_weights.get("valuation", 0.25) +
            health * sub_weights.get("health", 0.25) +
            purity * sub_weights.get("theme_purity", 0.15)
        )

        return DimensionScore(
            dimension="基本面安全垫",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "业绩增速": growth,
                "估值水平": valuation,
                "财务健康": health,
                "题材纯正度": purity,
            },
        )

    def _score_technical(self, ticker: str, technical: Dict) -> DimensionScore:
        """技术形态强度评分 (20分)"""
        config = self.dimensions_config["technical"]
        weight = config["weight"]

        ma = technical.get("ma_score", 50)
        breakout = technical.get("breakout_score", 50)
        volume = technical.get("volume_score", 50)
        indicators = technical.get("indicators_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            ma * sub_weights.get("ma_system", 0.3) +
            breakout * sub_weights.get("breakout", 0.3) +
            volume * sub_weights.get("volume", 0.2) +
            indicators * sub_weights.get("indicators", 0.2)
        )

        return DimensionScore(
            dimension="技术形态强度",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "均线系统": ma,
                "突破形态": breakout,
                "量能配合": volume,
                "技术指标": indicators,
            },
        )

    def _score_chip_structure(self, ticker: str, chip: Dict) -> DimensionScore:
        """筹码结构质量评分 (15分)"""
        config = self.dimensions_config["chip_structure"]
        weight = config["weight"]

        concentration = chip.get("concentration_score", 50)
        lock_ratio = chip.get("lock_ratio_score", 50)
        trapped = chip.get("trapped_ratio_score", 50)
        peak_shape = chip.get("peak_shape_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            concentration * sub_weights.get("concentration", 0.3) +
            lock_ratio * sub_weights.get("lock_ratio", 0.3) +
            trapped * sub_weights.get("trapped_ratio", 0.2) +
            peak_shape * sub_weights.get("peak_shape", 0.2)
        )

        return DimensionScore(
            dimension="筹码结构质量",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "筹码集中度": concentration,
                "底部锁定度": lock_ratio,
                "套牢盘比例": trapped,
                "筹码峰形态": peak_shape,
            },
        )

    def _score_emotion_fit(self, ticker: str, emotion: Dict) -> DimensionScore:
        """市场情绪适配评分 (15分)"""
        config = self.dimensions_config["emotion_fit"]
        weight = config["weight"]

        cycle = emotion.get("cycle_match_score", 50)
        sector = emotion.get("sector_effect_score", 50)
        dragon = emotion.get("dragon_status_score", 50)
        profit = emotion.get("profit_effect_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            cycle * sub_weights.get("cycle_match", 0.4) +
            sector * sub_weights.get("sector_effect", 0.25) +
            dragon * sub_weights.get("dragon_status", 0.2) +
            profit * sub_weights.get("profit_effect", 0.15)
        )

        return DimensionScore(
            dimension="市场情绪适配",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "情绪周期匹配": cycle,
                "板块效应": sector,
                "龙头地位": dragon,
                "赚钱效应": profit,
            },
        )

    def _score_fund_flow(self, ticker: str, fund: Dict) -> DimensionScore:
        """资金流向强度评分 (15分)"""
        config = self.dimensions_config["fund_flow"]
        weight = config["weight"]

        main = fund.get("main_inflow_score", 50)
        dragon_bond = fund.get("dragon_bond_score", 50)
        seal = fund.get("seal_strength_score", 50)
        northbound = fund.get("northbound_score", 50)
        sub_weights = config.get("sub_weights", {})

        score = (
            main * sub_weights.get("main_inflow", 0.35) +
            dragon_bond * sub_weights.get("dragon_bond", 0.25) +
            seal * sub_weights.get("seal_strength", 0.25) +
            northbound * sub_weights.get("northbound", 0.15)
        )

        return DimensionScore(
            dimension="资金流向强度",
            weight=weight,
            score=round(min(100, score), 1),
            details={
                "主力净流入": main,
                "龙虎榜质量": dragon_bond,
                "封单强度": seal,
                "北向资金": northbound,
            },
        )

    def _get_rating(self, score: float):
        """根据分数确定评级"""
        for (low, high), (rating, decision, risk, priority) in self.RATING_TABLE.items():
            if low <= score <= high:
                return rating, decision, risk, priority
        return "未知", "无法评估", RiskLevel.HIGH_RISK, 5

    def update_score(self, ticker: str, context_delta: Dict, current: ComprehensiveScore) -> ComprehensiveScore:
        """盘中评分动态更新"""
        logger.info(f"动态更新评分: {ticker}")
        return self.calculate_score(
            ticker=ticker,
            stock_name=current.stock_name,
            context=context_delta,
        )
