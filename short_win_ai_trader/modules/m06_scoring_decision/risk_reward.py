"""风险收益比计算系统 — 短线专用"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.logger import get_logger

logger = get_logger("swat.risk_reward")


@dataclass
class RiskRewardResult:
    """风险收益比计算结果"""
    risk_reward_ratio: float
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    risk_space: float
    reward_space: float
    decision: str
    max_position_pct: float


class RiskRewardCalculator:
    """风险收益比计算器
    
    核心公式: RR = (止盈价 - 入场价) / (入场价 - 止损价)
    
    止损体系(优先级): 逻辑止损 → 技术止损(支撑位-0.5%) → 固定止损(3-5%)
    止盈体系: 目标止盈(8-20%) + 动态止盈 + 情绪止盈(炸板率>50%清仓)
    """

    # 风险收益比决策标准
    DECISION_TABLE = {
        (3.0, float("inf")): ("强烈推荐介入", 40),
        (2.0, 3.0): ("推荐介入", 30),
        (1.5, 2.0): ("谨慎介入", 20),
        (0.0, 1.5): ("不建议介入", 0),
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self.risk_config = config.risk
        logger.info("风险收益比计算器初始化完成")

    def calculate(
        self,
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
    ) -> RiskRewardResult:
        """计算风险收益比
        
        Args:
            entry_price: 入场价格
            stop_loss_price: 止损价格（三重止损综合）
            take_profit_price: 止盈价格
        """
        risk_space = entry_price - stop_loss_price
        reward_space = take_profit_price - entry_price

        if risk_space <= 0:
            risk_space = entry_price * self.risk_config.default_stop_loss / 100

        rr_ratio = round(reward_space / risk_space, 2) if risk_space > 0 else 0

        decision, max_position = self._get_decision(rr_ratio)

        result = RiskRewardResult(
            risk_reward_ratio=rr_ratio,
            entry_price=round(entry_price, 2),
            stop_loss_price=round(stop_loss_price, 2),
            take_profit_price=round(take_profit_price, 2),
            risk_space=round(risk_space, 2),
            reward_space=round(reward_space, 2),
            decision=decision,
            max_position_pct=max_position,
        )

        logger.info(
            f"RR计算: 入场={entry_price} 止损={stop_loss_price} "
            f"止盈={take_profit_price} RR={rr_ratio}:1 → {decision}"
        )
        return result

    def calculate_from_score(
        self,
        entry_price: float,
        rating: str,
        technical_context: Dict,
    ) -> RiskRewardResult:
        """基于评分等级自动计算风险收益比
        
        不同评级对应不同止盈目标:
        - 顶级标的: 20%
        - 优质标的: 15%
        - 良好标的: 12%
        - 一般标的: 8%
        """
        # 根据评级确定止盈比例
        take_profit_pct = {
            "顶级标的": 20,
            "优质标的": 15,
            "良好标的": 12,
            "一般标的": 8,
        }.get(rating, 10)

        # 止损比例（默认4%）
        stop_loss_pct = self.risk_config.default_stop_loss

        # 技术支撑位可作为更精确的止损
        support = technical_context.get("support_price")
        if support and support < entry_price:
            stop_loss_price = round(support * 0.995, 2)  # 支撑位下方0.5%
        else:
            stop_loss_price = round(entry_price * (1 - stop_loss_pct / 100), 2)

        take_profit_price = round(entry_price * (1 + take_profit_pct / 100), 2)

        return self.calculate(entry_price, stop_loss_price, take_profit_price)

    def _get_decision(self, rr_ratio: float) -> Tuple[str, float]:
        """根据风险收益比确定决策"""
        for (low, high), (decision, position) in self.DECISION_TABLE.items():
            if low <= rr_ratio < high:
                return decision, position
        return "不建议介入", 0

    def generate_simple_trade_plan(
        self,
        entry_price: float,
        rating: str,
        technical: Dict,
    ) -> Dict:
        """生成简易交易计划参数"""
        rr = self.calculate_from_score(entry_price, rating, technical)
        return {
            "entry_price": rr.entry_price,
            "stop_loss": rr.stop_loss_price,
            "take_profit": rr.take_profit_price,
            "risk_reward": f"{rr.risk_reward_ratio}:1",
            "risk_space": rr.risk_space,
            "reward_space": rr.reward_space,
            "decision": rr.decision,
            "max_position": f"{rr.max_position_pct}%",
        }
