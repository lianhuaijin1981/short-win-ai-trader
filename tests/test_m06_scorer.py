"""测试: 模块六综合评分"""

import pytest

from short_win_ai_trader.core.config import load_config
from short_win_ai_trader.modules.m06_scoring_decision.scorer import ComprehensiveScorer
from short_win_ai_trader.modules.m06_scoring_decision.risk_reward import RiskRewardCalculator
from short_win_ai_trader.modules.m06_scoring_decision.position_manager import PositionManager
from short_win_ai_trader.modules.m06_scoring_decision.trade_planner import TradePlanner
from short_win_ai_trader.data_platform.data_models import EmotionCycle


class TestComprehensiveScorer:
    """综合评分测试"""

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def scorer(self, config):
        return ComprehensiveScorer(config)

    def test_score_calculation(self, scorer):
        """测试评分计算"""
        context = {
            "news": {"level_score": 85, "timeliness_score": 90, "strength_score": 80, "feedback_score": 75},
            "fundamental": {"growth_score": 80, "valuation_score": 70, "health_score": 75, "theme_purity_score": 85},
            "technical": {"ma_score": 85, "breakout_score": 90, "volume_score": 80, "indicators_score": 75},
            "chip": {"concentration_score": 70, "lock_ratio_score": 75, "trapped_ratio_score": 80, "peak_shape_score": 85},
            "emotion": {"cycle_match_score": 85, "sector_effect_score": 80, "dragon_status_score": 90, "profit_effect_score": 75},
            "fund_flow": {"main_inflow_score": 80, "dragon_bond_score": 85, "seal_strength_score": 75, "northbound_score": 70},
        }

        score = scorer.calculate_score("600519.SH", "贵州茅台", context)
        assert 0 <= score.total_score <= 100
        assert len(score.dimension_scores) == 6
        assert score.rating in ["顶级标的", "优质标的", "良好标的", "一般标的", "劣质标的"]

    def test_rating_levels(self, scorer):
        """测试评级等级"""
        high_context = {
            "news": {"level_score": 90, "timeliness_score": 90, "strength_score": 90, "feedback_score": 90},
            "fundamental": {"growth_score": 90, "valuation_score": 90, "health_score": 90, "theme_purity_score": 90},
            "technical": {"ma_score": 90, "breakout_score": 90, "volume_score": 90, "indicators_score": 90},
            "chip": {"concentration_score": 90, "lock_ratio_score": 90, "trapped_ratio_score": 90, "peak_shape_score": 90},
            "emotion": {"cycle_match_score": 90, "sector_effect_score": 90, "dragon_status_score": 90, "profit_effect_score": 90},
            "fund_flow": {"main_inflow_score": 90, "dragon_bond_score": 90, "seal_strength_score": 90, "northbound_score": 90},
        }

        score = scorer.calculate_score("600519.SH", "贵州茅台", high_context)
        assert score.rating in ["顶级标的", "优质标的"]


class TestRiskRewardCalculator:
    """风险收益比测试"""

    @pytest.fixture
    def calc(self):
        return RiskRewardCalculator(load_config())

    def test_calculate(self, calc):
        """测试RR计算"""
        result = calc.calculate(100.0, 96.0, 120.0)
        assert result.risk_reward_ratio == 5.0  # (120-100)/(100-96) = 20/4 = 5
        assert result.decision == "强烈推荐介入"

    def test_from_score_rating(self, calc):
        """测试基于评级的RR计算"""
        result = calc.calculate_from_score(100.0, "优质标的", {})
        assert result.risk_reward_ratio > 0
        assert result.take_profit_price > result.entry_price

    def test_low_rr(self, calc):
        """测试低RR情况"""
        result = calc.calculate(100.0, 97.0, 101.0)
        assert result.risk_reward_ratio < 1.5
        assert "不建议" in result.decision


class TestPositionManager:
    """仓位管理测试"""

    @pytest.fixture
    def pm(self):
        return PositionManager(load_config())

    def test_position_calculation(self, pm):
        """测试仓位计算"""
        result = pm.calculate_position(
            EmotionCycle.FERMENT, 85, "优质标的", 3.0
        )
        assert "发酵期" in result["emotion_cycle"]
        assert "%" in result["recommended_position"]

    def test_retreat_low_position(self, pm):
        """测试退潮期低仓位"""
        result = pm.calculate_position(
            EmotionCycle.RETREAT, 90, "顶级标的", 4.0
        )
        rec = float(result["recommended_position"].rstrip("%"))
        assert rec <= 5  # 退潮期单票不超过5%


class TestTradePlanner:
    """交易计划测试"""

    @pytest.fixture
    def planner(self):
        return TradePlanner(load_config())

    def test_generate_plan(self, planner):
        """测试交易计划生成"""
        plan = planner.generate_trade_plan(
            ticker="600519.SH",
            stock_name="贵州茅台",
            score=85,
            rating="优质标的",
            risk_reward_ratio=3.0,
            position_pct=30,
            entry_type="突破入场",
            entry_price=1800.0,
            stop_loss_price=1728.0,
            take_profit_price=2070.0,
        )
        assert plan.ticker == "600519.SH"
        assert len(plan.hold_conditions) > 0
        assert len(plan.sell_conditions) > 0

    def test_quick_plan(self, planner):
        """测试快速计划"""
        plan = planner.generate_quick_plan("600519.SH", "贵州茅台", 1800.0, 85, "优质标的")
        assert plan["ticker"] == "600519.SH"
        assert ":1" in plan["risk_reward"]
