"""交易笔记模块 — 当日复盘、次日计划、语音输入、评分决策

整合原评分决策模块(m06)和交易诊断模块(m07)的功能，提供:
1. 当日交易笔记：持仓记录、盈亏统计、交易逻辑、失误归因、心态复盘
2. 次日交易计划：大盘判断、跟踪标的、仓位管控、风控纪律
3. 语音输入支持：语音创建复盘笔记和交易计划
4. 标的评分决策：基于战法、指标对潜在标的进行评分和操作建议

模块结构:
- models.py: 数据模型定义
- note_engine.py: 交易笔记引擎（当日复盘+次日计划）
- voice_processor.py: 语音输入处理
- scoring_integration.py: 评分决策整合
- journal_manager.py: 笔记管理器（CRUD+持久化）
"""

from .models import (
    TradeNote,
    PositionRecord,
    TradeReview,
    NextDayPlan,
    WatchStock,
    VoiceNote,
)
from .note_engine import NoteEngine
from .journal_manager import JournalManager

__all__ = [
    "TradeNote",
    "PositionRecord",
    "TradeReview",
    "NextDayPlan",
    "WatchStock",
    "VoiceNote",
    "NoteEngine",
    "JournalManager",
]