"""资金流战法集成测试 — 验证6大资金流主播战法作为标准TacticRuleSet的集成

测试覆盖:
- 战法存在性与标准API访问
- 战法数据结构完整性（hard_conditions/shape_conditions等）
- 大类分类索引正确性
- 与原有15套战法的兼容性
- 各主播战法内容准确性

所有测试基于 tactics_library 标准接口，不依赖已删除的 capital_flow_library。

Author: SWAT Engine
Version: 2.0.0
"""

import pytest
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from short_win_ai_trader.modules.m05_tactic_screening.tactics_library import (
    ALL_TACTICS,
    TACTICS_BY_CATEGORY,
    TACTICS_BY_RISK,
    TacticRuleSet,
    get_tactic_by_code,
    get_tactic_by_name,
    get_tactics_by_category,
    get_all_categories,
    list_all_tactics,
    get_tactics_summary_stats,
)


# ──────────────────────────────────────────────────────────
# 测试常量
# ──────────────────────────────────────────────────────────

# 6个资金流战法编码
CAPITAL_FLOW_CODES = [
    "CAPITAL_3D_RESONANCE",
    "CAPITAL_DRAGON_TIGER",
    "CAPITAL_EMOTION_4PHASE",
    "CAPITAL_4STEP_METHOD",
    "CAPITAL_QUANT_INDEX",
    "CAPITAL_CHIP_RESONANCE",
]

# 6个资金流战法名称
CAPITAL_FLOW_NAMES = [
    "三维资金共振法",
    "龙虎榜资金流战法",
    "资金情绪四阶段模型",
    "资金流四步法",
    "资金流量化指标体系",
    "资金筹码共振战法",
]

# 主播名称与战法名称的对应关系
STREAMER_TACTIC_MAP = {
    "财金贝儿": "三维资金共振法",
    "阿宝龙哥": "龙虎榜资金流战法",
    "作手逍遥风": "资金情绪四阶段模型",
    "浪哥财经": "资金流四步法",
    "芝士财经": "资金流量化指标体系",
    "股海老司机": "资金筹码共振战法",
}

# 编码与主播名称的对应关系
CODE_STREAMER_MAP = {
    "CAPITAL_3D_RESONANCE": "财金贝儿",
    "CAPITAL_DRAGON_TIGER": "阿宝龙哥",
    "CAPITAL_EMOTION_4PHASE": "作手逍遥风",
    "CAPITAL_4STEP_METHOD": "浪哥财经",
    "CAPITAL_QUANT_INDEX": "芝士财经",
    "CAPITAL_CHIP_RESONANCE": "股海老司机",
}


# ──────────────────────────────────────────────────────────
# 1. 战法存在性测试
# ──────────────────────────────────────────────────────────

class TestCapitalFlowTacticExistence:
    """测试资金流战法在ALL_TACTICS中的存在性"""

    def test_total_tactic_count_including_capital_flow(self):
        """测试总战法数量 = 15(原有) + 6(资金流) = 21"""
        assert len(ALL_TACTICS) == 21, (
            f"ALL_TACTICS 应包含21个战法(15个原有 + 6个资金流), "
            f"实际有 {len(ALL_TACTICS)} 个"
        )

    def test_all_six_capital_flow_codes_exist(self):
        """测试ALL_TACTICS包含全部6个资金流战法编码"""
        all_codes = [t.code for t in ALL_TACTICS]
        for code in CAPITAL_FLOW_CODES:
            assert code in all_codes, f"资金流战法编码 '{code}' 不在 ALL_TACTICS 中"

    def test_all_six_capital_flow_names_exist(self):
        """测试ALL_TACTICS包含全部6个资金流战法名称"""
        all_names = [t.name for t in ALL_TACTICS]
        for name in CAPITAL_FLOW_NAMES:
            assert name in all_names, f"资金流战法名称 '{name}' 不在 ALL_TACTICS 中"

    def test_get_tactic_by_code_for_capital_flow(self):
        """测试通过get_tactic_by_code()可查找所有资金流战法"""
        for code in CAPITAL_FLOW_CODES:
            tactic = get_tactic_by_code(code)
            assert tactic is not None, f"get_tactic_by_code('{code}') 返回 None"
            assert isinstance(tactic, TacticRuleSet), (
                f"编码 '{code}' 返回的不是 TacticRuleSet 实例"
            )
            assert tactic.code == code

    def test_get_tactic_by_code_returns_correct_streamer(self):
        """测试通过编码查找返回正确的战法与主播对应关系"""
        for code, expected_streamer in CODE_STREAMER_MAP.items():
            tactic = get_tactic_by_code(code)
            assert tactic is not None
            assert expected_streamer in tactic.description, (
                f"战法 '{code}' 的 description 应包含主播名称 '{expected_streamer}'"
            )

    def test_get_tactic_by_name_for_capital_flow(self):
        """测试通过get_tactic_by_name()可查找所有资金流战法"""
        for name in CAPITAL_FLOW_NAMES:
            tactic = get_tactic_by_name(name)
            assert tactic is not None, f"get_tactic_by_name('{name}') 返回 None"
            assert isinstance(tactic, TacticRuleSet)
            assert tactic.name == name

    def test_get_tactic_by_code_not_found(self):
        """测试查找不存在的编码返回None"""
        assert get_tactic_by_code("CAPITAL_NOT_EXIST") is None

    def test_get_tactic_by_name_not_found(self):
        """测试查找不存在的名称返回None"""
        assert get_tactic_by_name("不存在战法") is None


