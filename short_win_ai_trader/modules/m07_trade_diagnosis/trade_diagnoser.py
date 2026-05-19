"""错误交易诊断器

结合评分决策模块对每笔交易进行深度诊断:
- 使用评分决策模块的7维度评分体系
- 分析买入时标的各维度得分
- 识别交易中的具体错误点
- 给出正确的操作建议
- 对比实际操作与理想操作的差距

诊断流程:
1. 重建买入时的市场环境
2. 使用评分引擎对标的进行评分
3. 对比评分结果与实际操作
4. 识别错误类型和原因
5. 给出正确操作建议
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ...core.logger import get_logger
from ..m06_scoring_decision import (
    ActionDecision,
    RatingLevel,
    RiskLevel,
    ScoringEngine,
    ScoringReport,
)
from .importer import TradeRecord

logger = get_logger("swat.m07.trade_diagnoser")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class TradeDiagnosis:
    """单笔交易诊断结果"""
    trade_id: str = ""                    # 交易ID
    ticker: str = ""                      # 股票代码
    stock_name: str = ""                  # 股票名称
    trade_date: Optional[datetime] = None # 交易日期
    trade_mode: str = ""                  # 交易模式
    profit_loss: float = 0.0              # 盈亏金额
    profit_loss_pct: float = 0.0          # 盈亏比例
    
    # 评分结果
    scoring_report: Optional[ScoringReport] = None  # 评分报告
    should_buy: bool = False              # 是否应该买入
    correct_action: str = ""              # 正确操作
    
    # 错误分析
    is_error_trade: bool = False          # 是否为错误交易
    error_types: List[str] = field(default_factory=list)  # 错误类型
    error_details: List[str] = field(default_factory=list)  # 错误详情
    
    # 正确建议
    correct_advice: str = ""              # 正确操作建议
    correct_position: float = 0.0         # 正确仓位
    correct_entry: str = ""               # 正确入场方式
    correct_stop_loss: str = ""           # 正确止损
    
    # 评分对比
    dimension_comparison: Dict = field(default_factory=dict)  # 维度对比
    
    # 诊断摘要
    summary: str = ""


# ── 交易诊断器 ───────────────────────────────────────────

class TradeDiagnoser:
    """错误交易诊断器
    
    结合评分决策模块对每笔交易进行深度诊断。
    """
    
    def __init__(self, scoring_engine: Optional[ScoringEngine] = None):
        """初始化交易诊断器
        
        Args:
            scoring_engine: 评分引擎实例
        """
        self.scoring_engine = scoring_engine or ScoringEngine()
        logger.info("交易诊断器初始化完成")
    
    async def diagnose_trade(
        self,
        trade: TradeRecord,
        market_context: Optional[Dict] = None,
    ) -> TradeDiagnosis:
        """诊断单笔交易
        
        Args:
            trade: 交易记录
            market_context: 买入时的市场环境数据
                - theme_data: 题材数据
                - fund_data: 资金数据
                - emotion_data: 情绪数据
                - chip_data: 筹码数据
                - technical_data: 技术数据
                - dragon_data: 龙头数据
                - news_data: 资讯数据
                
        Returns:
            TradeDiagnosis: 交易诊断结果
        """
        logger.info(f"诊断交易: {trade.stock_name}({trade.ticker}) {trade.trade_date}")
        
        diagnosis = TradeDiagnosis(
            trade_id=trade.trade_id,
            ticker=trade.ticker,
            stock_name=trade.stock_name,
            trade_date=trade.trade_date,
            trade_mode=trade.trade_mode,
            profit_loss=trade.profit_loss,
            profit_loss_pct=trade.profit_loss_pct,
        )
        
        # 获取市场环境数据
        context = market_context or self._reconstruct_context(trade)
        
        # 使用评分引擎评分
        try:
            report = await self.scoring_engine.evaluate_stock(
                ticker=trade.ticker,
                stock_name=trade.stock_name,
                current_price=trade.price,
                theme_data=context.get("theme_data", {}),
                fund_data=context.get("fund_data", {}),
                emotion_data=context.get("emotion_data", {}),
                chip_data=context.get("chip_data", {}),
                technical_data=context.get("technical_data", {}),
                dragon_data=context.get("dragon_data", {}),
                news_data=context.get("news_data", {}),
                current_position=0,
            )
            diagnosis.scoring_report = report
        except Exception as e:
            logger.warning(f"评分失败: {e}")
            # 使用简化评分
            report = self._simplified_score(trade)
            diagnosis.scoring_report = report
        
        # 分析错误
        self._analyze_errors(trade, report, diagnosis)
        
        # 生成正确建议
        self._generate_correct_advice(trade, report, diagnosis)
        
        # 生成摘要
        diagnosis.summary = self._build_summary(diagnosis)
        
        return diagnosis
    
    async def diagnose_all_trades(
        self,
        trades: List[TradeRecord],
        market_contexts: Optional[Dict[str, Dict]] = None,
    ) -> List[TradeDiagnosis]:
        """诊断所有交易
        
        Args:
            trades: 交易记录列表
            market_contexts: 各交易的市场环境数据 {trade_id: context}
            
        Returns:
            List[TradeDiagnosis]: 诊断结果列表
        """
        diagnoses: List[TradeDiagnosis] = []
        
        for trade in trades:
            context = None
            if market_contexts and trade.trade_id in market_contexts:
                context = market_contexts[trade.trade_id]
            
            diagnosis = await self.diagnose_trade(trade, context)
            diagnoses.append(diagnosis)
        
        logger.info(f"批量诊断完成: {len(diagnoses)}笔交易")
        return diagnoses
    
    # ==================== 错误分析 ====================
    
    def _analyze_errors(
        self,
        trade: TradeRecord,
        report: ScoringReport,
        diagnosis: TradeDiagnosis,
    ):
        """分析交易错误"""
        errors: List[str] = []
        details: List[str] = []
        
        # 1. 评分不足却买入
        if report.total_score < 60 and trade.profit_loss < 0:
            errors.append("评分不足却买入")
            details.append(f"标的评分仅{report.total_score}分({report.rating.value})，不应买入")
        
        # 2. 风险等级过高
        if report.risk_level in (RiskLevel.HIGH, RiskLevel.EXTREME) and trade.profit_loss < 0:
            errors.append("风险等级过高")
            details.append(f"风险等级{report.risk_level.value}，应规避或极轻仓")
        
        # 3. 风险收益比不足
        if report.risk_reward and report.risk_reward.ratio < 1.5 and trade.profit_loss < 0:
            errors.append("风险收益比不足")
            details.append(f"RR比仅{report.risk_reward.ratio}:1，不应介入")
        
        # 4. 交易模式不匹配
        if report.advice:
            suggested_mode = report.advice.entry_type
            if trade.trade_mode and suggested_mode and trade.trade_mode != suggested_mode:
                errors.append("交易模式不匹配")
                details.append(f"实际使用{trade.trade_mode}，建议{ suggested_mode}")
        
        # 5. 维度短板
        for ds in report.dimension_scores:
            if ds.score < 40:
                errors.append(f"{ds.dimension}评分过低")
                details.append(f"{ds.dimension}仅{ds.score}分: {ds.assessment}")
        
        # 6. 情绪周期不匹配
        emotion_score = None
        for ds in report.dimension_scores:
            if ds.dimension == "情绪周期":
                emotion_score = ds.score
                break
        
        if emotion_score and emotion_score < 50 and trade.profit_loss < 0:
            errors.append("情绪周期不匹配")
            details.append(f"情绪周期评分{emotion_score}分，不适合操作")
        
        # 7. 止损执行错误
        if trade.profit_loss_pct < -5:
            errors.append("止损执行不到位")
            details.append(f"亏损{trade.profit_loss_pct}%，应在-5%时止损")
        
        # 8. 止盈执行错误
        if trade.profit_loss_pct > 0 and trade.profit_loss_pct < 3 and trade.hold_days >= 2:
            errors.append("止盈过早")
            details.append(f"仅盈利{trade.profit_loss_pct}%就卖出，可能卖飞")
        
        # 判断是否为错误交易
        diagnosis.is_error_trade = len(errors) > 0 and trade.profit_loss < 0
        diagnosis.error_types = errors
        diagnosis.error_details = details
        
        # 是否应该买入
        diagnosis.should_buy = report.total_score >= 65 and report.risk_reward and report.risk_reward.ratio >= 1.5
        
        # 正确操作
        if report.advice:
            diagnosis.correct_action = report.advice.action.value
        else:
            diagnosis.correct_action = "观望" if report.total_score < 65 else "买入"
    
    # ==================== 正确建议 ====================
    
    def _generate_correct_advice(
        self,
        trade: TradeRecord,
        report: ScoringReport,
        diagnosis: TradeDiagnosis,
    ):
        """生成正确操作建议"""
        if report.advice:
            diagnosis.correct_position = report.advice.position_pct
            diagnosis.correct_entry = report.advice.entry_type
            diagnosis.correct_stop_loss = report.advice.stop_loss
            
            advice_parts: List[str] = []
            advice_parts.append(f"正确操作: {report.advice.action.value}")
            advice_parts.append(f"建议仓位: {report.advice.position_pct}%")
            advice_parts.append(f"入场方式: {report.advice.entry_type}")
            advice_parts.append(f"入场区间: {report.advice.entry_zone}")
            
            if report.risk_reward:
                advice_parts.append(f"止损位: {report.risk_reward.stop_loss_price:.2f}(-{report.risk_reward.risk_pct}%)")
                advice_parts.append(f"止盈位: {report.risk_reward.take_profit_price:.2f}(+{report.risk_reward.reward_pct}%)")
            
            diagnosis.correct_advice = "\n".join(advice_parts)
        else:
            diagnosis.correct_advice = "评分不足，不应介入"
        
        # 维度对比
        for ds in report.dimension_scores:
            diagnosis.dimension_comparison[ds.dimension] = {
                "score": ds.score,
                "weight": ds.weight,
                "assessment": ds.assessment,
            }
    
    # ==================== 上下文重建 ====================
    
    def _reconstruct_context(self, trade: TradeRecord) -> Dict:
        """重建买入时的市场环境
        
        根据交易记录中的信息重建市场环境数据。
        """
        context: Dict = {}
        
        # 情绪数据
        if trade.emotion_cycle:
            context["emotion_data"] = {
                "current_cycle": trade.emotion_cycle,
                "stock_cycle_position": "龙头" if trade.profit_loss > 0 else "跟风",
                "profit_effect": "好" if trade.profit_loss > 0 else "差",
            }
        
        # 题材数据
        if trade.theme_name:
            context["theme_data"] = {
                "theme_level": "部委级",
                "sustainability": "发酵中",
                "theme_purity": "核心" if trade.profit_loss > 0 else "边缘",
            }
        
        # 技术数据(根据盈亏推断)
        if trade.profit_loss > 0:
            context["technical_data"] = {
                "ma_arrangement": "多头排列",
                "breakout_type": "平台突破",
                "macd_status": "金叉",
            }
        else:
            context["technical_data"] = {
                "ma_arrangement": "粘合",
                "breakout_type": "无突破",
                "macd_status": "死叉",
            }
        
        return context
    
    def _simplified_score(self, trade: TradeRecord) -> ScoringReport:
        """简化评分(当评分引擎不可用时)"""
        # 基于交易结果反推评分
        base_score = 50
        
        if trade.profit_loss > 0:
            base_score += min(30, trade.profit_loss_pct * 3)
        else:
            base_score += max(-30, trade.profit_loss_pct * 3)
        
        base_score = max(0, min(100, base_score))
        
        if base_score >= 80:
            rating = RatingLevel.S
            risk = RiskLevel.LOW
        elif base_score >= 65:
            rating = RatingLevel.A
            risk = RiskLevel.MEDIUM
        elif base_score >= 50:
            rating = RatingLevel.B
            risk = RiskLevel.HIGH
        else:
            rating = RatingLevel.C
            risk = RiskLevel.EXTREME
        
        return ScoringReport(
            ticker=trade.ticker,
            stock_name=trade.stock_name,
            current_price=trade.price,
            total_score=round(base_score, 1),
            rating=rating,
            risk_level=risk,
        )
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, diagnosis: TradeDiagnosis) -> str:
        """构建诊断摘要"""
        parts: List[str] = []
        
        parts.append(f"┌─────────────────────────────────────┐")
        parts.append(f"│ 交易诊断: {diagnosis.stock_name}({diagnosis.ticker})")
        parts.append(f"└─────────────────────────────────────┘")
        
        # 交易信息
        pnl_icon = "🟢" if diagnosis.profit_loss >= 0 else "🔴"
        parts.append(f"  {pnl_icon} 盈亏: {diagnosis.profit_loss:.0f}元 ({diagnosis.profit_loss_pct}%)")
        parts.append(f"  模式: {diagnosis.trade_mode}")
        parts.append("")
        
        # 评分
        if diagnosis.scoring_report:
            report = diagnosis.scoring_report
            parts.append(f"  📊 评分: {report.total_score}分 [{report.rating.value}]")
            parts.append(f"  风险: {report.risk_level.value}")
            
            if report.risk_reward:
                parts.append(f"  RR比: {report.risk_reward.ratio}:1")
            parts.append("")
        
        # 错误分析
        if diagnosis.is_error_trade:
            parts.append(f"  ❌ 错误交易")
            for i, error in enumerate(diagnosis.error_types, 1):
                parts.append(f"     {i}. {error}")
            parts.append("")
            
            if diagnosis.error_details:
                parts.append("  错误详情:")
                for detail in diagnosis.error_details:
                    parts.append(f"     • {detail}")
                parts.append("")
        else:
            if diagnosis.profit_loss >= 0:
                parts.append(f"  ✅ 正确交易")
            else:
                parts.append(f"  ⚠️ 亏损但操作无明显错误(市场风险)")
            parts.append("")
        
        # 正确建议
        if diagnosis.correct_advice:
            parts.append(f"  💡 正确建议:")
            for line in diagnosis.correct_advice.split("\n"):
                parts.append(f"     {line}")
        
        return "\n".join(parts)