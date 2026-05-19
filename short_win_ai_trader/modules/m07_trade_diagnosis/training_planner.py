"""模拟训练计划生成器

根据交易诊断结果生成个性化模拟训练计划:
- 基于高频错误类型设计专项训练
- 基于交易水平设计训练难度
- 基于交易风格设计训练场景
- 提供循序渐进的训练路径
- 包含训练目标和评估标准

训练类型:
- 选股训练: 练习识别龙头/先锋/跟风
- 择时训练: 练习情绪周期判断
- 仓位训练: 练习仓位分配
- 止损训练: 练习止损执行
- 心态训练: 练习克服情绪化交易
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ...core.logger import get_logger
from .error_attribution import AttributionResult, ErrorPattern, ErrorType
from .improvement_advisor import ImprovementPlan
from .profiler import TradeProfile

logger = get_logger("swat.m07.training_planner")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class TrainingTask:
    """训练任务"""
    task_id: str = ""                     # 任务ID
    week: int = 0                         # 第几周
    category: str = ""                    # 类别(选股/择时/仓位/止损/心态)
    title: str = ""                       # 任务标题
    description: str = ""                 # 任务描述
    method: str = ""                      # 训练方法
    duration: str = ""                    # 训练时长
    target: str = ""                      # 训练目标
    evaluation: str = ""                  # 评估标准
    difficulty: str = ""                  # 难度(简单/中等/困难)


@dataclass
class TrainingWeek:
    """训练周计划"""
    week: int = 0                         # 第几周
    theme: str = ""                       # 周主题
    tasks: List[TrainingTask] = field(default_factory=list)
    review: str = ""                      # 周复盘要点


@dataclass
class TrainingPlan:
    """训练计划"""
    # 基本信息
    total_weeks: int = 0                  # 总周数
    current_level: str = ""               # 当前水平
    target_level: str = ""                # 目标水平
    
    # 训练重点
    focus_areas: List[str] = field(default_factory=list)  # 重点领域
    
    # 周计划
    weekly_plans: List[TrainingWeek] = field(default_factory=list)
    
    # 训练场景
    training_scenarios: List[str] = field(default_factory=list)
    
    # 评估标准
    evaluation_criteria: List[str] = field(default_factory=list)
    
    # 计划摘要
    summary: str = ""


# ── 训练计划生成器 ───────────────────────────────────────

class TrainingPlanner:
    """模拟训练计划生成器
    
    根据诊断结果生成个性化训练计划。
    """
    
    # 错误类型对应的训练类别
    ERROR_TRAINING_MAP = {
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
        """初始化训练计划生成器"""
        logger.info("训练计划生成器初始化完成")
    
    def generate_plan(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        improvement: ImprovementPlan,
    ) -> TrainingPlan:
        """生成训练计划
        
        Args:
            profile: 交易画像
            attribution: 错误归因结果
            improvement: 改进计划
            
        Returns:
            TrainingPlan: 训练计划
        """
        logger.info("开始生成训练计划")
        
        plan = TrainingPlan()
        
        # 基本信息
        plan.current_level = improvement.current_level
        plan.target_level = self._get_target_level(improvement.current_level)
        plan.total_weeks = self._calc_total_weeks(improvement.current_level)
        
        # 训练重点
        self._identify_focus_areas(attribution, improvement, plan)
        
        # 周计划
        self._generate_weekly_plans(profile, attribution, improvement, plan)
        
        # 训练场景
        self._generate_scenarios(profile, plan)
        
        # 评估标准
        self._generate_evaluation_criteria(plan)
        
        # 生成摘要
        plan.summary = self._build_summary(plan)
        
        logger.info(f"训练计划生成完成: {plan.total_weeks}周, {len(plan.weekly_plans)}个周计划")
        return plan
    
    # ==================== 基本信息 ====================
    
    def _get_target_level(self, current_level: str) -> str:
        """获取目标水平"""
        level_map = {
            "新手": "初级",
            "初级": "中级",
            "中级": "高级",
            "高级": "大师",
        }
        return level_map.get(current_level, "中级")
    
    def _calc_total_weeks(self, current_level: str) -> int:
        """计算总周数"""
        weeks_map = {
            "新手": 12,
            "初级": 8,
            "中级": 6,
            "高级": 4,
        }
        return weeks_map.get(current_level, 8)
    
    # ==================== 训练重点 ====================
    
    def _identify_focus_areas(
        self,
        attribution: AttributionResult,
        improvement: ImprovementPlan,
        plan: TrainingPlan,
    ):
        """识别训练重点领域"""
        # 统计各类错误频率
        category_errors: Dict[str, int] = {}
        for pattern in attribution.error_patterns:
            category = self.ERROR_TRAINING_MAP.get(pattern.error_type, "其他")
            category_errors[category] = category_errors.get(category, 0) + pattern.frequency
        
        # 按频率排序
        sorted_categories = sorted(category_errors.items(), key=lambda x: x[1], reverse=True)
        
        # Top3为重点
        plan.focus_areas = [cat for cat, _ in sorted_categories[:3]]
        
        # 如果没有错误，使用默认重点
        if not plan.focus_areas:
            plan.focus_areas = ["选股", "择时", "仓位"]
    
    # ==================== 周计划 ====================
    
    def _generate_weekly_plans(
        self,
        profile: TradeProfile,
        attribution: AttributionResult,
        improvement: ImprovementPlan,
        plan: TrainingPlan,
    ):
        """生成周计划"""
        total_weeks = plan.total_weeks
        
        # 根据水平确定训练阶段
        if plan.current_level in ("新手", "初级"):
            # 基础阶段: 选股→择时→仓位→止损→心态
            phases = [
                ("选股基础", "选股", 2),
                ("择时基础", "择时", 2),
                ("仓位管理", "仓位", 1),
                ("止损纪律", "止损", 1),
                ("心态建设", "心态", 1),
                ("综合训练", "综合", 1),
            ]
        elif plan.current_level == "中级":
            # 进阶阶段: 重点突破
            phases = [
                (f"{plan.focus_areas[0]}突破", plan.focus_areas[0], 2),
                (f"{plan.focus_areas[1] if len(plan.focus_areas) > 1 else '择时'}突破", 
                 plan.focus_areas[1] if len(plan.focus_areas) > 1 else "择时", 2),
                ("综合提升", "综合", 2),
            ]
        else:
            # 高级阶段: 精细化
            phases = [
                ("细节优化", "综合", 2),
                ("一致性训练", "综合", 2),
            ]
        
        week_num = 0
        for phase_name, category, weeks in phases:
            if week_num >= total_weeks:
                break
            
            for w in range(weeks):
                if week_num >= total_weeks:
                    break
                
                week_num += 1
                week_plan = TrainingWeek(
                    week=week_num,
                    theme=f"第{week_num}周: {phase_name}",
                )
                
                # 生成周任务
                self._generate_week_tasks(week_num, category, profile, week_plan)
                
                # 周复盘
                week_plan.review = self._get_week_review(category, week_num)
                
                plan.weekly_plans.append(week_plan)
    
    def _generate_week_tasks(
        self,
        week: int,
        category: str,
        profile: TradeProfile,
        week_plan: TrainingWeek,
    ):
        """生成周任务"""
        task_templates = {
            "选股": [
                {
                    "title": "龙头识别训练",
                    "description": "每日复盘识别板块龙头，记录龙头特征",
                    "method": "查看当日涨停股，分析板块效应，识别龙头/先锋/跟风",
                    "duration": "每日30分钟",
                    "target": "能准确识别板块龙头",
                    "evaluation": "连续5日正确识别龙头率>80%",
                    "difficulty": "中等",
                },
                {
                    "title": "评分体系训练",
                    "description": "使用7维度评分体系评估标的",
                    "method": "每日选取5只标的进行评分，对比实际表现",
                    "duration": "每日45分钟",
                    "target": "评分与实际走势吻合度>70%",
                    "evaluation": "评分>70的标的次日上涨率>60%",
                    "difficulty": "困难",
                },
                {
                    "title": "跟风股识别训练",
                    "description": "学会识别和规避跟风股",
                    "method": "对比龙头和跟风股的走势差异，总结特征",
                    "duration": "每日20分钟",
                    "target": "能准确识别跟风股",
                    "evaluation": "跟风股识别准确率>90%",
                    "difficulty": "简单",
                },
            ],
            "择时": [
                {
                    "title": "情绪周期判断训练",
                    "description": "每日判断当前情绪周期阶段",
                    "method": "观察涨停数/炸板率/连板高度等指标判断周期",
                    "duration": "每日20分钟",
                    "target": "准确判断情绪周期",
                    "evaluation": "周期判断准确率>75%",
                    "difficulty": "中等",
                },
                {
                    "title": "买入时机训练",
                    "description": "练习在正确时机买入",
                    "method": "模拟盘在启动/发酵期买入，退潮期空仓",
                    "duration": "每日实盘时间",
                    "target": "择时胜率>55%",
                    "evaluation": "模拟盘月度胜率",
                    "difficulty": "困难",
                },
                {
                    "title": "退潮期管手训练",
                    "description": "练习在退潮期控制交易冲动",
                    "method": "退潮期强制不操作，记录冲动次数",
                    "duration": "退潮期全天",
                    "target": "退潮期零交易",
                    "evaluation": "退潮期交易次数=0",
                    "difficulty": "中等",
                },
            ],
            "仓位": [
                {
                    "title": "仓位分配训练",
                    "description": "练习根据确定性分配仓位",
                    "method": "模拟盘按评分分配仓位: >80分30%, 70-80分20%, <70分10%",
                    "duration": "每日实盘时间",
                    "target": "仓位分配合理性>80%",
                    "evaluation": "高确定性标的仓位>低确定性标的",
                    "difficulty": "中等",
                },
                {
                    "title": "总仓位控制训练",
                    "description": "练习控制总仓位",
                    "method": "记录每日总仓位，退潮期<30%，发酵期<80%",
                    "duration": "每日记录",
                    "target": "总仓位控制在合理范围",
                    "evaluation": "仓位违规次数<2次/周",
                    "difficulty": "简单",
                },
            ],
            "止损": [
                {
                    "title": "止损执行训练",
                    "description": "练习严格执行止损",
                    "method": "模拟盘设置-5%硬性止损，触发即执行",
                    "duration": "每日实盘时间",
                    "target": "止损执行率100%",
                    "evaluation": "止损执行率=100%",
                    "difficulty": "中等",
                },
                {
                    "title": "移动止损训练",
                    "description": "练习使用移动止损保护利润",
                    "method": "盈利5%后止损上移至成本，盈利10%后止损上移至+5%",
                    "duration": "每日实盘时间",
                    "target": "杜绝盈利变亏损",
                    "evaluation": "盈利变亏损次数=0",
                    "difficulty": "中等",
                },
            ],
            "心态": [
                {
                    "title": "FOMO克服训练",
                    "description": "练习克服追涨冲动",
                    "method": "想追高时强制等待15分钟，记录冲动次数",
                    "duration": "每日实盘时间",
                    "target": "FOMO交易降至0",
                    "evaluation": "追高买入次数<1次/周",
                    "difficulty": "困难",
                },
                {
                    "title": "冷静期训练",
                    "description": "练习亏损后冷静",
                    "method": "亏损后强制休息30分钟，不做任何操作",
                    "duration": "亏损后30分钟",
                    "target": "杜绝报复性交易",
                    "evaluation": "报复性交易次数=0",
                    "difficulty": "中等",
                },
                {
                    "title": "交易计划执行训练",
                    "description": "练习按计划交易，不临时决策",
                    "method": "盘前制定交易计划，盘中严格执行",
                    "duration": "每日盘前+盘中",
                    "target": "计划执行率>90%",
                    "evaluation": "临时决策次数<2次/周",
                    "difficulty": "中等",
                },
            ],
            "综合": [
                {
                    "title": "全流程模拟训练",
                    "description": "完整执行选股→择时→仓位→止损全流程",
                    "method": "模拟盘完整执行交易系统",
                    "duration": "每日实盘时间",
                    "target": "模拟盘月度盈利>0",
                    "evaluation": "月度胜率>50%，盈亏比>1.5",
                    "difficulty": "困难",
                },
                {
                    "title": "复盘训练",
                    "description": "每日复盘总结交易得失",
                    "method": "记录每笔交易的买入逻辑/卖出原因/改进点",
                    "duration": "每日30分钟",
                    "target": "形成复盘习惯",
                    "evaluation": "每日复盘完成率=100%",
                    "difficulty": "简单",
                },
            ],
        }
        
        # 获取该类别的任务模板
        templates = task_templates.get(category, task_templates.get("综合", []))
        
        # 每周2-3个任务
        num_tasks = min(3, len(templates))
        for i in range(num_tasks):
            template = templates[i % len(templates)]
            task = TrainingTask(
                task_id=f"W{week}T{i+1}",
                week=week,
                category=category,
                title=template["title"],
                description=template["description"],
                method=template["method"],
                duration=template["duration"],
                target=template["target"],
                evaluation=template["evaluation"],
                difficulty=template["difficulty"],
            )
            week_plan.tasks.append(task)
    
    def _get_week_review(self, category: str, week: int) -> str:
        """获取周复盘要点"""
        reviews = {
            "选股": f"本周选股训练复盘:\n  1. 龙头识别准确率?\n  2. 评分体系使用熟练度?\n  3. 跟风股规避情况?",
            "择时": f"本周择时训练复盘:\n  1. 情绪周期判断准确率?\n  2. 买入时机是否合理?\n  3. 退潮期是否管住手?",
            "仓位": f"本周仓位训练复盘:\n  1. 仓位分配是否合理?\n  2. 总仓位是否控制?\n  3. 高确定性标的仓位是否足够?",
            "止损": f"本周止损训练复盘:\n  1. 止损执行率?\n  2. 移动止损使用情况?\n  3. 盈利变亏损次数?",
            "心态": f"本周心态训练复盘:\n  1. FOMO交易次数?\n  2. 报复性交易次数?\n  3. 计划执行率?",
            "综合": f"本周综合训练复盘:\n  1. 全流程执行情况?\n  2. 模拟盘盈亏?\n  3. 需要改进的地方?",
        }
        return reviews.get(category, "本周训练复盘")
    
    # ==================== 训练场景 ====================
    
    def _generate_scenarios(self, profile: TradeProfile, plan: TrainingPlan):
        """生成训练场景"""
        scenarios: List[str] = []
        
        # 基础场景
        scenarios.extend([
            "🎯 场景1: 主线题材启动日 - 练习龙头识别和打板",
            "🎯 场景2: 板块分歧日 - 练习分歧低吸",
            "🎯 场景3: 情绪退潮期 - 练习管住手",
            "🎯 场景4: 情绪冰点期 - 练习冰点试错",
            "🎯 场景5: 高潮加速日 - 练习不追涨",
        ])
        
        # 根据风格添加场景
        if profile.style == "龙头接力型":
            scenarios.extend([
                "🎯 场景6: 龙头首阴 - 练习龙头首阴低吸",
                "🎯 场景7: 龙头二波 - 练习二波启动识别",
            ])
        elif profile.style == "分歧低吸型":
            scenarios.extend([
                "🎯 场景6: 强势股分歧 - 练习分歧低吸时机",
                "🎯 场景7: 板块轮动 - 练习轮动低吸",
            ])
        
        plan.training_scenarios = scenarios
    
    # ==================== 评估标准 ====================
    
    def _generate_evaluation_criteria(self, plan: TrainingPlan):
        """生成评估标准"""
        criteria = [
            "📊 选股能力: 评分>70的标的次日上涨率>60%",
            "📊 择时能力: 情绪周期判断准确率>75%",
            "📊 仓位管理: 仓位违规次数<2次/周",
            "📊 止损执行: 止损执行率=100%",
            "📊 心态控制: FOMO/报复性交易=0",
            "📊 综合表现: 模拟盘月度胜率>50%，盈亏比>1.5",
            "📊 复盘习惯: 每日复盘完成率=100%",
        ]
        plan.evaluation_criteria = criteria
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, plan: TrainingPlan) -> str:
        """构建摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║         模拟训练计划                  ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        parts.append(f"📊 训练信息:")
        parts.append(f"   当前水平: {plan.current_level}")
        parts.append(f"   目标水平: {plan.target_level}")
        parts.append(f"   训练周期: {plan.total_weeks}周")
        parts.append(f"   训练重点: {', '.join(plan.focus_areas)}")
        parts.append("")
        
        if plan.weekly_plans:
            parts.append("📅 周计划概览:")
            for week_plan in plan.weekly_plans[:4]:
                parts.append(f"   {week_plan.theme}")
                for task in week_plan.tasks[:2]:
                    parts.append(f"      • {task.title} ({task.difficulty})")
            if len(plan.weekly_plans) > 4:
                parts.append(f"   ... 还有{len(plan.weekly_plans) - 4}周计划")
            parts.append("")
        
        if plan.training_scenarios:
            parts.append("🎯 训练场景:")
            for scenario in plan.training_scenarios[:5]:
                parts.append(f"   {scenario}")
            parts.append("")
        
        if plan.evaluation_criteria:
            parts.append("📊 评估标准:")
            for criterion in plan.evaluation_criteria:
                parts.append(f"   {criterion}")
        
        return "\n".join(parts)