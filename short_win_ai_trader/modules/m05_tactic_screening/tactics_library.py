"""战法量化规则库 — 短线致胜AI交易智能体核心战法引擎

包含15套经典超短线战法的完整量化规则定义，每套战法包含:
- 核心逻辑描述
- 5项硬性条件（入场门槛）
- 3项加分形态条件
- 最佳适用环境
- 风险边界
- 适用情绪周期

战法列表:
  1.  筹码峰战法      — 基于筹码分布的形态战法
  2.  三倍量突破战法   — 量能驱动的突破战法
  3.  缩量突破战法     — 缩量控盘突破战法
  4.  过左峰战法       — 历史前高突破战法
  5.  首阴战法         — 龙头首阴低吸战法
  6.  N字形战法        — 洗盘后二波战法
  7.  喜鹊闹梅战法     — 底部反转战法
  8.  平台突破战法     — 横盘突破战法
  9.  一进二战法       — 连板接力战法
  10. 龙头情绪战法     — 情绪周期龙头战法
  11. 布林带战法       — 布林带技术战法
  12. 分时承接战法     — 盘中承接力战法
  13. 三星探底战法     — 三次探底不创新低
  14. 反核战法         — 反包涨停战法
  15. 缩量尾盘先手战法 — 尾盘缩量企稳

Author: SWAT Engine
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────
# 数据模型
# ──────────────────────────────────────────────────────────

@dataclass
class TacticRuleSet:
    """单套战法的完整规则集"""
    # 基础信息
    name: str                          # 战法名称
    code: str                          # 战法编码
    core_logic: str                    # 核心逻辑一句话
    description: str                   # 详细描述
    risk_level: str                    # 风险等级: low/medium/high/extreme
    hold_period: str                   # 预期持有周期

    # 5项硬性条件（必须全部满足才能入选）
    hard_conditions: List[Dict[str, Any]] = field(default_factory=list)

    # 3项形态加分条件（满足越多得分越高）
    shape_conditions: List[Dict[str, Any]] = field(default_factory=list)

    # 最佳适用环境
    best_env: Dict[str, Any] = field(default_factory=dict)

    # 风险边界
    risk_boundary: Dict[str, Any] = field(default_factory=dict)

    # 适用情绪周期
    applicable_cycles: List[str] = field(default_factory=list)

    # 不适用的情绪周期
    forbidden_cycles: List[str] = field(default_factory=list)

    # 战法分类体系（大类 + 小类）
    category: str = ""                 # 大类: 资金流/筹码峰/技术分析/情绪周期/量价关系/跟庄
    subcategory: str = ""              # 小类: 根据大类细分


# ──────────────────────────────────────────────────────────
# 辅助函数：条件构造器
# ──────────────────────────────────────────────────────────

def _cond(name: str, indicator: str, operator: str, threshold: Any,
          weight: float = 1.0, description: str = "") -> Dict:
    """构造单项条件字典"""
    return {
        "name": name,
        "indicator": indicator,
        "operator": operator,       # gt/ge/lt/le/eq/between
        "threshold": threshold,
        "weight": weight,
        "description": description or name,
    }


def _env(min_limit_up: int = 0, max_limit_up: int = 999,
         min_up_down_ratio: float = 0.0, max_up_down_ratio: float = 999.0,
         volume_trend: str = "any", theme_requirement: str = "any",
         description: str = "") -> Dict:
    """构造环境要求字典"""
    return {
        "min_limit_up": min_limit_up,
        "max_limit_up": max_limit_up,
        "min_up_down_ratio": min_up_down_ratio,
        "max_up_down_ratio": max_up_down_ratio,
        "volume_trend": volume_trend,           # any/increase/decrease/stable
        "theme_requirement": theme_requirement, # any/strong/moderate/weak
        "description": description,
    }


def _risk(max_position_pct: float = 100.0, stop_loss_pct: float = 5.0,
          max_hold_days: int = 3, avoid_conditions: List[str] = None,
          description: str = "") -> Dict:
    """构造风险边界字典"""
    return {
        "max_position_pct": max_position_pct,
        "stop_loss_pct": stop_loss_pct,
        "max_hold_days": max_hold_days,
        "avoid_conditions": avoid_conditions or [],
        "description": description,
    }


# ──────────────────────────────────────────────────────────
# 15套战法完整规则定义
# ──────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════
# 1. 筹码峰战法
# ═══════════════════════════════════════════════════════
CHIP_PEAK_TACTIC = TacticRuleSet(
    name="筹码峰战法",
    code="CHIP_PEAK",
    core_logic="基于筹码分布形态识别主力建仓/洗盘/出货阶段，捕捉低位单峰密集后的启动信号",
    description=(
        "筹码峰战法通过分析股票的筹码分布形态，识别主力资金的建仓、洗盘和拉升行为。 "
        "核心关注低位单峰密集（主力建仓完毕）、上涨多峰（接力拉升）、双峰填谷（洗盘整理） "
        "和高位密集（出货信号）四种形态。买入信号主要出现在低位单峰密集后的放量突破时刻。"
    ),
    risk_level="medium",
    hold_period="2-5天",

    hard_conditions=[
        _cond("低位筹码集中度", "chip_concentration_low", "ge", 60,
              description="低位（当前价下方±10%）筹码占比>=60%，表明主力已高度控盘"),
        _cond("筹码峰形态", "chip_peak_shape", "eq", "single_peak",
              description="呈现单峰密集形态，筹码集中而非分散"),
        _cond("获利盘比例", "profit_ratio", "ge", 70,
              description="获利盘比例>=70%，表明大部分持仓者已盈利，抛压可控"),
        _cond("突破信号", "breakout_today", "eq", True,
              description="当日出现放量突破近期整理平台或均线压制"),
        _cond("涨幅控制", "change_pct_today", "ge", 3.0,
              description="当日涨幅>=3%，显示资金主动进攻意愿"),
    ],

    shape_conditions=[
        _cond("上方套牢盘少", "trapped_chip_above", "le", 15, weight=0.3,
              description="上方套牢筹码<=15%，拉升阻力小"),
        _cond("筹码峰上移", "chip_peak_shift", "eq", "up", weight=0.4,
              description="筹码主峰正在上移，主力拉升意图明显"),
        _cond("换手率适中", "turnover_rate", "between", (3.0, 15.0), weight=0.3,
              description="换手率3%-15%，活跃但不异常"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪回暖，量能温和放大，题材有一定持续性"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=5,
        avoid_conditions=["高位筹码密集", "换手率>25%", "跌停板附近"],
        description="若高位筹码开始密集或换手率异常放大，立即止盈离场"
    ),

    applicable_cycles=["启动期", "发酵期"],
    forbidden_cycles=["退潮期", "高潮期"],
    category="筹码峰",
    subcategory="筹码分布",
)


# ═══════════════════════════════════════════════════════
# 2. 三倍量突破战法
# ═══════════════════════════════════════════════════════
TRIPLE_VOLUME_BREAKOUT_TACTIC = TacticRuleSet(
    name="三倍量突破战法",
    code="TRIPLE_VOL_BREAK",
    core_logic="当日成交量达到5日或20日均量的3倍以上，伴随价格突破关键压力位",
    description=(
        "三倍量突破是最经典的强势启动信号之一。当个股成交量突然放大到近期均量的3倍以上， "
        "同时价格突破前期高点、均线压制或整理平台上沿，表明有大资金主动进攻。 "
        "此战法追求的是强势启动初期的惯性上涨。"
    ),
    risk_level="medium",
    hold_period="1-3天",

    hard_conditions=[
        _cond("成交量5倍比", "volume_ma5_ratio", "ge", 3.0,
              description="当日成交量 / 5日均量 >= 3倍"),
        _cond("成交量20倍比", "volume_ma20_ratio", "ge", 2.5,
              description="当日成交量 / 20日均量 >= 2.5倍，确认不是短期脉冲"),
        _cond("价格突破", "price_breakout", "eq", True,
              description="价格突破前高、平台整理上沿或重要均线压制"),
        _cond("涨幅要求", "change_pct_today", "ge", 5.0,
              description="当日涨幅>=5%，强势实体阳线"),
        _cond("封板质量", "seal_quality", "ge", 50.0,
              description="涨停封单金额/流通市值 >= 50个基点，封板质量好"),
    ],

    shape_conditions=[
        _cond("早盘放量", "morning_volume_ratio", "ge", 0.6, weight=0.3,
              description="早盘成交量占全天60%以上，表明资金抢筹积极"),
        _cond("均线多头排列", "ma_alignment", "eq", "bullish", weight=0.4,
              description="5/10/20日均线呈多头排列，趋势向好"),
        _cond("无长上影线", "upper_shadow_ratio", "le", 0.3, weight=0.3,
              description="上影线长度/实体长度 <= 0.3，抛压有限"),
    ],

    best_env=_env(
        min_limit_up=40, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪发酵或高潮期，主线题材强势，量能充沛"
    ),

    risk_boundary=_risk(
        max_position_pct=25.0, stop_loss_pct=-4.0, max_hold_days=3,
        avoid_conditions=["尾盘炸板", "次日低开>3%", "量能骤缩50%以上"],
        description="次日若低开超3%或量能大幅萎缩，果断止损"
    ),

    applicable_cycles=["发酵期", "高潮期", "启动期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="量价关系",
    subcategory="放量突破",
)


# ═══════════════════════════════════════════════════════
# 3. 缩量突破战法
# ═══════════════════════════════════════════════════════
SHRINK_VOLUME_BREAKOUT_TACTIC = TacticRuleSet(
    name="缩量突破战法",
    code="SHRINK_VOL_BREAK",
    core_logic="缩量突破前期高点，表明筹码锁定良好，主力控盘度高",
    description=(
        "缩量突破是判断主力控盘度的重要信号。当股价以较小成交量突破前期高点时， "
        "说明大部分筹码被主力锁定，浮筹极少，拉升阻力很小。这种突破往往持续性更好， "
        "后续涨幅空间更大。关键是确认突破的有效性和主力的真实意图。"
    ),
    risk_level="low",
    hold_period="3-7天",

    hard_conditions=[
        _cond("缩量程度", "volume_shrink_ratio", "le", 0.7,
              description="当日成交量 / 5日均量 <= 0.7，明显缩量"),
        _cond("突破确认", "price_breakout_high", "eq", True,
              description="收盘价突破近期（20日内）最高点"),
        _cond("控盘度指标", "chip_lock_ratio", "ge", 65,
              description="筹码锁定率>=65%，浮筹少"),
        _cond("换手率限制", "turnover_rate", "le", 8.0,
              description="换手率<=8%，筹码稳定不松动"),
        _cond("涨幅适中", "change_pct_today", "ge", 2.0,
              description="当日涨幅>=2%，有实质性上涨"),
    ],

    shape_conditions=[
        _cond("前期横盘整理", "consolidation_days", "ge", 10, weight=0.4,
              description="突破前有至少10天横盘整理，筹码充分换手"),
        _cond("均线粘合后发散", "ma_spread_after_pinch", "eq", True, weight=0.3,
              description="均线粘合后向上发散，整理充分"),
        _cond("筹码上移但不散", "chip_shift_quality", "eq", "compact", weight=0.3,
              description="筹码随价格上移但保持集中，未出现大面积分散"),
    ],

    best_env=_env(
        min_limit_up=25, min_up_down_ratio=1.0,
        volume_trend="stable", theme_requirement="moderate",
        description="市场情绪稳定，题材有持续性，不需要极端放量也能突破"
    ),

    risk_boundary=_risk(
        max_position_pct=35.0, stop_loss_pct=-5.0, max_hold_days=7,
        avoid_conditions=["突破后次日放量长阴", "换手率突增至15%以上"],
        description="若突破后快速放量下跌，视为假突破，立即止损"
    ),

    applicable_cycles=["启动期", "发酵期"],
    forbidden_cycles=["退潮期"],
    category="量价关系",
    subcategory="缩量控盘",
)


# ═══════════════════════════════════════════════════════
# 4. 过左峰战法
# ═══════════════════════════════════════════════════════
LEFT_PEAK_BREAK_TACTIC = TacticRuleSet(
    name="过左峰战法",
    code="LEFT_PEAK_BREAK",
    core_logic="有效突破前期历史高点或阶段性高点，解放所有套牢盘",
    description=(
        "过左峰（越过左侧山峰）是指股价突破前期明显的高点平台，将所有套牢筹码解放。 "
        "这种走势表明主力资金实力雄厚、志在高远。过左峰的有效性需要结合成交量、 "
        "突破幅度和后续回踩确认来判断。真正的过左峰后往往开启一波主升行情。"
    ),
    risk_level="medium",
    hold_period="3-5天",

    hard_conditions=[
        _cond("突破左峰", "break_left_peak", "eq", True,
              description="收盘价突破前期（40-120日内）最高价"),
        _cond("突破幅度", "breakout_margin_pct", "ge", 2.0,
              description="收盘价高于左峰至少2%，确保有效突破而非假突破"),
        _cond("量能配合", "volume_vs_left_peak", "ge", 0.8,
              description="当日成交量 >= 左峰当天成交量的80%"),
        _cond("涨幅要求", "change_pct_today", "ge", 4.0,
              description="当日涨幅>=4%，强势突破"),
        _cond("无巨量长上影", "upper_shadow_volume_ok", "eq", True,
              description="不能出现巨量长上影线，否则视为假突破"),
    ],

    shape_conditions=[
        _cond("左峰前整理充分", "days_since_left_peak", "ge", 20, weight=0.3,
              description="距左峰至少20个交易日，整理时间充足"),
        _cond("突破前缩量洗盘", "pre_breakout_shrink", "eq", True, weight=0.4,
              description="突破前有缩量洗盘行为，清洗浮筹"),
        _cond("均线系统支撑", "ma_support_below", "eq", True, weight=0.3,
              description="10日/20日均线在下方形成支撑带"),
    ],

    best_env=_env(
        min_limit_up=35, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪向好，主线题材强势，有利于突破后延续"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=5,
        avoid_conditions=["突破次日低开低走", "3日内跌回左峰下方"],
        description="若3日内收盘跌回左峰下方，视为假突破，止损离场"
    ),

    applicable_cycles=["发酵期", "启动期"],
    forbidden_cycles=["退潮期", "高潮期"],
    category="筹码峰",
    subcategory="压力突破",
)


# ═══════════════════════════════════════════════════════
# 5. 首阴战法
# ═══════════════════════════════════════════════════════
FIRST_YIN_TACTIC = TacticRuleSet(
    name="首阴战法",
    code="FIRST_YIN",
    core_logic="人气龙头首次出现阴线回调，缩量调整，关键均线不破",
    description=(
        "首阴战法针对市场人气龙头股的首次阴线调整。龙头股在连续上涨后首次出现阴线， "
        "如果伴随缩量、关键支撑位（如5日线）未有效跌破，往往是极佳的低吸机会。 "
        "核心逻辑是：龙头首阴不是顶，资金接力意愿仍在，次日反包概率大。"
    ),
    risk_level="high",
    hold_period="1-2天",

    hard_conditions=[
        _cond("龙头地位确认", "is_leader_stock", "eq", True,
              description="必须是当前市场或题材内公认的人气龙头"),
        _cond("连板高度", "consecutive_boards_before", "ge", 3,
              description="首阴前至少有3连板，确认龙头地位"),
        _cond("首次阴线", "is_first_yin_after_rally", "eq", True,
              description="上涨以来首次收阴线，非连续阴线"),
        _cond("缩量调整", "volume_shrink_ratio", "le", 0.7,
              description="首阴当天成交量 <= 前日成交量的70%，缩量回调"),
        _cond("均线支撑", "price_vs_ma5", "ge", 0.98,
              description="收盘价不低于5日均线的98%，即未有效跌破5日线"),
    ],

    shape_conditions=[
        _cond("尾盘有承接", "intraday_support", "eq", True, weight=0.3,
              description="分时图尾盘有明显承接，非单边下跌"),
        _cond("跌停未封死", "not_seal_limit_down", "eq", True, weight=0.4,
              description="若触及跌停，未能封死跌停板，有资金翘板"),
        _cond("龙虎榜游资未大卖", "yingyou_not_selling", "eq", True, weight=0.3,
              description="龙虎榜显示游资未大规模出货"),
    ],

    best_env=_env(
        min_limit_up=40, min_up_down_ratio=1.0,
        volume_trend="stable", theme_requirement="strong",
        description="市场情绪发酵或分歧期，龙头战法有效"
    ),

    risk_boundary=_risk(
        max_position_pct=20.0, stop_loss_pct=-4.0, max_hold_days=2,
        avoid_conditions=["次日低开>5%", "5日线有效跌破", "龙头地位被抢"],
        description="超短操作，次日不反包即离场，严格止损"
    ),

    applicable_cycles=["发酵期", "分歧期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="情绪周期",
    subcategory="龙头低吸",
)


# ═══════════════════════════════════════════════════════
# 6. N字形战法
# ═══════════════════════════════════════════════════════
N_SHAPE_TACTIC = TacticRuleSet(
    name="N字形战法",
    code="N_SHAPE",
    core_logic="第一波拉升->缩量洗盘->二次放量启动，形成N字形态",
    description=(
        "N字形战法捕捉股票在主升浪中的洗盘后再度启动机会。第一阶段是放量拉升， "
        "第二阶段是缩量回调洗盘（不跌破关键支撑），第三阶段是再度放量启动。 "
        "第三阶段的买入点是整个战法的核心，要求二次启动的量能不低于第一波。"
    ),
    risk_level="medium",
    hold_period="3-5天",

    hard_conditions=[
        _cond("第一波涨幅", "first_wave_gain_pct", "ge", 20,
              description="第一波拉升涨幅>=20%，确认有主力资金介入"),
        _cond("洗盘缩量", "washout_volume_ratio", "le", 0.6,
              description="洗盘阶段成交量 <= 第一波最大量的60%，充分缩量"),
        _cond("洗盘不破位", "washout_support_hold", "eq", True,
              description="洗盘未跌破第一波起涨点或20日均线支撑"),
        _cond("二次放量", "second_wave_volume_ratio", "ge", 0.8,
              description="二次启动量能 >= 第一波平均量能的80%"),
        _cond("二次启动涨幅", "second_wave_change_pct", "ge", 3.0,
              description="二次启动当日涨幅>=3%，确认启动有效"),
    ],

    shape_conditions=[
        _cond("洗盘时间适中", "washout_days", "between", (3, 10), weight=0.3,
              description="洗盘3-10个交易日，时间太短洗不干净，太长则人气消散"),
        _cond("N字右侧角度更大", "second_wave_slope", "ge", 1.0, weight=0.4,
              description="第二波启动斜率>=第一波，表明资金更急迫"),
        _cond("题材仍在发酵", "theme_still_active", "eq", True, weight=0.3,
              description="所属题材仍在发酵期，有持续催化"),
    ],

    best_env=_env(
        min_limit_up=35, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪发酵期，题材轮动活跃，N字二波容易成功"
    ),

    risk_boundary=_risk(
        max_position_pct=25.0, stop_loss_pct=-5.0, max_hold_days=5,
        avoid_conditions=["洗盘跌破起涨点", "二波量能不足第一波50%"],
        description="若洗盘破位或二波量能严重不足，放弃操作"
    ),

    applicable_cycles=["发酵期", "启动期"],
    forbidden_cycles=["退潮期"],
    category="技术分析",
    subcategory="K线形态",
)


# ═══════════════════════════════════════════════════════
# 7. 喜鹊闹梅战法
# ═══════════════════════════════════════════════════════
MAGPIE_PLUM_TACTIC = TacticRuleSet(
    name="喜鹊闹梅战法",
    code="MAGPIE_PLUM",
    core_logic="底部区域出现连续缩量十字星群，随后放量阳线确认反转",
    description=(
        "喜鹊闹梅是一种经典的底部反转战法。股价在长期下跌或横盘后，在底部区域 "
        "连续出现多根缩量十字星/小阴小阳线（如喜鹊在梅枝上跳跃），表明抛压穷尽、 "
        "多空趋于平衡。随后一根放量中阳线（如梅花绽放）确认反转信号。"
    ),
    risk_level="low",
    hold_period="5-10天",

    hard_conditions=[
        _cond("底部缩量十字星群", "consecutive_doji_count", "ge", 3,
              description="连续>=3个交易日出现十字星或小阴小阳（涨跌幅<2%）"),
        _cond("缩量程度", "doji_volume_vs_ma20", "le", 0.6,
              description="十字星期间成交量 <= 20日均量的60%"),
        _cond("反转阳线", "reversal_candle", "eq", True,
              description="随后出现一根涨幅>=3%的阳线，确认反转"),
        _cond("反转放量", "reversal_volume_ratio", "ge", 1.5,
              description="反转阳线成交量 >= 十字星期间均量的1.5倍"),
        _cond("底部区域确认", "is_in_bottom_area", "eq", True,
              description="处于下跌末期或底部横盘区域，非高位"),
    ],

    shape_conditions=[
        _cond("前期跌幅充分", "decline_from_high_pct", "ge", 30, weight=0.3,
              description="从高点的跌幅>=30%，调整充分"),
        _cond("RSI底背离", "rsi_bullish_divergence", "eq", True, weight=0.4,
              description="RSI指标出现底背离，价格新低但指标不新低"),
        _cond("MACD金叉或即将金叉", "macd_golden_cross", "eq", True, weight=0.3,
              description="MACD金叉或即将金叉，动量转多"),
    ],

    best_env=_env(
        min_limit_up=20, min_up_down_ratio=0.8,
        volume_trend="stable", theme_requirement="any",
        description="市场混沌期或启动初期，低位股容易受到资金关注"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-6.0, max_hold_days=10,
        avoid_conditions=["反转阳线次日低开低走", "跌回十字星区间"],
        description="若反转信号被否定，跌回整理区间，止损离场"
    ),

    applicable_cycles=["混沌期", "启动期"],
    forbidden_cycles=["高潮期", "退潮期"],
    category="技术分析",
    subcategory="底部反转",
)


# ═══════════════════════════════════════════════════════
# 8. 平台突破战法
# ═══════════════════════════════════════════════════════
PLATFORM_BREAKOUT_TACTIC = TacticRuleSet(
    name="平台突破战法",
    code="PLATFORM_BREAK",
    core_logic="经过横盘整理后，放量突破整理平台上沿，开启新一轮上涨",
    description=(
        "平台突破战法是最经典的技术形态战法之一。股价在一段上涨后进入横盘整理阶段， "
        "形成一个明显的整理平台。当股价以放量阳线突破平台上沿时，表明整理结束、 "
        "主力准备开启新一轮拉升。平台的整理时间越长、振幅越窄，突破后的爆发力越强。"
    ),
    risk_level="medium",
    hold_period="3-7天",

    hard_conditions=[
        _cond("平台整理时间", "platform_days", "ge", 10,
              description="平台整理时间>=10个交易日"),
        _cond("平台振幅", "platform_amplitude_pct", "le", 12,
              description="平台期间最大振幅<=12%，筹码充分换手"),
        _cond("放量突破", "breakout_volume_ratio", "ge", 2.0,
              description="突破日成交量 >= 平台期间均量的2倍"),
        _cond("突破幅度", "breakout_margin_pct", "ge", 2.0,
              description="收盘价突破平台上沿至少2%"),
        _cond("突破阳线实体", "breakout_body_pct", "ge", 2.5,
              description="突破日阳线实体>=2.5%，非十字星突破"),
    ],

    shape_conditions=[
        _cond("平台期间缩量", "platform_volume_vs_before", "le", 0.7, weight=0.3,
              description="平台期间成交量 <= 上涨阶段均量的70%"),
        _cond("均线系统粘合", "ma_convergence_in_platform", "eq", True, weight=0.4,
              description="平台期间5/10/20日均线粘合，整理充分"),
        _cond("筹码在平台内集中", "chip_concentrated_in_platform", "eq", True, weight=0.3,
              description="平台期间筹码在窄幅区间内集中"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪稳定向好，有利于突破后的持续"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=7,
        avoid_conditions=["突破后3日内跌回平台", "突破后巨量长阴线"],
        description="若3日内跌回平台内，视为假突破，止损离场"
    ),

    applicable_cycles=["启动期", "发酵期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="技术分析",
    subcategory="平台突破",
)


# ═══════════════════════════════════════════════════════
# 9. 一进二战法
# ═══════════════════════════════════════════════════════
BOARD_1TO2_TACTIC = TacticRuleSet(
    name="一进二战法",
    code="BOARD_1TO2",
    core_logic="首板涨停股次日继续涨停，捕捉连板接力机会",
    description=(
        "一进二是超短线中最经典的接力战法。首板股次日若能成功晋级二板， "
        "说明市场认可度高、接力资金充足。一进二战法要求首板质量好（早盘封板、封单足）、 "
        "次日竞价高开有度、题材处于发酵期。此战法追求隔日超短收益。"
    ),
    risk_level="high",
    hold_period="1天",

    hard_conditions=[
        _cond("首板确认", "is_first_board_yesterday", "eq", True,
              description="昨日为首板涨停（非连板）"),
        _cond("首板封板时间", "first_board_seal_time", "le", 45,
              description="首板在开盘后45分钟内封板，封板时间早说明强势"),
        _cond("次日高开幅度", "next_day_open_high_pct", "between", (2.0, 7.0),
              description="次日高开2%-7%，太高容易被砸，太低说明弱势"),
        _cond("次日竞价量", "auction_volume_ratio", "ge", 0.03,
              description="集合竞价成交量 >= 昨日总成交量的3%"),
        _cond("题材发酵中", "theme_in_ferment", "eq", True,
              description="所属题材处于发酵期，有涨停梯队"),
    ],

    shape_conditions=[
        _cond("首板封单充足", "first_board_seal_amount", "ge", 5e7, weight=0.3,
              description="首板封单金额>=5000万，封板质量好"),
        _cond("无减持/利空", "no_bad_news", "eq", True, weight=0.4,
              description="首板后无减持公告、利空消息"),
        _cond("流通市值适中", "float_market_cap", "between", (20e8, 200e8), weight=0.3,
              description="流通市值20-200亿，太小流动性差，太大拉不动"),
    ],

    best_env=_env(
        min_limit_up=40, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪发酵期，连板接力氛围好"
    ),

    risk_boundary=_risk(
        max_position_pct=20.0, stop_loss_pct=-3.0, max_hold_days=1,
        avoid_conditions=["开盘后快速下杀", "炸板后15分钟内未回封"],
        description="纯隔日超短，不板即走，炸板无法回封立即止损"
    ),

    applicable_cycles=["发酵期"],
    forbidden_cycles=["退潮期", "分歧期", "混沌期"],
    category="情绪周期",
    subcategory="连板接力",
)


# ═══════════════════════════════════════════════════════
# 10. 龙头情绪战法
# ═══════════════════════════════════════════════════════
DRAGON_EMOTION_TACTIC = TacticRuleSet(
    name="龙头情绪战法",
    code="DRAGON_EMOTION",
    core_logic="结合情绪周期、龙头身位和板块强度，在市场情绪最佳时点捕捉龙头",
    description=(
        "龙头情绪战法是将情绪周期理论应用于龙头股操作的综合性战法。通过判断当前 "
        "市场情绪所处周期（混沌/启动/发酵/高潮/分歧/退潮），选择对应的龙头操作策略。 "
        "核心是：在启动期识别龙头，在发酵期加仓龙头，在分歧期低吸龙头，在高潮期兑现龙头。"
    ),
    risk_level="high",
    hold_period="1-5天",

    hard_conditions=[
        _cond("龙头身位", "dragon_rank", "le", 3,
              description="当前为题材内前3身位的龙头，非跟风杂毛"),
        _cond("板块强度", "sector_limit_up_count", "ge", 5,
              description="所属板块当日涨停数>=5，板块效应强"),
        _cond("情绪周期匹配", "emotion_cycle_match", "eq", True,
              description="当前情绪周期在本战法适用范围内"),
        _cond("连板高度", "consecutive_boards", "ge", 2,
              description="当前至少有2连板，确认龙头气质"),
        _cond("板块梯队完整", "sector_ladder_complete", "eq", True,
              description="板块内有完整的连板梯队（2板/3板/首板均有）"),
    ],

    shape_conditions=[
        _cond("龙头封单领先", "dragon_seal_vs_followers", "ge", 2.0, weight=0.3,
              description="龙头封单金额是跟风股的2倍以上，辨识度最高"),
        _cond("龙虎榜游资介入", "yingyou_on_dragon", "eq", True, weight=0.4,
              description="龙虎榜显示知名游资席位介入"),
        _cond("题材催化未结束", "theme_catalyst_remaining", "eq", True, weight=0.3,
              description="题材催化事件尚未完全兑现，仍有预期差"),
    ],

    best_env=_env(
        min_limit_up=40, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪启动期或发酵期，题材明确，龙头清晰"
    ),

    risk_boundary=_risk(
        max_position_pct=25.0, stop_loss_pct=-4.0, max_hold_days=5,
        avoid_conditions=["龙头地位被卡位", "板块批量跌停", "情绪转入退潮"],
        description="一旦龙头地位被取代或情绪退潮，立即离场"
    ),

    applicable_cycles=["启动期", "发酵期", "分歧期"],
    forbidden_cycles=["退潮期"],
    category="情绪周期",
    subcategory="龙头博弈",
)


# ═══════════════════════════════════════════════════════
# 11. 布林带战法
# ═══════════════════════════════════════════════════════
BOLLINGER_TACTIC = TacticRuleSet(
    name="布林带战法",
    code="BOLLINGER",
    core_logic="布林带收口后突破上轨或中轨，捕捉趋势启动点",
    description=(
        "布林带（BOLL）战法利用布林带收口（squeeze）后的突破信号进行操作。 "
        "布林带收口表明波动率降至低位，即将选择方向。当价格放量突破中轨或上轨时， "
        "表明方向选择向上，此时是极佳的买入时机。布林带开口后的持续沿上轨运行 "
        "表明趋势强劲。"
    ),
    risk_level="medium",
    hold_period="3-7天",

    hard_conditions=[
        _cond("布林带收口", "boll_band_width_pct", "le", 5.0,
              description="布林带宽度（上下轨差/中轨）<=5%，收口状态"),
        _cond("突破中轨/上轨", "price_vs_boll_upper", "ge", 0.99,
              description="收盘价>=布林带上轨的99%，有效突破"),
        _cond("收口天数", "boll_squeeze_days", "ge", 5,
              description="布林带收口状态至少维持5个交易日"),
        _cond("突破放量", "breakout_volume_ratio", "ge", 1.5,
              description="突破日成交量 >= 5日均量的1.5倍"),
        _cond("中轨方向", "boll_mid_direction", "eq", "up",
              description="布林带中轨方向向上或走平转升"),
    ],

    shape_conditions=[
        _cond("下轨获得支撑", "price_bounce_off_lower", "eq", True, weight=0.3,
              description="突破前价格在下轨附近获得支撑反弹"),
        _cond("MACD配合金叉", "macd_aligned", "eq", True, weight=0.4,
              description="MACD金叉或红柱扩大，动量配合"),
        _cond("开口后沿上轨运行", "price_rides_upper_band", "eq", True, weight=0.3,
              description="突破后价格沿上轨运行，趋势强劲"),
    ],

    best_env=_env(
        min_limit_up=25, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="any",
        description="市场情绪稳定，技术走势有效性强"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=7,
        avoid_conditions=["突破后跌回中轨下方", "布林带开口向下"],
        description="若价格跌回中轨下方，视为假突破，止损离场"
    ),

    applicable_cycles=["启动期", "发酵期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="技术分析",
    subcategory="技术指标",
)


# ═══════════════════════════════════════════════════════
# 12. 分时承接战法
# ═══════════════════════════════════════════════════════
INTRADAY_SUPPORT_TACTIC = TacticRuleSet(
    name="分时承接战法",
    code="INTRADAY_SUPPORT",
    core_logic="分时图上股价回踩均价线获得支撑，显示买盘承接力强劲",
    description=(
        "分时承接战法专注于盘中分时走势的微观分析。当股价在盘中回调至均价线附近时， "
        "如果多次回踩不跌破均价线，且每次回踩后迅速拉起，表明下方买盘承接力极强。 "
        "这种形态常出现在强势股的洗盘过程中，是盘中低吸的绝佳时机。"
    ),
    risk_level="medium",
    hold_period="1-2天",

    hard_conditions=[
        _cond("均价线支撑", "price_vs_vwap_ratio", "ge", 0.995,
              description="股价始终维持在均价线附近或以上，未有效跌破"),
        _cond("回踩次数", "vwap_touch_count", "ge", 2,
              description="盘中至少2次回踩均价线均获得支撑"),
        _cond("日内趋势", "intraday_trend", "eq", "up",
              description="分时整体呈上升趋势，低点不断抬高"),
        _cond("涨幅基础", "change_pct_today", "ge", 2.0,
              description="当日已有一定涨幅基础（>=2%），确认强势"),
        _cond("量比配合", "volume_ratio_intraday", "ge", 1.5,
              description="量比>=1.5，成交活跃"),
    ],

    shape_conditions=[
        _cond("每次回踩后拉起", "bounce_strength_after_touch", "ge", 1.0, weight=0.4,
              description="每次回踩均价线后拉起幅度>=1%，承接有力"),
        _cond("大单净流入", "big_order_net_inflow", "ge", 0, weight=0.3,
              description="大单资金净流入，非散户行为"),
        _cond("买盘挂单厚度", "bid_depth_strength", "ge", 1.5, weight=0.3,
              description="买盘挂单厚度 >= 卖盘的1.5倍"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪稳定，个股有独立走势"
    ),

    risk_boundary=_risk(
        max_position_pct=25.0, stop_loss_pct=-3.0, max_hold_days=2,
        avoid_conditions=["尾盘放量跌破均价线", "次日低开>3%"],
        description="若尾盘放量跌破均价线，次日低开超3%，果断止损"
    ),

    applicable_cycles=["发酵期", "高潮期", "启动期"],
    forbidden_cycles=["退潮期"],
    category="技术分析",
    subcategory="分时盘口",
)


# ═══════════════════════════════════════════════════════
# 13. 三星探底战法
# ═══════════════════════════════════════════════════════
TRIPLE_BOTTOM_TACTIC = TacticRuleSet(
    name="三星探底战法",
    code="TRIPLE_BOTTOM",
    core_logic="三次测试同一支撑位不创新低，形成三重底形态后反弹",
    description=(
        "三星探底（三重底）是经典底部反转形态。股价在下跌过程中三次测试同一支撑位， "
        "每次都能守住不创新低，表明该支撑位有强大的买盘力量。当第三次探底后 "
        "出现放量阳线突破颈线位时，三重底形态完成，是中线建仓的良机。"
    ),
    risk_level="low",
    hold_period="7-15天",

    hard_conditions=[
        _cond("三次探底", "bottom_touch_count", "ge", 3,
              description="至少3次测试同一支撑位"),
        _cond("不创新低", "third_bottom_vs_second", "ge", 0.99,
              description="第三次低点 >= 第二次低点的99%，未创新低"),
        _cond("颈线突破", "neckline_breakout", "eq", True,
              description="收盘价突破三重底颈线位（三次反弹高点连线）"),
        _cond("突破放量", "breakout_volume_ratio", "ge", 1.5,
              description="突破颈线时成交量 >= 近期均量的1.5倍"),
        _cond("底部间隔时间", "bottom_spacing_days", "ge", 5,
              description="三次探底之间至少间隔5个交易日，形态有效"),
    ],

    shape_conditions=[
        _cond("探底缩量", "bottom_volume_vs_avg", "le", 0.7, weight=0.3,
              description="每次探底时成交量递减，抛压衰竭"),
        _cond("MACD底背离", "macd_bullish_divergence", "eq", True, weight=0.4,
              description="MACD出现底背离信号"),
        _cond("颈线回踩确认", "neckline_pullback_confirmed", "eq", True, weight=0.3,
              description="突破颈线后有回踩确认动作且未跌破"),
    ],

    best_env=_env(
        min_limit_up=20, min_up_down_ratio=0.8,
        volume_trend="stable", theme_requirement="any",
        description="市场情绪低迷或混沌期，正是布局底部反转股的时候"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-6.0, max_hold_days=15,
        avoid_conditions=["跌破第三底低点", "突破颈线后3日内跌回"],
        description="若跌破第三底低点，形态失败，止损离场"
    ),

    applicable_cycles=["混沌期", "启动期"],
    forbidden_cycles=["高潮期", "退潮期"],
    category="技术分析",
    subcategory="底部反转",
)


# ═══════════════════════════════════════════════════════
# 14. 反核战法
# ═══════════════════════════════════════════════════════
ANTI_NUCLEAR_TACTIC = TacticRuleSet(
    name="反核战法",
    code="ANTI_NUCLEAR",
    core_logic="强势股前日跌停或大阴线，次日超预期高开高走反包涨停",
    description=(
        "反核战法（反包战法）捕捉强势股在被核按钮（恐慌性抛售）后的超预期修复。 "
        "前一日跌停或收出大阴线后，次日市场预期继续下跌，但如果该股能够超预期 "
        "高开高走甚至涨停，将前日阴线完全包住，形成经典的反包形态。这种走势表明 "
        "资金强烈看好，洗盘彻底，后续往往还有上涨空间。"
    ),
    risk_level="extreme",
    hold_period="1-2天",

    hard_conditions=[
        _cond("前日大阴线", "prev_day_change_pct", "le", -7.0,
              description="前一日跌幅>=7%或为跌停板"),
        _cond("次日反包", "today_change_pct", "ge", 7.0,
              description="当日涨幅>=7%，强势反包"),
        _cond("价格反包", "price_engulf_prev_high", "ge", 1.0,
              description="当日最高价 >= 前日最高价，完成反包"),
        _cond("反包放量", "today_volume_vs_yesterday", "ge", 0.8,
              description="当日成交量 >= 前日成交量的80%"),
        _cond("人气基础", "is_popular_stock", "eq", True,
              description="为市场人气股或题材核心股，非冷门股"),
    ],

    shape_conditions=[
        _cond("竞价超预期", "auction_surprise", "eq", True, weight=0.4,
              description="集合竞价高开或平开，远超市场低开预期"),
        _cond("早盘快速拉升", "morning_rally_speed", "ge", 5.0, weight=0.3,
              description="开盘后30分钟内拉升>=5%，资金抢筹"),
        _cond("前日龙虎榜未大卖", "prev_day_yingyou_not_dump", "eq", True, weight=0.3,
              description="前日龙虎榜显示游资未大规模出货"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=0.8,
        volume_trend="increase", theme_requirement="moderate",
        description="市场分歧期或情绪修复期，反核成功率最高"
    ),

    risk_boundary=_risk(
        max_position_pct=15.0, stop_loss_pct=-3.0, max_hold_days=2,
        avoid_conditions=["反包后炸板未回封", "次日低开>5%"],
        description="极端高风险操作，仓位控制在1.5成以内，不板即走"
    ),

    applicable_cycles=["分歧期", "启动期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="情绪周期",
    subcategory="反包博弈",
)


# ═══════════════════════════════════════════════════════
# 15. 缩量尾盘先手战法
# ═══════════════════════════════════════════════════════
SHRINK_TAIL_PREEMPT_TACTIC = TacticRuleSet(
    name="缩量尾盘先手战法",
    code="SHRINK_TAIL_PREEMPT",
    core_logic="尾盘30分钟出现缩量企稳信号，提前布局次日先手",
    description=(
        "缩量尾盘先手战法是一种逆向布局战法。在尾盘30分钟内，当股价在日内低位 "
        "出现缩量企稳迹象（不再创新低、分时走平、买盘出现），表明空头力量衰竭。 "
        "此时提前买入布局，博取次日高开或反弹的先手优势。核心在于识别真正的 "
        "缩量企稳而非下跌中继。"
    ),
    risk_level="medium",
    hold_period="1-2天",

    hard_conditions=[
        _cond("尾盘缩量", "tail_volume_vs_avg", "le", 0.6,
              description="尾盘30分钟成交量 <= 当日均量的60%"),
        _cond("尾盘企稳", "tail_price_stable", "eq", True,
              description="尾盘30分钟内价格不再创新低，出现企稳迹象"),
        _cond("日内已有跌幅", "intraday_decline_pct", "ge", 3.0,
              description="当日已有>=3%的跌幅，释放风险"),
        _cond("未封跌停", "not_limit_down", "eq", True,
              description="未封死跌停板，有资金在承接"),
        _cond("次日高开预期", "next_day_up_expectation", "eq", True,
              description="存在次日高开或反弹的预期差"),
    ],

    shape_conditions=[
        _cond("尾盘出现买盘堆单", "tail_bid_stacking", "eq", True, weight=0.3,
              description="尾盘买盘挂单明显增厚"),
        _cond("MACD未死叉或即将金叉", "macd_tail_status", "eq", "bullish", weight=0.4,
              description="MACD指标未死叉或即将金叉，动量未恶化"),
        _cond("前日涨停或有辨识度", "has_recognition", "eq", True, weight=0.3,
              description="为前日涨停股或市场辨识度个股，次日有资金关注"),
    ],

    best_env=_env(
        min_limit_up=25, min_up_down_ratio=0.8,
        volume_trend="stable", theme_requirement="any",
        description="市场分歧期或震荡期，适合逆向布局"
    ),

    risk_boundary=_risk(
        max_position_pct=20.0, stop_loss_pct=-3.0, max_hold_days=2,
        avoid_conditions=["次日低开>4%", "尾盘继续下杀创新低"],
        description="纯隔日超短，次日不达预期立即离场"
    ),

    applicable_cycles=["分歧期", "混沌期"],
    forbidden_cycles=["退潮期"],
    category="技术分析",
    subcategory="尾盘策略",
)


# ═══════════════════════════════════════════════════════
# 16. 三维资金共振法
# ═══════════════════════════════════════════════════════
CAPITAL_3D_RESONANCE_TACTIC = TacticRuleSet(
    name="三维资金共振法",
    code="CAPITAL_3D_RESONANCE",
    core_logic="从宏观(北向资金)、中观(板块资金)、微观(个股主力资金)三个维度分析资金流向，三维共振时介入",
    description=(
        "【主播：财金贝儿】三维资金共振法核心哲学：资金是股价上涨的第一推动力，只有宏观、中观、微观三个维度资金同时流入，"
        "才能形成最强的上涨合力。战法释义：①宏观维度——北向资金连续3天净流入，外资看好A股整体；"
        "②中观维度——板块资金排名前5且持续流入，主力资金聚集该方向；③微观维度——个股主力资金净流入，有真实买盘推动。"
        "操作要点：三维度共振当日或次日开盘介入，选择最强势的个股；若两维度共振可轻仓试错，单维度不操作。"
        "风控纪律：任一维度出现资金流出信号，立即减仓；两个维度同时流出，清仓离场。"
    ),
    risk_level="medium",
    hold_period="2-5天",

    hard_conditions=[
        _cond("北向资金连续净流入", "northbound_net_inflow_days", "ge", 3,
              description="北向资金连续3天净流入，外资看好整体市场"),
        _cond("板块资金排名", "sector_capital_rank", "le", 5,
              description="所属板块资金排名前5且持续流入"),
        _cond("个股主力资金净流入", "main_force_net_inflow", "eq", True,
              description="个股主力资金当日净流入，有真实买盘"),
        _cond("成交量量比", "volume_ratio", "ge", 1.2,
              description="成交量量比>1.2，成交活跃"),
        _cond("换手率区间", "turnover_rate", "between", (5.0, 15.0),
              description="换手率5%-15%，有资金关注但不过度狂热"),
    ],

    shape_conditions=[
        _cond("股价沿5日均线上行", "price_above_ma5", "eq", True, weight=0.3,
              description="股价沿5日均线上行，短期趋势向上"),
        _cond("板块有涨停龙头", "sector_has_leader_board", "eq", True, weight=0.4,
              description="所属板块有涨停龙头股，板块效应强"),
        _cond("资金流向与股价正相关", "capital_price_correlation", "ge", 0.7, weight=0.3,
              description="资金流向与股价走势正相关系数>=0.7"),
    ],

    best_env=_env(
        min_limit_up=35, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪发酵期或加速期，资金活跃，主线明确"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=5,
        avoid_conditions=["北向资金转流出", "板块资金排名跌出前10", "个股主力连续流出2天"],
        description="任一维度资金流出即减仓，两维度流出清仓，严格按资金信号执行"
    ),

    applicable_cycles=["发酵期", "加速期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="资金流",
    subcategory="多维共振",
)


# ═══════════════════════════════════════════════════════
# 17. 龙虎榜资金流战法
# ═══════════════════════════════════════════════════════
CAPITAL_DRAGON_TIGER_TACTIC = TacticRuleSet(
    name="龙虎榜资金流战法",
    code="CAPITAL_DRAGON_TIGER",
    core_logic="龙虎榜买卖席位组合分析，识别主力真实意图，跟随主力资金操作",
    description=(
        "【主播：阿宝龙哥】龙虎榜资金流战法核心哲学：龙虎榜是观察主力资金动向的最佳窗口，"
        "通过分析买卖席位组合，可以识别主力是真实进攻还是拉高出货。"
        "战法释义：①三日榜连续净流入——主力资金持续流入，非一日游；②买入席位金额远大于卖出席位——买方力量占优；"
        "③单一席位买入不过半——筹码分布均匀，非单一庄家控盘；④封单量占流通盘比例高——市场认可度高。"
        "操作要点：选择有机构+游资合力买入的个股，知名游资席位参与为佳；次日高开不追太高，等分时回踩介入。"
        "风控纪律：龙虎榜一出即评估席位质量，出现东财/散户大本营大量买入要警惕；次日低开超预期立即止损。"
    ),
    risk_level="high",
    hold_period="1-2天",

    hard_conditions=[
        _cond("三日榜连续净流入", "dragon_tiger_3day_net_inflow", "eq", True,
              description="三日榜主力资金连续净流入，非一日游行情"),
        _cond("买卖比", "dragon_tiger_buy_sell_ratio", "ge", 2.0,
              description="买入席位总金额 >= 卖出席位总金额的2倍"),
        _cond("单一席位占比", "single_seat_buy_pct", "le", 50.0,
              description="单一席位买入金额占比<50%，筹码分散"),
        _cond("封单流通比", "seal_amount_float_ratio", "ge", 1.0,
              description="涨停封单量/流通盘 > 1%，封板力度强"),
        _cond("开板次数", "open_board_count", "le", 2,
              description="当日开板次数<=2，涨停板质量高"),
    ],

    shape_conditions=[
        _cond("机构游资合力", "institution_yingyou_together", "eq", True, weight=0.4,
              description="龙虎榜显示机构投资者与游资合力买入，非单一力量"),
        _cond("知名游资参与", "famous_yingyou_present", "eq", True, weight=0.3,
              description="知名游资席位参与买入，市场关注度高"),
        _cond("涨停板质量高", "limit_up_quality_score", "ge", 80, weight=0.3,
              description="涨停板质量评分>=80分（封板时间早、封单足、开板少）"),
    ],

    best_env=_env(
        min_limit_up=40, min_up_down_ratio=1.2,
        volume_trend="increase", theme_requirement="strong",
        description="市场情绪发酵期或加速期，连板氛围好，龙虎榜效应强"
    ),

    risk_boundary=_risk(
        max_position_pct=20.0, stop_loss_pct=-4.0, max_hold_days=2,
        avoid_conditions=["散户大本营大量买入", "次日低开>5%", "龙虎榜显示主力净卖出"],
        description="高风险操作，仓位控制在2成以内，次日不板即走"
    ),

    applicable_cycles=["发酵期", "加速期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="资金流",
    subcategory="龙虎榜",
)


# ═══════════════════════════════════════════════════════
# 18. 资金情绪四阶段模型
# ═══════════════════════════════════════════════════════
CAPITAL_EMOTION_4PHASE_TACTIC = TacticRuleSet(
    name="资金情绪四阶段模型",
    code="CAPITAL_EMOTION_4PHASE",
    core_logic="资金是情绪周期的量化体现，启动/发酵/加速/退潮四阶段的资金特征各不相同，据此精准操作",
    description=(
        "【主播：作手逍遥风】资金情绪四阶段模型核心哲学：资金是情绪的唯一量化指标，情绪周期的每个阶段都有独特的资金特征。"
        "战法释义：①启动期——资金试探性流入，成交量温和放大，是建仓时机；②发酵期——资金加速流入，成交量明显放大，是加仓时机；"
        "③加速期——资金爆发式流入，成交量天量，是持有或减仓时机；④退潮期——资金流出，成交量萎缩，是空仓时机。"
        "操作要点：严格按照资金阶段信号操作，启动期建底仓，发酵期加仓，加速期持有，退潮期清仓。做T操作仅在发酵期和加速期进行，"
        "单次做T亏损不超过3%。风控纪律：退潮期资金一流出立即空仓，绝不逆势操作；周期判断错误时立即止损切换。"
    ),
    risk_level="medium",
    hold_period="1-5天(分阶段)",

    hard_conditions=[
        _cond("启动期资金试探流入", "capital_inflow_startup", "eq", True,
              description="启动期资金试探性流入，成交量温和放大"),
        _cond("发酵期资金加速流入", "capital_inflow_ferment", "eq", True,
              description="发酵期资金加速流入，成交量明显放大"),
        _cond("加速期资金爆发流入", "capital_inflow_accelerate", "eq", True,
              description="加速期资金爆发式流入，成交量天量水平"),
        _cond("退潮期资金流出空仓", "capital_outflow_exit", "eq", True,
              description="退潮期资金流出，立即空仓等待"),
        _cond("做T亏损控制", "t_trade_max_loss_pct", "ge", -3.0,
              description="做T操作单次亏损控制在3%以内"),
    ],

    shape_conditions=[
        _cond("底部筹码峰未松动", "bottom_chip_peak_stable", "eq", True, weight=0.4,
              description="底部筹码峰未松动，主力未出货"),
        _cond("板块联动效应", "sector_linkage_effect", "eq", True, weight=0.3,
              description="所属板块出现联动效应，非个股独舞"),
        _cond("资金净流入大于流出", "net_inflow_vs_outflow", "eq", True, weight=0.3,
              description="个股资金净流入持续大于流出"),
    ],

    best_env=_env(
        min_limit_up=35, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪处于启动期、发酵期或加速期，资金活跃"
    ),

    risk_boundary=_risk(
        max_position_pct=25.0, stop_loss_pct=-5.0, max_hold_days=5,
        avoid_conditions=["退潮期资金流出", "筹码峰高位松动", "板块批量跌停"],
        description="按资金阶段严格操作，退潮期立即空仓，不逆势持股"
    ),

    applicable_cycles=["启动期", "发酵期", "加速期"],
    forbidden_cycles=["退潮期"],
    category="资金流",
    subcategory="资金周期",
)


# ═══════════════════════════════════════════════════════
# 19. 资金流四步法
# ═══════════════════════════════════════════════════════
CAPITAL_4STEP_METHOD_TACTIC = TacticRuleSet(
    name="资金流四步法",
    code="CAPITAL_4STEP_METHOD",
    core_logic="完整识别建仓→洗盘→拉升→出货的资金流全过程，在不同阶段采取不同策略",
    description=(
        "【主播：浪哥财经】资金流四步法核心哲学：主力操作的每个阶段都有独特的资金特征，"
        "通过识别资金流四步法的不同阶段，可以精准跟随主力节奏。"
        "战法释义：①建仓期——资金温和流入，成交量有节奏放大，股价缓慢上涨，是跟随建仓时机；"
        "②洗盘期——资金小幅流出，股价回调但不跌破主力成本区，是持股或低吸时机；"
        "③拉升期——资金大幅流入，成交量明显放大，股价快速上涨，是持有或加仓时机；"
        "④出货期——资金流出，筹码松动，是清仓时机。"
        "操作要点：建仓期跟随买入，洗盘期持股不动，拉升期持有享受主升，出货期第一时间离场。"
        "风控纪律：成本集中度<10%才确认主力控盘；出货期资金一流出立即离场，不可犹豫。"
    ),
    risk_level="medium",
    hold_period="5-10天",

    hard_conditions=[
        _cond("建仓期资金温和流入", "capital_building_inflow", "eq", True,
              description="建仓期资金温和流入，成交量有节奏放大"),
        _cond("洗盘期资金小幅流出", "capital_washout_mild_outflow", "eq", True,
              description="洗盘期资金小幅流出，股价不破主力成本区"),
        _cond("拉升期资金大幅流入", "capital_pull_inflow", "eq", True,
              description="拉升期资金大幅流入，成交量明显放大"),
        _cond("出货期资金流出离场", "capital_distribute_exit", "eq", True,
              description="出货期资金流出立即离场"),
        _cond("成本集中度", "cost_concentration_pct", "le", 10.0,
              description="主力成本集中度<10%，控盘度高"),
    ],

    shape_conditions=[
        _cond("建仓期成交量有节奏放大", "building_volume_rhythm", "eq", True, weight=0.3,
              description="建仓期成交量呈规律性放大，非脉冲式"),
        _cond("拉升期放量突破", "pull_volume_breakout", "eq", True, weight=0.4,
              description="拉升期放量突破关键压力位"),
        _cond("出货期筹码松动", "distribute_chip_loose", "eq", True, weight=0.3,
              description="出货期筹码峰开始松动，高位筹码增加"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪处于启动期、发酵期或加速期，适合中长线资金流跟踪"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=10,
        avoid_conditions=["洗盘跌破主力成本区", "出货期筹码松动", "资金连续流出3天"],
        description="主力成本区为最后防线，跌破即止损；出货期信号一出立即清仓"
    ),

    applicable_cycles=["启动期", "发酵期", "加速期"],
    forbidden_cycles=["退潮期", "混沌期"],
    category="资金流",
    subcategory="主力行为",
)


# ═══════════════════════════════════════════════════════
# 20. 资金流量化指标体系
# ═══════════════════════════════════════════════════════
CAPITAL_QUANT_INDEX_TACTIC = TacticRuleSet(
    name="资金流量化指标体系",
    code="CAPITAL_QUANT_INDEX",
    core_logic="资金流数据可量化验证，构建客观交易模型，用数据说话",
    description=(
        "【主播：芝士财经】资金流量化指标体系核心哲学：资金流数据完全可量化，通过构建客观指标体系，"
        "排除主观情绪干扰，实现数据驱动的交易决策。"
        "战法释义：①主力净流入率>5%且连续3天——主力资金强势流入；②北向持仓占比>2%且在加仓——外资认可；"
        "③机构持仓占比>10%——机构资金聚集；④资金流与股价相关系数>0.8——资金推动型上涨，非无量空涨；"
        "⑤背离度计算使用5天数据——识别资金与价格的背离信号。"
        "操作要点：所有指标同时满足时满仓操作，4项满足时8成仓，3项满足时5成仓，低于3项不操作。"
        "风控纪律：任何指标恶化立即降仓；背离度>0.5时视为强背离，减仓应对。"
    ),
    risk_level="low",
    hold_period="3-7天",

    hard_conditions=[
        _cond("主力净流入率", "main_force_inflow_rate_pct", "ge", 5.0,
              description="主力净流入率>5%且连续3天达标"),
        _cond("北向持仓占比", "northbound_hold_pct", "ge", 2.0,
              description="北向持仓占比>2%且处于加仓状态"),
        _cond("机构持仓占比", "institution_hold_pct", "ge", 10.0,
              description="机构持仓占比>10%，机构资金聚集"),
        _cond("资金流股价相关性", "capital_price_correlation", "ge", 0.8,
              description="资金流与股价相关系数>0.8，资金推动型上涨"),
        _cond("背离度监测", "divergence_5day_calc", "eq", True,
              description="使用5天数据计算资金流与价格背离度"),
    ],

    shape_conditions=[
        _cond("资金流强度评分", "capital_flow_score", "ge", 80, weight=0.4,
              description="资金流强度评分>=80分，多维度综合评估优秀"),
        _cond("背离度阈值", "divergence_strength", "ge", 0.5, weight=0.3,
              description="背离度>0.5为强背离信号，需警惕"),
        _cond("多指标共振", "multi_index_resonance", "eq", True, weight=0.3,
              description="多个量化指标同时发出同向信号，共振效应强"),
    ],

    best_env=_env(
        min_limit_up=20, min_up_down_ratio=0.8,
        volume_trend="any", theme_requirement="any",
        description="适用于所有市场情绪周期，量化模型不受情绪影响"
    ),

    risk_boundary=_risk(
        max_position_pct=35.0, stop_loss_pct=-5.0, max_hold_days=7,
        avoid_conditions=["主力净流入率转负", "北向资金连续3天减仓", "背离度突破0.5"],
        description="低风险量化模型，但指标恶化时仍需严格执行降仓纪律"
    ),

    applicable_cycles=["启动期", "发酵期", "加速期", "分歧期", "混沌期"],
    forbidden_cycles=["退潮期"],
    category="资金流",
    subcategory="量化指标",
)


# ═══════════════════════════════════════════════════════
# 21. 资金筹码共振战法
# ═══════════════════════════════════════════════════════
CAPITAL_CHIP_RESONANCE_TACTIC = TacticRuleSet(
    name="资金筹码共振战法",
    code="CAPITAL_CHIP_RESONANCE",
    core_logic="资金流决定股价方向，筹码峰决定上涨空间，两者共振时捕捉最佳买点",
    description=(
        "【主播：股海老司机】资金筹码共振战法核心哲学：资金流决定方向（往哪走），筹码峰决定空间（能走多远），"
        "两者共振时才是最安全的买点。"
        "战法释义：①底部筹码峰密集+资金流入=主力建仓信号——底部筹码集中说明主力在收集筹码，配合资金流入确认建仓；"
        "②筹码峰锁定+资金加速=拉升信号——筹码峰不动说明主力锁仓，配合资金加速流入确认拉升；"
        "③筹码峰松动+资金流出=出货信号——高位筹码分散说明主力出货，配合资金流出确认顶部。"
        "操作要点：建仓信号出现时建底仓，拉升信号出现时加仓，出货信号出现时清仓。"
        "风控纪律：套牢盘<10%才操作；跌破筹码峰下沿3%立即止损。"
    ),
    risk_level="medium",
    hold_period="3-7天",

    hard_conditions=[
        _cond("底部筹码峰密集资金流入", "bottom_chip_dense_capital_in", "eq", True,
              description="底部筹码峰密集且资金流入，主力建仓信号"),
        _cond("筹码峰锁定资金加速", "chip_locked_capital_accel", "eq", True,
              description="筹码峰锁定不动且资金加速流入，拉升信号"),
        _cond("筹码峰松动资金流出", "chip_loose_capital_out", "eq", True,
              description="筹码峰松动且资金流出，出货信号立即离场"),
        _cond("套牢盘比例", "trapped_chip_ratio", "le", 10.0,
              description="上方套牢盘<10%，拉升阻力小"),
        _cond("筹码峰止损", "chip_peak_stop_loss_pct", "ge", -3.0,
              description="跌破筹码峰下沿3%立即止损"),
    ],

    shape_conditions=[
        _cond("筹码峰厚实紧凑", "chip_peak_compact", "eq", True, weight=0.4,
              description="底部筹码峰厚实紧凑，主力控盘度高"),
        _cond("资金流入配合筹码峰上移", "capital_chip_peak_move_up", "eq", True, weight=0.3,
              description="资金流入配合筹码峰上移，健康上涨"),
        _cond("上方无套牢盘", "no_trapped_chip_above", "eq", True, weight=0.3,
              description="上方无密集套牢盘，上涨空间大"),
    ],

    best_env=_env(
        min_limit_up=30, min_up_down_ratio=1.0,
        volume_trend="increase", theme_requirement="moderate",
        description="市场情绪启动期或发酵期，主力资金积极建仓"
    ),

    risk_boundary=_risk(
        max_position_pct=30.0, stop_loss_pct=-5.0, max_hold_days=7,
        avoid_conditions=["筹码峰高位松动", "跌破筹码峰下沿3%", "资金连续流出2天"],
        description="筹码峰为操作核心参照，跌破筹码峰下沿3%是最后止损线"
    ),

    applicable_cycles=["启动期", "发酵期"],
    forbidden_cycles=["退潮期", "高潮期"],
    category="跟庄",
    subcategory="筹码资金共振",
)


# ──────────────────────────────────────────────────────────
# 战法总库
# ──────────────────────────────────────────────────────────

ALL_TACTICS: List[TacticRuleSet] = [
    CHIP_PEAK_TACTIC,               # 1. 筹码峰战法
    TRIPLE_VOLUME_BREAKOUT_TACTIC,  # 2. 三倍量突破战法
    SHRINK_VOLUME_BREAKOUT_TACTIC,  # 3. 缩量突破战法
    LEFT_PEAK_BREAK_TACTIC,         # 4. 过左峰战法
    FIRST_YIN_TACTIC,               # 5. 首阴战法
    N_SHAPE_TACTIC,                 # 6. N字形战法
    MAGPIE_PLUM_TACTIC,             # 7. 喜鹊闹梅战法
    PLATFORM_BREAKOUT_TACTIC,       # 8. 平台突破战法
    BOARD_1TO2_TACTIC,              # 9. 一进二战法
    DRAGON_EMOTION_TACTIC,          # 10. 龙头情绪战法
    BOLLINGER_TACTIC,               # 11. 布林带战法
    INTRADAY_SUPPORT_TACTIC,        # 12. 分时承接战法
    TRIPLE_BOTTOM_TACTIC,           # 13. 三星探底战法
    ANTI_NUCLEAR_TACTIC,                    # 14. 反核战法
    SHRINK_TAIL_PREEMPT_TACTIC,             # 15. 缩量尾盘先手战法
    CAPITAL_3D_RESONANCE_TACTIC,            # 16. 三维资金共振法
    CAPITAL_DRAGON_TIGER_TACTIC,            # 17. 龙虎榜资金流战法
    CAPITAL_EMOTION_4PHASE_TACTIC,          # 18. 资金情绪四阶段模型
    CAPITAL_4STEP_METHOD_TACTIC,            # 19. 资金流四步法
    CAPITAL_QUANT_INDEX_TACTIC,             # 20. 资金流量化指标体系
    CAPITAL_CHIP_RESONANCE_TACTIC,          # 21. 资金筹码共振战法
]

# 按风险等级分类
TACTICS_BY_RISK: Dict[str, List[TacticRuleSet]] = {
    "low":    [t for t in ALL_TACTICS if t.risk_level == "low"],
    "medium": [t for t in ALL_TACTICS if t.risk_level == "medium"],
    "high":   [t for t in ALL_TACTICS if t.risk_level == "high"],
    "extreme":[t for t in ALL_TACTICS if t.risk_level == "extreme"],
}

# 按适用周期分类
TACTICS_BY_CYCLE: Dict[str, List[TacticRuleSet]] = {}
for t in ALL_TACTICS:
    for cycle in t.applicable_cycles:
        if cycle not in TACTICS_BY_CYCLE:
            TACTICS_BY_CYCLE[cycle] = []
        if t not in TACTICS_BY_CYCLE[cycle]:
            TACTICS_BY_CYCLE[cycle].append(t)

# 按持有周期分类
TACTICS_BY_HOLD_PERIOD: Dict[str, List[TacticRuleSet]] = {
    "超短(1-2天)": [t for t in ALL_TACTICS
                     if t.hold_period in ("1天", "1-2天")],
    "短波(3-7天)": [t for t in ALL_TACTICS
                     if t.hold_period in ("2-5天", "3-5天", "3-7天")],
    "中线(5-15天)": [t for t in ALL_TACTICS
                      if t.hold_period in ("5-10天", "7-15天")],
}


def get_tactic_by_code(code: str) -> Optional[TacticRuleSet]:
    """通过编码查找战法

    Args:
        code: 战法编码（如 "N_SHAPE"）

    Returns:
        匹配的战法规则集，未找到返回None
    """
    for tactic in ALL_TACTICS:
        if tactic.code == code:
            return tactic
    return None


def get_tactic_by_name(name: str) -> Optional[TacticRuleSet]:
    """通过名称查找战法

    Args:
        name: 战法名称（如 "N字形战法"）

    Returns:
        匹配的战法规则集，未找到返回None
    """
    for tactic in ALL_TACTICS:
        if tactic.name == name:
            return tactic
    return None


def list_all_tactics() -> List[Dict[str, str]]:
    """列出所有战法概览

    Returns:
        战法概览列表，每项包含名称、编码、核心逻辑、风险等级
    """
    return [
        {
            "name": t.name,
            "code": t.code,
            "core_logic": t.core_logic,
            "risk_level": t.risk_level,
            "hold_period": t.hold_period,
            "applicable_cycles": ",".join(t.applicable_cycles),
        }
        for t in ALL_TACTICS
    ]


def get_tactics_for_cycle(cycle: str) -> List[TacticRuleSet]:
    """获取指定情绪周期适用的战法列表

    Args:
        cycle: 情绪周期名称（如 "发酵期"）

    Returns:
        适用的战法列表
    """
    return TACTICS_BY_CYCLE.get(cycle, [])


def get_tactics_summary_stats() -> Dict[str, Any]:
    """获取战法库统计信息

    Returns:
        统计字典
    """
    return {
        "total_tactics": len(ALL_TACTICS),
        "by_risk_level": {
            level: len(tactics)
            for level, tactics in TACTICS_BY_RISK.items()
        },
        "by_cycle": {
            cycle: len(tactics)
            for cycle, tactics in TACTICS_BY_CYCLE.items()
        },
        "by_hold_period": {
            period: len(tactics)
            for period, tactics in TACTICS_BY_HOLD_PERIOD.items()
        },
        "tactic_codes": [t.code for t in ALL_TACTICS],
        "tactic_names": [t.name for t in ALL_TACTICS],
    }


# ──────────────────────────────────────────────────────────
# 战法分类体系：6大类 + 小类
# ──────────────────────────────────────────────────────────

# 6大类定义
TACTIC_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "资金流": {
        "description": "基于主力资金流向、北向资金、龙虎榜等资金行为分析",
        "icon": "💰",
        "subcategories": {
            "多维共振": "宏观/中观/微观三维度资金共振",
            "龙虎榜": "龙虎榜席位分析与跟随",
            "资金周期": "资金情绪四阶段模型",
            "主力行为": "建仓/洗盘/拉升/出货全过程识别",
            "量化指标": "资金流量化指标体系",
        },
    },
    "筹码峰": {
        "description": "基于筹码分布、支撑压力位的资金沉淀分析",
        "icon": "🏔️",
        "subcategories": {
            "筹码分布": "低位单峰密集、多峰形态识别",
            "压力突破": "过左峰、解放套牢盘",
        },
    },
    "技术分析": {
        "description": "基于K线形态、技术指标、分时盘口的经典技术分析",
        "icon": "📊",
        "subcategories": {
            "K线形态": "N字形、喜鹊闹梅等经典形态",
            "底部反转": "三星探底、喜鹊闹梅等底部信号",
            "平台突破": "横盘整理后放量突破",
            "技术指标": "布林带、MACD等技术指标应用",
            "分时盘口": "分时承接、均价线支撑",
            "尾盘策略": "尾盘缩量企稳先手布局",
        },
    },
    "情绪周期": {
        "description": "基于市场情绪周期、连板接力、龙头博弈",
        "icon": "🔥",
        "subcategories": {
            "龙头低吸": "龙头首阴低吸战法",
            "连板接力": "一进二、连板晋级",
            "龙头博弈": "情绪周期龙头综合战法",
            "反包博弈": "反核反包涨停战法",
        },
    },
    "量价关系": {
        "description": "基于成交量与价格配合关系的量能分析",
        "icon": "📈",
        "subcategories": {
            "放量突破": "三倍量突破等放量启动信号",
            "缩量控盘": "缩量突破、筹码锁定",
        },
    },
    "跟庄": {
        "description": "跟随主力资金行为，识别庄家建仓/拉升/出货",
        "icon": "🎯",
        "subcategories": {
            "筹码资金共振": "资金流+筹码峰双重确认",
        },
    },
}


# 按大类分类索引
TACTICS_BY_CATEGORY: Dict[str, List[TacticRuleSet]] = {}
for t in ALL_TACTICS:
    cat = t.category
    if not cat:
        cat = "未分类"
    if cat not in TACTICS_BY_CATEGORY:
        TACTICS_BY_CATEGORY[cat] = []
    TACTICS_BY_CATEGORY[cat].append(t)


# 按小类分类索引
TACTICS_BY_SUBCATEGORY: Dict[str, List[TacticRuleSet]] = {}
for t in ALL_TACTICS:
    subcat = t.subcategory
    if subcat:
        if subcat not in TACTICS_BY_SUBCATEGORY:
            TACTICS_BY_SUBCATEGORY[subcat] = []
        TACTICS_BY_SUBCATEGORY[subcat].append(t)


def get_tactics_by_category(category: str) -> List[TacticRuleSet]:
    """按战法大类获取战法列表

    Args:
        category: 战法大类名称（如 "资金流" / "技术分析" / "情绪周期" / "筹码峰" / "量价关系" / "跟庄"）

    Returns:
        战法列表
    """
    return TACTICS_BY_CATEGORY.get(category, [])


def get_tactics_by_subcategory(subcategory: str) -> List[TacticRuleSet]:
    """按战法小类获取战法列表

    Args:
        subcategory: 战法小类名称（如 "多维共振" / "龙虎榜" / "K线形态" 等）

    Returns:
        战法列表
    """
    return TACTICS_BY_SUBCATEGORY.get(subcategory, [])


def get_all_categories() -> Dict[str, Any]:
    """获取所有战法大类及小类统计信息

    Returns:
        战法分类体系字典，包含6大类及其小类
    """
    result = {
        "categories": {},
        "total_tactics": len(ALL_TACTICS),
        "category_count": len(TACTIC_CATEGORIES),
    }

    for cat_name, cat_info in TACTIC_CATEGORIES.items():
        tactics = TACTICS_BY_CATEGORY.get(cat_name, [])
        subcategories = {}
        for subcat_name, subcat_desc in cat_info["subcategories"].items():
            sub_tactics = TACTICS_BY_SUBCATEGORY.get(subcat_name, [])
            subcategories[subcat_name] = {
                "description": subcat_desc,
                "count": len(sub_tactics),
                "tactics": [
                    {
                        "name": t.name,
                        "code": t.code,
                        "risk_level": t.risk_level,
                        "hold_period": t.hold_period,
                    }
                    for t in sub_tactics
                ],
            }

        result["categories"][cat_name] = {
            "description": cat_info["description"],
            "icon": cat_info["icon"],
            "count": len(tactics),
            "subcategories": subcategories,
            "tactics": [
                {
                    "name": t.name,
                    "code": t.code,
                    "risk_level": t.risk_level,
                    "subcategory": t.subcategory,
                }
                for t in tactics
            ],
        }

    return result


def get_category_tree() -> List[Dict[str, Any]]:
    """获取战法分类树形结构（用于前端展示）

    Returns:
        树形结构列表
    """
    tree = []
    for cat_name, cat_info in TACTIC_CATEGORIES.items():
        tactics = TACTICS_BY_CATEGORY.get(cat_name, [])
        children = []
        for subcat_name, subcat_desc in cat_info["subcategories"].items():
            sub_tactics = TACTICS_BY_SUBCATEGORY.get(subcat_name, [])
            children.append({
                "key": f"{cat_name}/{subcat_name}",
                "title": subcat_name,
                "description": subcat_desc,
                "count": len(sub_tactics),
                "tactics": [
                    {"name": t.name, "code": t.code, "risk_level": t.risk_level}
                    for t in sub_tactics
                ],
            })

        tree.append({
            "key": cat_name,
            "title": cat_name,
            "description": cat_info["description"],
            "icon": cat_info["icon"],
            "count": len(tactics),
            "children": children,
        })

    return tree
