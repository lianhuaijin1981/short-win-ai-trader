"""游资诊断模块(M04)测试用例

测试覆盖:
    - 游资指纹注册中心
    - 情绪阶段判定
    - 资金方向分析
    - 模式契合度计算
    - 标的推荐引擎
    - 共识分析
    - 组合策略
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List

from short_win_ai_trader.modules.m04_yingyou_diagnosis import (
    # fingerprints
    FingerprintRegistry,
    YingYouFingerprint,
    registry,
    # diagnosis
    YingYouDiagnosisEngine,
    EmotionPhase,
    EmotionPhaseDetector,
    FundDirection,
    FundDirectionAnalyzer,
    ModeFitScore,
    ModeFitCalculator,
    DiagnosisReport,
    diagnosis_engine,
    # recommender
    YingYouRecommender,
    StockYingYouMatch,
    DimensionScorer,
    recommender,
    # consensus
    ConsensusAnalyzer,
    ConsensusPool,
    ConsensusReport,
    ConsensusSignal,
    DivergenceAlert,
    consensus_analyzer,
    consensus_pool,
    # portfolio
    PortfolioStrategyEngine,
    PortfolioConfig,
    PortfolioConfigFactory,
    PortfolioStrategy,
    PortfolioExecution,
    portfolio_engine,
)


# ═══════════════════════════════════════════════════════════
# 测试: 游资指纹注册中心
# ═══════════════════════════════════════════════════════════

class TestFingerprintRegistry:
    """测试游资指纹注册中心"""

    def test_registry_initialization(self):
        """测试注册中心初始化"""
        assert registry is not None
        all_names = registry.list_all()
        assert len(all_names) >= 8, "至少应有8位游资指纹"

    def test_get_fingerprint(self):
        """测试获取游资指纹"""
        fp = registry.get("炒股养家")
        assert fp is not None
        assert fp.name == "炒股养家"
        assert fp.philosophy != ""
        assert len(fp.radar_scores) == 5

    def test_get_nonexistent_fingerprint(self):
        """测试获取不存在的游资指纹"""
        fp = registry.get("不存在的游资")
        assert fp is None

    def test_fingerprint_structure(self):
        """测试游资指纹结构完整性"""
        fp = registry.get("炒股养家")
        assert fp is not None
        
        # 检查必需字段
        assert fp.name != ""
        assert fp.nickname != ""
        assert fp.philosophy != ""
        assert fp.philosophy_detail != ""
        assert fp.mode_essence != ""
        assert fp.enlightenment != ""
        assert fp.bottleneck_broken != ""
        assert fp.core_insight != ""
        assert isinstance(fp.stock_selection, dict)
        assert isinstance(fp.entry_timing, dict)
        assert isinstance(fp.risk_control, dict)
        assert isinstance(fp.classic_tactics, list)
        assert len(fp.classic_tactics) >= 1
        assert isinstance(fp.radar_scores, dict)
        assert len(fp.radar_scores) == 5
        assert isinstance(fp.position_strategy, dict)
        assert isinstance(fp.applicable_cycles, list)
        assert fp.position_limit > 0
        assert fp.single_position_limit > 0
        assert fp.stop_loss_rule != ""
        assert fp.take_profit_rule != ""
        assert isinstance(fp.key_indicators, list)
        assert fp.quote != ""

    def test_radar_scores_range(self):
        """测试雷达图评分范围"""
        for name in registry.list_all():
            fp = registry.get(name)
            assert fp is not None
            for dim, score in fp.radar_scores.items():
                assert 0 <= score <= 100, f"{name}的{dim}评分应在0-100之间"

    def test_filter_by_cycle(self):
        """测试按情绪周期筛选"""
        fps = registry.filter_by_cycle("情绪修复")
        assert len(fps) > 0, "应有游资适用于情绪修复周期"

    def test_get_radar_data(self):
        """测试获取雷达图数据"""
        radar = registry.get_radar_data("炒股养家")
        assert radar is not None
        assert "dimensions" in radar
        assert "scores" in radar
        assert "full_marks" in radar
        assert len(radar["dimensions"]) == 5
        assert len(radar["scores"]) == 5

    def test_compare_fingerprints(self):
        """测试游资对比"""
        compare_data = registry.compare(["炒股养家", "退学炒股"])
        assert "dimensions" in compare_data
        assert "series" in compare_data
        assert len(compare_data["series"]) == 2

    def test_get_by_market_phase(self):
        """测试按市场阶段获取游资"""
        fps = registry.get_by_market_phase("修复")
        assert len(fps) > 0

    def test_search_by_name(self):
        """测试按名称搜索"""
        results = registry.search_by_name("炒股")
        assert len(results) >= 1

    def test_get_enlightenment(self):
        """测试获取悟道之路"""
        data = registry.get_enlightenment("炒股养家")
        assert data is not None
        assert "enlightenment" in data
        assert "bottleneck_broken" in data
        assert "core_insight" in data


# ═══════════════════════════════════════════════════════════
# 测试: 情绪阶段判定
# ═══════════════════════════════════════════════════════════

class TestEmotionPhaseDetector:
    """测试情绪阶段判定器"""

    @pytest.fixture
    def detector(self):
        return EmotionPhaseDetector()

    def test_calculate_indicators(self, detector):
        """测试指标计算"""
        mock_data = {
            "limit_up": 45,
            "limit_down": 8,
            "explode_rate": 0.35,
            "volume_ratio": 1.05,
            "max_boards": 5,
            "up_count": 2800,
            "down_count": 1800,
        }
        indicators = detector._calculate_indicators(mock_data)
        
        assert "涨停家数" in indicators
        assert "跌停家数" in indicators
        assert "炸板率" in indicators
        assert "量比" in indicators
        assert "情绪指数" in indicators
        assert indicators["涨停家数"] == 45.0

    def test_emotion_index_calculation(self, detector):
        """测试情绪指数计算"""
        # 强势市场
        index_strong = detector._calc_emotion_index(80, 2, 0.15, 1.5)
        # 弱势市场
        index_weak = detector._calc_emotion_index(15, 30, 0.65, 0.5)
        
        assert index_strong > index_weak
        assert 0 <= index_strong <= 100
        assert 0 <= index_weak <= 100

    def test_classify_phase_repair(self, detector):
        """测试修复期判定"""
        indicators = {
            "涨停家数": 40.0,
            "跌停家数": 8.0,
            "炸板率": 0.35,
            "量比": 1.0,
            "情绪指数": 45.0,
        }
        phase, confidence = detector._classify_phase(indicators)
        assert phase in ["修复", "高潮", "冰点", "退潮"]
        assert 0 <= confidence <= 1

    def test_get_suggestions(self, detector):
        """测试建议生成"""
        for phase in ["冰点", "修复", "高潮", "退潮"]:
            position, operation = detector._get_suggestions(phase)
            assert position != ""
            assert operation != ""

    def test_fallback_phase(self, detector):
        """测试降级返回"""
        fallback = detector._fallback_phase()
        assert fallback.phase == "修复"
        assert fallback.confidence == 0.5


# ═══════════════════════════════════════════════════════════
# 测试: 资金方向分析
# ═══════════════════════════════════════════════════════════

class TestFundDirectionAnalyzer:
    """测试资金方向分析器"""

    @pytest.fixture
    def analyzer(self):
        return FundDirectionAnalyzer()

    def test_mock_themes(self, analyzer):
        """测试模拟题材数据"""
        themes = analyzer._mock_themes()
        assert len(themes) >= 3
        assert "name" in themes[0]
        assert "score" in themes[0]

    def test_rank_themes(self, analyzer):
        """测试题材排序"""
        themes = [
            {"name": "A", "score": 80},
            {"name": "B", "score": 95},
            {"name": "C", "score": 70},
        ]
        ranked = analyzer._rank_themes(themes)
        assert ranked[0]["name"] == "B"

    def test_classify_sectors(self, analyzer):
        """测试板块分类"""
        sectors = [
            {"sector": "计算机", "net_flow": 25.5},
            {"sector": "银行", "net_flow": -15.8},
        ]
        inflow, outflow = analyzer._classify_sectors(sectors)
        assert "计算机" in inflow
        assert "银行" in outflow

    def test_calc_flow_score(self, analyzer):
        """测试资金流向评分"""
        score = analyzer._calc_flow_score(["A", "B"], ["C"])
        assert 0 <= score <= 100

    def test_activity_level(self, analyzer):
        """测试活跃度判断"""
        assert analyzer._activity_level(80) == "高"
        assert analyzer._activity_level(50) == "中"
        assert analyzer._activity_level(20) == "低"

    def test_fallback_direction(self, analyzer):
        """测试降级返回"""
        fallback = analyzer._fallback_direction()
        assert fallback.fund_flow_score == 50.0
        assert fallback.activity_level == "中"


# ═══════════════════════════════════════════════════════════
# 测试: 模式契合度计算
# ═══════════════════════════════════════════════════════════

class TestModeFitCalculator:
    """测试模式契合度计算器"""

    @pytest.fixture
    def calculator(self):
        return ModeFitCalculator()

    @pytest.fixture
    def mock_emotion(self):
        return EmotionPhase(
            phase="修复",
            confidence=0.7,
            indicators={"情绪指数": 50.0},
            position_suggestion="50-70%",
            operation_suggestion="积极做多",
        )

    @pytest.fixture
    def mock_fund(self):
        return FundDirection(
            primary_direction="人工智能",
            secondary_direction="半导体",
            hot_themes=[{"name": "人工智能", "score": 90}],
            fund_flow_score=65.0,
            activity_level="中",
            inflow_sectors=["计算机"],
            outflow_sectors=["银行"],
        )

    def test_calculate_all_fits(self, calculator, mock_emotion, mock_fund):
        """测试计算所有游资契合度"""
        results = calculator.calculate(mock_emotion, mock_fund)
        assert len(results) >= 8
        
        # 检查排序
        scores = [r.fit_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_cycle_match(self, calculator):
        """测试情绪周期匹配"""
        fp = registry.get("炒股养家")
        assert fp is not None
        
        # 完全匹配
        score = calculator._cycle_match(fp, "情绪修复")
        assert score == 1.0
        
        # 部分匹配或不匹配 - 情绪冰点可能与情绪修复有部分匹配关系
        score = calculator._cycle_match(fp, "情绪冰点")
        assert 0 <= score <= 1.0

    def test_opportunity_level(self, calculator):
        """测试机会级别"""
        assert calculator._opportunity_level(80) == "A"
        assert calculator._opportunity_level(60) == "B"
        assert calculator._opportunity_level(45) == "C"
        assert calculator._opportunity_level(30) == "D"

    def test_risk_level(self, calculator):
        """测试风险级别"""
        assert calculator._risk_level("高潮") == "高"
        assert calculator._risk_level("退潮") == "高"
        assert calculator._risk_level("修复") == "低"

    def test_suggest_position(self, calculator, mock_emotion):
        """测试仓位建议"""
        fp = registry.get("炒股养家")
        assert fp is not None
        
        position = calculator._suggest_position(fp, mock_emotion, 70)
        assert 0 <= position <= 100


# ═══════════════════════════════════════════════════════════
# 测试: 诊断引擎
# ═══════════════════════════════════════════════════════════

class TestDiagnosisEngine:
    """测试诊断引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert diagnosis_engine is not None
        assert diagnosis_engine.emotion_detector is not None
        assert diagnosis_engine.fund_analyzer is not None
        assert diagnosis_engine.fit_calculator is not None