# ──────────────────────────────────────────────────────────
# 2. 战法数据结构测试
# ──────────────────────────────────────────────────────────

class TestCapitalFlowTacticDataStructure:
    """测试资金流战法数据结构完整性"""

    def test_all_capital_flow_have_category_capital_flow(self):
        """测试所有资金流战法的 category 字段为 '资金流'"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert tactic.category == "资金流", (
                f"战法 '{tactic.code}' 的 category 应为 '资金流', "
                f"实际是 '{tactic.category}'"
            )

    def test_all_capital_flow_have_hard_conditions(self):
        """测试所有资金流战法有完整的hard_conditions（5项）"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert len(tactic.hard_conditions) == 5, (
                f"战法 '{tactic.code}' 应有5项 hard_conditions, "
                f"实际有 {len(tactic.hard_conditions)} 项"
            )

    def test_all_capital_flow_hard_conditions_have_required_fields(self):
        """测试hard_conditions每项都有必需的字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        required_fields = ["name", "indicator", "operator", "threshold", "weight", "description"]
        for tactic in capital_flow_tactics:
            for i, cond in enumerate(tactic.hard_conditions):
                for field in required_fields:
                    assert field in cond, (
                        f"战法 '{tactic.code}' 的 hard_conditions[{i}] 缺少字段 '{field}'"
                    )

    def test_all_capital_flow_have_shape_conditions(self):
        """测试所有资金流战法有完整的shape_conditions（3项）"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert len(tactic.shape_conditions) == 3, (
                f"战法 '{tactic.code}' 应有3项 shape_conditions, "
                f"实际有 {len(tactic.shape_conditions)} 项"
            )

    def test_all_capital_flow_shape_conditions_have_required_fields(self):
        """测试shape_conditions每项都有必需的字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        required_fields = ["name", "indicator", "operator", "threshold", "weight", "description"]
        for tactic in capital_flow_tactics:
            for i, cond in enumerate(tactic.shape_conditions):
                for field in required_fields:
                    assert field in cond, (
                        f"战法 '{tactic.code}' 的 shape_conditions[{i}] 缺少字段 '{field}'"
                    )

    def test_all_capital_flow_have_description_with_streamer(self):
        """测试所有资金流战法description字段包含对应主播名称"""
        for code, expected_streamer in CODE_STREAMER_MAP.items():
            tactic = get_tactic_by_code(code)
            assert tactic is not None
            assert tactic.description and len(tactic.description) > 0, (
                f"战法 '{code}' 的 description 为空"
            )
            assert expected_streamer in tactic.description, (
                f"战法 '{code}' 的 description 应包含主播 '{expected_streamer}', "
                f"实际描述: {tactic.description[:100]}..."
            )

    def test_all_capital_flow_have_risk_level(self):
        """测试所有资金流战法有有效的risk_level字段"""
        valid_risk_levels = ["low", "medium", "high", "extreme"]
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert tactic.risk_level in valid_risk_levels, (
                f"战法 '{tactic.code}' 的 risk_level '{tactic.risk_level}' 无效, "
                f"应为 {valid_risk_levels} 之一"
            )

    def test_all_capital_flow_have_hold_period(self):
        """测试所有资金流战法有hold_period字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert tactic.hold_period and len(tactic.hold_period) > 0, (
                f"战法 '{tactic.code}' 的 hold_period 为空"
            )

    def test_all_capital_flow_have_applicable_cycles(self):
        """测试所有资金流战法有applicable_cycles字段（非空列表）"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert isinstance(tactic.applicable_cycles, list), (
                f"战法 '{tactic.code}' 的 applicable_cycles 不是列表"
            )
            assert len(tactic.applicable_cycles) > 0, (
                f"战法 '{tactic.code}' 的 applicable_cycles 为空列表"
            )

    def test_all_capital_flow_have_best_env(self):
        """测试所有资金流战法有best_env字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert isinstance(tactic.best_env, dict), (
                f"战法 '{tactic.code}' 的 best_env 不是字典"
            )
            assert len(tactic.best_env) > 0, (
                f"战法 '{tactic.code}' 的 best_env 为空"
            )

    def test_all_capital_flow_have_risk_boundary(self):
        """测试所有资金流战法有risk_boundary字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert isinstance(tactic.risk_boundary, dict), (
                f"战法 '{tactic.code}' 的 risk_boundary 不是字典"
            )
            assert len(tactic.risk_boundary) > 0, (
                f"战法 '{tactic.code}' 的 risk_boundary 为空"
            )

    def test_all_capital_flow_have_core_logic(self):
        """测试所有资金流战法有core_logic字段"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert tactic.core_logic and len(tactic.core_logic) > 0, (
                f"战法 '{tactic.code}' 的 core_logic 为空"
            )

    def test_capital_flow_tactics_are_tactic_rule_set_instances(self):
        """测试所有资金流战法都是TacticRuleSet实例"""
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            assert isinstance(tactic, TacticRuleSet), (
                f"战法 '{tactic.code}' 不是 TacticRuleSet 实例, "
                f"实际是 {type(tactic).__name__}"
            )


