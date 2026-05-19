"""智能信号识别引擎 — 盘中看盘核心组件

实时识别A股超短交易中的关键盘口信号:
- 竞价信号: 竞价抢筹、竞价核按钮、竞价异动
- 盘口信号: 大单点火、封板加速、炸板预警、回封确认
- 量价信号: 放量突破、缩量回调、天量天价、地量地价
- 情绪信号: 板块共振、情绪冰点、情绪高潮、分歧转一致

信号分级:
- critical: 必须立即关注（核按钮、炸板无承接）
- high: 重点关注（竞价抢筹、回封确认）
- normal: 常规关注（量价异动、板块轮动）
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    ExpectationLevel,
    LimitUpStock,
    ThemeData,
)

logger = get_logger("swat.m03.signal_detector")


# ── 常量定义 ────────────────────────────────────────────

# 竞价信号阈值
AUCTION_SNATCH_VOL_RATIO = 3.0        # 竞价抢筹量比阈值
AUCTION_NUKE_DROP = -5.0              # 核按钮跌幅阈值(%)
AUCTION_UNUSUAL_CHANGE = 4.0          # 竞价异动幅度阈值(%)

# 盘口信号阈值
IGNITION_BIG_ORDER = 1e6              # 点火大单阈值(元)
SEAL_ACCELERATE_RATIO = 2.0           # 封板加速量比
EXPLODE_WARNING_DROP = -3.0           # 炸板预警跌幅(%)
RESEAL_CONFIRM_VOL = 1.5              # 回封确认量比

# 量价信号阈值
VOLUME_BREAKOUT_RATIO = 2.5           # 放量突破量比
SHRINK_PULLBACK_RATIO = 0.5           # 缩量回调量比
SKY_VOLUME_RATIO = 5.0                # 天量量比阈值
GROUND_VOLUME_RATIO = 0.3             # 地量量比阈值

# 情绪信号阈值
SECTOR_RESONANCE_COUNT = 5            # 板块共振涨停数
EMOTION_ICE_LIMIT_DOWN = 10           # 情绪冰点跌停数
EMOTION_PEAK_LIMIT_UP = 50            # 情绪高潮涨停数
DIVERGE_TO_CONSENSUS_RATE = 0.7       # 分歧转一致回封率

# 信号冷却时间(秒)
SIGNAL_COOLDOWN = 300                 # 同一信号5分钟内不重复


class SignalType(str, Enum):
    """信号类型"""
    # 竞价信号
    AUCTION_SNATCH = "竞价抢筹"
    AUCTION_NUKE = "竞价核按钮"
    AUCTION_UNUSUAL = "竞价异动"
    
    # 盘口信号
    BIG_ORDER_IGNITION = "大单点火"
    SEAL_ACCELERATE = "封板加速"
    EXPLODE_WARNING = "炸板预警"
    RESEAL_CONFIRM = "回封确认"
    
    # 量价信号
    VOLUME_BREAKOUT = "放量突破"
    SHRINK_PULLBACK = "缩量回调"
    SKY_VOLUME = "天量天价"
    GROUND_VOLUME = "地量地价"
    
    # 情绪信号
    SECTOR_RESONANCE = "板块共振"
    EMOTION_ICE = "情绪冰点"
    EMOTION_PEAK = "情绪高潮"
    DIVERGE_TO_CONSENSUS = "分歧转一致"


class SignalPriority(str, Enum):
    """信号优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class TradingSignal:
    """交易信号"""
    signal_type: SignalType = SignalType.AUCTION_UNUSUAL
    priority: SignalPriority = SignalPriority.NORMAL
    ticker: str = ""
    name: str = ""
    timestamp: Optional[datetime] = None
    description: str = ""
    trigger_condition: str = ""
    action_suggestion: str = ""
    related_data: Dict = field(default_factory=dict)
    confidence: float = 0.0           # 信号置信度 0-1


@dataclass
class SignalSummary:
    """信号汇总"""
    timestamp: Optional[datetime] = None
    critical_signals: List[TradingSignal] = field(default_factory=list)
    high_signals: List[TradingSignal] = field(default_factory=list)
    normal_signals: List[TradingSignal] = field(default_factory=list)
    market_mood: str = ""             # 市场情绪: 冰点/低迷/正常/活跃/高潮
    key_opportunities: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    summary_text: str = ""