# ═══════════════════════════════════════════════════════════
# 测试: 维度评分器
# ═══════════════════════════════════════════════════════════

class TestDimensionScorer:
    """测试维度评分器"""

    @pytest.fixture
    def scorer(self):
        return DimensionScorer()

    def test_dimension_weights(self, scorer):
        """测试维度权重"""
        weights = scorer.DIMENSION_WEIGHTS
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_mock_stock_data(self, scorer):
        """测试模拟股票数据"""
        data = scorer._mock_stock_data("600519.SH")
        assert "prices" in data
        assert "fundamentals" in data
        assert len(data["prices"]) == 20

    def test_score_trend(self, scorer):
        """测试趋势评分"""
        # 上升趋势
        closes_up = [10 + i * 0.5 for i in range(20)]
        score_up = scorer._score_trend(closes_up)
        assert score_up > 50

        # 下降趋势
        closes_down = [20 - i * 0.5 for i in range(20)]
        score_down = scorer._score_trend(closes_down)
        assert score_down < score_up

    def test_score_volume(self, scorer):
        """测试量能评分"""
        # 温和放量
        volumes = [100000 + i * 5000 for i in range(10)]
        score = scorer._score_volume(volumes)
        assert 0 <= score <= 100

    def test_score_position(self, scorer):
        """测试位置评分"""
        fp = registry.get("炒股养家")
        assert fp is not None
        
        closes = [10 + i * 0.2 for i in range(20)]
        score = scorer._score_position(closes, fp)
        assert 0 <= score <= 100

    def test_weighted_sum(self, scorer):
        """测试加权求和"""
        scores = {k: 60.0 for k in scorer.DIMENSION_WEIGHTS}
        total = scorer._weighted_sum(scores)
        assert total == pytest.approx(60.0, abs=0.1)

    def test_fallback_match(self, scorer):
        """测试降级匹配"""
        fp = registry.get("炒股养家")
        assert fp is not None
        
        match = scorer._fallback_match(fp, "600519.SH", "贵州茅台")
        assert match.match_score == 0.0
        assert match.ticker == "600519.SH"