# ──────────────────────────────────────────────────────────
# 3. 大类分类索引测试
# ──────────────────────────────────────────────────────────

class TestCategoryIndex:
    """测试TACTICS_BY_CATEGORY大类分类索引"""

    def test_category_index_contains_capital_flow(self):
        """测试TACTICS_BY_CATEGORY包含'资金流'大类"""
        assert "资金流" in TACTICS_BY_CATEGORY, (
            f"TACTICS_BY_CATEGORY 中缺少 '资金流' 大类, 现有: {list(TACTICS_BY_CATEGORY.keys())}"
        )

    def test_capital_flow_category_has_six_tactics(self):
        """测试'资金流'大类下有6个战法"""
        capital_flow_tactics = TACTICS_BY_CATEGORY.get("资金流", [])
        assert len(capital_flow_tactics) == 6, (
            f"'资金流' 大类应有6个战法, 实际有 {len(capital_flow_tactics)} 个"
        )

    def test_capital_flow_category_all_correct_codes(self):
        """测试'资金流'大类下的战法编码正确"""
        capital_flow_tactics = TACTICS_BY_CATEGORY.get("资金流", [])
        codes = [t.code for t in capital_flow_tactics]
        for expected_code in CAPITAL_FLOW_CODES:
            assert expected_code in codes, (
                f"'资金流' 大类中缺少战法 '{expected_code}'"
            )

    def test_get_tactics_by_category_capital_flow(self):
        """测试通过get_tactics_by_category('资金流')获取资金流战法"""
        tactics = get_tactics_by_category("资金流")
        assert len(tactics) == 6, (
            f"get_tactics_by_category('资金流') 应返回6个战法, "
            f"实际返回 {len(tactics)} 个"
        )

    def test_get_tactics_by_category_returns_tactic_rule_set(self):
        """测试get_tactics_by_category返回TacticRuleSet实例列表"""
        tactics = get_tactics_by_category("资金流")
        for tactic in tactics:
            assert isinstance(tactic, TacticRuleSet), (
                f"get_tactics_by_category('资金流') 返回了非 TacticRuleSet 实例: {type(tactic)}"
            )

    def test_get_tactics_by_category_empty_for_invalid(self):
        """测试对不存在的大类返回空列表"""
        tactics = get_tactics_by_category("不存在的大类")
        assert tactics == []

    def test_get_all_categories_contains_capital_flow(self):
        """测试get_all_categories()返回结果包含资金流大类"""
        categories_info = get_all_categories()
        assert "categories" in categories_info
        categories = categories_info["categories"]
        assert "资金流" in categories, (
            f"get_all_categories() 返回中缺少 '资金流', 现有: {list(categories.keys())}"
        )

    def test_get_all_categories_capital_flow_has_count(self):
        """测试get_all_categories()中资金流大类的计数为6"""
        categories_info = get_all_categories()
        capital_flow_info = categories_info["categories"]["资金流"]
        assert capital_flow_info["count"] == 6, (
            f"get_all_categories() 中 '资金流' 的 count 应为6, "
            f"实际是 {capital_flow_info['count']}"
        )

    def test_get_all_categories_total_tactics_is_21(self):
        """测试get_all_categories()返回的total_tactics为21"""
        categories_info = get_all_categories()
        assert categories_info["total_tactics"] == 21, (
            f"get_all_categories() 的 total_tactics 应为21, "
            f"实际是 {categories_info['total_tactics']}"
        )

    def test_category_does_not_mix_with_other_categories(self):
        """测试资金流战法不会出现在其他大类中"""
        for category, tactics in TACTICS_BY_CATEGORY.items():
            if category == "资金流":
                continue
            for tactic in tactics:
                assert tactic.code not in CAPITAL_FLOW_CODES, (
                    f"资金流战法 '{tactic.code}' 不应出现在 '{category}' 大类中"
                )


