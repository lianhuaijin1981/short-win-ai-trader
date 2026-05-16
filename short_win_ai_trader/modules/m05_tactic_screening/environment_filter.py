"""战法场景适配过滤引擎 — 情绪周期与战法错配防控

核心功能:
  1. 根据当前情绪周期，筛选适宜战法清单
  2. 根据当前情绪周期，生成禁忌战法清单
  3. 场景错配检测: 识别在当前环境下不适用的战法匹配
  4. 仓位建议: 根据周期给出战法使用仓位上限

情绪周期-战法适配矩阵:
  混沌期 → 底部战法、潜伏战法、低仓位试错
  启动期 → 突破战法、一进二、低吸核心
  发酵期 → 全战法适用，重点关注龙头/接力
  高潮期 → 止盈为主，谨慎追高
  分歧期 → 首阴低吸、反核、快进快出
  退潮期 → 全面防守，禁忌高位接力/追涨

Author: SWAT Engine
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...core.logger import get_logger
from ...data_platform.data_models import TacticMatchResult
from .tactics_library import (
    ALL_TACTICS,
    TACTICS_BY_CYCLE,
    TacticRuleSet,
)

logger = get_logger("swat.m05.env_filter")


# ──────────────────────────────────────────────────────────
# 情绪周期-战法适配配置
# ──────────────────────────────────────────────────────────

# 各周期适宜战法 (code列表)
SUITABLE_TACTICS_BY_CYCLE: Dict[str, List[str]] = {
    "混沌期": [
        "MAGPIE_PLUM",        # 喜鹊闹梅: 底部反转
        "TRIPLE_BOTTOM",      # 三星探底: 三次探底
        "BOLLINGER",          # 布林带: 收口待突破
        "SHRINK_TAIL_PREEMPT",# 缩量尾盘: 逆向布局
        "SHRINK_VOL_BREAK",   # 缩量突破: 底部缩量突破
    ],
    "启动期": [
        "TRIPLE_VOL_BREAK",   # 三倍量突破: 启动放量
        "PLATFORM_BREAK",     # 平台突破: 横盘后启动
        "BOARD_1TO2",         # 一进二: 首板接力
        "LEFT_PEAK_BREAK",    # 过左峰: 突破前高
        "DRAGON_EMOTION",     # 龙头情绪: 识别龙头
        "CHIP_PEAK",          # 筹码峰: 低位单峰
        "INTRADAY_SUPPORT",   # 分时承接: 盘中低吸
    ],
    "发酵期": [
        "TRIPLE_VOL_BREAK",   # 三倍量突破
        "BOARD_1TO2",         # 一进二
        "DRAGON_EMOTION",     # 龙头情绪
        "N_SHAPE",            # N字形: 二波启动
        "LEFT_PEAK_BREAK",    # 过左峰
        "PLATFORM_BREAK",     # 平台突破
        "FIRST_YIN",          # 首阴: 龙头分歧
        "CHIP_PEAK",          # 筹码峰
        "SHRINK_VOL_BREAK",   # 缩量突破
        "INTRADAY_SUPPORT",   # 分时承接
        "ANTI_NUCLEAR",       # 反核
    ],
    "高潮期": [
        "DRAGON_EMOTION",     # 龙头情绪: 龙头止盈
        "FIRST_YIN",          # 首阴: 分歧低吸（谨慎）
        "INTRADAY_SUPPORT",   # 分时承接
        "SHRINK_TAIL_PREEMPT",# 缩量尾盘: 逆向
    ],
    "分歧期": [
        "FIRST_YIN",          # 首阴: 核心战法
        "ANTI_NUCLEAR",       # 反核: 超预期修复
        "INTRADAY_SUPPORT",   # 分时承接
        "SHRINK_TAIL_PREEMPT",# 缩量尾盘
        "N_SHAPE",            # N字形: 二波分歧后
    ],
    "退潮期": [
        # 退潮期禁忌战法多，适宜战法极少
        "SHRINK_TAIL_PREEMPT",# 缩量尾盘: 极小仓位博弈次日修复
    ],
}

# 各周期禁忌战法 (code列表)
FORBIDDEN_TACTICS_BY_CYCLE: Dict[str, List[str]] = {
    "混沌期": [
        "BOARD_1TO2",         # 一进二: 无接力氛围
        "TRIPLE_VOL_BREAK",   # 三倍量突破: 容易被骗线
        "FIRST_YIN",          # 首阴: 无龙头可吸
        "ANTI_NUCLEAR",       # 反核: 成功率极低
    ],
    "启动期": [
        "ANTI_NUCLEAR",       # 反核: 启动期无核可反
        "SHRINK_TAIL_PREEMPT",# 尾盘先手: 启动期应早盘进攻
    ],
    "发酵期": [
        # 发酵期基本无禁忌，注意仓位控制即可
    ],
    "高潮期": [
        "BOARD_1TO2",         # 一进二: 高潮期接力风险大
        "TRIPLE_VOL_BREAK",   # 三倍量突破: 容易追到短期顶
        "LEFT_PEAK_BREAK",    # 过左峰: 高潮期突破持续性差
        "N_SHAPE",            # N字形: 高潮期二波容易被砸
        "PLATFORM_BREAK",     # 平台突破: 假突破概率高
    ],
    "分歧期": [
        "BOARD_1TO2",         # 一进二: 分歧期晋级率低
        "TRIPLE_VOL_BREAK",   # 三倍量突破: 放量可能是出货
        "LEFT_PEAK_BREAK",    # 过左峰: 分歧期突破易失败
        "PLATFORM_BREAK",     # 平台突破: 假突破风险
    ],
    "退潮期": [
        "BOARD_1TO2",         # 一进二: 接力等于接刀
        "TRIPLE_VOL_BREAK",   # 三倍量突破: 诱多陷阱
        "FIRST_YIN",          # 首阴: 退潮期首阴后有更阴
        "DRAGON_EMOTION",     # 龙头情绪: 龙头补跌
        "N_SHAPE",            # N字形: 二波变二杀
        "LEFT_PEAK_BREAK",    # 过左峰: 假突破
        "PLATFORM_BREAK",     # 平台突破: 向下突破
        "INTRADAY_SUPPORT",   # 分时承接: 承接无力
        "CHIP_PEAK",          # 筹码峰: 高位密集出货
    ],
}

# 各周期仓位上限 (%)
POSITION_LIMIT_BY_CYCLE = {
    "混沌期": 20,
    "启动期": 40,
    "发酵期": 60,
    "高潮期": 30,
    "分歧期": 30,
    "退潮期": 10,
}

# 周期风险警示语
CYCLE_WARNINGS: Dict[str, List[str]] = {
    "混沌期": [
        "市场处于混沌状态，题材快速轮动无持续性",
        "建议小仓位试错，不追高已涨过的题材",
        "重点关注低位首板和底部反转形态",
    ],
    "启动期": [
        "新周期正在启动，主动进攻建立底仓",
        "重点关注新题材的首板和二板接力",
        "逐步加仓，但注意控制总仓位",
    ],
    "发酵期": [
        "主线明确，赚钱效应扩散，顺势加仓",
        "持有核心龙头，放弃跟风杂毛",
        "注意高潮信号，准备分批止盈",
    ],
    "高潮期": [
        "情绪全面高潮，风险大于机会",
        "逢高兑现利润，不追新标的",
        "严控仓位在3成以下，防范分歧",
    ],
    "分歧期": [
        "强势股开始分化，后排掉队",
        "谨慎博弈龙头首阴和反核",
        "快进快出，严格止损",
    ],
    "退潮期": [
        "情绪全面退潮，全面防守",
        "停止高位交易，规避所有杂毛",
        "优先避险，等待新周期启动",
    ],
}


# ──────────────────────────────────────────────────────────
# 场景适配过滤引擎
# ──────────────────────────────────────────────────────────

@dataclass
class EnvironmentFilterResult:
    """环境过滤结果"""
    current_cycle: str                    # 当前情绪周期
    position_limit: int                   # 仓位上限(%)
    suitable_tactics: List[Dict]          # 适宜战法列表
    forbidden_tactics: List[Dict]         # 禁忌战法列表
    filtered_results: List[Dict]          # 被过滤掉的战法匹配
    warnings: List[str]                   # 风险警示
    summary: str                          # 总结建议


class EnvironmentFilter:
    """战法场景适配过滤引擎

    根据当前市场情绪周期，自动:
    1. 推荐适宜战法
    2. 标识禁忌战法
    3. 过滤掉与当前环境错配的战法匹配结果
    4. 给出仓位建议和风险控制提示
    """

    def __init__(self):
        logger.info("战法场景适配过滤引擎初始化完成")

    def get_suitability(self, emotion_cycle: str) -> Dict[str, Any]:
        """获取指定周期的战法适配性分析

        Args:
            emotion_cycle: 情绪周期名称

        Returns:
            适配性分析字典
        """
        cycle = self._normalize_cycle(emotion_cycle)

        suitable_codes = SUITABLE_TACTICS_BY_CYCLE.get(cycle, [])
        forbidden_codes = FORBIDDEN_TACTICS_BY_CYCLE.get(cycle, [])
        position_limit = POSITION_LIMIT_BY_CYCLE.get(cycle, 20)
        warnings = CYCLE_WARNINGS.get(cycle, ["市场状态不明，保持谨慎"])

        suitable = [self._tactic_info(code) for code in suitable_codes]
        forbidden = [self._tactic_info(code) for code in forbidden_codes]

        return {
            "current_cycle": cycle,
            "position_limit": position_limit,
            "suitable_tactics": suitable,
            "forbidden_tactics": forbidden,
            "warnings": warnings,
            "suitable_count": len(suitable),
            "forbidden_count": len(forbidden),
        }

    def filter_matches(self, emotion_cycle: str,
                       matches: List[TacticMatchResult]) -> EnvironmentFilterResult:
        """过滤战法匹配结果，移除与当前环境错配的结果

        Args:
            emotion_cycle: 当前情绪周期
            matches: 战法匹配结果列表

        Returns:
            过滤结果
        """
        cycle = self._normalize_cycle(emotion_cycle)
        forbidden_codes = set(FORBIDDEN_TACTICS_BY_CYCLE.get(cycle, []))
        position_limit = POSITION_LIMIT_BY_CYCLE.get(cycle, 20)
        warnings = CYCLE_WARNINGS.get(cycle, [])

        suitable_codes = set(SUITABLE_TACTICS_BY_CYCLE.get(cycle, []))

        kept_matches = []
        filtered_matches = []

        for match in matches:
            # 查找战法编码
            tactic_code = self._find_tactic_code(match.tactic_name)

            if tactic_code in forbidden_codes:
                filtered_matches.append({
                    "tactic_name": match.tactic_name,
                    "ticker": match.ticker,
                    "reason": f"'{match.tactic_name}'在{cycle}属于禁忌战法",
                    "original_score": match.match_score,
                })
            else:
                # 额外加分: 如果是特别适宜的战法
                if tactic_code in suitable_codes:
                    match.match_score = min(110, match.match_score + 3)
                kept_matches.append(match)

        # 获取适宜/禁忌战法清单
        suitable = [self._tactic_info(c) for c in suitable_codes]
        forbidden = [self._tactic_info(c) for c in forbidden_codes]

        summary = self._generate_summary(cycle, len(kept_matches), len(filtered_matches))

        return EnvironmentFilterResult(
            current_cycle=cycle,
            position_limit=position_limit,
            suitable_tactics=suitable,
            forbidden_tactics=forbidden,
            filtered_results=filtered_matches,
            warnings=warnings,
            summary=summary,
        )

    def is_tactic_suitable(self, emotion_cycle: str,
                           tactic_code: str) -> Dict[str, Any]:
        """判断某战法在当前周期是否适合

        Args:
            emotion_cycle: 情绪周期
            tactic_code: 战法编码

        Returns:
            适配性判断结果
        """
        cycle = self._normalize_cycle(emotion_cycle)
        suitable_codes = set(SUITABLE_TACTICS_BY_CYCLE.get(cycle, []))
        forbidden_codes = set(FORBIDDEN_TACTICS_BY_CYCLE.get(cycle, []))

        if tactic_code in forbidden_codes:
            return {
                "suitable": False,
                "level": "禁忌",
                "reason": f"{tactic_code}在{cycle}属于禁忌战法，应避免使用",
                "advice": "停止操作或切换至适宜战法",
            }
        elif tactic_code in suitable_codes:
            return {
                "suitable": True,
                "level": "适宜",
                "reason": f"{tactic_code}在{cycle}表现优异，推荐使用",
                "advice": "可按正常规则参与",
            }
        else:
            return {
                "suitable": True,
                "level": "中性",
                "reason": f"{tactic_code}在{cycle}无特殊适配或禁忌标注",
                "advice": "可使用但注意仓位控制",
            }

    def get_position_advice(self, emotion_cycle: str,
                            tactic_code: Optional[str] = None) -> Dict[str, Any]:
        """获取仓位建议

        Args:
            emotion_cycle: 情绪周期
            tactic_code: 战法编码（可选）

        Returns:
            仓位建议字典
        """
        cycle = self._normalize_cycle(emotion_cycle)
        base_limit = POSITION_LIMIT_BY_CYCLE.get(cycle, 20)

        # 根据战法风险等级微调
        if tactic_code:
            tactic_info = self._tactic_info(tactic_code)
            risk_level = tactic_info.get("risk_level", "medium")
            if risk_level == "high":
                base_limit = int(base_limit * 0.7)
            elif risk_level == "extreme":
                base_limit = int(base_limit * 0.5)
            elif risk_level == "low":
                base_limit = int(base_limit * 1.1)

        return {
            "cycle": cycle,
            "tactic_code": tactic_code,
            "position_limit_pct": base_limit,
            "single_stock_max_pct": min(base_limit, 30),
            "advice": f"当前{cycle}，建议总仓位不超过{base_limit}%，单票不超过{min(base_limit, 30)}%",
        }

    def _normalize_cycle(self, cycle: str) -> str:
        """标准化情绪周期名称"""
        cycle_map = {
            "chaos": "混沌期", "start": "启动期", "ferment": "发酵期",
            "peak": "高潮期", "diverge": "分歧期", "retreat": "退潮期",
            "混沌": "混沌期", "启动": "启动期", "发酵": "发酵期",
            "高潮": "高潮期", "分歧": "分歧期", "退潮": "退潮期",
        }
        return cycle_map.get(cycle, cycle)

    def _find_tactic_code(self, tactic_name: str) -> str:
        """根据战法名称查找编码"""
        from .tactics_library import get_tactic_by_name
        tactic = get_tactic_by_name(tactic_name)
        return tactic.code if tactic else ""

    def _tactic_info(self, code: str) -> Dict[str, str]:
        """获取战法信息字典"""
        from .tactics_library import get_tactic_by_code
        tactic = get_tactic_by_code(code)
        if tactic:
            return {
                "code": tactic.code,
                "name": tactic.name,
                "risk_level": tactic.risk_level,
                "core_logic": tactic.core_logic[:50] + "...",
            }
        return {"code": code, "name": code, "risk_level": "unknown", "core_logic": ""}

    def _generate_summary(self, cycle: str, kept: int, filtered: int) -> str:
        """生成过滤总结"""
        total = kept + filtered
        if total == 0:
            return f"当前{cycle}，无战法匹配结果"

        ratio = filtered / total * 100
        if cycle == "退潮期":
            return (
                f"退潮期全面防守: 共{total}条匹配，过滤{filtered}条({ratio:.0f}%)，"
                f"仅剩{kept}条符合要求的匹配"
            )
        elif cycle == "高潮期":
            return (
                f"高潮期谨慎参与: 共{total}条匹配，过滤{filtered}条({ratio:.0f}%)，"
                f"保留{kept}条（主要为龙头和低吸）"
            )
        elif cycle == "混沌期":
            return (
                f"混沌期小仓位试错: 共{total}条匹配，过滤{filtered}条({ratio:.0f}%)，"
                f"保留{kept}条底部战法"
            )
        else:
            return (
                f"{cycle}环境适配: 共{total}条匹配，过滤{filtered}条({ratio:.0f}%)，"
                f"保留{kept}条"
            )


# ──────────────────────────────────────────────────────────
# 便捷函数
# ──────────────────────────────────────────────────────────

def get_tactics_for_cycle(emotion_cycle: str) -> Dict[str, Any]:
    """获取指定情绪周期的战法适配清单

    Args:
        emotion_cycle: 情绪周期名称

    Returns:
        包含适宜战法、禁忌战法、仓位建议的字典
    """
    filter_engine = EnvironmentFilter()
    return filter_engine.get_suitability(emotion_cycle)


def check_tactic_environment(emotion_cycle: str,
                              tactic_code: str) -> Dict[str, Any]:
    """检查战法与当前环境的适配性

    Args:
        emotion_cycle: 情绪周期
        tactic_code: 战法编码

    Returns:
        适配性判断
    """
    filter_engine = EnvironmentFilter()
    return filter_engine.is_tactic_suitable(emotion_cycle, tactic_code)


def apply_environment_filter(emotion_cycle: str,
                              matches: List[TacticMatchResult]
                              ) -> EnvironmentFilterResult:
    """应用环境过滤到战法匹配结果

    Args:
        emotion_cycle: 情绪周期
        matches: 战法匹配结果列表

    Returns:
        过滤结果
    """
    filter_engine = EnvironmentFilter()
    return filter_engine.filter_matches(emotion_cycle, matches)
