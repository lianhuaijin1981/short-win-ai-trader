"""交易画像分析器

对用户的交易行为进行客观评价:
- 交易统计: 总交易数、胜率、盈亏比、平均收益
- 风格判定: 龙头接力型/分歧低吸型/趋势波段型/事件催化型
- 模式分析: 各交易模式的胜率和盈亏
- 时段分析: 不同时段交易表现
- 题材偏好: 偏好题材及表现
- 情绪周期适配: 不同情绪周期下的表现
- 仓位管理: 仓位使用合理性
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .importer import TradeRecord

logger = get_logger("swat.m07.profiler")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class TradeProfile:
    """交易画像"""
    # 基本信息
    total_trades: int = 0               # 总交易数
    win_trades: int = 0                 # 盈利交易数
    loss_trades: int = 0                # 亏损交易数
    win_rate: float = 0.0               # 胜率(%)
    
    # 盈亏统计
    total_profit: float = 0.0           # 总盈利
    total_loss: float = 0.0             # 总亏损
    net_profit: float = 0.0             # 净利润
    profit_loss_ratio: float = 0.0      # 盈亏比
    avg_profit: float = 0.0             # 平均盈利
    avg_loss: float = 0.0               # 平均亏损
    avg_return: float = 0.0             # 平均收益率(%)
    
    # 最大回撤
    max_drawdown: float = 0.0           # 最大回撤(%)
    max_drawdown_days: int = 0          # 最大回撤天数
    max_consecutive_wins: int = 0       # 最大连胜
    max_consecutive_losses: int = 0     # 最大连亏
    
    # 风格特征
    style: str = ""                     # 交易风格
    style_confidence: float = 0.0       # 风格置信度
    
    # 模式分析
    mode_stats: Dict = field(default_factory=dict)  # 各模式统计
    
    # 情绪周期分析
    emotion_stats: Dict = field(default_factory=dict)  # 各情绪周期统计
    
    # 题材偏好
    theme_preferences: Dict = field(default_factory=dict)  # 题材偏好
    
    # 时段分析
    time_stats: Dict = field(default_factory=dict)  # 时段统计
    
    # 持仓分析
    avg_hold_days: float = 0.0          # 平均持仓天数
    hold_days_distribution: Dict = field(default_factory=dict)  # 持仓天数分布
    
    # 综合评分
    overall_score: float = 0.0          # 综合评分(0-100)
    strengths: List[str] = field(default_factory=list)  # 优势
    weaknesses: List[str] = field(default_factory=list)  # 劣势
    
    # 画像摘要
    summary: str = ""


# ── 画像分析器 ───────────────────────────────────────────

class TradeProfiler:
    """交易画像分析器
    
    对交易记录进行全面分析，生成客观评价。
    """
    
    def __init__(self):
        """初始化画像分析器"""
        logger.info("交易画像分析器初始化完成")
    
    def generate_profile(self, trades: List[TradeRecord]) -> TradeProfile:
        """生成交易画像
        
        Args:
            trades: 交易记录列表
            
        Returns:
            TradeProfile: 交易画像
        """
        if not trades:
            logger.warning("无交易记录，无法生成画像")
            return TradeProfile()
        
        logger.info(f"开始生成交易画像: {len(trades)}笔交易")
        
        profile = TradeProfile()
        
        # 基本统计
        self._calc_basic_stats(trades, profile)
        
        # 盈亏统计
        self._calc_pnl_stats(trades, profile)
        
        # 回撤分析
        self._calc_drawdown(trades, profile)
        
        # 风格判定
        self._detect_style(trades, profile)
        
        # 模式分析
        self._analyze_modes(trades, profile)
        
        # 情绪周期分析
        self._analyze_emotion_cycles(trades, profile)
        
        # 题材偏好
        self._analyze_themes(trades, profile)
        
        # 持仓分析
        self._analyze_hold_days(trades, profile)
        
        # 综合评分
        self._calc_overall_score(profile)
        
        # 优劣势分析
        self._analyze_strengths_weaknesses(profile)
        
        # 生成摘要
        profile.summary = self._build_summary(profile)
        
        logger.info(f"画像生成完成: 胜率{profile.win_rate:.1f}% 盈亏比{profile.profit_loss_ratio:.2f}")
        return profile
    
    # ==================== 统计计算 ====================
    
    def _calc_basic_stats(self, trades: List[TradeRecord], profile: TradeProfile):
        """计算基本统计"""
        profile.total_trades = len(trades)
        profile.win_trades = sum(1 for t in trades if t.profit_loss > 0)
        profile.loss_trades = sum(1 for t in trades if t.profit_loss < 0)
        profile.win_rate = round(profile.win_trades / profile.total_trades * 100, 1) if profile.total_trades > 0 else 0
    
    def _calc_pnl_stats(self, trades: List[TradeRecord], profile: TradeProfile):
        """计算盈亏统计"""
        profits = [t.profit_loss for t in trades if t.profit_loss > 0]
        losses = [t.profit_loss for t in trades if t.profit_loss < 0]
        
        profile.total_profit = sum(profits)
        profile.total_loss = sum(losses)
        profile.net_profit = profile.total_profit + profile.total_loss
        
        profile.avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
        profile.avg_loss = round(sum(losses) / len(losses), 2) if losses else 0
        
        # 盈亏比 = 平均盈利 / |平均亏损|
        if profile.avg_loss != 0:
            profile.profit_loss_ratio = round(abs(profile.avg_profit / profile.avg_loss), 2)
        
        # 平均收益率
        returns = [t.profit_loss_pct for t in trades if t.amount > 0]
        profile.avg_return = round(sum(returns) / len(returns), 2) if returns else 0
        
        # 连胜连亏
        profile.max_consecutive_wins = self._calc_max_consecutive(trades, True)
        profile.max_consecutive_losses = self._calc_max_consecutive(trades, False)
    
    def _calc_max_consecutive(self, trades: List[TradeRecord], is_win: bool) -> int:
        """计算最大连胜/连亏"""
        max_count = 0
        current_count = 0
        
        sorted_trades = sorted(trades, key=lambda t: t.trade_date or datetime.min)
        
        for trade in sorted_trades:
            if (trade.profit_loss > 0) == is_win:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def _calc_drawdown(self, trades: List[TradeRecord], profile: TradeProfile):
        """计算最大回撤"""
        if not trades:
            return
        
        sorted_trades = sorted(trades, key=lambda t: t.trade_date or datetime.min)
        
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in sorted_trades:
            cumulative += trade.profit_loss_pct
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        profile.max_drawdown = round(max_dd, 2)
    
    # ==================== 风格判定 ====================
    
    def _detect_style(self, trades: List[TradeRecord], profile: TradeProfile):
        """判定交易风格"""
        mode_counts: Dict[str, int] = {}
        for trade in trades:
            mode = trade.trade_mode or "其他"
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if not mode_counts:
            profile.style = "未定型"
            profile.style_confidence = 0
            return
        
        # 主导模式
        dominant_mode = max(mode_counts, key=mode_counts.get)
        dominant_ratio = mode_counts[dominant_mode] / len(trades)
        
        # 风格映射
        style_map = {
            "打板": "龙头接力型",
            "接力": "龙头接力型",
            "低吸": "分歧低吸型",
            "半路": "趋势波段型",
            "其他": "综合型",
        }
        
        profile.style = style_map.get(dominant_mode, "综合型")
        profile.style_confidence = round(dominant_ratio * 100, 1)
        
        # 如果主导模式占比<40%，判定为综合型
        if dominant_ratio < 0.4:
            profile.style = "综合型"
            profile.style_confidence = round((1 - dominant_ratio) * 50, 1)
    
    # ==================== 模式分析 ====================
    
    def _analyze_modes(self, trades: List[TradeRecord], profile: TradeProfile):
        """分析各交易模式表现"""
        mode_trades: Dict[str, List[TradeRecord]] = {}
        
        for trade in trades:
            mode = trade.trade_mode or "其他"
            if mode not in mode_trades:
                mode_trades[mode] = []
            mode_trades[mode].append(trade)
        
        for mode, mode_trade_list in mode_trades.items():
            wins = sum(1 for t in mode_trade_list if t.profit_loss > 0)
            total = len(mode_trade_list)
            pnl = sum(t.profit_loss for t in mode_trade_list)
            
            profile.mode_stats[mode] = {
                "count": total,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "total_pnl": round(pnl, 2),
                "avg_pnl": round(pnl / total, 2) if total > 0 else 0,
            }
    
    # ==================== 情绪周期分析 ====================
    
    def _analyze_emotion_cycles(self, trades: List[TradeRecord], profile: TradeProfile):
        """分析各情绪周期表现"""
        cycle_trades: Dict[str, List[TradeRecord]] = {}
        
        for trade in trades:
            cycle = trade.emotion_cycle or "未知"
            if cycle not in cycle_trades:
                cycle_trades[cycle] = []
            cycle_trades[cycle].append(trade)
        
        for cycle, cycle_trade_list in cycle_trades.items():
            wins = sum(1 for t in cycle_trade_list if t.profit_loss > 0)
            total = len(cycle_trade_list)
            pnl = sum(t.profit_loss for t in cycle_trade_list)
            
            profile.emotion_stats[cycle] = {
                "count": total,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "total_pnl": round(pnl, 2),
                "avg_pnl": round(pnl / total, 2) if total > 0 else 0,
            }
    
    # ==================== 题材分析 ====================
    
    def _analyze_themes(self, trades: List[TradeRecord], profile: TradeProfile):
        """分析题材偏好"""
        theme_trades: Dict[str, List[TradeRecord]] = {}
        
        for trade in trades:
            theme = trade.theme_name or "未分类"
            if theme not in theme_trades:
                theme_trades[theme] = []
            theme_trades[theme].append(trade)
        
        for theme, theme_trade_list in theme_trades.items():
            wins = sum(1 for t in theme_trade_list if t.profit_loss > 0)
            total = len(theme_trade_list)
            pnl = sum(t.profit_loss for t in theme_trade_list)
            
            profile.theme_preferences[theme] = {
                "count": total,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "total_pnl": round(pnl, 2),
            }
    
    # ==================== 持仓分析 ====================
    
    def _analyze_hold_days(self, trades: List[TradeRecord], profile: TradeProfile):
        """分析持仓天数"""
        hold_days = [t.hold_days for t in trades if t.hold_days > 0]
        
        if hold_days:
            profile.avg_hold_days = round(sum(hold_days) / len(hold_days), 1)
            
            # 分布
            distribution = {"1天": 0, "2-3天": 0, "4-5天": 0, "5天以上": 0}
            for days in hold_days:
                if days == 1:
                    distribution["1天"] += 1
                elif days <= 3:
                    distribution["2-3天"] += 1
                elif days <= 5:
                    distribution["4-5天"] += 1
                else:
                    distribution["5天以上"] += 1
            
            profile.hold_days_distribution = distribution
    
    # ==================== 综合评分 ====================
    
    def _calc_overall_score(self, profile: TradeProfile):
        """计算综合评分"""
        score = 50  # 基础分
        
        # 胜率评分(0-20)
        if profile.win_rate >= 60:
            score += 20
        elif profile.win_rate >= 50:
            score += 15
        elif profile.win_rate >= 40:
            score += 10
        else:
            score += 5
        
        # 盈亏比评分(0-20)
        if profile.profit_loss_ratio >= 3:
            score += 20
        elif profile.profit_loss_ratio >= 2:
            score += 15
        elif profile.profit_loss_ratio >= 1.5:
            score += 10
        else:
            score += 5
        
        # 净利润评分(0-10)
        if profile.net_profit > 0:
            score += 10
        else:
            score -= 5
        
        # 回撤控制(0-10)
        if profile.max_drawdown < 10:
            score += 10
        elif profile.max_drawdown < 20:
            score += 5
        
        profile.overall_score = max(0, min(100, score))
    
    def _analyze_strengths_weaknesses(self, profile: TradeProfile):
        """分析优劣势"""
        # 优势
        if profile.win_rate >= 55:
            profile.strengths.append(f"胜率较高({profile.win_rate}%)")
        if profile.profit_loss_ratio >= 2:
            profile.strengths.append(f"盈亏比优秀({profile.profit_loss_ratio})")
        if profile.max_drawdown < 15:
            profile.strengths.append(f"回撤控制良好({profile.max_drawdown}%)")
        if profile.avg_return > 0:
            profile.strengths.append(f"平均收益为正({profile.avg_return}%)")
        
        # 最佳模式
        if profile.mode_stats:
            best_mode = max(profile.mode_stats.items(), key=lambda x: x[1].get("win_rate", 0))
            if best_mode[1]["win_rate"] >= 60:
                profile.strengths.append(f"{best_mode[0]}模式胜率高({best_mode[1]['win_rate']}%)")
        
        # 劣势
        if profile.win_rate < 40:
            profile.weaknesses.append(f"胜率偏低({profile.win_rate}%)，需提高选股能力")
        if profile.profit_loss_ratio < 1.5:
            profile.weaknesses.append(f"盈亏比不足({profile.profit_loss_ratio})，需优化止损止盈")
        if profile.max_drawdown > 20:
            profile.weaknesses.append(f"回撤过大({profile.max_drawdown}%)，需加强风控")
        if profile.net_profit < 0:
            profile.weaknesses.append("总体亏损，需系统性改进交易策略")
        
        # 最差模式
        if profile.mode_stats:
            worst_mode = min(profile.mode_stats.items(), key=lambda x: x[1].get("win_rate", 100))
            if worst_mode[1]["win_rate"] < 35:
                profile.weaknesses.append(f"{worst_mode[0]}模式胜率低({worst_mode[1]['win_rate']}%)，建议减少使用")
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, profile: TradeProfile) -> str:
        """构建画像摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║         交易画像分析报告              ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        # 基本统计
        parts.append(f"📊 交易统计:")
        parts.append(f"   总交易: {profile.total_trades}笔 | 盈利: {profile.win_trades}笔 | 亏损: {profile.loss_trades}笔")
        parts.append(f"   胜率: {profile.win_rate}% | 盈亏比: {profile.profit_loss_ratio}")
        parts.append(f"   净利润: {profile.net_profit:.2f}元 | 平均收益: {profile.avg_return}%")
        parts.append("")
        
        # 风格
        parts.append(f"🎯 交易风格: {profile.style} (置信度{profile.style_confidence}%)")
        parts.append("")
        
        # 模式表现
        if profile.mode_stats:
            parts.append("📈 模式表现:")
            for mode, stats in profile.mode_stats.items():
                parts.append(f"   {mode}: {stats['count']}笔 胜率{stats['win_rate']}% 盈亏{stats['total_pnl']:.0f}元")
            parts.append("")
        
        # 回撤
        parts.append(f"📉 最大回撤: {profile.max_drawdown}% | 最大连胜: {profile.max_consecutive_wins} | 最大连亏: {profile.max_consecutive_losses}")
        parts.append("")
        
        # 综合评分
        score_bar = "█" * int(profile.overall_score / 5) + "░" * (20 - int(profile.overall_score / 5))
        parts.append(f"⭐ 综合评分: {score_bar} {profile.overall_score}分")
        parts.append("")
        
        # 优势
        if profile.strengths:
            parts.append("✅ 优势:")
            for s in profile.strengths:
                parts.append(f"   • {s}")
            parts.append("")
        
        # 劣势
        if profile.weaknesses:
            parts.append("⚠️ 劣势:")
            for w in profile.weaknesses:
                parts.append(f"   • {w}")
        
        return "\n".join(parts)