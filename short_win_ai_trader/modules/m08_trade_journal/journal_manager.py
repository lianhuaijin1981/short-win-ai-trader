"""交易笔记管理器 — CRUD操作与持久化存储

提供:
1. 交易笔记的增删改查
2. JSON文件持久化存储
3. 笔记搜索与过滤
4. 数据导入导出
"""

import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...core.logger import get_logger
from .models import (
    NextDayPlan,
    TradeNote,
    TradeReview,
    VoiceNote,
)
from .note_engine import NoteEngine

logger = get_logger("swat.m08.journal_manager")


class DateTimeEncoder(json.JSONEncoder):
    """JSON编码器 — 支持date和datetime序列化"""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if hasattr(obj, '__dataclass_fields__'):
            # 处理dataclass
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, (date, datetime)):
                    result[field_name] = value.isoformat()
                elif hasattr(value, 'value'):  # Enum
                    result[field_name] = value.value
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self.default(value)
                elif isinstance(value, list):
                    result[field_name] = [
                        self.default(item) if hasattr(item, '__dataclass_fields__') else item
                        for item in value
                    ]
                else:
                    result[field_name] = value
            return result
        return super().default(obj)


class JournalManager:
    """交易笔记管理器
    
    负责交易笔记的存储、检索、更新和删除。
    使用JSON文件作为持久化存储。
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """初始化笔记管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.engine = NoteEngine()
        
        # 设置数据目录
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 默认使用用户home目录下的.swat/journal
            self.data_dir = Path.home() / ".swat" / "journal"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 笔记缓存
        self._notes_cache: Dict[str, TradeNote] = {}
        self._voice_cache: Dict[str, VoiceNote] = {}
        
        # 加载所有笔记
        self._load_all_notes()
        
        logger.info(f"交易笔记管理器初始化完成，数据目录: {self.data_dir}")
    
    # ==================== 笔记CRUD ====================
    
    def create_note(
        self,
        review_data: Optional[Dict] = None,
        plan_data: Optional[Dict] = None,
        source: str = "manual",
        tags: Optional[List[str]] = None,
        voice_note_id: Optional[str] = None,
        note_date: Optional[str] = None,
    ) -> TradeNote:
        """创建交易笔记
        
        Args:
            review_data: 复盘数据（字典）
            plan_data: 计划数据（字典）
            source: 来源
            tags: 标签
            voice_note_id: 关联语音笔记ID
            note_date: 笔记日期（ISO格式字符串）
            
        Returns:
            TradeNote: 创建的交易笔记
        """
        # 创建复盘
        review = None
        if review_data:
            positions = review_data.get("positions", [])
            review = self.engine.create_review(
                positions=positions,
                mindset_level=review_data.get("mindset_level", "一般"),
                mindset_summary=review_data.get("mindset_summary", ""),
                rhythm_summary=review_data.get("rhythm_summary", ""),
                discipline_summary=review_data.get("discipline_summary", ""),
                mindset_issues=review_data.get("mindset_issues", []),
                rhythm_issues=review_data.get("rhythm_issues", []),
                discipline_issues=review_data.get("discipline_issues", []),
                lessons_learned=review_data.get("lessons_learned", []),
                improvements=review_data.get("improvements", []),
                overall_summary=review_data.get("overall_summary", ""),
                self_score=review_data.get("self_score", 0.0),
                review_date=date.fromisoformat(note_date) if note_date else None,
            )
        
        # 创建计划
        next_day_plan = None
        if plan_data:
            next_day_plan = self.engine.create_next_day_plan(
                market_outlook=plan_data.get("market_outlook", "震荡中性"),
                market_reasoning=plan_data.get("market_reasoning", ""),
                key_levels=plan_data.get("key_levels", ""),
                watch_stocks=plan_data.get("watch_stocks", []),
                total_position_limit=plan_data.get("total_position_limit", 50.0),
                single_stock_limit=plan_data.get("single_stock_limit", 20.0),
                max_trades=plan_data.get("max_trades", 3),
                position_plan=plan_data.get("position_plan", ""),
                stop_loss_rule=plan_data.get("stop_loss_rule", ""),
                take_profit_rule=plan_data.get("take_profit_rule", ""),
                max_daily_loss=plan_data.get("max_daily_loss", 3.0),
                risk_rules=plan_data.get("risk_rules", []),
                risk_directions=plan_data.get("risk_directions", []),
                avoid_sectors=plan_data.get("avoid_sectors", []),
                avoid_stocks=plan_data.get("avoid_stocks", []),
                preferred_sectors=plan_data.get("preferred_sectors", []),
                preferred_tactics=plan_data.get("preferred_tactics", []),
                notes=plan_data.get("notes", ""),
                plan_date=date.fromisoformat(note_date) if note_date else None,
            )
        
        # 创建完整笔记
        note = self.engine.create_trade_note(
            review=review,
            next_day_plan=next_day_plan,
            source=source,
            tags=tags,
            voice_note_id=voice_note_id,
            note_date=date.fromisoformat(note_date) if note_date else None,
        )
        
        # 保存
        self._save_note(note)
        
        logger.info(f"创建交易笔记成功: ID={note.id}")
        return note
    
    def get_note(self, note_id: str) -> Optional[TradeNote]:
        """获取指定笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            TradeNote或None
        """
        # 先查缓存
        if note_id in self._notes_cache:
            return self._notes_cache[note_id]
        
        # 从文件加载
        note_file = self.data_dir / f"{note_id}.json"
        if note_file.exists():
            note = self._load_note_from_file(note_file)
            if note:
                self._notes_cache[note_id] = note
                return note
        
        return None
    
    def get_note_by_date(self, note_date: str) -> Optional[TradeNote]:
        """按日期获取笔记
        
        Args:
            note_date: 日期（ISO格式，如"2024-01-15"）
            
        Returns:
            TradeNote或None
        """
        target_date = date.fromisoformat(note_date)
        for note in self._notes_cache.values():
            if note.date == target_date:
                return note
        
        # 从文件搜索
        for note_file in self.data_dir.glob("*.json"):
            note = self._load_note_from_file(note_file)
            if note and note.date == target_date:
                self._notes_cache[note.id] = note
                return note
        
        return None
    
    def list_notes(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """列出笔记（支持过滤和分页）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            tag: 标签过滤
            source: 来源过滤
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            笔记摘要列表
        """
        notes = list(self._notes_cache.values())
        
        # 日期过滤
        if start_date:
            sd = date.fromisoformat(start_date)
            notes = [n for n in notes if n.date and n.date >= sd]
        if end_date:
            ed = date.fromisoformat(end_date)
            notes = [n for n in notes if n.date and n.date <= ed]
        
        # 标签过滤
        if tag:
            notes = [n for n in notes if tag in n.tags]
        
        # 来源过滤
        if source:
            notes = [n for n in notes if n.source == source]
        
        # 按日期降序
        notes.sort(key=lambda x: x.date or date.min, reverse=True)
        
        # 分页
        notes = notes[offset:offset + limit]
        
        # 返回摘要
        return [self._note_to_summary(n) for n in notes]
    
    def update_note(
        self,
        note_id: str,
        review_data: Optional[Dict] = None,
        plan_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[TradeNote]:
        """更新笔记
        
        Args:
            note_id: 笔记ID
            review_data: 更新的复盘数据
            plan_data: 更新的计划数据
            tags: 更新的标签
            
        Returns:
            更新后的TradeNote或None
        """
        note = self.get_note(note_id)
        if not note:
            logger.warning(f"笔记不存在: {note_id}")
            return None
        
        # 更新复盘
        if review_data:
            positions = review_data.get("positions", [])
            note.review = self.engine.create_review(
                positions=positions,
                mindset_level=review_data.get("mindset_level", "一般"),
                mindset_summary=review_data.get("mindset_summary", ""),
                rhythm_summary=review_data.get("rhythm_summary", ""),
                discipline_summary=review_data.get("discipline_summary", ""),
                mindset_issues=review_data.get("mindset_issues", []),
                rhythm_issues=review_data.get("rhythm_issues", []),
                discipline_issues=review_data.get("discipline_issues", []),
                lessons_learned=review_data.get("lessons_learned", []),
                improvements=review_data.get("improvements", []),
                overall_summary=review_data.get("overall_summary", ""),
                self_score=review_data.get("self_score", 0.0),
                review_date=note.date,
            )
        
        # 更新计划
        if plan_data:
            note.next_day_plan = self.engine.create_next_day_plan(
                market_outlook=plan_data.get("market_outlook", "震荡中性"),
                market_reasoning=plan_data.get("market_reasoning", ""),
                key_levels=plan_data.get("key_levels", ""),
                watch_stocks=plan_data.get("watch_stocks", []),
                total_position_limit=plan_data.get("total_position_limit", 50.0),
                single_stock_limit=plan_data.get("single_stock_limit", 20.0),
                max_trades=plan_data.get("max_trades", 3),
                position_plan=plan_data.get("position_plan", ""),
                stop_loss_rule=plan_data.get("stop_loss_rule", ""),
                take_profit_rule=plan_data.get("take_profit_rule", ""),
                max_daily_loss=plan_data.get("max_daily_loss", 3.0),
                risk_rules=plan_data.get("risk_rules", []),
                risk_directions=plan_data.get("risk_directions", []),
                avoid_sectors=plan_data.get("avoid_sectors", []),
                avoid_stocks=plan_data.get("avoid_stocks", []),
                preferred_sectors=plan_data.get("preferred_sectors", []),
                preferred_tactics=plan_data.get("preferred_tactics", []),
                notes=plan_data.get("notes", ""),
                plan_date=note.date,
            )
        
        # 更新标签
        if tags is not None:
            note.tags = tags
        
        # 更新时间
        note.updated_at = datetime.now()
        
        # 保存
        self._save_note(note)
        
        logger.info(f"更新笔记成功: ID={note_id}")
        return note
    
    def delete_note(self, note_id: str) -> bool:
        """删除笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            是否成功删除
        """
        note_file = self.data_dir / f"{note_id}.json"
        if note_file.exists():
            note_file.unlink()
            self._notes_cache.pop(note_id, None)
            logger.info(f"删除笔记成功: ID={note_id}")
            return True
        
        logger.warning(f"笔记不存在，无法删除: {note_id}")
        return False
    
    # ==================== 笔记分析 ====================
    
    def analyze_note(self, note_id: str) -> Optional[Dict]:
        """分析指定笔记
        
        Args:
            note_id: 笔记ID
            
        Returns:
            分析结果或None
        """
        note = self.get_note(note_id)
        if not note or not note.review:
            return None
        
        return self.engine.analyze_review(note.review)
    
    def get_performance(self, days: int = 30) -> Dict:
        """获取交易绩效统计
        
        Args:
            days: 统计天数
            
        Returns:
            绩效统计结果
        """
        notes = list(self._notes_cache.values())
        return self.engine.calculate_performance(notes, days)
    
    def get_plan_suggestions(self, note_id: str, market_data: Optional[Dict] = None) -> Optional[Dict]:
        """获取次日计划建议
        
        Args:
            note_id: 笔记ID
            market_data: 市场数据
            
        Returns:
            计划建议或None
        """
        note = self.get_note(note_id)
        if not note or not note.review:
            return None
        
        return self.engine.generate_plan_suggestions(note.review, market_data)
    
    # ==================== 内部方法 ====================
    
    def _save_note(self, note: TradeNote) -> None:
        """保存笔记到文件"""
        note_file = self.data_dir / f"{note.id}.json"
        try:
            with open(note_file, 'w', encoding='utf-8') as f:
                json.dump(note, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
            self._notes_cache[note.id] = note
        except Exception as e:
            logger.error(f"保存笔记失败: {e}")
    
    def _load_note_from_file(self, note_file: Path) -> Optional[TradeNote]:
        """从文件加载笔记"""
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析日期
            note_date = None
            if data.get("date"):
                note_date = date.fromisoformat(data["date"])
            
            created_at = None
            if data.get("created_at"):
                created_at = datetime.fromisoformat(data["created_at"])
            
            updated_at = None
            if data.get("updated_at"):
                updated_at = datetime.fromisoformat(data["updated_at"])
            
            # 解析复盘
            review = None
            if data.get("review"):
                review_data = data["review"]
                review_date = None
                if review_data.get("date"):
                    review_date = date.fromisoformat(review_data["date"])
                
                positions = []
                for p in review_data.get("positions", []):
                    positions.append(p)
                
                review = self.engine.create_review(
                    positions=positions,
                    mindset_level=review_data.get("mindset_level", "一般"),
                    mindset_summary=review_data.get("mindset_summary", ""),
                    rhythm_summary=review_data.get("rhythm_summary", ""),
                    discipline_summary=review_data.get("discipline_summary", ""),
                    mindset_issues=review_data.get("mindset_issues", []),
                    rhythm_issues=review_data.get("rhythm_issues", []),
                    discipline_issues=review_data.get("discipline_issues", []),
                    lessons_learned=review_data.get("lessons_learned", []),
                    improvements=review_data.get("improvements", []),
                    overall_summary=review_data.get("overall_summary", ""),
                    self_score=review_data.get("self_score", 0.0),
                    review_date=review_date,
                )
            
            # 解析计划
            next_day_plan = None
            if data.get("next_day_plan"):
                plan_data = data["next_day_plan"]
                next_day_plan = self.engine.create_next_day_plan(
                    market_outlook=plan_data.get("market_outlook", "震荡中性"),
                    market_reasoning=plan_data.get("market_reasoning", ""),
                    key_levels=plan_data.get("key_levels", ""),
                    watch_stocks=plan_data.get("watch_stocks", []),
                    total_position_limit=plan_data.get("total_position_limit", 50.0),
                    single_stock_limit=plan_data.get("single_stock_limit", 20.0),
                    max_trades=plan_data.get("max_trades", 3),
                    position_plan=plan_data.get("position_plan", ""),
                    stop_loss_rule=plan_data.get("stop_loss_rule", ""),
                    take_profit_rule=plan_data.get("take_profit_rule", ""),
                    max_daily_loss=plan_data.get("max_daily_loss", 3.0),
                    risk_rules=plan_data.get("risk_rules", []),
                    risk_directions=plan_data.get("risk_directions", []),
                    avoid_sectors=plan_data.get("avoid_sectors", []),
                    avoid_stocks=plan_data.get("avoid_stocks", []),
                    preferred_sectors=plan_data.get("preferred_sectors", []),
                    preferred_tactics=plan_data.get("preferred_tactics", []),
                    notes=plan_data.get("notes", ""),
                )
            
            note = TradeNote(
                id=data.get("id", ""),
                date=note_date,
                review=review,
                next_day_plan=next_day_plan,
                created_at=created_at,
                updated_at=updated_at,
                source=data.get("source", "manual"),
                tags=data.get("tags", []),
                voice_note_id=data.get("voice_note_id"),
            )
            
            return note
            
        except Exception as e:
            logger.error(f"加载笔记失败 {note_file}: {e}")
            return None
    
    def _load_all_notes(self) -> None:
        """加载所有笔记到缓存"""
        try:
            for note_file in self.data_dir.glob("*.json"):
                note = self._load_note_from_file(note_file)
                if note:
                    self._notes_cache[note.id] = note
            logger.info(f"加载了 {len(self._notes_cache)} 条笔记")
        except Exception as e:
            logger.error(f"加载笔记失败: {e}")
    
    def _note_to_summary(self, note: TradeNote) -> Dict:
        """将笔记转换为摘要格式"""
        summary = {
            "id": note.id,
            "date": note.date.isoformat() if note.date else None,
            "source": note.source,
            "tags": note.tags,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        }
        
        if note.review:
            summary["review"] = {
                "total_trades": note.review.total_trades,
                "win_rate": note.review.win_rate,
                "total_pnl": note.review.total_pnl,
                "total_pnl_pct": note.review.total_pnl_pct,
                "mindset_level": note.review.mindset_level.value,
                "self_score": note.review.self_score,
            }
        
        if note.next_day_plan:
            summary["next_day_plan"] = {
                "market_outlook": note.next_day_plan.market_outlook.value,
                "watch_stocks_count": len(note.next_day_plan.watch_stocks),
                "total_position_limit": note.next_day_plan.total_position_limit,
            }
        
        return summary