# ═══════════════════════════════════════════════════════════
# 测试: 推荐引擎
# ═══════════════════════════════════════════════════════════

class TestYingYouRecommender:
    """测试推荐引擎"""

    def test_recommender_initialization(self):
        """测试推荐引擎初始化"""
        assert recommender is not None
        assert recommender.scorer is not None

    def test_get_top_matches(self):
        """测试获取高匹配度结果"""
        matches = [
            StockYingYouMatch(
                yingyou_name="A", ticker="T1", name="N1",
                match_score=80, recommendation="", operation="",
                position="", stop_loss="", take_profit="",
                dimension_scores={}, fit_reason="", risk_warning="",
            ),
            StockYingYouMatch(
                yingyou_name="B", ticker="T1", name="N1",
                match_score=40, recommendation="", operation="",
                position="", stop_loss="", take_profit="",
                dimension_scores={}, fit_reason="", risk_warning="",
            ),
        ]
        top = recommender.get_top_matches(matches, threshold=50, top_n=3)
        assert len(top) == 1
        assert top[0].yingyou_name == "A"


# ═══════════════════════════════════════════════════════════
# 测试: 共识分析
# ═══════════════════════════════════════════════════════════

class TestConsensusAnalyzer:
    """测试共识分析器"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        assert consensus_analyzer is not None

    def test_calc_divergence(self):
        """测试分歧度计算"""
        matches = [
            StockYingYouMatch(
                yingyou_name=f"Y{i}", ticker="T1", name="N1",
                match_score=score, recommendation="", operation="",
                position="", stop_loss="", take_profit="",
                dimension_scores={}, fit_reason="", risk_warning="",
            )
            for i, score in enumerate([80, 75, 30, 25])
        ]
        divergence = consensus_analyzer._calc_divergence(matches)
        assert divergence > 40  # 高分歧

    def test_gen_consensus_summary(self):
        """测试共识总结生成"""
        summary = consensus_analyzer._gen_consensus_summary(
            ["炒股养家", "退学炒股"], 75.0, "B"
        )
        assert "中共识" in summary
        assert "75" in summary

    def test_gen_risk_note(self):
        """测试风险注释生成"""
        note_a = consensus_analyzer._gen_risk_note("A", 80)
        assert "确定性较高" in note_a
        
        # 低一致性时提示分歧
        note_weak = consensus_analyzer._gen_risk_note("C", 30)
        assert "分歧" in note_weak or "观望" in note_weak or "谨慎" in note_weak
        
        # 高一致性但弱共识
        note_c_high = consensus_analyzer._gen_risk_note("C", 80)
        assert "观望" in note_c_high or "较弱" in note_c_high


# ═══════════════════════════════════════════════════════════
# 测试: 共识标的池
# ═══════════════════════════════════════════════════════════

class TestConsensusPool:
    """测试共识标的池"""

    def test_pool_initialization(self):
        """测试池初始化"""
        assert consensus_pool is not None
        assert consensus_pool.get_pool() == {}

    def test_get_stats(self):
        """测试统计信息"""
        stats = consensus_pool.get_stats()
        assert "total" in stats
        assert "last_update" in stats


# ═══════════════════════════════════════════════════════════
# 测试: 组合策略
# ═══════════════════════════════════════════════════════════

class TestPortfolioConfigFactory:
    """测试组合配置工厂"""

    def test_create_beginner(self):
        """测试新手组合"""
        config = PortfolioConfigFactory.create_beginner()
        assert config.level == "新手"
        assert config.max_position == 50
        assert config.single_position_limit == 5
        assert "退学炒股" in config.yingyou_allocation

    def test_create_intermediate(self):
        """测试进阶组合"""
        config = PortfolioConfigFactory.create_intermediate()
        assert config.level == "进阶"
        assert config.max_position == 70
        assert "炒股养家" in config.yingyou_allocation

    def test_create_advanced(self):
        """测试高手组合"""
        config = PortfolioConfigFactory.create_advanced()
        assert config.level == "高手"
        assert config.max_position == 90
        assert "Asking" in config.yingyou_allocation

    def test_get_config(self):
        """测试获取配置"""
        config = PortfolioConfigFactory.get_config("新手")
        assert config is not None
        
        config = PortfolioConfigFactory.get_config("invalid")
        assert config is None


class TestPortfolioStrategyEngine:
    """测试组合策略引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert portfolio_engine is not None

    def test_get_all_levels(self):
        """测试获取所有等级"""
        levels = portfolio_engine.get_all_levels()
        assert "新手" in levels
        assert "进阶" in levels
        assert "高手" in levels

    def test_get_level_description(self):
        """测试等级描述"""
        desc = portfolio_engine.get_level_description("新手")
        assert desc["level"] == "新手"
        assert "max_position" in desc

    def test_emotion_to_position(self):
        """测试情绪到仓位映射"""
        max_pos = 100
        assert portfolio_engine._emotion_to_position("冰点", max_pos) == 30
        assert portfolio_engine._emotion_to_position("修复", max_pos) == 80
        assert portfolio_engine._emotion_to_position("高潮", max_pos) == 40
        assert portfolio_engine._emotion_to_position("退潮", max_pos) == 0


