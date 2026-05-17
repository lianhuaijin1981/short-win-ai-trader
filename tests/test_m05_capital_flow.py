"""资金流战法单元测试 — 验证6大资金流主播战法数据完整性

测试覆盖:
- 战法基础信息完整性
- 核心战法定义完整性
- 操作要点完整性
- 风控纪律完整性
- 分类与标签正确性
- 查找函数正确性

Author: SWAT Engine
Version: 1.0.0
"""

import pytest
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from short_win_ai_trader.modules.m05_tactic_screening.capital_flow_library import (
    ALL_CAPITAL_FLOW_TACTICS,
    CAPITAL_FLOW_BY_RISK,
    CAPITAL_FLOW_BY_STREAMER,
    CAPITAL_FLOW_BY_TAG,
    get_capital_flow_tactic_by_code,
    get_capital_flow_tactic_by_name,
    get_capital_flow_summary_stats,
    capital_flow_tactic_to_dict,
    CapitalFlowTactic,
    # 导入具体战法定义
    CAIJINBEIER_TACTIC,
    ABAOLOONG_TACTIC,
    XIAOYAOFENG_TACTIC,
    LANGGE_TACTIC,
    ZHISHI_TACTIC,
    LAOSIJI_TACTIC,
)
from short_win_ai_trader.modules.m05_tactic_screening.tactics_library import (
    get_all_tactics_with_categories,
    get_tactics_by_category,
)


# ──────────────────────────────────────────────────────────
# 测试数据完整性
# ──────────────────────────────────────────────────────────

class TestCapitalFlowTacticDataIntegrity:
    """测试资金流战法数据完整性"""

    def test_total_tactic_count(self):
        """测试总战法数量=6"""
        assert len(ALL_CAPITAL_FLOW_TACTICS) == 6

    def test_all_tactics_have_required_fields(self):
        """测试所有战法都包含必需字段"""
        required_str_fields = ["name", "code", "streamer_name", "streamer_title", "philosophy", "category"]
        required_list_fields = ["core_tactics", "operation_points", "risk_discipline", "tags"]

        for tactic in ALL_CAPITAL_FLOW_TACTICS:
            # 字符串字段
            for field in required_str_fields:
                value = getattr(tactic, field, None)
                assert value is not None, f"{tactic.code}.{field} 为 None"
                assert isinstance(value, str), f"{tactic.code}.{field} 不是字符串"
                assert len(value.strip()) > 0, f"{tactic.code}.{field} 为空"

            # 列表字段
            for field in required_list_fields:
                value = getattr(tactic, field, None)
                assert value is not None, f"{tactic.code}.{field} 为 None"
                assert isinstance(value, list), f"{tactic.code}.{field} 不是列表"
                assert len(value) > 0, f"{tactic.code}.{field} 为空列表"

            # risk_level
            assert tactic.risk_level in ["low", "medium", "high", "extreme"]

    def test_all_core_tactics_have_required_fields(self):
        """测试所有核心子战法都包含必需字段"""
        for tactic in ALL_CAPITAL_FLOW_TACTICS:
            for i, core in enumerate(tactic.core_tactics):
                assert "name" in core, f"{tactic.code}.core_tactics[{i}] 缺少 name"
                assert "interpretation" in core, f"{tactic.code}.core_tactics[{i}] 缺少 interpretation"
                assert "key_points" in core, f"{tactic.code}.core_tactics[{i}] 缺少 key_points"
                assert len(core["name"]) > 0
                assert len(core["interpretation"]) > 0
                assert len(core["key_points"]) > 0

    def test_category_is_capital_flow(self):
        """测试所有战法大类为'资金流'"""
        for tactic in ALL_CAPITAL_FLOW_TACTICS:
            assert tactic.category == "资金流", f"{tactic.code} 大类不是 '资金流'"


# ──────────────────────────────────────────────────────────
# 测试各主播战法具体内容
# ──────────────────────────────────────────────────────────

