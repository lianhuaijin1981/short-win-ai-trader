"""大盘趋势推演器 — 次日大盘走势预判

基于以下维度进行大盘趋势推演:
- 指数量能结构: 量价关系、量能变化趋势
- 均线形态: 5/10/20日线位置关系
- 关键支撑/压力位: 基于近期高低点和均线
- 市场承接力度: 涨跌家数、炸板率、赚钱效应
- 外围情绪联动: 外围市场表现对A股的影响

输出:
- 次日整体走势预判（震荡整理/强势延续/弱势调整/探底修复）
- 关键支撑位/压力位量化标注
- 趋势拐点预警
- 系统性风险提醒
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    EmotionCycle,
    EmotionDiagnosis,
    EmotionIndicators,
    MarketSnapshot,
    NextDayPrediction,
)

logger = get_logger("swat.m02.market_predictor")


@dataclass
class TechnicalContext:
    """技术面上下文"""
    sh_index: float = 0.0           # 上证指数
    ma5: float = 0.0                # 5日均线
    ma10: float = 0.0               # 10日均线
    ma20: float = 0.0               # 20日均线
    volume_ma5: float = 0.0         # 5日均量
    recent_high: float = 0.0        # 近期高点
    recent_low: float = 0.0         # 近期低点
    support_level_1: float = 0.0    # 第一支撑
    support_level_2: float = 0.0    # 第二支撑
    resistance_level_1: float = 0.0 # 第一阻力
    resistance_level_2: float = 0.0 # 第二阻力


class MarketPredictor:
    """大盘趋势推演器

    综合分析市场情绪诊断结果和技术面数据，
    推演次日大盘走势并输出关键点位。

    Attributes:
        config: 应用配置
    """

    def __init__(self, config: AppConfig):
        """初始化推演器

        Args:
            config: 应用配置对象
        """
        self.config = config
        logger.info("大盘趋势推演器初始化完成")

    def predict_next_day(
        self,
        diagnosis: EmotionDiagnosis,
        market_snap: Optional[MarketSnapshot] = None,
        technical_ctx: Optional[TechnicalContext] = None,
        global_context: Optional[Dict] = None,
    ) -> NextDayPrediction:
        """次日大盘趋势预判

        综合情绪周期诊断、市场快照数据、技术面和外围环境，
        对次日大盘走势进行多维度推演。

        Args:
            diagnosis: 情绪周期诊断结果
            market_snap: 市场快照（可选）
            technical_ctx: 技术面上下文（可选，含均线/支撑压力位）
            global_context: 外围市场环境（可选）

        Returns:
            NextDayPrediction 次日趋势预判结果

        Raises:
            ModuleError: 推演过程发生错误
        """
        try:
            logger.info("开始次日大盘趋势推演...")

            indicators = diagnosis.indicators
            if indicators is None:
                raise ModuleError("情绪指标数据缺失，无法进行趋势推演")

            # 1. 基于情绪周期判断基础趋势
            base_trend = self._emotion_based_trend(diagnosis.current_cycle)

            # 2. 结合技术面修正
            tech_adjustment = self._technical_adjustment(technical_ctx)

            # 3. 结合量能分析修正
            volume_adjustment = self._volume_adjustment(indicators)

            # 4. 结合外围环境修正
            global_adjustment = self._global_adjustment(global_context)

            # 5. 综合判定最终趋势
            final_trend = self._combine_trend_factors(
                base_trend, tech_adjustment, volume_adjustment, global_adjustment
            )

            # 6. 计算关键支撑/压力位
            support, resistance = self._calculate_key_levels(
                market_snap, technical_ctx, diagnosis
            )

            # 7. 生成风险提示
            risk_warning = self._generate_risk_warning(diagnosis, final_trend, indicators)

            prediction = NextDayPrediction(
                trend=final_trend,
                support_level=round(support, 2),
                resistance_level=round(resistance, 2),
                risk_warning=risk_warning,
            )

            logger.info(
                "大盘趋势推演完成",
                trend=prediction.trend,
                support=support,
                resistance=resistance,
                has_risk=risk_warning is not None,
            )

            return prediction

        except Exception as e:
            logger.error(f"大盘趋势推演错误: {e}")
            raise ModuleError(f"大盘趋势推演失败: {e}")

    # ==================== 趋势判定方法 ====================

    def _emotion_based_trend(self, cycle: EmotionCycle) -> str:
        """基于情绪周期的基础趋势判断

        Args:
            cycle: 当前情绪周期

        Returns:
            str: 基础趋势倾向
        """
        trend_map = {
            EmotionCycle.CHAOS: "震荡整理",      # 混沌期: 方向不明
            EmotionCycle.START: "探底修复",       # 启动期: 开始修复
            EmotionCycle.FERMENT: "强势延续",     # 发酵期: 延续强势
            EmotionCycle.PEAK: "强势延续",        # 高潮期: 惯性延续（但风险积聚）
            EmotionCycle.DIVERGE: "弱势调整",     # 分歧期: 开始调整
            EmotionCycle.RETREAT: "弱势调整",     # 退潮期: 调整为主
        }
        return trend_map.get(cycle, "震荡整理")

    def _technical_adjustment(self, technical_ctx: Optional[TechnicalContext]) -> float:
        """技术面修正因子

        基于均线系统和形态给出 -1.0 ~ +1.0 的修正值

        Args:
            technical_ctx: 技术面上下文

        Returns:
            float: 修正因子
        """
        if technical_ctx is None:
            return 0.0

        adjustment = 0.0
        idx = technical_ctx.sh_index

        # 均线系统判断
        if idx > technical_ctx.ma5 > technical_ctx.ma10 > technical_ctx.ma20:
            adjustment += 0.5  # 多头排列，偏强
        elif idx < technical_ctx.ma5 < technical_ctx.ma10 < technical_ctx.ma20:
            adjustment -= 0.5  # 空头排列，偏弱

        # 与5日线关系
        if idx > technical_ctx.ma5 * 1.02:
            adjustment += 0.2
        elif idx < technical_ctx.ma5 * 0.98:
            adjustment -= 0.2

        # 与近期高低点关系
        if technical_ctx.recent_high > technical_ctx.recent_low:
            position = (idx - technical_ctx.recent_low) / (technical_ctx.recent_high - technical_ctx.recent_low)
            if position > 0.8:
                adjustment -= 0.2  # 接近高点，承压
            elif position < 0.2:
                adjustment += 0.2  # 接近低点，有支撑

        return max(-1.0, min(1.0, adjustment))

    def _volume_adjustment(self, indicators: EmotionIndicators) -> float:
        """量能分析修正因子

        基于量能变化给出 -1.0 ~ +1.0 的修正值

        Args:
            indicators: 情绪指标

        Returns:
            float: 修正因子
        """
        adjustment = 0.0
        vol_change = indicators.volume_change

        if vol_change > 30:
            # 放量过猛，可能是赶顶或恐慌
            adjustment -= 0.3
        elif vol_change > 10:
            # 温和放量，正面
            adjustment += 0.3
        elif vol_change > -10:
            # 量平，中性
            adjustment += 0.0
        elif vol_change > -30:
            # 缩量，观望
            adjustment -= 0.2
        else:
            # 急剧缩量，警惕
            adjustment -= 0.4

        # 结合主力资金
        if indicators.main_inflow_ratio > 30:
            adjustment += 0.3
        elif indicators.main_inflow_ratio < -30:
            adjustment -= 0.3

        return max(-1.0, min(1.0, adjustment))

    def _global_adjustment(self, global_context: Optional[Dict]) -> float:
        """外围环境修正因子

        基于外围市场表现给出 -1.0 ~ +1.0 的修正值

        Args:
            global_context: 外围市场环境

        Returns:
            float: 修正因子
        """
        if global_context is None:
            return 0.0

        adjustment = 0.0

        # 美股表现
        us_change = global_context.get("us_overnight_change", 0.0)
        if us_change > 1.5:
            adjustment += 0.3
        elif us_change > 0.5:
            adjustment += 0.15
        elif us_change < -1.5:
            adjustment -= 0.3
        elif us_change < -0.5:
            adjustment -= 0.15

        # 港股表现
        hk_change = global_context.get("hk_overnight_change", 0.0)
        if hk_change > 1.0:
            adjustment += 0.2
        elif hk_change < -1.0:
            adjustment -= 0.2

        # 汇率
        usdcny_change = global_context.get("usdcny_change", 0.0)
        if usdcny_change > 0.3:  # 人民币贬值
            adjustment -= 0.15
        elif usdcny_change < -0.3:  # 人民币升值
            adjustment += 0.15

        # 富时A50
        a50_change = global_context.get("ftse_a50_change", 0.0)
        if a50_change > 0.8:
            adjustment += 0.2
        elif a50_change < -0.8:
            adjustment -= 0.2

        return max(-1.0, min(1.0, adjustment))

    def _combine_trend_factors(
        self,
        base_trend: str,
        tech_adj: float,
        vol_adj: float,
        global_adj: float,
    ) -> str:
        """综合多因素判定最终趋势

        将基础趋势与三个修正因子综合，得出最终趋势判断。

        Args:
            base_trend: 情绪周期基础趋势
            tech_adj: 技术面修正
            vol_adj: 量能修正
            global_adj: 外围修正

        Returns:
            str: 最终趋势判断
        """
        total_adjustment = tech_adj + vol_adj + global_adj

        # 趋势映射
        trend_order = ["弱势调整", "震荡整理", "探底修复", "强势延续"]

        # 基础趋势索引
        base_index = trend_order.index(base_trend) if base_trend in trend_order else 1

        # 应用修正: adjustment范围-3~+3，每1.5个单位移动一个趋势档位
        shift = int(total_adjustment / 1.2)
        final_index = max(0, min(len(trend_order) - 1, base_index + shift))

        return trend_order[final_index]

    def _calculate_key_levels(
        self,
        market_snap: Optional[MarketSnapshot],
        technical_ctx: Optional[TechnicalContext],
        diagnosis: EmotionDiagnosis,
    ) -> Tuple[float, float]:
        """计算关键支撑/压力位

        Args:
            market_snap: 市场快照
            technical_ctx: 技术面上下文
            diagnosis: 情绪诊断

        Returns:
            Tuple[float, float]: (支撑位, 压力位)
        """
        sh_index = market_snap.sh_index if market_snap else 3000.0

        if technical_ctx:
            # 使用技术面数据
            support = min(
                technical_ctx.support_level_1 or sh_index * 0.98,
                technical_ctx.ma5 or sh_index * 0.99,
                technical_ctx.ma10 or sh_index * 0.985,
            )
            resistance = max(
                technical_ctx.resistance_level_1 or sh_index * 1.02,
                technical_ctx.ma5 or sh_index * 1.01,
                technical_ctx.ma10 or sh_index * 1.015,
            )
        else:
            # 使用情绪指标估算
            indicators = diagnosis.indicators
            if indicators:
                # 情绪好则压力位远，支撑位近；情绪差则相反
                emotion_factor = indicators.profit_effect / 100
                support = sh_index * (0.97 + emotion_factor * 0.02)
                resistance = sh_index * (1.01 + (1 - emotion_factor) * 0.02)
            else:
                support = sh_index * 0.98
                resistance = sh_index * 1.02

        return support, resistance

    def _generate_risk_warning(
        self,
        diagnosis: EmotionDiagnosis,
        trend: str,
        indicators: EmotionIndicators,
    ) -> Optional[str]:
        """生成风险提示

        当出现系统性风险信号时，生成风险警告。

        Args:
            diagnosis: 情绪诊断
            trend: 预判趋势
            indicators: 情绪指标

        Returns:
            Optional[str]: 风险警告文本，无风险则None
        """
        warnings: List[str] = []

        # 退潮期强制提示
        if diagnosis.current_cycle == EmotionCycle.RETREAT:
            warnings.append("情绪处于退潮期，次日系统性风险较大，建议空仓规避")

        # 高潮期警惕
        if diagnosis.current_cycle == EmotionCycle.PEAK:
            warnings.append("情绪处于高潮期，次日大概率分化，注意兑现利润")

        # 炸板率异常
        if indicators.explode_rate > 50:
            warnings.append(f"炸板率高达{indicators.explode_rate:.1f}%，市场承接极弱")

        # 跌停过多
        if hasattr(indicators, "limit_down_count") and indicators.limit_down_count > 20:
            warnings.append("跌停数量过多，恐慌情绪蔓延")

        # 量能骤减
        if indicators.volume_change < -40:
            warnings.append(f"量能骤减{abs(indicators.volume_change):.1f}%，流动性风险")

        # 趋势与情绪背离
        if trend == "强势延续" and diagnosis.current_cycle in (EmotionCycle.DIVERGE, EmotionCycle.RETREAT):
            warnings.append("趋势预判与情绪周期背离，需警惕假突破")

        if not warnings:
            return None

        return "; ".join(warnings)

    def generate_technical_context_from_prices(
        self,
        sh_index_prices: List[float],
        volumes: Optional[List[float]] = None,
    ) -> TechnicalContext:
        """从历史价格数据生成技术面上下文

        Args:
            sh_index_prices: 上证指数近期收盘价列表（从旧到新）
            volumes: 对应成交量列表（可选）

        Returns:
            TechnicalContext 技术面上下文
        """
        if len(sh_index_prices) < 20:
            # 数据不足，使用默认值
            return TechnicalContext(
                sh_index=sh_index_prices[-1] if sh_index_prices else 3000.0,
            )

        ctx = TechnicalContext()
        ctx.sh_index = sh_index_prices[-1]

        # 计算均线
        ctx.ma5 = sum(sh_index_prices[-5:]) / 5
        ctx.ma10 = sum(sh_index_prices[-10:]) / 10
        ctx.ma20 = sum(sh_index_prices[-20:]) / 20

        # 近期高低点（近10日）
        recent = sh_index_prices[-10:]
        ctx.recent_high = max(recent)
        ctx.recent_low = min(recent)

        # 支撑位
        ctx.support_level_1 = ctx.ma10
        ctx.support_level_2 = ctx.ma20

        # 压力位
        ctx.resistance_level_1 = ctx.recent_high
        ctx.resistance_level_2 = ctx.ma5 * 1.02 if ctx.ma5 > ctx.ma10 else ctx.ma10 * 1.02

        # 均量
        if volumes and len(volumes) >= 5:
            ctx.volume_ma5 = sum(volumes[-5:]) / 5

        return ctx
