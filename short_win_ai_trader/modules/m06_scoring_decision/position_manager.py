"""动态仓位管理系统 — 情绪+胜率双驱动"""

from typing import Dict, Tuple

from ...core.config import AppConfig
from ...core.logger import get_logger
from ...data_platform.data_models import EmotionCycle

logger = get_logger("swat.position")


class PositionManager:
    """动态仓位管理器
    
    核心公式: 单票仓位 = 基础仓位 × 评分系数 × 胜率系数 × 风险系数
    
    仓位与情绪周期刚性绑定:
    - 冰点期: 1-3成，单票≤10%
    - 复苏期: 5-7成，单票≤40%
    - 发酵期: 5-6成，单票≤35%
    - 高潮期: <3成，单票≤20%
    - 分歧期: 2-3成，单票≤15%
    - 退潮期: 0-1成，单票≤5%
    """

    # 情绪周期 → (总仓位上限%, 单票上限%, 基础仓位%)
    CYCLE_POSITION = {
        EmotionCycle.CHAOS: (20, 10, 10),    # 混沌
        EmotionCycle.START: (40, 40, 20),    # 启动
        EmotionCycle.FERMENT: (60, 35, 20),  # 发酵
        EmotionCycle.PEAK: (30, 20, 10),     # 高潮
        EmotionCycle.DIVERGE: (30, 15, 10),  # 分歧
        EmotionCycle.RETREAT: (10, 5, 0),    # 退潮
    }

    # 评级 → 胜率系数
    RATING_WIN_RATE = {
        "顶级标的": 1.2,
        "优质标的": 1.1,
        "良好标的": 1.0,
        "一般标的": 0.8,
        "劣质标的": 0.6,
    }

    def __init__(self, config: AppConfig):
        self.config = config
        logger.info("仓位管理器初始化完成")

    def calculate_position(
        self,
        emotion_cycle: EmotionCycle,
        total_score: float,
        rating: str,
        risk_reward_ratio: float,
    ) -> Dict:
        """计算建议仓位
        
        Returns:
            Dict with total_limit, single_limit, recommended_pct, formula_details
        """
        cycle_cfg = self.CYCLE_POSITION.get(emotion_cycle, (20, 10, 10))
        total_limit, single_limit, base_position = cycle_cfg

        # 评分系数 = 综合评分 / 80
        score_coeff = min(1.25, max(0.75, total_score / 80))

        # 胜率系数
        win_rate_coeff = self.RATING_WIN_RATE.get(rating, 1.0)

        # 风险系数 = 风险收益比 / 2
        risk_coeff = min(1.5, max(0.75, risk_reward_ratio / 2))

        # 计算单票仓位
        position = base_position * score_coeff * win_rate_coeff * risk_coeff
        recommended_pct = round(min(position, single_limit), 1)

        result = {
            "emotion_cycle": emotion_cycle.value,
            "total_position_limit": f"{total_limit}%",
            "single_stock_limit": f"{single_limit}%",
            "recommended_position": f"{recommended_pct}%",
            "formula": {
                "base_position": f"{base_position}%",
                "score_coefficient": round(score_coeff, 3),
                "win_rate_coefficient": win_rate_coeff,
                "risk_coefficient": round(risk_coeff, 3),
                "calculation": f"{base_position}% × {round(score_coeff, 3)} × {win_rate_coeff} × {round(risk_coeff, 3)} = {round(position, 1)}%",
            },
        }

        logger.info(
            f"仓位计算: 情绪={emotion_cycle.value} 评分={total_score} "
            f"RR={risk_reward_ratio}:1 → 建议仓位={recommended_pct}%"
        )
        return result

    def get_position_warning(
        self,
        current_total_position: float,
        emotion_cycle: EmotionCycle,
    ) -> str:
        """检查是否需要仓位预警"""
        total_limit = self.CYCLE_POSITION.get(emotion_cycle, (20,))[0]
        if current_total_position > total_limit:
            return f"⚠️ 当前总仓位{current_total_position}%已超过{emotion_cycle.value}上限{total_limit}%，请减仓！"
        return ""