class TestStreamerTacticsContent:
    """测试各主播战法内容完整性"""

    def test_caijinbeier_tactic(self):
        """测试财金贝儿战法内容"""
        t = CAIJINBEIER_TACTIC
        assert t.streamer_name == "财金贝儿"
        assert "500万" in t.streamer_title
        assert "三维资金" in t.philosophy or "聪明钱" in t.philosophy
        assert len(t.core_tactics) >= 3
        # 检查子战法名称
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "三维资金共振法" in tactic_names
        assert "北向资金赛道映射法" in tactic_names
        assert "资金分歧转一致战法" in tactic_names
        # 检查操作要点
        assert any("北向资金" in point for point in t.operation_points)
        assert any("板块资金" in point for point in t.operation_points)
        # 检查风控纪律
        assert any("维度" in d for d in t.risk_discipline)

    def test_abaoloong_tactic(self):
        """测试阿宝龙哥战法内容"""
        t = ABAOLOONG_TACTIC
        assert t.streamer_name == "阿宝龙哥"
        assert "龙虎榜" in t.streamer_title
        assert "龙虎榜" in t.philosophy and "资金流" in t.philosophy
        assert len(t.core_tactics) >= 3
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "龙虎榜黄金组合战法" in tactic_names
        assert "三日榜资金流确认法" in tactic_names
        assert "资金承接强度量化法" in tactic_names
        assert any("一家独大" in d for d in t.risk_discipline)

    def test_xiaoyaofeng_tactic(self):
        """测试作手逍遥风战法内容"""
        t = XIAOYAOFENG_TACTIC
        assert t.streamer_name == "作手逍遥风"
        assert "央视" in t.streamer_title
        assert "情绪周期" in t.philosophy or "四阶段" in t.philosophy
        assert len(t.core_tactics) >= 3
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "爆点低吸战法" in tactic_names
        assert "趋势情绪资金法" in tactic_names
        assert "太极缠丝做T法" in tactic_names
        assert any("爆点" in point for point in t.operation_points)

    def test_langge_tactic(self):
        """测试浪哥财经战法内容"""
        t = LANGGE_TACTIC
        assert t.streamer_name == "浪哥财经"
        assert "主力" in t.streamer_title
        assert "假动作" in t.philosophy or "四步法" in t.philosophy
        assert len(t.core_tactics) >= 3
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "资金流四步法" in tactic_names
        assert "资金断层战法" in tactic_names
        assert "资金背离逃顶法" in tactic_names
        assert any("建仓" in point for point in t.operation_points)

    def test_zhishi_tactic(self):
        """测试芝士财经战法内容"""
        t = ZHISHI_TACTIC
        assert t.streamer_name == "芝士财经"
        assert "量化" in t.streamer_title
        assert "量化" in t.philosophy or "可量化" in t.philosophy
        assert len(t.core_tactics) >= 3
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "资金流量化选股模型" in tactic_names
        assert "资金流强度评分法" in tactic_names
        assert "资金流背离量化法" in tactic_names
        assert any("量化" in point for point in t.operation_points)

    def test_laosiji_tactic(self):
        """测试股海老司机战法内容"""
        t = LAOSIJI_TACTIC
        assert t.streamer_name == "股海老司机"
        assert "筹码" in t.streamer_title
        assert "筹码" in t.philosophy and "资金流" in t.philosophy
        assert len(t.core_tactics) >= 3
        tactic_names = [ct["name"] for ct in t.core_tactics]
        assert "资金筹码共振战法" in tactic_names
        assert "资金筹码断层战法" in tactic_names
        assert "资金筹码背离战法" in tactic_names
        assert any("筹码峰" in point for point in t.operation_points)


# ──────────────────────────────────────────────────────────
# 测试分类和索引
# ──────────────────────────────────────────────────────────

