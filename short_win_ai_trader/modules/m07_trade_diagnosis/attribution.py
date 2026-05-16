"""交易归因分析 — 盈利归因 + 亏损溯源"""

from typing import Dict, List, Optional

from ...core.logger import get_logger
from ...data_platform.data_models import SingleTradeDiagnosis, TradeRecord

logger = get_logger("swat.attribution")


class TradeAttribution:
    """交易归因分析器
    
    盈利交易5维归因: 行情/资讯/技术/模式/操作
    亏损交易7类溯源: 宏观/题材/标的/模式/节奏/风控/信息
    """

    # 盈利归因维度
    PROFIT_DIMENSIONS = [
        "行情层面", "资讯层面", "技术层面", "模式层面", "操作层面",
    ]

    # 亏损错误类型
    LOSS_ERROR_TYPES = [
        "宏观行情错误", "题材判断错误", "标的选择错误",
        "模式使用错误", "买卖节奏错误", "资金风控错误", "信息遗漏错误",
    ]

    def analyze_profit(self, trade: TradeRecord, context: Optional[Dict] = None) -> List[str]:
        """盈利交易深度归因分析"""
        factors = []

        if trade.profit_loss and trade.profit_loss <= 0:
            return factors

        # 行情层面
        if context:
            emotion = context.get("emotion_cycle", "")
            if emotion in ["发酵期", "高潮期"]:
                factors.append(f"【行情】契合{emotion}，市场情绪向上，大势配合")

            theme_cycle = context.get("theme_cycle", "")
            if theme_cycle in ["主升加速", "资金发酵"]:
                factors.append(f"【行情】踩中题材{theme_cycle}周期，题材主升带来溢价")

        # 资讯层面
        factors.append("【资讯】可能提前捕捉到高价值催化资讯，消息落地形成资金合力")

        # 技术层面
        factors.append("【技术】筹码结构健康，量价形态达标，突破/回踩形态标准")

        # 模式层面
        if trade.trade_mode:
            factors.append(f"【模式】贴合{trade.trade_mode}模式，战法运用得当")

        # 操作层面
        factors.append(f"【操作】入场时机精准，仓位控制合理")
        if trade.profit_loss and trade.profit_loss > 0:
            factors.append(f"【操作】止盈纪律到位，最终实现盈利 {trade.profit_loss:.2f} 元")

        return factors

    def analyze_loss(self, trade: TradeRecord, context: Optional[Dict] = None) -> Dict:
        """亏损交易精准溯源排查
        
        Returns:
            Dict with error_type, reasons, improvement
        """
        if trade.profit_loss is None or trade.profit_loss >= 0:
            return {"error_type": None, "reasons": [], "improvement": ""}

        reasons = []
        error_type = "标的选择错误"  # 默认

        # 宏观行情错误
        if context:
            emotion = context.get("emotion_cycle", "")
            if emotion in ["退潮期", "分歧期"]:
                reasons.append(f"【宏观】逆势交易！当前情绪{emotion}，应避免出手")
                error_type = "宏观行情错误"

        # 题材判断错误
        if context:
            theme = context.get("theme_cycle", "")
            if theme in ["题材退潮", "高位分歧"]:
                reasons.append(f"【题材】误判题材持续性，介入了处于{theme}的标的")
                if error_type == "标的选择错误":
                    error_type = "题材判断错误"

        # 标的选择错误
        reasons.append("【标的】标的辨识度不足，无板块联动或筹码高位松动")

        # 模式使用错误
        if trade.trade_mode:
            reasons.append(f"【模式】战法与行情不匹配，{trade.trade_mode}在当前环境下胜率低")

        # 买卖节奏错误
        reasons.append("【节奏】买点不够精准，可能追高介入或卖点犹豫")

        # 资金风控错误
        reasons.append("【风控】止损执行不坚决，亏损扩大后被动持仓")

        # 信息遗漏
        reasons.append("【信息】可能遗漏了高位减持/业绩利空/监管打压等关键信息")

        improvement = self._generate_improvement(error_type, reasons)

        return {
            "error_type": error_type,
            "reasons": reasons,
            "improvement": improvement,
        }

    def _generate_improvement(self, error_type: str, reasons: List[str]) -> str:
        """生成改进建议"""
        improvements = {
            "宏观行情错误": "严格按情绪周期匹配仓位，退潮期/分歧期减少出手频率",
            "题材判断错误": "加强题材生命周期研判，避免介入退潮期题材",
            "标的选择错误": "提高标的筛选标准，只做辨识度TOP3的核心标的",
            "模式使用错误": "战法与行情严格匹配，不适配时宁可空仓",
            "买卖节奏错误": "制定详细买卖计划并严格执行，不临时决策",
            "资金风控错误": "设置硬止损线，到达即执行，不犹豫不格局",
            "信息遗漏错误": "盘前完整阅读资讯和风险清单，高价值资讯优先",
        }
        return improvements.get(error_type, "全面复盘，逐项改进")

    def diagnose(self, trade: TradeRecord, context: Optional[Dict] = None) -> SingleTradeDiagnosis:
        """综合诊断单笔交易"""
        is_profitable = trade.profit_loss is not None and trade.profit_loss > 0

        if is_profitable:
            success_factors = self.analyze_profit(trade, context)
            failure_reasons = []
            error_type = None
            improvement = "继续保持，总结可复制的成功经验"
        else:
            success_factors = []
            loss_analysis = self.analyze_loss(trade, context)
            failure_reasons = loss_analysis["reasons"]
            error_type = loss_analysis["error_type"]
            improvement = loss_analysis["improvement"]

        return SingleTradeDiagnosis(
            trade=trade,
            is_profitable=is_profitable,
            success_factors=success_factors,
            failure_reasons=failure_reasons,
            error_type=error_type,
            improvement=improvement,
        )
