"""统一评分引擎 — 评分决策核心组件

整合所有维度评分器，为超短选手提供:
1. 多维度综合评分（7大维度加权）
2. 风险收益比评估
3. 操作建议生成（含仓位、入场、止损止盈）
4. 情绪化交易防范

评分引擎工作流程:
- 输入: 用户指定标的 + 多维度数据
- 处理: 各维度独立评分 → 加权汇总 → 风险收益比计算 → 操作建议生成
- 输出: 完整评分报告 + 可执行操作计划

核心原则:
- 客观量化，避免主观情绪
- 多维度交叉验证，提高准确性
- 风险优先，宁可错过不可做错
- 情绪周期适配，不同周期不同策略
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger

from .dimension_scorers import (
    DIMENSION_WEIGHTS,
    ChipStructureScorer,
    DimensionScore,
    DragonStatusScorer,
    EmotionCycleScorer,
    FundMatchScorer,
    NewsCatalystScorer,
    TechnicalScorer,
    ThemeStrengthScorer,
)

logger = get_logger("swat.m06.scoring_engine")


# ── 枚举定义 ─────────────────────────────────────────────

class RatingLevel(str, Enum):
    """评级等级"""
    S_PLUS = "S+级(顶级)"       # 90-100
    S = "S级(优质)"             # 80-89
    A = "A级(良好)"             # 70-79
    B = "B级(一般)"             # 60-69
    C = "C级(劣质)"             # 0-59


class ActionDecision(str, Enum):
    """操作决策"""
    STRONG_BUY = "强烈推荐买入"
    BUY = "推荐买入"
    CAUTIOUS_BUY = "谨慎买入"
    WAIT = "观望等待"
    AVOID = "坚决规避"
    SELL = "建议卖出"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    EXTREME = "极高风险"


# ── 数据类 ──────────────────────────────────────────────

@dataclass
class RiskRewardResult:
    """风险收益比结果"""
    ratio: float = 0.0                # 风险收益比
    entry_price: float = 0.0          # 入场价
    stop_loss_price: float = 0.0      # 止损价
    take_profit_price: float = 0.0    # 止盈价
    risk_pct: float = 0.0             # 风险空间(%)
    reward_pct: float = 0.0           # 收益空间(%)
    decision: str = ""                # 决策建议
    max_position_pct: float = 0.0     # 最大仓位(%)


@dataclass
class OperationAdvice:
    """操作建议"""
    action: ActionDecision = ActionDecision.WAIT
    position_pct: float = 0.0         # 建议仓位(%)
    entry_type: str = ""              # 入场方式(打板/低吸/半路/接力)
    entry_zone: str = ""              # 入场区间
    stop_loss: str = ""               # 止损策略
    take_profit: str = ""             # 止盈策略
    hold_conditions: List[str] = field(default_factory=list)
    sell_conditions: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    emotion_check: str = ""           # 情绪化交易检查


@dataclass
class ScoringReport:
    """完整评分报告"""
    timestamp: Optional[datetime] = None
    ticker: str = ""
    stock_name: str = ""
    current_price: float = 0.0
    
    # 综合评分
    total_score: float = 0.0
    rating: RatingLevel = RatingLevel.C
    risk_level: RiskLevel = RiskLevel.EXTREME
    
    # 维度评分
    dimension_scores: List[DimensionScore] = field(default_factory=list)
    strongest_dimension: str = ""     # 最强维度
    weakest_dimension: str = ""       # 最弱维度
    
    # 风险收益比
    risk_reward: Optional[RiskRewardResult] = None
    
    # 操作建议
    advice: Optional[OperationAdvice] = None
    
    # 完整摘要
    summary_text: str = ""


# ── 统一评分引擎 ─────────────────────────────────────────

class ScoringEngine:
    """统一评分引擎
    
    整合所有维度评分器，提供完整评分和操作建议。
    
    Attributes:
        config: 应用配置
        _scorers: 各维度评分器实例
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """初始化统一评分引擎
        
        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        
        # 初始化各维度评分器
        self.theme_scorer = ThemeStrengthScorer()
        self.fund_scorer = FundMatchScorer()
        self.emotion_scorer = EmotionCycleScorer()
        self.chip_scorer = ChipStructureScorer()
        self.technical_scorer = TechnicalScorer()
        self.dragon_scorer = DragonStatusScorer()
        self.news_scorer = NewsCatalystScorer()
        
        logger.info("统一评分引擎初始化完成")
    
    # ==================== 核心公共接口 ====================
    
    async def evaluate_stock(
        self,
        ticker: str,
        stock_name: str,
        current_price: float,
        theme_data: Optional[Dict] = None,
        fund_data: Optional[Dict] = None,
        emotion_data: Optional[Dict] = None,
        chip_data: Optional[Dict] = None,
        technical_data: Optional[Dict] = None,
        dragon_data: Optional[Dict] = None,
        news_data: Optional[Dict] = None,
        current_position: float = 0.0,
    ) -> ScoringReport:
        """评估标的 — 主入口
        
        Args:
            ticker: 股票代码
            stock_name: 股票名称
            current_price: 当前价格
            theme_data: 题材数据
            fund_data: 资金数据
            emotion_data: 情绪数据
            chip_data: 筹码数据
            technical_data: 技术数据
            dragon_data: 龙头数据
            news_data: 资讯数据
            current_position: 当前仓位(0-1)
            
        Returns:
            ScoringReport: 完整评分报告
            
        Raises:
            ModuleError: 评估过程发生错误
        """
        logger.info(f"========== 开始评估标的: {stock_name}({ticker}) ==========")
        
        try:
            # Step 1: 各维度评分
            logger.info("[Step 1/5] 执行维度评分...")
            dimension_scores = self._score_all_dimensions(
                theme_data or {},
                fund_data or {},
                emotion_data or {},
                chip_data or {},
                technical_data or {},
                dragon_data or {},
                news_data or {},
            )
            
            # Step 2: 计算综合评分
            logger.info("[Step 2/5] 计算综合评分...")
            total_score, rating, risk_level = self._calculate_total(dimension_scores)
            
            # Step 3: 计算风险收益比
            logger.info("[Step 3/5] 计算风险收益比...")
            risk_reward = self._calculate_risk_reward(
                current_price, rating, technical_data or {}
            )
            
            # Step 4: 生成操作建议
            logger.info("[Step 4/5] 生成操作建议...")
            advice = self._generate_advice(
                total_score, rating, risk_level, risk_reward,
                dimension_scores, emotion_data or {}, current_position
            )
            
            # Step 5: 编译报告
            logger.info("[Step 5/5] 编译评分报告...")
            report = self._compile_report(
                ticker, stock_name, current_price, total_score,
                rating, risk_level, dimension_scores, risk_reward, advice
            )
            
            logger.info(f"评估完成: {stock_name} = {total_score}分 [{rating.value}]")
            return report
            
        except Exception as e:
            logger.error(f"标的评估严重错误: {e}")
            raise ModuleError(f"标的评估失败: {e}")
    
    # ==================== 步骤1: 维度评分 ====================
    
    def _score_all_dimensions(
        self,
        theme_data: Dict,
        fund_data: Dict,
        emotion_data: Dict,
        chip_data: Dict,
        technical_data: Dict,
        dragon_data: Dict,
        news_data: Dict,
    ) -> List[DimensionScore]:
        """执行所有维度评分
        
        Returns:
            List[DimensionScore]: 维度评分列表
        """
        scores: List[DimensionScore] = []
        
        # 1. 题材强度 (20%)
        scores.append(self.theme_scorer.score(theme_data))
        
        # 2. 资金匹配 (18%)
        scores.append(self.fund_scorer.score(fund_data))
        
        # 3. 情绪周期 (17%)
        scores.append(self.emotion_scorer.score(emotion_data))
        
        # 4. 筹码结构 (12%)
        scores.append(self.chip_scorer.score(chip_data))
        
        # 5. 技术形态 (15%)
        scores.append(self.technical_scorer.score(technical_data))
        
        # 6. 龙头地位 (10%)
        scores.append(self.dragon_scorer.score(dragon_data))
        
        # 7. 资讯催化 (8%)
        scores.append(self.news_scorer.score(news_data))
        
        return scores
    
    # ==================== 步骤2: 综合评分 ====================
    
    def _calculate_total(
        self, 
        dimension_scores: List[DimensionScore]
    ) -> Tuple[float, RatingLevel, RiskLevel]:
        """计算综合评分
        
        Returns:
            Tuple: (总分, 评级, 风险等级)
        """
        # 加权求和
        total = sum(ds.weighted_score for ds in dimension_scores)
        total = round(max(0, min(100, total)), 1)
        
        # 确定评级
        if total >= 90:
            rating = RatingLevel.S_PLUS
            risk = RiskLevel.LOW
        elif total >= 80:
            rating = RatingLevel.S
            risk = RiskLevel.LOW
        elif total >= 70:
            rating = RatingLevel.A
            risk = RiskLevel.MEDIUM
        elif total >= 60:
            rating = RatingLevel.B
            risk = RiskLevel.HIGH
        else:
            rating = RatingLevel.C
            risk = RiskLevel.EXTREME
        
        # 维度一致性检查: 如果某个核心维度分数过低，降级
        core_dimensions = {"题材强度", "资金匹配", "情绪周期"}
        for ds in dimension_scores:
            if ds.dimension in core_dimensions and ds.score < 40:
                if rating in (RatingLevel.S_PLUS, RatingLevel.S):
                    rating = RatingLevel.A
                    risk = RiskLevel.MEDIUM
                break
        
        return total, rating, risk
    
    # ==================== 步骤3: 风险收益比 ====================
    
    def _calculate_risk_reward(
        self,
        current_price: float,
        rating: RatingLevel,
        technical_data: Dict,
    ) -> RiskRewardResult:
        """计算风险收益比
        
        Returns:
            RiskRewardResult: 风险收益比结果
        """
        # 根据评级确定止盈比例
        take_profit_pct_map = {
            RatingLevel.S_PLUS: 25,
            RatingLevel.S: 20,
            RatingLevel.A: 15,
            RatingLevel.B: 10,
            RatingLevel.C: 5,
        }
        take_profit_pct = take_profit_pct_map.get(rating, 10)
        
        # 止损比例
        stop_loss_pct_map = {
            RatingLevel.S_PLUS: 5,
            RatingLevel.S: 5,
            RatingLevel.A: 4,
            RatingLevel.B: 3,
            RatingLevel.C: 3,
        }
        stop_loss_pct = stop_loss_pct_map.get(rating, 4)
        
        # 技术支撑位作为更精确的止损
        support = technical_data.get("support_price")
        if support and support < current_price:
            stop_loss_price = round(support * 0.995, 2)
            stop_loss_pct = round((current_price - stop_loss_price) / current_price * 100, 1)
        else:
            stop_loss_price = round(current_price * (1 - stop_loss_pct / 100), 2)
        
        take_profit_price = round(current_price * (1 + take_profit_pct / 100), 2)
        
        # 计算风险收益比
        risk_space = current_price - stop_loss_price
        reward_space = take_profit_price - current_price
        
        if risk_space <= 0:
            risk_space = current_price * 0.04
        
        ratio = round(reward_space / risk_space, 2) if risk_space > 0 else 0
        
        # 决策
        if ratio >= 3.0:
            decision = "强烈推荐介入"
            max_position = 40
        elif ratio >= 2.0:
            decision = "推荐介入"
            max_position = 30
        elif ratio >= 1.5:
            decision = "谨慎介入"
            max_position = 20
        else:
            decision = "不建议介入"
            max_position = 0
        
        return RiskRewardResult(
            ratio=ratio,
            entry_price=round(current_price, 2),
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            risk_pct=round(stop_loss_pct, 1),
            reward_pct=round(take_profit_pct, 1),
            decision=decision,
            max_position_pct=max_position,
        )
    
    # ==================== 步骤4: 操作建议 ====================
    
    def _generate_advice(
        self,
        total_score: float,
        rating: RatingLevel,
        risk_level: RiskLevel,
        risk_reward: RiskRewardResult,
        dimension_scores: List[DimensionScore],
        emotion_data: Dict,
        current_position: float,
    ) -> OperationAdvice:
        """生成操作建议
        
        Returns:
            OperationAdvice: 操作建议
        """
        # 操作决策
        if total_score >= 85 and risk_reward.ratio >= 2.0:
            action = ActionDecision.STRONG_BUY
        elif total_score >= 75 and risk_reward.ratio >= 1.5:
            action = ActionDecision.BUY
        elif total_score >= 65:
            action = ActionDecision.CAUTIOUS_BUY
        elif total_score >= 50:
            action = ActionDecision.WAIT
        else:
            action = ActionDecision.AVOID
        
        # 如果已持仓，根据评分调整
        if current_position > 0:
            if total_score < 50:
                action = ActionDecision.SELL
            elif total_score < 65:
                action = ActionDecision.WAIT
        
        # 仓位建议
        position_pct = self._calculate_position(
            rating, risk_level, risk_reward, emotion_data, current_position
        )
        
        # 入场方式
        entry_type = self._determine_entry_type(emotion_data, dimension_scores)
        
        # 入场区间
        entry_zone = self._determine_entry_zone(entry_type, risk_reward)
        
        # 止损策略
        stop_loss = self._generate_stop_loss(risk_reward, dimension_scores)
        
        # 止盈策略
        take_profit = self._generate_take_profit(risk_reward, rating)
        
        # 持有条件
        hold_conditions = self._generate_hold_conditions(rating, dimension_scores)
        
        # 卖出条件
        sell_conditions = self._generate_sell_conditions(rating, risk_reward)
        
        # 风险提示
        risk_warnings = self._generate_risk_warnings(
            rating, risk_level, dimension_scores, emotion_data
        )
        
        # 情绪化交易检查
        emotion_check = self._emotion_trading_check(
            total_score, action, current_position, emotion_data
        )
        
        return OperationAdvice(
            action=action,
            position_pct=position_pct,
            entry_type=entry_type,
            entry_zone=entry_zone,
            stop_loss=stop_loss,
            take_profit=take_profit,
            hold_conditions=hold_conditions,
            sell_conditions=sell_conditions,
            risk_warnings=risk_warnings,
            emotion_check=emotion_check,
        )
    
    def _calculate_position(
        self,
        rating: RatingLevel,
        risk_level: RiskLevel,
        risk_reward: RiskRewardResult,
        emotion_data: Dict,
        current_position: float,
    ) -> float:
        """计算建议仓位
        
        Returns:
            float: 仓位百分比
        """
        # 基础仓位
        base_position_map = {
            RatingLevel.S_PLUS: 40,
            RatingLevel.S: 30,
            RatingLevel.A: 20,
            RatingLevel.B: 10,
            RatingLevel.C: 0,
        }
        base = base_position_map.get(rating, 10)
        
        # 风险等级调整
        risk_adjust_map = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 0.8,
            RiskLevel.HIGH: 0.5,
            RiskLevel.EXTREME: 0.2,
        }
        base *= risk_adjust_map.get(risk_level, 0.5)
        
        # 情绪周期调整
        current_cycle = emotion_data.get("current_cycle", "混沌")
        cycle_adjust_map = {
            "启动": 1.2,
            "发酵": 1.0,
            "高潮": 0.7,
            "分歧": 0.6,
            "退潮": 0.2,
            "混沌": 0.5,
        }
        base *= cycle_adjust_map.get(current_cycle, 0.5)
        
        # RR比调整
        if risk_reward.ratio >= 3.0:
            base *= 1.2
        elif risk_reward.ratio < 1.5:
            base *= 0.5
        
        # 最终仓位
        position = min(base, risk_reward.max_position_pct)
        position = max(0, min(50, round(position, 1)))
        
        return position
    
    def _determine_entry_type(
        self, 
        emotion_data: Dict, 
        dimension_scores: List[DimensionScore]
    ) -> str:
        """确定入场方式"""
        current_cycle = emotion_data.get("current_cycle", "混沌")
        
        # 根据情绪周期
        if current_cycle in ("启动", "发酵"):
            return "打板"
        elif current_cycle == "分歧":
            return "低吸"
        elif current_cycle == "高潮":
            return "半路"
        else:
            return "等待确认"
    
    def _determine_entry_zone(
        self, 
        entry_type: str, 
        risk_reward: RiskRewardResult
    ) -> str:
        """确定入场区间"""
        if entry_type == "打板":
            return f"涨停价{risk_reward.entry_price * 1.1:.2f}附近排队"
        elif entry_type == "低吸":
            return f"分时均线下方{risk_reward.entry_price * 0.97:.2f}-{risk_reward.entry_price * 0.95:.2f}"
        elif entry_type == "半路":
            return f"涨幅3-5%区间{risk_reward.entry_price * 1.03:.2f}-{risk_reward.entry_price * 1.05:.2f}"
        else:
            return f"等待明确信号，参考{risk_reward.entry_price:.2f}附近"
    
    def _generate_stop_loss(
        self, 
        risk_reward: RiskRewardResult, 
        dimension_scores: List[DimensionScore]
    ) -> str:
        """生成止损策略"""
        parts = [f"固定止损: {risk_reward.stop_loss_price:.2f}(-{risk_reward.risk_pct}%)"]
        
        # 逻辑止损
        parts.append("逻辑止损: 题材证伪/龙头跌停/板块崩溃 → 无条件卖出")
        
        # 技术止损
        parts.append("技术止损: 跌破5日线或关键支撑位且当日无法收回 → 卖出")
        
        return " | ".join(parts)
    
    def _generate_take_profit(
        self, 
        risk_reward: RiskRewardResult, 
        rating: RatingLevel
    ) -> str:
        """生成止盈策略"""
        parts = [f"目标止盈: {risk_reward.take_profit_price:.2f}(+{risk_reward.reward_pct}%)"]
        
        if rating in (RatingLevel.S_PLUS, RatingLevel.S):
            parts.append("分批止盈: 盈利10%减仓50%，盈利20%清仓")
        else:
            parts.append("分批止盈: 盈利5%减仓50%，盈利10%清仓")
        
        parts.append("动态止盈: 股价远离5日线>3%或放量滞涨 → 减仓")
        parts.append("情绪止盈: 市场情绪退潮/炸板率>50% → 全部卖出")
        
        return " | ".join(parts)
    
    def _generate_hold_conditions(
        self, 
        rating: RatingLevel, 
        dimension_scores: List[DimensionScore]
    ) -> List[str]:
        """生成持有条件"""
        conditions = [
            "股价沿5日线上涨，均线多头排列",
            "量能健康（缩量上涨或放量突破）",
            "板块效应持续（涨停≥3只）",
            "所属题材处于主升或发酵阶段",
        ]
        
        if rating in (RatingLevel.S_PLUS, RatingLevel.S):
            conditions.append("资金面持续流入，龙头地位稳固")
        
        return conditions
    
    def _generate_sell_conditions(
        self, 
        rating: RatingLevel, 
        risk_reward: RiskRewardResult
    ) -> List[str]:
        """生成卖出条件"""
        conditions = [
            f"【固定止损】亏损达{risk_reward.risk_pct}% → 严格执行",
            f"【目标止盈】达到{risk_reward.reward_pct}% → 分批卖出",
            "【逻辑止损】题材证伪/龙头跌停/板块崩溃 → 无条件卖出",
            "【技术止损】跌破5日线或关键支撑 → 卖出",
            "【动态止盈】放量滞涨/长上影 → 减仓",
            "【情绪止盈】情绪退潮/炸板率>50% → 清仓",
        ]
        return conditions
    
    def _generate_risk_warnings(
        self,
        rating: RatingLevel,
        risk_level: RiskLevel,
        dimension_scores: List[DimensionScore],
        emotion_data: Dict,
    ) -> List[str]:
        """生成风险提示"""
        warnings: List[str] = []
        
        # 风险等级提示
        if risk_level == RiskLevel.EXTREME:
            warnings.append("⚠️ 极高风险，强烈建议规避")
        elif risk_level == RiskLevel.HIGH:
            warnings.append("⚠️ 高风险，严格控制仓位")
        
        # 维度短板提示
        for ds in dimension_scores:
            if ds.score < 40:
                warnings.append(f"⚠️ {ds.dimension}评分过低({ds.score}分)，存在明显短板")
        
        # 情绪周期提示
        current_cycle = emotion_data.get("current_cycle", "混沌")
        if current_cycle == "退潮":
            warnings.append("⚠️ 退潮期，整体风险偏高，管住手")
        elif current_cycle == "高潮":
            warnings.append("⚠️ 高潮期，注意次日分化风险")
        
        return warnings
    
    def _emotion_trading_check(
        self,
        total_score: float,
        action: ActionDecision,
        current_position: float,
        emotion_data: Dict,
    ) -> str:
        """情绪化交易检查
        
        检测并提醒可能的情绪化交易行为。
        """
        checks: List[str] = []
        
        # FOMO检查: 评分低但想买入
        if total_score < 60 and action in (ActionDecision.STRONG_BUY, ActionDecision.BUY):
            checks.append("⚠️ 评分偏低却想买入，可能是FOMO情绪，请冷静")
        
        # 报复性交易检查: 已亏损还想加仓
        if current_position > 0.3 and action == ActionDecision.STRONG_BUY:
            checks.append("⚠️ 仓位已重还想加仓，可能是报复性交易，请控制")
        
        # 恐慌性卖出检查
        current_cycle = emotion_data.get("current_cycle", "混沌")
        if current_cycle == "退潮" and total_score >= 70:
            checks.append("提示: 退潮期但标的评分尚可，不必恐慌性卖出")
        
        # 过度自信检查
        if total_score >= 85 and current_position > 0.5:
            checks.append("提示: 标的虽好但仓位过重，注意分散风险")
        
        if not checks:
            return "✅ 无明显情绪化交易倾向，操作理性"
        
        return "\n".join(checks)
    
    # ==================== 步骤5: 编译报告 ====================
    
    def _compile_report(
        self,
        ticker: str,
        stock_name: str,
        current_price: float,
        total_score: float,
        rating: RatingLevel,
        risk_level: RiskLevel,
        dimension_scores: List[DimensionScore],
        risk_reward: RiskRewardResult,
        advice: OperationAdvice,
    ) -> ScoringReport:
        """编译完整评分报告"""
        now = datetime.now()
        
        # 最强/最弱维度
        strongest = max(dimension_scores, key=lambda ds: ds.score)
        weakest = min(dimension_scores, key=lambda ds: ds.score)
        
        # 生成摘要
        summary = self._build_summary(
            ticker, stock_name, current_price, total_score, rating,
            risk_level, dimension_scores, risk_reward, advice
        )
        
        return ScoringReport(
            timestamp=now,
            ticker=ticker,
            stock_name=stock_name,
            current_price=current_price,
            total_score=total_score,
            rating=rating,
            risk_level=risk_level,
            dimension_scores=dimension_scores,
            strongest_dimension=strongest.dimension,
            weakest_dimension=weakest.dimension,
            risk_reward=risk_reward,
            advice=advice,
            summary_text=summary,
        )
    
    def _build_summary(
        self,
        ticker: str,
        stock_name: str,
        current_price: float,
        total_score: float,
        rating: RatingLevel,
        risk_level: RiskLevel,
        dimension_scores: List[DimensionScore],
        risk_reward: RiskRewardResult,
        advice: OperationAdvice,
    ) -> str:
        """构建报告摘要"""
        now = datetime.now()
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║   标的评分报告 [{now.strftime('%H:%M:%S')}]                  ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        # 基本信息
        parts.append(f"📌 {stock_name}({ticker})")
        parts.append(f"   当前价: {current_price:.2f}元")
        parts.append(f"   综合评分: {total_score}分 [{rating.value}]")
        parts.append(f"   风险等级: {risk_level.value}")
        parts.append("")
        
        # 维度评分
        parts.append("📊 维度评分:")
        for ds in dimension_scores:
            bar = "█" * int(ds.score / 5) + "░" * (20 - int(ds.score / 5))
            parts.append(f"   {ds.dimension}: {bar} {ds.score}分 (权重{ds.weight:.0%})")
        parts.append("")
        
        # 风险收益比
        parts.append(f"⚖️ 风险收益比: {risk_reward.ratio}:1")
        parts.append(f"   入场: {risk_reward.entry_price:.2f} | 止损: {risk_reward.stop_loss_price:.2f}(-{risk_reward.risk_pct}%) | 止盈: {risk_reward.take_profit_price:.2f}(+{risk_reward.reward_pct}%)")
        parts.append(f"   RR决策: {risk_reward.decision}")
        parts.append("")
        
        # 操作建议
        parts.append(f"🎯 操作建议: {advice.action.value}")
        parts.append(f"   仓位: {advice.position_pct}% | 方式: {advice.entry_type}")
        parts.append(f"   入场区间: {advice.entry_zone}")
        parts.append("")
        
        # 风险提示
        if advice.risk_warnings:
            parts.append("⚠️ 风险提示:")
            for w in advice.risk_warnings:
                parts.append(f"   {w}")
            parts.append("")
        
        # 情绪化交易检查
        parts.append(f"🧠 情绪检查: {advice.emotion_check}")
        
        return "\n".join(parts)