# ═══════════════════════════════════════════════════════════
# 集成测试
# ═══════════════════════════════════════════════════════════

class TestIntegration:
    """集成测试"""

    def test_full_fingerprint_coverage(self):
        """测试所有游资指纹完整性"""
        all_names = registry.list_all()
        required_fields = [
            "name", "nickname", "philosophy", "stock_selection",
            "entry_timing", "risk_control", "classic_tactics",
            "radar_scores", "position_strategy", "applicable_cycles",
        ]
        
        for name in all_names:
            fp = registry.get(name)
            assert fp is not None, f"游资{name}指纹不存在"
            
            for field in required_fields:
                assert hasattr(fp, field), f"游资{name}缺少字段{field}"

    def test_diagnosis_components_integration(self):
        """测试诊断组件集成"""
        # 创建模拟数据
        emotion = EmotionPhase(
            phase="修复",
            confidence=0.7,
            indicators={},
            position_suggestion="50-70%",
            operation_suggestion="积极做多",
        )
        
        fund = FundDirection(
            primary_direction="AI",
            secondary_direction="半导体",
            hot_themes=[],
            fund_flow_score=60.0,
            activity_level="中",
            inflow_sectors=[],
            outflow_sectors=[],
        )
        
        # 计算契合度
        fits = diagnosis_engine.fit_calculator.calculate(emotion, fund)
        assert len(fits) >= 8
        
        # 检查契合度排序
        for i in range(len(fits) - 1):
            assert fits[i].fit_score >= fits[i + 1].fit_score


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])