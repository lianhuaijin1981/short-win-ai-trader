"""分时段提醒模块 — 盘中看盘核心组件

覆盖A股交易4个关键时段的智能提醒系统:
1. 集合竞价 (09:15-09:25) — 隔夜情绪+竞价异动
2. 开盘黄金30分 (09:30-10:00) — 方向选择+资金主攻
3. 盘中震荡 (10:00-14:00) — 趋势维持+异动监测
4. 尾盘 (14:00-15:00) — 次日预期+持仓决策

每个时段根据市场状态生成针对性提醒内容，
帮助交易者把握关键时间节点。
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    ExpectationLevel,
    FundFlowReport,
    SessionAlert,
)

logger = get_logger("swat.m03.session_alerts")


# ── 常量定义 ────────────────────────────────────────────

# 时段定义
SESSION_AUCTION_START = time(9, 15)     # 集合竞价开始
SESSION_AUCTION_END = time(9, 25)       # 集合竞价结束
SESSION_OPEN_START = time(9, 30)        # 开盘
SESSION_OPEN_END = time(10, 0)          # 开盘30分结束
SESSION_MIDDAY_START = time(10, 0)      # 盘中开始
SESSION_MIDDAY_END = time(14, 0)        # 尾盘前
SESSION_CLOSE_START = time(14, 0)       # 尾盘开始
SESSION_CLOSE_END = time(15, 0)         # 收盘

# 提醒优先级
PRIORITY_HIGH = "high"
PRIORITY_NORMAL = "normal"
PRIORITY_LOW = "low"


class SessionType(str, Enum):
    """时段类型"""
    AUCTION = "集合竞价"
    OPEN_30MIN = "开盘黄金30分"
    MIDDAY = "盘中震荡"
    CLOSE = "尾盘"
    UNKNOWN = "未知时段"


@dataclass
class AuctionAnalysis:
    """集合竞价分析结果"""
    overnight_sentiment: str = ""       # 隔夜情绪
    index_fair_value: str = ""          # 指数公允价值判断
    unusual_preOpens: List[Dict] = field(default_factory=list)  # 竞价异动股
    hot_sector_preview: str = ""        # 热点板块预览
    risk_signs: List[str] = field(default_factory=list)  # 风险信号
    recommendation: str = ""            # 操作建议


@dataclass
class Open30MinAnalysis:
    """开盘30分钟分析结果"""
    direction: str = ""                 # 方向选择: 向上/向下/震荡
    leading_sectors: List[str] = field(default_factory=list)  # 主攻板块
    dragon_performance: str = ""        # 龙头表现
    volume_assessment: str = ""         # 量能评估
    key_support_resistance: str = ""    # 关键支撑阻力
    operation_plan: str = ""            # 操作计划


@dataclass
class MiddayAnalysis:
    """盘中震荡分析结果"""
    trend_status: str = ""              # 趋势状态
    new_alerts: List[str] = field(default_factory=list)  # 新异动
    cooling_sectors: List[str] = field(default_factory=list)  # 冷却板块
    afternoon_preview: str = ""         # 下午展望
    risk_reminders: List[str] = field(default_factory=list)  # 风险提醒


@dataclass
class CloseAnalysis:
    """尾盘分析结果"""
    day_summary: str = ""               # 当日总结
    next_day_outlook: str = ""          # 次日展望
    position_advice: str = ""           # 持仓建议
    overnight_risk: str = ""            # 隔夜风险
    key_watch_list: List[str] = field(default_factory=list)  # 重点观察


class SessionAlertManager:
    """分时段提醒管理器

    根据当前交易时段，自动生成针对性的盘中提醒。

    Attributes:
        config: 应用配置
        _session_history: 历史提醒缓存
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化分时段提醒管理器

        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._session_history: Dict[SessionType, List[SessionAlert]] = {
            SessionType.AUCTION: [],
            SessionType.OPEN_30MIN: [],
            SessionType.MIDDAY: [],
            SessionType.CLOSE: [],
        }
        logger.info("分时段提醒管理器初始化完成")

    # ==================== 核心公共接口 ====================

    async def generate_session_alert(
        self,
        anchors: List[AnchorStock],
        fund_report: Optional[FundFlowReport] = None,
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """生成分时段提醒 — 主入口

        根据当前时间判断交易时段，生成对应提醒。

        Args:
            anchors: 锚定标的列表
            fund_report: 资金流向报告
            market_summary: 市场摘要数据

        Returns:
            SessionAlert: 当前时段提醒

        Raises:
            ModuleError: 生成过程发生严重错误
        """
        now = datetime.now()
        session_type = self._determine_session(now)

        logger.info(f"========== 生成{session_type.value}时段提醒 ==========")

        try:
            if session_type == SessionType.AUCTION:
                alert = self._generate_auction_alert(anchors, market_summary)
            elif session_type == SessionType.OPEN_30MIN:
                alert = self._generate_open_alert(anchors, fund_report, market_summary)
            elif session_type == SessionType.MIDDAY:
                alert = self._generate_midday_alert(anchors, fund_report, market_summary)
            elif session_type == SessionType.CLOSE:
                alert = self._generate_close_alert(anchors, fund_report, market_summary)
            else:
                alert = SessionAlert(
                    session="休市",
                    timestamp=now,
                    content="当前非交易时段",
                    priority=PRIORITY_LOW,
                )

            # 缓存
            if session_type in self._session_history:
                self._session_history[session_type].append(alert)
                # 只保留最近5条
                if len(self._session_history[session_type]) > 5:
                    self._session_history[session_type] = self._session_history[session_type][-5:]

            return alert

        except Exception as e:
            logger.error(f"时段提醒生成严重错误: {e}")
            raise ModuleError(f"时段提醒生成失败: {e}")

    def get_current_session(self) -> SessionType:
        """获取当前交易时段

        Returns:
            SessionType: 当前时段类型
        """
        return self._determine_session(datetime.now())

    def get_session_history(self, session_type: SessionType) -> List[SessionAlert]:
        """获取指定时段的历史提醒

        Args:
            session_type: 时段类型

        Returns:
            List[SessionAlert]: 历史提醒列表
        """
        return self._session_history.get(session_type, []).copy()

    # ==================== 时段判定 ====================

    def _determine_session(self, dt: datetime) -> SessionType:
        """根据时间判定交易时段

        Args:
            dt: 当前时间

        Returns:
            SessionType: 时段类型
        """
        t = dt.time()

        if SESSION_AUCTION_START <= t <= SESSION_AUCTION_END:
            return SessionType.AUCTION
        elif SESSION_OPEN_START <= t <= SESSION_OPEN_END:
            return SessionType.OPEN_30MIN
        elif SESSION_MIDDAY_START <= t <= SESSION_MIDDAY_END:
            return SessionType.MIDDAY
        elif SESSION_CLOSE_START <= t <= SESSION_CLOSE_END:
            return SessionType.CLOSE
        else:
            return SessionType.UNKNOWN

    # ==================== 时段1: 集合竞价提醒 ====================

    def _generate_auction_alert(
        self,
        anchors: List[AnchorStock],
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """生成集合竞价时段提醒

        关注要点:
        - 隔夜情绪和消息面
        - 指数高开/低开幅度
        - 竞价涨停/跌停股数量
        - 锚定标的是否竞价异动

        Args:
            anchors: 锚定标的
            market_summary: 市场摘要

        Returns:
            SessionAlert: 集合竞价提醒
        """
        now = datetime.now()
        content_parts: List[str] = []
        related_stocks: List[str] = []
        priority = PRIORITY_NORMAL

        # 隔夜情绪
        overnight = "中性"
        if market_summary:
            overnight = market_summary.get("overnight_sentiment", "中性")
        content_parts.append(f"隔夜情绪: {overnight}")

        # 指数预判
        if market_summary and "index_forecast" in market_summary:
            content_parts.append(f"指数预判: {market_summary['index_forecast']}")

        # 锚定标的竞价表现
        above_expectation = [a for a in anchors if a.expectation == ExpectationLevel.ABOVE]
        below_expectation = [a for a in anchors if a.expectation == ExpectationLevel.BELOW]

        if above_expectation:
            names = ",".join(a.name for a in above_expectation)
            content_parts.append(f"竞价超预期: {names}")
            related_stocks.extend(a.ticker for a in above_expectation)

        if below_expectation:
            names = ",".join(a.name for a in below_expectation)
            content_parts.append(f"竞价低于预期: {names}")
            related_stocks.extend(a.ticker for a in below_expectation)
            priority = PRIORITY_HIGH

        # 竞价涨停数量
        if market_summary:
            auction_limit_up = market_summary.get("auction_limit_up_count", 0)
            auction_limit_down = market_summary.get("auction_limit_down_count", 0)
            content_parts.append(f"竞价涨停{auction_limit_up}只、跌停{auction_limit_down}只")

            if auction_limit_down >= 5:
                content_parts.append("⚠️ 竞价多股跌停，情绪偏弱，谨慎开仓")
                priority = PRIORITY_HIGH
            elif auction_limit_up >= 10:
                content_parts.append("🔥 竞价涨停较多，情绪高涨")

        # 操作建议
        if below_expectation:
            content_parts.append("操作: 低于预期标的开盘不追高，观察5分钟再决定")
        else:
            content_parts.append("操作: 竞价定方向，开盘后看承接再出手")

        content = "\n".join(content_parts)

        return SessionAlert(
            session=SessionType.AUCTION.value,
            timestamp=now,
            content=content,
            priority=priority,
            related_stocks=related_stocks,
        )

    # ==================== 时段2: 开盘30分钟提醒 ====================

    def _generate_open_alert(
        self,
        anchors: List[AnchorStock],
        fund_report: Optional[FundFlowReport] = None,
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """生成开盘黄金30分钟提醒

        关注要点:
        - 资金主攻方向
        - 龙头开盘表现
        - 量能是否放大
        - 方向选择确认

        Args:
            anchors: 锚定标的
            fund_report: 资金流向报告
            market_summary: 市场摘要

        Returns:
            SessionAlert: 开盘30分钟提醒
        """
        now = datetime.now()
        content_parts: List[str] = []
        related_stocks: List[str] = []
        priority = PRIORITY_NORMAL

        content_parts.append("=== 开盘黄金30分 ===")

        # 资金主攻方向
        if fund_report:
            content_parts.append(f"主攻: {fund_report.first_direction}")
            if fund_report.second_direction:
                content_parts.append(f"次攻: {fund_report.second_direction}")
            if fund_report.rotation_direction:
                content_parts.append(f"轮动: {fund_report.rotation_direction}")

        # 锚定标的表现
        for anchor in anchors:
            exp = anchor.expectation.value
            if exp == "强于预期":
                content_parts.append(f"🔥 {anchor.name}: 超预期({anchor.score}分)")
                related_stocks.append(anchor.ticker)
                priority = PRIORITY_HIGH
            elif exp == "低于预期":
                content_parts.append(f"⚠️ {anchor.name}: 低于预期({anchor.score}分)")
                related_stocks.append(anchor.ticker)
                priority = PRIORITY_HIGH

        # 量能评估
        if market_summary:
            volume_status = market_summary.get("volume_status", "正常")
            if volume_status == "放量":
                content_parts.append("量能: 放量上攻，情绪积极")
            elif volume_status == "缩量":
                content_parts.append("量能: 缩量 caution，关注持续性")

        # 方向判断
        direction = "震荡"
        if market_summary and "direction" in market_summary:
            direction = market_summary["direction"]
        content_parts.append(f"方向: {direction}")

        # 操作建议
        if direction == "向上":
            content_parts.append("操作: 方向向上，锚定前排龙头")
        elif direction == "向下":
            content_parts.append("操作: 方向向下，管住手，不逆势")
        else:
            content_parts.append("操作: 方向不明，等待确定性")

        content = "\n".join(content_parts)

        return SessionAlert(
            session=SessionType.OPEN_30MIN.value,
            timestamp=now,
            content=content,
            priority=priority,
            related_stocks=related_stocks,
        )

    # ==================== 时段3: 盘中震荡提醒 ====================

    def _generate_midday_alert(
        self,
        anchors: List[AnchorStock],
        fund_report: Optional[FundFlowReport] = None,
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """生成盘中震荡时段提醒

        关注要点:
        - 趋势是否维持
        - 新异动板块
        - 冷却板块
        - 下午展望

        Args:
            anchors: 锚定标的
            fund_report: 资金流向报告
            market_summary: 市场摘要

        Returns:
            SessionAlert: 盘中震荡提醒
        """
        now = datetime.now()
        content_parts: List[str] = []
        related_stocks: List[str] = []
        priority = PRIORITY_NORMAL

        content_parts.append("=== 盘中震荡 ===")

        # 趋势状态
        trend = "震荡"
        if market_summary and "trend_status" in market_summary:
            trend = market_summary["trend_status"]
        content_parts.append(f"趋势: {trend}")

        # 资金流动
        if fund_report:
            inflow_sectors = list(fund_report.inflow_sectors.keys())[:3]
            outflow_sectors = list(fund_report.outflow_sectors.keys())[:3]
            if inflow_sectors:
                content_parts.append(f"流入: {', '.join(inflow_sectors)}")
            if outflow_sectors:
                content_parts.append(f"流出: {', '.join(outflow_sectors)}")

            # 撤退预警
            if fund_report.outflow_type:
                content_parts.append(f"撤退: {fund_report.outflow_type}")
                if "恐慌" in fund_report.outflow_type:
                    priority = PRIORITY_HIGH

        # 锚定标的中午状态
        for anchor in anchors:
            if anchor.expectation == ExpectationLevel.BELOW:
                content_parts.append(f"⚠️ {anchor.name}({anchor.ticker}): 走弱")
                related_stocks.append(anchor.ticker)

        # 新异动
        if market_summary and "new_movements" in market_summary:
            movements = market_summary["new_movements"]
            if movements:
                content_parts.append(f"异动: {', '.join(movements[:3])}")

        # 下午展望
        if trend == "向上":
            content_parts.append("下午: 趋势向上，持股为主")
        elif trend == "向下":
            content_parts.append("下午: 趋势向下，减仓避险")
        else:
            content_parts.append("下午: 震荡格局，高抛低吸")

        content = "\n".join(content_parts)

        return SessionAlert(
            session=SessionType.MIDDAY.value,
            timestamp=now,
            content=content,
            priority=priority,
            related_stocks=related_stocks,
        )

    # ==================== 时段4: 尾盘提醒 ====================

    def _generate_close_alert(
        self,
        anchors: List[AnchorStock],
        fund_report: Optional[FundFlowReport] = None,
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """生成尾盘时段提醒

        关注要点:
        - 当日总结
        - 次日展望
        - 持仓决策
        - 隔夜风险

        Args:
            anchors: 锚定标的
            fund_report: 资金流向报告
            market_summary: 市场摘要

        Returns:
            SessionAlert: 尾盘提醒
        """
        now = datetime.now()
        content_parts: List[str] = []
        related_stocks: List[str] = []
        priority = PRIORITY_NORMAL

        content_parts.append("=== 尾盘决策 ===")

        # 当日总结
        day_summary = ""
        if market_summary and "day_summary" in market_summary:
            day_summary = market_summary["day_summary"]
        else:
            # 根据锚定标的生成
            strong_count = sum(1 for a in anchors if a.expectation == ExpectationLevel.ABOVE)
            weak_count = sum(1 for a in anchors if a.expectation == ExpectationLevel.BELOW)
            if strong_count > weak_count:
                day_summary = "情绪偏强"
            elif weak_count > strong_count:
                day_summary = "情绪偏弱"
            else:
                day_summary = "情绪分化"
        content_parts.append(f"总结: {day_summary}")

        # 龙头状态
        total_dragons = [a for a in anchors if "总龙" in a.anchor_type.value]
        if total_dragons:
            dragon = total_dragons[0]
            content_parts.append(f"总龙: {dragon.name}({dragon.expectation.value})")
            related_stocks.append(dragon.ticker)

        # 次日展望
        if market_summary and "next_day_outlook" in market_summary:
            content_parts.append(f"次日: {market_summary['next_day_outlook']}")
        elif fund_report and fund_report.first_direction:
            content_parts.append(f"次日: 关注{fund_report.first_direction}持续性")

        # 持仓建议
        position_advice = "根据个股强弱决定去留"
        strong_anchors = [a for a in anchors if a.expectation == ExpectationLevel.ABOVE]
        weak_anchors = [a for a in anchors if a.expectation == ExpectationLevel.BELOW]

        if strong_anchors:
            strong_names = ",".join(a.name for a in strong_anchors)
            content_parts.append(f"持仓: {strong_names}可留")
        if weak_anchors:
            weak_names = ",".join(a.name for a in weak_anchors)
            content_parts.append(f"离场: {weak_names}走弱需走")
            priority = PRIORITY_HIGH

        # 隔夜风险
        if market_summary and "overnight_risk" in market_summary:
            risk = market_summary["overnight_risk"]
            if risk:
                content_parts.append(f"风险: {risk}")
                priority = PRIORITY_HIGH

        # 尾盘操作建议
        content_parts.append("操作: 弱股不留，强股可隔夜，控制仓位")

        content = "\n".join(content_parts)

        return SessionAlert(
            session=SessionType.CLOSE.value,
            timestamp=now,
            content=content,
            priority=priority,
            related_stocks=related_stocks,
        )

    # ==================== 便捷接口 ====================

    def force_generate_alert(
        self,
        session_type: SessionType,
        anchors: List[AnchorStock],
        fund_report: Optional[FundFlowReport] = None,
        market_summary: Optional[Dict] = None,
    ) -> SessionAlert:
        """强制生成指定时段提醒

        不受当前时间限制，用于测试或复盘。

        Args:
            session_type: 指定时段
            anchors: 锚定标的
            fund_report: 资金流向报告
            market_summary: 市场摘要

        Returns:
            SessionAlert: 时段提醒
        """
        now = datetime.now()

        if session_type == SessionType.AUCTION:
            return self._generate_auction_alert(anchors, market_summary)
        elif session_type == SessionType.OPEN_30MIN:
            return self._generate_open_alert(anchors, fund_report, market_summary)
        elif session_type == SessionType.MIDDAY:
            return self._generate_midday_alert(anchors, fund_report, market_summary)
        elif session_type == SessionType.CLOSE:
            return self._generate_close_alert(anchors, fund_report, market_summary)
        else:
            return SessionAlert(
                session="未知",
                timestamp=now,
                content="未知时段",
                priority=PRIORITY_LOW,
            )

    def clear_history(self):
        """清空历史提醒"""
        for key in self._session_history:
            self._session_history[key].clear()
        logger.info("时段提醒历史已清空")
