"""K线/分时图错误标注器

在K线图和分时图中标注交易错误:
- 买入点标注: 标注买入位置和价格
- 卖出点标注: 标注卖出位置和价格
- 错误标注: 在图中标注具体错误
- 正确操作标注: 标注应该怎么做
- 技术指标标注: 标注关键支撑/压力位

输出格式:
- 文本描述: 详细的图表分析描述
- 标注数据: 结构化的标注点数据(可用于前端渲染)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .importer import TradeRecord
from .trade_diagnoser import TradeDiagnosis

logger = get_logger("swat.m07.chart_annotator")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class ChartPoint:
    """图表标注点"""
    date: str = ""                        # 日期
    time: str = ""                        # 时间(分时图用)
    price: float = 0.0                    # 价格
    label: str = ""                       # 标注文字
    color: str = ""                       # 颜色
    icon: str = ""                        # 图标
    error_type: str = ""                  # 错误类型
    description: str = ""                 # 详细描述


@dataclass
class ChartAnnotation:
    """图表标注结果"""
    ticker: str = ""                      # 股票代码
    stock_name: str = ""                  # 股票名称
    
    # 买入标注
    buy_points: List[ChartPoint] = field(default_factory=list)
    
    # 卖出标注
    sell_points: List[ChartPoint] = field(default_factory=list)
    
    # 错误标注
    error_points: List[ChartPoint] = field(default_factory=list)
    
    # 正确操作标注
    correct_points: List[ChartPoint] = field(default_factory=list)
    
    # 关键位标注
    key_levels: List[ChartPoint] = field(default_factory=list)
    
    # K线图描述
    kline_description: str = ""
    
    # 分时图描述
    intraday_description: str = ""
    
    # 综合描述
    summary: str = ""


# ── 图表标注器 ───────────────────────────────────────────

class ChartAnnotator:
    """K线/分时图错误标注器
    
    在图表中标注交易错误和正确操作。
    """
    
    # 颜色定义
    COLORS = {
        "buy": "#00C853",        # 绿色(买入)
        "sell": "#FF1744",       # 红色(卖出)
        "error": "#FF6D00",      # 橙色(错误)
        "correct": "#2979FF",    # 蓝色(正确)
        "support": "#7C4DFF",    # 紫色(支撑)
        "resistance": "#FFD600", # 黄色(压力)
        "stop_loss": "#FF1744",  # 红色(止损)
        "take_profit": "#00C853",# 绿色(止盈)
    }
    
    def __init__(self):
        """初始化图表标注器"""
        logger.info("图表标注器初始化完成")
    
    def annotate(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        kline_data: Optional[List[Dict]] = None,
        intraday_data: Optional[List[Dict]] = None,
    ) -> ChartAnnotation:
        """标注交易图表
        
        Args:
            trade: 交易记录
            diagnosis: 交易诊断结果
            kline_data: K线数据 [{date, open, high, low, close, volume}, ...]
            intraday_data: 分时数据 [{time, price, volume}, ...]
            
        Returns:
            ChartAnnotation: 图表标注结果
        """
        logger.info(f"标注图表: {trade.stock_name}({trade.ticker})")
        
        annotation = ChartAnnotation(
            ticker=trade.ticker,
            stock_name=trade.stock_name,
        )
        
        # 买入点标注
        self._annotate_buy(trade, annotation)
        
        # 卖出点标注
        self._annotate_sell(trade, annotation)
        
        # 错误标注
        self._annotate_errors(trade, diagnosis, annotation)
        
        # 正确操作标注
        self._annotate_correct(trade, diagnosis, annotation)
        
        # 关键位标注
        self._annotate_key_levels(trade, diagnosis, annotation)
        
        # K线图描述
        annotation.kline_description = self._describe_kline(trade, diagnosis, kline_data)
        
        # 分时图描述
        annotation.intraday_description = self._describe_intraday(trade, diagnosis, intraday_data)
        
        # 综合描述
        annotation.summary = self._build_summary(annotation)
        
        return annotation
    
    # ==================== 买入标注 ====================
    
    def _annotate_buy(self, trade: TradeRecord, annotation: ChartAnnotation):
        """标注买入点"""
        date_str = trade.trade_date.strftime("%Y-%m-%d") if trade.trade_date else ""
        
        point = ChartPoint(
            date=date_str,
            price=trade.price,
            label=f"买入 {trade.price:.2f}元",
            color=self.COLORS["buy"],
            icon="▲",
            description=f"{trade.trade_mode or '买入'} @ {trade.price:.2f}元",
        )
        annotation.buy_points.append(point)
    
    # ==================== 卖出标注 ====================
    
    def _annotate_sell(self, trade: TradeRecord, annotation: ChartAnnotation):
        """标注卖出点(如果有盈亏数据，推算卖出价)"""
        if trade.profit_loss != 0 and trade.amount > 0:
            # 推算卖出价
            sell_price = trade.price + trade.profit_loss / trade.volume
            
            date_str = ""
            if trade.trade_date and trade.hold_days > 0:
                from datetime import timedelta
                sell_date = trade.trade_date + timedelta(days=trade.hold_days)
                date_str = sell_date.strftime("%Y-%m-%d")
            
            pnl_pct = trade.profit_loss_pct
            color = self.COLORS["buy"] if pnl_pct > 0 else self.COLORS["sell"]
            
            point = ChartPoint(
                date=date_str,
                price=sell_price,
                label=f"卖出 {sell_price:.2f}元 ({pnl_pct:+.1f}%)",
                color=color,
                icon="▼",
                description=f"卖出 @ {sell_price:.2f}元 盈亏{pnl_pct:+.1f}%",
            )
            annotation.sell_points.append(point)
    
    # ==================== 错误标注 ====================
    
    def _annotate_errors(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        annotation: ChartAnnotation,
    ):
        """标注错误点"""
        date_str = trade.trade_date.strftime("%Y-%m-%d") if trade.trade_date else ""
        
        for i, error_type in enumerate(diagnosis.error_types):
            detail = diagnosis.error_details[i] if i < len(diagnosis.error_details) else ""
            
            point = ChartPoint(
                date=date_str,
                price=trade.price,
                label=f"❌ {error_type}",
                color=self.COLORS["error"],
                icon="✕",
                error_type=error_type,
                description=detail,
            )
            annotation.error_points.append(point)
    
    # ==================== 正确操作标注 ====================
    
    def _annotate_correct(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        annotation: ChartAnnotation,
    ):
        """标注正确操作"""
        date_str = trade.trade_date.strftime("%Y-%m-%d") if trade.trade_date else ""
        
        if diagnosis.scoring_report and diagnosis.scoring_report.risk_reward:
            rr = diagnosis.scoring_report.risk_reward
            
            # 正确入场
            if not diagnosis.should_buy:
                point = ChartPoint(
                    date=date_str,
                    price=trade.price,
                    label="✓ 不应买入，应观望",
                    color=self.COLORS["correct"],
                    icon="✓",
                    description=f"评分{diagnosis.scoring_report.total_score}分，不应介入",
                )
                annotation.correct_points.append(point)
            else:
                # 正确止损位
                point = ChartPoint(
                    date=date_str,
                    price=rr.stop_loss_price,
                    label=f"止损位 {rr.stop_loss_price:.2f}元",
                    color=self.COLORS["stop_loss"],
                    icon="⊥",
                    description=f"止损: {rr.stop_loss_price:.2f}元 (-{rr.risk_pct}%)",
                )
                annotation.correct_points.append(point)
                
                # 正确止盈位
                point = ChartPoint(
                    date=date_str,
                    price=rr.take_profit_price,
                    label=f"止盈位 {rr.take_profit_price:.2f}元",
                    color=self.COLORS["take_profit"],
                    icon="⊤",
                    description=f"止盈: {rr.take_profit_price:.2f}元 (+{rr.reward_pct}%)",
                )
                annotation.correct_points.append(point)
    
    # ==================== 关键位标注 ====================
    
    def _annotate_key_levels(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        annotation: ChartAnnotation,
    ):
        """标注关键支撑/压力位"""
        if diagnosis.scoring_report and diagnosis.scoring_report.risk_reward:
            rr = diagnosis.scoring_report.risk_reward
            
            # 支撑位(止损位附近)
            point = ChartPoint(
                price=rr.stop_loss_price,
                label=f"支撑 {rr.stop_loss_price:.2f}",
                color=self.COLORS["support"],
                icon="—",
                description=f"关键支撑位: {rr.stop_loss_price:.2f}元",
            )
            annotation.key_levels.append(point)
            
            # 压力位(止盈位附近)
            point = ChartPoint(
                price=rr.take_profit_price,
                label=f"压力 {rr.take_profit_price:.2f}",
                color=self.COLORS["resistance"],
                icon="—",
                description=f"关键压力位: {rr.take_profit_price:.2f}元",
            )
            annotation.key_levels.append(point)
    
    # ==================== K线图描述 ====================
    
    def _describe_kline(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        kline_data: Optional[List[Dict]],
    ) -> str:
        """生成K线图描述"""
        parts: List[str] = []
        
        parts.append(f"📈 K线图分析 - {trade.stock_name}({trade.ticker})")
        parts.append("")
        
        # 买入位置描述
        parts.append(f"📍 买入位置:")
        parts.append(f"   日期: {trade.trade_date.strftime('%Y-%m-%d') if trade.trade_date else '未知'}")
        parts.append(f"   价格: {trade.price:.2f}元")
        parts.append(f"   模式: {trade.trade_mode or '未知'}")
        parts.append("")
        
        # 错误标注
        if diagnosis.error_types:
            parts.append("❌ 错误标注:")
            for i, error in enumerate(diagnosis.error_types):
                detail = diagnosis.error_details[i] if i < len(diagnosis.error_details) else ""
                parts.append(f"   • {error}")
                if detail:
                    parts.append(f"     → {detail}")
            parts.append("")
        
        # 正确操作
        if diagnosis.correct_advice:
            parts.append("💡 正确操作:")
            for line in diagnosis.correct_advice.split("\n"):
                parts.append(f"   {line}")
            parts.append("")
        
        # 如果有K线数据，分析形态
        if kline_data and len(kline_data) >= 5:
            parts.append("📊 K线形态分析:")
            self._analyze_kline_pattern(kline_data, trade, parts)
            parts.append("")
        
        return "\n".join(parts)
    
    def _analyze_kline_pattern(
        self,
        kline_data: List[Dict],
        trade: TradeRecord,
        parts: List[str],
    ):
        """分析K线形态"""
        if len(kline_data) < 5:
            return
        
        # 最近5根K线
        recent = kline_data[-5:]
        
        # 判断趋势
        closes = [k.get("close", 0) for k in recent]
        if closes[-1] > closes[0] * 1.03:
            parts.append("   趋势: 短期上涨")
        elif closes[-1] < closes[0] * 0.97:
            parts.append("   趋势: 短期下跌")
        else:
            parts.append("   趋势: 横盘震荡")
        
        # 买入位置相对高低
        if trade.price > max(closes) * 0.98:
            parts.append(f"   买入位置: 高位(接近近期高点{max(closes):.2f})")
            if trade.profit_loss < 0:
                parts.append("   ⚠️ 高位买入是亏损主因")
        elif trade.price < min(closes) * 1.02:
            parts.append(f"   买入位置: 低位(接近近期低点{min(closes):.2f})")
        else:
            parts.append(f"   买入位置: 中位")
        
        # 量能分析
        volumes = [k.get("volume", 0) for k in recent]
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        if volumes[-1] > avg_vol * 1.5:
            parts.append("   量能: 放量")
        elif volumes[-1] < avg_vol * 0.7:
            parts.append("   量能: 缩量")
        else:
            parts.append("   量能: 平量")
    
    # ==================== 分时图描述 ====================
    
    def _describe_intraday(
        self,
        trade: TradeRecord,
        diagnosis: TradeDiagnosis,
        intraday_data: Optional[List[Dict]],
    ) -> str:
        """生成分时图描述"""
        parts: List[str] = []
        
        parts.append(f"📉 分时图分析 - {trade.stock_name}({trade.ticker})")
        parts.append("")
        
        # 买入时点
        parts.append(f"📍 买入时点:")
        parts.append(f"   价格: {trade.price:.2f}元")
        parts.append(f"   模式: {trade.trade_mode or '未知'}")
        parts.append("")
        
        # 如果有分时数据
        if intraday_data and len(intraday_data) > 10:
            parts.append("📊 分时走势分析:")
            self._analyze_intraday_pattern(intraday_data, trade, parts)
            parts.append("")
        
        # 错误时点标注
        if diagnosis.is_error_trade:
            parts.append("❌ 错误时点标注:")
            parts.append(f"   在{trade.price:.2f}元买入时:")
            for error in diagnosis.error_types:
                parts.append(f"   • {error}")
            parts.append("")
            
            parts.append("💡 正确做法:")
            if not diagnosis.should_buy:
                parts.append("   此时不应买入，应等待更好的机会")
            else:
                parts.append(f"   应在更低位置买入，或等待确认信号")
        
        return "\n".join(parts)
    
    def _analyze_intraday_pattern(
        self,
        intraday_data: List[Dict],
        trade: TradeRecord,
        parts: List[str],
    ):
        """分析分时走势"""
        prices = [d.get("price", 0) for d in intraday_data]
        
        if not prices:
            return
        
        # 日内高低点
        high = max(prices)
        low = min(prices)
        open_price = prices[0]
        close_price = prices[-1]
        
        parts.append(f"   开盘: {open_price:.2f} | 最高: {high:.2f} | 最低: {low:.2f} | 收盘: {close_price:.2f}")
        
        # 买入位置
        buy_position = (trade.price - low) / (high - low) * 100 if high > low else 50
        parts.append(f"   买入位置: 日内{buy_position:.0f}%分位")
        
        if buy_position > 80:
            parts.append("   ⚠️ 买入在日内高位，追高风险大")
        elif buy_position < 20:
            parts.append("   ✓ 买入在日内低位，位置较好")
        
        # 走势判断
        if close_price > open_price * 1.02:
            parts.append("   日内走势: 强势上涨")
        elif close_price < open_price * 0.98:
            parts.append("   日内走势: 弱势下跌")
        else:
            parts.append("   日内走势: 震荡整理")
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, annotation: ChartAnnotation) -> str:
        """构建摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║     图表标注 - {annotation.stock_name}({annotation.ticker})")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        # 标注统计
        parts.append(f"📍 标注统计:")
        parts.append(f"   买入点: {len(annotation.buy_points)}个")
        parts.append(f"   卖出点: {len(annotation.sell_points)}个")
        parts.append(f"   错误标注: {len(annotation.error_points)}个")
        parts.append(f"   正确标注: {len(annotation.correct_points)}个")
        parts.append(f"   关键位: {len(annotation.key_levels)}个")
        parts.append("")
        
        # 错误标注详情
        if annotation.error_points:
            parts.append("❌ 错误标注:")
            for point in annotation.error_points:
                parts.append(f"   • {point.label}")
                if point.description:
                    parts.append(f"     → {point.description}")
            parts.append("")
        
        # 正确操作
        if annotation.correct_points:
            parts.append("💡 正确操作:")
            for point in annotation.correct_points:
                parts.append(f"   • {point.label}")
            parts.append("")
        
        return "\n".join(parts)