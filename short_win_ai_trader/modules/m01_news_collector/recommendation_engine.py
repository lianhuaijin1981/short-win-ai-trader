"""利好介入建议生成器 & 利空风险预警生成器

基于历史回测数据和消息影响力评估，生成:
1. 利好介入建议 — 对研判为重要利好的资讯提供操作建议
2. 利空风险预警 — 对重大利空资讯提供风险预警

核心逻辑:
- 结合消息类型、影响力评分、历史胜率、预期收益
- 考虑当前市场情绪周期和板块热度
- 生成具体的操作建议（买入时机、仓位、持有周期、止盈止损）
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .backtest_engine import BacktestEngine, MESSAGE_TYPE_PROFILES
from .models import NewsCategory, NewsItem, NewsGrade, ScoredNews

logger = get_logger("swat.m01.recommendation")


# ==================== 数据模型 ====================

@dataclass
class EntryRecommendation:
    """利好介入建议"""
    news_title: str = ""                    # 资讯标题
    news_source: str = ""                   # 资讯来源
    message_type: str = ""                  # 消息类型
    impact_score: float = 0.0               # 影响力评分
    direction: str = "bullish"              # 方向
    
    # 关联标的
    related_tickers: List[str] = field(default_factory=list)
    related_themes: List[str] = field(default_factory=list)
    
    # 操作建议
    action: str = ""                        # 操作动作（买入/观望/回避）
    urgency: str = "normal"                 # 紧急程度: urgent/normal/low
    entry_timing: str = ""                  # 介入时机
    position_pct: float = 0.0               # 建议仓位比例（0-100%）
    hold_days: int = 1                      # 建议持有天数
    target_profit_pct: float = 0.0          # 目标收益率
    stop_loss_pct: float = 0.0              # 止损线
    
    # 历史数据支撑
    win_rate: float = 0.0                   # 历史胜率
    expected_return: float = 0.0            # 预期收益
    max_drawdown: float = 0.0               # 最大回撤
    
    # 风险提示
    risk_warning: str = ""                  # 风险提示
    confidence: str = "medium"              # 置信度: high/medium/low
    
    # 元数据
    generated_at: str = ""                  # 生成时间
    news_id: str = ""                       # 关联资讯ID


@dataclass
class RiskAlert:
    """利空风险预警"""
    news_title: str = ""                    # 资讯标题
    news_source: str = ""                   # 资讯来源
    message_type: str = ""                  # 消息类型
    impact_score: float = 0.0               # 影响力评分
    severity: str = "medium"                # 严重程度: extreme/high/medium/low
    
    # 关联标的
    related_tickers: List[str] = field(default_factory=list)
    related_themes: List[str] = field(default_factory=list)
    
    # 风险详情
    risk_type: str = ""                     # 风险类型
    risk_description: str = ""              # 风险描述
    expected_loss: float = 0.0              # 预期亏损幅度
    worst_case_loss: float = 0.0            # 最坏情况亏损
    
    # 应对建议
    action: str = ""                        # 应对动作
    action_urgency: str = "normal"          # 紧急程度
    
    # 历史数据
    historical_win_rate: float = 0.0        # 历史上涨概率（越低越危险）
    historical_avg_loss: float = 0.0        # 历史平均亏损
    
    # 元数据
    generated_at: str = ""                  # 生成时间
    news_id: str = ""                       # 关联资讯ID


# ==================== 利好介入建议生成器 ====================

class EntryRecommendationGenerator:
    """利好介入建议生成器
    
    基于消息影响力评估和历史回测数据，生成具体的操作建议。
    """
    
    def __init__(self, backtest_engine: Optional[BacktestEngine] = None):
        """初始化建议生成器
        
        Args:
            backtest_engine: 回测引擎实例
        """
        self.backtest_engine = backtest_engine or BacktestEngine()
        
        # 仓位控制规则（基于影响力评分）
        self.position_rules = {
            "extreme": (60, 80),   # 极高影响: 60-80%仓位
            "high": (40, 60),      # 高影响: 40-60%仓位
            "medium": (20, 40),    # 中等影响: 20-40%仓位
            "low": (10, 20),       # 低影响: 10-20%仓位
        }
        
        logger.info("利好介入建议生成器初始化完成")
    
    def generate(
        self,
        scored_news: ScoredNews,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[EntryRecommendation]:
        """为单条资讯生成介入建议
        
        Args:
            scored_news: 已评分的资讯
            market_context: 市场上下文（情绪周期、板块热度等）
            
        Returns:
            EntryRecommendation 或 None（如果不建议介入）
        """
        # 只处理利好资讯（S级或A级）
        if scored_news.grade not in (NewsGrade.S, NewsGrade.A):
            return None
        
        # 检查是否为利好方向
        news = scored_news.news
        text = f"{news.title} {news.content}"
        
        # 使用回测引擎分类消息类型
        type_matches = self.backtest_engine.classify_message_type(news.title, news.content)
        
        if not type_matches:
            return None
        
        primary_type, confidence = type_matches[0]
        profile = self.backtest_engine.get_message_impact(primary_type)
        
        if not profile or profile.direction != "bullish":
            return None
        
        # 获取消息类型的历史数据
        msg_profile = MESSAGE_TYPE_PROFILES.get(primary_type, {})
        
        # 确定影响等级
        impact_level = msg_profile.get("impact_level", "medium")
        
        # 计算仓位
        pos_range = self.position_rules.get(impact_level, (20, 40))
        # 根据评分调整仓位
        score_factor = scored_news.score / 100
        position_pct = pos_range[0] + (pos_range[1] - pos_range[0]) * score_factor
        
        # 确定介入时机
        entry_timing = self._determine_entry_timing(
            primary_type, impact_level, news.publish_time, market_context
        )
        
        # 确定止盈止损
        avg_return = msg_profile.get("avg_return_1d", 3.0)
        max_return = msg_profile.get("max_return", 10.0)
        min_return = msg_profile.get("min_return", -5.0)
        
        target_profit = min(max_return * 0.7, avg_return * 2)
        stop_loss = max(min_return * 0.5, -5.0)  # 止损不超过5%
        
        # 确定紧急程度
        if impact_level == "extreme" and scored_news.score >= 80:
            urgency = "urgent"
        elif impact_level in ("extreme", "high") and scored_news.score >= 60:
            urgency = "normal"
        else:
            urgency = "low"
        
        # 确定置信度
        if scored_news.score >= 75 and confidence >= 0.7:
            rec_confidence = "high"
        elif scored_news.score >= 50 and confidence >= 0.5:
            rec_confidence = "medium"
        else:
            rec_confidence = "low"
        
        # 生成风险提示
        risk_warning = self._generate_risk_warning(
            primary_type, impact_level, msg_profile, market_context
        )
        
        # 生成操作动作
        if urgency == "urgent":
            action = "立即介入"
        elif urgency == "normal":
            action = "择机买入"
        else:
            action = "可考虑低吸"
        
        recommendation = EntryRecommendation(
            news_title=news.title,
            news_source=news.source.name,
            message_type=primary_type,
            impact_score=scored_news.score,
            direction="bullish",
            related_tickers=news.related_tickers,
            related_themes=news.related_themes,
            action=action,
            urgency=urgency,
            entry_timing=entry_timing,
            position_pct=round(position_pct, 1),
            hold_days=msg_profile.get("optimal_hold_days", 2),
            target_profit_pct=round(target_profit, 1),
            stop_loss_pct=round(stop_loss, 1),
            win_rate=profile.win_rate,
            expected_return=profile.expected_return_1d,
            max_drawdown=abs(min_return),
            risk_warning=risk_warning,
            confidence=rec_confidence,
            generated_at=datetime.now().isoformat(),
            news_id=news.id,
        )
        
        logger.info(
            f"生成介入建议: {news.title[:30]}",
            action=action,
            position=position_pct,
            urgency=urgency,
        )
        
        return recommendation
    
    def generate_batch(
        self,
        scored_news_list: List[ScoredNews],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> List[EntryRecommendation]:
        """批量生成介入建议
        
        Args:
            scored_news_list: 已评分的资讯列表
            market_context: 市场上下文
            
        Returns:
            List[EntryRecommendation] 介入建议列表（按紧急程度和评分排序）
        """
        recommendations = []
        
        for sn in scored_news_list:
            rec = self.generate(sn, market_context)
            if rec:
                recommendations.append(rec)
        
        # 排序: 紧急程度 > 影响力评分
        urgency_order = {"urgent": 0, "normal": 1, "low": 2}
        recommendations.sort(
            key=lambda r: (urgency_order.get(r.urgency, 3), -r.impact_score)
        )
        
        return recommendations
    
    def _determine_entry_timing(
        self,
        message_type: str,
        impact_level: str,
        publish_time: Optional[datetime],
        market_context: Optional[Dict],
    ) -> str:
        """确定介入时机"""
        # 基于消息类型和发布时间判断
        if not publish_time:
            return "开盘后观察承接力度再决定"
        
        hour = publish_time.hour
        
        # 盘前消息
        if hour < 9:
            if impact_level == "extreme":
                return "集合竞价阶段可考虑挂单，或开盘后立即介入"
            elif impact_level == "high":
                return "开盘后观察5-10分钟，确认强势后介入"
            else:
                return "开盘后观察30分钟，确认方向后介入"
        
        # 盘中消息
        elif 9 <= hour < 15:
            if impact_level == "extreme":
                return "消息发布后立即介入，不要等待回调"
            elif impact_level == "high":
                return "消息发布后观察10分钟，确认承接后介入"
            else:
                return "等待盘中回调时低吸"
        
        # 盘后消息
        else:
            if impact_level == "extreme":
                return "次日集合竞价挂单，或开盘后立即介入"
            elif impact_level == "high":
                return "次日开盘后观察承接力度再决定"
            else:
                return "次日盘中寻找低吸机会"
    
    def _generate_risk_warning(
        self,
        message_type: str,
        impact_level: str,
        msg_profile: Dict,
        market_context: Optional[Dict],
    ) -> str:
        """生成风险提示"""
        warnings = []
        
        # 基于历史最大回撤
        min_return = msg_profile.get("min_return", -5.0)
        warnings.append(f"历史最大回撤{abs(min_return):.0f}%")
        
        # 基于胜率
        win_rate = msg_profile.get("win_rate", 0.6)
        if win_rate < 0.7:
            warnings.append(f"历史胜率仅{win_rate*100:.0f}%，存在失败可能")
        
        # 基于市场环境
        if market_context:
            emotion_cycle = market_context.get("emotion_cycle", "")
            if emotion_cycle in ("退潮期", "分歧期"):
                warnings.append(f"当前处于{emotion_cycle}，需降低预期")
        
        # 基于影响等级
        if impact_level == "extreme":
            warnings.append("重大利好但需警惕利好出尽")
        
        return "；".join(warnings) if warnings else "注意仓位控制和止盈止损"


# ==================== 利空风险预警生成器 ====================

class RiskAlertGenerator:
    """利空风险预警生成器
    
    基于消息影响力评估和历史回测数据，生成风险预警。
    """
    
    def __init__(self, backtest_engine: Optional[BacktestEngine] = None):
        """初始化风险预警生成器
        
        Args:
            backtest_engine: 回测引擎实例
        """
        self.backtest_engine = backtest_engine or BacktestEngine()
        
        logger.info("利空风险预警生成器初始化完成")
    
    def generate(
        self,
        news: NewsItem,
        impact_score: float = 0.0,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[RiskAlert]:
        """为单条资讯生成风险预警
        
        Args:
            news: 资讯条目
            impact_score: 影响力评分
            market_context: 市场上下文
            
        Returns:
            RiskAlert 或 None（如果不是利空）
        """
        text = f"{news.title} {news.content}"
        
        # 使用回测引擎分类消息类型
        type_matches = self.backtest_engine.classify_message_type(news.title, news.content)
        
        if not type_matches:
            return None
        
        primary_type, confidence = type_matches[0]
        profile = self.backtest_engine.get_message_impact(primary_type)
        
        if not profile:
            return None
        
        # 只处理利空消息
        if profile.direction != "bearish":
            return None
        
        # 获取消息类型的历史数据
        msg_profile = MESSAGE_TYPE_PROFILES.get(primary_type, {})
        
        # 确定严重程度
        impact_level = msg_profile.get("impact_level", "medium")
        
        # 计算预期亏损
        avg_return = msg_profile.get("avg_return_1d", -3.0)
        min_return = msg_profile.get("min_return", -10.0)
        
        # 确定应对动作
        action, urgency = self._determine_action(impact_level, avg_return)
        
        # 确定风险类型
        risk_type = self._classify_risk_type(primary_type, news.category)
        
        # 生成风险描述
        risk_description = self._generate_risk_description(
            primary_type, news.title, msg_profile
        )
        
        # 确定严重程度标签
        if impact_level == "extreme":
            severity = "extreme"
        elif impact_level == "high":
            severity = "high"
        elif impact_level == "medium":
            severity = "medium"
        else:
            severity = "low"
        
        alert = RiskAlert(
            news_title=news.title,
            news_source=news.source.name,
            message_type=primary_type,
            impact_score=impact_score or profile.impact_score,
            severity=severity,
            related_tickers=news.related_tickers,
            related_themes=news.related_themes,
            risk_type=risk_type,
            risk_description=risk_description,
            expected_loss=round(abs(avg_return), 1),
            worst_case_loss=round(abs(min_return), 1),
            action=action,
            action_urgency=urgency,
            historical_win_rate=profile.win_rate,
            historical_avg_loss=round(abs(avg_return), 1),
            generated_at=datetime.now().isoformat(),
            news_id=news.id,
        )
        
        logger.info(
            f"生成风险预警: {news.title[:30]}",
            severity=severity,
            action=action,
        )
        
        return alert
    
    def generate_batch(
        self,
        news_list: List[NewsItem],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> List[RiskAlert]:
        """批量生成风险预警
        
        Args:
            news_list: 资讯列表
            market_context: 市场上下文
            
        Returns:
            List[RiskAlert] 风险预警列表（按严重程度排序）
        """
        alerts = []
        
        for news in news_list:
            alert = self.generate(news, market_context=market_context)
            if alert:
                alerts.append(alert)
        
        # 排序: 严重程度 > 影响力评分
        severity_order = {"extreme": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(
            key=lambda a: (severity_order.get(a.severity, 4), -a.impact_score)
        )
        
        return alerts
    
    def _determine_action(self, impact_level: str, avg_return: float) -> Tuple[str, str]:
        """确定应对动作和紧急程度"""
        if impact_level == "extreme":
            return "绝对禁入，持仓立即清仓", "urgent"
        elif impact_level == "high":
            return "高度谨慎，建议回避或减仓", "urgent"
        elif impact_level == "medium":
            return "谨慎对待，注意风险控制", "normal"
        else:
            return "关注后续发展", "low"
    
    def _classify_risk_type(self, message_type: str, category: NewsCategory) -> str:
        """分类风险类型"""
        risk_type_map = {
            "业绩大幅预亏": "业绩风险",
            "大股东减持": "筹码风险",
            "立案调查": "合规风险",
            "债务违约": "财务风险",
            "退市风险": "退市风险",
            "政策利空": "政策风险",
            "解禁压力": "解禁风险",
            "高管变动": "治理风险",
            "股权质押": "质押风险",
        }
        
        return risk_type_map.get(message_type, f"{category.value}风险")
    
    def _generate_risk_description(
        self,
        message_type: str,
        news_title: str,
        msg_profile: Dict,
    ) -> str:
        """生成风险描述"""
        avg_return = msg_profile.get("avg_return_1d", -3.0)
        win_rate = msg_profile.get("win_rate", 0.3)
        min_return = msg_profile.get("min_return", -10.0)
        
        description = f"【{message_type}】"
        description += f"历史数据显示，此类消息次日平均下跌{abs(avg_return):.1f}%，"
        description += f"上涨概率仅{win_rate*100:.0f}%，"
        description += f"最大亏损可达{abs(min_return):.0f}%。"
        
        if win_rate < 0.2:
            description += "历史上几乎全部下跌，风险极高！"
        elif win_rate < 0.35:
            description += "历史下跌概率超过65%，需高度警惕。"
        
        return description


# ==================== 综合建议引擎 ====================

class RecommendationEngine:
    """综合建议引擎
    
    整合利好介入建议和利空风险预警，提供完整的操作指导。
    """
    
    def __init__(self, backtest_engine: Optional[BacktestEngine] = None):
        """初始化综合建议引擎
        
        Args:
            backtest_engine: 回测引擎实例
        """
        self.backtest_engine = backtest_engine or BacktestEngine()
        self.entry_generator = EntryRecommendationGenerator(self.backtest_engine)
        self.risk_generator = RiskAlertGenerator(self.backtest_engine)
        
        logger.info("综合建议引擎初始化完成")
    
    def analyze(
        self,
        scored_news_list: List[ScoredNews],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """分析资讯列表，生成综合建议
        
        Args:
            scored_news_list: 已评分的资讯列表
            market_context: 市场上下文
            
        Returns:
            综合建议字典
        """
        # 生成利好介入建议
        entry_recs = self.entry_generator.generate_batch(scored_news_list, market_context)
        
        # 生成利空风险预警
        all_news = [sn.news for sn in scored_news_list]
        risk_alerts = self.risk_generator.generate_batch(all_news, market_context)
        
        # 统计
        urgent_entries = [r for r in entry_recs if r.urgency == "urgent"]
        extreme_risks = [a for a in risk_alerts if a.severity == "extreme"]
        
        # 生成综合摘要
        summary = self._generate_summary(entry_recs, risk_alerts, market_context)
        
        return {
            "summary": summary,
            "entry_recommendations": [
                {
                    "news_title": r.news_title,
                    "news_source": r.news_source,
                    "message_type": r.message_type,
                    "impact_score": r.impact_score,
                    "related_tickers": r.related_tickers,
                    "related_themes": r.related_themes,
                    "action": r.action,
                    "urgency": r.urgency,
                    "entry_timing": r.entry_timing,
                    "position_pct": r.position_pct,
                    "hold_days": r.hold_days,
                    "target_profit_pct": r.target_profit_pct,
                    "stop_loss_pct": r.stop_loss_pct,
                    "win_rate": r.win_rate,
                    "expected_return": r.expected_return,
                    "risk_warning": r.risk_warning,
                    "confidence": r.confidence,
                }
                for r in entry_recs
            ],
            "risk_alerts": [
                {
                    "news_title": a.news_title,
                    "news_source": a.news_source,
                    "message_type": a.message_type,
                    "impact_score": a.impact_score,
                    "severity": a.severity,
                    "related_tickers": a.related_tickers,
                    "related_themes": a.related_themes,
                    "risk_type": a.risk_type,
                    "risk_description": a.risk_description,
                    "expected_loss": a.expected_loss,
                    "worst_case_loss": a.worst_case_loss,
                    "action": a.action,
                    "action_urgency": a.action_urgency,
                }
                for a in risk_alerts
            ],
            "statistics": {
                "total_entry_recommendations": len(entry_recs),
                "urgent_entries": len(urgent_entries),
                "total_risk_alerts": len(risk_alerts),
                "extreme_risks": len(extreme_risks),
                "forbidden_tickers": list(set(
                    t for a in risk_alerts if a.severity == "extreme"
                    for t in a.related_tickers
                )),
            },
        }
    
    def _generate_summary(
        self,
        entry_recs: List[EntryRecommendation],
        risk_alerts: List[RiskAlert],
        market_context: Optional[Dict],
    ) -> str:
        """生成综合摘要"""
        parts = []
        
        # 利好统计
        urgent_entries = [r for r in entry_recs if r.urgency == "urgent"]
        if urgent_entries:
            parts.append(f"🔥 紧急介入机会{len(urgent_entries)}个")
        
        normal_entries = [r for r in entry_recs if r.urgency == "normal"]
        if normal_entries:
            parts.append(f"📈 建议关注机会{len(normal_entries)}个")
        
        # 风险统计
        extreme_risks = [a for a in risk_alerts if a.severity == "extreme"]
        if extreme_risks:
            parts.append(f"⚠️ 重大风险预警{len(extreme_risks)}个，绝对禁入")
        
        high_risks = [a for a in risk_alerts if a.severity == "high"]
        if high_risks:
            parts.append(f"🔴 高风险预警{len(high_risks)}个，建议回避")
        
        # 市场环境
        if market_context:
            emotion = market_context.get("emotion_cycle", "")
            if emotion:
                parts.append(f"当前情绪周期: {emotion}")
        
        if not parts:
            return "当日无显著利好或利空消息，建议观望为主"
        
        return " | ".join(parts)