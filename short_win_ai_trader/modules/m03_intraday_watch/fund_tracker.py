"""资金轨迹追踪模块 — 盘中看盘核心组件

实时追踪A股市场资金流动轨迹，捕捉资金从先锋股→主线题材→
补涨方向的传导链条，及时预警板块效应和资金撤退信号。

资金传导模型:
先锋点火 → 主线确认 → 补涨扩散 → 高潮/分歧

监测维度:
1. 板块效应预警: 涨停≥3只/批量高开≥3%/分支异动
2. 资金撤退监测: 良性调仓 vs 恐慌撤退
3. 每30分钟资金总结: 流入流出统计、方向判断

撤退类型判定:
- 良性调仓: 龙头分歧但跟风仍强，板块效应未散
- 恐慌撤退: 龙头核按钮+批量炸板+板块放量杀跌
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    FundFlowReport,
    LimitUpStock,
    SectorAlert,
    ThemeData,
)

logger = get_logger("swat.m03.fund_tracker")


# ── 常量定义 ────────────────────────────────────────────

# 板块效应预警阈值
SECTOR_LIMIT_UP_THRESHOLD = 3       # 板块涨停预警阈值
SECTOR_BATCH_HIGH_OPEN = 3.0        # 批量高开百分比阈值(%)  
SECTOR_BRANCH_MOVE_PCT = 4.0        # 分支异动涨幅阈值(%)

# 资金撤退判定参数
PANIC_EXPLODE_RATE = 40.0           # 恐慌炸板率阈值(%)
PANIC_DROP_PCT = 5.0                # 恐慌杀跌幅度阈值(%)
BENIGN_LEADER_DROP = 5.0            # 良性龙头分歧幅度(%)

# 资金流向总结间隔
FUND_SUMMARY_INTERVAL_MIN = 30      # 资金总结间隔(分钟)

# 资金流入分级
INFLOW_STRONG = 5e8                 # 强势流入: 5亿+
INFLOW_MODERATE = 1e8               # 中等流入: 1亿+
OUTFLOW_STRONG = -5e8               # 强势流出: -5亿+
OUTFLOW_MODERATE = -1e8             # 中等流出: -1亿+


@dataclass
class FundFlowSnapshot:
    """资金流向快照 — 单时刻资金状态"""
    timestamp: datetime = field(default_factory=datetime.now)
    sector: str = ""
    net_inflow: float = 0.0             # 净流入(元)
    inflow: float = 0.0                 # 流入
    outflow: float = 0.0                # 流出
    limit_up_count: int = 0             # 涨停数
    limit_up_changes: List[str] = field(default_factory=list)  # 涨停股变化
    avg_change_pct: float = 0.0         # 板块平均涨幅
    leader_status: str = ""             # 龙头状态
    alert_level: str = "normal"         # 预警级别: normal/watch/warning/critical


@dataclass
class FundTrack:
    """单板块资金轨迹"""
    sector: str = ""
    snapshots: List[FundFlowSnapshot] = field(default_factory=list)
    current_stage: str = ""             # 当前阶段: 萌芽/发酵/加速/分歧/退潮
    trend: str = ""                     # 趋势: 加强/维持/减弱/撤退
    is_retreating: bool = False
    retreat_type: str = ""              # 良性调仓/恐慌撤退/正常分化


@dataclass
class FundFlowSummary:
    """资金总结报告 — 每30分钟输出"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    top_inflow_sectors: List[Dict] = field(default_factory=list)
    top_outflow_sectors: List[Dict] = field(default_factory=list)
    new_hot_sectors: List[str] = field(default_factory=list)
    cooling_sectors: List[str] = field(default_factory=list)
    retreat_warnings: List[str] = field(default_factory=list)
    summary_text: str = ""


