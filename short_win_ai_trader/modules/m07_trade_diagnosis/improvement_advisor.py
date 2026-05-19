"""改进建议生成器

根据交易诊断结果生成针对性改进意见:
- 基于高频错误类型生成改进建议
- 基于交易画像优劣势生成提升方案
- 基于错误交易诊断生成纠正措施
- 生成可执行的改进行动计划
- 提供学习资源和训练方法
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ...core.logger import get_logger
from .error_attribution import AttributionResult, ErrorPattern, ErrorType
from .importer import TradeRecord
from .profiler import TradeProfile
from .trade_diagnoser import TradeDiagnosis

logger = get_logger("swat.m07.improvement_advisor")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class ImprovementAction:
    """改进行动"""
    priority: int = 0                     # 优先级(1-5, 1最高)
    category: str = ""                    # 类别(选股/择时/仓位/止损/心态)
    action: str = ""                      # 具体行动
    reason: str = ""                      # 原因
    method: str = ""                      # 执行方法
    target: str = ""                      # 目标
    timeline: str = ""                    # 时间线


@dataclass
class ImprovementPlan:
    """改进计划"""
    # 总体评估
    overall_assessment: str = ""          # 总体评估
    current_level: str = ""               # 当前水平(新手/初级/中级/高级)
    
    # 改进优先级
    top_priorities: List[str] = field(default_factory=list)  # Top改进项
    
    # 改进行动
    actions: List[ImprovementAction] = field(default_factory=list)
    
    # 分类建议
    stock_selection_advice: str = ""      # 选股建议
    timing_advice: str = ""               # 择时建议
    position_advice: str = ""             # 仓位建议
    stop_loss_advice: str = ""            # 止损建议
    mindset_advice: str = ""              # 心态建议
    
    # 学习资源
    learning_resources: List[str] = field(default_factory=list)
    
    # 计划摘要
    summary: str = ""


# ── 改进建议生成器 ───────────────────────────────────────

class ImprovementAdvisor:
    """改进建议生成器
    
    根据诊断结果生成针对性改进意见。
    """
    
    # 错误类型对应的改进类别
    ERROR_CATEGORY_MAP = {
        ErrorType.WRONG_STOCK: "选股",
        ErrorType.FOLLOW_WEAK: "选股",
        ErrorType.HIGH_CHASE: "选股",
        ErrorType.WRONG_TIMING: "择时",
        ErrorType.RETREAT_BUY: "择时",
        ErrorType.CLIMAX_CHASE: "择时",
        ErrorType.WRONG_MODE: "模式",
        ErrorType.MODE_MISMATCH: "模式",
        ErrorType.OVER_POSITION: "仓位",
        ErrorType.UNDER_POSITION: "仓位",
        ErrorType.NO_STOP_LOSS: "止损",
        ErrorType.LATE_STOP_LOSS: "止损",
        ErrorType.EARLY_STOP_LOSS: "止损",
        ErrorType.NO_TAKE_PROFIT: "止盈",
        ErrorType.EARLY_TAKE_PROFIT: "止盈",
        ErrorType.ROUND_TRIP: "止盈",
        ErrorType.FOMO: "心态",
        ErrorType.REVENGE_TRADE: "心态",
        ErrorType.PANIC_SELL: "心态",
        ErrorType.OVER_CONFIDENCE: "心态",
        ErrorType.ANCHORING: "心态",
        ErrorType.CONFIRMATION_BIAS: "心态",
    }
    
    def __init__(self):
        """初始化改进建议生成器"""
        logger.info("改进建议生成器初始化完成")
    
    def generate_plan(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        diagnoses: List[TradeDiagnosis],
    ) -> ImprovementPlan:
        """生成改进计划
        
        Args:
            profile: 交易画像
            attribution: 错误归因结果
            diagnoses: 交易诊断列表
            
        Returns:
            ImprovementPlan: 改进计划
        """
        logger.info("开始生成改进计划")
        
        plan = ImprovementPlan()
        
        # 总体评估
        self._assess_overall(profile, attribution, plan)
        
        # 改进优先级
        self._identify_priorities(profile, attribution, plan)
        
        # 改进行动
        self._generate_actions(profile, attribution, diagnoses, plan)
        
        # 分类建议
        self._generate_category_advice(profile, attribution, plan)
        
        # 学习资源
        self._recommend_resources(profile, plan)
        
        # 生成摘要
        plan.summary = self._build_summary(plan)
        
        logger.info(f"改进计划生成完成: {len(plan.actions)}项行动")
        return plan
    
    # ==================== 总体评估 ====================
    
    def _assess_overall(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        plan: ImprovementPlan,
    ):
        """总体评估"""
        score = profile.overall_score
        
        if score >= 80:
            plan.current_level = "高级"
            plan.overall_assessment = "交易水平较高，主要需优化细节和保持一致性"
        elif score >= 65:
            plan.current_level = "中级"
            plan.overall_assessment = "具备一定交易能力，但存在明显短板需要改进"
        elif score >= 50:
            plan.current_level = "初级"
            plan.overall_assessment = "交易基础薄弱，需要系统性学习和训练"
        else:
            plan.current_level = "新手"
            plan.overall_assessment = "交易能力不足，建议暂停实盘，先进行模拟训练"
    
    # ==================== 改进优先级 ====================
    
    def _identify_priorities(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        plan: ImprovementPlan,
    ):
        """识别改进优先级"""
        priorities: List[str] = []
        
        # 基于高频错误
        for pattern in attribution.high_frequency_errors[:3]:
            priorities.append(f"【{pattern.severity.value}】{pattern.error_type.value}: {pattern.improvement}")
        
        # 基于画像劣势
        for weakness in profile.weaknesses[:2]:
            priorities.append(f"【画像】{weakness}")
        
        plan.top_priorities = priorities
    
    # ==================== 改进行动 ====================
    
    def _generate_actions(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        diagnoses: List[TradeDiagnosis],
        plan: ImprovementPlan,
    ):
        """生成改进行动"""
        actions: List[ImprovementAction] = []
        
        # 基于错误归因生成行动
        for pattern in attribution.top_errors:
            category = self.ERROR_CATEGORY_MAP.get(pattern.error_type, "其他")
            
            action = ImprovementAction(
                priority=self._calc_priority(pattern),
                category=category,
                action=pattern.improvement,
                reason=pattern.description,
                method=self._get_method(pattern.error_type),
                target=self._get_target(pattern.error_type),
                timeline=self._get_timeline(pattern.severity),
            )
            actions.append(action)
        
        # 基于画像劣势生成行动
        for weakness in profile.weaknesses:
            action = ImprovementAction(
                priority=3,
                category="综合",
                action=weakness,
                reason="交易画像分析发现",
                method="系统性学习和刻意练习",
                target="改善交易表现",
                timeline="1-3个月",
            )
            actions.append(action)
        
        # 按优先级排序
        actions.sort(key=lambda a: a.priority)
        plan.actions = actions
    
    def _calc_priority(self, pattern: ErrorPattern) -> int:
        """计算优先级"""
        severity_map = {
            "严重": 1,
            "较高": 2,
            "中等": 3,
            "轻微": 4,
        }
        return severity_map.get(pattern.severity.value, 5)
    
    def _get_method(self, error_type: ErrorType) -> str:
        """获取执行方法"""
        methods = {
            ErrorType.WRONG_STOCK: "建立选股清单，只做评分>70分的标的",
            ErrorType.FOLLOW_WEAK: "坚持只做板块前3龙头，不碰跟风股",
            ErrorType.HIGH_CHASE: "设定追高限制：涨幅>7%不追",
            ErrorType.WRONG_TIMING: "学习情绪周期，只在启动/发酵期操作",
            ErrorType.RETREAT_BUY: "退潮期强制空仓，等待冰点信号",
            ErrorType.CLIMAX_CHASE: "高潮期不追涨，等次日分歧低吸",
            ErrorType.WRONG_MODE: "明确各模式适用场景，建立模式选择流程",
            ErrorType.MODE_MISMATCH: "交易前确认模式与场景匹配",
            ErrorType.OVER_POSITION: "单票仓位上限30%，总仓位上限80%",
            ErrorType.UNDER_POSITION: "高确定性标的(评分>80)仓位不低于20%",
            ErrorType.NO_STOP_LOSS: "设定硬性止损：-5%无条件卖出",
            ErrorType.LATE_STOP_LOSS: "使用条件单自动止损",
            ErrorType.EARLY_STOP_LOSS: "优化止损位，参考支撑位设置",
            ErrorType.NO_TAKE_PROFIT: "设定目标止盈：+15%开始分批卖出",
            ErrorType.EARLY_TAKE_PROFIT: "趋势未破不卖，使用移动止盈",
            ErrorType.ROUND_TRIP: "盈利后设置移动止损保护利润",
            ErrorType.FOMO: "建立冷静期：想追高时等15分钟",
            ErrorType.REVENGE_TRADE: "亏损后强制休息30分钟",
            ErrorType.PANIC_SELL: "按交易计划执行，不临时决策",
            ErrorType.OVER_CONFIDENCE: "连胜后降低仓位，保持敬畏",
            ErrorType.ANCHORING: "忘掉成本，只看当前市场状态",
            ErrorType.CONFIRMATION_BIAS: "交易前主动寻找3个风险点",
        }
        return methods.get(error_type, "刻意练习")
    
    def _get_target(self, error_type: ErrorType) -> str:
        """获取目标"""
        targets = {
            ErrorType.WRONG_STOCK: "选股胜率提升至50%以上",
            ErrorType.FOLLOW_WEAK: "杜绝跟风股交易",
            ErrorType.HIGH_CHASE: "高位接盘亏损减少80%",
            ErrorType.WRONG_TIMING: "择时胜率提升至55%以上",
            ErrorType.RETREAT_BUY: "退潮期零交易",
            ErrorType.CLIMAX_CHASE: "高潮期追涨亏损减少70%",
            ErrorType.WRONG_MODE: "模式匹配度提升至90%",
            ErrorType.MODE_MISMATCH: "杜绝模式错用",
            ErrorType.OVER_POSITION: "单笔最大亏损控制在总资金3%以内",
            ErrorType.UNDER_POSITION: "高确定性标的盈利贡献提升50%",
            ErrorType.NO_STOP_LOSS: "100%执行止损",
            ErrorType.LATE_STOP_LOSS: "止损执行延迟降至0",
            ErrorType.EARLY_STOP_LOSS: "止损后被拉起比例降至20%以下",
            ErrorType.NO_TAKE_PROFIT: "盈利回吐比例降至30%以下",
            ErrorType.EARLY_TAKE_PROFIT: "卖飞比例降至20%以下",
            ErrorType.ROUND_TRIP: "杜绝盈利变亏损",
            ErrorType.FOMO: "FOMO交易降至0",
            ErrorType.REVENGE_TRADE: "报复性交易降至0",
            ErrorType.PANIC_SELL: "恐慌性卖出降至0",
            ErrorType.OVER_CONFIDENCE: "连胜后回撤控制在5%以内",
            ErrorType.ANCHORING: "止损执行率提升至100%",
            ErrorType.CONFIRMATION_BIAS: "每笔交易前完成风险评估",
        }
        return targets.get(error_type, "改善交易表现")
    
    def _get_timeline(self, severity) -> str:
        """获取时间线"""
        timeline_map = {
            "严重": "立即执行，1周内见效",
            "较高": "本周开始，2周内见效",
            "中等": "本月开始，1个月内见效",
            "轻微": "持续改进，3个月内见效",
        }
        return timeline_map.get(severity.value if hasattr(severity, 'value') else str(severity), "持续改进")
    
    # ==================== 分类建议 ====================
    
    def _generate_category_advice(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        plan: ImprovementPlan,
    ):
        """生成分类建议"""
        # 选股建议
        stock_errors = [p for p in attribution.error_patterns 
                       if self.ERROR_CATEGORY_MAP.get(p.error_type) == "选股"]
        if stock_errors:
            plan.stock_selection_advice = (
                f"选股方面存在{len(stock_errors)}类错误，总亏损{abs(sum(p.total_loss for p in stock_errors)):.0f}元。\n"
                f"建议:\n"
                f"  1. 建立选股评分体系，只做评分>70分的标的\n"
                f"  2. 坚持做龙头/先锋，不碰跟风股\n"
                f"  3. 关注板块效应，选择有板块支撑的标的\n"
                f"  4. 避免高位接盘，控制追高幅度"
            )
        else:
            plan.stock_selection_advice = "选股方面表现良好，继续保持"
        
        # 择时建议
        timing_errors = [p for p in attribution.error_patterns 
                        if self.ERROR_CATEGORY_MAP.get(p.error_type) == "择时"]
        if timing_errors:
            plan.timing_advice = (
                f"择时方面存在{len(timing_errors)}类错误，总亏损{abs(sum(p.total_loss for p in timing_errors)):.0f}元。\n"
                f"建议:\n"
                f"  1. 学习情绪周期判断，在启动/发酵期操作\n"
                f"  2. 退潮期管住手，等待冰点信号\n"
                f"  3. 高潮期不追涨，等次日分歧机会\n"
                f"  4. 关注市场赚钱效应，顺势而为"
            )
        else:
            plan.timing_advice = "择时方面表现良好，继续保持"
        
        # 仓位建议
        position_errors = [p for p in attribution.error_patterns 
                          if self.ERROR_CATEGORY_MAP.get(p.error_type) == "仓位"]
        if position_errors:
            plan.position_advice = (
                f"仓位管理方面存在{len(position_errors)}类错误。\n"
                f"建议:\n"
                f"  1. 单票仓位不超过30%，总仓位不超过80%\n"
                f"  2. 高确定性标的(评分>80)可上20-30%仓位\n"
                f"  3. 中等确定性标的(评分70-80)仓位10-20%\n"
                f"  4. 低确定性标的(评分<70)不超过10%或不做\n"
                f"  5. 退潮期仓位控制在30%以下"
            )
        else:
            plan.position_advice = "仓位管理方面表现良好，继续保持"
        
        # 止损建议
        stop_errors = [p for p in attribution.error_patterns 
                      if self.ERROR_CATEGORY_MAP.get(p.error_type) in ("止损", "止盈")]
        if stop_errors:
            plan.stop_loss_advice = (
                f"止损止盈方面存在{len(stop_errors)}类错误，总亏损{abs(sum(p.total_loss for p in stop_errors)):.0f}元。\n"
                f"建议:\n"
                f"  1. 硬性止损：-5%无条件卖出，使用条件单\n"
                f"  2. 移动止损：盈利后设置移动止损保护利润\n"
                f"  3. 目标止盈：+15%开始分批卖出\n"
                f"  4. 趋势止盈：趋势破位(跌破5日线)全部卖出\n"
                f"  5. 杜绝盈利变亏损，盈利5%后止损上移至成本价"
            )
        else:
            plan.stop_loss_advice = "止损止盈方面表现良好，继续保持"
        
        # 心态建议
        mindset_errors = [p for p in attribution.error_patterns 
                         if self.ERROR_CATEGORY_MAP.get(p.error_type) == "心态"]
        if mindset_errors:
            plan.mindset_advice = (
                f"交易心态方面存在{len(mindset_errors)}类错误。\n"
                f"建议:\n"
                f"  1. 克服FOMO：宁可错过不可做错，建立15分钟冷静期\n"
                f"  2. 避免报复性交易：亏损后强制休息30分钟\n"
                f"  3. 避免恐慌性卖出：按交易计划执行，不临时决策\n"
                f"  4. 保持敬畏之心：连胜后更要谨慎，降低仓位\n"
                f"  5. 忘掉成本价：只看当前市场状态做决策\n"
                f"  6. 主动寻找风险：交易前找出3个风险点"
            )
        else:
            plan.mindset_advice = "交易心态方面表现良好，继续保持"
    
    # ==================== 学习资源 ====================
    
    def _recommend_resources(self, profile: TradeProfile, plan: ImprovementPlan):
        """推荐学习资源"""
        resources: List[str] = []
        
        # 根据水平推荐
        if plan.current_level in ("新手", "初级"):
            resources.extend([
                "📚 《股票大作手回忆录》- 理解市场心理",
                "📚 《日本蜡烛图技术》- K线基础",
                "📺 超短基础课程: 情绪周期/龙头战法/仓位管理",
            ])
        elif plan.current_level == "中级":
            resources.extend([
                "📚 《交易心理分析》- 克服心理障碍",
                "📚 《海龟交易法则》- 系统化交易",
                "📺 进阶课程: 筹码分析/资金流向/板块轮动",
            ])
        else:
            resources.extend([
                "📚 《金融炼金术》- 反身性理论",
                "📚 《通向财务自由之路》- 交易系统构建",
                "📺 高级研讨: 市场微观结构/量化辅助",
            ])
        
        # 根据错误类型推荐
        has_position_error = any(
            self.ERROR_CATEGORY_MAP.get(p.error_type) == "仓位" 
            for p in plan.actions
        )
        if has_position_error:
            resources.append("📺 专项训练: 仓位管理系统")
        
        has_mindset_error = any(
            self.ERROR_CATEGORY_MAP.get(p.error_type) == "心态" 
            for p in plan.actions
        )
        if has_mindset_error:
            resources.append("📺 专项训练: 交易心理建设")
        
        plan.learning_resources = resources
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, plan: ImprovementPlan) -> str:
        """构建摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║         改进建议与训练计划            ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        parts.append(f"📊 总体评估:")
        parts.append(f"   当前水平: {plan.current_level}")
        parts.append(f"   评估: {plan.overall_assessment}")
        parts.append("")
        
        if plan.top_priorities:
            parts.append("🎯 改进优先级:")
            for i, priority in enumerate(plan.top_priorities, 1):
                parts.append(f"   {i}. {priority}")
            parts.append("")
        
        if plan.actions:
            parts.append("📋 改进行动计划:")
            for action in plan.actions[:5]:
                parts.append(f"   【优先级{action.priority}】{action.category}")
                parts.append(f"      行动: {action.action}")
                parts.append(f"      方法: {action.method}")
                parts.append(f"      目标: {action.target}")
                parts.append(f"      时间: {action.timeline}")
                parts.append("")
        
        if plan.learning_resources:
            parts.append("📚 推荐学习资源:")
            for resource in plan.learning_resources:
                parts.append(f"   {resource}")
        
        return "\n".join(parts)