# ──────────────────────────────────────────────────────────
# 4. 与其他战法的兼容性测试
# ──────────────────────────────────────────────────────────

class TestCompatibilityWithExistingTactics:
    """测试资金流战法与原有战法的兼容性"""

    def test_capital_flow_appears_in_list_all_tactics(self):
        """测试资金流战法出现在list_all_tactics()结果中"""
        all_tactics_list = list_all_tactics()
        capital_flow_in_list = [
            item for item in all_tactics_list
            if item["code"] in CAPITAL_FLOW_CODES
        ]
        assert len(capital_flow_in_list) == 6, (
            f"list_all_tactics() 中应包含6个资金流战法, "
            f"实际包含 {len(capital_flow_in_list)} 个"
        )

    def test_list_all_tactics_total_count_is_21(self):
        """测试list_all_tactics()返回总数为21"""
        all_tactics_list = list_all_tactics()
        assert len(all_tactics_list) == 21, (
            f"list_all_tactics() 应返回21个战法, "
            f"实际返回 {len(all_tactics_list)} 个"
        )

    def test_capital_flow_in_summary_stats(self):
        """测试资金流战法出现在统计摘要中"""
        stats = get_tactics_summary_stats()
        assert stats["total_tactics"] == 21
        assert len(stats["tactic_codes"]) == 21
        assert len(stats["tactic_names"]) == 21
        for code in CAPITAL_FLOW_CODES:
            assert code in stats["tactic_codes"], (
                f"统计摘要中缺少资金流战法编码 '{code}'"
            )

    def test_existing_15_tactics_still_exist(self):
        """测试原有15个战法仍然存在且不受影响"""
        existing_codes = [
            "CHIP_PEAK", "TRIPLE_VOL_BREAK", "SHRINK_VOL_BREAK",
            "LEFT_PEAK_BREAK", "FIRST_YIN", "N_SHAPE",
            "MAGPIE_PLUM", "PLATFORM_BREAK", "BOARD_1TO2",
            "DRAGON_EMOTION", "BOLLINGER", "INTRADAY_SUPPORT",
            "TRIPLE_BOTTOM", "ANTI_NUCLEAR", "SHRINK_TAIL_PREEMPT",
        ]
        all_codes = [t.code for t in ALL_TACTICS]
        for code in existing_codes:
            assert code in all_codes, f"原有战法 '{code}' 不在 ALL_TACTICS 中"

    def test_capital_flow_in_risk_classification(self):
        """测试资金流战法被正确分类到TACTICS_BY_RISK中"""
        total_in_risk = sum(len(tactics) for tactics in TACTICS_BY_RISK.values())
        assert total_in_risk == 21, (
            f"TACTICS_BY_RISK 中所有战法总数应为21, 实际是 {total_in_risk}"
        )
        # 资金流战法应出现在某个风险等级中
        capital_flow_tactics = [t for t in ALL_TACTICS if t.code in CAPITAL_FLOW_CODES]
        for tactic in capital_flow_tactics:
            risk_group = TACTICS_BY_RISK.get(tactic.risk_level, [])
            assert tactic in risk_group, (
                f"资金流战法 '{tactic.code}' 未在 TACTICS_BY_RISK["
                f"'{tactic.risk_level}'] 中"
            )

    def test_no_duplicate_codes(self):
        """测试所有战法编码唯一，无重复"""
        all_codes = [t.code for t in ALL_TACTICS]
        assert len(all_codes) == len(set(all_codes)), (
            f"存在重复的战法编码: {all_codes}"
        )

    def test_no_duplicate_names(self):
        """测试所有战法名称唯一，无重复"""
        all_names = [t.name for t in ALL_TACTICS]
        assert len(all_names) == len(set(all_names)), (
            f"存在重复的战法名称"
        )


