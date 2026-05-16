"""模块五: 战法选股 — 短线致胜AI交易智能体

包含15套经典超短线战法的完整量化规则库和智能筛选引擎:
- tactics_library: 战法量化规则库
- screener: 4步智能筛选引擎
- resonance: 多战法共振选股
- environment_filter: 场景适配过滤

Usage:
    from short_win_ai_trader.modules.m05_tactic_screening import (
        TacticScreener, ResonanceEngine, EnvironmentFilter,
        ALL_TACTICS, list_all_tactics,
    )
"""

from .tactics_library import (
    ALL_TACTICS,
    TACTICS_BY_CYCLE,
    TACTICS_BY_HOLD_PERIOD,
    TACTICS_BY_RISK,
    get_tactic_by_code,
    get_tactic_by_name,
    get_tactics_for_cycle,
    get_tactics_summary_stats,
    list_all_tactics,
)

__all__ = [
    "ALL_TACTICS",
    "TACTICS_BY_CYCLE",
    "TACTICS_BY_HOLD_PERIOD",
    "TACTICS_BY_RISK",
    "get_tactic_by_code",
    "get_tactic_by_name",
    "get_tactics_for_cycle",
    "get_tactics_summary_stats",
    "list_all_tactics",
]
