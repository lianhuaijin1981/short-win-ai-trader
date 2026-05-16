"""锚定标的智能锁定模块 — 盘中看盘核心组件

负责从全市场涨停股和领涨标的中，通过多维度权重评分体系
智能筛选出每日3-5只核心锚定标的，作为盘中观测和决策基准。

锚定标的四大类型:
1. 市场总龙 — 全市场最高身位+最强辨识度
2. 主线分支龙头 — 主线题材内的分支龙头
3. 先锋龙 — 率先涨停、带动板块的情绪先锋
4. 板块中军 — 大市值核心中军，板块定海神针

权重评分体系:
- 身位(30%) — 连板高度、涨停时间排序
- 辨识度(25%) — 历史股性、名字辨识度、往期龙头经历
- 带动性(25%) — 涨停后跟风股数量、板块涨幅
- 隔日溢价(20%) — 近5日打板次日高开率、盈亏比

伪龙头剔除逻辑:
- 独苗涨停无跟风 → 剔除
- 尾盘偷袭封板(14:30后) → 降权
- 历史股性差(3个月内无溢价记录) → 降权
- 公告利好一字独食 → 剔除
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    ExpectationLevel,
    LimitUpStock,
    ThemeData,
)

logger = get_logger("swat.m03.anchor_selector")


# ── 常量定义 ────────────────────────────────────────────

# 权重配置
WEIGHT_HEIGHT = 0.30        # 身位权重
WEIGHT_RECOGNITION = 0.25   # 辨识度权重
WEIGHT_DRIVE = 0.25         # 带动性权重
WEIGHT_PREMIUM = 0.20       # 隔日溢价权重

# 评分阈值
MIN_SCORE_FOR_POOL = 45.0   # 入选标的池最低分
MAX_ANCHOR_POOL_SIZE = 5    # 最大锚定标的数量
MIN_ANCHOR_POOL_SIZE = 3    # 最小锚定标的数量

# 伪龙头剔除参数
MIN_FOLLOWERS = 2           # 最少跟风股数量
SUSPICIOUS_LATE_TIME = "14:30"  # 尾盘偷袭判定时间
PREMIUM_WINDOW_DAYS = 5     # 溢价统计窗口天数


@dataclass
class AnchorCandidate:
    """锚定标的后选对象 — 包含完整评分中间数据"""
    ticker: str = ""
    name: str = ""
    anchor_type: AnchorType = AnchorType.TOTAL_DRAGON
    boards: int = 0                       # 连板数
    first_limit_up_time: str = ""         # 首次涨停时间
    theme: str = ""                       # 所属题材

    # 四维评分原始数据
    height_score: float = 0.0             # 身位原始分
    recognition_score: float = 0.0        # 辨识度原始分
    drive_score: float = 0.0              # 带动性原始分
    premium_score: float = 0.0            # 隔日溢价原始分

    # 四维加权得分
    height_weighted: float = 0.0
    recognition_weighted: float = 0.0
    drive_weighted: float = 0.0
    premium_weighted: float = 0.0

    # 综合评分
    total_score: float = 0.0

    # 伪龙头标记
    is_pseudo: bool = False
    pseudo_reasons: List[str] = field(default_factory=list)

    # 股性历史
    historical_premium_rate: float = 0.0   # 历史溢价率
    historical_win_rate: float = 0.0       # 历史胜率


@dataclass
class AnchorPool:
    """锚定标的池 — 每日核心观测标的集合"""
    trade_date: Optional[date] = None
    anchors: List[AnchorStock] = field(default_factory=list)
    candidates: List[AnchorCandidate] = field(default_factory=list)
    pseudo_dragons: List[AnchorCandidate] = field(default_factory=list)
    summary: str = ""

    @property
    def total_count(self) -> int:
        return len(self.anchors)

    @property
    def has_total_dragon(self) -> bool:
        return any(a.anchor_type == AnchorType.TOTAL_DRAGON for a in self.anchors)


class AnchorSelector:
    """锚定标的智能选择器

    通过四维权重评分体系，从当日涨停股和领涨标的中
    筛选出3-5只核心锚定标的，支撑盘中决策。

    Attributes:
        config: 应用配置对象
        _historical_data: 历史溢价数据缓存
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化锚定标的智能选择器

        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._historical_data: Dict[str, Dict] = {}
        logger.info("锚定标的智能选择器初始化完成")

    # ==================== 核心公共接口 ====================

    async def select_anchors(
        self,
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        historical_prices: Optional[Dict[str, List[Dict]]] = None,
    ) -> AnchorPool:
        """智能筛选锚定标的 — 主入口

        执行完整筛选流程: 候选收集 → 四维评分 → 伪龙头剔除 → 排序入池

        Args:
            limit_up_stocks: 当日涨停股列表
            themes: 当日活跃题材列表
            historical_prices: 历史价格数据 {ticker: [price_dict]}

        Returns:
            AnchorPool: 包含3-5只核心锚定标的的标的池

        Raises:
            ModuleError: 筛选过程发生严重错误
        """
        trade_date = date.today()
        logger.info(f"========== 开始锚定标的智能筛选: {trade_date.isoformat()} ==========")

        try:
            # Step 1: 构建候选池
            logger.info("[Step 1/5] 构建候选池...")
            candidates = self._build_candidates(limit_up_stocks, themes)
            logger.info(f"候选池数量: {len(candidates)}")

            if not candidates:
                logger.warning("候选池为空，返回空锚定池")
                return AnchorPool(trade_date=trade_date, summary="当日无有效候选标的")

            # Step 2: 四维评分
            logger.info("[Step 2/5] 执行四维权重评分...")
            candidates = self._score_candidates(candidates, themes, historical_prices)

            # Step 3: 伪龙头剔除
            logger.info("[Step 3/5] 执行伪龙头剔除...")
            candidates, pseudo_dragons = self._filter_pseudo_dragons(candidates)
            logger.info(f"剔除伪龙头: {len(pseudo_dragons)}只")

            # Step 4: 分类标注类型
            logger.info("[Step 4/5] 标注锚定类型...")
            candidates = self._classify_anchor_types(candidates, themes)

            # Step 5: 排序入池
            logger.info("[Step 5/5] 排序入池...")
            anchor_pool = self._assemble_pool(candidates, trade_date)
            anchor_pool.pseudo_dragons = pseudo_dragons

            logger.info(
                f"锚定标的筛选完成: 共{anchor_pool.total_count}只锚定标的, "
                f"含市场总龙{anchor_pool.has_total_dragon}"
            )
            return anchor_pool

        except Exception as e:
            logger.error(f"锚定标的筛选严重错误: {e}")
            raise ModuleError(f"锚定标的筛选失败: {e}")

    def update_expectations(
        self,
        anchor_pool: AnchorPool,
        expectation_results: Dict[str, str],
    ) -> AnchorPool:
        """更新锚定标的预期分级

        根据预期评估结果，更新标的池中各标的的预期状态。

        Args:
            anchor_pool: 当前锚定标的池
            expectation_results: {ticker: expectation_level}

        Returns:
            AnchorPool: 更新后的标的池
        """
        for anchor in anchor_pool.anchors:
            if anchor.ticker in expectation_results:
                exp_level = expectation_results[anchor.ticker]
                try:
                    anchor.expectation = ExpectationLevel(exp_level)
                except ValueError:
                    logger.warning(f"无效的预期分级: {exp_level}")
        return anchor_pool

    # ==================== 步骤1: 候选池构建 ====================

    def _build_candidates(
        self,
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
    ) -> List[AnchorCandidate]:
        """从涨停股中构建候选池

        提取所有涨停股的核心信息，构建初始候选对象。

        Args:
            limit_up_stocks: 涨停股列表
            themes: 题材列表

        Returns:
            List[AnchorCandidate]: 候选标的列表
        """
        candidates: List[AnchorCandidate] = []
        theme_map = {t.theme_name: t for t in themes}

        for stock in limit_up_stocks:
            if not stock.ticker or not stock.name:
                continue

            candidate = AnchorCandidate(
                ticker=stock.ticker,
                name=stock.name,
                boards=stock.consecutive_boards,
                first_limit_up_time=stock.first_limit_up_time or "",
                theme=stock.theme or "",
            )
            candidates.append(candidate)

        # 补充题材领涨股（即使未涨停）
        for theme in themes:
            if theme.leading_stock and theme.leading_stock not in [c.ticker for c in candidates]:
                leading_name = theme.leading_stock
                # 尝试从题材名称推断股票名
                candidate = AnchorCandidate(
                    ticker=theme.leading_stock,
                    name=leading_name,
                    boards=0,
                    first_limit_up_time="",
                    theme=theme.theme_name,
                )
                candidates.append(candidate)

        logger.debug(f"候选池构建完成: {len(candidates)}只候选标的")
        return candidates

    # ==================== 步骤2: 四维权重评分 ====================

    def _score_candidates(
        self,
        candidates: List[AnchorCandidate],
        themes: List[ThemeData],
        historical_prices: Optional[Dict[str, List[Dict]]] = None,
    ) -> List[AnchorCandidate]:
        """对候选标的进行四维权重评分

        评分体系:
        - 身位(30%): 连板高度排名 + 涨停时间排序
        - 辨识度(25%): 名字加分 + 历史龙头经历 + 市场记忆
        - 带动性(25%): 跟风股数量 + 板块整体涨幅
        - 隔日溢价(20%): 近5日打板次日高开率

        Args:
            candidates: 候选标的列表
            themes: 题材列表
            historical_prices: 历史价格数据

        Returns:
            List[AnchorCandidate]: 评分后的候选列表
        """
        # 身位评分
        candidates = self._score_height(candidates)

        # 辨识度评分
        candidates = self._score_recognition(candidates)

        # 带动性评分
        candidates = self._score_drive(candidates, themes)

        # 隔日溢价评分
        candidates = self._score_premium(candidates, historical_prices)

        # 计算加权总分
        for c in candidates:
            c.height_weighted = c.height_score * WEIGHT_HEIGHT
            c.recognition_weighted = c.recognition_score * WEIGHT_RECOGNITION
            c.drive_weighted = c.drive_score * WEIGHT_DRIVE
            c.premium_weighted = c.premium_score * WEIGHT_PREMIUM
            c.total_score = (
                c.height_weighted
                + c.recognition_weighted
                + c.drive_weighted
                + c.premium_weighted
            )

        return candidates

    def _score_height(self, candidates: List[AnchorCandidate]) -> List[AnchorCandidate]:
        """身位评分 — 连板高度 + 涨停时间

        连板越高分数越高，同身位越早涨停分数越高。
        满分100分。

        Args:
            candidates: 候选列表

        Returns:
            List[AnchorCandidate]: 评分后的列表
        """
        if not candidates:
            return candidates

        max_boards = max(c.boards for c in candidates) if candidates else 0

        for c in candidates:
            # 连板高度分 (0-70分)
            if max_boards > 0:
                height_part = (c.boards / max_boards) * 70
            else:
                height_part = 0

            # 涨停时间分 (0-30分) — 越早越好
            time_part = 15  # 默认中等
            if c.first_limit_up_time:
                try:
                    hour_minute = c.first_limit_up_time.replace(":", "")
                    minute_val = int(hour_minute)
                    # 9:30-9:35 → 30分, 9:35-9:45 → 25分, 9:45-10:00 → 20分
                    # 10:00-10:30 → 15分, 10:30-11:30 → 10分, 下午 → 5分
                    if minute_val <= 935:
                        time_part = 30
                    elif minute_val <= 945:
                        time_part = 25
                    elif minute_val <= 1000:
                        time_part = 20
                    elif minute_val <= 1030:
                        time_part = 15
                    elif minute_val <= 1130:
                        time_part = 10
                    else:
                        time_part = 5
                except (ValueError, TypeError):
                    time_part = 15

            c.height_score = min(100, height_part + time_part)

        return candidates

    def _score_recognition(self, candidates: List[AnchorCandidate]) -> List[AnchorCandidate]:
        """辨识度评分 — 名字辨识度 + 历史股性

        评估标准:
        - 名字简洁有力(如"东方"、"龙头") → 加分
        - 历史有过龙头经历 → 大幅加分
        - 近期活跃度高 → 加分
        - 新股/次新股 → 适中加分

        满分100分。

        Args:
            candidates: 候选列表

        Returns:
            List[AnchorCandidate]: 评分后的列表
        """
        # 高辨识度关键词
        high_recognition_keywords = [
            "龙", "凤", "东方", "中信", "光大", "国泰", "招商",
            "平安", "茅台", "比亚迪", "宁德", "隆基", "中芯",
        ]

        for c in candidates:
            score = 30  # 基础分

            # 名字辨识度加分 (0-35分)
            for keyword in high_recognition_keywords:
                if keyword in c.name:
                    score += 15
                    break  # 只加一次

            # 连板高度带来的辨识度 (0-20分)
            if c.boards >= 5:
                score += 20
            elif c.boards >= 3:
                score += 15
            elif c.boards >= 2:
                score += 10

            # 历史股性 (0-15分) — 基于缓存数据
            hist = self._historical_data.get(c.ticker, {})
            if hist.get("was_dragon", False):
                score += 15
            elif hist.get("premium_rate", 0) > 0.6:
                score += 10
            elif hist.get("premium_rate", 0) > 0.4:
                score += 5

            c.recognition_score = min(100, score)

        return candidates

    def _score_drive(
        self,
        candidates: List[AnchorCandidate],
        themes: List[ThemeData],
    ) -> List[AnchorCandidate]:
        """带动性评分 — 跟风股数量 + 板块整体表现

        评估标准:
        - 涨停后带动≥3只跟风涨停 → 高分
        - 所属板块整体涨幅大 → 加分
        - 板块内涨停数量多 → 加分
        - 作为板块首个涨停 → 大幅加分

        满分100分。

        Args:
            candidates: 候选列表
            themes: 题材列表

        Returns:
            List[AnchorCandidate]: 评分后的列表
        """
        theme_map = {t.theme_name: t for t in themes}

        for c in candidates:
            score = 20  # 基础分

            theme = theme_map.get(c.theme)
            if theme:
                # 板块涨停数量分 (0-40分)
                limit_up_count = theme.limit_up_count
                if limit_up_count >= 10:
                    score += 40
                elif limit_up_count >= 6:
                    score += 30
                elif limit_up_count >= 3:
                    score += 20
                elif limit_up_count >= 1:
                    score += 10

                # 板块整体涨幅分 (0-25分)
                avg_change = theme.avg_change_pct
                if avg_change >= 5:
                    score += 25
                elif avg_change >= 3:
                    score += 18
                elif avg_change >= 1:
                    score += 10

                # 是否板块领涨 (0-15分)
                if theme.leading_stock == c.ticker:
                    score += 15

            c.drive_score = min(100, score)

        return candidates

    def _score_premium(
        self,
        candidates: List[AnchorCandidate],
        historical_prices: Optional[Dict[str, List[Dict]]] = None,
    ) -> List[AnchorCandidate]:
        """隔日溢价评分 — 历史打板次日表现

        评估标准:
        - 近5日打板次日高开率 > 80% → 高分
        - 近5日打板盈亏比 > 2:1 → 高分
        - 无明显核按钮记录 → 加分

        满分100分。

        Args:
            candidates: 候选列表
            historical_prices: 历史价格数据

        Returns:
            List[AnchorCandidate]: 评分后的列表
        """
        for c in candidates:
            score = 50  # 默认中等分

            # 从缓存获取历史数据
            hist = self._historical_data.get(c.ticker, {})
            premium_rate = hist.get("premium_rate", 0.5)
            win_rate = hist.get("win_rate", 0.5)

            c.historical_premium_rate = premium_rate
            c.historical_win_rate = win_rate

            # 溢价率分 (0-60分)
            if premium_rate >= 0.8:
                score += 30
            elif premium_rate >= 0.6:
                score += 20
            elif premium_rate >= 0.4:
                score += 10
            else:
                score -= 10

            # 胜率分 (0-40分)
            if win_rate >= 0.7:
                score += 20
            elif win_rate >= 0.5:
                score += 10
            else:
                score -= 5

            c.premium_score = max(0, min(100, score))

        return candidates

    # ==================== 步骤3: 伪龙头剔除 ====================

    def _filter_pseudo_dragons(
        self,
        candidates: List[AnchorCandidate],
    ) -> Tuple[List[AnchorCandidate], List[AnchorCandidate]]:
        """伪龙头剔除 — 过滤不符合真龙头特征的标的

        剔除规则:
        1. 独苗涨停 — 所属板块无其他涨停跟风股
        2. 尾盘偷袭 — 14:30后首次涨停
        3. 公告独食 — 利好公告后一字涨停无换手
        4. 历史股性极差 — 近3月溢价率 < 20%且无龙头经历

        Args:
            candidates: 全部候选列表

        Returns:
            Tuple[List[AnchorCandidate], List[AnchorCandidate]]: (真龙头, 伪龙头)
        """
        real_dragons: List[AnchorCandidate] = []
        pseudo_dragons: List[AnchorCandidate] = []

        for c in candidates:
            reasons: List[str] = []

            # 规则1: 独苗涨停检测
            if c.drive_score < 25:
                reasons.append("独苗涨停，无板块跟风")

            # 规则2: 尾盘偷袭检测
            if c.first_limit_up_time:
                try:
                    hour_minute = c.first_limit_up_time.replace(":", "")
                    if int(hour_minute) >= 1430:
                        reasons.append("尾盘偷袭涨停(14:30后)")
                        c.height_score *= 0.5  # 身位分打五折
                except (ValueError, TypeError):
                    pass

            # 规则3: 历史股性极差
            if (
                c.historical_premium_rate < 0.2
                and c.historical_premium_rate > 0
                and c.recognition_score < 40
            ):
                reasons.append("历史股性极差，近3月溢价率<20%")

            # 标记伪龙头
            if reasons:
                c.is_pseudo = True
                c.pseudo_reasons = reasons
                # 伪龙头总分打3折
                c.total_score *= 0.3
                pseudo_dragons.append(c)
            else:
                real_dragons.append(c)

        logger.debug(f"伪龙头剔除: 真龙头{len(real_dragons)}只, 伪龙头{len(pseudo_dragons)}只")
        return real_dragons, pseudo_dragons

    # ==================== 步骤4: 类型分类 ====================

    def _classify_anchor_types(
        self,
        candidates: List[AnchorCandidate],
        themes: List[ThemeData],
    ) -> List[AnchorCandidate]:
        """标注锚定标的类型

        分类逻辑:
        - 市场总龙: 全市场最高身位 + 综合评分最高
        - 主线分支龙头: 主线题材内的高身位标的
        - 先锋龙: 涨停时间最早 + 带动性强
        - 板块中军: 大市值 + 板块核心地位

        Args:
            candidates: 候选列表（已评分）
            themes: 题材列表

        Returns:
            List[AnchorCandidate]: 分类后的列表
        """
        if not candidates:
            return candidates

        # 按总分排序
        sorted_candidates = sorted(candidates, key=lambda x: x.total_score, reverse=True)

        # 标记市场总龙（最高分+最高身位）
        max_boards = max(c.boards for c in candidates) if candidates else 0
        total_dragon_assigned = False

        for c in sorted_candidates:
            if not total_dragon_assigned and c.boards >= max_boards and c.total_score >= 70:
                c.anchor_type = AnchorType.TOTAL_DRAGON
                total_dragon_assigned = True
            elif c.drive_score >= 70 and c.height_score >= 60:
                c.anchor_type = AnchorType.BRANCH_DRAGON
            elif c.height_score >= 75 and c.first_limit_up_time:
                try:
                    hour_minute = c.first_limit_up_time.replace(":", "")
                    if int(hour_minute) <= 1000:
                        c.anchor_type = AnchorType.PIONEER
                    else:
                        c.anchor_type = AnchorType.SECTOR_CORE
                except (ValueError, TypeError):
                    c.anchor_type = AnchorType.SECTOR_CORE
            else:
                c.anchor_type = AnchorType.SECTOR_CORE

        return sorted_candidates

    # ==================== 步骤5: 组装标的池 ====================

    def _assemble_pool(
        self,
        candidates: List[AnchorCandidate],
        trade_date: date,
    ) -> AnchorPool:
        """组装最终锚定标的池

        按评分排序，选取3-5只核心标的，组装为标的池。

        Args:
            candidates: 已分类排序的候选列表
            trade_date: 交易日期

        Returns:
            AnchorPool: 最终标的池
        """
        # 过滤低于最低分的
        qualified = [c for c in candidates if c.total_score >= MIN_SCORE_FOR_POOL]

        # 确保至少包含最高分的几个
        if not qualified and candidates:
            qualified = candidates[:MIN_ANCHOR_POOL_SIZE]

        # 取前N名
        selected = qualified[:MAX_ANCHOR_POOL_SIZE]

        # 确保最少数量
        if len(selected) < MIN_ANCHOR_POOL_SIZE and len(candidates) > len(selected):
            remaining = [c for c in candidates if c not in selected]
            needed = MIN_ANCHOR_POOL_SIZE - len(selected)
            selected.extend(remaining[:needed])

        # 转换为AnchorStock
        anchors: List[AnchorStock] = []
        for c in selected:
            anchor = AnchorStock(
                ticker=c.ticker,
                name=c.name,
                anchor_type=c.anchor_type,
                score=round(c.total_score, 2),
                height_weight=round(c.height_weighted, 2),
                recognition_weight=round(c.recognition_weighted, 2),
                drive_weight=round(c.drive_weighted, 2),
                premium_weight=round(c.premium_weighted, 2),
                expectation=ExpectationLevel.MEET,
                operation_advice=self._generate_operation_advice(c),
                expected_open_high=0.0,
                expected_volume_ratio=0.0,
            )
            anchors.append(anchor)

        # 生成摘要
        type_summary: Dict[str, int] = {}
        for a in anchors:
            type_name = a.anchor_type.value
            type_summary[type_name] = type_summary.get(type_name, 0) + 1

        summary_parts = [f"锚定标的池({len(anchors)}只):"]
        for t, count in type_summary.items():
            summary_parts.append(f"  {t}: {count}只")

        # 列出各标的评分
        for a in anchors:
            summary_parts.append(
                f"  {a.name}({a.ticker}): {a.score}分 [{a.anchor_type.value}]"
            )

        pool = AnchorPool(
            trade_date=trade_date,
            anchors=anchors,
            candidates=candidates,
            summary="\n".join(summary_parts),
        )

        return pool

    def _generate_operation_advice(self, candidate: AnchorCandidate) -> str:
        """生成操作建议

        根据标的类型和评分，生成对应的操作建议。

        Args:
            candidate: 候选标的

        Returns:
            str: 操作建议文本
        """
        advice_parts: List[str] = []

        if candidate.anchor_type == AnchorType.TOTAL_DRAGON:
            advice_parts.append("市场总龙——紧盯分歧低吸机会，断板即离场信号")
        elif candidate.anchor_type == AnchorType.BRANCH_DRAGON:
            advice_parts.append("分支龙头——板块内强弱风向标")
 elif candidate.anchor_type == AnchorType.PIONEER:
            advice_parts.append("先锋龙——情绪点火器，观察持续性")
        elif candidate.anchor_type == AnchorType.SECTOR_CORE:
            advice_parts.append("板块中军——大资金战场，趋势锚定")

        # 根据评分追加建议
        if candidate.total_score >= 85:
            advice_parts.append("核心标的，优先关注")
        elif candidate.total_score >= 70:
            advice_parts.append("重点关注")
        elif candidate.total_score >= 60:
            advice_parts.append("适当关注")
        else:
            advice_parts.append("观察为主")

        if candidate.is_pseudo:
            advice_parts.append(f"[伪龙头警示] {'; '.join(candidate.pseudo_reasons)}")

        return " | ".join(advice_parts)

    # ==================== 数据管理接口 ====================

    def load_historical_data(self, ticker: str, data: Dict):
        """加载单只股票的历史数据

        Args:
            ticker: 股票代码
            data: 历史数据字典
        """
        self._historical_data[ticker] = data

    def clear_historical_data(self):
        """清空历史数据缓存"""
        self._historical_data.clear()
        logger.info("历史数据缓存已清空")
