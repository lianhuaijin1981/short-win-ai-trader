"""完整交易计划生成器 — 入场/持有/卖出全流程"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.logger import get_logger
from ...data_platform.data_models import TradePlan

logger = get_logger("swat.trade_plan")


class TradePlanner:
    """交易计划生成器
    
    生成标准化可直接执行的交易计划:
    - 3类入场点: 突破入场 / 回踩入场 / 分歧入场
    - 3层止损: 逻辑止损 → 技术止损 → 固定止损(3-5%)
    - 3层止盈: 目标止盈(8-20%) → 动态止盈 → 情绪止盈
    """

    def __init__(self, config: AppConfig):
        self.config = config
        logger.info("交易计划生成器初始化完成")

    def generate_trade_plan(
        self,
        ticker: str,
        stock_name: str,
        score: float,
        rating: str,
        risk_reward_ratio: float,
        position_pct: float,
        entry_type: str,
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        context: Optional[Dict] = None,
    ) -> TradePlan:
        """生成完整交易计划"""

        # 持有条件
        hold_conditions = self._generate_hold_conditions(rating, context)

        # 卖出条件
        sell_conditions = self._generate_sell_conditions(rating, context)

        # 应急处理
        emergency = self._generate_emergency_plan(context)

        plan = TradePlan(
            ticker=ticker,
            stock_name=stock_name,
            entry_price=round(entry_price, 2),
            entry_type=entry_type,
            stop_loss_price=round(stop_loss_price, 2),
            take_profit_price=round(take_profit_price, 2),
            position_pct=round(position_pct, 1),
            hold_conditions=hold_conditions,
            sell_conditions=sell_conditions,
            emergency_plan=emergency,
        )

        logger.info(f"交易计划生成: {ticker} {entry_type} 仓位{position_pct}%")
        return plan

    def _generate_hold_conditions(self, rating: str, context: Optional[Dict]) -> List[str]:
        """生成持有条件"""
        conditions = [
            "股价沿5日线上涨，均线多头排列",
            "量能健康（缩量上涨或放量突破）",
            "板块效应持续（涨停≥3只）",
            "所属题材处于主升或发酵阶段",
            "龙头股地位稳固，未被卡位",
        ]

        if rating in ["顶级标的", "优质标的"]:
            conditions.append("资金面持续流入，龙虎榜质量优良")

        return conditions

    def _generate_sell_conditions(self, rating: str, context: Optional[Dict]) -> List[str]:
        """生成卖出条件（满足任一即卖出）"""
        conditions = [
            "【逻辑止损】题材证伪 / 龙头跌停 / 板块崩溃 / 情绪周期退潮 → 无条件卖出",
            f"【技术止损】跌破5日线/10日线或关键支撑位，当日无法收回 → 卖出",
            f"【固定止损】亏损达{self.config.risk.default_stop_loss}% → 严格执行止损",
            f"【目标止盈】达到预设收益目标 → 分批卖出（盈利10%减仓50%，盈利20%清仓）",
            "【动态止盈】股价远离5日线>3% / 放量滞涨/长上影（涨幅≥5%且换手≥15%）→ 减仓",
            "【情绪止盈】市场情绪退潮 / 新龙头卡位 / 炸板率>50% → 全部卖出空仓",
        ]
        return conditions

    def _generate_emergency_plan(self, context: Optional[Dict]) -> str:
        """生成应急处理方案"""
        plans = [
            "【停牌】自动提示停牌原因，预判复牌走势，复牌后视情况买入/卖出",
            "【突发利好/利空】3秒内触发提醒，调整评分/仓位/操作指引",
            "【大盘系统性风险】强制提示空仓规避，所有标的立即触发卖出提醒",
            "【个股异动临停】自动解读异动原因，判断良性/恶性，给出后续操作建议",
        ]
        return " | ".join(plans)

    def generate_quick_plan(
        self,
        ticker: str,
        stock_name: str,
        current_price: float,
        score: float,
        rating: str,
    ) -> Dict:
        """生成简易交易计划（快速模式）"""
        # 默认4%止损
        stop_loss_pct = self.config.risk.default_stop_loss
        # 根据评级定止盈
        take_profit_pct = {"顶级标的": 20, "优质标的": 15, "良好标的": 12}.get(rating, 10)

        stop_price = round(current_price * (1 - stop_loss_pct / 100), 2)
        profit_price = round(current_price * (1 + take_profit_pct / 100), 2)

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "suggested_entry": f"{current_price}元附近",
            "stop_loss": f"{stop_price}元（-{stop_loss_pct}%）",
            "take_profit": f"{profit_price}元（+{take_profit_pct}%）",
            "risk_reward": f"{round(take_profit_pct / stop_loss_pct, 1)}:1",
            "rating": rating,
            "score": score,
        }