class SignalDetector:
    """智能信号识别引擎
    
    实时检测盘口关键信号，为超短选手提供出手/撤退依据。
    
    Attributes:
        config: 应用配置
        _signal_history: 信号历史缓存
        _last_signal_time: 上次信号时间（用于冷却）
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """初始化信号识别引擎
        
        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._signal_history: List[TradingSignal] = []
        self._last_signal_time: Dict[str, datetime] = {}
        self._market_mood = "正常"
        logger.info("智能信号识别引擎初始化完成")
    
    # ==================== 核心公共接口 ====================
    
    async def detect_signals(
        self,
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        real_time_data: Dict[str, Dict],
        market_snapshot: Optional[Dict] = None,
    ) -> SignalSummary:
        """信号检测主入口
        
        执行完整检测流程: 竞价信号 → 盘口信号 → 量价信号 → 情绪信号
        
        Args:
            anchors: 锚定标的列表
            limit_up_stocks: 涨停股列表
            themes: 题材列表
            real_time_data: 实时数据 {ticker: {...}}
            market_snapshot: 市场快照数据
            
        Returns:
            SignalSummary: 信号汇总
            
        Raises:
            ModuleError: 检测过程发生严重错误
        """
        logger.info("========== 开始智能信号检测 ==========")
        
        try:
            all_signals: List[TradingSignal] = []
            
            # Step 1: 竞价信号检测
            logger.info("[Step 1/4] 检测竞价信号...")
            auction_signals = self._detect_auction_signals(anchors, real_time_data)
            all_signals.extend(auction_signals)
            
            # Step 2: 盘口信号检测
            logger.info("[Step 2/4] 检测盘口信号...")
            disk_signals = self._detect_disk_signals(anchors, limit_up_stocks, real_time_data)
            all_signals.extend(disk_signals)
            
            # Step 3: 量价信号检测
            logger.info("[Step 3/4] 检测量价信号...")
            volume_signals = self._detect_volume_signals(anchors, real_time_data)
            all_signals.extend(volume_signals)
            
            # Step 4: 情绪信号检测
            logger.info("[Step 4/4] 检测情绪信号...")
            emotion_signals = self._detect_emotion_signals(
                limit_up_stocks, themes, market_snapshot
            )
            all_signals.extend(emotion_signals)
            
            # 过滤冷却期内的重复信号
            all_signals = self._apply_cooldown(all_signals)
            
            # 生成汇总
            summary = self._compile_summary(all_signals, market_snapshot)
            
            # 缓存
            self._signal_history.extend(all_signals)
            # 只保留最近100条
            if len(self._signal_history) > 100:
                self._signal_history = self._signal_history[-100:]
            
            logger.info(
                f"信号检测完成: 共{len(all_signals)}条信号, "
                f"critical={len(summary.critical_signals)}, "
                f"high={len(summary.high_signals)}"
            )
            return summary
            
        except Exception as e:
            logger.error(f"信号检测严重错误: {e}")
            raise ModuleError(f"信号检测失败: {e}")
    
    def get_recent_signals(
        self, 
        minutes: int = 30,
        signal_type: Optional[SignalType] = None,
    ) -> List[TradingSignal]:
        """获取最近N分钟的信号
        
        Args:
            minutes: 时间窗口(分钟)
            signal_type: 信号类型过滤
            
        Returns:
            List[TradingSignal]: 信号列表
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        signals = [
            s for s in self._signal_history
            if s.timestamp and s.timestamp >= cutoff
        ]
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        return signals
    
    def get_market_mood(self) -> str:
        """获取当前市场情绪状态
        
        Returns:
            str: 市场情绪
        """
        return self._market_mood
    
    # ==================== 竞价信号检测 ====================
    
    def _detect_auction_signals(
        self,
        anchors: List[AnchorStock],
        real_time_data: Dict[str, Dict],
    ) -> List[TradingSignal]:
        """检测竞价阶段信号
        
        Args:
            anchors: 锚定标的
            real_time_data: 实时数据
            
        Returns:
            List[TradingSignal]: 竞价信号列表
        """
        signals: List[TradingSignal] = []
        now = datetime.now()
        
        for anchor in anchors:
            ticker = anchor.ticker
            if ticker not in real_time_data:
                continue
                
            rt = real_time_data[ticker]
            open_high = rt.get("open_high_pct", 0)
            vol_ratio = rt.get("volume_ratio", 0)
            
            # 竞价抢筹: 高开+巨量
            if open_high >= 5 and vol_ratio >= AUCTION_SNATCH_VOL_RATIO:
                signals.append(TradingSignal(
                    signal_type=SignalType.AUCTION_SNATCH,
                    priority=SignalPriority.HIGH,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}竞价抢筹，高开{open_high:.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition=f"高开≥5% 且 量比≥{AUCTION_SNATCH_VOL_RATIO}",
                    action_suggestion="竞价超预期，开盘观察承接可考虑跟随",
                    related_data={"open_high": open_high, "vol_ratio": vol_ratio},
                    confidence=min(1.0, 0.6 + (vol_ratio - AUCTION_SNATCH_VOL_RATIO) * 0.1),
                ))
            
            # 竞价核按钮: 大幅低开
            elif open_high <= AUCTION_NUKE_DROP:
                signals.append(TradingSignal(
                    signal_type=SignalType.AUCTION_NUKE,
                    priority=SignalPriority.CRITICAL,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}竞价核按钮，低开{abs(open_high):.1f}%",
                    trigger_condition=f"低开≤{AUCTION_NUKE_DROP}%",
                    action_suggestion="核按钮出现，持仓者反抽减仓，未持仓者观望",
                    related_data={"open_high": open_high},
                    confidence=min(1.0, 0.7 + abs(open_high - AUCTION_NUKE_DROP) * 0.05),
                ))
            
            # 竞价异动: 异常幅度
            elif abs(open_high) >= AUCTION_UNUSUAL_CHANGE:
                signals.append(TradingSignal(
                    signal_type=SignalType.AUCTION_UNUSUAL,
                    priority=SignalPriority.NORMAL,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}竞价异动，幅度{open_high:.1f}%",
                    trigger_condition=f"幅度≥{AUCTION_UNUSUAL_CHANGE}%",
                    action_suggestion="关注开盘后方向选择",
                    related_data={"open_high": open_high},
                    confidence=0.5,
                ))
        
        return signals
    
    # ==================== 盘口信号检测 ====================
    
    def _detect_disk_signals(
        self,
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        real_time_data: Dict[str, Dict],
    ) -> List[TradingSignal]:
        """检测盘口信号
        
        Args:
            anchors: 锚定标的
            limit_up_stocks: 涨停股
            real_time_data: 实时数据
            
        Returns:
            List[TradingSignal]: 盘口信号列表
        """
        signals: List[TradingSignal] = []
        now = datetime.now()
        
        # 构建涨停股映射
        limit_up_map = {s.ticker: s for s in limit_up_stocks}
        
        for anchor in anchors:
            ticker = anchor.ticker
            if ticker not in real_time_data:
                continue
                
            rt = real_time_data[ticker]
            board_status = rt.get("board_status", "未涨停")
            change_pct = rt.get("change_pct", 0)
            vol_ratio = rt.get("volume_ratio", 0)
            seal_amount = rt.get("seal_amount", 0)
            
            # 大单点火: 突然放量拉升
            if change_pct >= 3 and vol_ratio >= 2.0 and board_status == "未涨停":
                signals.append(TradingSignal(
                    signal_type=SignalType.BIG_ORDER_IGNITION,
                    priority=SignalPriority.HIGH,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}大单点火，涨幅{change_pct:.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition="涨幅≥3% 且 量比≥2.0",
                    action_suggestion="资金点火，观察是否带动板块，可轻仓跟随",
                    related_data={"change_pct": change_pct, "vol_ratio": vol_ratio},
                    confidence=min(1.0, 0.5 + vol_ratio * 0.1),
                ))
            
            # 封板加速: 涨停且封单加大
            if board_status == "涨停" and seal_amount > 0:
                limit_up_info = limit_up_map.get(ticker)
                if limit_up_info and vol_ratio >= SEAL_ACCELERATE_RATIO:
                    signals.append(TradingSignal(
                        signal_type=SignalType.SEAL_ACCELERATE,
                        priority=SignalPriority.HIGH,
                        ticker=ticker,
                        name=anchor.name,
                        timestamp=now,
                        description=f"{anchor.name}封板加速，封单{seal_amount/1e6:.1f}百万，量比{vol_ratio:.1f}",
                        trigger_condition=f"涨停 且 量比≥{SEAL_ACCELERATE_RATIO}",
                        action_suggestion="封板强势，持股者可锁仓，未持仓者排队或等分歧",
                        related_data={"seal_amount": seal_amount, "vol_ratio": vol_ratio},
                        confidence=min(1.0, 0.6 + (seal_amount / 1e7) * 0.1),
                    ))
            
            # 炸板预警: 涨停后回落
            if board_status == "炸板":
                signals.append(TradingSignal(
                    signal_type=SignalType.EXPLODE_WARNING,
                    priority=SignalPriority.CRITICAL,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}炸板预警，当前涨幅{change_pct:.1f}%",
                    trigger_condition="涨停后炸板",
                    action_suggestion="炸板风险，持仓者减仓，观察回封情况",
                    related_data={"change_pct": change_pct, "board_status": board_status},
                    confidence=0.8,
                ))
            
            # 回封确认: 炸板后重新封板
            if board_status == "回封" and vol_ratio >= RESEAL_CONFIRM_VOL:
                signals.append(TradingSignal(
                    signal_type=SignalType.RESEAL_CONFIRM,
                    priority=SignalPriority.HIGH,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}回封确认，量比{vol_ratio:.1f}",
                    trigger_condition=f"回封 且 量比≥{RESEAL_CONFIRM_VOL}",
                    action_suggestion="回封强势，分歧转一致，可考虑跟随",
                    related_data={"vol_ratio": vol_ratio, "board_status": board_status},
                    confidence=min(1.0, 0.6 + vol_ratio * 0.1),
                ))
        
        return signals
    
    # ==================== 量价信号检测 ====================
    
    def _detect_volume_signals(
        self,
        anchors: List[AnchorStock],
        real_time_data: Dict[str, Dict],
    ) -> List[TradingSignal]:
        """检测量价信号
        
        Args:
            anchors: 锚定标的
            real_time_data: 实时数据
            
        Returns:
            List[TradingSignal]: 量价信号列表
        """
        signals: List[TradingSignal] = []
        now = datetime.now()
        
        for anchor in anchors:
            ticker = anchor.ticker
            if ticker not in real_time_data:
                continue
                
            rt = real_time_data[ticker]
            change_pct = rt.get("change_pct", 0)
            vol_ratio = rt.get("volume_ratio", 0)
            high_pct = rt.get("high_5min_pct", 0)
            
            # 放量突破: 量价齐升
            if vol_ratio >= VOLUME_BREAKOUT_RATIO and change_pct >= 3:
                signals.append(TradingSignal(
                    signal_type=SignalType.VOLUME_BREAKOUT,
                    priority=SignalPriority.HIGH,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}放量突破，涨幅{change_pct:.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition=f"量比≥{VOLUME_BREAKOUT_RATIO} 且 涨幅≥3%",
                    action_suggestion="量价齐升，突破有效，可跟随",
                    related_data={"change_pct": change_pct, "vol_ratio": vol_ratio},
                    confidence=min(1.0, 0.5 + (vol_ratio - VOLUME_BREAKOUT_RATIO) * 0.1),
                ))
            
            # 缩量回调: 健康调整
            elif 0 < vol_ratio <= SHRINK_PULLBACK_RATIO and -3 <= change_pct < 0:
                signals.append(TradingSignal(
                    signal_type=SignalType.SHRINK_PULLBACK,
                    priority=SignalPriority.NORMAL,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}缩量回调，跌幅{abs(change_pct):.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition=f"量比≤{SHRINK_PULLBACK_RATIO} 且 小幅下跌",
                    action_suggestion="缩量回调属健康调整，可观察支撑位低吸",
                    related_data={"change_pct": change_pct, "vol_ratio": vol_ratio},
                    confidence=0.5,
                ))
            
            # 天量天价: 警惕见顶
            elif vol_ratio >= SKY_VOLUME_RATIO and change_pct >= 5:
                signals.append(TradingSignal(
                    signal_type=SignalType.SKY_VOLUME,
                    priority=SignalPriority.HIGH,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}天量天价，涨幅{change_pct:.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition=f"量比≥{SKY_VOLUME_RATIO}",
                    action_suggestion="天量需警惕，持仓者注意止盈，未持仓者不追高",
                    related_data={"change_pct": change_pct, "vol_ratio": vol_ratio},
                    confidence=min(1.0, 0.5 + (vol_ratio - SKY_VOLUME_RATIO) * 0.05),
                ))
            
            # 地量地价: 可能见底
            elif vol_ratio <= GROUND_VOLUME_RATIO and change_pct <= -3:
                signals.append(TradingSignal(
                    signal_type=SignalType.GROUND_VOLUME,
                    priority=SignalPriority.NORMAL,
                    ticker=ticker,
                    name=anchor.name,
                    timestamp=now,
                    description=f"{anchor.name}地量地价，跌幅{abs(change_pct):.1f}%，量比{vol_ratio:.1f}",
                    trigger_condition=f"量比≤{GROUND_VOLUME_RATIO} 且 跌幅≥3%",
                    action_suggestion="地量可能见底，观察是否有资金抄底",
                    related_data={"change_pct": change_pct, "vol_ratio": vol_ratio},
                    confidence=0.4,
                ))
        
        return signals
    
    # ==================== 情绪信号检测 ====================
    
    def _detect_emotion_signals(
        self,
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        market_snapshot: Optional[Dict] = None,
    ) -> List[TradingSignal]:
        """检测情绪信号
        
        Args:
            limit_up_stocks: 涨停股
            themes: 题材
            market_snapshot: 市场快照
            
        Returns:
            List[TradingSignal]: 情绪信号列表
        """
        signals: List[TradingSignal] = []
        now = datetime.now()
        
        # 统计市场数据
        total_limit_up = len(limit_up_stocks)
        limit_down_count = 0
        if market_snapshot:
            limit_down_count = market_snapshot.get("limit_down_count", 0)
        
        # 板块共振: 某板块多股涨停
        theme_limit_counts: Dict[str, List[str]] = {}
        for stock in limit_up_stocks:
            theme = stock.theme or "未知"
            if theme not in theme_limit_counts:
                theme_limit_counts[theme] = []
            theme_limit_counts[theme].append(stock.ticker)
        
        for theme, tickers in theme_limit_counts.items():
            if len(tickers) >= SECTOR_RESONANCE_COUNT:
                signals.append(TradingSignal(
                    signal_type=SignalType.SECTOR_RESONANCE,
                    priority=SignalPriority.HIGH,
                    ticker=tickers[0],
                    name=theme,
                    timestamp=now,
                    description=f"{theme}板块共振，{len(tickers)}只涨停",
                    trigger_condition=f"板块涨停≥{SECTOR_RESONANCE_COUNT}只",
                    action_suggestion=f"板块效应强，关注{theme}前排龙头",
                    related_data={"theme": theme, "limit_up_count": len(tickers), "tickers": tickers[:5]},
                    confidence=min(1.0, 0.5 + len(tickers) * 0.05),
                ))
        
        # 情绪冰点: 跌停多、涨停少
        if limit_down_count >= EMOTION_ICE_LIMIT_DOWN and total_limit_up < 10:
            signals.append(TradingSignal(
                signal_type=SignalType.EMOTION_ICE,
                priority=SignalPriority.HIGH,
                ticker="",
                name="全市场",
                timestamp=now,
                description=f"情绪冰点，跌停{limit_down_count}只，涨停仅{total_limit_up}只",
                trigger_condition=f"跌停≥{EMOTION_ICE_LIMIT_DOWN} 且 涨停<10",
                action_suggestion="情绪冰点，管住手，等待冰点后的修复机会",
                related_data={"limit_down": limit_down_count, "limit_up": total_limit_up},
                confidence=0.7,
            ))
            self._market_mood = "冰点"
        
        # 情绪高潮: 涨停极多
        elif total_limit_up >= EMOTION_PEAK_LIMIT_UP:
            signals.append(TradingSignal(
                signal_type=SignalType.EMOTION_PEAK,
                priority=SignalPriority.HIGH,
                ticker="",
                name="全市场",
                timestamp=now,
                description=f"情绪高潮，涨停{total_limit_up}只",
                trigger_condition=f"涨停≥{EMOTION_PEAK_LIMIT_UP}",
                action_suggestion="情绪高潮，注意次日分化，持仓者可逐步止盈",
                related_data={"limit_up": total_limit_up},
                confidence=0.7,
            ))
            self._market_mood = "高潮"
        
        # 分歧转一致: 炸板股多数回封
        if market_snapshot:
            explode_count = market_snapshot.get("explode_count", 0)
            reseal_count = market_snapshot.get("reseal_count", 0)
            if explode_count > 0:
                reseal_rate = reseal_count / explode_count
                if reseal_rate >= DIVERGE_TO_CONSENSUS_RATE:
                    signals.append(TradingSignal(
                        signal_type=SignalType.DIVERGE_TO_CONSENSUS,
                        priority=SignalPriority.HIGH,
                        ticker="",
                        name="全市场",
                        timestamp=now,
                        description=f"分歧转一致，炸板{explode_count}只，回封{reseal_count}只，回封率{reseal_rate:.0%}",
                        trigger_condition=f"回封率≥{DIVERGE_TO_CONSENSUS_RATE:.0%}",
                        action_suggestion="分歧转一致，情绪修复，可积极操作",
                        related_data={"explode": explode_count, "reseal": reseal_count, "rate": reseal_rate},
                        confidence=min(1.0, reseal_rate),
                    ))
        
        # 更新市场情绪
        if not any(s.signal_type in (SignalType.EMOTION_ICE, SignalType.EMOTION_PEAK) for s in signals):
            if total_limit_up >= 30:
                self._market_mood = "活跃"
            elif total_limit_up >= 15:
                self._market_mood = "正常"
            elif total_limit_up >= 5:
                self._market_mood = "低迷"
            else:
                self._market_mood = "冰点"
        
        return signals
    
    # ==================== 信号处理 ====================
    
    def _apply_cooldown(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """应用信号冷却，过滤重复信号
        
        Args:
            signals: 原始信号列表
            
        Returns:
            List[TradingSignal]: 过滤后的信号列表
        """
        now = datetime.now()
        filtered: List[TradingSignal] = []
        
        for signal in signals:
            key = f"{signal.signal_type.value}_{signal.ticker}"
            last_time = self._last_signal_time.get(key)
            
            if last_time is None or (now - last_time).total_seconds() >= SIGNAL_COOLDOWN:
                filtered.append(signal)
                self._last_signal_time[key] = now
        
        return filtered
    
    def _compile_summary(
        self,
        signals: List[TradingSignal],
        market_snapshot: Optional[Dict] = None,
    ) -> SignalSummary:
        """编译信号汇总
        
        Args:
            signals: 信号列表
            market_snapshot: 市场快照
            
        Returns:
            SignalSummary: 信号汇总
        """
        now = datetime.now()
        
        # 按优先级分类
        critical = [s for s in signals if s.priority == SignalPriority.CRITICAL]
        high = [s for s in signals if s.priority == SignalPriority.HIGH]
        normal = [s for s in signals if s.priority == SignalPriority.NORMAL]
        
        # 机会和风险
        opportunities: List[str] = []
        risks: List[str] = []
        
        for signal in signals:
            if signal.signal_type in (
                SignalType.AUCTION_SNATCH,
                SignalType.BIG_ORDER_IGNITION,
                SignalType.RESEAL_CONFIRM,
                SignalType.VOLUME_BREAKOUT,
                SignalType.SECTOR_RESONANCE,
                SignalType.DIVERGE_TO_CONSENSUS,
            ):
                opportunities.append(signal.description)
            elif signal.signal_type in (
                SignalType.AUCTION_NUKE,
                SignalType.EXPLODE_WARNING,
                SignalType.SKY_VOLUME,
                SignalType.EMOTION_ICE,
                SignalType.EMOTION_PEAK,
            ):
                risks.append(signal.description)
        
        # 生成摘要文本
        parts: List[str] = []
        parts.append(f"=== 信号汇总 [{now.strftime('%H:%M')}] ===")
        parts.append(f"市场情绪: {self._market_mood}")
        
        if critical:
            parts.append(f"⚠️ 紧急信号({len(critical)}条):")
            for s in critical[:3]:
                parts.append(f"  - {s.description}")
        
        if high:
            parts.append(f"🔥 重点信号({len(high)}条):")
            for s in high[:5]:
                parts.append(f"  - {s.description}")
        
        if opportunities:
            parts.append(f"机会: {len(opportunities)}个")
        if risks:
            parts.append(f"风险: {len(risks)}个")
        
        return SignalSummary(
            timestamp=now,
            critical_signals=critical,
            high_signals=high,
            normal_signals=normal,
            market_mood=self._market_mood,
            key_opportunities=opportunities[:5],
            key_risks=risks[:5],
            summary_text="\n".join(parts),
        )
    
    def clear_history(self):
        """清空信号历史"""
        self._signal_history.clear()
        self._last_signal_time.clear()
        logger.info("信号历史已清空")