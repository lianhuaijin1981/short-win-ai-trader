"""高频错误类型归因

识别用户交易中的高频错误类型:
- 标的选择错误: 跟风股/弱势股/高位接盘
- 时机选择错误: 退潮期买入/高潮期追涨/冰点恐慌
- 模式选择错误: 打板模式用在低吸场景等
- 仓位管理错误: 重仓弱势股/轻仓强势股/满仓操作
- 止损执行错误: 不止损/止损过晚/止损过早
- 止盈执行错误: 贪心不止盈/止盈过早/坐过山车
- 情绪化交易: FOMO追涨/报复性交易/恐慌性卖出
- 认知偏差: 过度自信/锚定效应/确认偏误

归因方法:
- 统计各错误类型出现频率
- 计算各错误类型造成的总亏损
- 识别错误模式之间的关联性
- 生成错误优先级排序
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .importer import TradeRecord

logger = get_logger("swat.m07.error_attribution")


# ── 枚举定义 ─────────────────────────────────────────────

class ErrorType(str, Enum):
    """错误类型"""
    # 标的选择类
    WRONG_STOCK = "标的选择错误"          # 选了不该买的股票
    FOLLOW_WEAK = "跟风弱势股"            # 买入跟风股/弱势股
    HIGH_CHASE = "高位接盘"               # 高位追涨接盘
    
    # 时机选择类
    WRONG_TIMING = "时机选择错误"         # 买入时机不对
    RETREAT_BUY = "退潮期买入"            # 退潮期逆势买入
    CLIMAX_CHASE = "高潮期追涨"           # 高潮期追高
    
    # 模式选择类
    WRONG_MODE = "模式选择错误"           # 交易模式不匹配
    MODE_MISMATCH = "模式与场景不匹配"     # 打板用在低吸场景等
    
    # 仓位管理类
    WRONG_POSITION = "仓位管理错误"       # 仓位分配不合理
    OVER_POSITION = "仓位过重"            # 重仓/满仓操作
    UNDER_POSITION = "仓位过轻"           # 强势股仓位太轻
    
    # 止损执行类
    NO_STOP_LOSS = "不止损"               # 亏损不止损
    LATE_STOP_LOSS = "止损过晚"           # 止损执行太迟
    EARLY_STOP_LOSS = "止损过早"          # 止损后被拉起
    
    # 止盈执行类
    NO_TAKE_PROFIT = "不止盈"             # 盈利不止盈
    EARLY_TAKE_PROFIT = "止盈过早"        # 卖飞
    ROUND_TRIP = "坐过山车"               # 盈利变亏损
    
    # 情绪化交易类
    FOMO = "FOMO追涨"                     # 害怕错过而追涨
    REVENGE_TRADE = "报复性交易"          # 亏损后急于翻本
    PANIC_SELL = "恐慌性卖出"             # 恐慌性割肉
    
    # 认知偏差类
    OVER_CONFIDENCE = "过度自信"          # 过度自信导致冒进
    ANCHORING = "锚定效应"               # 锚定成本价不愿卖出
    CONFIRMATION_BIAS = "确认偏误"        # 只看利好忽视风险


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    CRITICAL = "严重"     # 导致重大亏损
    HIGH = "较高"         # 导致明显亏损
    MEDIUM = "中等"       # 导致小幅亏损
    LOW = "轻微"          # 轻微影响


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class ErrorPattern:
    """错误模式"""
    error_type: ErrorType = ErrorType.WRONG_STOCK
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    frequency: int = 0                    # 出现次数
    frequency_pct: float = 0.0            # 频率(%)
    total_loss: float = 0.0               # 总亏损金额
    avg_loss: float = 0.0                 # 平均亏损
    max_loss: float = 0.0                 # 最大单笔亏损
    related_trades: List[str] = field(default_factory=list)  # 相关交易ID
    description: str = ""                 # 错误描述
    improvement: str = ""                 # 改进建议


@dataclass
class AttributionResult:
    """归因结果"""
    total_errors: int = 0                 # 总错误数
    error_patterns: List[ErrorPattern] = field(default_factory=list)  # 错误模式列表
    top_errors: List[ErrorPattern] = field(default_factory=list)  # Top错误(按亏损排序)
    high_frequency_errors: List[ErrorPattern] = field(default_factory=list)  # 高频错误
    total_loss_from_errors: float = 0.0   # 错误导致的总亏损
    summary: str = ""                     # 归因摘要


# ── 错误归因器 ───────────────────────────────────────────

class ErrorAttribution:
    """高频错误类型归因器
    
    识别和量化交易中的高频错误类型。
    """
    
    # 错误类型权重(用于计算严重程度)
    SEVERITY_WEIGHTS = {
        ErrorType.NO_STOP_LOSS: 1.5,
        ErrorType.OVER_POSITION: 1.3,
        ErrorType.FOMO: 1.2,
        ErrorType.REVENGE_TRADE: 1.3,
        ErrorType.PANIC_SELL: 1.1,
        ErrorType.HIGH_CHASE: 1.2,
        ErrorType.RETREAT_BUY: 1.2,
        ErrorType.WRONG_STOCK: 1.0,
        ErrorType.WRONG_TIMING: 1.0,
        ErrorType.WRONG_MODE: 0.8,
        ErrorType.EARLY_TAKE_PROFIT: 0.7,
        ErrorType.EARLY_STOP_LOSS: 0.6,
    }
    
    def __init__(self):
        """初始化错误归因器"""
        logger.info("错误归因器初始化完成")
    
    def analyze(self, trades: List[TradeRecord]) -> AttributionResult:
        """分析交易错误
        
        Args:
            trades: 交易记录列表
            
        Returns:
            AttributionResult: 归因结果
        """
        if not trades:
            return AttributionResult()
        
        logger.info(f"开始错误归因: {len(trades)}笔交易")
        
        result = AttributionResult()
        
        # 检测各类错误
        all_errors: Dict[ErrorType, List[TradeRecord]] = {}
        
        # 1. 标的选择错误
        self._detect_stock_errors(trades, all_errors)
        
        # 2. 时机选择错误
        self._detect_timing_errors(trades, all_errors)
        
        # 3. 模式选择错误
        self._detect_mode_errors(trades, all_errors)
        
        # 4. 仓位管理错误
        self._detect_position_errors(trades, all_errors)
        
        # 5. 止损执行错误
        self._detect_stop_loss_errors(trades, all_errors)
        
        # 6. 止盈执行错误
        self._detect_take_profit_errors(trades, all_errors)
        
        # 7. 情绪化交易
        self._detect_emotion_errors(trades, all_errors)
        
        # 构建错误模式
        for error_type, error_trades in all_errors.items():
            pattern = self._build_error_pattern(error_type, error_trades, len(trades))
            result.error_patterns.append(pattern)
        
        # 排序
        result.error_patterns.sort(key=lambda p: p.total_loss, reverse=True)
        
        # Top错误(按亏损)
        result.top_errors = result.error_patterns[:5]
        
        # 高频错误(频率>15%)
        result.high_frequency_errors = [
            p for p in result.error_patterns if p.frequency_pct > 15
        ]
        
        # 统计
        result.total_errors = sum(p.frequency for p in result.error_patterns)
        result.total_loss_from_errors = sum(p.total_loss for p in result.error_patterns)
        
        # 生成摘要
        result.summary = self._build_summary(result)
        
        logger.info(f"错误归因完成: {result.total_errors}个错误, 总亏损{result.total_loss_from_errors:.0f}元")
        return result
    
    # ==================== 错误检测 ====================
    
    def _detect_stock_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测标的选择错误"""
        for trade in trades:
            if trade.profit_loss < 0:
                # 跟风股亏损
                if "跟风" in (trade.notes or ""):
                    self._add_error(errors, ErrorType.FOLLOW_WEAK, trade)
                # 高位接盘(亏损>5%)
                elif trade.profit_loss_pct < -5:
                    self._add_error(errors, ErrorType.HIGH_CHASE, trade)
                # 一般标的错误
                else:
                    self._add_error(errors, ErrorType.WRONG_STOCK, trade)
    
    def _detect_timing_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测时机选择错误"""
        for trade in trades:
            if trade.profit_loss < 0:
                # 退潮期买入
                if trade.emotion_cycle in ("退潮", "退潮期"):
                    self._add_error(errors, ErrorType.RETREAT_BUY, trade)
                # 高潮期追涨
                elif trade.emotion_cycle in ("高潮", "高潮期") and trade.trade_mode == "打板":
                    self._add_error(errors, ErrorType.CLIMAX_CHASE, trade)
                # 一般时机错误
                elif trade.profit_loss_pct < -3:
                    self._add_error(errors, ErrorType.WRONG_TIMING, trade)
    
    def _detect_mode_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测模式选择错误"""
        for trade in trades:
            if trade.profit_loss < 0:
                # 低吸模式但买入涨停股
                if trade.trade_mode == "低吸" and trade.profit_loss_pct < -5:
                    self._add_error(errors, ErrorType.MODE_MISMATCH, trade)
                # 打板模式但非涨停买入
                elif trade.trade_mode == "打板" and trade.profit_loss_pct < -3:
                    self._add_error(errors, ErrorType.WRONG_MODE, trade)
    
    def _detect_position_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测仓位管理错误"""
        for trade in trades:
            if trade.profit_loss < 0 and trade.amount > 0:
                # 大额亏损(仓位过重)
                if trade.amount > 100000 and trade.profit_loss_pct < -5:
                    self._add_error(errors, ErrorType.OVER_POSITION, trade)
                # 小额盈利(仓位过轻)
                elif trade.profit_loss > 0 and trade.amount < 20000 and trade.profit_loss_pct > 5:
                    self._add_error(errors, ErrorType.UNDER_POSITION, trade)
    
    def _detect_stop_loss_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测止损执行错误"""
        for trade in trades:
            if trade.profit_loss < 0:
                # 大亏损(不止损)
                if trade.profit_loss_pct < -8:
                    self._add_error(errors, ErrorType.NO_STOP_LOSS, trade)
                # 中等亏损(止损过晚)
                elif trade.profit_loss_pct < -5:
                    self._add_error(errors, ErrorType.LATE_STOP_LOSS, trade)
    
    def _detect_take_profit_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测止盈执行错误"""
        for trade in trades:
            # 止盈过早(盈利但<2%)
            if 0 < trade.profit_loss_pct < 2 and trade.hold_days >= 2:
                self._add_error(errors, ErrorType.EARLY_TAKE_PROFIT, trade)
            # 坐过山车(持仓多天但最终亏损)
            elif trade.profit_loss < 0 and trade.hold_days >= 3:
                self._add_error(errors, ErrorType.ROUND_TRIP, trade)
    
    def _detect_emotion_errors(self, trades: List[TradeRecord], errors: Dict):
        """检测情绪化交易"""
        sorted_trades = sorted(trades, key=lambda t: t.trade_date or datetime.min)
        
        for i, trade in enumerate(sorted_trades):
            if trade.profit_loss < 0:
                # FOMO: 连续上涨后追高买入
                if trade.trade_mode == "打板" and trade.profit_loss_pct < -5:
                    self._add_error(errors, ErrorType.FOMO, trade)
                
                # 报复性交易: 前一笔亏损后立即大额买入
                if i > 0:
                    prev = sorted_trades[i - 1]
                    if prev.profit_loss < 0 and trade.amount > prev.amount * 1.5:
                        self._add_error(errors, ErrorType.REVENGE_TRADE, trade)
                
                # 恐慌性卖出: 小幅下跌就割肉
                if trade.profit_loss_pct > -3 and trade.profit_loss_pct < 0 and trade.hold_days <= 1:
                    self._add_error(errors, ErrorType.PANIC_SELL, trade)
    
    # ==================== 辅助方法 ====================
    
    def _add_error(self, errors: Dict, error_type: ErrorType, trade: TradeRecord):
        """添加错误记录"""
        if error_type not in errors:
            errors[error_type] = []
        errors[error_type].append(trade)
    
    def _build_error_pattern(
        self, 
        error_type: ErrorType, 
        error_trades: List[TradeRecord],
        total_trades: int,
    ) -> ErrorPattern:
        """构建错误模式"""
        losses = [t.profit_loss for t in error_trades if t.profit_loss < 0]
        
        frequency = len(error_trades)
        frequency_pct = round(frequency / total_trades * 100, 1) if total_trades > 0 else 0
        total_loss = sum(losses) if losses else 0
        avg_loss = round(total_loss / len(losses), 2) if losses else 0
        max_loss = min(losses) if losses else 0
        
        # 确定严重程度
        severity = self._determine_severity(error_type, frequency_pct, total_loss)
        
        # 错误描述
        description = self._get_error_description(error_type, frequency, total_loss)
        
        # 改进建议
        improvement = self._get_improvement_suggestion(error_type)
        
        return ErrorPattern(
            error_type=error_type,
            severity=severity,
            frequency=frequency,
            frequency_pct=frequency_pct,
            total_loss=round(total_loss, 2),
            avg_loss=avg_loss,
            max_loss=max_loss,
            related_trades=[t.trade_id for t in error_trades],
            description=description,
            improvement=improvement,
        )
    
    def _determine_severity(
        self, 
        error_type: ErrorType, 
        frequency_pct: float, 
        total_loss: float,
    ) -> ErrorSeverity:
        """确定错误严重程度"""
        weight = self.SEVERITY_WEIGHTS.get(error_type, 1.0)
        score = frequency_pct * weight + abs(total_loss) / 1000
        
        if score >= 50:
            return ErrorSeverity.CRITICAL
        elif score >= 30:
            return ErrorSeverity.HIGH
        elif score >= 15:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _get_error_description(
        self, 
        error_type: ErrorType, 
        frequency: int, 
        total_loss: float,
    ) -> str:
        """获取错误描述"""
        descriptions = {
            ErrorType.WRONG_STOCK: f"标的选择不当，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.FOLLOW_WEAK: f"买入跟风弱势股，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.HIGH_CHASE: f"高位追涨接盘，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.WRONG_TIMING: f"买入时机不当，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.RETREAT_BUY: f"退潮期逆势买入，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.CLIMAX_CHASE: f"高潮期追涨，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.WRONG_MODE: f"交易模式选择错误，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.MODE_MISMATCH: f"模式与场景不匹配，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.OVER_POSITION: f"仓位过重导致大亏，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.UNDER_POSITION: f"强势股仓位过轻，错失盈利机会",
            ErrorType.NO_STOP_LOSS: f"亏损不止损，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.LATE_STOP_LOSS: f"止损执行过晚，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.EARLY_STOP_LOSS: f"止损过早被洗出，{frequency}笔交易",
            ErrorType.NO_TAKE_PROFIT: f"盈利不止盈，利润回吐",
            ErrorType.EARLY_TAKE_PROFIT: f"止盈过早卖飞，{frequency}笔交易",
            ErrorType.ROUND_TRIP: f"坐过山车盈利变亏损，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.FOMO: f"FOMO情绪追涨，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.REVENGE_TRADE: f"报复性交易，{frequency}笔交易亏损{abs(total_loss):.0f}元",
            ErrorType.PANIC_SELL: f"恐慌性卖出，{frequency}笔交易",
            ErrorType.OVER_CONFIDENCE: f"过度自信导致冒进",
            ErrorType.ANCHORING: f"锚定成本价不愿止损",
            ErrorType.CONFIRMATION_BIAS: f"只看利好忽视风险",
        }
        return descriptions.get(error_type, f"{error_type.value}: {frequency}笔交易")
    
    def _get_improvement_suggestion(self, error_type: ErrorType) -> str:
        """获取改进建议"""
        suggestions = {
            ErrorType.WRONG_STOCK: "提高选股标准，只做龙头/先锋，规避跟风股",
            ErrorType.FOLLOW_WEAK: "坚持只做板块龙头和先锋，不碰跟风股",
            ErrorType.HIGH_CHASE: "控制追高冲动，等待分歧低吸机会",
            ErrorType.WRONG_TIMING: "学习情绪周期判断，在启动/发酵期操作",
            ErrorType.RETREAT_BUY: "退潮期管住手，等待情绪冰点后再出手",
            ErrorType.CLIMAX_CHASE: "高潮期不追涨，等待次日分歧机会",
            ErrorType.WRONG_MODE: "根据市场状态选择合适交易模式",
            ErrorType.MODE_MISMATCH: "明确每种模式的适用场景，不混用",
            ErrorType.OVER_POSITION: "严格控制单票仓位不超过30%，弱势股不超过10%",
            ErrorType.UNDER_POSITION: "高确定性标的敢于上仓位",
            ErrorType.NO_STOP_LOSS: "严格执行止损纪律，亏损达5%无条件卖出",
            ErrorType.LATE_STOP_LOSS: "设定明确止损位，触发即执行，不犹豫",
            ErrorType.EARLY_STOP_LOSS: "优化止损位设置，避免被正常波动洗出",
            ErrorType.NO_TAKE_PROFIT: "设定目标止盈位，达到后分批卖出",
            ErrorType.EARLY_TAKE_PROFIT: "学会锁仓，趋势未破不轻易卖出",
            ErrorType.ROUND_TRIP: "盈利后设置移动止损，保护利润",
            ErrorType.FOMO: "克服FOMO心理，宁可错过不可做错",
            ErrorType.REVENGE_TRADE: "亏损后冷静30分钟再操作，不急于翻本",
            ErrorType.PANIC_SELL: "避免恐慌性卖出，按交易计划执行",
            ErrorType.OVER_CONFIDENCE: "保持敬畏之心，连胜后更要谨慎",
            ErrorType.ANCHORING: "忘掉成本价，只看当前市场状态做决策",
            ErrorType.CONFIRMATION_BIAS: "主动寻找反面证据，客观评估风险",
        }
        return suggestions.get(error_type, "需要改进")
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, result: AttributionResult) -> str:
        """构建归因摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║       高频错误类型归因分析            ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        parts.append(f"📊 错误统计:")
        parts.append(f"   总错误数: {result.total_errors}")
        parts.append(f"   错误导致总亏损: {abs(result.total_loss_from_errors):.0f}元")
        parts.append("")
        
        if result.top_errors:
            parts.append("🔴 Top错误(按亏损排序):")
            for i, pattern in enumerate(result.top_errors, 1):
                severity_icon = {"严重": "🔴", "较高": "🟠", "中等": "🟡", "轻微": "🟢"}.get(pattern.severity.value, "⚪")
                parts.append(f"   {i}. {severity_icon} {pattern.error_type.value}")
                parts.append(f"      频率: {pattern.frequency}次({pattern.frequency_pct}%) | 亏损: {abs(pattern.total_loss):.0f}元 | 均亏: {abs(pattern.avg_loss):.0f}元")
                parts.append(f"      改进: {pattern.improvement}")
            parts.append("")
        
        if result.high_frequency_errors:
            parts.append("⚠️ 高频错误(频率>15%):")
            for pattern in result.high_frequency_errors:
                parts.append(f"   • {pattern.error_type.value}: {pattern.frequency_pct}% - {pattern.description}")
            parts.append("")
        
        return "\n".join(parts)