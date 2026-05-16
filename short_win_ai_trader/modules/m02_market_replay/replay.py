"""复盘主引擎 — 全维度智能复盘入口

全自动完成超短线所需全维度复盘工作，覆盖:
- 大盘基础数据自动统计（涨跌家数、涨停、跌停、炸板率、量能等）
- 连板梯队全自动梳理
- 题材梯队自动划分
- 资金行为智能复盘
- 市场情绪周期智能研判
- 题材炒作全周期演化研判
- 大盘运行趋势推演

执行流程:
1. 抓取当日行情+资讯+资金数据
2. 完成基础复盘（大盘+连板+题材+资金）
3. 情绪因子量化计算
4. 判定当前情绪周期
5. 推演题材生命周期
6. 预判次日大盘与题材趋势
7. 匹配对应仓位策略
8. 生成完整复盘报告
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.data_manager import DataManager
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    DragonBond,
    EmotionDiagnosis,
    EmotionIndicators,
    LimitUpStock,
    MarketSnapshot,
    NextDayPrediction,
    ThemeCycleAnalysis,
    ThemeData,
)

from .emotion_engine import EmotionEngine
from .market_predictor import MarketPredictor, TechnicalContext
from .theme_analyzer import ThemeAnalyzer

logger = get_logger("swat.m02.replay")


@dataclass
class BoardLadder:
    """连板梯队数据"""
    board_level: int = 0                    # 连板层级
    stocks: List[Dict] = field(default_factory=list)  # 该层级股票列表
    count: int = 0                          # 数量


@dataclass
class MarketReplayReport:
    """完整复盘报告"""
    trade_date: Optional[date] = None
    # 基础复盘数据
    market_summary: str = ""                # 大盘综述
    board_ladders: List[BoardLadder] = field(default_factory=list)  # 连板梯队
    theme_tiers: List[Dict] = field(default_factory=list)  # 题材梯队
    fund_summary: str = ""                  # 资金复盘摘要
    # 情绪周期诊断
    emotion_diagnosis: Optional[EmotionDiagnosis] = None
    # 题材周期分析
    theme_analysis: List[ThemeCycleAnalysis] = field(default_factory=list)
    # 次日预判
    next_day_prediction: Optional[NextDayPrediction] = None
    # 复盘统计
    statistics: Dict = field(default_factory=dict)
    # 核心结论
    key_conclusions: List[str] = field(default_factory=list)
    # 次日交易方向
    next_day_directions: Dict = field(default_factory=dict)


class MarketReplay:
    """智能复盘主引擎

    全自动完成从数据采集到报告生成的完整复盘流程。

    Attributes:
        data_manager: 统一数据管理器
        config: 应用配置
        emotion_engine: 情绪周期研判引擎
        theme_analyzer: 题材周期分析器
        market_predictor: 大盘趋势推演器
    """

    def __init__(self, data_manager: DataManager, config: Optional[AppConfig] = None):
        """初始化复盘引擎

        Args:
            data_manager: 统一数据管理器实例
            config: 应用配置对象（可选）
        """
        self.data_manager = data_manager
        self.config = config or data_manager.config
        self.emotion_engine = EmotionEngine(self.config)
        self.theme_analyzer = ThemeAnalyzer(self.config)
        self.market_predictor = MarketPredictor(self.config)

        logger.info("智能复盘主引擎初始化完成")

    # ==================== 核心公共接口 ====================

    async def replay_market(self, trade_date: Optional[date] = None) -> MarketReplayReport:
        """全自动复盘主入口

        执行完整复盘流程，包括数据采集、情绪研判、题材分析、趋势推演。

        Args:
            trade_date: 复盘日期，默认当日

        Returns:
            MarketReplayReport 完整复盘报告

        Raises:
            ModuleError: 复盘过程发生严重错误
        """
        trade_date = trade_date or date.today()
        logger.info(f"========== 开始全维度复盘: {trade_date.isoformat()} ==========")

        try:
            # Step 1: 数据采集
            logger.info("[Step 1/7] 采集市场数据...")
            market_data = await self._fetch_market_data(trade_date)

            snapshot = market_data.get("snapshot", MarketSnapshot())
            limit_ups = market_data.get("limit_up_stocks", [])
            dragon_bonds = market_data.get("dragon_bonds", [])
            themes = market_data.get("themes", [])

            # Step 2: 基础复盘（大盘+连板+题材+资金）
            logger.info("[Step 2/7] 完成基础复盘...")
            market_summary = self._generate_market_summary(snapshot)
            board_ladders = self._analyze_board_ladders(limit_ups)
            theme_tiers = self._classify_theme_tiers(themes)
            fund_summary = self._analyze_fund_flow(dragon_bonds)

            # Step 3: 情绪因子量化计算
            logger.info("[Step 3/7] 计算情绪量化指标...")
            indicators = self.emotion_engine.calculate_emotion_indicators(
                snapshot, limit_ups, themes, dragon_bonds
            )

            # Step 4: 情绪周期研判
            logger.info("[Step 4/7] 研判情绪周期...")
            diagnosis = self.emotion_engine.diagnose_emotion_cycle(indicators)

            # Step 5: 题材生命周期推演
            logger.info("[Step 5/7] 推演题材生命周期...")
            theme_analysis = self.theme_analyzer.analyze_themes(
                themes, limit_ups, dragon_bonds, trade_date
            )

            # Step 6: 次日大盘趋势预判
            logger.info("[Step 6/7] 预判次日趋势...")
            prediction = self.market_predictor.predict_next_day(diagnosis, snapshot)

            # Step 7: 生成完整报告
            logger.info("[Step 7/7] 生成复盘报告...")
            report = self._compile_report(
                trade_date=trade_date,
                snapshot=snapshot,
                indicators=indicators,
                diagnosis=diagnosis,
                theme_analysis=theme_analysis,
                prediction=prediction,
                market_summary=market_summary,
                board_ladders=board_ladders,
                theme_tiers=theme_tiers,
                fund_summary=fund_summary,
                limit_ups=limit_ups,
                dragon_bonds=dragon_bonds,
            )

            logger.info(f"========== 复盘完成: {trade_date.isoformat()} ==========")
            return report

        except Exception as e:
            logger.error(f"复盘流程严重错误: {e}")
            raise ModuleError(f"全维度复盘失败: {e}")

    # ==================== 各步骤实现 ====================

    async def _fetch_market_data(self, trade_date: date) -> Dict:
        """采集市场数据

        并行获取市场快照、涨停股、龙虎榜和题材数据。

        Args:
            trade_date: 交易日

        Returns:
            Dict: 包含 snapshot, limit_up_stocks, dragon_bonds, themes
        """
        try:
            # 获取市场快照
            snapshot = await self.data_manager.ifind.get_market_snapshot(trade_date)
        except Exception as e:
            logger.warning(f"获取市场快照失败: {e}")
            snapshot = MarketSnapshot(trade_date=trade_date)

        try:
            # 获取涨停股
            limit_ups = await self.data_manager.ifind.get_limit_up_stocks(trade_date)
        except Exception as e:
            logger.warning(f"获取涨停股失败: {e}")
            limit_ups = []

        try:
            # 获取龙虎榜
            dragon_bonds = await self.data_manager.ifind.get_dragon_bonds(trade_date)
        except Exception as e:
            logger.warning(f"获取龙虎榜失败: {e}")
            dragon_bonds = []

        # 获取题材数据（使用模拟数据，实际可从iFind获取）
        themes = self._generate_mock_themes(trade_date)

        return {
            "snapshot": snapshot,
            "limit_up_stocks": limit_ups,
            "dragon_bonds": dragon_bonds,
            "themes": themes,
        }

    def _generate_market_summary(self, snapshot: MarketSnapshot) -> str:
        """生成大盘基础数据综述

        统计涨跌家数、涨停、跌停、炸板率、量能等核心指标。

        Args:
            snapshot: 市场快照

        Returns:
            str: 大盘综述文本
        """
        parts: List[str] = []

        # 涨跌概况
        total = snapshot.total_stocks
        up = snapshot.up_count
        down = snapshot.down_count
        if total > 0:
            up_pct = (up / total) * 100
            parts.append(f"两市共{total}家，涨{up}家({up_pct:.1f}%)、跌{down}家")

        # 涨停跌停
        parts.append(f"涨停{snapshot.limit_up_count}只、跌停{snapshot.limit_down_count}只")

        # 炸板率
        parts.append(f"炸板率{snapshot.explode_rate:.1f}%")

        # 量能
        volume_wan = snapshot.total_volume / 1e4 if snapshot.total_volume else 0
        parts.append(f"两市成交额{volume_wan:.0f}万")
        if snapshot.volume_change_pct > 0:
            parts.append(f"量能放大{snapshot.volume_change_pct:.1f}%")
        elif snapshot.volume_change_pct < 0:
            parts.append(f"量能萎缩{abs(snapshot.volume_change_pct):.1f}%")

        # 指数
        if snapshot.sh_index > 0:
            parts.append(f"上证{snapshot.sh_index:.2f}")

        # 异常提醒
        alerts: List[str] = []
        if snapshot.explode_rate >= 50:
            alerts.append("炸板率>=50%，市场分歧极大")
        if snapshot.limit_down_count >= 10:
            alerts.append(f"跌停{snapshot.limit_down_count}只，风险信号")
        if abs(snapshot.volume_change_pct) >= 30:
            direction = "骤增" if snapshot.volume_change_pct > 0 else "骤减"
            alerts.append(f"量能{direction}>=30%，注意拐点信号")

        summary = "; ".join(parts)
        if alerts:
            summary += f" [异常提醒] {'; '.join(alerts)}"

        return summary

    def _analyze_board_ladders(self, limit_ups: List[LimitUpStock]) -> List[BoardLadder]:
        """全自动梳理连板梯队

        按连板层级整理涨停股，标注题材和关键数据。

        Args:
            limit_ups: 涨停股列表

        Returns:
            List[BoardLadder]: 连板梯队列表
        """
        if not limit_ups:
            return []

        # 按连板数分组
        board_map: Dict[int, List[Dict]] = {}
        for st in limit_ups:
            level = st.consecutive_boards
            if level not in board_map:
                board_map[level] = []
            board_map[level].append({
                "ticker": st.ticker,
                "name": st.name,
                "theme": st.theme,
                "first_time": st.first_limit_up_time,
                "seal_amount": st.seal_amount,
            })

        # 构建梯队（从高到低排列）
        ladders: List[BoardLadder] = []
        for level in sorted(board_map.keys(), reverse=True):
            stocks = board_map[level]
            ladders.append(BoardLadder(
                board_level=level,
                stocks=stocks,
                count=len(stocks),
            ))

        return ladders

    def _classify_theme_tiers(self, themes: List[ThemeData]) -> List[Dict]:
        """题材梯队自动划分

        将题材分为一级主线、二级支线、一日游杂毛三级。

        Args:
            themes: 题材数据列表

        Returns:
            List[Dict]: 分级后的题材列表
        """
        if not themes:
            return []

        # 计算每个题材的强度评分
        scored_themes: List[Tuple[ThemeData, float]] = []
        for theme in themes:
            score = (
                theme.limit_up_count * 20  # 涨停权重最高
                + theme.avg_change_pct * 5
                + len(theme.stocks) * 2
                + (1e8 if theme.leading_stock else 0)
            )
            scored_themes.append((theme, score))

        # 按强度排序
        scored_themes.sort(key=lambda x: x[1], reverse=True)

        # 分级
        tiers: List[Dict] = []
        total = len(scored_themes)

        for idx, (theme, score) in enumerate(scored_themes):
            if idx == 0 or score >= scored_themes[0][1] * 0.5:
                tier = "一级主线"
            elif idx < total * 0.4 or score >= scored_themes[0][1] * 0.2:
                tier = "二级支线"
            else:
                tier = "一日游杂毛"

            tiers.append({
                "theme_name": theme.theme_name,
                "tier": tier,
                "score": round(score, 1),
                "limit_up_count": theme.limit_up_count,
                "avg_change": round(theme.avg_change_pct, 2),
                "leading_stock": theme.leading_stock,
                "stock_count": len(theme.stocks),
                "total_inflow": theme.total_inflow,
            })

        return tiers

    def _analyze_fund_flow(self, dragon_bonds: List[DragonBond]) -> str:
        """资金行为智能复盘

        分析龙虎榜数据，输出资金动向摘要。

        Args:
            dragon_bonds: 龙虎榜数据

        Returns:
            str: 资金复盘摘要
        """
        if not dragon_bonds:
            return "当日龙虎榜数据暂无"

        # 游资/机构分类统计
        yingyou_buy = sum(db.buy_amount for db in dragon_bonds if db.seat_type == "游资")
        yingyou_sell = sum(db.sell_amount for db in dragon_bonds if db.seat_type == "游资")
        institution_buy = sum(db.buy_amount for db in dragon_bonds if db.seat_type == "机构")
        institution_sell = sum(db.sell_amount for db in dragon_bonds if db.seat_type == "机构")

        yingyou_net = yingyou_buy - yingyou_sell
        institution_net = institution_buy - institution_sell

        parts: List[str] = []
        parts.append(f"游资净{'买入' if yingyou_net > 0 else '卖出'}{abs(yingyou_net)/1e4:.0f}万")
        parts.append(f"机构净{'买入' if institution_net > 0 else '卖出'}{abs(institution_net)/1e4:.0f}万")

        # 主攻方向
        ticker_flow: Dict[str, float] = {}
        for db in dragon_bonds:
            if db.ticker not in ticker_flow:
                ticker_flow[db.ticker] = 0
            ticker_flow[db.ticker] += db.net_amount

        top_tickers = sorted(ticker_flow.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_tickers:
            top_names = [f"{t[0]}({t[1]/1e4:.0f}万)" for t in top_tickers]
            parts.append(f"资金主攻: {', '.join(top_names)}")

        return "; ".join(parts)

    def _compile_report(
        self,
        trade_date: date,
        snapshot: MarketSnapshot,
        indicators: EmotionIndicators,
        diagnosis: EmotionDiagnosis,
        theme_analysis: List[ThemeCycleAnalysis],
        prediction: NextDayPrediction,
        market_summary: str,
        board_ladders: List[BoardLadder],
        theme_tiers: List[Dict],
        fund_summary: str,
        limit_ups: List[LimitUpStock],
        dragon_bonds: List[DragonBond],
    ) -> MarketReplayReport:
        """汇总所有分析结果，生成完整复盘报告

        Args:
            trade_date: 交易日
            snapshot: 市场快照
            indicators: 情绪指标
            diagnosis: 情绪诊断
            theme_analysis: 题材分析
            prediction: 次日预判
            market_summary: 大盘综述
            board_ladders: 连板梯队
            theme_tiers: 题材分级
            fund_summary: 资金摘要
            limit_ups: 涨停股
            dragon_bonds: 龙虎榜

        Returns:
            MarketReplayReport 完整复盘报告
        """
        # 核心结论
        conclusions: List[str] = []

        # 情绪周期结论
        cycle = diagnosis.current_cycle
        conclusions.append(
            f"情绪周期: {cycle.value} (置信度{diagnosis.confidence:.1f}%)，"
            f"建议仓位不超过{diagnosis.position_limit}%"
        )

        # 连板梯队结论
        if board_ladders:
            max_board = board_ladders[0].board_level if board_ladders else 0
            conclusions.append(f"最高连板: {max_board}板，连板情绪{'强势' if max_board >= 5 else '一般' if max_board >= 3 else '弱势'}")

        # 量能结论
        if abs(indicators.volume_change) > 20:
            direction = "异常放大" if indicators.volume_change > 0 else "明显萎缩"
            conclusions.append(f"量能{direction}({indicators.volume_change:.1f}%)，注意节奏变化")

        # 次日交易方向
        attack_themes = [ta.theme_name for ta in theme_analysis
                        if ta.current_stage in (ThemeCycle.SPROUT, ThemeCycle.FERMENT)][:3]
        avoid_themes = [ta.theme_name for ta in theme_analysis
                       if ta.current_stage in (ThemeCycle.DIVERGE, ThemeCycle.RETREAT)][:3]
        backup_themes = [ta.theme_name for ta in theme_analysis
                        if ta.current_stage == ThemeCycle.COMPLEMENT][:2]

        next_day_directions = {
            "主攻方向": attack_themes,
            "备选方向": backup_themes,
            "避雷方向": avoid_themes,
            "适配模式": diagnosis.adapted_mode,
            "核心原则": diagnosis.core_principle,
        }

        # 统计数据
        statistics = {
            "up_count": snapshot.up_count,
            "down_count": snapshot.down_count,
            "limit_up_count": snapshot.limit_up_count,
            "limit_down_count": snapshot.limit_down_count,
            "explode_rate": snapshot.explode_rate,
            "total_volume_wan": round(snapshot.total_volume / 1e4, 2),
            "volume_change_pct": snapshot.volume_change_pct,
            "max_boards": indicators.max_consecutive_boards,
            "theme_count": len(theme_analysis),
            "dragon_bond_count": len(dragon_bonds),
            "emotion_cycle": cycle.value,
            "position_limit": diagnosis.position_limit,
        }

        report = MarketReplayReport(
            trade_date=trade_date,
            market_summary=market_summary,
            board_ladders=board_ladders,
            theme_tiers=theme_tiers,
            fund_summary=fund_summary,
            emotion_diagnosis=diagnosis,
            theme_analysis=theme_analysis,
            next_day_prediction=prediction,
            statistics=statistics,
            key_conclusions=conclusions,
            next_day_directions=next_day_directions,
        )

        return report

    def _generate_mock_themes(self, trade_date: date) -> List[ThemeData]:
        """生成模拟题材数据（Mock，实际应从iFind获取）

        Args:
            trade_date: 交易日

        Returns:
            List[ThemeData]: 模拟题材数据
        """
        mock_themes = [
            ThemeData(
                theme_name="人工智能",
                stocks=["300308.SZ", "002230.SZ", "000938.SZ", "603019.SH"],
                avg_change_pct=5.2,
                total_inflow=1.5e9,
                limit_up_count=12,
                leading_stock="300308.SZ",
                cycle_stage=None,
                description="AI大模型催化，算力需求爆发",
            ),
            ThemeData(
                theme_name="低空经济",
                stocks=["002151.SZ", "300024.SZ", "002097.SZ"],
                avg_change_pct=4.8,
                total_inflow=8e8,
                limit_up_count=8,
                leading_stock="002151.SZ",
                cycle_stage=None,
                description="多地出台低空经济支持政策",
            ),
            ThemeData(
                theme_name="新能源汽车",
                stocks=["300750.SZ", "002594.SZ", "601012.SH", "688223.SH"],
                avg_change_pct=3.1,
                total_inflow=6e8,
                limit_up_count=6,
                leading_stock="300750.SZ",
                cycle_stage=None,
                description="政策利好+销量数据向好",
            ),
            ThemeData(
                theme_name="消费电子",
                stocks=["002475.SZ", "002241.SZ", "300433.SZ"],
                avg_change_pct=2.5,
                total_inflow=3e8,
                limit_up_count=4,
                leading_stock="002475.SZ",
                cycle_stage=None,
                description="Vision Pro销量超预期",
            ),
            ThemeData(
                theme_name="银行保险",
                stocks=["600036.SH", "601318.SH", "601398.SH"],
                avg_change_pct=0.8,
                total_inflow=-1e8,
                limit_up_count=0,
                leading_stock=None,
                cycle_stage=None,
                description="防御性板块，资金流出",
            ),
        ]
        return mock_themes

    # ==================== 便捷查询接口 ====================

    def get_emotion_engine(self) -> EmotionEngine:
        """获取情绪周期研判引擎实例"""
        return self.emotion_engine

    def get_theme_analyzer(self) -> ThemeAnalyzer:
        """获取题材周期分析器实例"""
        return self.theme_analyzer

    def get_market_predictor(self) -> MarketPredictor:
        """获取大盘趋势推演器实例"""
        return self.market_predictor