class FundTracker:
    """资金轨迹追踪器

    实时追踪市场资金流动，预警板块效应和撤退信号。

    Attributes:
        config: 应用配置
        _sector_tracks: 各板块资金轨迹缓存
        _last_summary_time: 上次总结时间
        _alerts: 预警列表
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化资金轨迹追踪器

        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._sector_tracks: Dict[str, FundTrack] = {}
        self._last_summary_time: Optional[datetime] = None
        self._alerts: List[SectorAlert] = []
        self._snapshots_history: List[FundFlowSnapshot] = []
        logger.info("资金轨迹追踪器初始化完成")

    # ==================== 核心公共接口 ====================

    async def track_fund_flow(
        self,
        sector_data: List[ThemeData],
        limit_up_stocks: List[LimitUpStock],
        anchors: List[AnchorStock],
    ) -> FundFlowReport:
        """资金轨迹追踪主入口

        执行完整追踪流程: 快照采集 → 轨迹更新 → 预警检测 → 撤退判定

        Args:
            sector_data: 板块/题材数据列表
            limit_up_stocks: 涨停股列表
            anchors: 当前锚定标的列表

        Returns:
            FundFlowReport: 资金流向报告

        Raises:
            ModuleError: 追踪过程发生严重错误
        """
        logger.info("========== 开始资金轨迹追踪 ==========")

        try:
            # Step 1: 采集板块资金快照
            logger.info("[Step 1/4] 采集板块资金快照...")
            snapshots = self._capture_snapshots(sector_data, limit_up_stocks, anchors)

            # Step 2: 更新板块轨迹
            logger.info("[Step 2/4] 更新板块资金轨迹...")
            self._update_tracks(snapshots)

            # Step 3: 板块效应预警
            logger.info("[Step 3/4] 检测板块效应预警...")
            alerts = self._detect_sector_alerts(snapshots, limit_up_stocks)
            self._alerts.extend(alerts)

            # Step 4: 撤退监测
            logger.info("[Step 4/4] 监测资金撤退信号...")
            retreat_warnings = self._detect_retreat_signals(snapshots, anchors)

            # 生成报告
            report = self._compile_report(snapshots, alerts, retreat_warnings)

            logger.info(
                f"资金追踪完成: {len(snapshots)}个板块, "
                f"{len(alerts)}条预警, {len(retreat_warnings)}条撤退信号"
            )
            return report

        except Exception as e:
            logger.error(f"资金轨迹追踪严重错误: {e}")
            raise ModuleError(f"资金轨迹追踪失败: {e}")

    def get_sector_alerts(self, clear: bool = False) -> List[SectorAlert]:
        """获取板块预警列表

        Args:
            clear: 是否清空预警缓存

        Returns:
            List[SectorAlert]: 预警列表
        """
        alerts = self._alerts.copy()
        if clear:
            self._alerts.clear()
        return alerts

    def should_generate_summary(self) -> bool:
        """判断是否需要生成30分钟资金总结

        Returns:
            bool: 是否需要生成总结
        """
        now = datetime.now()
        if self._last_summary_time is None:
            return True
        elapsed = (now - self._last_summary_time).total_seconds() / 60
        return elapsed >= FUND_SUMMARY_INTERVAL_MIN

    def generate_fund_summary(self) -> FundFlowSummary:
        """生成30分钟资金总结

        统计最近30分钟资金流向，输出Top流入/流出板块、
        新热点、冷却板块和撤退预警。

        Returns:
            FundFlowSummary: 资金总结报告
        """
        now = datetime.now()
        if self._last_summary_time is None:
            window_start = now - timedelta(minutes=FUND_SUMMARY_INTERVAL_MIN)
        else:
            window_start = self._last_summary_time

        # 收集窗口期内快照
        window_snapshots = [
            s for s in self._snapshots_history
            if window_start <= s.timestamp <= now
        ]

        # 按板块汇总
        sector_net: Dict[str, float] = {}
        sector_limit_up: Dict[str, int] = {}
        for s in window_snapshots:
            sector_net[s.sector] = sector_net.get(s.sector, 0) + s.net_inflow
            sector_limit_up[s.sector] = max(
                sector_limit_up.get(s.sector, 0),
                s.limit_up_count,
            )

        # Top流入板块
        sorted_inflow = sorted(sector_net.items(), key=lambda x: x[1], reverse=True)
        top_inflow = [
            {"sector": s, "net": net, "level": self._classify_inflow(net)}
            for s, net in sorted_inflow[:5] if net > 0
        ]

        # Top流出板块
        top_outflow = [
            {"sector": s, "net": abs(net), "level": self._classify_inflow(net)}
            for s, net in sorted_inflow[-5:] if net < 0
        ]

        # 新热点: 之前不活跃，突然流入
        new_hot = [
            s for s, net in sorted_inflow[:3]
            if net > INFLOW_MODERATE and s not in self._sector_tracks
        ]

        # 冷却板块: 资金明显流出
        cooling = [
            s for s, net in sorted_inflow[-5:]
            if net < OUTFLOW_MODERATE
        ]

        # 撤退预警
        retreat_warnings: List[str] = []
        for sector, track in self._sector_tracks.items():
            if track.is_retreating:
                retreat_warnings.append(
                    f"{sector}: {track.retreat_type} [{track.trend}]"
                )

        # 生成总结文本
        parts: List[str] = []
        parts.append(f"=== 资金总结 [{window_start.strftime('%H:%M')}-{now.strftime('%H:%M')}] ===")

        if top_inflow:
            parts.append(f"资金主攻: {', '.join(t['sector'] for t in top_inflow[:3])}")
        if top_outflow:
            parts.append(f"资金流出: {', '.join(t['sector'] for t in top_outflow[:3])}")
        if new_hot:
            parts.append(f"新热点: {', '.join(new_hot)}")
        if cooling:
            parts.append(f"冷却中: {', '.join(cooling)}")
        if retreat_warnings:
            parts.append(f"撤退预警: {'; '.join(retreat_warnings)}")

        summary = FundFlowSummary(
            start_time=window_start,
            end_time=now,
            top_inflow_sectors=top_inflow,
            top_outflow_sectors=top_outflow,
            new_hot_sectors=new_hot,
            cooling_sectors=cooling,
            retreat_warnings=retreat_warnings,
            summary_text="\n".join(parts),
        )

        self._last_summary_time = now
        logger.info("30分钟资金总结已生成")
        return summary

    # ==================== 步骤1: 快照采集 ====================

    def _capture_snapshots(
        self,
        sector_data: List[ThemeData],
        limit_up_stocks: List[LimitUpStock],
        anchors: List[AnchorStock],
    ) -> List[FundFlowSnapshot]:
        """采集各板块资金快照

        Args:
            sector_data: 板块数据
            limit_up_stocks: 涨停股
            anchors: 锚定标的

        Returns:
            List[FundFlowSnapshot]: 快照列表
        """
        snapshots: List[FundFlowSnapshot] = []
        now = datetime.now()

        # 为每个板块创建快照
        for theme in sector_data:
            # 统计板块内涨停股
            sector_limits = [
                s for s in limit_up_stocks
                if s.theme == theme.theme_name
            ]

            # 判断龙头状态
            leader_status = "正常"
            for anchor in anchors:
                if anchor.ticker == theme.leading_stock:
                    if anchor.expectation.value == "低于预期":
                        leader_status = "低于预期"
                    elif anchor.expectation.value == "强于预期":
                        leader_status = "强势"
                    break

            # 预警级别判定
            alert_level = "normal"
            if len(sector_limits) >= SECTOR_LIMIT_UP_THRESHOLD:
                alert_level = "warning"
            if theme.avg_change_pct >= SECTOR_BATCH_HIGH_OPEN:
                alert_level = "warning"

            snapshot = FundFlowSnapshot(
                timestamp=now,
                sector=theme.theme_name,
                net_inflow=theme.total_inflow,
                inflow=max(0, theme.total_inflow),
                outflow=max(0, -theme.total_inflow),
                limit_up_count=len(sector_limits),
                avg_change_pct=theme.avg_change_pct,
                leader_status=leader_status,
                alert_level=alert_level,
            )
            snapshots.append(snapshot)
            self._snapshots_history.append(snapshot)

        # 清理过老的历史
        cutoff = now - timedelta(hours=4)
        self._snapshots_history = [
            s for s in self._snapshots_history if s.timestamp > cutoff
        ]

        return snapshots

    # ==================== 步骤2: 轨迹更新 ====================

    def _update_tracks(self, snapshots: List[FundFlowSnapshot]):
        """更新各板块资金轨迹

        将新快照合并到对应板块的资金轨迹中。

        Args:
            snapshots: 新采集的快照列表
        """
        for snapshot in snapshots:
            sector = snapshot.sector
            if sector not in self._sector_tracks:
                self._sector_tracks[sector] = FundTrack(sector=sector)

            track = self._sector_tracks[sector]
            track.snapshots.append(snapshot)

            # 只保留最近20个快照
            if len(track.snapshots) > 20:
                track.snapshots = track.snapshots[-20:]

            # 更新阶段
            track.current_stage = self._determine_stage(track)

            # 更新趋势
            track.trend = self._determine_trend(track)

    def _determine_stage(self, track: FundTrack) -> str:
        """判定板块当前阶段

        根据资金流入强度和涨停数判定阶段。

        Args:
            track: 板块资金轨迹

        Returns:
            str: 阶段描述
        """
        if not track.snapshots:
            return "观察"

        latest = track.snapshots[-1]
        prev = track.snapshots[-2] if len(track.snapshots) >= 2 else None

        # 根据流入和涨停数判断
        if latest.net_inflow > INFLOW_STRONG and latest.limit_up_count >= 8:
            return "高潮"
        elif latest.net_inflow > INFLOW_MODERATE and latest.limit_up_count >= 5:
            return "加速"
        elif latest.net_inflow > INFLOW_MODERATE and latest.limit_up_count >= 3:
            return "发酵"
        elif latest.net_inflow > 0 and latest.limit_up_count >= 1:
            return "萌芽"
        elif prev and latest.net_inflow < prev.net_inflow * 0.5:
            return "分歧"
        elif latest.net_inflow < 0 and latest.limit_up_count == 0:
            return "退潮"
        else:
            return "观察"

    def _determine_trend(self, track: FundTrack) -> str:
        """判定板块趋势方向

        Args:
            track: 板块资金轨迹

        Returns:
            str: 趋势描述
        """
        if len(track.snapshots) < 2:
            return "观察"

        recent = track.snapshots[-3:]  # 最近3个
        net_changes = [s.net_inflow for s in recent]

        # 连续增强
        if all(net_changes[i] < net_changes[i + 1] for i in range(len(net_changes) - 1)):
            return "加强"
        # 连续减弱
        elif all(net_changes[i] > net_changes[i + 1] for i in range(len(net_changes) - 1)):
            return "减弱"
        # 波动维持
        elif max(net_changes) - min(net_changes) < INFLOW_MODERATE:
            return "维持"
        else:
            return "波动"

    # ==================== 步骤3: 板块效应预警 ====================

    def _detect_sector_alerts(
        self,
        snapshots: List[FundFlowSnapshot],
        limit_up_stocks: List[LimitUpStock],
    ) -> List[SectorAlert]:
        """检测板块效应预警

        预警类型:
        - 强板块效应: 涨停≥3只
        - 批量高开: 板块平均高开≥3%
        - 分支异动: 细分方向突然走强

        Args:
            snapshots: 板块快照
            limit_up_stocks: 涨停股

        Returns:
            List[SectorAlert]: 预警列表
        """
        alerts: List[SectorAlert] = []

        for snap in snapshots:
            # 强板块效应预警
            if snap.limit_up_count >= SECTOR_LIMIT_UP_THRESHOLD:
                affected = [
                    s.ticker for s in limit_up_stocks
                    if s.theme == snap.sector
                ][:10]

                urgency = "high" if snap.limit_up_count >= 6 else "normal"
                alerts.append(SectorAlert(
                    sector_name=snap.sector,
                    alert_type="强板块效应",
                    trigger_condition=f"板块涨停{snap.limit_up_count}只",
                    affected_stocks=affected,
                    urgency=urgency,
                    advice=f"关注{snap.sector}板块前排标的，把握介入时机",
                ))

            # 批量高开预警
            if snap.avg_change_pct >= SECTOR_BATCH_HIGH_OPEN:
                alerts.append(SectorAlert(
                    sector_name=snap.sector,
                    alert_type="批量高开",
                    trigger_condition=f"板块平均涨幅{snap.avg_change_pct:.1f}%",
                    affected_stocks=[],
                    urgency="normal",
                    advice=f"{snap.sector}批量高开，观察持续性避免追高",
                ))

            # 分支异动预警
            if snap.avg_change_pct >= SECTOR_BRANCH_MOVE_PCT and snap.limit_up_count >= 2:
                alerts.append(SectorAlert(
                    sector_name=snap.sector,
                    alert_type="分支异动",
                    trigger_condition=f"涨幅{snap.avg_change_pct:.1f}%+涨停{snap.limit_up_count}只",
                    affected_stocks=[],
                    urgency="normal",
                    advice=f"{snap.sector}分支异动，可能为新的套利方向",
                ))

        return alerts

    # ==================== 步骤4: 撤退监测 ====================

    def _detect_retreat_signals(
        self,
        snapshots: List[FundFlowSnapshot],
        anchors: List[AnchorStock],
    ) -> List[str]:
        """监测资金撤退信号

        区分良性调仓和恐慌撤退:
        - 良性调仓: 龙头分歧但跟风仍强
        - 恐慌撤退: 龙头核按钮+批量炸板

        Args:
            snapshots: 板块快照
            anchors: 锚定标的

        Returns:
            List[str]: 撤退预警信号文本
        """
        warnings: List[str] = []

        for snap in snapshots:
            # 恐慌撤退判定
            is_panic = False
            is_benign = False

            # 资金大幅流出
            if snap.net_inflow < OUTFLOW_STRONG:
                is_panic = True

            # 龙头低于预期
            if snap.leader_status == "低于预期":
                # 进一步判断跟风情况
                if snap.limit_up_count >= 3:
                    is_benign = True
                else:
                    is_panic = True

            # 板块退潮确认
            if snap.avg_change_pct < -PANIC_DROP_PCT and snap.net_inflow < 0:
                is_panic = True

            # 记录判定结果
            sector = snap.sector
            if sector not in self._sector_tracks:
                continue

            track = self._sector_tracks[sector]

            if is_panic:
                track.is_retreating = True
                track.retreat_type = "恐慌撤退"
                warnings.append(
                    f"[恐慌撤退] {sector}: 资金大幅流出({snap.net_inflow/1e8:.1f}亿), "
                    f"龙头状态{snap.leader_status}"
                )
            elif is_benign:
                track.is_retreating = True
                track.retreat_type = "良性调仓"
                warnings.append(
                    f"[良性调仓] {sector}: 龙头分歧但跟风仍强({snap.limit_up_count}只涨停), "
                    f"资金可能切换标的"
                )

        return warnings

    # ==================== 报告生成 ====================

    def _compile_report(
        self,
        snapshots: List[FundFlowSnapshot],
        alerts: List[SectorAlert],
        retreat_warnings: List[str],
    ) -> FundFlowReport:
        """汇总资金流向报告

        Args:
            snapshots: 板块快照
            alerts: 预警
            retreat_warnings: 撤退信号

        Returns:
            FundFlowReport: 资金流向报告
        """
        # 流入/流出板块排序
        sorted_sectors = sorted(snapshots, key=lambda s: s.net_inflow, reverse=True)

        top_inflow = {
            s.sector: s.net_inflow for s in sorted_sectors[:3] if s.net_inflow > 0
        }
        top_outflow = {
            s.sector: abs(s.net_inflow) for s in sorted_sectors[-3:] if s.net_inflow < 0
        }

        # 判断第一/第二进攻方向
        first_direction = sorted_sectors[0].sector if sorted_sectors else ""
        second_direction = sorted_sectors[1].sector if len(sorted_sectors) > 1 else ""

        # 轮动方向: 从退潮板块流出的资金可能去向
        rotation_candidates = [
            s.sector for s in sorted_sectors
            if 0 < s.net_inflow < INFLOW_MODERATE and s.limit_up_count >= 2
        ]
        rotation_direction = rotation_candidates[0] if rotation_candidates else ""

        # 撤退类型
        retreat_type = ""
        if retreat_warnings:
            if "恐慌" in retreat_warnings[0]:
                retreat_type = "恐慌撤退"
            elif "良性" in retreat_warnings[0]:
                retreat_type = "良性调仓"

        # 生成摘要
        parts: List[str] = []
        parts.append(f"第一进攻: {first_direction}")
        if second_direction:
            parts.append(f"第二进攻: {second_direction}")
        if rotation_direction:
            parts.append(f"轮动方向: {rotation_direction}")
        if retreat_warnings:
            parts.append(f"撤退信号: {retreat_warnings[0]}")
        parts.append(f"板块预警: {len(alerts)}条")

        return FundFlowReport(
            first_direction=first_direction,
            second_direction=second_direction,
            rotation_direction=rotation_direction,
            inflow_sectors=top_inflow,
            outflow_sectors=top_outflow,
            outflow_type=retreat_type,
            summary="; ".join(parts),
        )

    # ==================== 辅助方法 ====================

    def _classify_inflow(self, net: float) -> str:
        """资金流入分级

        Args:
            net: 净流入金额

        Returns:
            str: 分级描述
        """
        if net >= INFLOW_STRONG:
            return "强势流入"
        elif net >= INFLOW_MODERATE:
            return "中等流入"
        elif net > 0:
            return "小幅流入"
        elif net >= OUTFLOW_MODERATE:
            return "小幅流出"
        elif net >= OUTFLOW_STRONG:
            return "中等流出"
        else:
            return "强势流出"

    def clear_history(self):
        """清空追踪历史"""
        self._sector_tracks.clear()
        self._snapshots_history.clear()
        self._alerts.clear()
        self._last_summary_time = None
        logger.info("资金追踪历史已清空")

    def get_track_status(self, sector: str) -> Optional[FundTrack]:
        """获取指定板块的资金轨迹

        Args:
            sector: 板块名称

        Returns:
            Optional[FundTrack]: 资金轨迹
        """
        return self._sector_tracks.get(sector)

    def get_all_tracks(self) -> Dict[str, FundTrack]:
        """获取所有板块的资金轨迹

        Returns:
            Dict[str, FundTrack]: 板块→轨迹映射
        """
        return self._sector_tracks.copy()
