"""资金流战法库 — 抖音主播资金流战法体系

包含6大资金流实战派主播的完整战法体系，每套战法包含:
- 主播名称与核心交易哲学
- 战法释义（核心逻辑详解）
- 操作要点（具体执行规则）
- 风控纪律（止损止盈纪律）

主播列表:
  1. 财金贝儿    — 三维资金共振法
  2. 阿宝龙哥    — 龙虎榜资金流战法体系
  3. 作手逍遥风  — 资金情绪四阶段模型
  4. 浪哥财经    — 资金流四步法
  5. 芝士财经    — 资金流量化指标体系
  6. 股海老司机  — 资金筹码共振战法

Author: SWAT Engine
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────
# 数据模型
# ──────────────────────────────────────────────────────────

@dataclass
class CapitalFlowTactic:
    """资金流战法 — 主播战法模型

    资金流战法不同于量化战法(TacticRuleSet)，更侧重资金行为学原理、
    主力资金意图识别和资金流与股价关系的深度解析。
    """
    # 基础信息
    name: str                          # 战法名称
    code: str                          # 战法编码
    streamer_name: str                 # 主播名称
    streamer_title: str                # 主播头衔/简介
    philosophy: str                    # 核心交易哲学

    # 战法核心（多个子战法）
    core_tactics: List[Dict[str, Any]] = field(default_factory=list)

    # 操作要点
    operation_points: List[str] = field(default_factory=list)

    # 风控纪律
    risk_discipline: List[str] = field(default_factory=list)

    # 分类与标签
    category: str = "资金流"            # 战法大类
    risk_level: str = "medium"         # 风险等级: low/medium/high/extreme
    tags: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────
# 辅助函数：子战法构造器
# ──────────────────────────────────────────────────────────

def _core_tactic(name: str, interpretation: str, key_points: List[str]) -> Dict[str, Any]:
    """构造单个子战法字典"""
    return {
        "name": name,
        "interpretation": interpretation,       # 战法释义
        "key_points": key_points,               # 核心要点
    }


# ═══════════════════════════════════════════════════════
# 1. 财金贝儿 — 三维资金共振法
# ═══════════════════════════════════════════════════════
CAIJINBEIER_TACTIC = CapitalFlowTactic(
    name="三维资金共振法",
    code="CAPITAL_3D_RESONANCE",
    streamer_name="财金贝儿",
    streamer_title="资金流入门权威，粉丝超500万",
    philosophy="资金是股价涨跌的唯一驱动，通过「三维资金分析法」穿透主力伪装，实现「跟着聪明钱吃肉」的稳定盈利模式。",

    core_tactics=[
        _core_tactic(
            name="三维资金共振法",
            interpretation=(
                "从宏观、中观、微观三个维度分析资金流向，三维共振时产生最强信号。"
                "宏观资金判断市场整体趋势，中观资金锁定主线赛道，微观资金筛选具体标的。"
                "三维共振意味着市场、板块、个股的资金流向形成同向合力，此时介入胜率最高。"
            ),
            key_points=[
                "宏观资金：北向资金连续3-5天净流入，判断市场整体趋势",
                "中观资金：板块资金排名前5且持续流入，锁定主线赛道",
                "微观资金：个股主力资金净流入且股价稳步抬升，筛选标的",
            ],
        ),
        _core_tactic(
            name="北向资金赛道映射法",
            interpretation=(
                "通过北向资金在沪股通和深股通之间的流向差异，判断市场风格偏好。"
                "深股通净流入大于沪股通时，市场偏好成长型科技股；"
                "沪股通净流入大于深股通时，市场偏好价值型大盘蓝筹。"
                "据此映射调整持仓风格和选股方向。"
            ),
            key_points=[
                "深股通净流入 > 沪股通 → 聚焦创业板科技股",
                "沪股通净流入 > 深股通 → 布局大盘蓝筹白马",
                "结合汇率因素和外围市场环境综合判断",
            ],
        ),
        _core_tactic(
            name="资金分歧转一致战法",
            interpretation=(
                "捕捉主力资金从分歧走向一致的关键节点。"
                "个股连续3天资金小幅流入但股价横盘，说明多空分歧；"
                "第4天放量流入且股价突破，说明资金达成共识，合力拉升。"
                "分歧转一致的瞬间是最佳介入时机。"
            ),
            key_points=[
                "分歧期：个股连续3天资金小幅流入 + 股价横盘",
                "一致期：第4天放量流入 + 股价突破",
                "介入点：一致期确认当天尾盘或次日开盘",
            ],
        ),
    ],

    operation_points=[
        "北向资金不看单日看趋势，连续5天净流入为强信号",
        "板块资金需满足「连续3天净流入 + 涨幅<10%」，避免追高",
        "个股资金流入需配合成交量温和放大（量比>1.2），换手率控制在5%-15%",
        "三维资金信号出现共振时立即建仓，不等待回调",
        "优先选择机构+北向+游资合力买入的标的",
    ],

    risk_discipline=[
        "三维资金任一维度不满足，放弃操作",
        "北向资金单日流出超100亿，空仓观望",
        "个股资金流入但股价滞涨，视为诱多，立即离场",
        "三维共振信号消失后次日不修复，减半仓",
        "板块资金连续2天净流出，个股同步减仓",
    ],

    risk_level="medium",
    tags=["北向资金", "主力资金", "板块资金", "三维共振", "趋势跟踪"],
)


# ═══════════════════════════════════════════════════════
# 2. 阿宝龙哥 — 龙虎榜资金流战法体系
# ═══════════════════════════════════════════════════════
ABAOLOONG_TACTIC = CapitalFlowTactic(
    name="龙虎榜资金流战法体系",
    code="CAPITAL_DRAGON_TIGER",
    streamer_name="阿宝龙哥",
    streamer_title="龙虎榜+资金流双料实战派",
    philosophy="龙虎榜是主力资金的「体检报告」，资金流是「心电图」，两者结合可精准判断主力意图，构建「龙虎榜资金流战法体系」。",

    core_tactics=[
        _core_tactic(
            name="龙虎榜黄金组合战法",
            interpretation=(
                "通过分析龙虎榜买卖席位组合，识别主力资金的性质和意图。"
                "不同席位组合代表不同的市场信号：机构+北向+一线游资合力是最强买入信号；"
                "纯游资接力需要谨慎；机构大卖+游资接盘是危险信号。"
            ),
            key_points=[
                "王炸组合：机构+北向+一线游资（章盟主/赵老哥等）合力净买，重仓介入",
                "潜力组合：一线游资+二线游资协同买入，轻仓试错",
                "风险组合：机构大卖+游资接盘，坚决回避",
            ],
        ),
        _core_tactic(
            name="三日榜资金流确认法",
            interpretation=(
                "龙虎榜单日数据容易被主力操纵（对倒、诱多），三日榜更能反映真实意图。"
                "通过对比单日榜和三日榜的资金流向差异，识别真假建仓信号。"
                "三日榜连续净流入且金额递增，说明主力真心建仓而非短线对倒。"
            ),
            key_points=[
                "优先选择三日榜而非单日榜，避免主力单日对倒",
                "三日榜连续净流入且金额递增，为真建仓信号",
                "单日榜净流入但三日榜净流出，为诱多陷阱",
            ],
        ),
        _core_tactic(
            name="资金承接强度量化法",
            interpretation=(
                "通过量化涨停板封单数据，判断资金承接强度和涨停板质量。"
                "封单量/流通盘比例越高，封板质量越好，次日溢价率越高。"
                "开板次数反映抛压程度，开板过多说明分歧大、承接弱。"
            ),
            key_points=[
                "涨停板封单量/流通盘 > 1%，且封单稳定，为强承接",
                "开板次数≤2次，为有效涨停",
                "买入席位金额 > 卖出席位金额2倍以上，视为强买入",
                "机构席位净买占比>30%，适合中长线持有；游资席位净买占比>50%，适合短线套利",
            ],
        ),
    ],

    operation_points=[
        "优先选择三日榜而非单日榜，避免主力单日对倒",
        "买入席位金额 > 卖出席位金额2倍以上，视为强买入",
        "机构席位净买占比>30%，适合中长线持有；游资席位净买占比>50%，适合短线套利",
        "关注知名游资席位动向（章盟主、赵老哥、炒股养家等）",
        "龙虎榜出现机构专用席位大额买入时重点跟踪",
    ],

    risk_discipline=[
        "龙虎榜显示「一家独大」（单一席位买入>50%），放弃操作，避免主力砸盘",
        "涨停板封单量持续减少，且换手率>20%，立即止盈",
        "三日榜资金净流出，无条件止损",
        "机构席位连续3天净卖出，减仓至3成以下",
        "游资席位一日游特征明显（买入次日全部卖出），不追高接力",
    ],

    risk_level="high",
    tags=["龙虎榜", "游资", "机构资金", "涨停板", "席位分析"],
)


# ═══════════════════════════════════════════════════════
# 3. 作手逍遥风 — 资金情绪四阶段模型
# ═══════════════════════════════════════════════════════
XIAOYAOFENG_TACTIC = CapitalFlowTactic(
    name="资金情绪四阶段模型",
    code="CAPITAL_EMOTION_4PHASE",
    streamer_name="作手逍遥风",
    streamer_title="资金流+情绪周期融合派，央视特邀分析师",
    philosophy="资金流是情绪周期的量化体现，通过「资金情绪四阶段模型」精准把握市场节奏，实现「爆点低吸、加速重仓」的高效交易。",

    core_tactics=[
        _core_tactic(
            name="爆点低吸战法",
            interpretation=(
                "在主力资金建仓完毕、即将拉升的关键节点（爆点）进行低吸。"
                "通过识别低位横盘+缩量+资金持续流入的底部特征，"
                "在股价突破横盘平台且资金净流入放大3倍时确认爆点，"
                "待回踩平台上沿且资金承接有力时介入。"
            ),
            key_points=[
                "筛选：低位横盘（跌幅≥50%）+长期缩量（<5日均量30%）+资金小幅持续流入",
                "爆点：股价突破横盘平台+资金净流入放大3倍以上",
                "介入：爆点后回踩平台上沿，且资金承接有力时低吸",
            ],
        ),
        _core_tactic(
            name="趋势情绪资金法",
            interpretation=(
                "将市场划分为四个阶段（启动期、发酵期、加速期、退潮期），"
                "根据资金流入的节奏和强度匹配不同仓位。"
                "启动期资金试探性流入，轻仓试错；发酵期资金加速流入，加仓至5成；"
                "加速期资金爆发式流入，重仓至7-8成；退潮期资金持续流出，空仓观望。"
            ),
            key_points=[
                "启动期：资金试探性流入，轻仓试错",
                "发酵期：资金加速流入，加仓至5成",
                "加速期：资金爆发式流入，重仓至7-8成",
                "退潮期：资金持续流出，空仓观望",
            ],
        ),
        _core_tactic(
            name="太极缠丝做T法",
            interpretation=(
                "利用主力资金日内流入流出的节奏波动，通过高抛低吸降低持仓成本。"
                "核心在于识别资金流入时的低吸点和资金流出时的高抛点，"
                "通过日内波段操作锁定利润、降低风险。"
            ),
            key_points=[
                "利用资金流入流出节奏，高抛低吸降低成本",
                "资金净流入加速时加仓，净流出加速时减仓",
                "做T时需确保资金净流入>流出，避免逆势操作",
            ],
        ),
    ],

    operation_points=[
        "爆点低吸需满足「底部筹码峰未松动」+「资金流入持续3天以上」",
        "趋势情绪资金法需结合板块联动，优先选择主线题材",
        "做T时需确保资金净流入>流出，避免逆势操作",
        "加速期个股出现天量（是均量5倍以上）时减半仓",
        "退潮期即使个股基本面好也要减仓，尊重资金流信号",
    ],

    risk_discipline=[
        "爆点后股价跌破平台下沿3%，止损离场",
        "退潮期板块跌停≥5家，将仓位降至10%以下",
        "做T单次亏损≤3%，立即停止操作",
        "加速期到退潮期转换信号出现（龙头首阴、涨停炸板率>50%），次日清仓",
        "情绪周期与资金流向背离时，以资金流向为准",
    ],

    risk_level="medium",
    tags=["情绪周期", "爆点低吸", "做T", "资金管理", "仓位控制"],
)


# ═══════════════════════════════════════════════════════
# 4. 浪哥财经 — 资金流四步法
# ═══════════════════════════════════════════════════════
LANGGE_TACTIC = CapitalFlowTactic(
    name="资金流四步法",
    code="CAPITAL_4STEP_METHOD",
    streamer_name="浪哥财经",
    streamer_title="主力资金行为学专家",
    philosophy="看懂主力资金的「假动作」是盈利关键，通过「资金流四步法」识别主力建仓、洗盘、拉升、出货的完整轨迹，避免被割韭菜。",

    core_tactics=[
        _core_tactic(
            name="资金流四步法",
            interpretation=(
                "将主力资金操作划分为四个阶段：建仓→洗盘→拉升→出货。"
                "通过资金流向和股价行为的组合特征，识别每个阶段的信号。"
                "建仓期资金温和流入+股价重心上移；洗盘期资金小幅流出+股价回调但不破成本区；"
                "拉升期资金大幅流入+股价放量突破；出货期资金流出+股价滞涨。"
            ),
            key_points=[
                "建仓识别：低位横盘+资金温和流入+股价重心上移，为有效建仓",
                "洗盘识别：资金小幅流出+股价回调但不跌破建仓成本区，为强势洗盘",
                "拉升识别：资金大幅流入+股价放量突破+底部筹码锁定，为主升浪启动",
                "出货识别：资金流出+股价滞涨+底部筹码松动，为出货信号",
            ],
        ),
        _core_tactic(
            name="资金断层战法",
            interpretation=(
                "股价跳空高开+资金大幅流入+无套牢盘，形成资金断层形态。"
                "跳空缺口上方没有成交密集区，意味着拉升阻力极小；"
                "资金大幅流入表明主力抢筹意愿强烈。"
                "这是短线爆发力最强的形态之一。"
            ),
            key_points=[
                "股价跳空高开+资金大幅流入+无套牢盘，为短线爆发力最强形态",
                "跳空缺口>2%，资金净流入>前一日3倍",
                "上方无套牢盘（套牢盘<10%）+下方有强支撑",
            ],
        ),
        _core_tactic(
            name="资金背离逃顶法",
            interpretation=(
                "股价创新高但资金持续净流出，形成顶背离信号。"
                "这表明上涨缺乏资金支撑，是主力边拉边出的典型特征。"
                "顶背离一旦确认，往往是中期顶部的信号。"
            ),
            key_points=[
                "股价创新高但资金持续净流出，为顶背离，立即离场",
                "顶背离需连续3天确认，避免误判",
                "结合MACD顶背离和成交量萎缩综合判断",
            ],
        ),
    ],

    operation_points=[
        "建仓期需满足「70%成本集中度<10%」+「成交量有节奏放大」",
        "资金断层需满足「跳空缺口>2%」+「资金净流入>前一日3倍」",
        "顶背离需连续3天确认，避免误判",
        "洗盘期不操作，等待洗盘结束信号（缩量十字星+资金回流）",
        "拉升期持股不动，不因日内波动轻易离场",
    ],

    risk_discipline=[
        "建仓期股价跌破成本区3%，视为建仓失败，止损",
        "资金断层后回补缺口，且资金流出，立即离场",
        "顶背离确认后，全仓卖出，不贪恋最后一波涨幅",
        "出货期即使股价还在涨，也要分批减仓",
        "四步节奏被打乱（如洗盘变出货），立即重新评估",
    ],

    risk_level="medium",
    tags=["主力行为", "建仓洗盘拉升出货", "资金断层", "顶背离", "逃顶"],
)


# ═══════════════════════════════════════════════════════
# 5. 芝士财经 — 资金流量化指标体系
# ═══════════════════════════════════════════════════════
ZHISHI_TACTIC = CapitalFlowTactic(
    name="资金流量化指标体系",
    code="CAPITAL_QUANT_INDEX",
    streamer_name="芝士财经",
    streamer_title="资金流量化实战派",
    philosophy="资金流数据可量化、可验证，通过「资金流量化指标体系」构建客观交易模型，避免主观判断失误。",

    core_tactics=[
        _core_tactic(
            name="资金流量化选股模型",
            interpretation=(
                "将资金流数据转化为可量化的选股指标，通过设定明确的阈值条件筛选标的。"
                "模型综合考虑主力资金净流入率、北向资金持仓占比、机构资金持仓占比"
                "以及资金流与股价的相关性，确保选股标准的客观性和可执行性。"
            ),
            key_points=[
                "主力资金净流入率>5%（连续3天）",
                "北向资金持仓占比>2%且持续加仓",
                "机构资金持仓占比>10%",
                "资金流与股价正相关（相关系数>0.8）",
            ],
        ),
        _core_tactic(
            name="资金流强度评分法",
            interpretation=(
                "建立综合评分体系，对主力资金、北向资金、机构资金、成交量等指标进行加权评分。"
                "满分100分，≥80分买入，<60分卖出，60-80分持有观望。"
                "评分每日更新，动态调整仓位。"
            ),
            key_points=[
                "综合主力资金、北向资金、机构资金、成交量等指标，满分100分",
                "≥80分买入，<60分卖出",
                "资金流强度评分每日更新，动态调整仓位",
            ],
        ),
        _core_tactic(
            name="资金流背离量化法",
            interpretation=(
                "通过计算资金流与股价的背离度，量化顶背离和底背离信号。"
                "背离度>0.5视为强背离，是明确的卖出信号；"
                "背离度<-0.5视为强底背离，是潜在买入信号。"
            ),
            key_points=[
                "通过计算资金流与股价的背离度，当背离度>0.5时，视为强背离，卖出信号",
                "背离度计算需使用至少5天数据，避免短期波动影响",
                "结合成交量确认背离信号的有效性",
            ],
        ),
    ],

    operation_points=[
        "量化模型需满足所有条件，缺一不可",
        "资金流强度评分每日更新，动态调整仓位",
        "背离度计算需使用至少5天数据，避免短期波动影响",
        "评分在60-80分区间时，仓位控制在5成以内",
        "多指标共振时（评分>80+主力资金大幅流入），可满仓操作",
    ],

    risk_discipline=[
        "量化模型任一指标不满足，放弃操作",
        "资金流强度评分<60分，立即减仓至3成以下",
        "背离度>0.5，全仓卖出，不犹豫",
        "评分连续3天下降，即使仍>80分也减半仓",
        "量化信号与主观判断冲突时，以量化信号为准",
    ],

    risk_level="low",
    tags=["量化", "指标体系", "评分模型", "背离量化", "客观交易"],
)


# ═══════════════════════════════════════════════════════
# 6. 股海老司机 — 资金筹码共振战法
# ═══════════════════════════════════════════════════════
LAOSIJI_TACTIC = CapitalFlowTactic(
    name="资金筹码共振战法",
    code="CAPITAL_CHIP_RESONANCE",
    streamer_name="股海老司机",
    streamer_title="资金流+筹码峰双剑合璧派",
    philosophy="资金流决定方向，筹码峰决定空间，两者结合可实现「精准买点+可观收益」的双重目标。",

    core_tactics=[
        _core_tactic(
            name="资金筹码共振战法",
            interpretation=(
                "将资金流向与筹码分布结合分析，资金流确认方向，筹码峰确认空间。"
                "底部筹码峰密集+资金持续流入=建仓信号；"
                "底部筹码峰锁定+资金加速流入=拉升信号；"
                "底部筹码峰松动+资金流出=出货信号。"
                "两者共振时信号最可靠。"
            ),
            key_points=[
                "底部筹码峰密集+资金持续流入→建仓信号",
                "底部筹码峰锁定+资金加速流入→拉升信号",
                "底部筹码峰松动+资金流出→出货信号",
            ],
        ),
        _core_tactic(
            name="资金筹码断层战法",
            interpretation=(
                "股价突破筹码真空区（上方无套牢盘区域）时，资金大幅流入。"
                "筹码真空区意味着拉升阻力极小，配合资金大幅流入，"
                "形成爆发力极强的短线起爆点。"
            ),
            key_points=[
                "股价突破筹码真空区+资金大幅流入，为短线起爆点",
                "上方无套牢盘（套牢盘<10%）+下方有强支撑",
                "突破时成交量是5日均量2倍以上",
            ],
        ),
        _core_tactic(
            name="资金筹码背离战法",
            interpretation=(
                "底部筹码峰松动但资金仍流入，形成顶背离信号。"
                "这表明主力在利用资金流入的表象吸引跟风盘，"
                "实际上底部筹码已经开始出货，是危险的诱多信号。"
            ),
            key_points=[
                "底部筹码峰松动但资金仍流入，为诱多信号，立即离场",
                "结合换手率异常放大（>20%）确认诱多",
                "顶部筹码峰增加+资金流入减少=双重顶背离",
            ],
        ),
    ],

    operation_points=[
        "底部筹码峰需厚实、紧凑，代表主力底仓稳固",
        "资金流入需配合筹码峰上移，为有效上涨",
        "资金筹码断层需满足「上方无套牢盘（套牢盘<10%）」+「下方有强支撑」",
        "拉升期筹码峰在低位锁定不动，是持股的最佳信号",
        "高位出现新筹码峰+资金开始流出，准备减仓",
    ],

    risk_discipline=[
        "底部筹码峰松动，立即减仓",
        "资金流入但筹码峰下移，视为「死筹码」，放弃操作",
        "股价跌破筹码峰下沿3%，无条件止损",
        "高位筹码峰占比>30%且资金流出，清仓",
        "筹码分布与资金流向严重背离时，以筹码分布为准",
    ],

    risk_level="medium",
    tags=["筹码峰", "资金流", "共振", "断层", "背离"],
)


# ──────────────────────────────────────────────────────────
# 资金流战法总库
# ──────────────────────────────────────────────────────────

ALL_CAPITAL_FLOW_TACTICS: List[CapitalFlowTactic] = [
    CAIJINBEIER_TACTIC,     # 1. 财金贝儿 — 三维资金共振法
    ABAOLOONG_TACTIC,       # 2. 阿宝龙哥 — 龙虎榜资金流战法体系
    XIAOYAOFENG_TACTIC,     # 3. 作手逍遥风 — 资金情绪四阶段模型
    LANGGE_TACTIC,          # 4. 浪哥财经 — 资金流四步法
    ZHISHI_TACTIC,          # 5. 芝士财经 — 资金流量化指标体系
    LAOSIJI_TACTIC,         # 6. 股海老司机 — 资金筹码共振战法
]

# 按风险等级分类
CAPITAL_FLOW_BY_RISK: Dict[str, List[CapitalFlowTactic]] = {
    "low":    [t for t in ALL_CAPITAL_FLOW_TACTICS if t.risk_level == "low"],
    "medium": [t for t in ALL_CAPITAL_FLOW_TACTICS if t.risk_level == "medium"],
    "high":   [t for t in ALL_CAPITAL_FLOW_TACTICS if t.risk_level == "high"],
    "extreme":[t for t in ALL_CAPITAL_FLOW_TACTICS if t.risk_level == "extreme"],
}

# 按主播名称索引
CAPITAL_FLOW_BY_STREAMER: Dict[str, CapitalFlowTactic] = {
    t.streamer_name: t for t in ALL_CAPITAL_FLOW_TACTICS
}

# 按标签分类
CAPITAL_FLOW_BY_TAG: Dict[str, List[CapitalFlowTactic]] = {}
for t in ALL_CAPITAL_FLOW_TACTICS:
    for tag in t.tags:
        if tag not in CAPITAL_FLOW_BY_TAG:
            CAPITAL_FLOW_BY_TAG[tag] = []
        CAPITAL_FLOW_BY_TAG[tag].append(t)


def get_capital_flow_tactic_by_code(code: str) -> Optional[CapitalFlowTactic]:
    """通过编码查找资金流战法

    Args:
        code: 战法编码（如 "CAPITAL_3D_RESONANCE"）

    Returns:
        匹配的战法，未找到返回None
    """
    for tactic in ALL_CAPITAL_FLOW_TACTICS:
        if tactic.code == code:
            return tactic
    return None


def get_capital_flow_tactic_by_name(name: str) -> Optional[CapitalFlowTactic]:
    """通过战法名称查找资金流战法

    Args:
        name: 战法名称（如 "三维资金共振法"）

    Returns:
        匹配的战法，未找到返回None
    """
    for tactic in ALL_CAPITAL_FLOW_TACTICS:
        if tactic.name == name:
            return tactic
    return None


def get_capital_flow_summary_stats() -> Dict[str, Any]:
    """获取资金流战法统计摘要"""
    return {
        "total_count": len(ALL_CAPITAL_FLOW_TACTICS),
        "risk_distribution": {
            "low": len(CAPITAL_FLOW_BY_RISK.get("low", [])),
            "medium": len(CAPITAL_FLOW_BY_RISK.get("medium", [])),
            "high": len(CAPITAL_FLOW_BY_RISK.get("high", [])),
            "extreme": len(CAPITAL_FLOW_BY_RISK.get("extreme", [])),
        },
        "streamer_list": [t.streamer_name for t in ALL_CAPITAL_FLOW_TACTICS],
        "all_tags": sorted(set(
            tag for t in ALL_CAPITAL_FLOW_TACTICS for tag in t.tags
        )),
        "category": "资金流",
    }


def capital_flow_tactic_to_dict(tactic: CapitalFlowTactic) -> Dict[str, Any]:
    """将资金流战法转换为字典"""
    return {
        "name": tactic.name,
        "code": tactic.code,
        "streamer_name": tactic.streamer_name,
        "streamer_title": tactic.streamer_title,
        "philosophy": tactic.philosophy,
        "core_tactics": tactic.core_tactics,
        "operation_points": tactic.operation_points,
        "risk_discipline": tactic.risk_discipline,
        "category": tactic.category,
        "risk_level": tactic.risk_level,
        "tags": tactic.tags,
    }
