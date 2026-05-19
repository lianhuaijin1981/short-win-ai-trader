"""交易笔记引擎 — 当日复盘 + 次日计划核心逻辑

提供:
1. 当日交易复盘生成与分析
2. 次日交易计划生成
3. 交易统计与绩效分析
4. 智能建议生成
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .models import (
    MarketOutlook,
    MindsetLevel,
    NextDayPlan,
    PositionRecord,
    TradeNote,
    TradeResult,
    TradeReview,
    WatchStock,
)

logger = get_logger("swat.m08.note_engine")


class NoteEngine:
    """交易笔记引擎
    
    负责生成、分析、优化交易笔记（当日复盘+次日计划）。
    """
    
    def __init__(self):
        """初始化交易笔记引擎"""
        logger.info("交易笔记引擎初始化完成")
    
    # ==================== 当日复盘 ====================
    
    def create_review(
        self,
        positions: List[Dict],
        mindset_level: str = "一般",
        mindset_summary: str = "",
        rhythm_summary: str = "",
        discipline_summary: str = "",
        mindset_issues: Optional[List[str]] = None,
        rhythm_issues: Optional[List[str]] = None,
        discipline_issues: Optional[List[str]] = None,
        lessons_learned: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
        overall_summary: str = "",
        self_score: float = 0.0,
        review_date: Optional[date] = None,
    ) -> TradeReview:
        """创建当日交易复盘
        
        Args:
            positions: 持仓记录列表（字典格式）
            mindset_level: 心态评级
            mindset_summary: 心态总结
            rhythm_summary: 节奏总结
            discipline_summary: 纪律总结
            mindset_issues: 心态问题列表
            rhythm_issues: 节奏问题列表
            discipline_issues: 纪律问题列表
            lessons_learned: 经验教训列表
            improvements: 改进方向列表
            overall_summary: 整体总结
            self_score: 自我评分
            review_date: 复盘日期
            
        Returns:
            TradeReview: 交易复盘对象
        """
        # 转换持仓记录
        position_records = []
        for p in positions:
            record = PositionRecord(
                ticker=p.get("ticker", ""),
                stock_name=p.get("stock_name", ""),
                sector=p.get("sector", ""),
                entry_price=p.get("entry_price", 0.0),
                entry_time=p.get("entry_time", ""),
                entry_reason=p.get("entry_reason", ""),
                entry_method=p.get("entry_method", ""),
                exit_price=p.get("exit_price", 0.0),
                exit_time=p.get("exit_time", ""),
                exit_reason=p.get("exit_reason", ""),
                position_size=p.get("position_size", 0.0),
                profit_loss_pct=p.get("profit_loss_pct", 0.0),
                profit_loss_amount=p.get("profit_loss_amount", 0.0),
                result=TradeResult(p.get("result", "未结")),
                trade_logic=p.get("trade_logic", ""),
                tactic_used=p.get("tactic_used", ""),
                has_error=p.get("has_error", False),
                error_type=p.get("error_type", ""),
                error_summary=p.get("error_summary", ""),
                notes=p.get("notes", ""),
            )
            position_records.append(record)
        
        # 计算统计数据
        total_trades = len(position_records)
        win_count = sum(1 for p in position_records if p.result == TradeResult.PROFIT)
        loss_count = sum(1 for p in position_records if p.result == TradeResult.LOSS)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
        total_pnl = sum(p.profit_loss_amount for p in position_records)
        total_pnl_pct = sum(p.profit_loss_pct for p in position_records)
        
        # 映射心态评级
        mindset_map = {
            "优秀": MindsetLevel.EXCELLENT,
            "良好": MindsetLevel.GOOD,
            "一般": MindsetLevel.NORMAL,
            "较差": MindsetLevel.POOR,
            "极差": MindsetLevel.TERRIBLE,
        }
        mindset = mindset_map.get(mindset_level, MindsetLevel.NORMAL)
        
        review = TradeReview(
            date=review_date or date.today(),
            positions=position_records,
            total_trades=total_trades,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=round(win_rate, 1),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
            mindset_level=mindset,
            mindset_summary=mindset_summary,
            rhythm_summary=rhythm_summary,
            discipline_summary=discipline_summary,
            mindset_issues=mindset_issues or [],
            rhythm_issues=rhythm_issues or [],
            discipline_issues=discipline_issues or [],
            lessons_learned=lessons_learned or [],
            improvements=improvements or [],
            overall_summary=overall_summary,
            self_score=self_score,
        )
        
        logger.info(f"创建交易复盘: {total_trades}笔交易, 胜率{win_rate:.1f}%, 盈亏{total_pnl:.2f}")
        return review
    
    # ==================== 次日计划 ====================
    
    def create_next_day_plan(
        self,
        market_outlook: str = "震荡中性",
        market_reasoning: str = "",
        key_levels: str = "",
        watch_stocks: Optional[List[Dict]] = None,
        total_position_limit: float = 50.0,
        single_stock_limit: float = 20.0,
        max_trades: int = 3,
        position_plan: str = "",
        stop_loss_rule: str = "",
        take_profit_rule: str = "",
        max_daily_loss: float = 3.0,
        risk_rules: Optional[List[str]] = None,
        risk_directions: Optional[List[str]] = None,
        avoid_sectors: Optional[List[str]] = None,
        avoid_stocks: Optional[List[str]] = None,
        preferred_sectors: Optional[List[str]] = None,
        preferred_tactics: Optional[List[str]] = None,
        notes: str = "",
        plan_date: Optional[date] = None,
    ) -> NextDayPlan:
        """创建次日交易计划
        
        Args:
            market_outlook: 大盘整体判断
            market_reasoning: 大盘判断思路
            key_levels: 关键支撑/压力位
            watch_stocks: 观察标的列表
            total_position_limit: 整体仓位上限
            single_stock_limit: 单票仓位上限
            max_trades: 最大交易笔数
            position_plan: 仓位管控计划
            stop_loss_rule: 止损纪律
            take_profit_rule: 止盈纪律
            max_daily_loss: 单日最大亏损限制
            risk_rules: 风控规则列表
            risk_directions: 风险避雷方向
            avoid_sectors: 规避板块
            avoid_stocks: 规避个股
            preferred_sectors: 重点关注板块
            preferred_tactics: 首选战法
            notes: 备注
            plan_date: 计划日期
            
        Returns:
            NextDayPlan: 次日交易计划对象
        """
        # 映射大盘预判
        outlook_map = {
            "强势看多": MarketOutlook.STRONG,
            "震荡偏多": MarketOutlook.NEUTRAL_BULL,
            "震荡中性": MarketOutlook.NEUTRAL,
            "震荡偏空": MarketOutlook.NEUTRAL_BEAR,
            "弱势看空": MarketOutlook.WEAK,
        }
        outlook = outlook_map.get(market_outlook, MarketOutlook.NEUTRAL)
        
        # 转换观察标的
        watch_stock_records = []
        for ws in (watch_stocks or []):
            watch_stock = WatchStock(
                ticker=ws.get("ticker", ""),
                stock_name=ws.get("stock_name", ""),
                sector=ws.get("sector", ""),
                watch_reason=ws.get("watch_reason", ""),
                expected_action=ws.get("expected_action", ""),
                key_price=ws.get("key_price", 0.0),
                trigger_condition=ws.get("trigger_condition", ""),
                score=ws.get("score", 0.0),
                rating=ws.get("rating", ""),
                risk_level=ws.get("risk_level", ""),
                advice=ws.get("advice", ""),
                priority=ws.get("priority", 0),
            )
            watch_stock_records.append(watch_stock)
        
        # 按优先级排序
        watch_stock_records.sort(key=lambda x: x.priority if x.priority > 0 else 99)
        
        # 默认风控规则
        default_risk_rules = [
            "严格执行止损，不得移动止损位",
            "单日亏损达上限立即停止交易",
            "不追高，不抄底，只做确定性机会",
            "仓位管理：单票不超过上限，总仓位不超限",
        ]
        
        # 默认止损止盈规则
        default_stop_loss = stop_loss_rule or "固定止损-5%，逻辑止损（题材证伪/龙头跌停）无条件卖出"
        default_take_profit = take_profit_rule or "分批止盈：盈利5%减半，10%清仓；动态止盈：远离5日线减仓"
        
        plan = NextDayPlan(
            date=plan_date or (date.today() + timedelta(days=1)),
            created_at=datetime.now(),
            market_outlook=outlook,
            market_reasoning=market_reasoning,
            key_levels=key_levels,
            watch_stocks=watch_stock_records,
            total_position_limit=total_position_limit,
            single_stock_limit=single_stock_limit,
            max_trades=max_trades,
            position_plan=position_plan or f"总仓位不超过{total_position_limit}%，单票不超过{single_stock_limit}%",
            stop_loss_rule=default_stop_loss,
            take_profit_rule=default_take_profit,
            max_daily_loss=max_daily_loss,
            risk_rules=risk_rules or default_risk_rules,
            risk_directions=risk_directions or [],
            avoid_sectors=avoid_sectors or [],
            avoid_stocks=avoid_stocks or [],
            preferred_sectors=preferred_sectors or [],
            preferred_tactics=preferred_tactics or [],
            notes=notes,
        )
        
        logger.info(f"创建次日计划: 大盘{market_outlook}, 观察{len(watch_stock_records)}只标的")
        return plan
    
    # ==================== 完整笔记 ====================
    
    def create_trade_note(
        self,
        review: Optional[TradeReview] = None,
        next_day_plan: Optional[NextDayPlan] = None,
        source: str = "manual",
        tags: Optional[List[str]] = None,
        voice_note_id: Optional[str] = None,
        note_date: Optional[date] = None,
    ) -> TradeNote:
        """创建完整交易笔记
        
        Args:
            review: 交易复盘
            next_day_plan: 次日计划
            source: 来源
            tags: 标签
            voice_note_id: 关联语音笔记ID
            note_date: 笔记日期
            
        Returns:
            TradeNote: 完整交易笔记
        """
        note = TradeNote(
            id=str(uuid.uuid4())[:12],
            date=note_date or date.today(),
            review=review,
            next_day_plan=next_day_plan,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=source,
            tags=tags or [],
            voice_note_id=voice_note_id,
        )
        
        logger.info(f"创建交易笔记: ID={note.id}, 来源={source}")
        return note
    
    # ==================== 智能分析 ====================
    
    def analyze_review(self, review: TradeReview) -> Dict:
        """分析交易复盘，生成智能建议
        
        Args:
            review: 交易复盘对象
            
        Returns:
            Dict: 分析结果
        """
        analysis = {
            "summary": {},
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "risk_alerts": [],
        }
        
        # 基础统计
        analysis["summary"] = {
            "total_trades": review.total_trades,
            "win_rate": review.win_rate,
            "total_pnl": review.total_pnl,
            "total_pnl_pct": review.total_pnl_pct,
            "mindset_level": review.mindset_level.value,
            "self_score": review.self_score,
        }
        
        # 优势分析
        if review.win_rate >= 60:
            analysis["strengths"].append(f"胜率{review.win_rate}%，交易质量较高")
        if review.total_pnl > 0:
            analysis["strengths"].append(f"整体盈利{review.total_pnl:.2f}元，赚钱效应良好")
        if review.mindset_level in (MindsetLevel.EXCELLENT, MindsetLevel.GOOD):
            analysis["strengths"].append(f"心态{review.mindset_level.value}，情绪控制良好")
        
        # 劣势分析
        if review.win_rate < 40:
            analysis["weaknesses"].append(f"胜率仅{review.win_rate}%，需提高选股质量")
        if review.total_pnl < 0:
            analysis["weaknesses"].append(f"整体亏损{abs(review.total_pnl):.2f}元，需反思交易逻辑")
        if review.mindset_level in (MindsetLevel.POOR, MindsetLevel.TERRIBLE):
            analysis["weaknesses"].append(f"心态{review.mindset_level.value}，情绪管理需加强")
        
        # 失误分析
        error_count = sum(1 for p in review.positions if p.has_error)
        if error_count > 0:
            analysis["weaknesses"].append(f"存在{error_count}笔操作失误，需重点改进")
            error_types = {}
            for p in review.positions:
                if p.has_error and p.error_type:
                    error_types[p.error_type] = error_types.get(p.error_type, 0) + 1
            for etype, count in error_types.items():
                analysis["suggestions"].append(f"减少{etype}类失误（出现{count}次）")
        
        # 智能建议
        if review.win_rate < 50 and review.total_trades >= 3:
            analysis["suggestions"].append("建议减少交易频率，提高单笔交易质量")
        if review.total_pnl_pct < -5:
            analysis["risk_alerts"].append("当日亏损较大，建议次日降低仓位或空仓观望")
        if len(review.discipline_issues) > 0:
            analysis["suggestions"].append("纪律问题需重视，建议制定更严格的交易规则")
        
        # 心态建议
        if review.mindset_level == MindsetLevel.TERRIBLE:
            analysis["suggestions"].append("心态极差，建议暂停交易1-2天调整状态")
        elif review.mindset_level == MindsetLevel.POOR:
            analysis["suggestions"].append("心态较差，建议次日轻仓操作，找回节奏")
        
        return analysis
    
    def generate_plan_suggestions(
        self, 
        review: TradeReview, 
        market_data: Optional[Dict] = None
    ) -> Dict:
        """基于复盘数据生成次日计划建议
        
        Args:
            review: 交易复盘
            market_data: 市场数据（可选）
            
        Returns:
            Dict: 计划建议
        """
        suggestions = {
            "market_outlook": "震荡中性",
            "position_limit": 50.0,
            "max_trades": 3,
            "risk_level": "中风险",
            "key_reminders": [],
            "preferred_tactics": [],
            "avoid_directions": [],
        }
        
        # 基于复盘表现调整建议
        if review.win_rate >= 60 and review.total_pnl > 0:
            suggestions["market_outlook"] = "震荡偏多"
            suggestions["position_limit"] = 60.0
            suggestions["risk_level"] = "低风险"
            suggestions["key_reminders"].append("状态良好，可适当积极操作")
        elif review.win_rate < 40 or review.total_pnl < 0:
            suggestions["market_outlook"] = "震荡偏空"
            suggestions["position_limit"] = 30.0
            suggestions["max_trades"] = 2
            suggestions["risk_level"] = "高风险"
            suggestions["key_reminders"].append("状态不佳，建议降低仓位，减少交易")
        
        # 基于心态调整
        if review.mindset_level in (MindsetLevel.POOR, MindsetLevel.TERRIBLE):
            suggestions["position_limit"] = min(suggestions["position_limit"], 20.0)
            suggestions["max_trades"] = min(suggestions["max_trades"], 1)
            suggestions["key_reminders"].append("心态不稳，建议轻仓或空仓观望")
        
        # 基于市场数据调整
        if market_data:
            emotion_cycle = market_data.get("emotion_cycle", "")
            if emotion_cycle in ("退潮期", "冰点期"):
                suggestions["position_limit"] = min(suggestions["position_limit"], 20.0)
                suggestions["avoid_directions"].append("高位连板股")
                suggestions["key_reminders"].append("情绪退潮，注意风险")
            elif emotion_cycle in ("发酵期", "高潮期"):
                suggestions["preferred_tactics"].extend(["打板", "接力"])
        
        return suggestions
    
    # ==================== 绩效统计 ====================
    
    def calculate_performance(
        self, 
        notes: List[TradeNote], 
        days: int = 30
    ) -> Dict:
        """计算交易绩效统计
        
        Args:
            notes: 交易笔记列表
            days: 统计天数
            
        Returns:
            Dict: 绩效统计结果
        """
        if not notes:
            return {
                "total_days": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_daily_pnl": 0.0,
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "avg_score": 0.0,
            }
        
        # 过滤日期范围
        cutoff = date.today() - timedelta(days=days)
        filtered = [n for n in notes if n.date and n.date >= cutoff and n.review]
        
        total_trades = 0
        total_wins = 0
        total_pnl = 0.0
        scores = []
        
        for note in filtered:
            if note.review:
                total_trades += note.review.total_trades
                total_wins += note.review.win_count
                total_pnl += note.review.total_pnl
                if note.review.self_score > 0:
                    scores.append(note.review.self_score)
        
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0
        avg_daily_pnl = total_pnl / len(filtered) if filtered else 0.0
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # 计算连胜/连败
        max_win_streak = 0
        max_loss_streak = 0
        current_win = 0
        current_loss = 0
        
        for note in sorted(filtered, key=lambda x: x.date or date.min):
            if note.review and note.review.total_pnl > 0:
                current_win += 1
                current_loss = 0
                max_win_streak = max(max_win_streak, current_win)
            elif note.review and note.review.total_pnl < 0:
                current_loss += 1
                current_win = 0
                max_loss_streak = max(max_loss_streak, current_loss)
            else:
                current_win = 0
                current_loss = 0
        
        return {
            "total_days": len(filtered),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_daily_pnl": round(avg_daily_pnl, 2),
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
            "avg_score": round(avg_score, 1),
            "profit_days": sum(1 for n in filtered if n.review and n.review.total_pnl > 0),
            "loss_days": sum(1 for n in filtered if n.review and n.review.total_pnl < 0),
        }