# ──────────────────────────────────────────────────────────
# 5. 每个战法的内容测试
# ──────────────────────────────────────────────────────────

class TestIndividualTacticContent:
    """测试每个资金流战法的具体内容准确性"""

    def test_caijinbeier_3d_resonance(self):
        """测试财金贝儿-三维资金共振法: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_3D_RESONANCE")
        assert tactic is not None
        assert tactic.name == "三维资金共振法"
        assert "财金贝儿" in tactic.description
        assert tactic.category == "资金流"

    def test_abaoloong_dragon_tiger(self):
        """测试阿宝龙哥-龙虎榜资金流战法: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_DRAGON_TIGER")
        assert tactic is not None
        assert tactic.name == "龙虎榜资金流战法"
        assert "阿宝龙哥" in tactic.description
        assert tactic.category == "资金流"

    def test_xiaoyaofeng_emotion_4phase(self):
        """测试作手逍遥风-资金情绪四阶段模型: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_EMOTION_4PHASE")
        assert tactic is not None
        assert tactic.name == "资金情绪四阶段模型"
        assert "作手逍遥风" in tactic.description
        assert tactic.category == "资金流"

    def test_langge_4step_method(self):
        """测试浪哥财经-资金流四步法: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_4STEP_METHOD")
        assert tactic is not None
        assert tactic.name == "资金流四步法"
        assert "浪哥财经" in tactic.description
        assert tactic.category == "资金流"

    def test_zhishi_quant_index(self):
        """测试芝士财经-资金流量化指标体系: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_QUANT_INDEX")
        assert tactic is not None
        assert tactic.name == "资金流量化指标体系"
        assert "芝士财经" in tactic.description
        assert tactic.category == "资金流"

    def test_laosiji_chip_resonance(self):
        """测试股海老司机-资金筹码共振战法: 编码、名称、主播名称"""
        tactic = get_tactic_by_code("CAPITAL_CHIP_RESONANCE")
        assert tactic is not None
        assert tactic.name == "资金筹码共振战法"
        assert "股海老司机" in tactic.description
        assert tactic.category == "资金流"

    def test_all_streamer_tactic_name_mapping(self):
        """测试所有主播名称与战法名称的对应关系"""
        for streamer, expected_name in STREAMER_TACTIC_MAP.items():
            # 通过战法名称查找
            tactic = get_tactic_by_name(expected_name)
            assert tactic is not None, (
                f"无法找到战法 '{expected_name}' (主播: {streamer})"
            )
            assert streamer in tactic.description, (
                f"战法 '{expected_name}' 的 description 应包含主播 '{streamer}'"
            )


# ──────────────────────────────────────────────────────────
# 运行测试
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
