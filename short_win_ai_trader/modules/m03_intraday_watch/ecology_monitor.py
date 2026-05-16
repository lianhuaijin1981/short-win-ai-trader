"""龙头生态梯队监测模块 — 盘中看盘核心组件

监测龙头生态完整梯队结构:
先锋(点火) → 中军(主心骨) → 跟风(补涨)

梯队健康度评估:
- 完整梯队: 先锋+中军+跟风均健康 → 板块行情可持续
- 梯队断层: 先锋强但无跟风 / 中军掉队 → 注意风险
- 梯队崩塌: 先锋核按钮+跟风全面回落 → 撤退信号

断层检测:
- 先锋-中军断层: 先锋涨停但中军绿盘
- 中军-跟风断层: 中军强势但跟风寥寥
- 全面断层: 仅有一只独苗涨停
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    DragonEcology,
    ExpectationLevel,
    LimitUpStock,
    ThemeData,
)

logger = get_logger("swat.m03.ecology_monitor")


# ── 常量定义 ────────────────────────────────────────────

# 梯队健康度阈值
ECOLOGY_HEALTH_PERFECT = 85.0       # 完美梯队
ECOLOGY_HEALTH_GOOD = 70.0          # 健康梯队
ECOLOGY_HEALTH_WARNING = 50.0       # 预警梯队
ECOLOGY_HEALTH_DANGER = 30.0        # 危险梯队

# 断层判定参数
GAP_PIONEER_CORE_MAX = 5.0          # 先锋-中军最大合理价差(%)
GAP_CORE_FOLLOWER_MIN = 2           # 中军-跟风最小跟风数量
GAP_FOLLOWER_LIMIT_MIN = 1          # 跟风最少涨停数

# 梯队完整性权重
WEIGHT_PIONEER_HEALTH = 0.35        # 先锋健康权重
WEIGHT_CORE_HEALTH = 0.35           # 中军健康权重
WEIGHT_FOLLOWER_HEALTH = 0.30       # 跟风健康权重


@dataclass
class TierHealth:
    """梯队健康状态"""
    tier_type: str = ""                 # pioneer/core/follower
    status: str = "normal"              # normal/warning/critical
    score: float = 0.0                  # 0-100
    concerns: List[str] = field(default_factory=list)


@dataclass
class TierGap:
    """梯队断层信息"""
    gap_type: str = ""                  # pioneer_core/core_follower/comprehensive
    severity: str = "minor"             # minor/moderate/severe
    description: str = ""
    recommendation: str = ""


@dataclass
class EcologyReport:
    """生态梯队完整报告"""
    trade_date: Optional[date] = None
    dragon_ecology: Optional[DragonEcology] = None
    tier_healths: List[TierHealth] = field(default_factory=list)
    gaps: List[TierGap] = field(default_factory=list)
    overall_health: float = 0.0
    overall_status: str = ""            # 完美/健康/预警/危险
    summary: str = ""


class EcologyMonitor:
    """龙头生态梯队监测器

    实时监测龙头生态的完整性和健康度，检测梯队断层，
    评估板块行情的可持续性。

    Attributes:
        config: 应用配置
        _ecology_cache: 生态数据缓存
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化龙头生态梯队监测器

        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._ecology_cache: Dict[str, DragonEcology] = {}
        logger.info("龙头生态梯队监测器初始化完成")

    # ==================== 核心公共接口 ====================

    async def monitor_ecology(
        self,
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        real_time_data: Optional[Dict[str, Dict]] = None,
    ) -> EcologyReport:
        """监测龙头生态梯队 — 主入口

        执行完整监测流程: 梯队构建 → 健康评估 → 断层检测 → 报告生成

        Args:
            anchors: 锚定标的列表
            limit_up_stocks: 涨停股列表
            themes: 题材列表
            real_time_data: 实时数据 {ticker: {change_pct, volume, ...}}

        Returns:
            EcologyReport: 生态梯队完整报告

        Raises:
            ModuleError: 监测过程发生严重错误
        """
        logger.info("========== 开始龙头生态梯队监测 ==========")

        try:
            # Step 1: 构建生态梯队
            logger.info("[Step 1/3] 构建龙头生态梯队...")
            ecology = self._build_ecology(anchors, limit_up_stocks, themes)

            # Step 2: 健康度评估
            logger.info("[Step 2/3] 评估梯队健康度...")
            tier_healths = self._assess_tier_health(ecology, real_time_data)

            # Step 3: 断层检测
            logger.info("[Step 3/3] 检测梯队断层...")
            gaps = self._detect_tier_gaps(ecology, tier_healths)

            # 综合评估
            overall_health = self._calculate_overall_health(tier_healths, gaps)
            overall_status = self._classify_overall_status(overall_health)

            # 生成摘要
            summary = self._generate_summary(ecology, overall_health, overall_status, gaps)

            report = EcologyReport(
                trade_date=date.today(),
                dragon_ecology=ecology,
                tier_healths=tier_healths,
                gaps=gaps,
                overall_health=overall_health,
                overall_status=overall_status,
                summary=summary,
            )

            # 缓存
            for anchor in anchors:
                self._ecology_cache[anchor.ticker] = ecology

            logger.info(
                f"生态监测完成: 整体健康度{overall_health:.1f}({overall_status}), "
                f"断层{len(gaps)}处"
            )
            return report

        except Exception as e:
            logger.error(f"龙头生态监测严重错误: {e}")
            raise ModuleError(f"生态监测失败: {e}")

    def get_ecology(self, ticker: str) -> Optional[DragonEcology]:
        """获取指定标的的生态数据

        Args:
            ticker: 股票代码

        Returns:
            Optional[DragonEcology]: 生态数据
        """
        return self._ecology_cache.get(ticker)

    # ==================== 步骤1: 梯队构建 ====================

    def _build_ecology(
        self,
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
    ) -> DragonEcology:
        """构建龙头生态梯队

        从锚定标的和涨停股中识别:
        - 先锋龙: 率先涨停、情绪先锋
        - 板块中军: 市值大、地位核心
        - 跟风股: 补涨跟风

        Args:
            anchors: 锚定标的
            limit_up_stocks: 涨停股
            themes: 题材

        Returns:
            DragonEcology: 龙头生态
        """
        # 识别先锋龙
        pioneer = self._identify_pioneer(anchors)

        # 识别中军
        core = self._identify_core(anchors)

        # 识别市场总龙
        dragon = self._identify_total_dragon(anchors)

        # 识别跟风股
        followers = self._identify_followers(pioneer, core, limit_up_stocks, themes)

        # 计算初始健康度
        health = self._initial_health_estimate(pioneer, core, followers)

        ecology = DragonEcology(
            dragon=dragon,
            pioneer=pioneer,
            core=core,
            followers=followers,
            ecology_health=health,
            risk_warning=None,
        )

        return ecology

    def _identify_pioneer(self, anchors: List[AnchorStock]) -> Optional[AnchorStock]:
        """识别先锋龙

        先锋龙特征: 涨停时间最早 + 先锋类型

        Args:
            anchors: 锚定标的

        Returns:
            Optional[AnchorStock]: 先锋龙
        """
        for anchor in anchors:
            if anchor.anchor_type == AnchorType.PIONEER:
                return anchor

        # 如果没有明确标注，选评分最高且身位较低的
        candidates = sorted(anchors, key=lambda a: a.score, reverse=True)
        for c in candidates:
            if c.score >= 60:
                return c

        return candidates[0] if candidates else None

    def _identify_core(self, anchors: List[AnchorStock]) -> Optional[AnchorStock]:
        """识别板块中军

        中军特征: SECTOR_CORE类型 或 评分最高

        Args:
            anchors: 锚定标的

        Returns:
            Optional[AnchorStock]: 中军
        """
        for anchor in anchors:
            if anchor.anchor_type == AnchorType.SECTOR_CORE:
                return anchor

        # 选评分最高的作为中军
        candidates = sorted(anchors, key=lambda a: a.score, reverse=True)
        return candidates[0] if candidates else None

    def _identify_total_dragon(
        self,
        anchors: List[AnchorStock],
    ) -> Optional[AnchorStock]:
        """识别市场总龙

        Args:
            anchors: 锚定标的

        Returns:
            Optional[AnchorStock]: 市场总龙
        """
        for anchor in anchors:
            if anchor.anchor_type == AnchorType.TOTAL_DRAGON:
                return anchor
        return None

    def _identify_followers(
        self,
        pioneer: Optional[AnchorStock],
        core: Optional[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
    ) -> List[str]:
        """识别跟风股

        跟风股: 同题材涨停但非先锋/中军

        Args:
            pioneer: 先锋龙
            core: 中军
            limit_up_stocks: 涨停股
            themes: 题材

        Returns:
            List[str]: 跟风股代码列表
        """
        followers: List[str] = []
        pioneer_theme = pioneer.theme if pioneer else ""
        core_theme = core.theme if core else ""

        # 收集先锋和中军所属题材的所有涨停股
        target_themes = set()
        if pioneer_theme:
            target_themes.add(pioneer_theme)
        if core_theme:
            target_themes.add(core_theme)

        for stock in limit_up_stocks:
            if stock.theme in target_themes:
                # 排除先锋和中军本身
                if pioneer and stock.ticker == pioneer.ticker:
                    continue
                if core and stock.ticker == core.ticker:
                    continue
                followers.append(stock.ticker)

        return followers

    # ==================== 步骤2: 健康度评估 ====================

    def _assess_tier_health(
        self,
        ecology: DragonEcology,
        real_time_data: Optional[Dict[str, Dict]] = None,
    ) -> List[TierHealth]:
        """评估各梯队健康度

        Args:
            ecology: 龙头生态
            real_time_data: 实时数据

        Returns:
            List[TierHealth]: 各梯队健康状态
        """
        healths: List[TierHealth] = []

        # 先锋龙健康度
        pioneer_health = self._assess_pioneer_health(ecology.pioneer, real_time_data)
        healths.append(pioneer_health)

        # 中军健康度
        core_health = self._assess_core_health(ecology.core, real_time_data)
        healths.append(core_health)

        # 跟风梯队健康度
        follower_health = self._assess_follower_health(ecology.followers, real_time_data)
        healths.append(follower_health)

        return healths

    def _assess_pioneer_health(
        self,
        pioneer: Optional[AnchorStock],
        real_time_data: Optional[Dict[str, Dict]] = None,
    ) -> TierHealth:
        """评估先锋龙健康度

        Args:
            pioneer: 先锋龙
            real_time_data: 实时数据

        Returns:
            TierHealth: 先锋梯队健康状态
        """
        if not pioneer:
            return TierHealth(
                tier_type="pioneer",
                status="critical",
                score=0,
                concerns=["无先锋龙，生态缺失"],
            )

        score = 70.0
        concerns: List[str] = []

        # 预期状态
        if pioneer.expectation == ExpectationLevel.BELOW:
            score -= 30
            concerns.append("先锋低于预期")
        elif pioneer.expectation == ExpectationLevel.ABOVE:
            score += 15

        # 实时数据
        if real_time_data and pioneer.ticker in real_time_data:
            rt = real_time_data[pioneer.ticker]
            change_pct = rt.get("change_pct", 0)
            if change_pct < 0:
                score -= 25
                concerns.append(f"先锋下跌({change_pct:.1f}%)")
            elif change_pct >= 5:
                score += 10

            if rt.get("board_status") == "炸板":
                score -= 20
                concerns.append("先锋炸板")

        # 身位评估
        if pioneer.score < 50:
            score -= 15
            concerns.append("先锋评分偏低")

        score = max(0, min(100, score))

        if score >= 70:
            status = "normal"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        return TierHealth(
            tier_type="pioneer",
            status=status,
            score=score,
            concerns=concerns,
        )

    def _assess_core_health(
        self,
        core: Optional[AnchorStock],
        real_time_data: Optional[Dict[str, Dict]] = None,
    ) -> TierHealth:
        """评估中军健康度

        Args:
            core: 中军标的
            real_time_data: 实时数据

        Returns:
            TierHealth: 中军梯队健康状态
        """
        if not core:
            return TierHealth(
                tier_type="core",
                status="critical",
                score=0,
                concerns=["无板块中军，生态不稳"],
            )

        score = 70.0
        concerns: List[str] = []

        # 预期状态
        if core.expectation == ExpectationLevel.BELOW:
            score -= 25
            concerns.append("中军低于预期")
        elif core.expectation == ExpectationLevel.ABOVE:
            score += 10

        # 实时数据
        if real_time_data and core.ticker in real_time_data:
            rt = real_time_data[core.ticker]
            change_pct = rt.get("change_pct", 0)
            if change_pct < -2:
                score -= 20
                concerns.append(f"中军走弱({change_pct:.1f}%)")
            elif change_pct >= 3:
                score += 10

        # 中军评分
        if core.score < 50:
            score -= 10
            concerns.append("中军评分偏低")

        score = max(0, min(100, score))

        if score >= 70:
            status = "normal"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        return TierHealth(
            tier_type="core",
            status=status,
            score=score,
            concerns=concerns,
        )

    def _assess_follower_health(
        self,
        followers: List[str],
        real_time_data: Optional[Dict[str, Dict]] = None,
    ) -> TierHealth:
        """评估跟风梯队健康度

        Args:
            followers: 跟风股列表
            real_time_data: 实时数据

        Returns:
            TierHealth: 跟风梯队健康状态
        """
        follower_count = len(followers)
        score = 50.0
        concerns: List[str] = []

        # 数量评估
        if follower_count >= 5:
            score += 25
        elif follower_count >= 3:
            score += 15
        elif follower_count >= 1:
            score += 5
        else:
            score -= 20
            concerns.append("无跟风股，独苗行情")

        # 实时数据检查
        if real_time_data and followers:
            up_count = 0
            down_count = 0
            for ticker in followers:
                if ticker in real_time_data:
                    change = real_time_data[ticker].get("change_pct", 0)
                    if change > 0:
                        up_count += 1
                    elif change < 0:
                        down_count += 1

            if down_count > up_count:
                score -= 15
                concerns.append(f"跟风股跌多涨少({down_count}/{follower_count})")
            elif up_count > 0 and follower_count > 0:
                ratio = up_count / follower_count
                if ratio >= 0.8:
                    score += 10

        score = max(0, min(100, score))

        if score >= 70:
            status = "normal"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        return TierHealth(
            tier_type="follower",
            status=status,
            score=score,
            concerns=concerns,
        )

    # ==================== 步骤3: 断层检测 ====================

    def _detect_tier_gaps(
        self,
        ecology: DragonEcology,
        tier_healths: List[TierHealth],
    ) -> List[TierGap]:
        """检测梯队断层

        Args:
            ecology: 龙头生态
            tier_healths: 各梯队健康状态

        Returns:
            List[TierGap]: 断层列表
        """
        gaps: List[TierGap] = []

        # 构建健康度映射
        health_map = {h.tier_type: h for h in tier_healths}

        pioneer_health = health_map.get("pioneer")
        core_health = health_map.get("core")
        follower_health = health_map.get("follower")

        # 先锋-中军断层
        if pioneer_health and core_health:
            if pioneer_health.status == "normal" and core_health.status in ("warning", "critical"):
                gaps.append(TierGap(
                    gap_type="pioneer_core",
                    severity="moderate",
                    description="先锋强势但中军走弱，梯队不稳",
                    recommendation="谨慎参与，观察中军能否修复",
                ))
            elif pioneer_health.status == "critical" and core_health.status == "normal":
                gaps.append(TierGap(
                    gap_type="pioneer_core",
                    severity="minor",
                    description="先锋走弱但中军稳健，可能切换龙头",
                    recommendation="关注中军能否接力",
                ))

        # 中军-跟风断层
        if core_health and follower_health:
            if core_health.status == "normal" and follower_health.status in ("warning", "critical"):
                gaps.append(TierGap(
                    gap_type="core_follower",
                    severity="moderate",
                    description="中军强势但跟风不足，行情难以持续",
                    recommendation="注意冲高回落风险",
                ))

        # 全面断层
        critical_count = sum(1 for h in tier_healths if h.status == "critical")
        if critical_count >= 2:
            gaps.append(TierGap(
                gap_type="comprehensive",
                severity="severe",
                description="多梯队同时走弱，生态可能崩塌",
                recommendation="减仓撤退为主",
            ))

        # 独苗行情
        if ecology.pioneer and not ecology.followers:
            gaps.append(TierGap(
                gap_type="core_follower",
                severity="severe",
                description="仅先锋独苗涨停，无跟风梯队",
                recommendation="独苗行情不参与或轻仓套利",
            ))

        return gaps

    # ==================== 综合评估 ====================

    def _calculate_overall_health(
        self,
        tier_healths: List[TierHealth],
        gaps: List[TierGap],
    ) -> float:
        """计算整体健康度

        Args:
            tier_healths: 各梯队健康度
            gaps: 断层列表

        Returns:
            float: 整体健康度 0-100
        """
        if not tier_healths:
            return 0.0

        # 加权平均
        weights = {
            "pioneer": WEIGHT_PIONEER_HEALTH,
            "core": WEIGHT_CORE_HEALTH,
            "follower": WEIGHT_FOLLOWER_HEALTH,
        }

        weighted_sum = sum(
            h.score * weights.get(h.tier_type, 0.33)
            for h in tier_healths
        )

        # 断层扣分
        gap_penalty = 0
        for gap in gaps:
            if gap.severity == "minor":
                gap_penalty += 5
            elif gap.severity == "moderate":
                gap_penalty += 10
            elif gap.severity == "severe":
                gap_penalty += 20

        return max(0, min(100, weighted_sum - gap_penalty))

    def _classify_overall_status(self, health: float) -> str:
        """整体健康状态分级

        Args:
            health: 健康度分数

        Returns:
            str: 状态描述
        """
        if health >= ECOLOGY_HEALTH_PERFECT:
            return "完美"
        elif health >= ECOLOGY_HEALTH_GOOD:
            return "健康"
        elif health >= ECOLOGY_HEALTH_WARNING:
            return "预警"
        elif health >= ECOLOGY_HEALTH_DANGER:
            return "危险"
        return "崩塌"

    def _initial_health_estimate(
        self,
        pioneer: Optional[AnchorStock],
        core: Optional[AnchorStock],
        followers: List[str],
    ) -> float:
        """估算初始健康度

        Args:
            pioneer: 先锋龙
            core: 中军
            followers: 跟风股

        Returns:
            float: 初始健康度
        """
        score = 50.0
        if pioneer:
            score += 20
        if core:
            score += 20
        if len(followers) >= 3:
            score += 20
        elif len(followers) >= 1:
            score += 10
        return min(100, score)

    def _generate_summary(
        self,
        ecology: DragonEcology,
        health: float,
        status: str,
        gaps: List[TierGap],
    ) -> str:
        """生成生态监测摘要

        Args:
            ecology: 龙头生态
            health: 健康度
            status: 状态
            gaps: 断层列表

        Returns:
            str: 摘要文本
        """
        parts: List[str] = []
        parts.append(f"龙头生态: 整体健康度{health:.1f}({status})")

        if ecology.pioneer:
            parts.append(f"先锋: {ecology.pioneer.name}({ecology.pioneer.score}分)")
        if ecology.core:
            parts.append(f"中军: {ecology.core.name}({ecology.core.score}分)")
        if ecology.followers:
            parts.append(f"跟风: {len(ecology.followers)}只")
        else:
            parts.append("跟风: 无(独苗行情)")

        if gaps:
            parts.append(f"断层: {len(gaps)}处")
            for gap in gaps:
                parts.append(f"  - {gap.description}")

        return " | ".join(parts)

    # ==================== 便捷接口 ====================

    def quick_check(
        self,
        pioneer_status: str,
        core_status: str,
        follower_count: int,
    ) -> Tuple[float, str]:
        """快速检查生态健康度

        Args:
            pioneer_status: 先锋状态 (strong/weak/none)
            core_status: 中军状态 (strong/weak/none)
            follower_count: 跟风数量

        Returns:
            Tuple[float, str]: (健康度, 状态描述)
        """
        score = 50.0
        if pioneer_status == "strong":
            score += 20
        elif pioneer_status == "none":
            score -= 20

        if core_status == "strong":
            score += 20
        elif core_status == "none":
            score -= 20

        if follower_count >= 5:
            score += 20
        elif follower_count >= 3:
            score += 15
        elif follower_count >= 1:
            score += 5
        else:
            score -= 15

        health = max(0, min(100, score))
        status = self._classify_overall_status(health)
        return health, status

    def clear_cache(self):
        """清空缓存"""
        self._ecology_cache.clear()
        logger.info("生态监测缓存已清空")