class TestClassificationAndIndex:
    """测试分类和索引功能"""

    def test_by_streamer_index(self):
        """测试按主播索引"""
        assert len(CAPITAL_FLOW_BY_STREAMER) == 6
        streamers = ["财金贝儿", "阿宝龙哥", "作手逍遥风", "浪哥财经", "芝士财经", "股海老司机"]
        for name in streamers:
            assert name in CAPITAL_FLOW_BY_STREAMER, f"主播 {name} 未在索引中"

    def test_by_risk_classification(self):
        """测试按风险等级分类"""
        total = sum(len(tactics) for tactics in CAPITAL_FLOW_BY_RISK.values())
        assert total == 6

    def test_by_tag_classification(self):
        """测试按标签分类"""
        assert len(CAPITAL_FLOW_BY_TAG) > 0
        # 检查一些预期标签
        expected_tags = ["资金流", "主力资金", "筹码峰"]
        for tag in expected_tags:
            assert tag in CAPITAL_FLOW_BY_TAG, f"标签 '{tag}' 未在分类中"


# ──────────────────────────────────────────────────────────
# 测试查找函数
# ──────────────────────────────────────────────────────────

class TestLookupFunctions:
    """测试查找函数"""

    def test_find_by_code(self):
        """测试按编码查找"""
        t = get_capital_flow_tactic_by_code("CAPITAL_3D_RESONANCE")
        assert t is not None
        assert t.streamer_name == "财金贝儿"

        t = get_capital_flow_tactic_by_code("CAPITAL_DRAGON_TIGER")
        assert t is not None
        assert t.streamer_name == "阿宝龙哥"

    def test_find_by_name(self):
        """测试按名称查找"""
        t = get_capital_flow_tactic_by_name("资金流四步法")
        assert t is not None
        assert t.streamer_name == "浪哥财经"

        t = get_capital_flow_tactic_by_name("资金情绪四阶段模型")
        assert t is not None
        assert t.streamer_name == "作手逍遥风"

    def test_find_not_found(self):
        """测试查找不存在的战法"""
        assert get_capital_flow_tactic_by_code("NOT_EXIST") is None
        assert get_capital_flow_tactic_by_name("不存在") is None


# ──────────────────────────────────────────────────────────
# 测试统计和转换函数
# ──────────────────────────────────────────────────────────

class TestStatsAndConversion:
    """测试统计和转换函数"""

    def test_summary_stats(self):
        """测试统计摘要"""
        stats = get_capital_flow_summary_stats()
        assert stats["total_count"] == 6
        assert stats["category"] == "资金流"
        assert "low" in stats["risk_distribution"]
        assert "medium" in stats["risk_distribution"]
        assert len(stats["streamer_list"]) == 6
        assert len(stats["all_tags"]) > 0

    def test_tactic_to_dict(self):
        """测试战法转字典"""
        t = CAIJINBEIER_TACTIC
        d = capital_flow_tactic_to_dict(t)
        assert d["name"] == t.name
        assert d["code"] == t.code
        assert d["streamer_name"] == t.streamer_name
        assert d["philosophy"] == t.philosophy
        assert len(d["core_tactics"]) == len(t.core_tactics)
        assert len(d["operation_points"]) == len(t.operation_points)
        assert len(d["risk_discipline"]) == len(t.risk_discipline)

    def test_category_integration(self):
        """测试与主战法库的分类集成"""
        categories = get_all_tactics_with_categories()
        assert "categories" in categories
        assert "量化战法" in categories["categories"]
        assert "资金流战法" in categories["categories"]
        assert categories["total_capital_flow"] == 6
        assert categories["grand_total"] == 15 + 6  # 量化15 + 资金流6

    def test_get_tactics_by_category(self):
        """测试按大类获取战法"""
        cf_tactics = get_tactics_by_category("资金流战法")
        assert len(cf_tactics) == 6
        quant_tactics = get_tactics_by_category("量化战法")
        assert len(quant_tactics) == 15
        empty = get_tactics_by_category("不存在")
        assert len(empty) == 0


# ──────────────────────────────────────────────────────────
# 运行测试
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
