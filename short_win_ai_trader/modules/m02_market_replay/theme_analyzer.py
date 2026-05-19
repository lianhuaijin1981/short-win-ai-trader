"""题材周期分析器 — 题材炒作全周期演化研判

将题材生命周期标准化划分为六段:
题材萌芽 → 资金发酵 → 主升加速 → 高位分歧 → 补涨收尾 → 题材退潮

核心功能:
- 自动判定热门题材所处生命周期位置
- 题材持续性预判（长期主线/短期套利/一日游）
- 操作节点精准标注（入场/加仓/止盈/清仓）
- 轮动预判: 提前捕捉资金即将切换的新热点题材
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    DragonBond,
    LimitUpStock,
    ThemeCorrelation,
    ThemeCycle,
    ThemeCycleAnalysis,
    ThemeData,
    ThemeRotationSpeed,
)

logger = get_logger("swat.m02.theme_analyzer")


# ==================== 题材周期判定参数 ====================

THEME_STAGE_THRESHOLDS = {
    # 题材萌芽: 首板出现，资金试探
    ThemeCycle.SPROUT: {
        "min_limit_up": 1,
        "max_limit_up": 3,
        "min_avg_change": 2.0,
        "max_consecutive_boards": 1,
        "max_inflow": 5e8,
    },
    # 资金发酵: 涨停增多，资金持续流入
    ThemeCycle.FERMENT: {
        "min_limit_up": 3,
        "max_limit_up": 10,
        "min_avg_change": 3.0,
        "min_consecutive_boards": 2,
        "min_inflow": 3e8,
    },
    # 主升加速: 龙头连板，板块效应最强
    ThemeCycle.ACCELERATE: {
        "min_limit_up": 8,
        "min_avg_change": 4.0,
        "min_consecutive_boards": 3,
        "min_inflow": 8e8,
    },
    # 高位分歧: 龙头开板，分化加剧
    ThemeCycle.DIVERGE: {
        "max_explode_rate": 40.0,  # 炸板率上升
        "limit_up_range": (5, 15),  # 涨停数减少
        "min_avg_change": 2.0,
    },
    # 补涨收尾: 补涨股活跃，龙头滞涨
    ThemeCycle.COMPLEMENT: {
        "max_limit_up": 8,
        "leader_stagnant": True,  # 龙头滞涨
        "complement_active": True,  # 补涨活跃
    },
    # 题材退潮: 全面退潮，亏钱效应
    ThemeCycle.RETREAT: {
        "max_limit_up": 3,
        "max_avg_change": 1.0,
        "negative_flow": True,  # 资金流出
    },
}


# ==================== 题材类型判定标准 ====================

THEME_TYPE_CRITERIA = {
    "长期主线": {
        "min_duration_days": 5,      # 持续至少5个交易日
        "min_limit_up_total": 20,    # 累计涨停数
        "has_leader": True,          # 有明确龙头
        "policy_support": True,      # 有政策支撑
    },
    "短期套利": {
        "min_duration_days": 2,
        "max_duration_days": 4,
        "min_limit_up_total": 8,
        "event_driven": True,        # 事件驱动
    },
    "一日游": {
        "max_duration_days": 1,
        "max_limit_up_total": 5,
        "no_leader": True,           # 无持续龙头
    },
}


class ThemeAnalyzer:
    """题材周期分析器

    基于量化指标自动研判各热门题材所处的生命周期阶段，
    并输出操作节点和轮动预判。
    支持题材关联度分析、轮动速度分析。

    Attributes:
        config: 应用配置
        theme_history: 题材历史数据缓存（用于持续性分析）
    """

    def __init__(self, config: AppConfig):
        """初始化题材分析器

        Args:
            config: 应用配置对象
        """
        self.config = config
        # 题材历史记录: {theme_name: [{date, limit_up_count, avg_change, ...}, ...]}
        self._theme_history: Dict[str, List[Dict]] = {}
        # 题材阶段历史: {theme_name: [(date, stage), ...]}
        self._theme_stage_history: Dict[str, List[Tuple[date, ThemeCycle]]] = {}

        logger.info("题材周期分析器初始化完成")

    def analyze_themes(
        self,
        themes: List[ThemeData],
        limit_up_stocks: List[LimitUpStock],
        dragon_bonds: List[DragonBond],
        trade_date: Optional[date] = None,
    ) -> List[ThemeCycleAnalysis]:
        """题材全周期演化研判

        对所有热门题材进行生命周期定位和持续性预判。

        Args:
            themes: 题材数据列表
            limit_up_stocks: 涨停股列表（用于交叉验证）
            dragon_bonds: 龙虎榜数据（用于资金流向分析）
            trade_date: 交易日

        Returns:
            List[ThemeCycleAnalysis] 各题材的周期分析结果

        Raises:
            ModuleError: 分析过程发生错误
        """
        trade_date = trade_date or date.today()
        logger.info(f"开始题材周期分析: {trade_date.isoformat()}, 题材数: {len(themes)}")

        try:
            results: List[ThemeCycleAnalysis] = []

            for theme in themes:
                # 更新历史记录
                self._update_theme_history(theme, trade_date)

                # 生命周期判定
                stage = self._determine_stage(theme, limit_up_stocks)

                # 持续性类型判断
                persistence = self._judge_persistence(theme, trade_date)

                # 操作节点生成
                entry, add, take_profit, exit_point = self._generate_operation_points(
                    stage, theme
                )

                # 趋势预判
                prediction = self._predict_theme_trend(theme, stage, persistence)

                # 轮动目标预判
                rotation_target = self._predict_rotation_target(theme, themes, dragon_bonds)

                analysis = ThemeCycleAnalysis(
                    theme_name=theme.theme_name,
                    current_stage=stage,
                    persistence_type=persistence,
                    prediction=prediction,
                    entry_point=entry,
                    add_point=add,
                    take_profit_point=take_profit,
                    exit_point=exit_point,
                    rotation_target=rotation_target,
                )
                results.append(analysis)

                logger.debug(
                    f"题材[{theme.theme_name}]分析完成",
                    stage=stage.value,
                    persistence=persistence,
                )

            # 按题材强度排序
            results.sort(key=lambda x: self._get_theme_priority(x), reverse=True)

            logger.info(f"题材周期分析完成: {len(results)}个题材")
            return results

        except Exception as e:
            logger.error(f"题材周期分析错误: {e}")
            raise ModuleError(f"题材周期分析失败: {e}")

    def get_theme_trend(
        self,
        theme_name: str,
        days: int = 5,
    ) -> List[Dict]:
        """获取指定题材近期走势数据

        Args:
            theme_name: 题材名称
            days: 回溯天数

        Returns:
            List[Dict] 近期走势数据列表
        """
        history = self._theme_history.get(theme_name, [])
        if not history:
            return []

        # 按日期排序取最近days条
        sorted_history = sorted(history, key=lambda x: x["date"], reverse=True)
        return sorted_history[:days]

    def update_hot_themes(self, themes: List[str]) -> None:
        """更新热门题材列表（可由外部模块调用）

        Args:
            themes: 热门题材名称列表
        """
        logger.info(f"热门题材列表更新: {themes}")

    def analyze_theme_correlations(
        self,
        themes: List[ThemeData],
        days: int = 10,
    ) -> List[ThemeCorrelation]:
        """分析题材间关联度

        基于历史数据，分析题材间的联动关系，识别正相关、负相关题材对。

        Args:
            themes: 题材数据列表
            days: 分析天数

        Returns:
            List[ThemeCorrelation] 题材关联度列表
        """
        correlations: List[ThemeCorrelation] = []
        theme_names = [t.theme_name for t in themes]

        for i, theme_a in enumerate(theme_names):
            for theme_b in theme_names[i + 1:]:
                corr = self._calculate_theme_correlation(theme_a, theme_b, days)
                if corr.correlation_score > 20:  # 只返回有关联的
                    correlations.append(corr)

        # 按关联度排序
        correlations.sort(key=lambda x: x.correlation_score, reverse=True)
        return correlations

    def analyze_rotation_speed(
        self,
        theme_name: str,
    ) -> Optional[ThemeRotationSpeed]:
        """分析题材轮动速度

        基于题材阶段历史，分析轮动速度和预估剩余时间。

        Args:
            theme_name: 题材名称

        Returns:
            ThemeRotationSpeed 轮动速度分析结果
        """
        stage_history = self._theme_stage_history.get(theme_name, [])
        if len(stage_history) < 2:
            return None

        # 统计各阶段持续天数
        stage_duration: Dict[str, int] = {}
        current_stage = stage_history[0][1]
        current_start = stage_history[0][0]

        for date_val, stage in stage_history[1:]:
            if stage != current_stage:
                duration = (date_val - current_start).days
                stage_name = current_stage.value
                stage_duration[stage_name] = stage_duration.get(stage_name, 0) + duration
                current_stage = stage
                current_start = date_val

        # 当前阶段已持续天数
        if stage_history:
            last_date = stage_history[-1][0]
            current_duration = (last_date - current_start).days
            current_stage_name = current_stage.value
            stage_duration[current_stage_name] = stage_duration.get(current_stage_name, 0) + current_duration

        # 计算轮动速度（总天数/阶段数）
        total_days = sum(stage_duration.values())
        stage_count = len(stage_duration)
        rotation_speed = total_days / max(stage_count, 1)

        # 判断是否加速轮动
        is_accelerating = False
        if len(stage_history) >= 4:
            recent_stages = [s for _, s in stage_history[-4:]]
            unique_recent = len(set(recent_stages))
            if unique_recent >= 3:
                is_accelerating = True

        # 预估剩余天数
        stage_order = [
            ThemeCycle.SPROUT,
            ThemeCycle.FERMENT,
            ThemeCycle.ACCELERATE,
            ThemeCycle.DIVERGE,
            ThemeCycle.COMPLEMENT,
            ThemeCycle.RETREAT,
        ]
        current_idx = stage_order.index(current_stage) if current_stage in stage_order else 0
        remaining_stages = len(stage_order) - current_idx - 1
        estimated_remaining = int(remaining_stages * rotation_speed)

        return ThemeRotationSpeed(
            theme_name=theme_name,
            rotation_speed=round(rotation_speed, 1),
            stage_duration=stage_duration,
            is_accelerating=is_accelerating,
            estimated_remaining_days=max(0, estimated_remaining),
        )

    def get_theme_momentum(
        self,
        theme_name: str,
        days: int = 5,
    ) -> Dict:
        """获取题材动量指标

        计算题材的短期动量，判断题材强度变化趋势。

        Args:
            theme_name: 题材名称
            days: 计算天数

        Returns:
            Dict 动量指标
        """
        history = self._theme_history.get(theme_name, [])
        if len(history) < 2:
            return {"momentum": 0, "trend": "数据不足"}

        recent = sorted(history, key=lambda x: x["date"], reverse=True)[:days]

        # 计算涨停数变化动量
        limit_up_changes = []
        for i in range(1, len(recent)):
            change = recent[i - 1]["limit_up_count"] - recent[i]["limit_up_count"]
            limit_up_changes.append(change)

        avg_change = sum(limit_up_changes) / len(limit_up_changes) if limit_up_changes else 0

        # 计算资金流入动量
        inflow_changes = []
        for i in range(1, len(recent)):
            change = recent[i - 1]["total_inflow"] - recent[i]["total_inflow"]
            inflow_changes.append(change)

        avg_inflow_change = sum(inflow_changes) / len(inflow_changes) if inflow_changes else 0

        # 综合动量
        momentum = avg_change * 10 + avg_inflow_change / 1e7

        if momentum > 5:
            trend = "加速上升"
        elif momentum > 0:
            trend = "温和上升"
        elif momentum > -5:
            trend = "温和下降"
        else:
            trend = "加速下降"

        return {
            "momentum": round(momentum, 2),
            "trend": trend,
            "limit_up_momentum": round(avg_change, 2),
            "inflow_momentum": round(avg_inflow_change / 1e7, 2),
        }

    # ==================== 内部方法 ====================

    def _update_theme_history(self, theme: ThemeData, trade_date: date) -> None:
        """更新题材历史记录"""
        if theme.theme_name not in self._theme_history:
            self._theme_history[theme.theme_name] = []

        record = {
            "date": trade_date.isoformat(),
            "limit_up_count": theme.limit_up_count,
            "avg_change_pct": theme.avg_change_pct,
            "total_inflow": theme.total_inflow,
            "leading_stock": theme.leading_stock,
            "stock_count": len(theme.stocks),
        }

        # 去重（同一天只保留最新）
        self._theme_history[theme.theme_name] = [
            r for r in self._theme_history[theme.theme_name]
            if r["date"] != trade_date.isoformat()
        ]
        self._theme_history[theme.theme_name].append(record)

    def _determine_stage(
        self,
        theme: ThemeData,
        limit_up_stocks: List[LimitUpStock],
    ) -> ThemeCycle:
        """判定题材当前生命周期阶段

        基于多维指标综合判定，按优先级从高到低:
        退潮 → 加速 → 分歧 → 发酵 → 萌芽

        Args:
            theme: 题材数据
            limit_up_stocks: 涨停股列表

        Returns:
            ThemeCycle 生命周期阶段
        """
        scores: Dict[ThemeCycle, float] = {}

        # 获取该题材的涨停股明细
        theme_limit_ups = [lu for lu in limit_up_stocks if lu.theme == theme.theme_name]

        # 退潮判定: 涨停数极少、涨幅低、资金流出
        if (theme.limit_up_count <= 3 and theme.avg_change_pct <= 1.0
                and theme.total_inflow < 0):
            scores[ThemeCycle.RETREAT] = 0.8

        # 高位分歧: 龙头炸板、涨停数减少
        if theme_limit_ups:
            explode_count = sum(lu.explode_count for lu in theme_limit_ups)
            if explode_count >= 3 and theme.limit_up_count < 10:
                scores[ThemeCycle.DIVERGE] = 0.7

        # 主升加速: 涨停多、龙头连板高、资金大幅流入
        theme_max_boards = max(
            (lu.consecutive_boards for lu in theme_limit_ups),
            default=0,
        )
        if (theme.limit_up_count >= 8 and theme_max_boards >= 3
                and theme.total_inflow >= 8e8):
            scores[ThemeCycle.ACCELERATE] = 0.8

        # 资金发酵: 涨停增多、有连板、资金流入
        if (theme.limit_up_count >= 3 and theme_max_boards >= 2
                and theme.total_inflow >= 3e8):
            scores[ThemeCycle.FERMENT] = 0.6

        # 题材萌芽: 少量首板
        if theme.limit_up_count <= 3 and theme.avg_change_pct >= 2.0:
            scores[ThemeCycle.SPROUT] = 0.5

        # 补涨收尾: 龙头滞涨但补涨活跃
        if theme_limit_ups and theme.limit_up_count <= 8 and theme.limit_up_count >= 3:
            avg_boards = sum(lu.consecutive_boards for lu in theme_limit_ups) / len(theme_limit_ups)
            if avg_boards < 2:
                scores[ThemeCycle.COMPLEMENT] = 0.5

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]

        return ThemeCycle.SPROUT  # 默认萌芽

    def _judge_persistence(self, theme: ThemeData, trade_date: date) -> str:
        """判断题材持续性类型

        Args:
            theme: 题材数据
            trade_date: 交易日

        Returns:
            str: "长期主线" / "短期套利" / "一日游"
        """
        history = self._theme_history.get(theme.theme_name, [])

        if not history:
            return "一日游"  # 无历史数据，暂判一日游

        # 计算持续天数（有涨停记录的天数）
        active_days = len([h for h in history if h["limit_up_count"] > 0])
        total_limit_ups = sum(h["limit_up_count"] for h in history)

        # 长期主线判定
        if (active_days >= 5 and total_limit_ups >= 20
                and theme.leading_stock is not None):
            return "长期主线"

        # 短期套利判定
        if (2 <= active_days <= 4 and total_limit_ups >= 8):
            return "短期套利"

        # 一日游
        if active_days <= 1 and total_limit_ups <= 5:
            return "一日游"

        # 中间状态，根据综合特征判断
        if theme.leading_stock and total_limit_ups >= 10:
            return "短期套利" if active_days <= 3 else "长期主线"

        return "短期套利"

    def _generate_operation_points(
        self,
        stage: ThemeCycle,
        theme: ThemeData,
    ) -> Tuple[str, str, str, str]:
        """生成操作节点建议

        Args:
            stage: 生命周期阶段
            theme: 题材数据

        Returns:
            Tuple[str, str, str, str]: (入场点, 加仓点, 止盈点, 清仓点)
        """
        operations = {
            ThemeCycle.SPROUT: (
                "首板试错、低吸题材先锋股",
                "确认题材持续性后加仓（二板定龙头）",
                "加速后高抛、不贪心",
                "题材一日游确认后止损",
            ),
            ThemeCycle.FERMENT: (
                "龙头分歧低吸、跟风首板",
                "涨停梯队完整时加仓",
                "高潮日止盈（缩量加速）",
                "龙头断板或后排先跌清仓",
            ),
            ThemeCycle.ACCELERATE: (
                "不建议新入场（持有者可持有）",
                "不加仓",
                "龙头炸板或封单减少止盈",
                "分歧日不修复清仓",
            ),
            ThemeCycle.DIVERGE: (
                "仅龙头首阴低吸（高手）",
                "不加仓",
                "反弹不创新高止盈",
                "确认退潮清仓",
            ),
            ThemeCycle.COMPLEMENT: (
                "补涨股低吸",
                "补涨股涨停次日不加仓",
                "补涨股涨停开板止盈",
                "龙头持续弱势清仓",
            ),
            ThemeCycle.RETREAT: (
                "停止买入、空仓观望",
                "不加仓",
                "有持仓立即止盈/止损",
                "全部清仓",
            ),
        }
        return operations.get(stage, (
            "观察等待", "观察等待", "观察等待", "观察等待"
        ))

    def _predict_theme_trend(
        self,
        theme: ThemeData,
        stage: ThemeCycle,
        persistence: str,
    ) -> str:
        """预判题材后续走势

        Args:
            theme: 题材数据
            stage: 生命周期阶段
            persistence: 持续性类型

        Returns:
            str 趋势预判描述
        """
        trend_map = {
            ThemeCycle.SPROUT: {
                "长期主线": "题材具备成为主线的潜力，关注龙头持续性和板块扩散",
                "短期套利": "题材可能走2-3天短线行情，快进快出",
                "一日游": "题材持续性差，次日大概率分化",
            },
            ThemeCycle.FERMENT: {
                "长期主线": "题材发酵良好，有望进入主升阶段，可积极布局",
                "短期套利": "题材进入加速期，注意及时兑现",
                "一日游": "一日游题材发酵属异常，警惕诱多",
            },
            ThemeCycle.ACCELERATE: {
                "长期主线": "主线加速中，持有核心标的但注意高潮信号",
                "短期套利": "加速即尾声，次日逢高减仓",
                "一日游": "一日游加速是离场信号",
            },
            ThemeCycle.DIVERGE: {
                "长期主线": "主线分歧，若龙头能抗住可能走二波",
                "短期套利": "分歧后大概率退潮，减仓为主",
                "一日游": "一日游分歧后直接结束",
            },
            ThemeCycle.COMPLEMENT: {
                "长期主线": "主线高位震荡，补涨后可能结束",
                "短期套利": "补涨行情接近尾声",
                "一日游": "一日游无补涨阶段",
            },
            ThemeCycle.RETREAT: {
                "长期主线": "主线退潮中，等待企稳后可能有二波",
                "短期套利": "退潮结束，不再关注",
                "一日游": "一日游已结束",
            },
        }

        stage_trends = trend_map.get(stage, {})
        return stage_trends.get(persistence, "走势不明，保持观察")

    def _predict_rotation_target(
        self,
        current_theme: ThemeData,
        all_themes: List[ThemeData],
        dragon_bonds: List[DragonBond],
    ) -> Optional[str]:
        """预判资金轮动目标题材

        基于当前题材状态和资金流向，预判资金可能切换的方向。

        Args:
            current_theme: 当前题材
            all_themes: 所有题材列表
            dragon_bonds: 龙虎榜数据

        Returns:
            Optional[str] 预判的轮动目标题材，无则None
        """
        # 仅对退潮或分歧阶段题材做轮动预判
        if current_theme.cycle_stage not in (ThemeCycle.DIVERGE, ThemeCycle.RETREAT):
            return None

        # 查找近期开始活跃的题材（萌芽/发酵期）
        candidates = [
            t for t in all_themes
            if t.theme_name != current_theme.theme_name
            and t.cycle_stage in (ThemeCycle.SPROUT, ThemeCycle.FERMENT)
            and t.total_inflow > 0
        ]

        if not candidates:
            return None

        # 按资金流入排序，选最可能承接资金的题材
        best_candidate = max(candidates, key=lambda t: t.total_inflow + t.limit_up_count * 1e8)

        # 仅当有明显资金流入时才给出轮动预判
        if best_candidate.total_inflow > 1e8:
            return best_candidate.theme_name

        return None

    def _get_theme_priority(self, analysis: ThemeCycleAnalysis) -> float:
        """计算题材优先级（用于排序）

        排序优先级:
        1. 发酵期和加速期优先
        2. 长期主线优先
        3. 涨停数多的优先
        """
        stage_scores = {
            ThemeCycle.ACCELERATE: 100,
            ThemeCycle.FERMENT: 90,
            ThemeCycle.SPROUT: 70,
            ThemeCycle.DIVERGE: 50,
            ThemeCycle.COMPLEMENT: 30,
            ThemeCycle.RETREAT: 10,
        }
        stage_score = stage_scores.get(analysis.current_stage, 0)

        persistence_scores = {
            "长期主线": 20,
            "短期套利": 10,
            "一日游": 0,
        }
        persistence_score = persistence_scores.get(analysis.persistence_type, 0)

        return stage_score + persistence_score

    def _calculate_theme_correlation(
        self,
        theme_a: str,
        theme_b: str,
        days: int,
    ) -> ThemeCorrelation:
        """计算两个题材的关联度"""
        history_a = self._theme_history.get(theme_a, [])
        history_b = self._theme_history.get(theme_b, [])

        if not history_a or not history_b:
            return ThemeCorrelation(
                theme_a=theme_a,
                theme_b=theme_b,
                correlation_score=0,
                correlation_type="无关联",
            )

        # 按日期对齐
        dates_a = {h["date"]: h for h in history_a[-days:]}
        dates_b = {h["date"]: h for h in history_b[-days:]}
        common_dates = sorted(set(dates_a.keys()) & set(dates_b.keys()))

        if len(common_dates) < 3:
            return ThemeCorrelation(
                theme_a=theme_a,
                theme_b=theme_b,
                correlation_score=0,
                correlation_type="数据不足",
            )

        # 计算涨跌同向天数
        co_movement = 0
        total_pairs = 0

        for i in range(1, len(common_dates)):
            date_curr = common_dates[i]
            date_prev = common_dates[i - 1]

            change_a = dates_a[date_curr]["avg_change_pct"] - dates_a[date_prev]["avg_change_pct"]
            change_b = dates_b[date_curr]["avg_change_pct"] - dates_b[date_prev]["avg_change_pct"]

            # 同向运动
            if (change_a > 0 and change_b > 0) or (change_a < 0 and change_b < 0):
                co_movement += 1
            total_pairs += 1

        # 关联度计算
        if total_pairs > 0:
            correlation_ratio = co_movement / total_pairs
            correlation_score = correlation_ratio * 100
        else:
            correlation_score = 0

        # 判断关联类型
        if correlation_score > 70:
            correlation_type = "强正相关"
        elif correlation_score > 50:
            correlation_type = "正相关"
        elif correlation_score < 30:
            correlation_type = "负相关"
        else:
            correlation_type = "弱关联"

        return ThemeCorrelation(
            theme_a=theme_a,
            theme_b=theme_b,
            correlation_score=round(correlation_score, 1),
            correlation_type=correlation_type,
            co_movement_days=co_movement,
            lead_lag_days=0,  # 需要更复杂的分析
        )

    def _update_theme_stage_history(self, theme_name: str, stage: ThemeCycle, trade_date: date) -> None:
        """更新题材阶段历史"""
        if theme_name not in self._theme_stage_history:
            self._theme_stage_history[theme_name] = []

        # 去重
        self._theme_stage_history[theme_name] = [
            (d, s) for d, s in self._theme_stage_history[theme_name]
            if d != trade_date
        ]
        self._theme_stage_history[theme_name].append((trade_date, stage))

        # 保持最多60天
        if len(self._theme_stage_history[theme_name]) > 60:
            self._theme_stage_history[theme_name] = self._theme_stage_history[theme_name][-60:]
