"""游资数字指纹库 — 8大顶级游资完整数字画像

每位游资包含5大维度:
    - 交易哲学: 核心投资理念
    - 选股标准: 标的筛选条件(量化可计算)
    - 买入时机: 入场信号与条件
    - 风控铁律: 风险控制规则
    - 经典战法: 标志性交易策略

每位游资的指纹数据包含雷达图5维评分(0-100):
    - 情绪敏感度: 对市场情绪的感知与利用能力
    - 执行力: 买卖决策的果断程度
    - 选股能力: 挖掘龙头标的的准确度
    - 风控水平: 风险控制与回撤管理能力
    - 盈利稳定性: 收益的稳定性与可持续性
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class YingYouFingerprint:
    """游资数字指纹 — 完整画像"""
    name: str                               # 游资名称
    nickname: str                           # 江湖称号
    philosophy: str                         # 交易哲学(一句话)
    philosophy_detail: str                  # 交易哲学(详细)
    stock_selection: Dict                   # 选股标准
    entry_timing: Dict                      # 买入时机
    risk_control: Dict                      # 风控铁律
    classic_tactics: List[Dict]             # 经典战法列表
    radar_scores: Dict[str, float]          # 雷达图5维评分
    position_strategy: Dict                 # 仓位策略
    applicable_cycles: List[str]            # 适用情绪周期
    position_limit: int                     # 最大仓位(%)
    single_position_limit: int              # 单笔仓位上限(%)
    stop_loss_rule: str                     # 止损规则
    take_profit_rule: str                   # 止盈规则
    key_indicators: List[str]               # 关注核心指标
    behavioral_tags: List[str]              # 行为标签
    quote: str                              # 经典语录


# ═══════════════════════════════════════════════════════════
# 1. 炒股养家 — 情绪周期大师
# ═══════════════════════════════════════════════════════════

def _chao_gu_yang_jia() -> YingYouFingerprint:
    """炒股养家 — 情绪周期定仓位宗师"""
    return YingYouFingerprint(
        name="炒股养家",
        nickname="情绪周期宗师",
        philosophy="情绪周期定仓位，主流题材定方向",
        philosophy_detail=(
            "养家老师是A股情绪周期理论的奠基人，核心在于'情绪周期定仓位'。"
            "他将市场情绪的演化划分为冰点→修复→高潮→退潮的完整周期，"
            "在不同情绪阶段匹配不同仓位。核心认知: 市场情绪是有周期的，"
            "超短本质是情绪博弈，要在别人贪婪时恐惧，在别人恐惧时贪婪。"
            "买在分歧(情绪冰点/分歧日)，卖在一致(情绪高潮日)。"
        ),
        stock_selection={
            "market_position": "主流题材龙头，市场人气核心标的",
            "market_cap": "流通市值30-150亿，兼顾流动性与弹性",
            "turnover_rate": "5-25%，过于缩量说明无关注，过于放量可能出货",
            "consecutive_boards": "2板以上确认龙头地位，首板需题材催化",
            "theme_strength": "必须是当日最强题材的前排标的",
            "fund_flow": "主力资金净流入为正，大单占比>30%",
            "sentiment": "市场情绪处于冰点或修复期",
            "avoid": ["冷门题材", "庄股", "无板块效应的独立股", "连续缩量阴跌"],
        },
        entry_timing={
            "primary": "情绪冰点日，市场恐慌后的首次分歧",
            "secondary": "题材发酵初期，首板确认日",
            "tertiary": "龙头首次分歧(首阴)，次日竞价弱转强",
            "signals": [
                "涨停家数<30家(情绪冰点)",
                "跌停家数>20家(极度恐慌，反而孕育机会)",
                "炸板率>50%后次日回落",
                "市场最高标断板后次日竞价弱转强",
                "题材发酵首日，板块涨停>5家",
            ],
            "entry_method": "竞价介入或分歧低吸，不打缩量一致板",
            "time_preference": "早盘竞价或尾盘30分钟",
        },
        risk_control={
            "max_position": "情绪高潮期降至3成以下，冰点半仓以上",
            "single_limit": "单标的不超过总仓位30%",
            "stop_loss": "买入次日低开-3%且10:30前未翻红则止损",
            "take_profit": "连板持有，断板即走；高潮日减仓",
            "empty_condition": "连续3天炸板率>60%或涨停<15家空仓",
            "drawdown_control": "单月回撤不超过8%",
            "key_rule": "永远不在情绪高潮日开仓，永远不在情绪冰点日清仓",
        },
        classic_tactics=[
            {
                "name": "龙头首阴",
                "description": "市场龙头首次断板(首阴)次日，竞价出现弱转强信号时介入",
                "conditions": ["市场公认龙头", "首次断板", "次日竞价高开或平开后快速拉升"],
                "success_rate": "65-70%",
                "risk_reward": "1:3",
            },
            {
                "name": "情绪冰点抄底",
                "description": "市场情绪极度恐慌(涨停<20家，跌停>30家)时，低吸核心标的",
                "conditions": ["涨停家数<20", "跌停>30家", "炸板率>60%", "选择前期强势标的"],
                "success_rate": "60-65%",
                "risk_reward": "1:2.5",
            },
            {
                "name": "买在分歧",
                "description": "题材发酵初期，板块内部分标的出现分歧时，介入最强势标的",
                "conditions": ["题材首日发酵", "板块涨停>=5家", "选择最先涨停或回封标的"],
                "success_rate": "70%+",
                "risk_reward": "1:2",
            },
        ],
        radar_scores={
            "情绪敏感度": 98.0,
            "执行力": 90.0,
            "选股能力": 92.0,
            "风控水平": 95.0,
            "盈利稳定性": 88.0,
        },
        position_strategy={
            "冰点期": "60-80%",
            "修复期": "50-70%",
            "高潮期": "10-30%",
            "退潮期": "0-20%",
        },
        applicable_cycles=["情绪冰点", "情绪修复", "首次分歧"],
        position_limit=80,
        single_position_limit=30,
        stop_loss_rule="次日低开-3%且10:30前未翻红止损",
        take_profit_rule="断板即走，高潮日减仓",
        key_indicators=["涨停家数", "跌停家数", "炸板率", "连板高度", "量能变化"],
        behavioral_tags=["情绪周期", "买在分歧", "龙头首阴", "仓位管理大师"],
        quote="别人贪婪我恐惧，别人恐惧我贪婪。情绪周期才是超短的灵魂。",
    )


# ═══════════════════════════════════════════════════════════
# 2. 退学炒股 — 空仓祖师爷
# ═══════════════════════════════════════════════════════════

def _tui_xue_chao_gu() -> YingYouFingerprint:
    """退学炒股 — 空仓即是战胜市场的开始"""
    return YingYouFingerprint(
        name="退学炒股",
        nickname="空仓祖师爷",
        philosophy="空仓即是战胜市场的开始，看不懂时不做就是最好的做",
        philosophy_detail=(
            "退学炒股是游资界的'纪律之王'，其核心哲学是'空仓'。"
            "他认为超短交易中，防守远比进攻重要。在弱势市场中，"
            "空仓就是最大的进攻。其核心逻辑: 只在确定性的机会出手，"
            "没有确定性就空仓等待。擅长在市场恐慌杀跌后寻找超跌+题材"
            "共振的机会，单笔仓位严格控制在5%以内，通过高胜率累计收益。"
        ),
        stock_selection={
            "market_position": "超跌反弹标的，恐慌错杀股",
            "market_cap": "流通市值20-100亿",
            "decline_range": "短期跌幅20-40%，严重偏离均线",
            "theme_resonance": "必须叠加热点题材，纯超跌不做",
            "volume_shrink": "缩量下跌后出现放量阳线",
            "support_level": "重要均线支撑或前低支撑",
            "sentiment": "市场恐慌后，情绪开始企稳",
            "avoid": ["无量阴跌", "无题材叠加", "业绩暴雷股", "高位补跌股"],
        },
        entry_timing={
            "primary": "恐慌杀跌后的企稳信号日",
            "secondary": "超跌标的出现首根放量阳线",
            "tertiary": "题材与超跌形成共振的启动点",
            "signals": [
                "跌停家数从峰值减少50%以上",
                "标的短期跌幅>30%",
                "出现长下影线或缩量十字星",
                "次日大盘高开或平开",
                "板块出现首板标的",
            ],
            "entry_method": "低吸为主，不追高，分2笔建仓",
            "time_preference": "早盘竞价低开时或尾盘30分钟",
        },
        risk_control={
            "max_position": "30-50%",
            "single_limit": "单笔不超过总仓位5%",
            "stop_loss": "跌破前低点或-5%严格止损",
            "take_profit": "反弹10-15%止盈，不幻想反转",
            "empty_condition": "连续5日无法选出符合条件的标的则空仓",
            "drawdown_control": "单月回撤不超过5%",
            "key_rule": "看不懂就空仓，没有确定性就不做",
        },
        classic_tactics=[
            {
                "name": "超跌题材共振",
                "description": "标的短期大幅超跌(>30%)叠加热点题材催化，在企稳日低吸",
                "conditions": ["短期跌幅>30%", "叠加当前热点题材", "出现缩量十字星或长下影"],
                "success_rate": "65%",
                "risk_reward": "1:2",
            },
            {
                "name": "恐慌后低吸",
                "description": "市场恐慌日(跌停>50家)次日，低吸被错杀的前期强势标的",
                "conditions": ["前日跌停>50家", "次日跌停家数减半", "选择前期辨识度标的"],
                "success_rate": "60-68%",
                "risk_reward": "1:2.5",
            },
            {
                "name": "均线反弹",
                "description": "严重偏离均线后的技术性反弹，叠加题材更好",
                "conditions": ["股价偏离20日均线>20%", "出现止跌K线", "有题材催化"],
                "success_rate": "58-63%",
                "risk_reward": "1:1.8",
            },
        ],
        radar_scores={
            "情绪敏感度": 85.0,
            "执行力": 98.0,
            "选股能力": 82.0,
            "风控水平": 99.0,
            "盈利稳定性": 92.0,
        },
        position_strategy={
            "冰点期": "20-40%",
            "修复期": "40-60%",
            "高潮期": "0-10%",
            "退潮期": "0%",
        },
        applicable_cycles=["情绪冰点", "恐慌后的修复期"],
        position_limit=50,
        single_position_limit=5,
        stop_loss_rule="跌破前低或-5%严格止损",
        take_profit_rule="反弹10-15%分批止盈",
        key_indicators=["跌停家数变化", "超跌幅度", "缩量程度", "题材热度"],
        behavioral_tags=["空仓大师", "超跌反弹", "纪律如铁", "单笔轻仓"],
        quote="空仓即是战胜市场的开始，看不懂的时候不做就是最好的做。",
    )


# ═══════════════════════════════════════════════════════════
# 3. 涅槃重生 — 次新股之王
# ═══════════════════════════════════════════════════════════

def _nie_pan_chong_sheng() -> YingYouFingerprint:
    """涅槃重生 — 次新+题材双驱动，竞价收割机"""
    return YingYouFingerprint(
        name="涅槃重生",
        nickname="次新股之王",
        philosophy="次日竞价割不犹豫，次新+题材双轮驱动",
        philosophy_detail=(
            "涅槃重生是游资界的'次新股专家'，以'次日竞价割'的果决著称。"
            "他的核心模式是次新股+热点的双轮驱动。次新股由于筹码干净、"
            "无历史套牢盘，在题材催化下容易出现连续涨停。他偏好高换手"
            "标的(15-30%)，认为换手代表市场关注度与筹码交换的充分性。"
            "次日竞价即决定走留，绝不拖泥带水。"
        ),
        stock_selection={
            "market_position": "次新股+热点题材的双驱动标的",
            "listing_time": "上市3个月以内的新股",
            "market_cap": "流通市值10-60亿，小流通盘优先",
            "turnover_rate": "15-30%，高换手代表活跃",
            "price_range": "股价20-80元，低价次新优先",
            "theme_overlap": "必须与当前热点题材重叠",
            "volume_feature": "上市首日换手>50%，随后持续放量",
            "avoid": ["老次新(上市>6个月)", "无题材次新", "换手率<10%", "一字板无换手"],
        },
        entry_timing={
            "primary": "次新股首次开板后回踩，出现反包信号",
            "secondary": "次新股涨停炸板后，回封时介入",
            "tertiary": "题材爆发时，选择叠加题材的次新股",
            "signals": [
                "次新股上市<3个月",
                "首次开板后换手>20%",
                "出现首根阳线反包",
                "题材发酵首日",
                "竞价高开2-5%",
            ],
            "entry_method": "回封板或低吸，次日竞价决定去留",
            "time_preference": "炸板回封时或早盘竞价",
        },
        risk_control={
            "max_position": "40-60%",
            "single_limit": "单笔不超过总仓位20%",
            "stop_loss": "次日竞价低开>2%直接割肉",
            "take_profit": "次日竞价高开>3%则持有看板，不连板就走",
            "empty_condition": "无新开板次新或题材退潮时空仓",
            "drawdown_control": "单次亏损不超过-5%",
            "key_rule": "次日竞价不翻红就割，绝不幻想",
        },
        classic_tactics=[
            {
                "name": "次新首板反包",
                "description": "次新股开板后首根涨停反包，代表新资金入场",
                "conditions": ["上市<3个月", "开板后调整<5日", "首根涨停", "换手>15%"],
                "success_rate": "68-72%",
                "risk_reward": "1:2",
            },
            {
                "name": "次新+题材共振",
                "description": "热点题材爆发时，选择叠加该题材的次新股",
                "conditions": ["题材涨停>5家", "次新股市值<50亿", "换手>15%"],
                "success_rate": "70%+",
                "risk_reward": "1:2.5",
            },
            {
                "name": "高换手接力",
                "description": "次新股连续高换手(>20%)后的接力机会",
                "conditions": ["连续3日换手>20%", "股价沿5日线上行", "题材持续"],
                "success_rate": "60-65%",
                "risk_reward": "1:1.8",
            },
        ],
        radar_scores={
            "情绪敏感度": 88.0,
            "执行力": 96.0,
            "选股能力": 90.0,
            "风控水平": 92.0,
            "盈利稳定性": 85.0,
        },
        position_strategy={
            "冰点期": "10-20%",
            "修复期": "40-60%",
            "高潮期": "30-50%",
            "退潮期": "0-10%",
        },
        applicable_cycles=["情绪修复", "情绪高潮", "次新行情周期"],
        position_limit=60,
        single_position_limit=20,
        stop_loss_rule="次日竞价低开>2%直接割",
        take_profit_rule="次日不连板必走",
        key_indicators=["换手率", "开板天数", "题材热度", "竞价强度"],
        behavioral_tags=[["次新股", "高换手", "竞价割", "果决执行"]],
        quote="次日竞价不翻红就割，犹豫是亏损的源泉。次新股是情绪的放大器。",
    )


# ═══════════════════════════════════════════════════════════
# 4. 92科比 — 计划交易大师
# ═══════════════════════════════════════════════════════════

def _92_ke_bi() -> YingYouFingerprint:
    """92科比 — 计划你的交易，交易你的计划"""
    return YingYouFingerprint(
        name="92科比",
        nickname="计划交易大师",
        philosophy="计划你的交易，交易你的计划。强势股回调10-15%是黄金买点",
        philosophy_detail=(
            "92科比以'计划交易'闻名游资界。他每晚复盘后制定第二天的详细交易计划，"
            "第二天严格按计划执行，不被盘中波动干扰。核心模式是强势股回调10-15%后的"
            "缩量低吸，认为强势股首次深度回调是资金洗盘的信号。极致缩量(<前日30%)"
            "代表抛压穷尽，是最佳低吸时机。分仓不超过3成，单笔风险可控。"
        ),
        stock_selection={
            "market_position": "近期强势股(前期有连板)，回调后的低吸机会",
            "market_cap": "流通市值30-120亿",
            "decline_range": "从近期高点回调10-15%，最佳区间",
            "volume_feature": "缩量至极致(低于前5日均量30%)",
            "support_level": "10日线/20日线支撑位",
            "theme": "必须是近期热点题材的前排标的",
            "historical_strength": "前期至少有2连板，辨识度足够",
            "avoid": ["弱市无题材个股", "下跌放量(非缩量)", "跌破重要均线无支撑", "无前期涨停基因"],
        },
        entry_timing={
            "primary": "强势股回调10-15%后出现缩量十字星/小阳线",
            "secondary": "标的回踩10日线或20日线企稳",
            "tertiary": "题材回流时，前期龙头回调后的反包",
            "signals": [
                "前期强势股(>=2连板)",
                "回调幅度10-15%",
                "成交量缩至前期30%以下",
                "出现止跌K线(十字星/小阳线)",
                "10日线或20日线附近有支撑",
            ],
            "entry_method": "低吸为主，分2笔建仓(第一笔3成，确认后加2成)",
            "time_preference": "早盘低开时或尾盘30分钟",
        },
        risk_control={
            "max_position": "50-60%",
            "single_limit": "单笔不超过总仓位30%，分<=3成",
            "stop_loss": "跌破支撑位或-5%止损",
            "take_profit": "反弹10%减半，反弹15%清仓",
            "empty_condition": "无符合条件的回调强势股则空仓",
            "drawdown_control": "单笔最大亏损-5%",
            "key_rule": "只做计划内的交易，盘中不临时起意",
        },
        classic_tactics=[
            {
                "name": "缩量极致低吸",
                "description": "强势股回调10-15%，成交量缩至极致时低吸",
                "conditions": ["回调10-15%", "量能<前期30%", "出现止跌信号", "有题材支撑"],
                "success_rate": "68-73%",
                "risk_reward": "1:2.5",
            },
            {
                "name": "均线支撑反弹",
                "description": "强势股回踩10日/20日均线获得支撑后的反弹",
                "conditions": ["回踩10日或20日线", "均线附近出现小阳线", "缩量", "题材未退潮"],
                "success_rate": "65-70%",
                "risk_reward": "1:2",
            },
            {
                "name": "龙头二次启动",
                "description": "前期龙头回调后，题材回流时的二次启动",
                "conditions": ["前期龙头", "回调10%+", "题材回流信号", "首根阳线启动"],
                "success_rate": "62-68%",
                "risk_reward": "1:2.2",
            },
        ],
        radar_scores={
            "情绪敏感度": 82.0,
            "执行力": 94.0,
            "选股能力": 88.0,
            "风控水平": 93.0,
            "盈利稳定性": 90.0,
        },
        position_strategy={
            "冰点期": "20-30%",
            "修复期": "50-70%",
            "高潮期": "30-40%",
            "退潮期": "0-20%",
        },
        applicable_cycles=["情绪修复", "情绪高潮初期", "题材回流期"],
        position_limit=60,
        single_position_limit=30,
        stop_loss_rule="跌破支撑位或-5%止损",
        take_profit_rule="反弹10%减半，15%清仓",
        key_indicators=[["回调幅度", "缩量程度", "均线支撑", "题材持续性"]],
        behavioral_tags=[["计划交易", "回调低吸", "缩量极致", "分仓控险"]],
        quote="计划你的交易，交易你的计划。没有计划就不开盘。",
    )


# ═══════════════════════════════════════════════════════════
# 5. 小鳄鱼 — 打板效率之王
# ═══════════════════════════════════════════════════════════

def _xiao_e_yu() -> YingYouFingerprint:
    """小鳄鱼 — 打板最有效率，总龙核心信仰者"""
    return YingYouFingerprint(
        name="小鳄鱼",
        nickname="打板效率之王",
        philosophy="打板是最有效率的交易方式，只做总龙头和主线核心",
        philosophy_detail=(
            "小鳄鱼是游资界的'打板王'，坚信打板是最有效率的超短模式。"
            "他只做两类标的: 市场总龙头和主线核心标的。核心逻辑是: "
            "只有涨停板的强度才能证明一个标的的真正价值。"
            "10:30之前的硬板(非尾盘偷鸡)才有质量，代表资金的真实意图。"
            "次日不连板必走，绝不锁仓幻想。"
        ),
        stock_selection={
            "market_position": "市场总龙头或主线核心标的",
            "market_cap": "流通市值30-200亿",
            "board_type": "必须是硬板(10:30前涨停)，非尾盘板",
            "theme": "当前最强主线题材",
            "linkage": "板块效应明显，跟风标的>=3只",
            "volume": "涨停板有充分换手(非一字无量板)",
            "board_level": "2板以上，确认龙头地位",
            "avoid": ["尾盘偷鸡板", "独立涨停无板块", "一字无量板", "弱市硬做"],
        },
        entry_timing={
            "primary": "打板，涨停板确认时介入",
            "secondary": "首板确认题材发酵时打板",
            "tertiary": "龙头分歧转一致时打板",
            "signals": [
                "10:30前冲击涨停",
                "换手充分(>5%)",
                "板块有>=3只跟风涨停",
                "是市场最高标或题材龙头",
                "封单坚决，无反复开板",
            ],
            "entry_method": "打板买入，不低吸不半路",
            "time_preference": "10:30前",
        },
        risk_control={
            "max_position": "50-70%",
            "single_limit": "单笔不超过总仓位35%",
            "stop_loss": "次日不连板开盘就走",
            "take_profit": "连板持有，断板即走",
            "empty_condition": "10:30前无硬板可打则空仓",
            "drawdown_control": "连续2次打板失败则降仓至3成",
            "key_rule": "次日不连板必走，不锁仓不幻想",
        },
        classic_tactics=[
            {
                "name": "总龙打板",
                "description": "市场总龙头涨停时打板介入",
                "conditions": ["市场最高连板", "10:30前涨停", "硬板", "板块跟风"],
                "success_rate": "70-75%",
                "risk_reward": "1:3",
            },
            {
                "name": "主线核心首板",
                "description": "主线题材发酵首日，核心标的首次涨停时打板",
                "conditions": ["题材首日发酵", "板块涨停>5家", "最先涨停的前排标的"],
                "success_rate": "68-72%",
                "risk_reward": "1:2",
            },
            {
                "name": "分歧转一致板",
                "description": "龙头炸板后回封，代表资金意见一致",
                "conditions": ["龙头炸板", "回封坚决", "换手持筹", "题材持续"],
                "success_rate": "65-70%",
                "risk_reward": "1:2.5",
            },
        ],
        radar_scores={
            "情绪敏感度": 90.0,
            "执行力": 95.0,
            "选股能力": 92.0,
            "风控水平": 88.0,
            "盈利稳定性": 82.0,
        },
        position_strategy={
            "冰点期": "0-10%",
            "修复期": "50-70%",
            "高潮期": "70-80%",
            "退潮期": "0%",
        },
        applicable_cycles=["情绪修复", "情绪高潮"],
        position_limit=80,
        single_position_limit=35,
        stop_loss_rule="次日不连板开盘就走",
        take_profit_rule="连板持有，断板即走",
        key_indicators=["涨停时间", "换手程度", "板块跟风", "连板高度"],
        behavioral_tags=[["打板", "总龙头", "硬板", "次日必走"]],
        quote="打板是最有效率的。只做总龙头，10:30前的硬板，次日不连板必走。",
    )


# ═══════════════════════════════════════════════════════════
# 6. 龙飞虎 — 机构游资共振猎手
# ═══════════════════════════════════════════════════════════

def _long_fei_hu() -> YingYouFingerprint:
    """龙飞虎 — 题材+业绩双驱动，机构游资共振"""
    return YingYouFingerprint(
        name="龙飞虎",
        nickname="机构游资共振猎手",
        philosophy="题材+业绩双驱动，机构游资共振时介入",
        philosophy_detail=(
            "龙飞虎是游资界少有的'基本面+技术面'双料高手。"
            "他不纯粹做情绪博弈，而是寻找题材催化+业绩支撑的双重驱动标的。"
            "当机构资金(基本面)与游资资金(情绪面)形成共振时，"
            "标的上涨的确定性最高、持续性最强。他偏好趋势加速初期的标的，"
            "在趋势刚刚加速时介入，享受主升浪。"
        ),
        stock_selection={
            "market_position": "题材+业绩双驱动的趋势加速标的",
            "market_cap": "流通市值50-300亿",
            "fundamental": "业绩同比增长>30%，或业绩拐点确认",
            "theme": "有明确题材催化，非纯价值股",
            "fund_resonance": "机构持仓增加+游资活跃度提升",
            "trend_stage": "趋势加速初期，刚刚突破平台",
            "volume": "放量突破(成交量>5日均量2倍)",
            "avoid": ["纯概念股无业绩", "趋势末端高位股", "机构持续减仓", "无题材催化"],
        },
        entry_timing={
            "primary": "趋势加速初期，放量突破平台时",
            "secondary": "机构调研密集+游资介入共振",
            "tertiary": "业绩公告超预期+题材催化",
            "signals": [
                "放量突破震荡平台",
                "业绩同比大幅增长",
                "机构席位出现在龙虎榜",
                "题材催化刚启动",
                "股价沿5日线上行",
            ],
            "entry_method": "突破买入或回踩5日线低吸",
            "time_preference": "突破确认时或尾盘",
        },
        risk_control={
            "max_position": "50-70%",
            "single_limit": "单笔不超过总仓位25%",
            "stop_loss": "跌破20日线或-8%止损",
            "take_profit": "趋势走坏或出现放量长阴则离场",
            "empty_condition": "无业绩+题材双驱动标的则空仓",
            "drawdown_control": "单月回撤不超过10%",
            "key_rule": "趋势为王，跌破趋势就走",
        },
        classic_tactics=[
            {
                "name": "趋势加速突破",
                "description": "趋势股放量突破震荡平台，进入加速阶段",
                "conditions": ["横盘整理>10日", "放量突破", "业绩支撑", "题材催化"],
                "success_rate": "72-76%",
                "risk_reward": "1:3",
            },
            {
                "name": "机构游资共振",
                "description": "龙虎榜同时出现机构席位与游资席位买入",
                "conditions": ["龙虎榜机构买入", "游资席位买入", "题材催化", "趋势良好"],
                "success_rate": "70%+",
                "risk_reward": "1:2.5",
            },
            {
                "name": "业绩超预期启动",
                "description": "业绩公告大幅超预期，叠加题材催化启动",
                "conditions": ["业绩同比增长>50%", "超预期", "题材催化", "首板启动"],
                "success_rate": "68-72%",
                "risk_reward": "1:2",
            },
        ],
        radar_scores={
            "情绪敏感度": 85.0,
            "执行力": 88.0,
            "选股能力": 95.0,
            "风控水平": 88.0,
            "盈利稳定性": 92.0,
        },
        position_strategy={
            "冰点期": "30-40%",
            "修复期": "50-70%",
            "高潮期": "60-80%",
            "退潮期": "30-40%",
        },
        applicable_cycles=["情绪修复", "情绪高潮", "趋势行情"],
        position_limit=80,
        single_position_limit=25,
        stop_loss_rule="跌破20日线或-8%止损",
        take_profit_rule="趋势走坏即走",
        key_indicators=[["业绩增速", "机构动向", "趋势强度", "成交量变化"]],
        behavioral_tags=[["趋势加速", "机构游资共振", "业绩驱动", "基本面选股"]],
        quote="题材是催化剂，业绩是压舱石。机构游资共振时，主升最确定。",
    )


# ═══════════════════════════════════════════════════════════
# 7. 职业炒手 — 超强势股信仰者
# ═══════════════════════════════════════════════════════════

def _zhi_ye_chao_shou() -> YingYouFingerprint:
    """职业炒手 — 只做超强势股，连板高度第一"""
    return YingYouFingerprint(
        name="职业炒手",
        nickname="超强势股市猎手",
        philosophy="只做超强势股，连板高度是第一优先级，弱市空仓休息",
        philosophy_detail=(
            "职业炒手是超短线'纯粹派'代表，只做超强势股，"
            "以连板高度作为选股的第一优先级。他认为超短的本质就是"
            "做最强，只有市场最强势的股票才值得交易。弱市行情下"
            "坚决空仓，不参与任何弱势反弹。他对'超强势股'的定义是: "
            "市场连板高度最高的标的，或当日最强板块的最强标的。"
        ),
        stock_selection={
            "market_position": "市场最高连板标的或最强板块龙头",
            "market_cap": "流通市值20-150亿",
            "consecutive_boards": "市场最高连板或同身位最强标的",
            "strength_ranking": "市场强度排名前10",
            "theme": "必须是当日最强题材",
            "linkage": "板块内跟风标的>=3只涨停",
            "board_quality": "硬板为主，换手充分",
            "avoid": ["跟风股", "补涨股", "弱市杂毛", "趋势慢牛股"],
        },
        entry_timing={
            "primary": "市场最高标确认时介入",
            "secondary": "最强题材发酵时介入前排标的",
            "tertiary": "高位分歧转一致时",
            "signals": [
                "市场最高连板标的",
                "最强题材龙头",
                "硬板涨停",
                "板块跟风强劲",
                "市场情绪处于修复或高潮期",
            ],
            "entry_method": "打板或竞价介入",
            "time_preference": "早盘竞价或涨停瞬间",
        },
        risk_control={
            "max_position": "50-80%",
            "single_limit": "单笔不超过总仓位40%",
            "stop_loss": "次日低开-3%或断板即走",
            "take_profit": "连板持有，断板清仓",
            "empty_condition": "弱市(涨停<30家)空仓",
            "drawdown_control": "连续3笔亏损则强制空仓3天",
            "key_rule": "弱市不做，只做最强",
        },
        classic_tactics=[
            {
                "name": "最高标接力",
                "description": "接力市场最高连板标的",
                "conditions": ["市场最高连板", "硬板", "题材持续", "情绪良好"],
                "success_rate": "65-70%",
                "risk_reward": "1:3",
            },
            {
                "name": "最强题材龙头",
                "description": "只做当日最强题材的最强标的",
                "conditions": ["题材强度第1", "板块涨停>5家", "标的为板块最先涨停"],
                "success_rate": "70-75%",
                "risk_reward": "1:2.5",
            },
            {
                "name": "弱市空仓",
                "description": "弱市行情下坚决空仓不参与",
                "conditions": ["涨停<30家", "跌停>10家", "炸板率>50%"],
                "success_rate": "100%(避免亏损)",
                "risk_reward": "N/A",
            },
        ],
        radar_scores={
            "情绪敏感度": 92.0,
            "执行力": 92.0,
            "选股能力": 93.0,
            "风控水平": 85.0,
            "盈利稳定性": 80.0,
        },
        position_strategy={
            "冰点期": "0%",
            "修复期": "50-70%",
            "高潮期": "70-90%",
            "退潮期": "0-10%",
        },
        applicable_cycles=["情绪修复", "情绪高潮"],
        position_limit=90,
        single_position_limit=40,
        stop_loss_rule="次日低开-3%或断板即走",
        take_profit_rule="连板持有，断板清仓",
        key_indicators=["连板高度", "涨停家数", "题材强度", "市场情绪"],
        behavioral_tags=["只做最强", "连板信仰", "弱市空仓", "纯粹超短"],
        quote="只做超强势股，连板高度是第一优先级。弱市不做，空仓也是交易。",
    )


# ═══════════════════════════════════════════════════════════
# 8. Asking — 龙头追涨之王
# ═══════════════════════════════════════════════════════════

def _asking() -> YingYouFingerprint:
    """Asking — 只做市场最高连板，只做龙头"""
    return YingYouFingerprint(
        name="Asking",
        nickname="龙头追涨之王",
        philosophy="只做市场最高连板，只做龙头，永远追最强",
        philosophy_detail=(
            "Asking是超短最纯粹的'龙头信仰者'，只做市场最高连板标的。"
            "他的交易极其纯粹: 只买市场最高标，只买龙头。"
            "核心逻辑: 龙头是市场资金共识的焦点，即使短期调整也会"
            "有资金回流。跟风股可能A杀，龙头总有体面离场的机会。"
            "他通常在龙头确认后的分歧日低吸，或在龙头转强时追涨。"
        ),
        stock_selection={
            "market_position": "市场唯一最高连板标的",
            "market_cap": "流通市值30-150亿",
            "consecutive_boards": "必须是市场最高连板(唯一)",
            "theme": "有题材支撑，非独立走势",
            "board_quality": "硬板，有换手",
            "market_attention": "市场关注度最高，论坛讨论最热",
            "historical": "前期龙头基因，有辨识度",
            "avoid": ["跟风股", "同身位竞争", "一字无量板", "独立无题材"],
        },
        entry_timing={
            "primary": "龙头分歧日低吸(首次断板或盘中炸板)",
            "secondary": "龙头转强日(竞价弱转强)",
            "tertiary": "龙头确认日(连续加速后的首次分歧)",
            "signals": [
                "市场唯一最高标",
                "首次分歧(首阴/炸板)",
                "次日竞价弱转强",
                "题材持续发酵",
                "有市场辨识度",
            ],
            "entry_method": "分歧低吸或竞价介入",
            "time_preference": "分歧时低吸或早盘竞价",
        },
        risk_control={
            "max_position": "60-90%",
            "single_limit": "单笔不超过总仓位50%",
            "stop_loss": "次日低开-5%或跌破10日线止损",
            "take_profit": "断板即走，不连板不持有",
            "empty_condition": "无明确最高标或情绪冰点时空仓",
            "drawdown_control": "单笔最大亏损-7%",
            "key_rule": "只做龙头，不做跟风；断板就走",
        },
        classic_tactics=[
            {
                "name": "龙头分歧低吸",
                "description": "市场最高标首次分歧时低吸",
                "conditions": ["市场唯一最高标", "首次断板或炸板", "题材持续", "低吸不追高"],
                "success_rate": "65-72%",
                "risk_reward": "1:3",
            },
            {
                "name": "龙头竞价转强",
                "description": "龙头断板次日，竞价弱转强时介入",
                "conditions": ["前日断板", "次日竞价高开", "快速拉升", "题材持续"],
                "success_rate": "70%+",
                "risk_reward": "1:2.5",
            },
            {
                "name": "龙头首阴反包",
                "description": "龙头首阴次日出现反包涨停",
                "conditions": ["龙头首阴", "次日高开高走", "快速上板", "市场资金回流"],
                "success_rate": "72-78%",
                "risk_reward": "1:2",
            },
        ],
        radar_scores={
            "情绪敏感度": 93.0,
            "执行力": 94.0,
            "选股能力": 96.0,
            "风控水平": 82.0,
            "盈利稳定性": 85.0,
        },
        position_strategy={
            "冰点期": "0-10%",
            "修复期": "60-80%",
            "高潮期": "80-100%",
            "退潮期": "0%",
        },
        applicable_cycles=["情绪修复", "情绪高潮"],
        position_limit=100,
        single_position_limit=50,
        stop_loss_rule="次日低开-5%或跌破10日线止损",
        take_profit_rule="断板即走",
        key_indicators=["连板高度", "市场唯一性", "题材持续性", "竞价强度"],
        behavioral_tags=["只做龙头", "最高标", "分歧低吸", "纯粹极致"],
        quote="只做龙头，永远追最强。龙头亏钱的概率远小于跟风股。",
    )


# ═══════════════════════════════════════════════════════════
# 指纹注册中心
# ═══════════════════════════════════════════════════════════

class FingerprintRegistry:
    """游资指纹注册中心 — 统一管理所有游资数字指纹"""

    def __init__(self):
        self._fingerprints: Dict[str, YingYouFingerprint] = {}
        self._register_all()

    def _register_all(self):
        """注册全部8大游资指纹"""
        constructors = [
            _chao_gu_yang_jia,
            _tui_xue_chao_gu,
            _nie_pan_chong_sheng,
            _92_ke_bi,
            _xiao_e_yu,
            _long_fei_hu,
            _zhi_ye_chao_shou,
            _asking,
        ]
        for constructor in constructors:
            fp = constructor()
            self._fingerprints[fp.name] = fp

    def get(self, name: str) -> Optional[YingYouFingerprint]:
        """根据名称获取游资指纹"""
        return self._fingerprints.get(name)

    def list_all(self) -> List[str]:
        """获取所有游资名称列表"""
        return list(self._fingerprints.keys())

    def get_all(self) -> Dict[str, YingYouFingerprint]:
        """获取全部指纹字典"""
        return self._fingerprints.copy()

    def filter_by_cycle(self, cycle: str) -> List[YingYouFingerprint]:
        """根据情绪周期筛选适用游资"""
        result = []
        for fp in self._fingerprints.values():
            if cycle in fp.applicable_cycles:
                result.append(fp)
        return result

    def get_radar_data(self, name: str) -> Optional[Dict]:
        """获取指定游资的雷达图数据"""
        fp = self._fingerprints.get(name)
        if not fp:
            return None
        return {
            "dimensions": list(fp.radar_scores.keys()),
            "scores": list(fp.radar_scores.values()),
            "full_marks": [100.0] * 5,
        }

    def compare(self, names: List[str]) -> Dict:
        """对比多个游资的雷达图数据"""
        result = {"dimensions": [], "series": []}
        for name in names:
            fp = self._fingerprints.get(name)
            if not fp:
                continue
            if not result["dimensions"]:
                result["dimensions"] = list(fp.radar_scores.keys())
            result["series"].append({
                "name": name,
                "scores": list(fp.radar_scores.values()),
            })
        return result


# 全局注册中心实例
registry = FingerprintRegistry()
