"""交易风格画像 — 大数据统计 + 精准定型"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from ...core.logger import get_logger
from ...data_platform.data_models import TraderProfile, TradeRecord

logger = get_logger("swat.profiler")


class TradeProfiler:
    """交易风格画像生成器
    
    通过海量历史交易数据自动判定用户专属交易风格:
    - 风格分类: 龙头接力/分歧低吸/事件催化/趋势波段/冰点试错/首板挖掘
    - 能力圈: 擅长题材/标的/战法 vs 亏损禁区
    - 黄金时段: 早盘/午盘/尾盘
    """

    def generate_profile(self, trades: List[TradeRecord]) -> TraderProfile:
        """生成交易风格画像"""
        if not trades:
            return TraderProfile()

        total = len(trades)
        wins = [t for t in trades if t.profit_loss and t.profit_loss > 0]
        losses = [t for t in trades if t.profit_loss and t.profit_loss < 0]

        win_count = len(wins)
        win_rate = win_count / total * 100 if total > 0 else 0

        # 盈亏比
        avg_profit = sum(t.profit_loss for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t.profit_loss for t in losses) / len(losses)) if losses else 1
        profit_loss_ratio = round(avg_profit / avg_loss, 2) if avg_loss > 0 else 0

        # 最大回撤（简化计算）
        max_drawdown = self._calc_max_drawdown(trades)

        # 风格判定
        style = self._detect_style(trades)

        # 黄金时段
        golden_hour = self._detect_golden_hour(trades)

        # 题材偏好
        strength_themes, weakness_themes = self._analyze_themes(trades)

        # 模式偏好
        strength_modes, weakness_modes = self._analyze_modes(trades)

        # 高频错误
        error_patterns = self._detect_errors(trades)

        profile = TraderProfile(
            total_trades=total,
            win_rate=round(win_rate, 1),
            profit_loss_ratio=profit_loss_ratio,
            max_drawdown=round(max_drawdown, 1),
            avg_profit=round(avg_profit, 2),
            avg_loss=round(avg_loss, 2),
            style=style,
            golden_hour=golden_hour,
            strength_themes=strength_themes,
            weakness_themes=weakness_themes,
            strength_modes=strength_modes,
            weakness_modes=weakness_modes,
            error_patterns=error_patterns,
        )

        logger.info(f"交易画像生成: {total}笔交易 胜率{win_rate:.1f}% 风格:{style}")
        return profile

    def _calc_max_drawdown(self, trades: List[TradeRecord]) -> float:
        """计算最大回撤"""
        sorted_trades = sorted(trades, key=lambda t: t.trade_date or datetime.min)
        cumulative = 0
        peak = 0
        max_dd = 0

        for trade in sorted_trades:
            if trade.profit_loss:
                cumulative += trade.profit_loss
                if cumulative > peak:
                    peak = cumulative
                dd = (peak - cumulative) / peak * 100 if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd

        return max_dd

    def _detect_style(self, trades: List[TradeRecord]) -> str:
        """判定交易风格"""
        modes = Counter(t.trade_mode for t in trades if t.trade_mode)
        if not modes:
            return "未定型"

        top_mode = modes.most_common(1)[0][0]
        style_map = {
            "打板": "龙头接力型",
            "接力": "龙头接力型",
            "低吸": "分歧低吸型",
            "半路": "趋势波段型",
            "潜伏": "事件催化套利型",
            "套利": "事件催化套利型",
        }
        return style_map.get(top_mode, "综合型")

    def _detect_golden_hour(self, trades: List[TradeRecord]) -> str:
        """判定黄金出手时段"""
        hour_wins = defaultdict(lambda: {"wins": 0, "total": 0})

        for trade in trades:
            if trade.trade_date:
                hour = trade.trade_date.hour if hasattr(trade.trade_date, "hour") else 10
                if 9 <= hour <= 10:
                    slot = "早盘(9:30-10:30)"
                elif 10 < hour <= 13:
                    slot = "午盘(10:30-13:00)"
                else:
                    slot = "尾盘(14:00-15:00)"

                hour_wins[slot]["total"] += 1
                if trade.profit_loss and trade.profit_loss > 0:
                    hour_wins[slot]["wins"] += 1

        if not hour_wins:
            return "未确定"

        best_slot = max(
            hour_wins.items(),
            key=lambda x: x[1]["wins"] / x[1]["total"] if x[1]["total"] > 0 else 0,
        )
        wr = best_slot[1]["wins"] / best_slot[1]["total"] * 100 if best_slot[1]["total"] > 0 else 0
        return f"{best_slot[0]} (胜率{wr:.0f}%)"

    def _analyze_themes(self, trades: List[TradeRecord]) -> tuple:
        """分析题材偏好"""
        # 简化处理，使用stock_name分组
        theme_perf = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0})

        for trade in trades:
            # 使用ticker前缀作为"题材"分组
            prefix = trade.ticker[:4] if trade.ticker else "未知"
            theme_perf[prefix]["total"] += 1
            if trade.profit_loss:
                theme_perf[prefix]["pnl"] += trade.profit_loss
                if trade.profit_loss > 0:
                    theme_perf[prefix]["wins"] += 1

        # 按盈亏排序
        sorted_themes = sorted(theme_perf.items(), key=lambda x: x[1]["pnl"], reverse=True)
        strength = [t[0] for t in sorted_themes[:3] if t[1]["pnl"] > 0]
        weakness = [t[0] for t in sorted_themes[-3:] if t[1]["pnl"] < 0]

        return strength, weakness

    def _analyze_modes(self, trades: List[TradeRecord]) -> tuple:
        """分析模式偏好"""
        mode_perf = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0})

        for trade in trades:
            mode = trade.trade_mode or "未知"
            mode_perf[mode]["total"] += 1
            if trade.profit_loss:
                mode_perf[mode]["pnl"] += trade.profit_loss
                if trade.profit_loss > 0:
                    mode_perf[mode]["wins"] += 1

        sorted_modes = sorted(mode_perf.items(), key=lambda x: x[1]["pnl"], reverse=True)
        strength = [m[0] for m in sorted_modes[:3] if m[1]["pnl"] > 0]
        weakness = [m[0] for m in sorted_modes[-3:] if m[1]["pnl"] < 0]

        return strength, weakness

    def _detect_errors(self, trades: List[TradeRecord]) -> List[str]:
        """检测高频错误模式"""
        errors = []

        # 止损问题
        big_losses = [t for t in trades if t.profit_loss_pct and t.profit_loss_pct < -5]
        if len(big_losses) > len(trades) * 0.1:
            errors.append(f"大亏损次数过多({len(big_losses)}次)，止损执行不坚决")

        # 胜率低
        wins = [t for t in trades if t.profit_loss and t.profit_loss > 0]
        if len(wins) / len(trades) * 100 < 40:
            errors.append(f"总胜率仅{len(wins)/len(trades)*100:.0f}%，需提高选股质量")

        # 连续亏损
        consecutive_losses = 0
        max_consecutive = 0
        for t in sorted(trades, key=lambda x: x.trade_date or datetime.min):
            if t.profit_loss and t.profit_loss < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0

        if max_consecutive >= 3:
            errors.append(f"最大连续亏损{max_consecutive}次，需设置强制休息机制")

        return errors
